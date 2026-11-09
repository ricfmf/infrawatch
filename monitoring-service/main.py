import json
import os
import pika
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

app = FastAPI(title="InfraWatch Monitoring Service")

RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "rabbitmq")
QUEUE_NAME = "alerts_queue"

class ServerMetric(BaseModel):
    server_id: str = Field(..., example="srv-node-01")
    cpu_percent: float = Field(..., ge=0, le=100, example=85.5)
    memory_percent: float = Field(..., ge=0, le=100, example=70.0)
    status: str = Field(..., example="online")

def publish_alert(alert_payload: dict):
    try:
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(host=RABBITMQ_HOST)
        )
        channel = connection.channel()
        channel.queue_declare(queue=QUEUE_NAME, durable=True)
        channel.basic_publish(
            exchange="",
            routing_key=QUEUE_NAME,
            body=json.dumps(alert_payload),
            properties=pika.BasicProperties(
                delivery_mode=pika.DeliveryMode.Persistent
            )
        )
        connection.close()
    except Exception as e:
        print(f"[ERRO] Falha ao enviar alerta para o RabbitMQ: {e}")

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "monitoring-service"}

@app.post("/metrics")
def receive_metrics(metric: ServerMetric):
    alerts_triggered = []

    if metric.cpu_percent > 80.0:
        alerts_triggered.append({
            "type": "HIGH_CPU_USAGE",
            "server_id": metric.server_id,
            "value": metric.cpu_percent,
            "threshold": 80.0
        })

    if metric.memory_percent > 85.0:
        alerts_triggered.append({
            "type": "HIGH_MEMORY_USAGE",
            "server_id": metric.server_id,
            "value": metric.memory_percent,
            "threshold": 85.0
        })

    for alert in alerts_triggered:
        publish_alert(alert)

    return {
        "status": "processed",
        "server_id": metric.server_id,
        "alerts_generated": len(alerts_triggered)
    }
