import os
import json
import logging
import time
from datetime import datetime
from kafka import KafkaConsumer
from kafka.errors import KafkaError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Kafka configuration
KAFKA_BOOTSTRAP_SERVERS = os.environ.get('KAFKA_BOOTSTRAP_SERVERS', 'kafka1:29092,kafka2:29093,kafka3:29094')
KAFKA_TOPIC = os.environ.get('KAFKA_TOPIC', 'item-events')
KAFKA_GROUP_ID = os.environ.get('KAFKA_GROUP_ID', 'item-consumer-group')

def process_item_created(event_data):
    """Process item created event"""
    item = event_data.get('data', {})
    logger.info(f"Item Created: ID={item.get('id')}, Name={item.get('name')}, Price=${item.get('price')}")

def process_item_updated(event_data):
    """Process item updated event"""
    item = event_data.get('data', {})
    logger.info(f"Item Updated: ID={item.get('id')}, Name={item.get('name')}, New Price=${item.get('price')}, Quantity={item.get('quantity')}")

def process_item_deleted(event_data):
    """Process item deleted event"""
    item = event_data.get('data', {})
    logger.info(f"Item Deleted: ID={item.get('id')}, Name={item.get('name')}")

def process_event(event_data):
    """Process event based on event type"""
    event_type = event_data.get('event_type')
    
    if event_type == 'item_created':
        process_item_created(event_data)
    elif event_type == 'item_updated':
        process_item_updated(event_data)
    elif event_type == 'item_deleted':
        process_item_deleted(event_data)
    else:
        logger.warning(f"Unknown event type: {event_type}")

def start_consumer():
    """Start Kafka consumer"""
    logger.info(f"Starting Kafka consumer - Group: {KAFKA_GROUP_ID}, Topic: {KAFKA_TOPIC}")
    
    # Initialize consumer with retry logic
    max_retries = 10
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            consumer = KafkaConsumer(
                KAFKA_TOPIC,
                bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS.split(','),
                group_id=KAFKA_GROUP_ID,
                auto_offset_reset='earliest',
                enable_auto_commit=True,
                value_deserializer=lambda x: json.loads(x.decode('utf-8')),
                key_deserializer=lambda x: x.decode('utf-8') if x else None
            )
            
            logger.info("Kafka consumer initialized successfully")
            break
        except KafkaError as e:
            logger.error(f"Failed to initialize Kafka consumer: {e}")
            retry_count += 1
            wait_time = 5 * retry_count
            logger.info(f"Retrying in {wait_time} seconds (attempt {retry_count}/{max_retries})...")
            time.sleep(wait_time)
    
    if retry_count >= max_retries:
        logger.error("Failed to initialize Kafka consumer after multiple retries")
        return
    
    # Process messages
    try:
        for message in consumer:
            logger.debug(f"Received message - Partition: {message.partition}, Offset: {message.offset}")
            
            try:
                event_data = message.value
                process_event(event_data)
            except Exception as e:
                logger.error(f"Error processing message: {e}")
    except KafkaError as e:
        logger.error(f"Kafka consumer error: {e}")
    finally:
        logger.info("Closing Kafka consumer")
        if 'consumer' in locals():
            consumer.close()

if __name__ == "__main__":
    start_consumer()