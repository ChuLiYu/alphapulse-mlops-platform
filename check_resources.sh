#!/bin/bash

# 檢查變數是否存在
if [ -z "$TF_VAR_compartment_id" ]; then
  echo "❌ 錯誤: 環境變數 TF_VAR_compartment_id 未設定。"
  echo "請先執行 export TF_VAR_compartment_id='...'
  exit 1
fi

echo "🔍 開始檢查 Oracle Cloud 資源 (Compartment: ${TF_VAR_compartment_id:0:10}...)"

echo "\n📋 [1/3] 檢查執行中的實例 (Running Instances)..."
oci compute instance list --compartment-id "$TF_VAR_compartment_id" --lifecycle-state RUNNING --output table --query "data[*].{Name:\"display-name\", Shape:shape, OCPUs:\"shape-config\".ocpus, Memory:\"shape-config\".\"memory-in-gbs\"}"

echo "\n📋 [2/3] 檢查已停止的實例 (Stopped Instances - 仍可能佔用配額)..."
oci compute instance list --compartment-id "$TF_VAR_compartment_id" --lifecycle-state STOPPED --output table --query "data[*].{Name:\"display-name\", Shape:shape, OCPUs:\"shape-config\".ocpus, Memory:\"shape-config\".\"memory-in-gbs\"}"

echo "\n💾 [3/3] 檢查開機磁碟 (Boot Volumes - 佔用 200GB 額度)..."
oci bv boot-volume list --compartment-id "$TF_VAR_compartment_id" --output table --query "data[*].{Name:\"display-name\", SizeGB:\"size-in-gbs\", State:\"lifecycle-state\"}"

echo "\n✅ 檢查完成。"
