import { BrowserRouter, Routes, Route } from "react-router-dom";
import Layout from "./components/Layout/Layout";
import Dashboard from "./pages/Dashboard";
import FullMap from "./pages/FullMap";
import DetectorDetail from "./pages/DetectorDetail";
import Comparison from "./pages/Comparison";
import AnomalyList from "./pages/AnomalyList";

function App() {
  return (
    <BrowserRouter>
      <Layout>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/map" element={<FullMap />} />
          <Route path="/detector/:id" element={<DetectorDetail />} />
          <Route path="/comparison" element={<Comparison />} />
          <Route path="/anomalies" element={<AnomalyList />} />
        </Routes>
      </Layout>
    </BrowserRouter>
  );
}

export default App;
