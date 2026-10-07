# Lab K8s Supervisor

Infrastructure repository for the **Tennessee Eastman CPS Lab** project.
Contains cluster configurations, deployment manifests, and setup scripts for running the TEP plant, the historian and the supervisory operator across different environments. It also holds the TEP-specific manifests the operator evaluates: the Downs & Vogel cost function and the mode 1 operating policy (`local/k8s/tep/`).

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
| [tep-operator](https://github.com/Green-Cinnamon-Labs/tep-operator) | Supervisory operator (Go + controller-runtime): evaluates the declared cost function and policy |

## Note

> `.gitignore` ignores credentials, SSH keys, and Terraform artifacts. It's normal for these files not to appear in the remote repository.
