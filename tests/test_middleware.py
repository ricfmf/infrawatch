import sys
import os
from unittest.mock import AsyncMock, patch
import pytest
from fastapi.testclient import TestClient
import httpx

# Adiciona o diretório do middleware ao PYTHONPATH
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "middleware")))
from main import app, EXPECTED_TOKEN

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy", "service": "middleware"}

def test_metrics_unauthorized_without_token():
    payload = {"server_id": "srv-test", "cpu_percent": 50.0, "memory_percent": 50.0, "status": "online"}
    response = client.post("/metrics", json=payload)
    assert response.status_code == 401
    assert "Não autorizado" in response.json()["detail"]

def test_metrics_unauthorized_invalid_token():
    payload = {"server_id": "srv-test", "cpu_percent": 50.0, "memory_percent": 50.0, "status": "online"}
    headers = {"Authorization": "Bearer token-invalido"}
    response = client.post("/metrics", json=payload, headers=headers)
    assert response.status_code == 401

def test_correlation_id_generated_and_propagated():
    response = client.get("/health")
    assert "x-correlation-id" in response.headers
    assert len(response.headers["x-correlation-id"]) > 0

@pytest.mark.asyncio
async def test_retry_mechanism_on_monitoring_service_down():
    # Simula falha contínua de conexão ao tentar encaminhar para o monitoring-service
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.side_effect = httpx.ConnectError("Connection refused")
        
        headers = {"Authorization": f"Bearer {EXPECTED_TOKEN}"}
        payload = {"server_id": "srv-test", "cpu_percent": 40.0, "memory_percent": 40.0, "status": "online"}
        
        response = client.post("/metrics", json=payload, headers=headers)
        
        # O middleware deve esgotar as 3 tentativas e responder HTTP 503
        assert response.status_code == 503
        assert mock_post.call_count == 3
        assert "indisponível após 3 tentativas" in response.json()["detail"]
