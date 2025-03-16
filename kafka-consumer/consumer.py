import os
import json
import logging
import threading
import time
import queue
from datetime import datetime
from flask import Flask, render_template, Response, jsonify
from kafka_init import KafkaEventConsumer
from logger import logger

# Kafka configuration
KAFKA_BOOTSTRAP_SERVERS = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'kafka1:29092,kafka2:29093,kafka3:29094')
KAFKA_TOPIC = os.getenv('KAFKA_TOPIC', 'item-events')
KAFKA_GROUP_ID = os.getenv('KAFKA_GROUP_ID', 'item-consumer-group')

# Flask app
app = Flask(__name__, template_folder="templates")

# Shared data structures
events = []
events_lock = threading.Lock()
event_queue = queue.Queue()



# Initialize Kafka Consumer
kafka_consumer = KafkaEventConsumer(
    topic=KAFKA_TOPIC,
    bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
    group_id=KAFKA_GROUP_ID,
    event_store=events,
    event_queue=event_queue,
    event_lock=events_lock
)
kafka_consumer.start()


@app.route('/')
def index():
    """Serve the HTML page."""
    return render_template('index.html')


@app.route('/events')
def get_events():
    """Return current events as JSON."""
    with events_lock:
        return jsonify(events)


def generate_event_stream():
    """Generate events for Server-Sent Events (SSE)."""
    with events_lock:
        for event in events:
            yield f"data: {json.dumps(event)}\n\n"

    while True:
        try:
            event = event_queue.get(timeout=30)
            yield f"data: {json.dumps(event)}\n\n"
        except queue.Empty:
            yield ": keep-alive\n\n"


@app.route('/stream')
def stream():
    """Stream events using Server-Sent Events."""
    return Response(generate_event_stream(), mimetype="text/event-stream")


def generate_test_event() -> dict:
    """Generate a test event."""
    return {
        "event_type": "test_event",
        "item_id": 999,
        "timestamp": datetime.now().isoformat(),
        "data": {
            "id": 999,
            "name": "Test Item",
            "description": "This is a test item",
            "price": 99.99,
            "quantity": 10
        }
    }


@app.route('/test-event')
def test_event():
    """Add a test event."""
    test_data = generate_test_event()
    
    with events_lock:
        events.insert(0, test_data)
        if len(events) > 100:
            events.pop()
    
    event_queue.put(test_data)

    logger.info(f"Test event added: {test_data}")
    return jsonify({"status": "success", "message": "Test event added"})


if __name__ == '__main__':
    try:
        logger.info("Starting Flask server")
        app.run(host='0.0.0.0', port=5002, threaded=True, debug=True)
    finally:
        kafka_consumer.stop()  
