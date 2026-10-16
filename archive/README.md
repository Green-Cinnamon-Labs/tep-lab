# Archive

Material from before the TEP lab took its current shape, kept for the record. Nothing here is needed to run the lab.

## `aws-capi-practice/`

A practice from the start of the project, in Portuguese, used to learn how Kubernetes is extended with custom resources: an EC2 instance provisioned with Terraform, a Kind cluster on it acting as management cluster, and the Cluster API creating workload clusters from CRDs.

| File | What it is |
|---|---|
| [`k8s-lab-1-aws/`](aws-capi-practice/k8s-lab-1-aws/) | Step by step: SSH key, Terraform, bootstrap script, Cluster API manifests. |
| [`aws-account.md`](aws-capi-practice/aws-account.md) | Setting up the AWS account, IAM user and credentials for the practice. |
| [`SAQ.md`](aws-capi-practice/SAQ.md) | Short answers to questions that came up (Kind, `clusterctl`, EC2 restarts, Kubernetes versus plain infrastructure as code). |

The commands assume the old layout, with `k8s-lab-1-aws/` and `.aws/` at the repository root. Credentials and SSH keys were never committed; `.gitignore` still excludes them anywhere in the repository.
