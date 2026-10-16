#!/bin/sh
# Monta o application.toml a cada partida: o da versão compilada mais o endpoint OPC UA do container.
# Refeito do zero para que um restart do container não duplique a seção [monjolo.opcua].
set -e
cp application.base.toml application.toml
printf '\n[monjolo.opcua]\nendpoint = "opc.tcp://%s:4840/tep/server/"\n' "${OPCUA_HOST:-$(hostname)}" >> application.toml
exec ./tep-plant
