#!/bin/bash
# AlphaPulse OCI Free Tier Guard
# This script checks for resources that might exceed Always Free limits.

export SUPPRESS_LABEL_WARNING=True

COMPARTMENT_ID="ocid1.compartment.oc1..aaaaaaaadu5qdcthiuxcyybpiozzca27tlu2ef7dpgxlk67p42o3wln6ehia"
REGION="ca-toronto-1"

echo "---------------------------------------------------"
echo "🔍 AlphaPulse OCI Cost Guard - Scanning Account..."
echo "---------------------------------------------------"

# 1. Check Instances
echo -n "[1/4] Checking ARM Instances... "
INSTANCES=$(oci compute instance list --compartment-id $COMPARTMENT_ID --lifecycle-state RUNNING --all 2>/dev/null)
OCPU_COUNT=$(echo "$INSTANCES" | jq -r '.data[]. "shape-config".ocpus | select(. != null)' 2>/dev/null | awk '{s+=$1} END {print s+0}')

if [ "$OCPU_COUNT" -le 4 ]; then
    echo "✅ PASS ($OCPU_COUNT/4 OCPUs used)"
else
    echo "❌ WARNING! ($OCPU_COUNT/4 OCPUs used - YOU WILL BE CHARGED)"
fi

# 2. Check Storage
echo -n "[2/4] Checking Boot Volumes... "
VOLUMES=$(oci bv boot-volume list --compartment-id $COMPARTMENT_ID --all 2>/dev/null)
TOTAL_SIZE=$(echo "$VOLUMES" | jq -r '.data[] | select(."lifecycle-state" != "TERMINATED") | ."size-in-gbs"' 2>/dev/null | awk '{s+=$1} END {print s+0}')

if [ "$TOTAL_SIZE" -le 200 ]; then
    echo "✅ PASS ($TOTAL_SIZE/200 GB used)"
else
    echo "❌ WARNING! ($TOTAL_SIZE/200 GB used - YOU WILL BE CHARGED)"
fi

# 3. Check Backups (Common hidden cost)
echo -n "[3/4] Checking Backups... "
BACKUPS=$(oci bv boot-volume-backup list --compartment-id $COMPARTMENT_ID --all 2>/dev/null)
if [ -z "$BACKUPS" ]; then
    BACKUP_COUNT=0
else
    BACKUP_COUNT=$(echo "$BACKUPS" | jq '.data | length' 2>/dev/null || echo 0)
fi

if [ "$BACKUP_COUNT" -eq 0 ]; then
    echo "✅ PASS (0 backups found)"
else
    echo "⚠️  INFO ($BACKUP_COUNT backups found - these count towards your 200GB limit)"
fi

# 4. Check Public IPs
echo -n "[4/4] Checking Reserved IPs... "
IPS=$(oci network public-ip list --scope REGION --compartment-id $COMPARTMENT_ID --all 2>/dev/null)
UNASSIGNED_IPS=$(echo "$IPS" | jq -r '.data[] | select(."assigned-entity-id" == null) | ."ip-address"' 2>/dev/null)

if [ -z "$UNASSIGNED_IPS" ]; then
    echo "✅ PASS (All IPs are assigned)"
else
    echo "❌ WARNING! Unassigned IPs found: $UNASSIGNED_IPS (These cost money when not in use!)"
fi

echo "---------------------------------------------------"
echo "Scan complete. If all checks are green, your bill should be 0."
