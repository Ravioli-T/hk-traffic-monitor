import { Box, Typography } from "@mui/material";
import { SPEED_COLORS } from "../../utils/constants";

const ITEMS = [
  { color: SPEED_COLORS.good, label: "≥60 km/h" },
  { color: SPEED_COLORS.moderate, label: "30-60 km/h" },
  { color: SPEED_COLORS.slow, label: "<30 km/h" },
  { color: SPEED_COLORS.offline, label: "Offline" },
];

export default function MapLegend() {
  return (
    <Box
      sx={{
        position: "absolute",
        bottom: 12,
        right: 12,
        zIndex: 1000,
        bgcolor: "rgba(255,255,255,0.95)",
        borderRadius: 1,
        px: 2,
        py: 1.5,
        boxShadow: 2,
      }}
    >
      <Typography variant="caption" fontWeight={600} sx={{ display: "block", mb: 0.5 }}>
        Speed
      </Typography>
      <Box sx={{ display: "flex", flexDirection: "column", gap: 0.5 }}>
        {ITEMS.map(({ color, label }) => (
          <Box key={label} sx={{ display: "flex", alignItems: "center", gap: 1 }}>
            <Box
              sx={{
                width: 12,
                height: 12,
                borderRadius: "50%",
                bgcolor: color,
                border: "1px solid #fff",
              }}
            />
            <Typography variant="caption">{label}</Typography>
          </Box>
        ))}
      </Box>
    </Box>
  );
}
