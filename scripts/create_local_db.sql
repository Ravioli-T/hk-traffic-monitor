-- ============================================
-- 1. 创建数据库
-- ============================================
CREATE DATABASE IF NOT EXISTS hk_traffic
    DEFAULT CHARACTER SET utf8mb4
    DEFAULT COLLATE utf8mb4_unicode_ci;

USE hk_traffic;

-- ============================================
-- 2. 创建项目专用账户（而非直接用 root）
-- ============================================
CREATE USER IF NOT EXISTS 'traffic_user'@'localhost'
    IDENTIFIED BY 'Traffic2025!';

GRANT ALL PRIVILEGES ON hk_traffic.* TO 'traffic_user'@'localhost';

FLUSH PRIVILEGES;

-- ============================================
-- 3. 检测器元数据表（从 CSV 一次性导入）
-- ============================================
CREATE TABLE IF NOT EXISTS detector_info (
    detector_id   VARCHAR(20)   PRIMARY KEY,
    district      VARCHAR(50),
    road_name_en  VARCHAR(200),
    road_name_tc  VARCHAR(200),
    latitude      DECIMAL(9,6),
    longitude     DECIMAL(9,6),
    direction     VARCHAR(50),
    easting       DECIMAL(12,2),
    northing      DECIMAL(12,2),
    source_type   ENUM('strategic', 'lamppost') NOT NULL,
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- ============================================
-- 4. 交通读数表（核心数据表）
-- ============================================
CREATE TABLE IF NOT EXISTS traffic_readings (
    id            BIGINT AUTO_INCREMENT PRIMARY KEY,
    detector_id   VARCHAR(20)   NOT NULL,
    source_type   ENUM('strategic', 'lamppost') NOT NULL,
    timestamp     DATETIME      NOT NULL,
    lane_id       VARCHAR(30)   NOT NULL,
    speed         INT,
    volume        INT,
    occupancy     INT,
    speed_sd      DECIMAL(5,2),
    valid         CHAR(1)       DEFAULT 'Y',
    created_at    TIMESTAMP     DEFAULT CURRENT_TIMESTAMP,

    -- 按检测器+时间查询（ML 和 EDA 的主要查询模式）
    INDEX idx_detector_time (detector_id, timestamp),
    -- 按时间范围查询
    INDEX idx_timestamp (timestamp),
    -- 按数据来源筛选（strategic vs lamppost 对比分析）
    INDEX idx_source_type (source_type)
) ENGINE=InnoDB;

-- ============================================
-- 5. 验证
-- ============================================
SHOW TABLES;
SELECT USER(), DATABASE();