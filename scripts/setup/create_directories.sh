#!/bin/bash
# Script to create the standardized directory structure for AlphaPulse
# Reference: docs/FILE_STRUCTURE.md

set -e

echo "🏗️  Creating AlphaPulse directory structure..."

# Configuration directories
mkdir -p config/{dev,prod}

# Documentation directories
mkdir -p docs/{deployment,api}

# Infrastructure directories
mkdir -p infra/terraform/modules/{s3,ec2,networking}
mkdir -p infra/terraform/environments/{dev,prod}
mkdir -p infra/k3s/{base,overlays}

# Notebooks for exploration
mkdir -p notebooks/{exploratory,experiments}

# Scripts organization
mkdir -p scripts/{deployment,data,monitoring}

# Source code structure
mkdir -p src/alphapulse/{api,core,data,ml,monitoring,utils}
mkdir -p src/alphapulse/api/{routes,schemas}
mkdir -p src/alphapulse/data/{collectors,storage}
mkdir -p src/alphapulse/ml/{training,inference}

# Test organization
mkdir -p tests/{unit,integration,e2e}

# Create .gitkeep files to preserve empty directories
find config docs/deployment docs/api infra/terraform infra/k3s notebooks scripts/deployment scripts/data scripts/monitoring src tests/{unit,integration,e2e} -type d -empty -exec touch {}/.gitkeep \;

echo "✅ Directory structure created successfully!"
echo "📋 Run 'tree -L 3' to visualize the structure"
