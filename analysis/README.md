# TEP Analysis — Pacote de Análise

Pacote Python que transforma as gravações do laboratório (`../data/`) em figuras.

## Por que este pacote existe

- Separar lógica de plot e análise de dados do serviço de simulação em Rust
- Fornecer um CLI (`plot`) para geração rápida de gráficos
- Garantir isolamento de dependências via Poetry

## Pré-requisitos

Execute a partir do diretório `analysis/`:

```bash
poetry install
```

(Opcional) verificar o ambiente virtual:

```bash
poetry env info --path
```

## Comandos

### 1. Gerar plot (CSV padrão)

```bash
poetry run plot
```

Usa o entry point definido em `pyproject.toml`: `plot = "tep_analysis.plot:main"`

### 2. Gerar plot com CSV específico

```bash
poetry run plot --csv ../data/simulations/simulation_log.csv --smooth 41 --tmax 10
```

### 3. Comando equivalente via módulo Python

```bash
poetry run python -m tep_analysis.plot
```

## Verificar ambiente virtual

```bash
poetry run python -c "import sys; print(sys.executable)"
```

O caminho deve apontar para o ambiente virtual do Poetry, não para o Python global.

## Saída

A imagem do plot é salva ao lado do CSV, com extensão `.png`.

Exemplo:
- `../data/simulations/simulation_log.csv`
- `../data/simulations/simulation_log.png`

## Linha do tempo de uma rodada (`run-timeline`)

Para as gravações feitas com `../local/scripts/record_run.py` (calibração e experimento #82): um gráfico com quatro painéis no tempo simulado (`clock.t_h`) — custo J contra o orçamento, as conditions do veredito como faixas, o Predictability Index de cada malha contra o limiar, e o σ da válvula contra o portão.

```bash
poetry install
poetry run run-timeline ../data/experiment_82/idv6_2026-10-08.csv --mark 2.31:"IDV6 ligado" --mark 3.84:"IDV6 desligado"
```

O PNG sai ao lado do CSV. `--pi-threshold` e `--gate` devem bater com `minPredictability` e `minOutputStd` da política (padrão 0.12 e 0.05); `--max-offset malha=valor` acrescenta o painel do offset.

## Sinais da planta (`signals-timeline`)

Para as gravações do `../local/scripts/record_signals.py`: um painel por sinal no tempo simulado; por padrão, válvula de purga, pressão, nível e temperatura do reator e inerte B na purga (`--keys` escolhe outros). Aceita mais de uma gravação, sobrepostas nos mesmos eixos (`--label` para cada uma).

## Releitura do índice das malhas (`loop-rereading`)

Refaz, sobre gravações do `record_run.py`, o julgamento das malhas na escala do artigo de Bradu et al. (`1 − pi`), com as mesmas regras do supervisor e sem o critério de offset. Imprime uma tabela por rodada e, com `--plot`, gera a figura.

Os comandos exatos que geraram cada figura dos experimentos estão em [`../data/README.md`](../data/README.md).
