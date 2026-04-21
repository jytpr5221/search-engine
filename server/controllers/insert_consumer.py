from kafka import KafkaConsumer
from elasticsearch import Elasticsearch
import json

# Elasticsearch client
es = Elasticsearch("http://localhost:9200")

# Kafka consumer
consumer = KafkaConsumer(
    "sync_postgres_to_es",   # ✅ FIXED topic
    bootstrap_servers="localhost:9092",
    api_version=(0, 10),
    value_deserializer=lambda x: json.loads(x.decode('utf-8'))  # ✅ FIXED
)

print("Consumer started...")

for message in consumer:
    data = message.value

    print("Received:", data)

    if data.get("type") == "delete":
        # 🔥 DELETE in Elasticsearch
        es.delete(index="books", id=data["id"])
        print("Deleted from ES:", data["id"])

    else:
        # 🔥 INSERT / UPDATE
        es.index(
            index="books",
            id=data["id"],
            document=data
        )
        print("Indexed in ES:", data["id"])
