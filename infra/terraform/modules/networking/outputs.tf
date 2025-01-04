# Outputs for networking module

# AWS Outputs
output "aws_vpc_id" {
  description = "ID of the AWS VPC"
  value       = aws_vpc.main.id
}

output "aws_vpc_cidr_block" {
  description = "CIDR block of the AWS VPC"
  value       = aws_vpc.main.cidr_block
}

output "aws_public_subnet_id" {
  description = "ID of the AWS public subnet"
  value       = aws_subnet.public.id
}

output "aws_public_subnet_cidr_block" {
  description = "CIDR block of the AWS public subnet"
  value       = aws_subnet.public.cidr_block
}

output "aws_security_group_id" {
  description = "ID of the AWS default security group"
  value       = aws_security_group.default.id
}

output "aws_internet_gateway_id" {
  description = "ID of the AWS Internet Gateway"
  value       = aws_internet_gateway.main.id
}

# Hetzner Cloud Outputs
output "hcloud_network_id" {
  description = "ID of the Hetzner Cloud network"
  value       = hcloud_network.main.id
}

output "hcloud_network_name" {
  description = "Name of the Hetzner Cloud network"
  value       = hcloud_network.main.name
}

output "hcloud_network_ip_range" {
  description = "IP range of the Hetzner Cloud network"
  value       = hcloud_network.main.ip_range
}

output "hcloud_subnet_id" {
  description = "ID of the Hetzner Cloud subnet"
  value       = hcloud_network_subnet.main.id
}

output "hcloud_subnet_ip_range" {
  description = "IP range of the Hetzner Cloud subnet"
  value       = hcloud_network_subnet.main.ip_range
}

output "hcloud_firewall_id" {
  description = "ID of the Hetzner Cloud firewall"
  value       = hcloud_firewall.main.id
}

output "hcloud_firewall_name" {
  description = "Name of the Hetzner Cloud firewall"
  value       = hcloud_firewall.main.name
}

# Combined Outputs
output "environment" {
  description = "Environment name"
  value       = var.environment
}

output "network_summary" {
  description = "Summary of networking configuration"
  value = {
    aws_vpc_cidr         = aws_vpc.main.cidr_block
    aws_public_subnet    = aws_subnet.public.cidr_block
    hcloud_network_range = hcloud_network.main.ip_range
    hcloud_subnet_range  = hcloud_network_subnet.main.ip_range
    environment          = var.environment
  }
}