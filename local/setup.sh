#!/usr/bin/env bash
# setup.sh — cria o cluster Kind, deploya o operator supervisório e aplica os manifestos TEP.
#
# A planta TEP e o historian rodam FORA do cluster (docker compose ou nativo).
# O operator roda DENTRO do Kind e consulta o historian via HTTP em host.docker.internal:8090.
#
# Pré-requisitos:
#   - docker rodando
#   - kind instalado (v0.27+)
#   - kubectl instalado
#   - imagem do operator já buildada:
#       docker build -t tep-operator:latest <path-to-tep-operator>
#
# Uso: bash setup.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLUSTER_NAME="tep-lab"

echo "=== TEP Lab Local Setup ==="

# ── 1. Criar cluster Kind ──────────────────────────────────────────────────
if kind get clusters 2>/dev/null | grep -q "^${CLUSTER_NAME}$"; then
    echo "[ok] Cluster '${CLUSTER_NAME}' já existe."
else
    echo "[1/4] Criando cluster Kind '${CLUSTER_NAME}'..."
    kind create cluster --config "${SCRIPT_DIR}/kind-config.yaml"
fi

# Garantir que kubectl aponta pro cluster certo
kubectl cluster-info --context "kind-${CLUSTER_NAME}" > /dev/null 2>&1 || {
    echo "[erro] Não consegui conectar ao cluster '${CLUSTER_NAME}'."
    exit 1
}
kubectl config use-context "kind-${CLUSTER_NAME}"

# ── 2. Carregar imagem do operator no Kind ─────────────────────────────────
echo "[2/4] Carregando imagem do operator no cluster..."

if docker image inspect tep-operator:latest > /dev/null 2>&1; then
    kind load docker-image tep-operator:latest --name "${CLUSTER_NAME}"
    echo "  ✓ tep-operator:latest"
else
    echo "  ⚠ tep-operator:latest não encontrada. Builde antes:"
    echo "    docker build -t tep-operator:latest <path-to-tep-operator>"
fi

# ── 3. CRDs + operator ────────────────────────────────────────────────────
echo "[3/4] Aplicando CRDs e o operator..."

# crd.yaml = os 3 CRDs gerados em tep-operator/config/crd/bases/ (Plant, OperatingPolicy,
# CostFunction). Se os types mudarem, regenere com:
#   cat <path-to-tep-operator>/config/crd/bases/supervision.greenlabs.io_*.yaml > k8s/crd.yaml
kubectl apply -f "${SCRIPT_DIR}/k8s/crd.yaml"
kubectl wait --for=condition=Established crd --all --timeout=30s > /dev/null
kubectl apply -f "${SCRIPT_DIR}/k8s/operator-deployment.yaml"

# A imagem tep-operator:latest foi carregada no Kind, mas pods existentes não são recriados
# automaticamente. Reinicia o Deployment para o pod usar a imagem recém-carregada.
kubectl rollout restart deployment/tep-operator

# Se o operator entrar em CrashLoop ou não ficar pronto no timeout, o setup falha aqui.
kubectl rollout status deployment/tep-operator --timeout=60s

# ── 4. Manifestos TEP (função de custo, política, planta) ─────────────────
echo "[4/4] Aplicando manifestos TEP..."
kubectl apply -f "${SCRIPT_DIR}/k8s/tep/"

echo ""
echo "=== Setup concluído ==="
echo ""
echo "A planta e o historian rodam fora do Kind (docker compose up)."
echo "O operator consulta o historian em host.docker.internal:8090."
echo ""
echo "Comandos úteis:"
echo "  kubectl get plants                     # custo J e veredito"
echo "  kubectl describe plant tep             # conditions e mensagens"
echo "  kubectl get costfunctions,operatingpolicies"
echo "  kubectl logs -f deploy/tep-operator    # logs do operator"
echo "  kind delete cluster --name ${CLUSTER_NAME}  # destruir cluster"
