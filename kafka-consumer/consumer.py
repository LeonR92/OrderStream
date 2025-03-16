import os
import json
import logging
import threading
import time
from flask import Flask, render_template
from flask_socketio import SocketIO
from kafka import KafkaConsumer, KafkaError

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Kafka configuration
KAFKA_BOOTSTRAP_SERVERS = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'kafka1:29092,kafka2:29093,kafka3:29094')
KAFKA_TOPIC = os.getenv('KAFKA_TOPIC', 'item-events')
KAFKA_GROUP_ID = os.getenv('KAFKA_GROUP_ID', 'item-consumer-group')

# Flask app with WebSockets
app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")  # Allow any frontend to connect

def kafka_consumer():
    """Kafka consumer running in a separate thread, emitting messages via WebSockets."""
    logger.info(f"Starting Kafka consumer for topic: {KAFKA_TOPIC}")
    
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
            
            for message in consumer:
                event_data = message.value
                logger.info(f"New event: {event_data}")
                socketio.emit('new_event', event_data)  # Send data to connected clients
        
        except KafkaError as e:
            logger.error(f"Kafka consumer error: {e}")
            time.sleep(5)  # Retry after 5 seconds

# Start Kafka consumer in a separate thread
consumer_thread = threading.Thread(target=kafka_consumer, daemon=True)
consumer_thread.start()

# HTML template with WebSocket frontend
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Kafka Live Stream</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.js"></script>
    <script>
        var socket = io();
        socket.on('new_event', function(data) {
            var table = document.getElementById("events");
            var row = table.insertRow(1);
            row.insertCell(0).innerText = data.event_type;
            row.insertCell(1).innerText = data.data.id || 'N/A';
            row.insertCell(2).innerText = data.data.name || 'N/A';
            row.insertCell(3).innerText = data.data.price || 'N/A';
            row.insertCell(4).innerText = data.data.quantity || 'N/A';
        });
    </script>
</head>
<body>
    <h2>Live Kafka Events</h2>
    <table id="events" border="1">
        <tr>
            <th>Event Type</th>
            <th>Item ID</th>
            <th>Name</th>
            <th>Price</th>
            <th>Quantity</th>
        </tr>
    </table>
</body>
</html>
"""

@app.route('/')
def index():
    """Serve the HTML page with WebSocket updates."""
    return HTML_TEMPLATE

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5002, debug=True)
