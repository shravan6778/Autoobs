# AutoObs: Agentic Observability Platform

AutoObs is an AI-first observability platform that transforms raw telemetry into actionable root-cause analysis and one-click fixes.

## Architecture

- **Data Collection:** eBPF & OpenTelemetry (OTel) via DaemonSet.
- **Storage:** Prometheus (Metrics), Loki (Logs), Tempo (Traces).
- **Streaming:** Redpanda.
- **AI Engine:** Ollama (Mistral) running in-cluster.
- **Backend:** FastAPI (Multi-tenant).
- **Frontend:** React + Vite + Tailwind.

## Prerequisites

- Kubernetes (Minikube/Kind)
- kubectl

## Installation

To install the core infrastructure and telemetry pipelines into your cluster:

```bash
kubectl apply -f k8s/install.yaml
```

This sets up the `autoobs` namespace, the storage engines, Redpanda, Ollama, and the privileged OTel/eBPF DaemonSet for data collection.
