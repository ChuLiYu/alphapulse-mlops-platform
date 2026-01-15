provider "oci" {
  # The provider will automatically use:
  # OCI_TENANCY_OCID, OCI_USER_OCID, OCI_FINGERPRINT, OCI_PRIVATE_KEY_PATH, OCI_REGION
}

# --- Networking ---
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

  # SSH
  ingress_security_rules {
    protocol = "6"
    source   = "0.0.0.0/0"
    tcp_options {
      min = 22
      max = 22
    }
  }

  # HTTP
  ingress_security_rules {
    protocol = "6"
    source   = "0.0.0.0/0"
    tcp_options {
      min = 80
      max = 80
    }
  }

  # HTTPS
  ingress_security_rules {
    protocol = "6"
    source   = "0.0.0.0/0"
    tcp_options {
      min = 443
      max = 443
    }
  }
  
  # K3s API (Optional, restrict source IP in production if possible)
  ingress_security_rules {
    protocol = "6"
    source   = "0.0.0.0/0"
    tcp_options {
      min = 6443
      max = 6443
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

# --- Compute (ARM64) ---
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
    assign_public_ip = true
  }

  source_details {
    source_type = "image"
    source_id   = data.oci_core_images.oracle_linux_arm.images[0].id
  }

  metadata = {
    ssh_authorized_keys = file(var.ssh_public_key_path)
    user_data           = base64encode("#!/bin/bash\niptables -F\nfirewall-cmd --permanent --add-port=80/tcp\nfirewall-cmd --permanent --add-port=443/tcp\nfirewall-cmd --permanent --add-port=6443/tcp\nfirewall-cmd --reload")
  }
}

data "oci_identity_availability_domains" "ads" {
  compartment_id = var.compartment_id
}

output "server_public_ip" {
  value = oci_core_instance.alphapulse_server.public_ip
}