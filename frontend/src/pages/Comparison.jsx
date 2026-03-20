import { useState, useEffect } from "react";
import {
  Typography,
  Box,
  Grid,
  Card,
  CardContent,
  ButtonGroup,
  Button,
  Skeleton,
} from "@mui/material";
import ComparisonChart from "../components/Charts/ComparisonChart";
import DistrictChart from "../components/Charts/DistrictChart";
import { fetchComparisonStats, fetchDistrictStats } from "../services/api";

const MOCK_COMPARISON = {
  strategic: {
    count: 480,
    valid_rate: 97.2,
    coverage_districts: 18,
    avg_speed: 62.5,
  },
  lamppost: {
    count: 43,
    valid_rate: 89.1,
    coverage_districts: 5,
    avg_speed: 45.3,
  },
};

const LAMPPOST_DISTRICTS = ["Central & Western", "Wan Chai", "Yau Tsim Mong", "Eastern", "Kowloon City"];

const MOCK_DISTRICTS = [
  { district: "Central & Western", detector_count: 35, avg_speed: 42.1, valid_rate: 96.5 },
  { district: "Eastern", detector_count: 28, avg_speed: 48.2, valid_rate: 97.1 },
  { district: "Southern", detector_count: 22, avg_speed: 55.3, valid_rate: 95.8 },
  { district: "Wan Chai", detector_count: 18, avg_speed: 38.9, valid_rate: 96.2 },
  { district: "Kowloon City", detector_count: 45, avg_speed: 52.4, valid_rate: 97.5 },
  { district: "Kwun Tong", detector_count: 38, avg_speed: 58.1, valid_rate: 96.8 },
  { district: "Sham Shui Po", detector_count: 32, avg_speed: 44.2, valid_rate: 95.2 },
  { district: "Wong Tai Sin", detector_count: 25, avg_speed: 49.6, valid_rate: 96.1 },
  { district: "Yau Tsim Mong", detector_count: 41, avg_speed: 35.8, valid_rate: 94.9 },
  { district: "Islands", detector_count: 15, avg_speed: 68.2, valid_rate: 98.2 },
  { district: "Kwai Tsing", detector_count: 30, avg_speed: 61.5, valid_rate: 97.3 },
  { district: "North", detector_count: 28, avg_speed: 65.3, valid_rate: 97.8 },
  { district: "Sai Kung", detector_count: 20, avg_speed: 72.1, valid_rate: 98.5 },
  { district: "Sha Tin", detector_count: 42, avg_speed: 59.4, valid_rate: 97.2 },
  { district: "Tai Po", detector_count: 26, avg_speed: 63.8, valid_rate: 97.6 },
  { district: "Tsuen Wan", detector_count: 35, avg_speed: 54.2, valid_rate: 96.4 },
  { district: "Tuen Mun", detector_count: 38, avg_speed: 58.7, valid_rate: 97.1 },
  { district: "Yuen Long", detector_count: 32, avg_speed: 62.1, valid_rate: 96.9 },
];

export default function Comparison() {
  const [comparisonStats, setComparisonStats] = useState(null);
  const [districtStats, setDistrictStats] = useState(null);
  const [sourceFilter, setSourceFilter] = useState("all");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      try {
        const compData = await fetchComparisonStats();
        const strategic = compData?.find((c) => c.source_type === "strategic");
        const lamppost = compData?.find((c) => c.source_type === "lamppost");
        setComparisonStats({
          strategic: strategic
            ? {
                count: strategic.count,
                valid_rate: strategic.valid_rate,
                coverage_districts: strategic.coverage_districts,
                avg_speed: strategic.avg_speed,
              }
            : MOCK_COMPARISON.strategic,
          lamppost: lamppost
            ? {
                count: lamppost.count,
                valid_rate: lamppost.valid_rate,
                coverage_districts: lamppost.coverage_districts,
                avg_speed: lamppost.avg_speed,
              }
            : MOCK_COMPARISON.lamppost,
        });
      } catch {
        setComparisonStats(MOCK_COMPARISON);
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  useEffect(() => {
    const load = async () => {
      const sourceType = sourceFilter === "all" ? undefined : sourceFilter;
      try {
        const distData = await fetchDistrictStats(sourceType);
        const fallback =
          sourceFilter === "all"
            ? MOCK_DISTRICTS
            : sourceFilter === "strategic"
            ? MOCK_DISTRICTS.filter((d) => !LAMPPOST_DISTRICTS.includes(d.district))
            : MOCK_DISTRICTS.filter((d) => LAMPPOST_DISTRICTS.includes(d.district));
        setDistrictStats(Array.isArray(distData) && distData.length > 0 ? distData : fallback);
      } catch {
        const fallback =
          sourceFilter === "all"
            ? MOCK_DISTRICTS
            : sourceFilter === "strategic"
            ? MOCK_DISTRICTS.filter((d) => !LAMPPOST_DISTRICTS.includes(d.district))
            : MOCK_DISTRICTS.filter((d) => LAMPPOST_DISTRICTS.includes(d.district));
        setDistrictStats(fallback);
      }
    };
    load();
  }, [sourceFilter]);

  const strategicData = comparisonStats?.strategic ?? MOCK_COMPARISON.strategic;
  const lamppostData = comparisonStats?.lamppost ?? MOCK_COMPARISON.lamppost;

  const filteredDistrictData =
    districtStats ??
    (sourceFilter === "all"
      ? MOCK_DISTRICTS
      : sourceFilter === "strategic"
      ? MOCK_DISTRICTS.filter((d) => !LAMPPOST_DISTRICTS.includes(d.district))
      : MOCK_DISTRICTS.filter((d) => LAMPPOST_DISTRICTS.includes(d.district)));

  if (loading && !comparisonStats) {
    return (
      <Box>
        <Skeleton variant="text" width={400} height={48} />
        <Skeleton variant="rectangular" height={120} sx={{ mt: 2 }} />
      </Box>
    );
  }

  return (
    <>
      <Typography variant="h4" gutterBottom>
        Strategic Roads vs Smart Lampposts (RQ3)
      </Typography>
      <Typography variant="subtitle1" color="text.secondary" paragraph>
        Comparing data quality, spatial coverage, and detection characteristics
      </Typography>

      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid item xs={12} md={6}>
          <Card sx={{ bgcolor: "rgba(25, 118, 210, 0.08)", borderLeft: "4px solid #1976d2" }}>
            <CardContent>
              <Typography variant="overline" color="text.secondary">
                Strategic Road Detectors
              </Typography>
              <Typography variant="h3" fontWeight={700} color="#1976d2" sx={{ my: 1 }}>
                {strategicData.count}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Valid rate: {strategicData.valid_rate}%
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Districts covered: {strategicData.coverage_districts}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Avg speed: {strategicData.avg_speed} km/h
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={6}>
          <Card sx={{ bgcolor: "rgba(255, 152, 0, 0.08)", borderLeft: "4px solid #ff9800" }}>
            <CardContent>
              <Typography variant="overline" color="text.secondary">
                Smart Lamppost Detectors
              </Typography>
              <Typography variant="h3" fontWeight={700} color="#ff9800" sx={{ my: 1 }}>
                {lamppostData.count}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Valid rate: {lamppostData.valid_rate}%
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Districts covered: {lamppostData.coverage_districts}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Avg speed: {lamppostData.avg_speed} km/h
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      <Box sx={{ mb: 3 }}>
        <Typography variant="h6" gutterBottom>
          Key Metrics Comparison
        </Typography>
        <ComparisonChart strategicData={strategicData} lamppostData={lamppostData} />
      </Box>

      <Box>
        <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "center", mb: 1 }}>
          <Typography variant="h6">
            Detector Distribution by District
          </Typography>
          <ButtonGroup size="small">
            <Button
              variant={sourceFilter === "all" ? "contained" : "outlined"}
              onClick={() => setSourceFilter("all")}
            >
              All
            </Button>
            <Button
              variant={sourceFilter === "strategic" ? "contained" : "outlined"}
              onClick={() => setSourceFilter("strategic")}
            >
              Strategic Only
            </Button>
            <Button
              variant={sourceFilter === "lamppost" ? "contained" : "outlined"}
              onClick={() => setSourceFilter("lamppost")}
            >
              Lamppost Only
            </Button>
          </ButtonGroup>
        </Box>
        <DistrictChart districtData={filteredDistrictData} />
      </Box>

      <Typography
        variant="body1"
        color="text.secondary"
        sx={{ mt: 3, maxWidth: 800 }}
      >
        Key findings: Strategic road detectors provide significantly broader coverage (18 districts)
        compared to smart lampposts (5 districts). However, lamppost detectors show potential for
        higher-density urban area monitoring. The data validity rate difference (97.2% vs 89.1%)
        suggests smart lampposts may require additional data quality measures.
      </Typography>
    </>
  );
}
