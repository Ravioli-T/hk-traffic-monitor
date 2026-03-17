"""
批量导入历史 Raw XML 数据到 traffic_readings 表。

目录结构约定:
    data/raw/history/
    ├── Traffic Speed, Volume and Road Occupancy (Raw Data) - 20260314/
    │   └── https%3A%2F%2F.../
    │       ├── 20260314-0001-rawSpeedVol-all.xml
    │       ├── 20260314-0002-rawSpeedVol-all.xml
    │       └── ...
    ├── Traffic Speed, Volume and Road Occupancy (Raw Data) - 20260315/
    │   └── ...
    └── (更多日期...)

每个日期文件夹由 DATA.GOV.HK 下载后解压得到，脚本自动扫描 history/ 下所有日期。
XML schema 和实时 API 完全一致，直接复用 xml_fetcher.parse_xml()。

使用方式:
    cd hk-traffic-monitor
    python scripts/import_historical_data.py                    # 导入 history/ 下所有日期
    python scripts/import_historical_data.py --date 20260314    # 只导入指定日期
    python scripts/import_historical_data.py --dry-run          # 只扫描不导入，看看有多少数据
"""

import argparse
import glob
import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.fetcher.xml_fetcher import parse_xml
from src.database.connection import get_session_factory
from src.database.crud import bulk_insert_readings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

# 默认历史数据根目录
DEFAULT_HISTORY_DIR = os.path.join(
    os.path.dirname(__file__), "..", "data", "raw", "history"
)

# 每批写入数据库的行数（避免单次 INSERT 太大）
BATCH_SIZE = 5000


def find_date_folders(history_dir: str) -> list[tuple[str, str]]:
    """
    扫描 history/ 下的所有日期文件夹。

    Returns
    -------
    list of (date_str, folder_path)
        例如 [("20260314", "D:/hk-traffic-monitor/data/raw/history/Traffic ... - 20260314")]
    """
    results = []
    if not os.path.isdir(history_dir):
        logger.error("历史数据目录不存在: %s", history_dir)
        return results

    for entry in sorted(os.listdir(history_dir)):
        full_path = os.path.join(history_dir, entry)
        if not os.path.isdir(full_path):
            continue

        # 从文件夹名中提取日期，格式: "... - 20260314"
        # 取最后 8 个字符尝试解析为日期
        folder_name = entry.strip()
        date_str = folder_name[-8:]
        try:
            datetime.strptime(date_str, "%Y%m%d")
            results.append((date_str, full_path))
        except ValueError:
            logger.warning("无法识别日期文件夹: %s", entry)
            continue

    return results


def find_xml_files(date_folder: str) -> list[str]:
    """
    在日期文件夹（及其子目录）中递归查找所有 XML 文件。

    DATA.GOV.HK 下载解压后，XML 文件通常在一层编码过的子目录里，
    所以用递归搜索最可靠。
    """
    xml_files = []
    for root, dirs, files in os.walk(date_folder):
        for f in files:
            if f.lower().endswith(".xml"):
                xml_files.append(os.path.join(root, f))

    # 按文件名排序，保证按时间顺序导入
    xml_files.sort()
    return xml_files


def detect_source_type(xml_files: list[str]) -> str:
    """
    根据文件名判断数据来源。
    rawSpeedVol-all.xml → strategic
    rawSpeedVol_SLP-all.xml → lamppost
    """
    if not xml_files:
        return "strategic"

    sample_name = os.path.basename(xml_files[0]).lower()
    if "slp" in sample_name:
        return "lamppost"
    return "strategic"


def import_date(
    date_str: str,
    date_folder: str,
    session_factory,
    dry_run: bool = False,
) -> dict:
    """
    导入一个日期的所有 XML 文件。

    Returns
    -------
    dict
        {"date": str, "files": int, "readings": int, "inserted": int, "errors": int, "seconds": float}
    """
    result = {
        "date": date_str,
        "files": 0,
        "readings": 0,
        "inserted": 0,
        "errors": 0,
        "seconds": 0,
    }

    start_time = time.time()

    # 找到所有 XML 文件
    xml_files = find_xml_files(date_folder)
    result["files"] = len(xml_files)

    if not xml_files:
        logger.warning("[%s] 未找到 XML 文件: %s", date_str, date_folder)
        return result

    source_type = detect_source_type(xml_files)
    logger.info(
        "[%s] 找到 %d 个 XML 文件 (source=%s)",
        date_str, len(xml_files), source_type,
    )

    if dry_run:
        # 只解析第一个文件估算总量
        with open(xml_files[0], "r", encoding="utf-8") as f:
            sample = parse_xml(f.read(), source_type)
        estimated = len(sample) * len(xml_files)
        logger.info("[%s] [dry-run] 预估总行数: ~%d", date_str, estimated)
        result["readings"] = estimated
        result["seconds"] = time.time() - start_time
        return result

    # 逐文件解析，攒批写入
    buffer = []
    files_done = 0

    for xml_path in xml_files:
        try:
            with open(xml_path, "r", encoding="utf-8") as f:
                xml_text = f.read()

            readings = parse_xml(xml_text, source_type)
            result["readings"] += len(readings)

            # 转为 dict 列表
            for r in readings:
                buffer.append({
                    "detector_id": r.detector_id,
                    "source_type": r.source_type,
                    "timestamp": r.timestamp.isoformat(),
                    "lane_id": r.lane_id,
                    "speed": r.speed,
                    "volume": r.volume,
                    "occupancy": r.occupancy,
                    "speed_sd": r.speed_sd,
                    "valid": r.valid,
                })

            # 攒够一批就写入
            if len(buffer) >= BATCH_SIZE:
                inserted = _flush_to_db(session_factory, buffer)
                result["inserted"] += inserted
                buffer.clear()

        except Exception as e:
            logger.error("[%s] 解析失败 %s: %s", date_str, os.path.basename(xml_path), e)
            result["errors"] += 1
            continue

        files_done += 1
        # 每 100 个文件打印一次进度
        if files_done % 100 == 0:
            logger.info(
                "[%s] 进度: %d/%d 文件, %d 条已入库",
                date_str, files_done, len(xml_files), result["inserted"],
            )

    # 写入剩余 buffer
    if buffer:
        inserted = _flush_to_db(session_factory, buffer)
        result["inserted"] += inserted
        buffer.clear()

    result["seconds"] = time.time() - start_time
    return result


def _flush_to_db(session_factory, rows: list[dict]) -> int:
    """批量写入数据库，返回成功插入的行数。"""
    session = session_factory()
    try:
        count = bulk_insert_readings(session, rows)
        session.commit()
        return count
    except Exception as e:
        session.rollback()
        logger.error("数据库写入失败 (%d 行): %s", len(rows), e)
        return 0
    finally:
        session.close()


def check_existing_data(session_factory, date_str: str) -> int:
    """检查数据库中某一天已有多少条数据。"""
    from sqlalchemy import text
    date_obj = datetime.strptime(date_str, "%Y%m%d").date()
    session = session_factory()
    try:
        count = session.execute(
            text("SELECT COUNT(*) FROM traffic_readings WHERE DATE(timestamp) = :d"),
            {"d": date_obj},
        ).scalar()
        return count
    finally:
        session.close()


def main():
    parser = argparse.ArgumentParser(
        description="批量导入历史 Raw XML 数据到 traffic_readings 表"
    )
    parser.add_argument(
        "--history-dir",
        default=DEFAULT_HISTORY_DIR,
        help="历史数据根目录 (default: data/raw/history/)",
    )
    parser.add_argument(
        "--date",
        default=None,
        help="只导入指定日期，格式 YYYYMMDD (例如 20260314)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="只扫描不导入，查看有多少数据",
    )
    parser.add_argument(
        "--skip-existing",
        action="store_true",
        help="跳过数据库中已有数据的日期",
    )
    parser.add_argument(
        "--db-url",
        default=None,
        help="MySQL 连接 URL (默认从 .env 读取)",
    )
    args = parser.parse_args()

    history_dir = os.path.abspath(args.history_dir)

    # 扫描所有日期文件夹
    all_dates = find_date_folders(history_dir)

    if args.date:
        all_dates = [(d, p) for d, p in all_dates if d == args.date]
        if not all_dates:
            print(f"❌ 未找到日期 {args.date} 的数据文件夹")
            print(f"   搜索路径: {history_dir}")
            return

    if not all_dates:
        print(f"❌ 未找到任何历史数据文件夹")
        print(f"   搜索路径: {history_dir}")
        print(f"   请将 DATA.GOV.HK 下载的日期文件夹放在此目录下")
        return

    print(f"\n{'='*60}")
    print(f"  历史数据批量导入")
    print(f"{'='*60}")
    print(f"  数据目录: {history_dir}")
    print(f"  发现 {len(all_dates)} 个日期:")
    for d, p in all_dates:
        folder_name = os.path.basename(p)
        print(f"    📁 {d}  ({folder_name})")
    print()

    if args.dry_run:
        print("  🔍 Dry-run 模式: 只扫描不导入\n")

    # 初始化数据库
    session_factory = get_session_factory(args.db_url)

    # 逐日期导入
    summary = []

    for date_str, date_folder in all_dates:
        # 检查是否已有数据
        if args.skip_existing and not args.dry_run:
            existing = check_existing_data(session_factory, date_str)
            if existing > 0:
                print(f"  ⏭️  {date_str}: 数据库已有 {existing:,} 条，跳过")
                summary.append({
                    "date": date_str, "files": 0, "readings": 0,
                    "inserted": 0, "errors": 0, "seconds": 0,
                    "skipped": True,
                })
                continue

        print(f"  {'📊 扫描' if args.dry_run else '📥 导入'} {date_str}...")
        result = import_date(date_str, date_folder, session_factory, args.dry_run)
        result["skipped"] = False
        summary.append(result)

        status = "✅" if result["errors"] == 0 else "⚠️"
        if args.dry_run:
            print(f"  {status} {date_str}: {result['files']} 个文件, "
                  f"预估 ~{result['readings']:,} 条")
        else:
            print(f"  {status} {date_str}: {result['files']} 个文件, "
                  f"{result['readings']:,} 条解析, "
                  f"{result['inserted']:,} 条入库, "
                  f"{result['errors']} 错误, "
                  f"{result['seconds']:.1f}s")

    # 汇总报告
    print(f"\n{'='*60}")
    print(f"  导入完成 — 汇总报告")
    print(f"{'='*60}")

    total_files = sum(r["files"] for r in summary)
    total_readings = sum(r["readings"] for r in summary)
    total_inserted = sum(r["inserted"] for r in summary)
    total_errors = sum(r["errors"] for r in summary)
    total_seconds = sum(r["seconds"] for r in summary)
    skipped = sum(1 for r in summary if r.get("skipped"))

    print(f"  日期数:    {len(summary)} ({skipped} 跳过)")
    print(f"  XML 文件:  {total_files:,}")
    print(f"  解析行数:  {total_readings:,}")
    if not args.dry_run:
        print(f"  入库行数:  {total_inserted:,}")
    print(f"  错误数:    {total_errors}")
    print(f"  耗时:      {total_seconds:.1f}s")

    # 逐日明细
    print(f"\n  {'日期':<12} {'文件':<8} {'解析':<12} {'入库':<12} {'状态'}")
    print(f"  {'-'*56}")
    for r in summary:
        if r.get("skipped"):
            status = "⏭️ 跳过"
        elif r["errors"] > 0:
            status = f"⚠️ {r['errors']} 错误"
        else:
            status = "✅"
        print(f"  {r['date']:<12} {r['files']:<8} {r['readings']:<12,} "
              f"{r['inserted']:<12,} {status}")

    print()


if __name__ == "__main__":
    main()
