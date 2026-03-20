import { Card, CardContent, Grid, Typography, Chip, Box } from "@mui/material";
import { STATUS_COLORS } from "../../utils/constants";

export default function DetectorInfoCard({
  detector = {},
  latestReading = null,
  predictionStatus = "Normal",
  explanation = "",
}) {
  const firstLane = latestReading?.lanes?.[0];
  const speed = firstLane?.speed ?? 0;
  const volume = firstLane?.volume ?? 0;
  const occupancy = firstLane?.occupancy ?? 0;
  const statusColor = STATUS_COLORS[predictionStatus] ?? STATUS_COLORS.Normal;

  return (
    <Card sx={{ height: "100%" }}>
      <CardContent>
        <Grid container spacing={2}>
          <Grid item xs={6}>
            <Typography variant="overline" color="text.secondary">
              Detector ID
            </Typography>
            <Typography variant="body1" fontWeight={600}>
              {detector.detector_id || "—"}
            </Typography>
            <Typography variant="overline" color="text.secondary" sx={{ mt: 1, display: "block" }}>
              District
            </Typography>
            <Typography variant="body2">{detector.district || "—"}</Typography>
            <Typography variant="overline" color="text.secondary" sx={{ mt: 1, display: "block" }}>
              Road
            </Typography>
            <Typography variant="body2">{detector.road_name_en || "—"}</Typography>
            <Typography variant="overline" color="text.secondary" sx={{ mt: 1, display: "block" }}>
              Direction
            </Typography>
            <Typography variant="body2">{detector.direction || "—"}</Typography>
            <Typography variant="overline" color="text.secondary" sx={{ mt: 1, display: "block" }}>
              Source
            </Typography>
            <Typography variant="body2">{detector.source_type || "—"}</Typography>
          </Grid>
          <Grid item xs={6}>
            <Typography variant="overline" color="text.secondary">
              Current Speed
            </Typography>
            <Typography variant="h4" fontWeight={700} color="primary.main">
              {speed} km/h
            </Typography>
            <Typography variant="overline" color="text.secondary" sx={{ mt: 1, display: "block" }}>
              Volume
            </Typography>
            <Typography variant="h5" fontWeight={600}>
              {volume} veh/30s
            </Typography>
            <Typography variant="overline" color="text.secondary" sx={{ mt: 1, display: "block" }}>
              Occupancy
            </Typography>
            <Typography variant="h5" fontWeight={600}>
              {occupancy}%
            </Typography>
            <Box sx={{ mt: 2 }}>
              <Chip
                label={predictionStatus}
                size="small"
                sx={{
                  bgcolor: statusColor,
                  color: "white",
                  fontWeight: 600,
                }}
              />
            </Box>
            {explanation && (
              <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: "block" }}>
                {explanation}
              </Typography>
            )}
          </Grid>
        </Grid>
      </CardContent>
    </Card>
  );
}
