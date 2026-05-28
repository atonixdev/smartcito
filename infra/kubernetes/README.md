# Kubernetes Infra

Kubernetes manifests for the Orca application layer and the connected
data-movement backbone.

## Purpose

Deploy Orca services, Memcached, Kafka, Spark Streaming, visualization,
logging, and supporting storage on a Kubernetes cluster that runs on OpenStack.

## Included platform layers

- Namespaces for backend, ingestion, AI, security, visualization, database, and data-platform workloads.
- Shared ConfigMap and Secret placeholders aligned with `.env.example`.
- Memcached cluster for shared low-latency caching and exporter metrics.
- OpenStack Cinder-backed persistent storage.
- Kafka KRaft cluster and topic bootstrap job.
- Spark master, workers, and a packaged streaming job image with checkpoint storage.
- Orca API and standalone Kafka consumer deployments.
- Plotly Dash, a private visualization gateway, and internal frontend exposure.
- Prometheus, Grafana, PostgreSQL and Kafka exporters, and node metrics collection.
- Elasticsearch, Kibana, and Fluent Bit for centralized platform logs.
- Network policies for internal-only traffic between ingestion, Kafka, Spark, backend, visualization, observability, and database.

## How To Run

```bash
cp .env.example .env
kubectl apply -f infra/kubernetes/namespaces.yaml
kubectl apply -f infra/kubernetes/platform-config.yaml
bash infra/kubernetes/apply-backend-secret.sh .env
kubectl apply -f infra/kubernetes/storage-openstack.yaml
kubectl apply -f infra/kubernetes/memcached-cluster.yaml
kubectl apply -f infra/kubernetes/plotly-dash.yaml
kubectl apply -f infra/kubernetes/observability-stack.yaml
kubectl apply -f infra/kubernetes/logging-stack.yaml
kubectl apply -f infra/kubernetes/visualization-gateway.yaml
kubectl apply -f infra/kubernetes/
```

Use the OpenStack cloud controller manager and Cinder CSI driver so
`LoadBalancer` services and `cinder-csi` persistent volumes are provisioned by
the underlying OpenStack cluster.

`infra/kubernetes/apply-backend-secret.sh` rebuilds the backend
`orca-platform-secrets` Secret from `.env`, including both the canonical
`OPENSTACK_*` variables used by Orca and `OS_*` aliases commonly expected
by OpenStack tooling.

Replace placeholder secrets such as Grafana admin credentials, PostgreSQL
passwords, and OpenStack network CIDRs before applying the manifests to a live
cluster.
