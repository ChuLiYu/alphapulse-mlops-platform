# --- AlphaPulse MLOps Production Infrastructure ---
# Verified: TFC VCS-driven workflow is active.
provider "oci" {
  tenancy_ocid     = var.tenancy_ocid
  user_ocid        = var.user_ocid
  fingerprint      = var.fingerprint
  private_key_path = var.private_key_path
  private_key      = var.private_key
  region           = var.region
}

# --- Networking: Reserved Static IP ---
resource "oci_core_public_ip" "alphapulse_static_ip" {
  compartment_id = var.compartment_id
  lifetime       = "RESERVED"
  display_name   = "alphapulse-static-ip"
  private_ip_id  = data.oci_core_private_ips.primary_vnic_private_ips.private_ips[0].id
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

  ingress_security_rules {
    protocol    = "6"
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
    assign_public_ip = false
  }

  source_details {
    source_type             = "image"
    source_id               = data.oci_core_images.oracle_linux_arm.images[0].id
    boot_volume_size_in_gbs = 200
  }

  metadata = {
    ssh_authorized_keys = var.ssh_public_key != null ? var.ssh_public_key : file(var.ssh_public_key_path)
    user_data = base64encode(<<EOF
#!/bin/bash
set -x
exec > /var/log/user_data.log 2>&1

echo "Starting deployment at $(date)"

# Expand filesystem to match boot volume size
/usr/libexec/oci-growfs -y

# Open firewall
iptables -F
iptables -P INPUT ACCEPT
iptables -P FORWARD ACCEPT
iptables -P OUTPUT ACCEPT
# Persistent firewall changes for Oracle Linux
if command -v firewall-cmd >/dev/null 2>&1; then
  firewall-cmd --permanent --add-port=80/tcp
  firewall-cmd --permanent --add-port=443/tcp
  firewall-cmd --reload
fi
systemctl stop firewalld || true

# Install K3s
curl -sfL https://get.k3s.io | sh - 

# 1. Resolve Path Issues: Create symbolic links
ln -s /usr/local/bin/k3s /usr/bin/k3s || true
ln -s /usr/local/bin/kubectl /usr/bin/kubectl || true

# 2. Resolve Race Condition: Wait for Node to be Ready
echo "Waiting for K3s node to be Ready..."
timeout 600s bash -c 'until /usr/local/bin/kubectl get nodes | grep -q "  Ready "; do sleep 10; echo "Still waiting for node..."; done'

export KUBECONFIG=/etc/rancher/k3s/k3s.yaml
alias kubectl='/usr/local/bin/kubectl'

# GHCR Secret
export KUBECONFIG=/etc/rancher/k3s/k3s.yaml
/usr/local/bin/kubectl create namespace alphapulse || true
/usr/local/bin/kubectl create secret docker-registry regcred \
  --docker-server=ghcr.io \
  --docker-username=chuliyu \
  --docker-password="${var.github_token}" \
  --docker-email=chuliyu@example.com \
  -n alphapulse --dry-run=client -o yaml | /usr/local/bin/kubectl apply -f -

# Deploy
dnf install git -y
git clone https://github.com/ChuLiYu/alphapulse-mlops-platform.git /root/deploy || true
/usr/local/bin/kubectl apply -k /root/deploy/infra/k3s/base

echo "Deployment finished at $(date)"
EOF
    )
  }
}

# --- IP Binding ---
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

output "server_static_ip" {
  description = "The permanent public IP address of the AlphaPulse server"
  value       = oci_core_public_ip.alphapulse_static_ip.ip_address
}
