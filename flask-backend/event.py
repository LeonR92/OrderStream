import json
import logging
from datetime import datetime
from kafka import KafkaProducer, KafkaError
from typing import List, Optional

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class KafkaEventPublisher:
    """Handles Kafka event publishing for the application."""

    def __init__(self, bootstrap_servers: List[str], topic: str):
        """
        Initializes the Kafka producer.

        :param bootstrap_servers: List of Kafka bootstrap servers.
        :param topic: Kafka topic to publish events.
        """
        self.bootstrap_servers = bootstrap_servers
        self.topic = topic

        try:
            self.producer = KafkaProducer(
                bootstrap_servers=self.bootstrap_servers,
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                key_serializer=lambda v: str(v).encode('utf-8')
            )
            logger.info("Kafka producer initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Kafka producer: {e}")
            self.producer = None

    def publish_event(self, event_type: str, item_id: int, data: dict) -> bool:
        """Publishes an event to Kafka."""
        if not self.producer:
            logger.warning("Kafka producer not available, skipping event publishing")
            return False

        try:
            event = {
                'event_type': event_type,
                'item_id': item_id,
                'timestamp': datetime.utcnow().isoformat(),
                'data': data
            }

            future = self.producer.send(self.topic, key=item_id, value=event)
            record_metadata = future.get(timeout=10)

            logger.info(f"Event published: {event_type} - Partition: {record_metadata.partition}, Offset: {record_metadata.offset}")
            return True
        except KafkaError as e:
            logger.error(f"Failed to publish event: {e}")
            return False
