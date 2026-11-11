import os
import random
import time
import requests

MIDDLEWARE_URL = os.getenv("MIDDLEWARE_URL", "http://middleware:8000/metrics")
API_TOKEN = os.getenv("API_TOKEN", "dev-token-123")
INTERVAL_SECONDS = float(os.getenv("INTERVAL_SECONDS", "3.0"))

SERVERS = ["srv-web-01", "srv-db-01", "srv-worker-01"]
headers = {
    "Authorization": f"Bearer {API_TOKEN}",
    "Content-Type": "application/json"
}

def generate_metric(server_id: str) -> dict:
    is_spike = random.random() < 0.20
    if is_spike:
        cpu = round(random.uniform(85.0, 99.0), 1)
        mem = round(random.uniform(80.0, 96.0), 1)
    else:
        cpu = round(random.uniform(15.0, 60.0), 1)
        mem = round(random.uniform(30.0, 70.0), 1)
    return {
        "server_id": server_id,
        "cpu_percent": cpu,
        "memory_percent": mem,
        "status": "online"
    }

def main():
    print(f"[*] Simulador iniciado. Enviando para: {MIDDLEWARE_URL}", flush=True)
    time.sleep(3)
    while True:
        for srv in SERVERS:
            payload = generate_metric(srv)
            try:
                resp = requests.post(MIDDLEWARE_URL, json=payload, headers=headers, timeout=5.0)
                corr_id = resp.headers.get("X-Correlation-ID", "N/A")
                data = resp.json()
                print(f"[METRICA] {srv} | CPU: {payload['cpu_percent']}% | RAM: {payload['memory_percent']}% | Alertas: {data.get('alerts_generated')} | Corr-ID: {corr_id}", flush=True)
            except Exception as e:
                print(f"[ERRO] {srv}: {e}", flush=True)
        time.sleep(INTERVAL_SECONDS)

if __name__ == "__main__":
    main()
