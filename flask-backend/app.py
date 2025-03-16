from flask import Flask, render_template, request, jsonify
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

@app.route("/")
def show_order_form():
    return render_template("index.html")


@app.route('/api/items', methods=['POST'])
def create_item():
    data = request.form

    # Required fields
    required_fields = ['first-name', 'price', 'quantity']
    
    missing_fields = [field for field in required_fields if not data.get(field)]
    if missing_fields:
        return jsonify({'error': f"Missing required fields: {', '.join(missing_fields)}"}), 400

    try:
        item_data = {
            'name': data.get('first-name'),
            'description': data.get('description'),
            'quantity': int(data.get('quantity', 1)),
            'price': float(data.get('price', 0.0))
        }
    except ValueError:
        return jsonify({'error': 'Invalid data type for price or quantity'}), 400

    item = Item.create(item_data)
    if not item:
        return jsonify({'error': 'Error creating item'}), 500

    # Publish event
    event_publisher.publish_event('item_created', item.id, item.to_dict())

    return jsonify("succesfully added item. Go to http://localhost:5002/ to see the live results or go back to add a new one"), 201



# Create tables
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
