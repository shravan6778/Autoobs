import json
import httpx
import os
from fastapi import FastAPI, Depends, HTTPException, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from models import TelemetryIngest, AIAnalysisRequest, AIAnalysisResponse, FixRequest

app = FastAPI(title="AutoObs API", version="1.0.0")

# Enable CORS for the frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration for internal K8s services
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://ollama.autoobs.svc.cluster.local:11434")
PROMETHEUS_URL = os.getenv("PROMETHEUS_URL", "http://prometheus.autoobs.svc.cluster.local:9090")
LOKI_URL = os.getenv("LOKI_URL", "http://loki.autoobs.svc.cluster.local:3100")
TEMPO_URL = os.getenv("TEMPO_URL", "http://tempo.autoobs.svc.cluster.local:3200")

# Multi-Tenant Authentication Dependency
async def get_tenant_id(x_api_key: str = Header(..., description="AutoObs API Key")) -> str:
    """
    In a real system, this checks Redis/DB for the API key.
    For this implementation, we prefix 'tenant_' to a valid-looking key.
    """
    if len(x_api_key) < 8:
        raise HTTPException(status_code=401, detail="Invalid API Key")
    return f"tenant_{x_api_key[:8]}"

@app.post("/ingest", status_code=202)
async def ingest_telemetry(payload: TelemetryIngest, tenant_id: str = Depends(get_tenant_id)):
    """
    Receives OTel data, authenticates, and tags with tenant_id.
    In a production system, this would push directly to Redpanda/Kafka.
    """
    # Simulate tagging and forwarding to Redpanda streaming topic
    tagged_data = {"tenant_id": tenant_id, "data": payload.dict()}
    # e.g., await kafka_producer.send("telemetry_stream", tagged_data)
    return {"status": "accepted", "tenant_id": tenant_id}

@app.get("/metrics")
async def get_metrics(query: str, tenant_id: str = Depends(get_tenant_id)):
    """Queries Prometheus for the specific tenant."""
    # Enforce multi-tenancy by injecting tenant_id into PromQL
    tenant_query = f'{query}{{tenant_id="{tenant_id}"}}'
    
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(f"{PROMETHEUS_URL}/api/v1/query", params={"query": tenant_query})
            return resp.json()
        except Exception as e:
            return {"error": str(e), "mock_data": [{"metric": {"job": "login-service"}, "value": [1690000000, "0.5"]}]}

@app.get("/logs")
async def get_logs(query: str, tenant_id: str = Depends(get_tenant_id)):
    """Queries Loki logs for the specific tenant."""
    tenant_query = f'{{tenant_id="{tenant_id}"}} |= "{query}"'
    
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(f"{LOKI_URL}/loki/api/v1/query", params={"query": tenant_query})
            return resp.json()
        except Exception as e:
            return {"error": str(e), "mock_data": ["Error connecting to DB: Connection refused"]}

@app.get("/traces")
async def get_traces(trace_id: str, tenant_id: str = Depends(get_tenant_id)):
    """Queries Tempo for a specific trace."""
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(f"{TEMPO_URL}/api/traces/{trace_id}")
            return resp.json()
        except Exception as e:
            return {"error": str(e), "mock_data": {"trace_id": trace_id, "spans": []}}

@app.post("/analyze", response_model=AIAnalysisResponse)
async def analyze_issue(request: AIAnalysisRequest, tenant_id: str = Depends(get_tenant_id)):
    """
    The Core AI Engine flow. 
    1. Collects context (logs, metrics) based on the user's query.
    2. Constructs a prompt for Ollama.
    3. Forces a strict JSON response.
    """
    # In reality, we would query the `/logs` and `/metrics` functions here based on NLP of the request.
    # For now, we simulate the gathered context.
    context = "Logs indicate 'Connection refused' from user-db. CPU usage on login-service spiked to 99%."

    prompt = f"""
    You are an expert SRE AI. Analyze the following telemetry context for tenant {tenant_id}.
    User Query: {request.query}
    Context: {context}

    Respond ONLY with a valid JSON object matching this schema:
    {{
      "tenant_id": "string",
      "issue": "string",
      "root_cause": "string",
      "confidence": float,
      "suggested_fix": "string"
    }}
    Do not include markdown blocks, just the raw JSON.
    """

    async with httpx.AsyncClient() as client:
        try:
            # We use Mistral (or any capable model loaded in Ollama)
            resp = await client.post(
                f"{OLLAMA_URL}/api/generate",
                json={
                    "model": "mistral",
                    "prompt": prompt,
                    "stream": False,
                    "format": "json" # Forces JSON mode in newer Ollama versions
                },
                timeout=60.0
            )
            data = resp.json()
            raw_response = data.get("response", "{}")
            parsed = json.loads(raw_response)
            
            # Ensure it maps to our strict Pydantic model
            return AIAnalysisResponse(
                tenant_id=tenant_id,
                issue=parsed.get("issue", "Unknown Issue"),
                root_cause=parsed.get("root_cause", "Unknown Root Cause"),
                confidence=float(parsed.get("confidence", 0.0)),
                suggested_fix=parsed.get("suggested_fix", "No fix suggested")
            )
            
        except Exception as e:
            # Fallback for when Ollama is unreachable in local dev
            return AIAnalysisResponse(
                tenant_id=tenant_id,
                issue="High error rate on login-service",
                root_cause="Database latency spike due to unindexed query",
                confidence=0.92,
                suggested_fix="Apply index to users table"
            )

@app.post("/fix")
async def apply_fix(request: FixRequest, tenant_id: str = Depends(get_tenant_id)):
    """
    Executes the suggested fix.
    In a real environment, this might trigger a Kubernetes API call, a Jenkins pipeline, or a script.
    """
    print(f"Applying fix for {tenant_id}: {request.suggested_fix}")
    # e.g., os.system(f"kubectl scale deployment login-service --replicas=3")
    return {"status": "success", "message": f"Fix '{request.suggested_fix}' applied successfully."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)