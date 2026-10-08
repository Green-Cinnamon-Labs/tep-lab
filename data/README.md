# data

Dados gerados pelo laboratório: séries de simulação (CSV) e os gráficos feitos a partir delas. Ficam aqui, e não no repositório de especificação, para que `spec-tennessee-eastman` guarde só documentação e discussão de issues. Movidos de lá em 2026-10-08; os experimentos que os produziram estão descritos em `spec-tennessee-eastman/experimentos.md`.

## simulations/

| Arquivo | Origem no spec | Observação |
|---|---|---|
| `simulation_log.csv`, `simulation_log_N.csv`, `simulation_log_N.0.csv` | `docs/simulations/` | Uma série por experimento (o número é o do experimento em `experimentos.md`) |
| `simulation_log_exp_13.csv` | `docs/data/` | Série do Exp 13, diferente de `simulation_log_13.csv` (conteúdo não idêntico) |
| `plots/simulation_log*.png` | `docs/simulations/plots/` | Gráfico de cada série |
| `plots/simulation_log_14.0_alt.png` | `docs/csvs/simulation_log_14.0.png` | Outra versão do gráfico do Exp 14 (não idêntica a `plots/simulation_log_14.0.png`) |

O gráfico que ficava dentro do próprio pacote de análise (`analysis/docs/simulations/plots/simulation_log.png` no spec) está em `../analysis/plots/`.

## experiment_82/

Gravações do experimento #82 (função de custo e qualidade das malhas sob distúrbio), feitas com `../local/scripts/record_run.py` e resumidas com `../local/scripts/summarize_run.py`.

| Arquivo | O que é |
|---|---|
| `calibracao_2026-10-08.csv` | Operação nominal com ruído, sem distúrbio, velocidade 5 (≈10× o tempo real), `clock.t_h` 1.75 → 5.06 h, 41 avaliações do supervisor. Base dos limiares da política Modo 1 (bloco 6 da spec #85). |
| `calibracao_2026-10-08.png` | Linha do tempo dessa rodada (`analysis/` → `poetry run run-timeline`). |
| `idv6_2026-10-08.csv` | Experimento 25: IDV6 ligado em `clock.t_h` 2.31 e desligado em 3.84, regras fixas (política calibrada), velocidade 5; 44 avaliações. |
| `idv6_2026-10-08.png` | Linha do tempo dessa rodada, com os marcos de liga/desliga. |

## Como plotar

Com o pacote em `../analysis/`:

```bash
cd tep-lab/analysis
poetry install
poetry run plot --csv ../data/simulations/simulation_log.csv
```

Novas rodadas (por exemplo, as gravações do experimento #82) também entram aqui, em uma subpasta por experimento.
