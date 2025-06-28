from confluent_kafka import Producer
from app.core.config import kafka_producer_config

producer = Producer(**kafka_producer_config)

def producer_delivery_report(err, msg):
    if err:
        print("Error while sendind message,", err)
    else:
        print("Message successsfully sended")
