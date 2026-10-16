# tep-lab

Everything needed to run the Tennessee Eastman supervision lab on one machine, and the record of what was run on it.

The lab puts a simulated chemical plant (the Tennessee Eastman process) under the watch of a Kubernetes controller that judges it against a declared operating policy. What the project is and what came out of it are explained in [`spec-tennessee-eastman`](https://github.com/Green-Cinnamon-Labs/spec-tennessee-eastman); this repository is how to reproduce it.

| Folder | What is in it |
|---|---|
| [`local/`](local/) | The lab itself: Docker Compose for the plant, the historian and the HMI; a Kind cluster for the supervisor; the TEP manifests the supervisor evaluates; scripts that record a run. |
| [`data/`](data/) | Recordings and figures from the experiments, one folder per experiment. |
| [`analysis/`](analysis/) | Python package that turns the recordings into figures. |
| [`docs/`](docs/) | [Why each piece runs where it runs](docs/arquitetura-local.md) (in Portuguese). |
| [`archive/`](archive/) | An early AWS and Cluster API practice, kept for the record. |

## Running the lab

You need Docker Desktop, [Kind](https://kind.sigs.k8s.io/) (0.27 or later), `kubectl` and a bash shell (Git Bash on Windows). From `local/`:

```bash
bash build-images.sh    # builds the four images from the release tags on GitHub
docker compose up -d    # plant, historian and HMI
bash setup.sh           # Kind cluster, supervisor, CRDs and the TEP manifests
kubectl get plants
```

The first build compiles the plant in Rust inside Docker and takes a few minutes. Within a minute the plant shows up as `Compliant`:

```
NAME   POLICY      COST     UNIT   PHASE       LOOPS   AGE
tep    tep-mode1   166.45   $/h    Compliant   True    6m
```

`LOOPS` stays `Unknown` for the first five minutes, until the loop-quality window fills. The HMI is at http://localhost:8080.

| Piece | Where | Version |
|---|---|---|
| `tep-plant` (with `monjolo`) | container, OPC UA on port 4840 | `v2.0.0` (`monjolo v1.1.0`) |
| `tep-historian` | container, HTTP on port 8090 | `v1.0.0` |
| `tep-ihm` | container, web on port 8080 | `v1.2.0` |
| `plant-supervisor` | pod in the Kind cluster `tep-lab` | `v1.0.0` |

`bash build-images.sh pi` builds the plant with proportional-integral loops instead (`tep-plant v2.1.0-alpha`, the one in Experiment 27); start it with `TEP_PLANT_IMAGE=tep-plant:2.1.0-alpha docker compose up -d`. Step-by-step notes and troubleshooting are in [`local/README.md`](local/README.md).

## Driving the plant

The plant is driven over OPC UA with a generic client such as [UaExpert](https://www.unified-automation.com/products/development-tools/uaexpert.html). The plant announces itself as `tep-plant`, so on Windows add this line to the hosts file once (PowerShell as administrator):

```powershell
Add-Content C:\Windows\System32\drivers\etc\hosts "127.0.0.1 tep-plant"
```

Then connect to `opc.tcp://tep-plant:4840/tep/server/` (no security, anonymous). Under `Objects/Signals`:

- `control.set_speed` (method): how fast the simulation runs. At 1 the plant runs at twice real time; the experiments used 5 (about 10 times real time). The speed goes back to 1 whenever the plant container restarts.
- `disturbance.idv1`, `idv2`, `idv3`, `idv6`, `idv7`: write 1 to switch a disturbance on, 0 to switch it off.
- `control.pause`, `control.resume`, `control.reset`: the simulation's life cycle.
- Every measurement (`xmeas.*`), valve (`valve.*`) and the simulated clock `clock.t_h`.

## Reproducing the experiments

| Experiment | What to do | What to expect | Recording to compare |
|---|---|---|---|
| Normal operation | speed 5, wait | `Compliant`, J ≈ 166.8 $/h, `LOOPS True` | [`data/experiment_82/calibracao_2026-10-08.csv`](data/experiment_82/) |
| Loss of the A feed (Experiment 26) | speed 5; after about 1 h of process time, `disturbance.idv6` = 1 | level loops flagged about 0.8 h later, `NonCompliant` about 1.1 h later; the plant does not recover after switching it off | [`data/experiment_82/idv6_maxoffset_2026-10-08.csv`](data/experiment_82/) |
| Same, without the tracking criterion (Experiment 25) | remove the `maxOffset` lines with `kubectl edit operatingpolicy tep-mode1`, then as above | `NonCompliant`, but `LOOPS` stays `True` | [`data/experiment_82/idv6_2026-10-08.csv`](data/experiment_82/) |
| Changing the policy live | lower `maxCost` to 160 with `kubectl edit operatingpolicy tep-mode1` | the supervisor re-evaluates at once; `NonCompliant` on the third evaluation, about a minute later | — |
| PI loops (Experiment 27) | `pi` images, speed 30, wait about 35 min | the reactor level drains, the cost falls, `NonCompliant` from the level limit around 31 h of process time, plant lost near 33 h | [`data/experiment_89/`](data/experiment_89/) |

`setup.sh` re-applies the manifests, so it undoes any `kubectl edit`. Each experiment is described in full in [`experimentos.md`](https://github.com/Green-Cinnamon-Labs/spec-tennessee-eastman/blob/main/experimentos.md).

To record a run, with the lab up (Python 3.9 or later, standard library only):

```bash
python local/scripts/record_run.py --out data/my-run/verdict.csv       # the supervisor's verdict every 10 s
python local/scripts/record_signals.py --out data/my-run/signals.csv   # plant signals the verdict does not carry
python local/scripts/summarize_run.py data/my-run/verdict.csv          # cost, conditions and loop index, summarized
```

The figures come from the [`analysis/`](analysis/) package (`poetry run run-timeline`, `signals-timeline`, `loop-rereading`).

## The TEP manifests

Everything the supervisor knows about the TEP is in [`local/k8s/tep/`](local/k8s/tep/):

| File | What it declares |
|---|---|
| [`cost-function-downs-vogel.yaml`](local/k8s/tep/cost-function-downs-vogel.yaml) | The operating cost J of Downs and Vogel (1993, Table 9), as 12 terms of coefficient × signal averages. |
| [`policy-mode1.yaml`](local/k8s/tep/policy-mode1.yaml) | Mode 1: product targets, operating limits, cost budget (170.6 $/h), persistence, and the three control loops with their quality and tracking criteria. |
| [`plant.yaml`](local/k8s/tep/plant.yaml) | The plant: where its historian is, which policy is active, how often to evaluate. |

Each one is explained line by line in the [design notes](https://github.com/Green-Cinnamon-Labs/spec-tennessee-eastman/tree/main/docs/issue77_cost_function_k8s).
