import random
from locust import HttpUser, task, between

class InfraWatchLoadUser(HttpUser):
    wait_time = between(0.5, 1.5)

    def on_start(self):
        self.headers = {
            "Authorization": "Bearer dev-token-123",
            "Content-Type": "application/json"
        }
        self.server_id = f"srv-load-{random.randint(1, 50):02d}"

    @task(8)
    def send_metrics(self):
        is_spike = random.random() < 0.15
        payload = {
            "server_id": self.server_id,
            "cpu_percent": round(random.uniform(85.0, 99.0) if is_spike else random.uniform(15.0, 65.0), 1),
            "memory_percent": round(random.uniform(85.0, 96.0) if is_spike else random.uniform(25.0, 70.0), 1),
            "status": "online"
        }
        with self.client.post("/metrics", json=payload, headers=self.headers, catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Falha HTTP {response.status_code}: {response.text}")

    @task(2)
    def check_stats(self):
        self.client.get("/stats")
