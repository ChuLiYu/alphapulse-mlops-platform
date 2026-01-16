#!/bin/bash

# Check if required environment variables are set
if [ -z "$TF_VAR_compartment_id" ]; then
  echo "❌ Error: Environment variable TF_VAR_compartment_id is not set."
  echo "Please run: export TF_VAR_compartment_id='...'
  exit 1
fi

echo "🔍 Starting Oracle Cloud resource check (Compartment: ${TF_VAR_compartment_id:0:10}...)"

echo "\n📋 [1/3] Checking Running Instances..."
oci compute instance list --compartment-id "$TF_VAR_compartment_id" --lifecycle-state RUNNING --output table --query "data[*].{Name:\"display-name\", Shape:shape, OCPUs:\"shape-config\".ocpus, Memory:\"shape-config\".\"memory-in-gbs\"}"

echo "\n📋 [2/3] Checking Stopped Instances (May still occupy quota)..."
oci compute instance list --compartment-id "$TF_VAR_compartment_id" --lifecycle-state STOPPED --output table --query "data[*].{Name:\"display-name\", Shape:shape, OCPUs:\"shape-config\".ocpus, Memory:\"shape-config\".\"memory-in-gbs\"}"

echo "\n💾 [3/3] Checking Boot Volumes (200GB Free Tier limit)..."
oci bv boot-volume list --compartment-id "$TF_VAR_compartment_id" --output table --query "data[*].{Name:\"display-name\", SizeGB:\"size-in-gbs\", State:\"lifecycle-state\"}"

echo "\n✅ Check complete."