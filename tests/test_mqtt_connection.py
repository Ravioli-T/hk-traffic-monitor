"""
测试 MQTT Broker (Mosquitto) 连接 — paho-mqtt 2.x 兼容版
运行前确保：
  1. Mosquitto 服务已启动 (localhost:1883)
  2. 已安装依赖：pip install paho-mqtt
"""

import time
import json
import threading
import paho.mqtt.client as mqtt

BROKER_HOST = "localhost"
BROKER_PORT = 1883
TEST_TOPIC = "hk-traffic/strategic/Kowloon City/TEST001"

received_messages = []
connected_event = threading.Event()


def test_mqtt():
    print("=" * 50)
    print("HK Traffic — MQTT Broker 连接测试")
    print("=" * 50)

    # ── 1. 测试基本连接 ──
    print("\n[1/3] 正在连接 MQTT Broker...")

    def on_connect(client, userdata, flags, reason_code, properties):
        if reason_code == 0:
            connected_event.set()

    def on_message(client, userdata, msg):
        payload = json.loads(msg.payload.decode())
        received_messages.append(payload)

    # 创建一个客户端同时做订阅和发布
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="test-all-in-one")
    client.on_connect = on_connect
    client.on_message = on_message

    try:
        client.connect(BROKER_HOST, BROKER_PORT, keepalive=60)
    except Exception as e:
        print(f"  ❌ 连接失败: {e}")
        print("\n请检查：")
        print("  - Mosquitto 服务是否已启动")
        print("  - 端口 1883 是否被占用")
        return

    client.loop_start()

    # 等待连接完成（最多 5 秒）
    if not connected_event.wait(timeout=5):
        print("  ❌ 连接超时")
        client.loop_stop()
        return

    print(f"  ✅ 连接成功! Broker: {BROKER_HOST}:{BROKER_PORT}")

    # ── 2. 测试发布/订阅 ──
    print("\n[2/3] 测试发布与订阅...")

    test_payload = {
        "detector_id": "TEST001",
        "source_type": "strategic",
        "timestamp": "2025-03-15T08:30:00",
        "direction": "South East",
        "lanes": [
            {
                "lane_id": "Fast Lane",
                "speed": 65,
                "volume": 8,
                "occupancy": 12,
                "speed_sd": 5.2,
                "valid": "Y"
            }
        ]
    }

    # 先订阅
    client.subscribe("hk-traffic/#", qos=1)
    time.sleep(1)

    # 再发布
    payload_json = json.dumps(test_payload)
    result = client.publish(TEST_TOPIC, payload_json, qos=1)
    result.wait_for_publish()
    print(f"  📤 已发布消息 → {TEST_TOPIC}")

    # 等待消息到达（最多 5 秒）
    deadline = time.time() + 5
    while not received_messages and time.time() < deadline:
        time.sleep(0.1)

    if received_messages:
        received = received_messages[0]
        print(f"  📨 收到消息!")
        print(f"     detector_id: {received['detector_id']}")
        print(f"     speed: {received['lanes'][0]['speed']} km/h")
        print("  ✅ 发布/订阅测试通过!")
    else:
        print("  ❌ 未收到消息，请检查 Mosquitto 配置")
        client.loop_stop()
        client.disconnect()
        return

    # ── 3. 验证消息内容完整性 ──
    print("\n[3/3] 验证消息内容...")
    checks = [
        ("detector_id", received.get("detector_id") == "TEST001"),
        ("source_type", received.get("source_type") == "strategic"),
        ("lanes 数量", len(received.get("lanes", [])) == 1),
        ("speed 值",   received["lanes"][0]["speed"] == 65),
    ]
    all_passed = True
    for name, passed in checks:
        status = "✅" if passed else "❌"
        print(f"  {status} {name}")
        if not passed:
            all_passed = False

    # 清理
    client.loop_stop()
    client.disconnect()

    # 结果
    print("\n" + "=" * 50)
    if all_passed:
        print("🎉 全部测试通过！MQTT Broker 已就绪。")
    else:
        print("⚠️  部分测试未通过，请检查上方输出。")
    print("=" * 50)


if __name__ == "__main__":
    test_mqtt()