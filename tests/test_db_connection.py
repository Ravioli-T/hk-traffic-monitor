"""
测试 MySQL 数据库连接
运行前确保：
  1. MySQL 服务已启动
  2. 已执行建库建表 SQL
  3. 已安装依赖：pip install sqlalchemy pymysql python-dotenv
"""

import sys
from sqlalchemy import create_engine, text

# ── 配置 ──────────────────────────────────────
# 直接写在这里方便测试，正式项目中应从 .env 读取
DB_HOST = "localhost"
DB_PORT = 3306
DB_NAME = "hk_traffic"
DB_USER = "traffic_user"
DB_PASSWORD = "Traffic2025!"

DB_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"


def test_connection():
    """测试数据库连接、表结构、读写"""

    print("=" * 50)
    print("HK Traffic — MySQL 连接测试")
    print("=" * 50)

    # ── 1. 测试连接 ──
    print("\n[1/4] 正在连接数据库...")
    try:
        engine = create_engine(DB_URL, echo=False)
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            result.fetchone()
        print("  ✅ 连接成功!")
    except Exception as e:
        print(f"  ❌ 连接失败: {e}")
        print("\n请检查：")
        print("  - MySQL 服务是否已启动")
        print("  - 用户名/密码是否正确")
        print("  - 数据库 hk_traffic 是否已创建")
        sys.exit(1)

    # ── 2. 检查表是否存在 ──
    print("\n[2/4] 检查数据表...")
    with engine.connect() as conn:
        result = conn.execute(text("SHOW TABLES"))
        tables = [row[0] for row in result]
        print(f"  发现 {len(tables)} 张表: {tables}")

        expected = {"detector_info", "traffic_readings"}
        missing = expected - set(tables)
        if missing:
            print(f"  ⚠️  缺少表: {missing}")
        else:
            print("  ✅ 两张表都存在!")

    # ── 3. 测试写入 ──
    print("\n[3/4] 测试写入（插入一条测试数据）...")
    with engine.connect() as conn:
        conn.execute(text("""
            INSERT INTO traffic_readings
                (detector_id, source_type, timestamp, lane_id, speed, volume, occupancy, speed_sd, valid)
            VALUES
                ('TEST001', 'strategic', NOW(), 'Fast Lane', 60, 10, 15, 3.5, 'Y')
        """))
        conn.commit()
        print("  ✅ 写入成功!")

    # ── 4. 测试读取并清理 ──
    print("\n[4/4] 测试读取并清理测试数据...")
    with engine.connect() as conn:
        result = conn.execute(text(
            "SELECT id, detector_id, speed, volume FROM traffic_readings WHERE detector_id = 'TEST001'"
        ))
        rows = result.fetchall()
        print(f"  读取到 {len(rows)} 条记录:")
        for row in rows:
            print(f"    id={row[0]}, detector_id={row[1]}, speed={row[2]}, volume={row[3]}")

        # 清理测试数据
        conn.execute(text("DELETE FROM traffic_readings WHERE detector_id = 'TEST001'"))
        conn.commit()
        print("  ✅ 测试数据已清理!")

    # ── 完成 ──
    print("\n" + "=" * 50)
    print("🎉 全部测试通过！数据库已就绪。")
    print("=" * 50)


if __name__ == "__main__":
    test_connection()
