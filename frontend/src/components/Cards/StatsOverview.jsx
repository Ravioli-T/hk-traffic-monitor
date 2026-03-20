import { useState, useEffect } from "react";
import { Grid, Skeleton } from "@mui/material";
import DeviceHubIcon from "@mui/icons-material/DeviceHub";
import CheckCircleIcon from "@mui/icons-material/CheckCircle";
import CancelIcon from "@mui/icons-material/Cancel";
import WarningIcon from "@mui/icons-material/Warning";
import TrafficIcon from "@mui/icons-material/Traffic";
import EmojiObjectsIcon from "@mui/icons-material/EmojiObjects";
import StatsCard from "./StatsCard";
import { fetchOverviewStats } from "../../services/api";

const MOCK_STATS = {
  total_detectors: 523,
  online_count: 498,
  offline_count: 25,
  anomaly_count: 12,
  strategic_count: 480,
  lamppost_count: 43,
  last_update: "2024-03-15T14:30:00",
};

const CARDS = [
  {
    key: "total_detectors",
    title: "Total Detectors",
    valueKey: "total_detectors",
    icon: <DeviceHubIcon fontSize="small" />,
    color: "#2196f3",
  },
  {
    key: "online",
    title: "Online",
    valueKey: "online_count",
    icon: <CheckCircleIcon fontSize="small" />,
    color: "#4caf50",
  },
  {
    key: "offline",
    title: "Offline",
    valueKey: "offline_count",
    icon: <CancelIcon fontSize="small" />,
    color: "#9e9e9e",
  },
  {
    key: "anomalies",
    title: "Anomalies",
    valueKey: "anomaly_count",
    icon: <WarningIcon fontSize="small" />,
    color: "#f44336",
  },
  {
    key: "strategic",
    title: "Strategic",
    valueKey: "strategic_count",
    icon: <TrafficIcon fontSize="small" />,
    color: "#9c27b0",
  },
  {
    key: "lamppost",
    title: "Lamppost",
    valueKey: "lamppost_count",
    icon: <EmojiObjectsIcon fontSize="small" />,
    color: "#ff9800",
  },
];

export default function StatsOverview() {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      try {
        const data = await fetchOverviewStats();
        setStats(data);
      } catch (err) {
        setStats(MOCK_STATS);
      } finally {
        setLoading(false);
      }
    };
    load();
    const interval = setInterval(load, 60000);
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return (
      <Grid container spacing={2}>
        {CARDS.map((c) => (
          <Grid item xs={2} key={c.key}>
            <Skeleton variant="rounded" height={120} />
          </Grid>
        ))}
      </Grid>
    );
  }

  const data = stats || MOCK_STATS;

  return (
    <Grid container spacing={2}>
      {CARDS.map((c) => (
        <Grid item xs={2} key={c.key}>
          <StatsCard
            title={c.title}
            value={data[c.valueKey] ?? 0}
            icon={c.icon}
            color={c.color}
          />
        </Grid>
      ))}
    </Grid>
  );
}
