import asyncio
import logging
import os
import time
import uuid
import httpx
from fastapi import FastAPI, Header, HTTPException, Request, Response
from fastapi.responses import JSONResponse
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("infrawatch-middleware")

app = FastAPI(title="InfraWatch Custom Middleware")

MONITORING_SERVICE_URL = os.getenv("MONITORING_SERVICE_URL", "http://monitoring-service:8001")
EXPECTED_TOKEN = os.getenv("API_TOKEN", "dev-token-123")
MAX_RETRIES = 3
INITIAL_BACKOFF = 0.5

# Métricas em memória para o endpoint /stats
METRICS_DATA = {
    "total_requests": 0,
    "authorized_requests": 0,
    "unauthorized_requests": 0,
    "successful_forwards": 0,
    "failed_forwards": 0,
    "total_retries": 0,
    "total_duration_ms": 0.0
}

# Métricas oficiais do Prometheus
PROM_REQUESTS = Counter("infrawatch_requests_total", "Total de requisições no middleware", ["method", "endpoint", "status"])
PROM_RETRIES = Counter("infrawatch_retries_total", "Total de retentativas feitas ao monitoring-service")
PROM_LATENCY = Histogram("infrawatch_request_duration_seconds", "Latência das requisições em segundos", ["endpoint"])

@app.middleware("http")
async def correlation_and_logging_middleware(request: Request, call_next):
    correlation_id = request.headers.get("X-Correlation-ID") or str(uuid.uuid4())
    request.state.correlation_id = correlation_id
    start_time = time.time()

    METRICS_DATA["total_requests"] += 1
    logger.info(f"[INÍCIO] {request.method} {request.url.path} | Correlation-ID: {correlation_id}")
    
    response = await call_next(request)
    
    duration_sec = time.time() - start_time
    duration_ms = round(duration_sec * 1000, 2)
    METRICS_DATA["total_duration_ms"] += duration_ms

    # Registra no Prometheus (ignora o próprio scraping para não poluir)
    if request.url.path != "/prometheus":
        PROM_REQUESTS.labels(method=request.method, endpoint=request.url.path, status=response.status_code).inc()
        PROM_LATENCY.labels(endpoint=request.url.path).observe(duration_sec)

    response.headers["X-Correlation-ID"] = correlation_id
    logger.info(f"[FIM] {request.method} {request.url.path} | Status: {response.status_code} | Duração: {duration_ms}ms | Correlation-ID: {correlation_id}")
    
    return response

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "middleware"}

@app.get("/stats")
def get_metrics():
    avg_latency = 0.0
    if METRICS_DATA["total_requests"] > 0:
        avg_latency = round(METRICS_DATA["total_duration_ms"] / METRICS_DATA["total_requests"], 2)
    return {
        **METRICS_DATA,
        "average_latency_ms": avg_latency
    }

@app.get("/prometheus")
def prometheus_metrics():
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)

@app.post("/metrics")
async def proxy_metrics(request: Request, authorization: str = Header(None)):
    correlation_id = request.state.correlation_id

    if not authorization or authorization != f"Bearer {EXPECTED_TOKEN}":
        METRICS_DATA["unauthorized_requests"] += 1
        logger.warning(f"[AUTH FALHOU] Token ausente ou inválido | Correlation-ID: {correlation_id}")
        raise HTTPException(status_code=401, detail="Não autorizado: Bearer token ausente ou inválido")

    METRICS_DATA["authorized_requests"] += 1
    body = await request.body()
    forward_headers = {
        "Content-Type": "application/json",
        "X-Correlation-ID": correlation_id
    }

    async with httpx.AsyncClient(timeout=3.0) as client:
        last_error = None
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                target_url = f"{MONITORING_SERVICE_URL}/metrics"
                logger.info(f"[FORWARD] Tentativa {attempt}/{MAX_RETRIES} -> {target_url} | Correlation-ID: {correlation_id}")
                
                resp = await client.post(target_url, content=body, headers=forward_headers)
                
                if resp.status_code < 500:
                    METRICS_DATA["successful_forwards"] += 1
                    return JSONResponse(status_code=resp.status_code, content=resp.json())
                
                last_error = f"Status {resp.status_code}: {resp.text}"
            except (httpx.ConnectError, httpx.TimeoutException) as exc:
                last_error = str(exc)
            
            METRICS_DATA["total_retries"] += 1
            PROM_RETRIES.inc()
            logger.warning(f"[RETRY] Tentativa {attempt} falhou ({last_error}). Aguardando backoff...")
            await asyncio.sleep(INITIAL_BACKOFF * (2 ** (attempt - 1)))

    METRICS_DATA["failed_forwards"] += 1
    raise HTTPException(status_code=503, detail=f"Monitoring Service indisponível após {MAX_RETRIES} tentativas: {last_error}")
