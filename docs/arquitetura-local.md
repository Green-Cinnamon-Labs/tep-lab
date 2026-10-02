# Arquitetura do Ambiente Local

Este documento explica como o ambiente local funciona: o que roda onde, por que cada coisa é assim, e como os componentes se comunicam.

## O que roda na máquina do desenvolvedor

Na máquina do dev rodam dois mundos com funções completamente diferentes: a planta e seu historian (fora do Kubernetes) e o nó Kind (o Kubernetes):

```
Máquina do Dev (Docker Desktop)
│
├── tep-plant (Rust) — container ou processo nativo
│   └── Simulação Tennessee Eastman, sinais publicados via OPC-UA
│   └── Porta exposta: 4840
│   └── Roda standalone, não sabe que o Kubernetes existe
│
├── tep-historian (Python) — container ou processo nativo
│   └── Lê todos os sinais da planta via OPC-UA, serve médias por janela via HTTP
│   └── Porta exposta: 8090
│
└── Container: Kind (nó Kubernetes)
    └── containerd (runtime de containers do K8s)
        ├── Pod: tep-operator (Go, controller-runtime)
        ├── Pod: kube-apiserver
        ├── Pod: etcd
        ├── Pod: coredns
        └── Pod: kube-controller-manager, kube-scheduler, kube-proxy

Comunicação:
  tep-historian ──OPC-UA──▶ tep-plant (:4840)
  tep-operator  ──HTTP────▶ tep-historian (via host.docker.internal:8090)
```

A **planta** simula o processo químico Tennessee Eastman e publica seus sinais via OPC-UA. Ela não tem nada a ver com Kubernetes.

O **historian** é o middleware: traduz sinais brutos em estatísticas por janela. O Kubernetes nunca vê sinal bruto.

O **nó Kind** Dentro dele roda um Kubernetes real e completo, com seu próprio runtime de containers (containerd). O operator roda como Pod dentro desse Kubernetes.

## O que roda DENTRO do Kind

O Kind (Kubernetes in Docker) é um container Docker que simula um nó Kubernetes. Dentro dele:

- Roda um **Kubernetes real** com todos os componentes: etcd, kube-apiserver, controller-manager, scheduler.
- O runtime de containers **não é o Docker** — é o containerd, que o Kubernetes usa pra subir Pods.
- O operator (`tep-operator`) roda como um **Pod** gerenciado pelo Kubernetes.

Sim, tecnicamente o operator é um **container dentro de um container**. Isso é específico do Kind — é o custo de simular um cluster inteiro na sua máquina. Em produção, o nó seria uma VM real (ou bare metal) e não haveria essa aninhação.

## Por que o operator precisa rodar DENTRO do Kubernetes

O Kubernetes só gerencia o que roda dentro dele. Ele não sabe que existem containers Docker avulsos na sua máquina. Se o operator rodasse fora do cluster, ele seria apenas um binário Go solto, sem orquestração.

Rodando como Pod dentro do Kubernetes, o operator ganha:

1. **Acesso nativo aos CRs** — O operator precisa ler `CostFunction`, `OperatingPolicy` e o spec do `Plant`, e escrever o veredito no status do `Plant`. Rodando como Pod, ele faz isso via controller-runtime, usando o ServiceAccount e o RBAC do cluster.

2. **Lifecycle management** — O Kubernetes garante que o operator está rodando. Se o Pod cair, o Deployment recria. Se precisar escalar, é só ajustar as réplicas.

3. **Observabilidade** — Logs, events, conditions, métricas — tudo integrado no ecossistema K8s.

## Por que o operator precisa de uma imagem Docker própria

Qualquer programa que roda no Kubernetes precisa estar empacotado como imagem de container. Não tem como rodar um `.exe` ou um binário Go direto num Pod.

O `tep-operator:latest` é o código Go compilado dentro de uma imagem minimal (distroless). O Kubernetes baixa essa imagem e sobe como Pod.

O comando `kind load docker-image tep-operator:latest` copia a imagem do Docker Desktop da máquina pra dentro do nó Kind. Isso é necessário porque são ambientes isolados — o Docker Desktop e o containerd dentro do Kind não compartilham imagens. Sem esse `kind load`, o Kubernetes tentaria puxar a imagem de um registry remoto e falharia.

## Por que a planta NÃO roda dentro do Kind

A planta é um **sistema externo** que o operator supervisiona. Ela não é parte do Kubernetes — é o "mundo real" que o operator observa.

Num cenário de produção, a planta seria:
- Um **PLC físico** numa fábrica
- Uma **simulação** rodando em outro servidor
- Um **sistema legado** que expõe dados via protocolo industrial

Rodar a planta dentro do Kind criaria uma falsa dependência. O Kubernetes não gerencia a planta — ele só gerencia o operator que a observa. Manter a planta fora do cluster é mais realista e reflete a separação de responsabilidades: a planta é o processo, o operator é o supervisor.

## Como o operator alcança os dados da planta

O operator (dentro do Kind) não fala com a planta — só com o historian, que está fora do cluster. A comunicação acontece pela rede Docker:

1. O historian expõe a porta 8090 no host
2. O operator chama `http://host.docker.internal:8090/aggregate`
3. `host.docker.internal` é um DNS especial que o Docker resolve pro IP da máquina host (no Docker Desktop do Windows ele resolve para um endereço IPv6, e funciona de dentro dos Pods)

No CRD, o endereço é configurado no spec do `Plant`:
```yaml
spec:
  historianURL: "http://host.docker.internal:8090"
```

Se `host.docker.internal` não funcionar (alguns ambientes Linux), use o IP da bridge Docker:
```bash
docker network inspect bridge | grep Gateway
# Exemplo: 172.17.0.1
```
E configure: `historianURL: "http://172.17.0.1:8090"`
