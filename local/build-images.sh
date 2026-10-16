#!/usr/bin/env bash
# Constrói as imagens do laboratório a partir das tags publicadas no GitHub, sem depender do estado
# das cópias locais. Cada conjunto é o par de versões de uma release.
#
#   bash build-images.sh        # planta com malhas P (tep-plant v2.0.0): a versão fechada do TCC
#   bash build-images.sh pi     # planta com malhas PI (tep-plant v2.1.0-alpha): a do Experimento 27
#
# A planta compila dentro do Docker (images/tep-plant/Dockerfile); a primeira vez leva alguns minutos.
# As outras três imagens usam o Dockerfile do próprio repositório, na tag indicada.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
GH="https://github.com/Green-Cinnamon-Labs"

case "${1:-p}" in
    p)  PLANT="v2.0.0";       MONJOLO="v1.1.0" ;;
    pi) PLANT="v2.1.0-alpha"; MONJOLO="v1.2.0-alpha" ;;
    *)  echo "uso: bash build-images.sh [p|pi]" >&2; exit 1 ;;
esac
HISTORIAN="v1.0.0"
IHM="v1.2.0"
SUPERVISOR="v1.0.0"

build() {
    echo ""
    echo "==> $1"
    docker build -t "$@"
}

build "tep-plant:${PLANT#v}" \
    --build-context plant="${GH}/tep-plant.git#${PLANT}" \
    --build-context monjolo="${GH}/monjolo.git#${MONJOLO}" \
    "${SCRIPT_DIR}/images/tep-plant"
build "tep-historian:${HISTORIAN#v}" "${GH}/tep-historian.git#${HISTORIAN}"
build "tep-ihm:${IHM#v}" "${GH}/tep-ihm.git#${IHM}"
# O setup.sh carrega plant-supervisor:latest no Kind.
build "plant-supervisor:${SUPERVISOR#v}" -t plant-supervisor:latest "${GH}/plant-supervisor.git#${SUPERVISOR}"

echo ""
echo "Imagens prontas. Planta: tep-plant:${PLANT#v} (monjolo ${MONJOLO})."
if [ "${1:-p}" = "pi" ]; then
    echo "Para subir esta planta: TEP_PLANT_IMAGE=tep-plant:${PLANT#v} docker compose up -d"
fi
