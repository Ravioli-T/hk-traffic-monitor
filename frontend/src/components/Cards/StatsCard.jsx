import { Card, Typography, Box } from "@mui/material";

export default function StatsCard({ title, value, icon, color }) {
  return (
    <Card
      sx={{
        height: 120,
        display: "flex",
        alignItems: "stretch",
        overflow: "hidden",
        borderLeft: `4px solid ${color}`,
        borderRadius: 1,
        "&:hover": {
          boxShadow: 4,
        },
      }}
    >
      <Box
        sx={{
          display: "flex",
          flexDirection: "column",
          justifyContent: "center",
          p: 2,
          flex: 1,
        }}
      >
        <Box sx={{ display: "flex", alignItems: "center", gap: 1, mb: 0.5 }}>
          <Box sx={{ color, opacity: 0.9 }}>{icon}</Box>
          <Typography variant="caption" color="text.secondary">
            {title}
          </Typography>
        </Box>
        <Typography variant="h4" component="div" fontWeight={600}>
          {value}
        </Typography>
      </Box>
    </Card>
  );
}
