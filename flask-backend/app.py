import os
import json
import logging
from datetime import datetime
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from kafka import KafkaProducer
from kafka.errors import KafkaError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)

# Configure database
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
    'DATABASE_URI', 'postgresql://postgres:postgres@postgres:5432/itemsdb'
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Kafka configuration
KAFKA_BOOTSTRAP_SERVERS = os.environ.get('KAFKA_BOOTSTRAP_SERVERS', 'kafka1:29092,kafka2:29093,kafka3:29094')
KAFKA_TOPIC = os.environ.get('KAFKA_TOPIC', 'item-events')

# Initialize Kafka producer
try:
    producer = KafkaProducer(
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS.split(','),
        value_serializer=lambda v: json.dumps(v).encode('utf-8'),
        key_serializer=lambda v: str(v).encode('utf-8')
    )
    logger.info("Kafka producer initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize Kafka producer: {e}")
    producer = None

# Define item model
class Item(db.Model):
    __tablename__ = 'items'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'price': float(self.price),
            'quantity': self.quantity,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

# Publish event to Kafka
def publish_event(event_type, item_id, data):
    if not producer:
        logger.warning("Kafka producer not available, skipping event publishing")
        return False
        
    try:
        event = {
            'event_type': event_type,
            'item_id': item_id,
            'timestamp': datetime.utcnow().isoformat(),
            'data': data
        }
        
        future = producer.send(KAFKA_TOPIC, key=item_id, value=event)
        record_metadata = future.get(timeout=10)
        
        logger.info(f"Event published: {event_type} - Partition: {record_metadata.partition}, Offset: {record_metadata.offset}")
        return True
    except KafkaError as e:
        logger.error(f"Failed to publish event: {e}")
        return False

# API Routes
@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy', 'timestamp': datetime.utcnow().isoformat()})

@app.route('/api/items', methods=['GET'])
def get_items():
    items = Item.query.all()
    return jsonify([item.to_dict() for item in items])

@app.route('/api/items/<int:item_id>', methods=['GET'])
def get_item(item_id):
    item = Item.query.get_or_404(item_id)
    return jsonify(item.to_dict())

@app.route('/api/items', methods=['POST'])
def create_item():
    data = request.get_json()
    
    # Validate required fields
    for field in ['name', 'price', 'quantity']:
        if field not in data:
            return jsonify({'error': f"Missing required field: {field}"}), 400
    
    try:
        # Create new item
        item = Item(
            name=data['name'],
            description=data.get('description', ''),
            price=data['price'],
            quantity=data['quantity']
        )
        
        db.session.add(item)
        db.session.commit()
        
        # Publish event
        publish_event('item_created', item.id, item.to_dict())
        
        return jsonify(item.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating item: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/items/<int:item_id>', methods=['PUT'])
def update_item(item_id):
    item = Item.query.get_or_404(item_id)
    data = request.get_json()
    
    try:
        # Update fields
        if 'name' in data:
            item.name = data['name']
        if 'description' in data:
            item.description = data['description']
        if 'price' in data:
            item.price = data['price']
        if 'quantity' in data:
            item.quantity = data['quantity']
        
        db.session.commit()
        
        # Publish event
        publish_event('item_updated', item.id, item.to_dict())
        
        return jsonify(item.to_dict())
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating item: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/items/<int:item_id>', methods=['DELETE'])
def delete_item(item_id):
    item = Item.query.get_or_404(item_id)
    
    try:
        item_data = item.to_dict()
        
        db.session.delete(item)
        db.session.commit()
        
        # Publish event
        publish_event('item_deleted', item_id, item_data)
        
        return jsonify({'message': f"Item {item_id} deleted successfully"})
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting item: {e}")
        return jsonify({'error': str(e)}), 500

# Create all tables
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)