import json
import logging
import queue
import threading
import time
from logger import logger
from kafka import KafkaConsumer



class KafkaEventConsumer:
    """Encapsulates Kafka consumer functionality."""

    def __init__(self, topic: str, bootstrap_servers: str, group_id: str, 
                 event_store: list, event_queue: queue.Queue, event_lock: threading.Lock):
        self.topic = topic
        self.bootstrap_servers = bootstrap_servers
        self.group_id = group_id
        self.event_store = event_store
        self.event_queue = event_queue
        self.event_lock = event_lock
        self.consumer = None
        self.thread = threading.Thread(target=self._consume_messages, daemon=True)
        self.running = False

    def _initialize_consumer(self) -> KafkaConsumer:
        """Initialize and return a Kafka consumer."""
        return KafkaConsumer(
            self.topic,
            bootstrap_servers=self.bootstrap_servers.split(','),
            group_id=self.group_id,
            auto_offset_reset='latest',
            enable_auto_commit=True,
            value_deserializer=lambda x: json.loads(x.decode('utf-8')),
            key_deserializer=lambda x: x.decode('utf-8') if x else None
        )

    def _store_event(self, event_data: dict):
        """Store event in memory and maintain only the latest 100 events."""
        with self.event_lock:
            self.event_store.insert(0, event_data)
            if len(self.event_store) > 100:
                self.event_store.pop()

    def _consume_messages(self):
        """Continuously consume Kafka messages and store them."""
        logger.info(f"Starting Kafka consumer for topic: {self.topic}")
        time.sleep(3)  

        while self.running:
            try:
                self.consumer = self._initialize_consumer()
                logger.info("Kafka consumer connected. Waiting for messages...")

                for message in self.consumer:
                    if not self.running:
                        break

                    event_data = message.value
                    logger.info(f"Received from Kafka: {event_data}")

                    self._store_event(event_data)
                    self.event_queue.put(event_data)

                    logger.info(f"Event stored. Total events: {len(self.event_store)}")

            except Exception as e:
                logger.error(f"Kafka consumer error: {e}")
                time.sleep(5)  # Retry on failure

    def start(self):
        """Start the Kafka consumer thread."""
        if not self.running:
            self.running = True
            self.thread.start()
            logger.info("Kafka consumer thread started.")

    def stop(self):
        """Stop the Kafka consumer thread."""
        self.running = False
        if self.consumer:
            self.consumer.close()
        logger.info("Kafka consumer stopped.")