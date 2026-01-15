# Resource Variables (Provided via TF_VAR_ environment variables)
variable "compartment_id" {
  description = "OCI Compartment ID"
  type        = string
}

variable "region" {
  description = "OCI Region"
  type        = string
}

variable "availability_domain" {
  description = "OCI Availability Domain"
  type        = string
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
  default = "~/.ssh/id_rsa.pub"
}
