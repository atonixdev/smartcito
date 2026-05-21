# Kubernetes Infra

Kubernetes manifests for SmartCito services.

## Purpose

Deploy split-function services with namespaces, services, network policies, and
scaling controls.

## Technologies Used

- Kubernetes Deployments and Services
- NetworkPolicy
- HorizontalPodAutoscaler

## How To Run

```bash
kubectl apply -f infra/kubernetes/
```

## Example Usage

Apply the manifests to create `ingestion`, `ai`, `security`, and
`visualization` namespaces with the SmartCito service workloads.
