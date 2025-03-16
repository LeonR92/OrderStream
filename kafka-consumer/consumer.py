import os
import json
import logging
import threading
import time
from datetime import datetime
from flask import Flask, render_template, jsonify
from kafka import KafkaConsumer

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Kafka configuration
KAFKA_BOOTSTRAP_SERVERS = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'kafka1:29092,kafka2:29093,kafka3:29094')
KAFKA_TOPIC = os.getenv('KAFKA_TOPIC', 'item-events')
KAFKA_GROUP_ID = os.getenv('KAFKA_GROUP_ID', 'item-consumer-group')

# Flask app
app = Flask(__name__, template_folder="templates")

# In-memory storage for events (limit to last 100)
events = []
events_lock = threading.Lock()

def kafka_consumer():
    """Kafka consumer that stores events in memory."""
    logger.info(f"Starting Kafka consumer for topic: {KAFKA_TOPIC}")
    
    # Give the server time to start
    time.sleep(3)
    
    while True:
        try:
            consumer = KafkaConsumer(
                KAFKA_TOPIC,
                bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS.split(','),
                group_id=KAFKA_GROUP_ID,
                auto_offset_reset='latest',
                enable_auto_commit=True,
                value_deserializer=lambda x: json.loads(x.decode('utf-8')),
                key_deserializer=lambda x: x.decode('utf-8') if x else None
            )
            
            logger.info("Kafka consumer connected. Waiting for messages...")
            
            for message in consumer:
                event_data = message.value
                logger.info(f"Received from Kafka: {event_data}")
                
                with events_lock:
                    # Add to the beginning of the list
                    events.insert(0, event_data)
                    # Keep only the last 100 events
                    if len(events) > 100:
                        events.pop()
                
                logger.info(f"Event stored in memory. Total events: {len(events)}")
                
        except Exception as e:
            logger.error(f"Kafka consumer error: {e}")
            time.sleep(5)  # Retry after 5 seconds

@app.route('/')
def index():
    """Serve the HTML page."""
    return render_template('index.html')

@app.route('/events')
def get_events():
    """Return current events as JSON."""
    with events_lock:
        return jsonify(events)

@app.route('/test-event')
def test_event():
    """Add a test event."""
    test_data = {
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
    
    with events_lock:
        # Add to the beginning of the list
        events.insert(0, test_data)
        # Keep only the last 100 events
        if len(events) > 100:
            events.pop()
    
    logger.info(f"Test event added: {test_data}")
    return jsonify({"status": "success", "message": "Test event added"})

if __name__ == '__main__':
    # Start Kafka consumer in a separate thread
    consumer_thread = threading.Thread(target=kafka_consumer, daemon=True)
    consumer_thread.start()
    
    # Run the Flask server
    logger.info("Starting Flask server")
    app.run(host='0.0.0.0', port=5002, debug=True)