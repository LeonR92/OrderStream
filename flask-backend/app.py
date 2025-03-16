from flask import Flask, request, jsonify
import os
import logging
from datetime import datetime
from models import db, Item  
from event import KafkaEventPublisher  

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)

# Configure database
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URI')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database with Flask app
db.init_app(app)

# Kafka Configuration
KAFKA_BOOTSTRAP_SERVERS = os.environ.get('KAFKA_BOOTSTRAP_SERVERS', 'kafka1:29092,kafka2:29093,kafka3:29094').split(',')
KAFKA_TOPIC = os.environ.get('KAFKA_TOPIC', 'item-events')

event_publisher = KafkaEventPublisher(bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS, topic=KAFKA_TOPIC)

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy', 'timestamp': datetime.utcnow().isoformat()})

@app.route('/api/items', methods=['GET'])
def get_items():
    items = Item.get_all()
    return jsonify([item.to_dict() for item in items])

@app.route('/api/items/<int:item_id>', methods=['GET'])
def get_item(item_id):
    item = Item.get_by_id(item_id)
    if not item:
        return jsonify({'error': 'Item not found'}), 404
    return jsonify(item.to_dict())

@app.route('/api/items', methods=['POST'])
def create_item():
    data = request.get_json()
    
    for field in ['name', 'price', 'quantity']:
        if field not in data:
            return jsonify({'error': f"Missing required field: {field}"}), 400

    item = Item.create(data)
    if not item:
        return jsonify({'error': 'Error creating item'}), 500

    event_publisher.publish_event('item_created', item.id, item.to_dict())
    return jsonify(item.to_dict()), 201

@app.route('/api/items/<int:item_id>', methods=['PUT'])
def update_item(item_id):
    data = request.get_json()
    item = Item.update(item_id, data)

    if not item:
        return jsonify({'error': 'Item not found or update failed'}), 404

    event_publisher.publish_event('item_updated', item.id, item.to_dict())
    return jsonify(item.to_dict())

@app.route('/api/items/<int:item_id>', methods=['DELETE'])
def delete_item(item_id):
    success = Item.delete(item_id)

    if not success:
        return jsonify({'error': 'Item not found or deletion failed'}), 404

    event_publisher.publish_event('item_deleted', item_id, {})
    return jsonify({'message': f"Item {item_id} deleted successfully"})

# Create tables
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
