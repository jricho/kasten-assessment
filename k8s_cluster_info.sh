#!/bin/bash
# k8s_cluster_info.sh
# Usage: curl -sSL <url-to-this-script> | bash

set -euo pipefail

# Formatting
bold="\033[1m"
green="\033[32m"
blue="\033[34m"
yellow="\033[33m"
reset="\033[0m"

# Unicode icons
icon_info="\xE2\x84\xB9"      # ℹ️
icon_node="\xF0\x9F\x9A\x80" # 🚀
icon_pvc="\xF0\x9F\x93\x81"  # 📁
icon_pod="\xF0\x9F\x90\xB3"   # 🐳
icon_k8s="\xE2\x9A\x99\xEF\xB8\x8F" # ⚙️
icon_crd="\xF0\x9F\x93\x9D"   # 📝
icon_csi="\xF0\x9F\x9A\xA7"   # 🚧
icon_snap="\xF0\x9F\x93\x8A"  # 📊
icon_ns="\xF0\x9F\x94\x96"    # 🔖
icon_kasten="\xF0\x9F\x92\xBE" # 💾

line="${blue}------------------------------------------------------------${reset}"

echo ""
echo ""

# Print title
echo -e "${bold}${blue}${icon_info} ==== Please wait, gathering information ====${reset}\n$line\n"

# Print section header
echo -e "${bold}${blue}${icon_info} ==== Kubernetes Cluster Info ====${reset}\n$line\n"

# Kubernetes Version
echo -e "${bold}${green}${icon_k8s}  Kubernetes Version  ${reset}\n$line"
kubectl version; echo -e "\n"

# Nodes
echo -e "${bold}${green}${icon_node}  Nodes  ${reset}\n$line"
kubectl get nodes -o wide; echo -e "\n"

# Pods
echo -e "${bold}${green}${icon_pod}  Pods  ${reset}\n$line"
kubectl get pods -n kasten-io -o wide; echo -e "\n"

# PVCs
echo -e "${bold}${green}${icon_pvc}  PersistentVolumeClaims (PVCs)  ${reset}\n$line"
kubectl get pvc -A -o wide; echo -e "\n"

# CRDs
echo -e "${bold}${green}${icon_crd}  CustomResourceDefinitions (CRDs)  ${reset}\n$line"
kubectl get crd; echo -e "\n"

# CSI Drivers
echo -e "${bold}${green}${icon_csi}  CSI Drivers  ${reset}\n$line"
kubectl get csidriver; echo -e "\n"

echo -e "${bold}${green}${icon_csi}  CSI Nodes  ${reset}\n$line"
kubectl get csinodes; echo -e "\n"

# VolumeSnapshotClass
echo -e "${bold}${green}${icon_snap}  VolumeSnapshotClass  ${reset}\n$line"
kubectl get volumesnapshotclass || echo "(none)"; echo -e "\n"

# Kasten K10 Inventory (if present)
if kubectl get ns | grep -q 'kasten-io'; then
  echo -e "${bold}${yellow}${icon_kasten}  Kasten K10 Inventory  ${reset}\n$line"
  for r in storagerepositories.kio.kasten.io restorepoints applications.apps.kio.kasten.io profiles.config.kio.kasten.io policies.config.kio.kasten.io actionsets blueprints.cr.kanister.io; do
    echo -e "${bold}Resource:${reset} $r"
    kubectl get "$r" -A 2>/dev/null || echo "(none)"
    echo -e "\n"
  done
fi

echo -e "${bold}${blue}${icon_info} ==== End of Report ====${reset}\n$line\n"
