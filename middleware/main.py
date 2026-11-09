import asyncio
import logging
import os
import time
import uuid
import httpx
from fastapi import FastAPI, Header, HTTPException, Request, Response
from fastapi.responses import JSONResponse

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("infrawatch-middleware")

app = FastAPI(title="InfraWatch Custom Middleware")

MONITORING_SERVICE_URL = os.getenv("MONITORING_SERVICE_URL", "http://monitoring-service:8001")
EXPECTED_TOKEN = os.getenv("API_TOKEN", "dev-token-123")
MAX_RETRIES = 3
INITIAL_BACKOFF = 0.5

@app.middleware("http")
async def correlation_and_logging_middleware(request: Request, call_next):
    correlation_id = request.headers.get("X-Correlation-ID") or str(uuid.uuid4())
    request.state.correlation_id = correlation_id
    start_time = time.time()

    logger.info(f"[INÍCIO] {request.method} {request.url.path} | Correlation-ID: {correlation_id}")
    
    response = await call_next(request)
    
    duration_ms = round((time.time() - start_time) * 1000, 2)
    response.headers["X-Correlation-ID"] = correlation_id
    logger.info(f"[FIM] {request.method} {request.url.path} | Status: {response.status_code} | Duração: {duration_ms}ms | Correlation-ID: {correlation_id}")
    
    return response

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "middleware"}

@app.post("/metrics")
async def proxy_metrics(request: Request, authorization: str = Header(None)):
    correlation_id = request.state.correlation_id

    # 1. Autenticação
    if not authorization or authorization != f"Bearer {EXPECTED_TOKEN}":
        logger.warning(f"[AUTH FALHOU] Token ausente ou inválido | Correlation-ID: {correlation_id}")
        raise HTTPException(status_code=401, detail="Não autorizado: Bearer token ausente ou inválido")

    body = await request.body()
    forward_headers = {
        "Content-Type": "application/json",
        "X-Correlation-ID": correlation_id
    }

    # 2. Encaminhamento com Resiliência (Timeout e Retry com Backoff)
    async with httpx.AsyncClient(timeout=3.0) as client:
        last_error = None
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                target_url = f"{MONITORING_SERVICE_URL}/metrics"
                logger.info(f"[FORWARD] Tentativa {attempt}/{MAX_RETRIES} -> {target_url} | Correlation-ID: {correlation_id}")
                
                resp = await client.post(target_url, content=body, headers=forward_headers)
                
                if resp.status_code < 500:
                    return JSONResponse(status_code=resp.status_code, content=resp.json())
                
                last_error = f"Status {resp.status_code}: {resp.text}"
            except (httpx.ConnectError, httpx.TimeoutException) as exc:
                last_error = str(exc)
            
            logger.warning(f"[RETRY] Tentativa {attempt} falhou ({last_error}). Tentando novamente...")
            await asyncio.sleep(INITIAL_BACKOFF * (2 ** (attempt - 1)))

    raise HTTPException(status_code=503, detail=f"Monitoring Service indisponível após {MAX_RETRIES} tentativas: {last_error}")
