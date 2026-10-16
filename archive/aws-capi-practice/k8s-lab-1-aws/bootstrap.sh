#!/usr/bin/env bash
set -e

USER_NAME=ubuntu

# ---------- Atualização básica ----------
sudo apt update -y
sudo apt upgrade -y

# ---------- Docker ----------
if ! command -v docker >/dev/null 2>&1; then
  sudo apt install -y docker.io
  sudo systemctl enable --now docker
fi

# Garante usuário no grupo docker
if ! groups $USER_NAME | grep -q docker; then
  sudo usermod -aG docker $USER_NAME
  echo "INFO: usuário '$USER_NAME' adicionado ao grupo docker."
  echo "IMPORTANTE: saia e entre novamente na sessão SSH para aplicar a permissão."
fi

# ---------- KIND ----------
if ! command -v kind >/dev/null 2>&1; then
  curl -Lo kind https://kind.sigs.k8s.io/dl/v0.20.0/kind-linux-amd64
  chmod +x kind
  sudo mv kind /usr/local/bin/
fi

# ---------- kubectl ----------
if ! command -v kubectl >/dev/null 2>&1; then
  curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
  chmod +x kubectl
  sudo mv kubectl /usr/local/bin/
fi

# ---------- Cluster KIND ----------
if ! kind get clusters | grep -q capi-mgmt; then
  kind create cluster --name capi-mgmt
fi

# ---------- clusterctl ----------
if ! command -v clusterctl >/dev/null 2>&1; then
  curl -L https://github.com/kubernetes-sigs/cluster-api/releases/download/v1.7.2/clusterctl-linux-amd64 -o clusterctl
  chmod +x clusterctl
  sudo mv clusterctl /usr/local/bin/
fi

# ---------- Cluster API ----------
if ! kubectl get crd clusters.cluster.x-k8s.io >/dev/null 2>&1; then
  export AWS_B64ENCODED_CREDENTIALS=$(base64 -w0 ~/.aws/credentials)
  clusterctl init --infrastructure aws
fi

# ---------- Verificações ----------
kubectl get nodes
kubectl get pods -A
