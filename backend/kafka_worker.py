from kafka import KafkaConsumer
import json
from utils.file_loader import parse_pdf_text
from services.vector_search import add_to_index


consumer = KafkaConsumer(
    'doc-upload',
    bootstrap_servers='localhost:9092',
    group_id='embedder',
    value_deserializer=lambda m: json.loads(m.decode('utf-8'))
    )

 

for msg in consumer:
    text = parse_pdf_text('backend/uploads/'+msg.value['filename'])
    add_to_index(text)
    print(f"[Kafka] Indexed {msg.value['filename']}")