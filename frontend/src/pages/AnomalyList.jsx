import { useState, useMemo, useEffect } from "react";
import { Link } from "react-router-dom";
import {
  Typography,
  Box,
  Grid,
  Card,
  CardContent,
  ButtonGroup,
  Button,
  Chip,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
} from "@mui/material";
import ReactECharts from "echarts-for-react";
import dayjs from "dayjs";
import { fetchRecentAnomalies } from "../services/api";
import { formatTimestamp } from "../utils/formatters";

const DISTRICTS = ["Central", "Kowloon City", "Kwun Tong", "Sha Tin", "Tuen Mun", "Wan Chai", "Yau Tsim Mong"];
const ROADS = ["Nathan Road", "Queen's Road", "Tolo Highway", "Tuen Mun Road", "Gloucester Road", "Prince Edward Road", "Kwun Tong Road"];

function generateMockAnomalies() {
  const items = [];
  const now = dayjs();
  const statuses = [
    ...Array(12).fill("Abnormal Event"),
    ...Array(8).fill("Abnormal Congestion"),
  ];
  for (let i = 0; i < 20; i++) {
    const status = statuses[i];
    let speed, volume, occupancy, explanation;
    if (status === "Abnormal Event") {
      const isLow = Math.random() > 0.5;
      speed = isLow ? 5 + Math.floor(Math.random() * 12) : 102 + Math.floor(Math.random() * 25);
      volume = 2 + Math.floor(Math.random() * 6);
      occupancy = isLow ? 35 + Math.floor(Math.random() * 40) : 5 + Math.floor(Math.random() * 15);
      explanation = isLow
        ? "Speed dropped below 15 km/h — possible incident or heavy congestion"
        : "Unusual speed spike detected — incident clearance or sensor anomaly";
    } else {
      speed = 8 + Math.floor(Math.random() * 18);
      volume = 18 + Math.floor(Math.random() * 25);
      occupancy = 45 + Math.floor(Math.random() * 35);
      explanation = "High volume with low speed — congestion pattern detected";
    }
    const hoursAgo = Math.random() * 24;
    const timestamp = now.subtract(hoursAgo, "hour").toISOString();
    const district = DISTRICTS[Math.floor(Math.random() * DISTRICTS.length)];
    const road = ROADS[Math.floor(Math.random() * ROADS.length)];
    items.push({
      id: `a${i + 1}`,
      timestamp,
      detector_id: `AID${String(10000 + i).slice(1)}`,
      lane_id: ["Fast Lane", "Slow Lane", "Middle Lane"][Math.floor(Math.random() * 3)],
      speed,
      volume,
      occupancy,
      status,
      explanation,
      district,
      road_name_en: road,
    });
  }
  return items.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));
}

const MOCK_ANOMALIES = generateMockAnomalies();

export default function AnomalyList() {
  const [timeRange, setTimeRange] = useState(24);
  const [statusFilter, setStatusFilter] = useState("all");
  const [districtFilter, setDistrictFilter] = useState("");
  const [anomalies, setAnomalies] = useState(MOCK_ANOMALIES);

  useEffect(() => {
    const load = async () => {
      try {
        const data = await fetchRecentAnomalies(24);
        if (Array.isArray(data) && data.some((d) => d.detector_id && d.status)) {
          const mapped = data.map((item, i) => ({
            id: item.id ?? `a${i}`,
            timestamp: item.timestamp ?? item.time ?? new Date().toISOString(),
            detector_id: item.detector_id ?? "—",
            lane_id: item.lane_id ?? (item.lanes?.[0]?.lane_id) ?? "—",
            speed: item.speed ?? item.lanes?.[0]?.speed ?? 0,
            volume: item.volume ?? item.lanes?.[0]?.volume ?? 0,
            occupancy: item.occupancy ?? item.lanes?.[0]?.occupancy ?? 0,
            status: item.status ?? "Abnormal Event",
            explanation: item.explanation ?? "",
            district: item.district ?? "—",
            road_name_en: item.road_name_en ?? item.road ?? "—",
          }));
          setAnomalies(mapped.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp)));
        }
      } catch {
        setAnomalies(MOCK_ANOMALIES);
      }
    };
    load();
  }, []);

  const filteredAnomalies = useMemo(() => {
    return anomalies.filter((a) => {
      if (statusFilter !== "all" && a.status !== statusFilter) return false;
      if (districtFilter && a.district !== districtFilter) return false;
      const cutoff = dayjs().subtract(timeRange, "hour");
      if (new Date(a.timestamp) < cutoff) return false;
      return true;
    });
  }, [anomalies, statusFilter, districtFilter, timeRange]);

  const stats = useMemo(() => {
    const total = filteredAnomalies.length;
    const congestion = filteredAnomalies.filter((a) => a.status === "Abnormal Congestion").length;
    const events = filteredAnomalies.filter((a) => a.status === "Abnormal Event").length;
    return { total, congestion, events };
  }, [filteredAnomalies]);

  const hourlyDistribution = useMemo(() => {
    const byHour = Array(24).fill(0).map((_, i) => ({ hour: i, congestion: 0, event: 0 }));
    filteredAnomalies.forEach((a) => {
      const h = dayjs(a.timestamp).hour();
      if (a.status === "Abnormal Congestion") byHour[h].congestion++;
      else byHour[h].event++;
    });
    return byHour;
  }, [filteredAnomalies]);

  const chartOption = useMemo(() => ({
    title: { text: "Anomaly Distribution by Hour", left: "center" },
    tooltip: { trigger: "axis" },
    legend: { data: ["Abnormal Congestion", "Abnormal Event"], top: 10 },
    grid: { left: "3%", right: "4%", bottom: "3%", top: "18%", containLabel: true },
    xAxis: {
      type: "category",
      data: Array.from({ length: 24 }, (_, i) => `${i}:00`),
    },
    yAxis: { type: "value", name: "Count" },
    series: [
      { name: "Abnormal Congestion", type: "bar", stack: "total", data: hourlyDistribution.map((d) => d.congestion), itemStyle: { color: "#d32f2f" } },
      { name: "Abnormal Event", type: "bar", stack: "total", data: hourlyDistribution.map((d) => d.event), itemStyle: { color: "#ff9800" } },
    ],
  }), [hourlyDistribution]);

  const districts = useMemo(() => {
    const set = new Set(anomalies.map((a) => a.district).filter(Boolean));
    return Array.from(set).sort();
  }, [anomalies]);

  return (
    <>
      <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", mb: 2 }}>
        <Box>
          <Typography variant="h4" gutterBottom>
            Recent Anomaly Events
          </Typography>
          <Typography variant="subtitle1" color="text.secondary">
            Detected by Isolation Forest (contamination=2%)
          </Typography>
        </Box>
        <ButtonGroup size="small">
          {[1, 6, 12, 24].map((h) => (
            <Button
              key={h}
              variant={timeRange === h ? "contained" : "outlined"}
              onClick={() => setTimeRange(h)}
            >
              {h}h
            </Button>
          ))}
        </ButtonGroup>
      </Box>

      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="overline" color="text.secondary">
                Total Anomalies
              </Typography>
              <Typography variant="h4" fontWeight={700}>
                {stats.total}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={4}>
          <Card sx={{ borderLeft: "4px solid #d32f2f" }}>
            <CardContent>
              <Typography variant="overline" color="text.secondary">
                Abnormal Congestion
              </Typography>
              <Typography variant="h4" fontWeight={700} color="#d32f2f">
                {stats.congestion}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={4}>
          <Card sx={{ borderLeft: "4px solid #ff9800" }}>
            <CardContent>
              <Typography variant="overline" color="text.secondary">
                Abnormal Events
              </Typography>
              <Typography variant="h4" fontWeight={700} color="#ff9800">
                {stats.events}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      <Box sx={{ mb: 2, display: "flex", gap: 2, alignItems: "center", flexWrap: "wrap" }}>
        <Box sx={{ display: "flex", gap: 0.5 }}>
          <Chip
            label="All"
            variant={statusFilter === "all" ? "filled" : "outlined"}
            onClick={() => setStatusFilter("all")}
            color={statusFilter === "all" ? "primary" : "default"}
          />
          <Chip
            label="Abnormal Congestion"
            variant={statusFilter === "Abnormal Congestion" ? "filled" : "outlined"}
            onClick={() => setStatusFilter("Abnormal Congestion")}
            sx={{ color: statusFilter === "Abnormal Congestion" ? "#d32f2f" : undefined }}
          />
          <Chip
            label="Abnormal Event"
            variant={statusFilter === "Abnormal Event" ? "filled" : "outlined"}
            onClick={() => setStatusFilter("Abnormal Event")}
            sx={{ color: statusFilter === "Abnormal Event" ? "#ff9800" : undefined }}
          />
        </Box>
        <FormControl size="small" sx={{ minWidth: 180 }}>
          <InputLabel>District</InputLabel>
          <Select
            value={districtFilter}
            onChange={(e) => setDistrictFilter(e.target.value)}
            label="District"
          >
            <MenuItem value="">All</MenuItem>
            {districts.map((d) => (
              <MenuItem key={d} value={d}>
                {d}
              </MenuItem>
            ))}
          </Select>
        </FormControl>
      </Box>

      <TableContainer component={Paper} sx={{ mb: 3, maxHeight: 500 }}>
        <Table stickyHeader size="small">
          <TableHead>
            <TableRow>
              <TableCell>Time</TableCell>
              <TableCell>Detector ID</TableCell>
              <TableCell>District</TableCell>
              <TableCell>Road</TableCell>
              <TableCell>Lane</TableCell>
              <TableCell align="right">Speed</TableCell>
              <TableCell align="right">Volume</TableCell>
              <TableCell>Status</TableCell>
              <TableCell sx={{ maxWidth: 280 }}>Explanation</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {filteredAnomalies.map((row) => (
              <TableRow key={row.id} hover>
                <TableCell>{formatTimestamp(row.timestamp)}</TableCell>
                <TableCell>
                  <Link
                    to={`/detector/${row.detector_id}`}
                    style={{ color: "#2196f3", textDecoration: "none", fontWeight: 600 }}
                  >
                    {row.detector_id}
                  </Link>
                </TableCell>
                <TableCell>{row.district}</TableCell>
                <TableCell>{row.road_name_en}</TableCell>
                <TableCell>{row.lane_id}</TableCell>
                <TableCell align="right">{row.speed} km/h</TableCell>
                <TableCell align="right">{row.volume}</TableCell>
                <TableCell>
                  <Chip
                    label={row.status}
                    size="small"
                    sx={{
                      bgcolor: row.status === "Abnormal Congestion" ? "rgba(211,47,47,0.2)" : "rgba(255,152,0,0.2)",
                      color: row.status === "Abnormal Congestion" ? "#d32f2f" : "#ff9800",
                      fontWeight: 600,
                    }}
                  />
                </TableCell>
                <TableCell sx={{ maxWidth: 280 }}>{row.explanation}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      <Box sx={{ mb: 3 }}>
        <ReactECharts option={chartOption} style={{ height: 350 }} notMerge />
      </Box>

      <Typography variant="body2" color="text.secondary" sx={{ fontStyle: "italic" }}>
        ℹ️ Anomaly detection is powered by Isolation Forest model. ML service integration pending —
        currently showing sample data.
      </Typography>
    </>
  );
}
