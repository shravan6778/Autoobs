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
- Python 3.11+ (Tested on Python 3.13)
- Node.js 18+ & npm (for frontend)

## Step 1: Infrastructure Installation

To install the core infrastructure and telemetry pipelines into your Kubernetes cluster:

```bash
kubectl apply -f k8s/install.yaml
```

This sets up the `autoobs` namespace, the storage engines, Redpanda, Ollama, and the privileged OTel/eBPF DaemonSet for data collection.

## Step 2: Backend API Setup

The backend is a multi-tenant FastAPI application that handles telemetry ingestion, querying the K8s observability stack, and orchestrating the AI root-cause analysis via Ollama.

### Running Locally

Navigate to the `backend` directory and set up your Python environment:

```bash
cd backend

# Create and activate a virtual environment
python -m venv myvenv

# On Windows:
myvenv\Scripts\activate
# On macOS/Linux:
# source myvenv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start the server
python main.py
```

The API will be available at `http://localhost:8000`.
You can view the interactive Swagger UI documentation at `http://localhost:8000/docs`.

### Key Endpoints

All endpoints require an `x-api-key` header for multi-tenant isolation.

- `POST /ingest`: Receives OTel telemetry data and tags it with the tenant ID.
- `GET /metrics`, `GET /logs`, `GET /traces`: Queries Prometheus, Loki, and Tempo strictly scoped to the tenant.
- `POST /analyze`: Compiles context and triggers the Ollama AI engine to determine root cause and suggest a structured JSON fix.
- `POST /fix`: Executes the AI-suggested remediation.
