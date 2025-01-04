# Networking module for AlphaPulse hybrid cloud infrastructure
# Provides VPC, subnets, security groups, and network connectivity

terraform {
  required_version = ">= 1.5.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    hcloud = {
      source  = "hetznercloud/hcloud"
      version = "~> 1.45"
    }
  }
}

# AWS VPC for S3 and other AWS resources
resource "aws_vpc" "main" {
  cidr_block           = var.aws_vpc_cidr
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name        = "alphapulse-vpc"
    Environment = var.environment
    Project     = "AlphaPulse"
  }
}

# AWS Public Subnet
resource "aws_subnet" "public" {
  vpc_id                  = aws_vpc.main.id
  cidr_block              = var.aws_public_subnet_cidr
  availability_zone       = var.aws_availability_zone
  map_public_ip_on_launch = true

  tags = {
    Name        = "alphapulse-public-subnet"
    Environment = var.environment
    Project     = "AlphaPulse"
  }
}

# AWS Internet Gateway
resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id

  tags = {
    Name        = "alphapulse-igw"
    Environment = var.environment
    Project     = "AlphaPulse"
  }
}

# AWS Route Table
resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.main.id
  }

  tags = {
    Name        = "alphapulse-public-rt"
    Environment = var.environment
    Project     = "AlphaPulse"
  }
}

# AWS Route Table Association
resource "aws_route_table_association" "public" {
  subnet_id      = aws_subnet.public.id
  route_table_id = aws_route_table.public.id
}

# AWS Security Group for general access
resource "aws_security_group" "default" {
  name        = "alphapulse-default-sg"
  description = "Default security group for AlphaPulse"
  vpc_id      = aws_vpc.main.id

  # SSH access from anywhere (for management)
  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "SSH access"
  }

  # HTTP access
  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "HTTP access"
  }

  # HTTPS access
  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "HTTPS access"
  }

  # All outbound traffic
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "alphapulse-default-sg"
    Environment = var.environment
    Project     = "AlphaPulse"
  }
}

# Hetzner Cloud Network
resource "hcloud_network" "main" {
  name     = "alphapulse-network-${var.environment}"
  ip_range = var.hcloud_network_cidr

  labels = {
    Environment = var.environment
    Project     = "AlphaPulse"
  }
}

# Hetzner Cloud Subnet
resource "hcloud_network_subnet" "main" {
  network_id   = hcloud_network.main.id
  type         = "cloud"
  network_zone = var.hcloud_network_zone
  ip_range     = var.hcloud_subnet_cidr
}

# Hetzner Cloud Firewall
resource "hcloud_firewall" "main" {
  name = "alphapulse-firewall-${var.environment}"

  # SSH access
  rule {
    direction  = "in"
    protocol   = "tcp"
    port       = "22"
    source_ips = ["0.0.0.0/0", "::/0"]
    description = "SSH access"
  }

  # HTTP access
  rule {
    direction  = "in"
    protocol   = "tcp"
    port       = "80"
    source_ips = ["0.0.0.0/0", "::/0"]
    description = "HTTP access"
  }

  # HTTPS access
  rule {
    direction  = "in"
    protocol   = "tcp"
    port       = "443"
    source_ips = ["0.0.0.0/0", "::/0"]
    description = "HTTPS access"
  }

  # Mage.ai UI port
  rule {
    direction  = "in"
    protocol   = "tcp"
    port       = "6789"
    source_ips = ["0.0.0.0/0", "::/0"]
    description = "Mage.ai UI"
  }

  # MLflow UI port
  rule {
    direction  = "in"
    protocol   = "tcp"
    port       = "5001"
    source_ips = ["0.0.0.0/0", "::/0"]
    description = "MLflow UI"
  }

  # MinIO Console port
  rule {
    direction  = "in"
    protocol   = "tcp"
    port       = "9001"
    source_ips = ["0.0.0.0/0", "::/0"]
    description = "MinIO Console"
  }

  # PostgreSQL port
  rule {
    direction  = "in"
    protocol   = "tcp"
    port       = "5432"
    source_ips = ["0.0.0.0/0", "::/0"]
    description = "PostgreSQL"
  }

  # Allow all outbound traffic
  rule {
    direction       = "out"
    protocol        = "tcp"
    port            = "any"
    destination_ips = ["0.0.0.0/0", "::/0"]
    description     = "Outbound TCP"
  }

  rule {
    direction       = "out"
    protocol        = "udp"
    port            = "any"
    destination_ips = ["0.0.0.0/0", "::/0"]
    description     = "Outbound UDP"
  }

  rule {
    direction       = "out"
    protocol        = "icmp"
    destination_ips = ["0.0.0.0/0", "::/0"]
    description     = "Outbound ICMP"
  }

  labels = {
    Environment = var.environment
    Project     = "AlphaPulse"
  }
}