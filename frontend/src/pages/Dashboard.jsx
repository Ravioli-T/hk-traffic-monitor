import { useState, useEffect, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { Typography, Box, Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Paper } from "@mui/material";
import StatsOverview from "../components/Cards/StatsOverview";
import HKMap from "../components/Map/HKMap";
import MapLegend from "../components/Map/MapLegend";
import { fetchDetectors, fetchLatestReadings, fetchOverviewStats } from "../services/api";
import { formatTimestamp } from "../utils/formatters";

const MOCK_DETECTORS = [
  { detector_id: "MOCK01", district: "Central", road_name_en: "Queen's Road", latitude: 22.28, longitude: 114.16, direction: "East", source_type: "strategic" },
  { detector_id: "MOCK02", district: "Kowloon", road_name_en: "Nathan Road", latitude: 22.31, longitude: 114.17, direction: "South", source_type: "strategic" },
  { detector_id: "MOCK03", district: "Sha Tin", road_name_en: "Tai Po Road", latitude: 22.38, longitude: 114.19, direction: "North", source_type: "strategic" },
  { detector_id: "MOCK04", district: "Tuen Mun", road_name_en: "Tuen Mun Road", latitude: 22.39, longitude: 113.97, direction: "West", source_type: "strategic" },
  { detector_id: "MOCK05", district: "Aberdeen", road_name_en: "Ap Lei Chau Bridge Road", latitude: 22.26, longitude: 114.15, direction: "South", source_type: "lamppost" },
];

const MOCK_LATEST_READINGS = MOCK_DETECTORS.map((d, i) => ({
  detector_id: d.detector_id,
  timestamp: new Date().toISOString(),
  lanes: [
    { lane_id: "Fast Lane", speed: 45 + i * 6, volume: 5 + i, occupancy: 10 + i * 2, valid: "Y" },
  ],
}));

const MOCK_ANOMALIES = [
  { time: "2024-03-15T14:25:00", detector_id: "AID01101", speed: 12, status: "Abnormal Congestion", explanation: "Speed dropped below 15 km/h during peak hour" },
  { time: "2024-03-15T14:18:00", detector_id: "AID20051", speed: 0, status: "Abnormal Event", explanation: "Detector offline for 5 minutes" },
  { time: "2024-03-15T14:10:00", detector_id: "AID03021", speed: 8, status: "Abnormal Congestion", explanation: "Heavy congestion detected" },
  { time: "2024-03-15T14:02:00", detector_id: "AID05011", speed: 85, status: "Normal", explanation: "Speed spike after incident clearance" },
  { time: "2024-03-15T13:55:00", detector_id: "LMP001", speed: 22, status: "Normal Congestion", explanation: "Moderate congestion on approach" },
];

export default function Dashboard() {
  const navigate = useNavigate();
  const [detectors, setDetectors] = useState([]);
  const [latestReadings, setLatestReadings] = useState([]);
  const [overviewStats, setOverviewStats] = useState(null);
  const [lastUpdate, setLastUpdate] = useState(null);

  const loadData = useCallback(async () => {
    const load = async () => {
      let detectorsData = [];
      let readingsData = [];
      let statsData = null;

      try {
        detectorsData = await fetchDetectors();
      } catch {
        detectorsData = MOCK_DETECTORS;
      }

      try {
        readingsData = await fetchLatestReadings();
      } catch {
        readingsData = MOCK_LATEST_READINGS;
      }

      try {
        statsData = await fetchOverviewStats();
      } catch {
        statsData = {
          total_detectors: 523,
          online_count: 498,
          offline_count: 25,
          anomaly_count: 12,
          strategic_count: 480,
          lamppost_count: 43,
          last_update: "2024-03-15T14:30:00",
        };
      }

      setDetectors(detectorsData);
      setLatestReadings(readingsData);
      setOverviewStats(statsData);
      setLastUpdate(statsData?.last_update || new Date().toISOString());
    };

    await load();
  }, []);

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 60000);
    return () => clearInterval(interval);
  }, [loadData]);

  const handleDetectorClick = (detectorId) => {
    navigate(`/detector/${detectorId}`);
  };

  const displayDetectors = detectors.length > 0 ? detectors : MOCK_DETECTORS;
  const displayReadings = latestReadings.length > 0 ? latestReadings : MOCK_LATEST_READINGS;

  return (
    <>
      <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "center", mb: 2 }}>
        <Typography variant="h4" gutterBottom>
          Real-time Traffic Overview
        </Typography>
        {lastUpdate && (
          <Typography variant="body2" color="text.secondary">
            Last update: {formatTimestamp(lastUpdate)}
          </Typography>
        )}
      </Box>

      <Box sx={{ mb: 3 }}>
        <StatsOverview />
      </Box>

      <Box sx={{ position: "relative", height: 500, mb: 3, "& > div": { height: "100%" } }}>
        <div style={{ height: "100%", width: "100%" }}>
          <HKMap
            detectors={displayDetectors}
            latestReadings={displayReadings}
            onDetectorClick={handleDetectorClick}
          />
        </div>
        <MapLegend />
      </Box>

      <Typography variant="h6" gutterBottom>
        Recent Anomaly Events
      </Typography>
      <TableContainer component={Paper} sx={{ maxHeight: 280 }}>
        <Table stickyHeader size="small">
          <TableHead>
            <TableRow>
              <TableCell>Time</TableCell>
              <TableCell>Detector</TableCell>
              <TableCell align="right">Speed</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Explanation</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {MOCK_ANOMALIES.map((row, i) => (
              <TableRow key={i} hover>
                <TableCell>{formatTimestamp(row.time)}</TableCell>
                <TableCell>{row.detector_id}</TableCell>
                <TableCell align="right">{row.speed} km/h</TableCell>
                <TableCell>{row.status}</TableCell>
                <TableCell sx={{ maxWidth: 300 }}>{row.explanation}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </>
  );
}
