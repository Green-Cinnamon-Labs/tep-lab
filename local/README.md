# Lab Local — Kind + TEP

Lab local para rodar o experimento Tennessee Eastman completo no seu PC: a planta publica sinais, o historian os agrega, e o Kubernetes acompanha a funcao de custo J e o cumprimento da politica de operacao.

Sao quatro pecas:

| Peca | Onde roda | Funcao |
|------|-----------|--------|
| **tep-plant** | Docker ou nativo | Planta TEP (Rust). Publica sinais via OPC-UA na porta 4840. |
| **tep-historian** | Docker ou nativo | Coleta os sinais via OPC-UA e serve medias por janela via HTTP na porta 8090. |
| **tep-operator** | Pod dentro do Kind | Operator K8s (Go). Le a funcao de custo e a politica (CRDs), pede medias ao historian e grava o veredito no `status` do `Plant`. |
| **tep-ihm** | Docker ou nativo | Dashboard (Python) na porta 8080. Sinais ao vivo via OPC-UA; veredito via API do K8s. |

**Nenhuma cloud.** So Docker + Kind.

## Pre-requisitos

| Ferramenta | Versao minima | Instalacao |
|------------|---------------|------------|
| Docker     | 20.10+        | [docs.docker.com](https://docs.docker.com/get-docker/) |
| Kind       | 0.27+         | `choco install kind` ou [kind.sigs.k8s.io](https://kind.sigs.k8s.io/docs/user/quick-start/#installation) |
| kubectl    | 1.28+         | `choco install kubernetes-cli` ou [kubernetes.io](https://kubernetes.io/docs/tasks/tools/) |

## Estrutura

```
local/
├── docker-compose.yml               # Sobe planta + historian + IHM
├── kind-config.yaml                 # Config do cluster Kind
├── setup.sh                         # Sobe o cluster, o operator e os manifestos TEP
├── k8s/
│   ├── crd.yaml                     # As 3 CRDs (copiadas de tep-operator/config/crd/bases/)
│   ├── operator-deployment.yaml     # Deploy + RBAC do operator
│   └── tep/
│       ├── cost-function-downs-vogel.yaml  # J de Downs & Vogel (1993), Tabela 9 — 12 termos
│       ├── policy-mode1.yaml               # Modo 1: metas, restricoes (Tabela 6), orcamento
│       └── plant.yaml                      # A planta: historian + politica ativa
└── README.md
```

---

## Teste completo — passo a passo

### 1. Planta + historian (+ IHM)

**Opcao A — Docker compose.** Builde as imagens e suba:

```bash
# tep-plant: o Dockerfile copia um binario Linux ja compilado (target/release/tep-plant),
# com a feature opcua ligada:  cargo build --release --bin tep-plant --features opcua
docker build -t tep-plant:latest <path-to-tep-plant>
docker build -t tep-historian:latest <path-to-tep-historian>
docker build -t tep-ihm:latest <path-to-tep-ihm>

cd tep-supervisor/local/
docker compose up
```

**Opcao B — nativo** (o caminho mais simples no Windows, onde o binario da planta e `.exe`):

```bash
cd <path-to-tep-plant>      && cargo run --features opcua
cd <path-to-tep-historian>  && poetry run tep-historian
cd <path-to-tep-ihm>        && poetry run python src/server.py   # opcional
```

Confira o historian: `curl localhost:8090/healthz` deve mostrar `"connected": true` e ~60 sinais.

### 2. Kind + operator + manifestos TEP

```bash
docker build -t tep-operator:latest <path-to-tep-operator>
cd tep-supervisor/local/
bash setup.sh
```

O script cria o cluster `tep-lab`, carrega a imagem do operator, aplica as CRDs, deploya o operator e aplica `k8s/tep/`.

### 3. Verificar

```bash
kubectl get plants
kubectl describe plant tep
```

Esperado (em ate ~30 s):

```
NAME   POLICY      COST     UNIT   PHASE       AGE
tep    tep-mode1   166.39   $/h    Compliant   1m
```

Se a fase ficar `Pending`, a condition `DataAvailable` diz o motivo (`HistorianUnreachable`, `PlantDisconnected`, `MissingSignals`, `PolicyNotFound`...).

### 4. Trocar de politica ou mexer no orcamento

```bash
kubectl edit operatingpolicy tep-mode1     # ex.: baixar maxCost para 150 → CostWithinBudget=False
kubectl edit plant tep                     # trocar policyRef para outra OperatingPolicy
```

O operator reavalia na hora. O veredito so vira `NonCompliant` depois de `persistenceEvaluations` avaliacoes ruins seguidas.

### Atualizar as CRDs

Se os types mudarem em `tep-operator`, regenere la (`make generate manifests`) e copie:

```bash
cat <path-to-tep-operator>/config/crd/bases/supervision.greenlabs.io_*.yaml > k8s/crd.yaml
```

---

## Conectividade

```
Host (Docker Desktop)
├── tep-plant      (:4840)   ← compose ou nativo
├── tep-historian  (:8090)   ← compose ou nativo, le a planta via OPC-UA
├── tep-ihm        (:8080)   ← compose ou nativo
└── tep-lab-control-plane    ← container Kind
    └── tep-operator (Pod)   ← chama http://host.docker.internal:8090
```

- O **operator** (dentro do Kind) so fala com o historian, nunca com a planta. Chega nele por `host.docker.internal:8090`, porque a porta 8090 esta exposta no host.
- A **IHM** le os sinais direto da planta (OPC-UA) e o veredito pela API do Kind (`K8S_SERVER=https://host.docker.internal:6443` quando roda em container).

---

## Comandos uteis

```bash
docker compose down                         # parar planta + historian + IHM
kubectl logs -f deploy/tep-operator         # logs do operator (uma linha por avaliacao)
kubectl get costfunctions,operatingpolicies
kubectl get plant tep -o yaml               # status completo: termos de J, metas, restricoes
kind delete cluster --name tep-lab          # destruir o cluster
```

## Issues relacionadas

- [#77 — Funcao de custo J observavel pelo Kubernetes (epic)](https://github.com/Green-Cinnamon-Labs/spec-tennessee-eastman/issues/77)
- [#80 — Manifestos TEP e infra sem gRPC](https://github.com/Green-Cinnamon-Labs/spec-tennessee-eastman/issues/80)
