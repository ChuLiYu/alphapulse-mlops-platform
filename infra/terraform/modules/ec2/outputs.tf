# Outputs for compute module

# Server Information
output "server_id" {
  description = "ID of the Hetzner server"
  value       = hcloud_server.main.id
}

output "server_name" {
  description = "Name of the Hetzner server"
  value       = hcloud_server.main.name
}

output "server_type" {
  description = "Type of the Hetzner server"
  value       = hcloud_server.main.server_type
}

output "server_location" {
  description = "Location of the Hetzner server"
  value       = hcloud_server.main.location
}

# IP Addresses
output "public_ip" {
  description = "Public IP address (floating IP)"
  value       = hcloud_floating_ip.main.ip_address
}

output "private_ip" {
  description = "Private IP address"
  value       = hcloud_server.main.ipv4_address
}

output "ipv6_address" {
  description = "IPv6 address"
  value       = hcloud_server.main.ipv6_address
}

# SSH Access
output "ssh_private_key_path" {
  description = "Path to the SSH private key file"
  value       = local_file.private_key.filename
  sensitive   = true
}

output "ssh_public_key" {
  description = "SSH public key"
  value       = tls_private_key.server_key.public_key_openssh
}

# Service URLs
output "public_ip" {
  description = "Public IP address of the EC2 instance"
  value       = aws_instance.app_server.public_ip
}


output "mlflow_ui_url" {
  description = "URL for MLflow UI"
  value       = "http://${hcloud_floating_ip.main.ip_address}:5001"
}

output "minio_console_url" {
  description = "URL for MinIO Console"
  value       = "http://${hcloud_floating_ip.main.ip_address}:9001"
}

output "minio_api_url" {
  description = "URL for MinIO API"
  value       = "http://${hcloud_floating_ip.main.ip_address}:9000"
}

# Volume Information
output "data_volume_id" {
  description = "ID of the data volume (if enabled)"
  value       = var.enable_data_volume ? hcloud_volume.data[0].id : null
}

output "data_volume_size" {
  description = "Size of the data volume in GB"
  value       = var.enable_data_volume ? hcloud_volume.data[0].size : 0
}

# Cost Information
output "monthly_cost_estimate" {
  description = "Estimated monthly cost in EUR"
  value = {
    server      = 9.50 # CPX21 fixed price
    floating_ip = 0.00 # Included
    volume      = var.enable_data_volume ? var.data_volume_size * 0.004 : 0.00
    total       = 9.50 + (var.enable_data_volume ? var.data_volume_size * 0.004 : 0.00)
  }
}

# Deployment Information
output "inventory_file" {
  description = "Path to the generated Ansible inventory file"
  value       = local_file.inventory.filename
}

output "server_info_file" {
  description = "Path to the server information file"
  value       = local_file.server_info.filename
}

output "deployment_status" {
  description = "Deployment status summary"
  value = {
    server_created       = true
    services_deployed    = true
    ssh_configured       = true
    firewall_configured  = true
    floating_ip_assigned = true
    environment          = var.environment
    timestamp            = timestamp()
  }
}

# Connection Instructions
output "connection_instructions" {
  description = "Instructions for connecting to the server"
  value       = <<-EOT
    To connect to the AlphaPulse server:
    
    1. SSH Access:
       ssh -i ${local_file.private_key.filename} root@${hcloud_floating_ip.main.ip_address}
    
    2. Service URLs:
       - Airflow Webserver: http://${hcloud_floating_ip.main.ip_address}:8080
       - MLflow UI: http://${hcloud_floating_ip.main.ip_address}:5001
       - MinIO Console: http://${hcloud_floating_ip.main.ip_address}:9001
       - MinIO API: http://${hcloud_floating_ip.main.ip_address}:9000
    
    3. Database Access:
       Host: ${hcloud_server.main.ipv4_address}
       Port: 5432
       Database: alphapulse
       Username: postgres
       Password: ${var.postgres_password}
    
    4. Check deployment status:
       ssh -i ${local_file.private_key.filename} root@${hcloud_floating_ip.main.ip_address} "systemctl status alphapulse.service"
    
    Deployment completed at: ${timestamp()}
  EOT
}