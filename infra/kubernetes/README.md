# Kubernetes Infra

Kubernetes manifests for the SmartCito application layer and the connected
data-movement backbone.

## Purpose

Deploy SmartCito services, Memcached, Kafka, Spark Streaming, visualization,
logging, and supporting storage on a Kubernetes cluster that runs on OpenStack.

## Included platform layers

- Namespaces for backend, ingestion, AI, security, visualization, database, and data-platform workloads.
- Shared ConfigMap and Secret placeholders aligned with `.env.example`.
- Memcached cluster for shared low-latency caching and exporter metrics.
- OpenStack Cinder-backed persistent storage.
- Kafka KRaft cluster and topic bootstrap job.
- Spark master, workers, and a packaged streaming job image with checkpoint storage.
- SmartCito API and standalone Kafka consumer deployments.
- Plotly Dash, a private visualization gateway, and internal frontend exposure.
- Prometheus, Grafana, PostgreSQL and Kafka exporters, and node metrics collection.
- Elasticsearch, Kibana, and Fluent Bit for centralized platform logs.
- Network policies for internal-only traffic between ingestion, Kafka, Spark, backend, visualization, observability, and database.

## How To Run

```bash
kubectl apply -f infra/kubernetes/namespaces.yaml
kubectl apply -f infra/kubernetes/platform-config.yaml
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

Replace placeholder secrets such as Grafana admin credentials, PostgreSQL
passwords, and OpenStack network CIDRs before applying the manifests to a live
cluster.
