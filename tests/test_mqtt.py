"""
Tests for MQTT publisher and subscriber modules.

These tests verify the logic without requiring a running MQTT broker or MySQL.
Run: python tests/test_mqtt.py
"""

import sys
import os
import json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from datetime import datetime
from unittest.mock import MagicMock, patch
from src.fetcher.xml_fetcher import TrafficReading


# ---------------------------------------------------------------------------
# Publisher tests
# ---------------------------------------------------------------------------

def test_publisher_build_topic():
    """Topic format: hk-traffic/{source_type}/{detector_id}"""
    from src.mqtt.publisher import TrafficMqttPublisher

    pub = TrafficMqttPublisher.__new__(TrafficMqttPublisher)
    pub.TOPIC_PREFIX = "hk-traffic"

    assert pub._build_topic("strategic", "AID01101") == "hk-traffic/strategic/AID01101"
    assert pub._build_topic("lamppost", "AID20051") == "hk-traffic/lamppost/AID20051"


def test_publisher_publish_reading_payload():
    """Verify the JSON payload format sent to MQTT."""
    from src.mqtt.publisher import TrafficMqttPublisher

    reading = TrafficReading(
        detector_id="AID01101",
        source_type="strategic",
        timestamp=datetime(2026, 3, 18, 8, 30, 0),
        lane_id="Fast Lane",
        speed=67,
        volume=4,
        occupancy=2,
        speed_sd=14.6,
        valid="Y",
        direction="South East",
    )

    pub = TrafficMqttPublisher.__new__(TrafficMqttPublisher)
    pub.TOPIC_PREFIX = "hk-traffic"
    pub._connected = True
    pub.qos = 1

    # Mock the MQTT client
    mock_client = MagicMock()
    mock_result = MagicMock()
    mock_result.rc = 0
    mock_client.publish.return_value = mock_result
    pub.client = mock_client

    result = pub.publish_reading(reading)
    assert result is True

    # Verify the call
    call_args = mock_client.publish.call_args
    topic = call_args[0][0]
    payload = json.loads(call_args[0][1])

    assert topic == "hk-traffic/strategic/AID01101"
    assert payload["detector_id"] == "AID01101"
    assert payload["speed"] == 67
    assert payload["lane_id"] == "Fast Lane"
    assert payload["timestamp"] == "2026-03-18T08:30:00"


def test_publisher_not_connected():
    """Publish should fail gracefully when not connected."""
    from src.mqtt.publisher import TrafficMqttPublisher

    reading = TrafficReading(
        detector_id="AID01101", source_type="strategic",
        timestamp=datetime.now(), lane_id="Fast Lane",
        speed=60, volume=5, occupancy=3, speed_sd=2.0, valid="Y",
    )

    pub = TrafficMqttPublisher.__new__(TrafficMqttPublisher)
    pub._connected = False

    assert pub.publish_reading(reading) is False


def test_publisher_batch_stats():
    """publish_readings should return correct stats."""
    from src.mqtt.publisher import TrafficMqttPublisher

    readings = [
        TrafficReading(
            detector_id=f"AID{i:05d}", source_type="strategic",
            timestamp=datetime.now(), lane_id="Fast Lane",
            speed=60, volume=5, occupancy=3, speed_sd=2.0, valid="Y",
        )
        for i in range(5)
    ]

    pub = TrafficMqttPublisher.__new__(TrafficMqttPublisher)
    pub.TOPIC_PREFIX = "hk-traffic"
    pub._connected = True
    pub.qos = 1

    mock_client = MagicMock()
    mock_result = MagicMock()
    mock_result.rc = 0
    mock_client.publish.return_value = mock_result
    pub.client = mock_client

    result = pub.publish_readings(readings)
    assert result["total"] == 5
    assert result["published"] == 5
    assert result["failed"] == 0


# ---------------------------------------------------------------------------
# Subscriber tests
# ---------------------------------------------------------------------------

def test_subscriber_parse_topic():
    """Subscriber correctly extracts source_type and detector_id from topic."""
    topic = "hk-traffic/strategic/AID01101"
    parts = topic.split("/")
    assert parts[1] == "strategic"
    assert parts[2] == "AID01101"

    topic2 = "hk-traffic/lamppost/AID20051"
    parts2 = topic2.split("/")
    assert parts2[1] == "lamppost"
    assert parts2[2] == "AID20051"


def test_subscriber_message_parsing():
    """Subscriber correctly parses incoming MQTT message into DB row."""
    from src.mqtt.subscriber import TrafficMqttSubscriber

    sub = TrafficMqttSubscriber.__new__(TrafficMqttSubscriber)
    sub._msg_received = 0
    sub._msg_errors = 0
    sub._buffer = []
    sub._buffer_lock = __import__("threading").Lock()
    sub.batch_size = 999  # don't auto-flush

    # Simulate an incoming MQTT message
    mock_msg = MagicMock()
    mock_msg.topic = "hk-traffic/strategic/AID01101"
    mock_msg.payload = json.dumps({
        "detector_id": "AID01101",
        "source_type": "strategic",
        "timestamp": "2026-03-18T08:30:00",
        "lane_id": "Fast Lane",
        "speed": 67,
        "volume": 4,
        "occupancy": 2,
        "speed_sd": 14.6,
        "valid": "Y",
        "direction": "South East",
    }).encode("utf-8")

    sub._on_message(None, None, mock_msg)

    assert sub._msg_received == 1
    assert len(sub._buffer) == 1

    row = sub._buffer[0]
    assert row["detector_id"] == "AID01101"
    assert row["source_type"] == "strategic"
    assert row["speed"] == 67
    assert row["lane_id"] == "Fast Lane"
    assert row["valid"] == "Y"


def test_subscriber_bad_json():
    """Subscriber handles malformed JSON without crashing."""
    from src.mqtt.subscriber import TrafficMqttSubscriber

    sub = TrafficMqttSubscriber.__new__(TrafficMqttSubscriber)
    sub._msg_received = 0
    sub._msg_errors = 0
    sub._buffer = []
    sub._buffer_lock = __import__("threading").Lock()
    sub.batch_size = 999

    mock_msg = MagicMock()
    mock_msg.topic = "hk-traffic/strategic/AID01101"
    mock_msg.payload = b"not valid json{{"

    sub._on_message(None, None, mock_msg)

    assert sub._msg_received == 1
    assert sub._msg_errors == 1
    assert len(sub._buffer) == 0


def test_subscriber_bad_topic():
    """Subscriber handles unexpected topic format."""
    from src.mqtt.subscriber import TrafficMqttSubscriber

    sub = TrafficMqttSubscriber.__new__(TrafficMqttSubscriber)
    sub._msg_received = 0
    sub._msg_errors = 0
    sub._buffer = []
    sub._buffer_lock = __import__("threading").Lock()
    sub.batch_size = 999

    mock_msg = MagicMock()
    mock_msg.topic = "wrong-topic"
    mock_msg.payload = b'{"speed": 50}'

    sub._on_message(None, None, mock_msg)

    assert sub._msg_errors == 1
    assert len(sub._buffer) == 0


# ---------------------------------------------------------------------------
# Run all
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import traceback

    tests = [v for k, v in sorted(globals().items())
             if k.startswith("test_") and callable(v)]
    passed = failed = 0

    for fn in tests:
        try:
            fn()
            print(f"  PASS  {fn.__name__}")
            passed += 1
        except Exception as e:
            print(f"  FAIL  {fn.__name__}: {e}")
            traceback.print_exc()
            failed += 1

    print(f"\n{'='*40}")
    print(f"Results: {passed} passed, {failed} failed, {passed+failed} total")
    if failed:
        sys.exit(1)