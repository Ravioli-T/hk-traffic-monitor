import { useState, useEffect, useCallback } from "react";
import { useParams, useNavigate } from "react-router-dom";
import {
  Typography,
  Box,
  Button,
  Grid,
  ToggleButtonGroup,
  ToggleButton,
  ButtonGroup,
  Skeleton,
} from "@mui/material";
import ArrowBackIcon from "@mui/icons-material/ArrowBack";
import DetectorInfoCard from "../components/Cards/DetectorInfoCard";
import MiniMap from "../components/Map/MiniMap";
import SpeedVolumeChart from "../components/Charts/SpeedVolumeChart";
import PredictionChart from "../components/Charts/PredictionChart";
import {
  fetchDetectorById,
  fetchDetectorLatest,
  fetchReadingsHistory,
  fetchPrediction,
} from "../services/api";
import dayjs from "dayjs";

const TIME_RANGES = [
  { label: "1h", hours: 1 },
  { label: "3h", hours: 3 },
  { label: "6h", hours: 6 },
  { label: "12h", hours: 12 },
  { label: "24h", hours: 24 },
];

function generateMockHistory(hours, baseSpeed = 50, baseVolume = 8) {
  const points = [];
  const end = dayjs();
  const stepMinutes = 10;
  const count = Math.floor((hours * 60) / stepMinutes);
  for (let i = count; i >= 0; i--) {
    const ts = end.subtract(i * stepMinutes, "minute");
    points.push({
      timestamp: ts.toISOString(),
      speed: Math.round(baseSpeed + (Math.random() - 0.5) * 30),
      volume: Math.max(0, Math.round(baseVolume + (Math.random() - 0.5) * 8)),
      occupancy: Math.round(10 + Math.random() * 20),
    });
  }
  return points;
}

function generateMockPrediction(currentSpeed) {
  const forecast = [];
  const base = dayjs();
  for (let i = 1; i <= 12; i++) {
    const t = base.add(i * 10, "minute");
    const predSpeed = Math.max(0, currentSpeed + (Math.random() - 0.5) * 10);
    forecast.push({
      time: t.toISOString(),
      pred_speed: predSpeed,
      pred_volume: Math.round(8 + Math.random() * 8),
      speed_lower: predSpeed - 5,
      speed_upper: predSpeed + 5,
    });
  }
  return {
    forecast,
    future_congestion: Array(12).fill(0),
    status: "Normal",
    explanation: "Mock prediction data",
  };
}

const MOCK_DETECTOR = {
  detector_id: "MOCK01",
  district: "Central",
  road_name_en: "Queen's Road",
  latitude: 22.28,
  longitude: 114.16,
  direction: "East",
  source_type: "strategic",
};

const MOCK_LATEST = {
  detector_id: "MOCK01",
  timestamp: dayjs().toISOString(),
  lanes: [
    { lane_id: "Fast Lane", speed: 52, volume: 10, occupancy: 15, valid: "Y" },
    { lane_id: "Slow Lane", speed: 38, volume: 6, occupancy: 22, valid: "Y" },
  ],
};

export default function DetectorDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [detector, setDetector] = useState(null);
  const [latestReading, setLatestReading] = useState(null);
  const [historyData, setHistoryData] = useState([]);
  const [prediction, setPrediction] = useState(null);
  const [selectedLane, setSelectedLane] = useState(null);
  const [timeRangeHours, setTimeRangeHours] = useState(6);
  const [loading, setLoading] = useState(true);
  const [isMock, setIsMock] = useState(false);

  const loadDetectorAndLatest = useCallback(async () => {
    if (!id) return;
    let det = null;
    let latest = null;
    try {
      det = await fetchDetectorById(id);
    } catch {
      det = { ...MOCK_DETECTOR, detector_id: id };
    }
    try {
      latest = await fetchDetectorLatest(id);
    } catch {
      latest = { ...MOCK_LATEST, detector_id: id };
    }
    setDetector(det);
    setLatestReading(latest);
    if (latest?.lanes?.length > 0 && !selectedLane) {
      setSelectedLane(latest.lanes[0].lane_id);
    }
    return { det, latest };
  }, [id]);

  const loadHistory = useCallback(async () => {
    if (!id) return;
    const end = dayjs();
    const start = end.subtract(timeRangeHours, "hour");
    try {
      const data = await fetchReadingsHistory(
        id,
        start.toISOString(),
        end.toISOString(),
        selectedLane || undefined
      );
      if (Array.isArray(data) && data.length > 0) {
        const byTs = {};
        for (const r of data) {
          const ts = r.timestamp;
          if (!byTs[ts] || (selectedLane && r.lane_id === selectedLane)) {
            byTs[ts] = r;
          }
        }
        const sorted = Object.values(byTs).sort(
          (a, b) => new Date(a.timestamp) - new Date(b.timestamp)
        );
        setHistoryData(
          sorted.map((r) => ({
            timestamp: r.timestamp,
            speed: r.speed,
            volume: r.volume,
            occupancy: r.occupancy,
          }))
        );
      } else {
        const firstLane = latestReading?.lanes?.[0];
        const baseSpeed = firstLane?.speed ?? 50;
        const baseVolume = firstLane?.volume ?? 8;
        setHistoryData(generateMockHistory(timeRangeHours, baseSpeed, baseVolume));
      }
    } catch {
      const firstLane = latestReading?.lanes?.[0];
      const baseSpeed = firstLane?.speed ?? 50;
      const baseVolume = firstLane?.volume ?? 8;
      setHistoryData(generateMockHistory(timeRangeHours, baseSpeed, baseVolume));
    }
  }, [id, timeRangeHours, selectedLane, latestReading]);

  const loadPrediction = useCallback(async () => {
    if (!id) return;
    try {
      const data = await fetchPrediction(id, selectedLane || undefined);
      setPrediction(data);
      setIsMock(false);
    } catch {
      const firstLane = latestReading?.lanes?.find((l) => l.lane_id === selectedLane) || latestReading?.lanes?.[0];
      const currentSpeed = firstLane?.speed ?? 50;
      setPrediction(generateMockPrediction(currentSpeed));
      setIsMock(true);
    }
  }, [id, selectedLane, latestReading]);

  useEffect(() => {
    let mounted = true;
    const run = async () => {
      setLoading(true);
      await loadDetectorAndLatest();
      if (mounted) setLoading(false);
    };
    run();
    return () => { mounted = false; };
  }, [loadDetectorAndLatest]);

  useEffect(() => {
    if (selectedLane === null && latestReading?.lanes?.length > 0) {
      setSelectedLane(latestReading.lanes[0].lane_id);
    }
  }, [latestReading, selectedLane]);

  useEffect(() => {
    if (!id) return;
    loadHistory();
  }, [id, timeRangeHours, selectedLane, loadHistory]);

  useEffect(() => {
    if (!id) return;
    loadPrediction();
  }, [id, selectedLane, loadPrediction]);

  const lanes = latestReading?.lanes ?? [];
  const displayLane = selectedLane ?? lanes[0]?.lane_id;
  const currentSpeed = lanes.find((l) => l.lane_id === displayLane)?.speed ?? 0;

  if (loading && !detector) {
    return (
      <Box>
        <Skeleton variant="text" width={200} height={40} />
        <Skeleton variant="rectangular" height={200} sx={{ mt: 2 }} />
      </Box>
    );
  }

  return (
    <>
      <Box sx={{ display: "flex", alignItems: "center", gap: 2, mb: 2 }}>
        <Button
          startIcon={<ArrowBackIcon />}
          onClick={() => navigate("/")}
          size="small"
        >
          Back to Dashboard
        </Button>
        <Typography variant="h4">Detector {id || "—"}</Typography>
      </Box>

      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid item xs={12} md={8}>
          <DetectorInfoCard
            detector={detector || {}}
            latestReading={latestReading}
            predictionStatus={prediction?.status ?? "Normal"}
            explanation={prediction?.explanation}
          />
        </Grid>
        <Grid item xs={12} md={4}>
          <MiniMap
            latitude={detector?.latitude}
            longitude={detector?.longitude}
            detectorId={id}
          />
        </Grid>
      </Grid>

      {lanes.length > 1 && (
        <Box sx={{ mb: 2 }}>
          <Typography variant="subtitle2" color="text.secondary" gutterBottom>
            Lane
          </Typography>
          <ToggleButtonGroup
            value={displayLane}
            exclusive
            onChange={(_, v) => v != null && setSelectedLane(v)}
            size="small"
          >
            {lanes.map((l) => (
              <ToggleButton key={l.lane_id} value={l.lane_id}>
                {l.lane_id}
              </ToggleButton>
            ))}
          </ToggleButtonGroup>
        </Box>
      )}

      <Box sx={{ mb: 2 }}>
        <Typography variant="subtitle2" color="text.secondary" gutterBottom>
          Time Range
        </Typography>
        <ButtonGroup size="small">
          {TIME_RANGES.map(({ label, hours }) => (
            <Button
              key={label}
              variant={timeRangeHours === hours ? "contained" : "outlined"}
              onClick={() => setTimeRangeHours(hours)}
            >
              {label}
            </Button>
          ))}
        </ButtonGroup>
      </Box>

      <Box sx={{ mb: 3 }}>
        <SpeedVolumeChart
          data={historyData}
          title={`Speed & Volume (${timeRangeHours}h)`}
        />
      </Box>

      <Box>
        <Typography variant="h6" gutterBottom>
          2-Hour Prediction (Prophet Model)
        </Typography>
        {prediction?.status && (
          <Typography variant="body2" color="text.secondary" sx={{ mb: 0.5 }}>
            Status: {prediction.status} — {prediction.explanation}
          </Typography>
        )}
        {isMock && (
          <Typography variant="caption" color="warning.main" sx={{ display: "block", mb: 1 }}>
            ⚠️ ML service not connected — showing mock data
          </Typography>
        )}
        <PredictionChart
          forecast={prediction?.forecast ?? []}
          currentSpeed={currentSpeed}
          futureCongestion={prediction?.future_congestion ?? []}
        />
      </Box>
    </>
  );
}
