provider "oci" {
  tenancy_ocid     = var.tenancy_ocid
  user_ocid        = var.user_ocid
  fingerprint      = var.fingerprint
  private_key_path = var.private_key_path
  private_key      = var.private_key
  region           = var.region
}

# --- Networking: Reserved Static IP ---
# NOTE: Using a RESERVED lifetime ensures this IP persists even if the instance is deleted.
resource "oci_core_public_ip" "alphapulse_static_ip" {
  compartment_id = var.compartment_id
  lifetime       = "RESERVED"
  display_name   = "alphapulse-static-ip"
}

# --- Networking: VCN & Subnet ---
resource "oci_core_vcn" "alphapulse_vcn" {
  cidr_block     = var.vcn_cidr
  compartment_id = var.compartment_id
  display_name   = "alphapulse-vcn"
  dns_label      = "alphapulse"
}

resource "oci_core_internet_gateway" "alphapulse_ig" {
  compartment_id = var.compartment_id
  vcn_id         = oci_core_vcn.alphapulse_vcn.id
  display_name   = "alphapulse-ig"
}

resource "oci_core_route_table" "alphapulse_rt" {
  compartment_id = var.compartment_id
  vcn_id         = oci_core_vcn.alphapulse_vcn.id
  display_name   = "alphapulse-rt"
  route_rules {
    destination       = "0.0.0.0/0"
    destination_type  = "CIDR_BLOCK"
    network_entity_id = oci_core_internet_gateway.alphapulse_ig.id
  }
}

resource "oci_core_security_list" "alphapulse_sl" {
  compartment_id = var.compartment_id
  vcn_id         = oci_core_vcn.alphapulse_vcn.id
  display_name   = "alphapulse-sl"

  egress_security_rules {
    destination = "0.0.0.0/0"
    protocol    = "all"
  }

  # IMPORTANT: DO NOT USE SEMICOLONS IN tcp_options. 
  # Arguments must be separated by newlines.

  ingress_security_rules {
    protocol    = "6" # TCP
    source      = "0.0.0.0/0"
    source_type = "CIDR_BLOCK"
    tcp_options {
      min = 22
      max = 22
    }
  }

  ingress_security_rules {
    protocol    = "6"
    source      = "0.0.0.0/0"
    source_type = "CIDR_BLOCK"
    tcp_options {
      min = 80
      max = 80
    }
  }

  ingress_security_rules {
    protocol    = "6"
    source      = "0.0.0.0/0"
    source_type = "CIDR_BLOCK"
    tcp_options {
      min = 443
      max = 443
    }
  }
}

resource "oci_core_subnet" "alphapulse_subnet" {
  cidr_block        = var.subnet_cidr
  compartment_id    = var.compartment_id
  vcn_id            = oci_core_vcn.alphapulse_vcn.id
  display_name      = "alphapulse-public-subnet"
  route_table_id    = oci_core_route_table.alphapulse_rt.id
  security_list_ids = [oci_core_security_list.alphapulse_sl.id]
}

# --- Compute: ARM64 Instance ---
data "oci_core_images" "oracle_linux_arm" {
  compartment_id           = var.compartment_id
  operating_system         = "Oracle Linux"
  operating_system_version = "8"
  shape                    = var.instance_shape
  sort_by                  = "TIMECREATED"
  sort_order               = "DESC"
}

resource "oci_core_instance" "alphapulse_server" {
  availability_domain = var.availability_domain
  compartment_id      = var.compartment_id
  display_name        = "alphapulse-k3s-server"
  shape               = var.instance_shape

  shape_config {
    ocpus         = var.instance_ocpus
    memory_in_gbs = var.instance_memory_in_gbs
  }

  create_vnic_details {
    subnet_id        = oci_core_subnet.alphapulse_subnet.id
    assign_public_ip = false # We link the Reserved IP manually below
  }

  source_details {
    source_type = "image"
    source_id   = data.oci_core_images.oracle_linux_arm.images[0].id
  }

    metadata = {

      ssh_authorized_keys = var.ssh_public_key != null ? var.ssh_public_key : file(var.ssh_public_key_path)

      user_data           = base64encode(<<EOF

  #!/bin/bash

  set -e

  export GH_PAT_TOKEN="${var.github_token}"

  

  # Flush and disable local firewall

   to allow K3s internal traffic
iptables -F
iptables -P INPUT ACCEPT
iptables -P FORWARD ACCEPT
iptables -P OUTPUT ACCEPT
systemctl stop firewalld || true
systemctl disable firewalld || true

# Automated K3s Installation
curl -sfL https://get.k3s.io | sh -

# Wait for K3s API to become ready
KUBECTL="/usr/local/bin/kubectl"
until [ -f "$KUBECTL" ] && "$KUBECTL" get nodes | grep -q "Ready"; do 
  sleep 5
done

# Create namespace and GHCR Secret for Private Images
"$KUBECTL" create namespace alphapulse || true
"$KUBECTL" create secret regcred \
  --docker-server=ghcr.io \
  --docker-username=ChuLiYu \
  --docker-password=$${GH_PAT_TOKEN} \
  --docker-email=chuliyu@example.com \
  -n alphapulse --dry-run=client -o yaml | "$KUBECTL" apply -f -

dnf install httpd-tools git -y
htpasswd -bc /root/auth admin AlphaPulse2026
"$KUBECTL" create secret generic admin-credentials --from-file=auth=/root/auth -n alphapulse --dry-run=client -o yaml | "$KUBECTL" apply -f -

# Zero-touch Application Deployment
DEPLOY_DIR="/root/deploy"
rm -rf "$DEPLOY_DIR"
git clone https://github.com/ChuLiYu/alphapulse-mlops-platform.git "$DEPLOY_DIR"
"$KUBECTL" apply -k "$DEPLOY_DIR/infra/k3s/base"
EOF
    )
  }
}

# --- IP Binding: Link Reserved IP to Instance ---
# To assign a Reserved IP, we must target the specific Private IP of the instance VNIC.
data "oci_core_vnic_attachments" "instance_vnics" {
  compartment_id = var.compartment_id
  instance_id    = oci_core_instance.alphapulse_server.id
}

data "oci_core_vnic" "primary_vnic" {
  vnic_id = data.oci_core_vnic_attachments.instance_vnics.vnic_attachments[0].vnic_id
}

data "oci_core_private_ips" "primary_vnic_private_ips" {
  vnic_id = data.oci_core_vnic.primary_vnic.id
}

# Final resource that performs the association
resource "oci_core_public_ip" "assign_reserved_ip" {
  compartment_id = var.compartment_id
  lifetime       = "RESERVED"
  private_ip_id  = data.oci_core_private_ips.primary_vnic_private_ips.private_ips[0].id
  # Reference the static IP address from the resource created at the top
  public_ip_pool_id = null
}

# --- Outputs ---
output "server_static_ip" {
  description = "The permanent public IP address of the AlphaPulse server"
  value       = oci_core_public_ip.alphapulse_static_ip.ip_address
}