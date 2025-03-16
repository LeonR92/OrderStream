import json
import queue
import threading
import pytest
from unittest.mock import patch, MagicMock
from kafka_client import KafkaEventConsumer  


@pytest.fixture
def kafka_consumer():
    """Fixture to initialize KafkaEventConsumer with mock dependencies."""
    event_store = []
    event_queue = queue.Queue()
    event_lock = threading.Lock()

    consumer = KafkaEventConsumer(
        topic="test-topic",
        bootstrap_servers="localhost:9092",
        group_id="test-group",
        event_store=event_store,
        event_queue=event_queue,
        event_lock=event_lock
    )
    return consumer, event_store, event_queue


def test_kafka_consumer_initialization(kafka_consumer):
    """Test if Kafka consumer initializes correctly."""
    consumer, event_store, event_queue = kafka_consumer

    assert consumer.topic == "test-topic"
    assert consumer.bootstrap_servers == "localhost:9092"
    assert consumer.group_id == "test-group"
    assert consumer.event_store == event_store
    assert consumer.event_queue == event_queue
    assert consumer.consumer is None  
    assert not consumer.running  


@patch("event.KafkaConsumer")
def test_kafka_message_consumption(MockKafkaConsumer, kafka_consumer):
    """Test Kafka consumer message handling."""
    consumer, event_store, event_queue = kafka_consumer

    mock_consumer_instance = MockKafkaConsumer.return_value
    mock_message = MagicMock()
    mock_message.value = json.dumps({"event_type": "test", "data": "mock_data"}).encode("utf-8")

    mock_consumer_instance.__iter__.return_value = [mock_message]

    with patch.object(consumer, "_initialize_consumer", return_value=mock_consumer_instance):
        consumer._consume_messages()

    assert len(event_store) == 1
    assert event_queue.qsize() == 1
    assert event_store[0]["event_type"] == "test"
    assert event_queue.get()["event_type"] == "test"


@patch("event.KafkaConsumer")
def test_kafka_consumer_thread_start(MockKafkaConsumer, kafka_consumer):
    """Test starting the Kafka consumer in a thread."""
    consumer, _, _ = kafka_consumer

    with patch.object(consumer, "_consume_messages") as mock_consume:
        consumer.start()
        assert consumer.running is True
        mock_consume.assert_called_once()  

    consumer.stop()
    assert consumer.running is False
