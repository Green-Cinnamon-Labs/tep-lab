# tep-lab

Infrastructure repository for the **Tennessee Eastman CPS Lab** project.
Contains cluster configurations, deployment manifests, and setup scripts for running the TEP plant, the historian and the plant supervisor across different environments. It also holds the TEP-specific manifests the supervisor evaluates: the Downs & Vogel cost function and the mode 1 operating policy (`local/k8s/tep/`).

## Data and analysis

| Directory | Content |
|-----------|---------|
| [`data/`](data/) | Lab data: simulation series (CSV) and their plots, one per experiment. See [`data/README.md`](data/README.md). |
| [`analysis/`](analysis/) | Python package to plot the simulation series (`poetry run plot --csv ../data/simulations/...`). |

Both moved here from `spec-tennessee-eastman` (2026-10-08), which now holds only documentation and issue discussions.

## Environments

| Directory | Environment | Status |
|-----------|----------|--------|
| [`local/`](local/) | **Kind** (local cluster, no cloud) | active |
| [`k8s-lab-1-aws/`](k8s-lab-1-aws/) | AWS (EC2 + Terraform) | legacy |
| [`k8s-lab-1-azr/`](k8s-lab-1-azr/) | Azure | placeholder |
| [`k8s-lab-1-gcp/`](k8s-lab-1-gcp/) | GCP | placeholder |

## Local Lab (Kind)

The main development environment. Runs everything on your machine with Docker + Kind.

**Prerequisites:** Docker, Kind (v0.27+), kubectl.

```bash
cd local/
bash setup.sh
```

Full details in [`local/README.md`](local/README.md).

## Related repositories

| Repo | Description |
|------|-----------|
| [tep-plant](https://github.com/Green-Cinnamon-Labs/tep-plant) | TEP plant (Rust simulation, signals over OPC-UA) |
| tep-historian | OPC-UA collector, window statistics over HTTP |
| [plant-supervisor](https://github.com/Green-Cinnamon-Labs/plant-supervisor) | Supervisory operator (Go + controller-runtime): evaluates the declared cost function and policy |

## Note

> `.gitignore` ignores credentials, SSH keys, and Terraform artifacts. It's normal for these files not to appear in the remote repository.
