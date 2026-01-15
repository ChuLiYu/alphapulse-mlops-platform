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

