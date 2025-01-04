# Compute module for AlphaPulse hybrid cloud infrastructure
# Provides Hetzner CPX21 server for Docker Compose deployment

terraform {
  required_version = ">= 1.5.0"
  required_providers {
    hcloud = {
      source  = "hetznercloud/hcloud"
      version = "~> 1.45"
    }
    local = {
      source  = "hashicorp/local"
      version = "~> 2.4"
    }
    tls = {
      source  = "hashicorp/tls"
      version = "~> 4.0"
    }
  }
}

# Generate SSH key pair for server access
resource "tls_private_key" "server_key" {
  algorithm = "RSA"
  rsa_bits  = 4096
}

# Save private key to local file (for provisioning)
resource "local_file" "private_key" {
  content         = tls_private_key.server_key.private_key_openssh
  filename        = "${path.module}/../../../../.ssh/alphapulse_${var.environment}_key"
  file_permission = "0600"
}

# Save public key to local file
resource "local_file" "public_key" {
  content  = tls_private_key.server_key.public_key_openssh
  filename = "${path.module}/../../../../.ssh/alphapulse_${var.environment}_key.pub"
}

# Upload SSH key to Hetzner Cloud
resource "hcloud_ssh_key" "server_key" {
  name       = "alphapulse-${var.environment}-key"
  public_key = tls_private_key.server_key.public_key_openssh

  labels = {
    Environment = var.environment
    Project     = "AlphaPulse"
  }
}

# Hetzner Server (CPX11 for dev, CPX21 for prod)
resource "hcloud_server" "main" {
  name        = "alphapulse-${var.environment}-server"
  server_type = var.server_type  # cpx11: 2 vCPU, 2GB RAM, 40GB SSD, €4.51/month
  image       = "ubuntu-22.04"
  location    = var.hcloud_location
  ssh_keys    = [hcloud_ssh_key.server_key.id]

  # Attach to network
  network {
    network_id = var.hcloud_network_id
  }

  # User data for initial setup (cloud-init)
  user_data = templatefile("${path.module}/user_data.yaml", {
    environment          = var.environment
    docker_compose_file  = var.docker_compose_file
    postgres_password    = var.postgres_password
    minio_access_key     = var.minio_access_key
    minio_secret_key     = var.minio_secret_key
    mlflow_tracking_uri  = var.mlflow_tracking_uri
    aws_s3_bucket        = var.aws_s3_bucket
    aws_access_key_id    = var.aws_access_key_id
    aws_secret_access_key = var.aws_secret_access_key
    ssh_key              = tls_private_key.server_key.public_key_openssh
  })

  labels = {
    Environment = var.environment
    Project     = "AlphaPulse"
    Role        = "application-server"
    CostCenter  = "mlops-platform"
  }

  # Lifecycle policy
  lifecycle {
    # Ignore changes to user_data to prevent unnecessary recreation
    ignore_changes = [user_data]
  }
}

# Attach firewall to server
resource "hcloud_firewall_attachment" "main" {
  firewall_id = var.hcloud_firewall_id
  server_ids  = [hcloud_server.main.id]
}

# Floating IP for stable public IP
resource "hcloud_floating_ip" "main" {
  type          = "ipv4"
  home_location = var.hcloud_location
  server_id     = hcloud_server.main.id

  labels = {
    Environment = var.environment
    Project     = "AlphaPulse"
  }
}

# DNS record (if domain is provided)
resource "hcloud_rdns" "main" {
  count = var.domain_name != "" ? 1 : 0

  floating_ip_id = hcloud_floating_ip.main.id
  ip_address     = hcloud_floating_ip.main.ip_address
  dns_ptr        = "${var.environment}.${var.domain_name}"
}

# Volume for persistent data (optional)
resource "hcloud_volume" "data" {
  count = var.enable_data_volume ? 1 : 0

  name      = "alphapulse-${var.environment}-data"
  size      = var.data_volume_size
  format    = "ext4"
  server_id = hcloud_server.main.id

  labels = {
    Environment = var.environment
    Project     = "AlphaPulse"
    Purpose     = "data-storage"
  }
}

# Local inventory file for Ansible/configuration management
resource "local_file" "inventory" {
  content = templatefile("${path.module}/inventory.tmpl", {
    server_name     = hcloud_server.main.name
    public_ip       = hcloud_floating_ip.main.ip_address
    private_ip      = hcloud_server.main.ipv4_address
    ssh_user        = "root"
    ssh_private_key = local_file.private_key.filename
    environment     = var.environment
  })
  filename = "${path.module}/../../../../inventory/${var.environment}.ini"
}

# Output server information to local file
resource "local_file" "server_info" {
  content = templatefile("${path.module}/server_info.tmpl", {
    environment          = var.environment
    server_name          = hcloud_server.main.name
    public_ip            = hcloud_floating_ip.main.ip_address
    private_ip           = hcloud_server.main.ipv4_address
    server_type          = hcloud_server.main.server_type
    server_location      = hcloud_server.main.location
    ssh_key_path         = local_file.private_key.filename
    enable_data_volume   = var.enable_data_volume
    data_volume_size     = var.data_volume_size
  })
  
  filename = "${path.module}/../../../../server_info_${var.environment}.txt"
}