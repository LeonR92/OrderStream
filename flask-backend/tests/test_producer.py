import pytest
import json
from unittest.mock import MagicMock, patch
from datetime import datetime
from event import KafkaEventPublisher  # Ensure correct import path

@pytest.fixture
def kafka_publisher():
    """Fixture to initialize KafkaEventPublisher with a mocked producer."""
    with patch("event.KafkaProducer") as MockKafkaProducer:
        mock_producer = MockKafkaProducer.return_value
        return KafkaEventPublisher(bootstrap_servers=["localhost:9092"], topic="test-topic")

def test_kafka_producer_initialization(kafka_publisher):
    """Test if Kafka producer initializes correctly."""
    assert kafka_publisher.producer is not None

def test_publish_event(kafka_publisher):
    """Test publishing an event."""
    kafka_publisher.producer.send = MagicMock()

    event_data = {"name": "Test Item"}
    result = kafka_publisher.publish_event("item_created", 1, event_data)

    assert result is True
    kafka_publisher.producer.send.assert_called_once()

    # Validate sent data
    _, kwargs = kafka_publisher.producer.send.call_args
    sent_data = kwargs["value"]
    assert sent_data["event_type"] == "item_created"
    assert sent_data["item_id"] == 1
    assert "timestamp" in sent_data
