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
| `idv6_maxoffset_2026-10-08.csv` | Experimento 26: mesma rodada com o critério de seguimento de setpoint (`maxOffset`); IDV6 ligado em 2.02 e desligado em 3.22; 35 avaliações. |
| `idv6_maxoffset_2026-10-08.png` | Linha do tempo dessa rodada. |

## experiment_89/

Gravações do Experimento 27 (spec #89): malhas PI em operação nominal, sem distúrbio, e o controle com malhas P. O registro do supervisor é feito com `../local/scripts/record_run.py`; os sinais da planta, que o `Plant.status` não traz (nível do reator, composições, válvulas), com `../local/scripts/record_signals.py`, lendo o historian.

| Arquivo | O que é |
|---|---|
| `pi_nominal_2026-10-10.csv` | Rodada 1: malhas PI, velocidade 5 (≈10× o tempo real), `clock.t_h` 0.03 → 9.97 h, 122 avaliações do supervisor. |
| `pi_nominal_2026-10-10.png` | Linha do tempo dessa rodada (`run-timeline`, com o painel de offset). |
| `pi_nominal_longo_2026-10-10.csv` | Rodada 2: malhas PI, velocidade 30 (≈56×), `clock.t_h` 0.16 → 32.83 h, até a perda da planta; 70 avaliações. |
| `pi_nominal_longo_2026-10-10.png` | Linha do tempo do supervisor nessa rodada. |
| `pi_nominal_longo_sinais_2026-10-10.csv` | Sinais da planta na rodada 2, `clock.t_h` 0.02 → 32.92 h, uma linha a cada 10 s de relógio (≈9 min simulados). |
| `pi_nominal_longo_sinais_2026-10-10.png` | Linha do tempo desses sinais (`signals-timeline`). |
| `pi_nominal_longo_sinais_final_2026-10-10.png` | Os mesmos sinais a partir de `clock.t_h` 28.5: o colapso em detalhe. |
| `p_controle_2026-10-11.csv` | Controle: malhas P (integral congelada), velocidade 30, `clock.t_h` 1.15 → 40.26 h; 84 avaliações. |
| `p_controle_2026-10-11.png` | Linha do tempo do supervisor no controle. |
| `p_controle_sinais_2026-10-11.csv` | Sinais da planta no controle, `clock.t_h` 0.01 → 40.5 h. |
| `pi_vs_p_sinais_2026-10-11.png` | Rodada 2 (PI) e controle (P) sobrepostos nos mesmos eixos — a figura principal do experimento. |
| `pi_vs_p_quem_flutua_2026-10-11.png` | A mesma comparação só até `clock.t_h` 30 (antes do colapso), com a pressão em escala fina: com P quem se move é a pressão, com PI é a purga. |

Para refazer as figuras, de dentro de `../analysis/`:

```bash
poetry run run-timeline ../data/experiment_89/pi_nominal_longo_2026-10-10.csv --max-offset reactor_pressure=20 --max-offset separator_level=1 --max-offset stripper_level=1
poetry run signals-timeline ../data/experiment_89/pi_nominal_longo_sinais_2026-10-10.csv ../data/experiment_89/p_controle_sinais_2026-10-11.csv --label PI --label P --out ../data/experiment_89/pi_vs_p_sinais_2026-10-11.png
```

## Como plotar

Com o pacote em `../analysis/`:

```bash
cd tep-lab/analysis
poetry install
poetry run plot --csv ../data/simulations/simulation_log.csv
```

Novas rodadas (por exemplo, as gravações do experimento #82) também entram aqui, em uma subpasta por experimento.
