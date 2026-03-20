import { useState, useEffect } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import {
  AppBar,
  Toolbar,
  Typography,
  Button,
  Box,
} from "@mui/material";
import DashboardIcon from "@mui/icons-material/Dashboard";
import MapIcon from "@mui/icons-material/Map";
import CompareArrowsIcon from "@mui/icons-material/CompareArrows";
import WarningIcon from "@mui/icons-material/Warning";
import dayjs from "dayjs";

const navItems = [
  { path: "/", label: "Dashboard", icon: <DashboardIcon /> },
  { path: "/map", label: "Map", icon: <MapIcon /> },
  { path: "/comparison", label: "Comparison", icon: <CompareArrowsIcon /> },
  { path: "/anomalies", label: "Anomalies", icon: <WarningIcon /> },
];

export default function Header() {
  const navigate = useNavigate();
  const location = useLocation();
  const [currentTime, setCurrentTime] = useState(dayjs().format("HH:mm:ss"));

  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentTime(dayjs().format("HH:mm:ss"));
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  return (
    <AppBar position="fixed" sx={{ zIndex: (theme) => theme.zIndex.drawer + 1 }}>
      <Toolbar>
        <Typography
          variant="h6"
          component="div"
          sx={{ flexGrow: 1, fontWeight: 600, cursor: "pointer" }}
          onClick={() => navigate("/")}
        >
          HK Smart Traffic Monitor
        </Typography>
        <Box sx={{ display: "flex", gap: 1, alignItems: "center" }}>
          {navItems.map(({ path, label, icon }) => (
            <Button
              key={path}
              color="inherit"
              startIcon={icon}
              onClick={() => navigate(path)}
              variant={location.pathname === path ? "outlined" : "text"}
              sx={{
                borderColor: "rgba(255,255,255,0.5)",
                "&:hover": { borderColor: "white" },
              }}
            >
              {label}
            </Button>
          ))}
          <Typography
            variant="body2"
            sx={{
              ml: 2,
              px: 1.5,
              py: 0.5,
              bgcolor: "rgba(255,255,255,0.15)",
              borderRadius: 1,
              fontFamily: "monospace",
            }}
          >
            {currentTime}
          </Typography>
        </Box>
      </Toolbar>
    </AppBar>
  );
}
