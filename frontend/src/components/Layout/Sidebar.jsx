import { useNavigate, useLocation } from "react-router-dom";
import {
  Drawer,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Toolbar,
} from "@mui/material";
import DashboardIcon from "@mui/icons-material/Dashboard";
import MapIcon from "@mui/icons-material/Map";
import InfoOutlinedIcon from "@mui/icons-material/InfoOutlined";
import CompareArrowsIcon from "@mui/icons-material/CompareArrows";
import WarningIcon from "@mui/icons-material/Warning";

const DRAWER_WIDTH = 220;

const menuItems = [
  { path: "/", label: "Dashboard", icon: <DashboardIcon /> },
  { path: "/map", label: "Map", icon: <MapIcon /> },
  { path: "/detector", label: "Detector Detail", icon: <InfoOutlinedIcon /> },
  { path: "/comparison", label: "Comparison", icon: <CompareArrowsIcon /> },
  { path: "/anomalies", label: "Anomalies", icon: <WarningIcon /> },
];

export default function Sidebar() {
  const navigate = useNavigate();
  const location = useLocation();

  const isActive = (path) => {
    if (path === "/") return location.pathname === "/";
    if (path === "/detector")
      return location.pathname.startsWith("/detector/");
    return location.pathname.startsWith(path);
  };

  const handleClick = (path) => {
    if (path === "/detector") {
      navigate("/detector/AID01101");
    } else {
      navigate(path);
    }
  };

  return (
    <Drawer
      variant="permanent"
      sx={{
        width: DRAWER_WIDTH,
        flexShrink: 0,
        "& .MuiDrawer-paper": {
          width: DRAWER_WIDTH,
          boxSizing: "border-box",
          mt: 7,
          borderRight: 1,
          borderColor: "divider",
        },
      }}
    >
      <Toolbar />
      <List sx={{ pt: 2 }}>
        {menuItems.map(({ path, label, icon }) => (
          <ListItem key={path} disablePadding>
            <ListItemButton
              selected={isActive(path)}
              onClick={() => handleClick(path)}
              sx={{
                mx: 1,
                borderRadius: 1,
                "&.Mui-selected": {
                  bgcolor: "primary.light",
                  color: "primary.contrastText",
                  "&:hover": { bgcolor: "primary.main" },
                },
              }}
            >
              <ListItemIcon
                sx={{
                  color: "inherit",
                  minWidth: 40,
                }}
              >
                {icon}
              </ListItemIcon>
              <ListItemText primary={label} />
            </ListItemButton>
          </ListItem>
        ))}
      </List>
    </Drawer>
  );
}
