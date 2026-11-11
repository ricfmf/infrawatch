import json
import os
import time
import pika

RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "rabbitmq")
QUEUE_NAME = "alerts_queue"

def callback(ch, method, properties, body):
    try:
        alert = json.loads(body.decode("utf-8"))
        print("\n" + "="*50)
        print(" [!] ALERTA CRÍTICO RECEBIDO")
        print(f" Servidor : {alert.get('server_id')}")
        print(f" Tipo     : {alert.get('type')}")
        print(f" Valor    : {alert.get('value')}% (Limite: {alert.get('threshold')}%)")
        print("="*50 + "\n", flush=True)
        ch.basic_ack(delivery_tag=method.delivery_tag)
    except Exception as e:
        print(f"[ERRO] Falha ao processar mensagem: {e}", flush=True)

def connect_with_retry():
    while True:
        try:
            return pika.BlockingConnection(pika.ConnectionParameters(host=RABBITMQ_HOST))
        except pika.exceptions.AMQPConnectionError:
            print("[Aguardando] RabbitMQ indisponível. Tentando em 3s...", flush=True)
            time.sleep(3)

def main():
    print(f"[*] Iniciando Alert Service conectado em '{RABBITMQ_HOST}'...", flush=True)
    connection = connect_with_retry()
    channel = connection.channel()
    channel.queue_declare(queue=QUEUE_NAME, durable=True)
    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue=QUEUE_NAME, on_message_callback=callback)
    print(f"[*] Aguardando alertas na fila '{QUEUE_NAME}'.", flush=True)
    channel.start_consuming()

if __name__ == "__main__":
    main()
