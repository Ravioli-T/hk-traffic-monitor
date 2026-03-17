"""
端到端集成测试 — 验证完整数据管线:

    XML API  →  Fetcher  →  MQTT Publisher  →  Mosquitto  →  MQTT Subscriber  →  MySQL

前提条件（在你的本机上）:
    1. MySQL 已启动，hk_traffic 库和表已建好
    2. Mosquitto 已启动（localhost:1883）
    3. Python venv 已激活，依赖已安装

运行方式:
    cd hk-traffic-monitor
    python scripts/e2e.py
"""

import sys
import os
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
)
logger = logging.getLogger("e2e_test")
logging.getLogger("urllib3").setLevel(logging.WARNING)

# ---------- 配置 ----------
DB_URL = "mysql+pymysql://traffic_user:Traffic2025!@localhost:3306/hk_traffic?charset=utf8mb4"
BROKER_HOST = "localhost"
BROKER_PORT = 1883
MAX_PUBLISH = 30  # 只发 30 条，够验证就行


def banner(step, title):
    print(f"\n{'='*60}")
    print(f"  Step {step}: {title}")
    print(f"{'='*60}")


def ok(msg):
    print(f"  ✅ {msg}")


def fail(msg):
    print(f"  ❌ {msg}")


def info(msg):
    print(f"     {msg}")


def main():
    print("\n" + "="*60)
    print("  HK Traffic Monitor — 端到端集成测试")
    print("="*60)

    # ==========================================================
    # Step 1: MySQL 连接
    # ==========================================================
    banner(1, "检查 MySQL 连接")
    try:
        from sqlalchemy import create_engine, text
        engine = create_engine(DB_URL)
        with engine.connect() as conn:
            db = conn.execute(text("SELECT DATABASE()")).scalar()
            ok(f"MySQL 连接成功 (database={db})")

            tables = [r[0] for r in conn.execute(text("SHOW TABLES"))]
            if "traffic_readings" not in tables:
                fail("traffic_readings 表不存在")
                return
            if "detector_info" not in tables:
                fail("detector_info 表不存在")
                return
            ok(f"表结构正常: {tables}")

            # 记录测试前的数据量
            before_count = conn.execute(
                text("SELECT COUNT(*) FROM traffic_readings")
            ).scalar()
            info(f"当前 traffic_readings 行数: {before_count}")
        engine.dispose()
    except Exception as e:
        fail(f"MySQL 连接失败: {e}")
        info("请检查 MySQL 是否在运行，用户名密码是否正确")
        return

    # ==========================================================
    # Step 2: Mosquitto 连接
    # ==========================================================
    banner(2, "检查 Mosquitto 连接")
    try:
        import paho.mqtt.client as mqtt

        probe_connected = False

        def on_connect(client, userdata, flags, rc, properties):
            nonlocal probe_connected
            probe_connected = (rc == 0)

        probe = mqtt.Client(
            callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
            client_id="e2e-probe",
        )
        probe.on_connect = on_connect
        probe.connect(BROKER_HOST, BROKER_PORT)
        probe.loop_start()
        for _ in range(10):
            if probe_connected:
                break
            time.sleep(0.1)
        probe.loop_stop()
        probe.disconnect()

        if probe_connected:
            ok(f"Mosquitto 连接成功 ({BROKER_HOST}:{BROKER_PORT})")
        else:
            fail("Mosquitto 连接超时")
            info("请确认 Mosquitto 服务正在运行")
            return
    except Exception as e:
        fail(f"Mosquitto 连接失败: {e}")
        return

    # ==========================================================
    # Step 3: 从 XML API 抓取实时数据
    # ==========================================================
    banner(3, "从 XML API 抓取实时数据")
    try:
        from src.fetcher.xml_fetcher import TrafficDataFetcher

        fetcher = TrafficDataFetcher()
        readings = fetcher.fetch_strategic()
        fetcher.close()

        if not readings:
            fail("未抓取到数据，API 可能不可用")
            return

        ok(f"抓取成功: {len(readings)} 条原始数据")

        # 只取前 MAX_PUBLISH 条用于测试
        test_readings = readings[:MAX_PUBLISH]
        info(f"取前 {MAX_PUBLISH} 条用于测试")

        # 显示样本
        r = test_readings[0]
        info(f"样本: {r.detector_id} | {r.lane_id} | "
             f"speed={r.speed} vol={r.volume} | {r.timestamp}")
    except Exception as e:
        fail(f"数据抓取失败: {e}")
        return

    # ==========================================================
    # Step 4: 启动 Subscriber (后台接收 + 写 MySQL)
    # ==========================================================
    banner(4, "启动 MQTT Subscriber")
    try:
        from src.mqtt.subscriber import TrafficMqttSubscriber

        subscriber = TrafficMqttSubscriber(
            broker_host=BROKER_HOST,
            broker_port=BROKER_PORT,
            db_url=DB_URL,
            client_id="e2e-subscriber",
            batch_size=10,         # 小批次，快速 flush
            flush_interval=1.0,    # 1 秒 flush 一次
        )

        if not subscriber.start():
            fail("Subscriber 启动失败")
            return

        ok("Subscriber 已启动 (batch_size=10, flush_interval=1s)")
    except Exception as e:
        fail(f"Subscriber 启动失败: {e}")
        return

    # ==========================================================
    # Step 5: 通过 Publisher 发布数据
    # ==========================================================
    banner(5, "通过 MQTT Publisher 发布数据")
    try:
        from src.mqtt.publisher import TrafficMqttPublisher

        publisher = TrafficMqttPublisher(
            broker_host=BROKER_HOST,
            broker_port=BROKER_PORT,
            client_id="e2e-publisher",
        )

        if not publisher.connect():
            fail("Publisher 连接失败")
            subscriber.stop()
            return

        result = publisher.publish_readings(test_readings)
        ok(f"发布完成: total={result['total']} "
           f"published={result['published']} failed={result['failed']}")

        publisher.disconnect()
    except Exception as e:
        fail(f"Publisher 错误: {e}")
        subscriber.stop()
        return

    # ==========================================================
    # Step 6: 等待 Subscriber 写入完成
    # ==========================================================
    banner(6, "等待数据写入 MySQL")

    max_wait = 10  # 最多等 10 秒
    for i in range(max_wait):
        time.sleep(1)
        stats = subscriber.stats
        info(f"[{i+1}s] received={stats['received']} "
             f"saved={stats['saved']} errors={stats['errors']} "
             f"buffer={stats['buffer_size']}")

        # 所有消息都写入了
        if stats["saved"] >= MAX_PUBLISH:
            break

    subscriber.stop()

    final_stats = {
        "received": stats["received"],
        "saved": stats["saved"],
        "errors": stats["errors"],
    }

    if final_stats["saved"] >= MAX_PUBLISH:
        ok(f"全部写入成功: {final_stats['saved']}/{MAX_PUBLISH}")
    elif final_stats["saved"] > 0:
        ok(f"部分写入: {final_stats['saved']}/{MAX_PUBLISH} "
           f"(errors={final_stats['errors']})")
    else:
        fail(f"写入失败: saved=0, errors={final_stats['errors']}")

    # ==========================================================
    # Step 7: 从 MySQL 验证数据
    # ==========================================================
    banner(7, "从 MySQL 验证数据")
    try:
        engine = create_engine(DB_URL)
        with engine.connect() as conn:
            after_count = conn.execute(
                text("SELECT COUNT(*) FROM traffic_readings")
            ).scalar()
            new_rows = after_count - before_count

            info(f"测试前: {before_count} 行")
            info(f"测试后: {after_count} 行")
            info(f"新增:   {new_rows} 行")

            if new_rows >= MAX_PUBLISH:
                ok(f"数据验证通过！新增 {new_rows} 行")
            elif new_rows > 0:
                ok(f"部分数据入库: {new_rows}/{MAX_PUBLISH}")
            else:
                fail("MySQL 中没有新数据")

            # 查看最新几条记录
            rows = conn.execute(text(
                "SELECT detector_id, lane_id, speed, volume, timestamp "
                "FROM traffic_readings ORDER BY id DESC LIMIT 3"
            )).fetchall()
            info("最新 3 条记录:")
            for row in rows:
                info(f"  {row[0]} | {row[1]:15s} | speed={row[2]} "
                     f"vol={row[3]} | {row[4]}")

        engine.dispose()
    except Exception as e:
        fail(f"MySQL 验证失败: {e}")

    # ==========================================================
    # 总结
    # ==========================================================
    print(f"\n{'='*60}")
    print("  测试完成!")
    print(f"{'='*60}")
    print(f"  Fetcher:    ✅ 抓取 {len(readings)} 条")
    print(f"  MQTT:       ✅ 发布 {result['published']} 条")
    print(f"  Subscriber: {'✅' if final_stats['saved']>0 else '❌'} "
          f"写入 {final_stats['saved']} 条")
    print(f"  MySQL:      {'✅' if new_rows>0 else '❌'} "
          f"新增 {new_rows} 行")
    print()


if __name__ == "__main__":
    main()
