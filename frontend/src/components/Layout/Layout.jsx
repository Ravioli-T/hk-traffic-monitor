import { Box } from "@mui/material";
import Header from "./Header";
import Sidebar from "./Sidebar";

export default function Layout({ children }) {
  return (
    <Box sx={{ display: "flex", minHeight: "100vh" }}>
      <Header />
      <Sidebar />
      <Box
        component="main"
        sx={{
          flexGrow: 1,
          ml: "220px",
          mt: 7,
          p: 3,
          minHeight: "100vh",
        }}
      >
        {children}
      </Box>
    </Box>
  );
}
