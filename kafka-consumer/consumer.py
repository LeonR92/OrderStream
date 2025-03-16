import os
import json
import logging
import threading
import time
from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit
from kafka import KafkaConsumer

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Kafka configuration
KAFKA_BOOTSTRAP_SERVERS = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'kafka1:29092,kafka2:29093,kafka3:29094')
KAFKA_TOPIC = os.getenv('KAFKA_TOPIC', 'item-events')
KAFKA_GROUP_ID = os.getenv('KAFKA_GROUP_ID', 'item-consumer-group')

# Flask app with WebSockets
app = Flask(__name__, template_folder="templates")
socketio = SocketIO(app, 
                    cors_allowed_origins="*", 
                    json=json,
                    logger=True, 
                    engineio_logger=True)

# Track clients by session ID
connected_clients = set()
clients_lock = threading.Lock()

# Flag to force events to be sent regardless of connection count
FORCE_EMIT = True

# Connection handlers for the events namespace
@socketio.on('connect', namespace='/events')
def events_connect():
    client_id = request.sid
    with clients_lock:
        connected_clients.add(client_id)
        client_count = len(connected_clients)
    
    logger.info(f"Client connected to /events namespace (ID: {client_id}). Active clients: {client_count}")
    emit('connection_response', {
        'status': 'connected', 
        'namespace': '/events',
        'client_id': client_id,
        'active_clients': client_count
    })

@socketio.on('disconnect', namespace='/events')
def events_disconnect():
    client_id = request.sid
    with clients_lock:
        if client_id in connected_clients:
            connected_clients.remove(client_id)
        client_count = len(connected_clients)
    
    logger.info(f"Client disconnected from /events namespace (ID: {client_id}). Active clients: {client_count}")

# Root namespace handlers for compatibility
@socketio.on('connect')
def connect():
    client_id = request.sid
    with clients_lock:
        connected_clients.add(client_id)
        client_count = len(connected_clients)
    
    logger.info(f"Client connected to root namespace (ID: {client_id}). Active clients: {client_count}")
    emit('connection_response', {
        'status': 'connected', 
        'namespace': 'root',
        'client_id': client_id,
        'active_clients': client_count
    })

@socketio.on('disconnect')
def disconnect():
    client_id = request.sid
    with clients_lock:
        if client_id in connected_clients:
            connected_clients.remove(client_id)
        client_count = len(connected_clients)
    
    logger.info(f"Client disconnected from root namespace (ID: {client_id}). Active clients: {client_count}")

# Ping handler to keep connections alive
@socketio.on('ping_server', namespace='/events')
def handle_ping_events():
    client_id = request.sid
    logger.info(f"Ping received from client (ID: {client_id}) on /events namespace")
    emit('pong', {'timestamp': time.time(), 'client_id': client_id})

@socketio.on('ping_server')
def handle_ping_root():
    client_id = request.sid
    logger.info(f"Ping received from client (ID: {client_id}) on root namespace")
    emit('pong', {'timestamp': time.time(), 'client_id': client_id})

def kafka_consumer():
    """Kafka consumer that emits events to websocket clients."""
    logger.info(f"Starting Kafka consumer for topic: {KAFKA_TOPIC}")
    
    # Give the server time to start
    time.sleep(3)
    
    while True:
        try:
            logger.info(f"Connecting to Kafka servers at {KAFKA_BOOTSTRAP_SERVERS}")
            consumer = KafkaConsumer(
                KAFKA_TOPIC,
                bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS.split(','),
                group_id=KAFKA_GROUP_ID,
                auto_offset_reset='latest',
                enable_auto_commit=True,
                value_deserializer=lambda x: json.loads(x.decode('utf-8')),
                key_deserializer=lambda x: x.decode('utf-8') if x else None
            )
            
            logger.info("Kafka consumer connected successfully. Waiting for messages...")
            
            for message in consumer:
                event_data = message.value
                logger.info(f"✅ Received from Kafka: {event_data}")
                
                with clients_lock:
                    client_count = len(connected_clients)
                
                if client_count > 0 or FORCE_EMIT:
                    try:
                        # Get the item ID in a safe way
                        item_id = None
                        if 'item_id' in event_data:
                            item_id = event_data['item_id']
                        elif 'data' in event_data and 'id' in event_data['data']:
                            item_id = event_data['data']['id']
                            
                        logger.info(f"Emitting event to {client_count} clients: {event_data.get('event_type')} - ID: {item_id}")
                        
                        # Send to both namespaces for maximum compatibility
                        socketio.emit('new_event', event_data, namespace='/events')
                        socketio.emit('new_event', event_data)
                        
                        logger.info(f"Event successfully emitted")
                    except Exception as e:
                        logger.error(f"Error emitting event: {e}")
                else:
                    logger.info("No active clients, skipping event emission")
        
        except Exception as e:
            logger.error(f"Kafka consumer error: {e}")
            time.sleep(5)  # Retry after 5 seconds

@app.route('/')
def index():
    """Serve the HTML page with WebSocket updates."""
    logger.info("Serving index page")
    return render_template('index.html')

@app.route('/test-event')
def test_event():
    """Send a test event via WebSocket."""
    test_data = {
        "event_type": "test_event",
        "item_id": 999,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "data": {
            "id": 999,
            "name": "Test Item",
            "description": "This is a test item",
            "price": 99.99,
            "quantity": 10
        }
    }
    
    # Send to both namespaces
    socketio.emit('new_event', test_data, namespace='/events')
    socketio.emit('new_event', test_data)
    
    logger.info(f"Test event emitted: {test_data}")
    return "Test event sent. Check your WebSocket client."

@app.route('/status')
def status():
    """Return the current connection status."""
    with clients_lock:
        client_count = len(connected_clients)
        clients_list = list(connected_clients)
    
    status_data = {
        "active_clients": client_count,
        "client_ids": clients_list,
        "force_emit": FORCE_EMIT
    }
    
    return json.dumps(status_data)

if __name__ == '__main__':
    # Start Kafka consumer in a separate thread
    consumer_thread = threading.Thread(target=kafka_consumer, daemon=True)
    consumer_thread.start()
    
    # Run the Flask-SocketIO server
    logger.info("Starting Flask-SocketIO server")
    socketio.run(app, host='0.0.0.0', port=5002, debug=True)