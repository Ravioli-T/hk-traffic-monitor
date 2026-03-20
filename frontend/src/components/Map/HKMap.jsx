import { useCallback, useEffect } from "react";
import { Link } from "react-router-dom";
import {
  MapContainer,
  TileLayer,
  CircleMarker,
  Popup,
  Tooltip,
  useMap,
} from "react-leaflet";
import { HK_CENTER, DEFAULT_ZOOM } from "../../utils/constants";
import { getSpeedColor } from "../../utils/formatters";

function MapFlyTo({ target }) {
  const map = useMap();
  useEffect(() => {
    if (target?.latitude != null && target?.longitude != null) {
      map.flyTo([target.latitude, target.longitude], target.zoom ?? 15, {
        duration: 1.5,
      });
    }
  }, [map, target?.latitude, target?.longitude, target?.zoom, target?._t]);
  return null;
}

function buildLatestByDetector(latestReadings) {
  const map = {};
  if (!Array.isArray(latestReadings)) return map;
  for (const r of latestReadings) {
    map[r.detector_id] = r;
  }
  return map;
}

function getDetectorColor(detectorId, latestByDetector) {
  const reading = latestByDetector[detectorId];
  if (!reading || !reading.lanes || reading.lanes.length === 0) {
    return "#9e9e9e";
  }
  const validLanes = reading.lanes.filter((l) => l.valid === "Y");
  if (validLanes.length === 0) {
    return "#9e9e9e";
  }
  const avgSpeed =
    validLanes.reduce((sum, l) => sum + Number(l.speed || 0), 0) /
    validLanes.length;
  return getSpeedColor(avgSpeed, "Y");
}

export default function HKMap({
  detectors = [],
  latestReadings = [],
  onDetectorClick,
  flyToTarget,
}) {
  const latestByDetector = useCallback(
    () => buildLatestByDetector(latestReadings),
    [latestReadings]
  );

  const byDetector = latestByDetector();

  return (
    <MapContainer
      center={[HK_CENTER.lat, HK_CENTER.lng]}
      zoom={DEFAULT_ZOOM}
      style={{ height: "100%", width: "100%" }}
      scrollWheelZoom={true}
    >
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      {flyToTarget && <MapFlyTo target={flyToTarget} />}
      {detectors.map((d) => {
        const lat = Number(d.latitude);
        const lng = Number(d.longitude);
        if (isNaN(lat) || isNaN(lng)) return null;

        const fillColor = getDetectorColor(d.detector_id, byDetector);
        const reading = byDetector[d.detector_id];
        const firstLane = reading?.lanes?.[0];

        return (
          <CircleMarker
            key={d.detector_id}
            center={[lat, lng]}
            radius={6}
            pathOptions={{
              fillColor,
              fillOpacity: 0.8,
              weight: 1,
              color: "#fff",
            }}
            eventHandlers={{
              click: () => onDetectorClick?.(d.detector_id),
            }}
          >
            <Tooltip>
              <strong>{d.detector_id}</strong>
              <br />
              {d.road_name_en || "—"}
            </Tooltip>
            <Popup>
              <div style={{ minWidth: 200 }}>
                <p>
                  <strong>{d.detector_id}</strong>
                </p>
                <p>Road: {d.road_name_en || "—"}</p>
                <p>District: {d.district || "—"}</p>
                <p>Direction: {d.direction || "—"}</p>
                {firstLane && (
                  <>
                    <hr style={{ margin: "8px 0" }} />
                    <p>Speed: {firstLane.speed ?? 0} km/h</p>
                    <p>Volume: {firstLane.volume ?? 0} veh/30s</p>
                    <p>Occupancy: {firstLane.occupancy ?? 0}%</p>
                  </>
                )}
                <hr style={{ margin: "8px 0" }} />
                <Link
                  to={`/detector/${d.detector_id}`}
                  style={{
                    fontSize: 14,
                    fontWeight: 600,
                    textDecoration: "none",
                    color: "#2196f3",
                  }}
                >
                  View Details →
                </Link>
              </div>
            </Popup>
          </CircleMarker>
        );
      })}
    </MapContainer>
  );
}
