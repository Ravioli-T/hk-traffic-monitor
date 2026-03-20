import { useState, useEffect, useCallback, useMemo } from "react";
import {
  Box,
  Paper,
  FormControlLabel,
  Radio,
  RadioGroup,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  TextField,
  InputAdornment,
  Typography,
  Button,
} from "@mui/material";
import SearchIcon from "@mui/icons-material/Search";
import HKMap from "../components/Map/HKMap";
import MapLegend from "../components/Map/MapLegend";
import { fetchDetectors, fetchLatestReadings } from "../services/api";

const MOCK_DETECTORS = [
  { detector_id: "AID01101", district: "Tuen Mun", road_name_en: "Tuen Mun Road", latitude: 22.3908, longitude: 113.9718, direction: "East", source_type: "strategic" },
  { detector_id: "AID02115", district: "Sha Tin", road_name_en: "Tolo Highway", latitude: 22.3964, longitude: 114.181, direction: "North", source_type: "strategic" },
  { detector_id: "TDS90081", district: "Wan Chai", road_name_en: "Gloucester Road", latitude: 22.2783, longitude: 114.1747, direction: "East", source_type: "lamppost" },
  { detector_id: "AID03021", district: "Central", road_name_en: "Connaught Road Central", latitude: 22.2865, longitude: 114.1572, direction: "West", source_type: "strategic" },
  { detector_id: "AID04011", district: "Kowloon City", road_name_en: "Prince Edward Road", latitude: 22.3245, longitude: 114.1712, direction: "East", source_type: "strategic" },
  { detector_id: "AID05031", district: "Kwun Tong", road_name_en: "Kwun Tong Road", latitude: 22.3122, longitude: 114.2256, direction: "South", source_type: "strategic" },
  { detector_id: "AID06021", district: "Tsuen Wan", road_name_en: "Tsuen Wan Road", latitude: 22.3712, longitude: 114.1123, direction: "North", source_type: "strategic" },
  { detector_id: "AID07015", district: "Yuen Long", road_name_en: "Yuen Long Highway", latitude: 22.4412, longitude: 114.0312, direction: "West", source_type: "strategic" },
  { detector_id: "LMP002", district: "Central", road_name_en: "Queen's Road Central", latitude: 22.2812, longitude: 114.1545, direction: "East", source_type: "lamppost" },
  { detector_id: "AID08041", district: "Mong Kok", road_name_en: "Nathan Road", latitude: 22.3189, longitude: 114.1698, direction: "South", source_type: "strategic" },
  { detector_id: "AID09022", district: "Tai Po", road_name_en: "Tai Po Road", latitude: 22.4523, longitude: 114.1654, direction: "North", source_type: "strategic" },
  { detector_id: "AID10033", district: "North", road_name_en: "Fanling Highway", latitude: 22.4912, longitude: 114.1423, direction: "East", source_type: "strategic" },
  { detector_id: "AID11051", district: "Aberdeen", road_name_en: "Aberdeen Tunnel Road", latitude: 22.2512, longitude: 114.1523, direction: "South", source_type: "strategic" },
  { detector_id: "AID12061", district: "Sham Shui Po", road_name_en: "Lai Chi Kok Road", latitude: 22.3312, longitude: 114.1589, direction: "West", source_type: "strategic" },
  { detector_id: "LMP003", district: "Causeway Bay", road_name_en: "Hennessy Road", latitude: 22.2767, longitude: 114.1823, direction: "East", source_type: "lamppost" },
  { detector_id: "AID13071", district: "Sai Kung", road_name_en: "Hiram's Highway", latitude: 22.3812, longitude: 114.2712, direction: "East", source_type: "strategic" },
  { detector_id: "AID14081", district: "Kwai Tsing", road_name_en: "Kwai Chung Road", latitude: 22.3612, longitude: 114.1256, direction: "South", source_type: "strategic" },
  { detector_id: "AID15091", district: "Islands", road_name_en: "North Lantau Highway", latitude: 22.3212, longitude: 113.9412, direction: "West", source_type: "strategic" },
  { detector_id: "AID16101", district: "Wong Tai Sin", road_name_en: "Lung Cheung Road", latitude: 22.3412, longitude: 114.2012, direction: "North", source_type: "strategic" },
  { detector_id: "LMP004", district: "Jordan", road_name_en: "Jordan Road", latitude: 22.3056, longitude: 114.1712, direction: "South", source_type: "lamppost" },
  { detector_id: "AID17111", district: "Eastern", road_name_en: "Island Eastern Corridor", latitude: 22.2812, longitude: 114.2212, direction: "East", source_type: "strategic" },
  { detector_id: "AID18121", district: "Southern", road_name_en: "Aberdeen Main Road", latitude: 22.2489, longitude: 114.1489, direction: "South", source_type: "strategic" },
  { detector_id: "AID19131", district: "Yau Tsim Mong", road_name_en: "Canton Road", latitude: 22.3012, longitude: 114.1656, direction: "South", source_type: "strategic" },
  { detector_id: "AID20141", district: "Sham Shui Po", road_name_en: "Cheung Sha Wan Road", latitude: 22.3356, longitude: 114.1512, direction: "West", source_type: "strategic" },
];

function buildMockReadings(detectors) {
  return detectors.map((d) => ({
    detector_id: d.detector_id,
    timestamp: new Date().toISOString(),
    lanes: [
      {
        lane_id: "Fast Lane",
        speed: 40 + Math.floor(Math.random() * 40),
        volume: 3 + Math.floor(Math.random() * 12),
        occupancy: 5 + Math.floor(Math.random() * 25),
        valid: "Y",
      },
    ],
  }));
}

export default function FullMap() {
  const [detectors, setDetectors] = useState([]);
  const [latestReadings, setLatestReadings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [sourceType, setSourceType] = useState("all");
  const [selectedDistricts, setSelectedDistricts] = useState([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [flyToTarget, setFlyToTarget] = useState(null);

  const loadData = useCallback(async () => {
    try {
      const [detData, readData] = await Promise.all([
        fetchDetectors(),
        fetchLatestReadings(),
      ]);
      setDetectors(Array.isArray(detData) ? detData : []);
      setLatestReadings(Array.isArray(readData) ? readData : []);
    } catch {
      setDetectors(MOCK_DETECTORS);
      setLatestReadings(buildMockReadings(MOCK_DETECTORS));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 60000);
    return () => clearInterval(interval);
  }, [loadData]);

  const districts = useMemo(() => {
    const set = new Set();
    detectors.forEach((d) => d.district && set.add(d.district));
    return Array.from(set).sort();
  }, [detectors]);

  const filteredDetectors = useMemo(() => {
    return detectors.filter((d) => {
      if (sourceType !== "all" && d.source_type !== sourceType) return false;
      if (selectedDistricts.length > 0 && !selectedDistricts.includes(d.district)) return false;
      return true;
    });
  }, [detectors, sourceType, selectedDistricts]);

  const handleSearch = () => {
    const q = searchQuery.trim().toUpperCase();
    if (!q) return;
    const found = detectors.find(
      (d) => d.detector_id.toUpperCase().includes(q) || q.includes(d.detector_id.toUpperCase())
    );
    if (found && found.latitude != null && found.longitude != null) {
      setFlyToTarget({
        latitude: Number(found.latitude),
        longitude: Number(found.longitude),
        zoom: 15,
        _t: Date.now(),
      });
    }
  };

  return (
    <Box
      sx={{
        position: "relative",
        height: "calc(100vh - 64px)",
        margin: -3,
        marginBottom: 0,
        overflow: "hidden",
      }}
    >
      <Box sx={{ position: "relative", height: "100%", width: "100%" }}>
        <HKMap
          detectors={filteredDetectors}
          latestReadings={latestReadings}
          flyToTarget={flyToTarget}
        />
        <MapLegend />

        {loading && (
          <Box
            sx={{
              position: "absolute",
              top: "50%",
              left: "50%",
              transform: "translate(-50%, -50%)",
              zIndex: 1000,
              bgcolor: "rgba(255,255,255,0.9)",
              px: 3,
              py: 2,
              borderRadius: 2,
              boxShadow: 3,
            }}
          >
            <Typography>Loading detectors...</Typography>
          </Box>
        )}

        <Paper
          sx={{
            position: "absolute",
            top: 16,
            left: 16,
            zIndex: 1000,
            p: 2,
            minWidth: 200,
          }}
        >
          <Typography variant="subtitle2" gutterBottom fontWeight={600}>
            Filters
          </Typography>
          <RadioGroup
            value={sourceType}
            onChange={(e) => setSourceType(e.target.value)}
            sx={{ mb: 2 }}
          >
            <FormControlLabel value="all" control={<Radio size="small" />} label="All" />
            <FormControlLabel value="strategic" control={<Radio size="small" />} label="Strategic" />
            <FormControlLabel value="lamppost" control={<Radio size="small" />} label="Lamppost" />
          </RadioGroup>
          <FormControl fullWidth size="small" sx={{ minWidth: 180 }}>
            <InputLabel>District</InputLabel>
            <Select
              multiple
              value={selectedDistricts}
              onChange={(e) => setSelectedDistricts(e.target.value)}
              label="District"
              renderValue={(v) => (v.length === 0 ? "All" : v.join(", "))}
            >
              {districts.map((d) => (
                <MenuItem key={d} value={d}>
                  {d}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </Paper>

        <Paper
          sx={{
            position: "absolute",
            top: 16,
            right: 16,
            zIndex: 1000,
            p: 2,
          }}
        >
          <Box sx={{ display: "flex", gap: 1, alignItems: "center" }}>
            <TextField
              size="small"
              placeholder="Search detector_id"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleSearch()}
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <SearchIcon fontSize="small" />
                  </InputAdornment>
                ),
              }}
              sx={{ width: 200 }}
            />
            <Button variant="contained" size="small" onClick={handleSearch}>
              Search
            </Button>
          </Box>
        </Paper>
      </Box>
    </Box>
  );
}
