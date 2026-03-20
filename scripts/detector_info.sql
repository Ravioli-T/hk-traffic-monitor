use hk_traffic;
SELECT source_type, COUNT(*) FROM detector_info GROUP BY source_type;
SELECT COUNT(*) FROM traffic_readings;