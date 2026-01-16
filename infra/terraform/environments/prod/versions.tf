terraform {
  required_version = ">= 1.5.0"

  cloud {
    organization = "lui-personal"
    workspaces {
      name = "prod-core-oci-arm64-free-tier"
    }
  }

  required_providers {
    oci = {
      source  = "oracle/oci"
      version = ">= 5.0.0"
    }
    cloudflare = {
      source  = "cloudflare/cloudflare"
      version = "~> 4.0"
    }
  }
}
