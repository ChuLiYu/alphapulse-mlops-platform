# Resource Variables (Provided via TF_VAR_ environment variables)
variable "tenancy_ocid" {}
variable "user_ocid" {}
variable "fingerprint" {}
variable "private_key_path" {
  default = null
}
variable "private_key" {
  default = null
}
variable "region" {}
variable "compartment_id" {}
variable "availability_domain" {}
variable "github_token" {
  description = "GitHub PAT for GHCR access"
  type        = string
  sensitive   = true
}

variable "cloudflare_api_token" {
  description = "Cloudflare API Token with Zone.DNS and Zone.Zone permissions"
  type        = string
  sensitive   = true
}

variable "cloudflare_zone_id" {
  description = "The Cloudflare Zone ID for the domain"
  type        = string
}

variable "domain_name" {
  description = "The domain name for the frontend (e.g., alphapulse.example.com)"
  type        = string
  default     = "alphapulse.luichu.dev"
}

# Network Configuration
variable "vcn_cidr" {
  default = "10.0.0.0/16"
}

variable "subnet_cidr" {
  default = "10.0.1.0/24"
}

# Compute Configuration (Always Free ARM)
variable "instance_shape" {
  default = "VM.Standard.A1.Flex"
}

variable "instance_ocpus" {
  default = 4
}

variable "instance_memory_in_gbs" {
  default = 24
}

variable "ssh_public_key_path" {
  default = null
}
variable "ssh_public_key" {
  default = null
}

