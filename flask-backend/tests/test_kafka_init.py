from unittest.mock import MagicMock, patch
from event import KafkaEventPublisher  

def test_kafka_producer_initialization():
    """Test if Kafka producer initializes correctly."""
    with patch("event.KafkaProducer") as MockKafkaProducer:
        mock_producer = MockKafkaProducer.return_value
        publisher = KafkaEventPublisher(bootstrap_servers=["localhost:9092"], topic="test-topic")

        assert publisher.producer is mock_producer  

def test_publish_event():
    """Test publishing an event."""
    with patch("event.KafkaProducer") as MockKafkaProducer:
        mock_producer = MockKafkaProducer.return_value
        mock_producer.send = MagicMock()  

        publisher = KafkaEventPublisher(bootstrap_servers=["localhost:9092"], topic="test-topic")

        event_data = {"name": "Test Item"}
        result = publisher.publish_event("item_created", 1, event_data)

        assert result is True
        mock_producer.send.assert_called_once()

        _, kwargs = mock_producer.send.call_args
        sent_data = kwargs["value"]
        assert sent_data["event_type"] == "item_created"
        assert sent_data["item_id"] == 1
        assert "timestamp" in sent_data
