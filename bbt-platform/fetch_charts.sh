#!/bin/bash
set -euo pipefail
mkdir -p charts
helm pull rancher --repo https://releases.rancher.com/server-charts/stable --version 2.15.2 --destination charts
helm pull nfs-subdir-external-provisioner --repo https://kubernetes-sigs.github.io/nfs-subdir-external-provisioner --version 4.0.18 --destination charts
helm pull juicefs-csi-driver --repo https://juicedata.github.io/charts --version 0.33.2 --destination charts
helm pull gpu-operator --repo https://helm.ngc.nvidia.com/nvidia --version v26.7.2 --destination charts
helm pull volcano --repo https://volcano-sh.github.io/helm-charts --version 1.14.1 --destination charts
helm pull oci://ghcr.io/slinkyproject/charts/slurm-operator-crds --version 1.1.0 --destination charts
helm pull oci://ghcr.io/slinkyproject/charts/slurm-operator --version 1.1.0 --destination charts
helm pull oci://ghcr.io/slinkyproject/charts/slurm --version 1.1.0 --destination charts
helm pull oci://quay.io/jetstack/charts/cert-manager --version 1.21.3 --destination charts
helm pull kube-prometheus-stack --repo https://prometheus-community.github.io/helm-charts --version 92.14.0 --destination charts
helm pull argo-cd --repo https://argoproj.github.io/argo-helm --version 10.11.6 --destination charts
sha256sum charts/*.tgz > charts/SHA256SUMS
