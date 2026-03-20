import {
  MapContainer,
  TileLayer,
  CircleMarker,
  Tooltip,
  useMap,
} from "react-leaflet";
import { useEffect } from "react";
import { HK_CENTER, DEFAULT_ZOOM } from "../../utils/constants";

function MapCenter({ lat, lng }) {
  const map = useMap();
  useEffect(() => {
    if (lat != null && lng != null && !isNaN(lat) && !isNaN(lng)) {
      map.setView([lat, lng], 14);
    }
  }, [map, lat, lng]);
  return null;
}

export default function MiniMap({
  latitude,
  longitude,
  detectorId = "",
}) {
  const lat = Number(latitude);
  const lng = Number(longitude);
  const valid = !isNaN(lat) && !isNaN(lng);

  return (
    <div style={{ height: 200, width: "100%", borderRadius: 8, overflow: "hidden" }}>
      <MapContainer
        center={valid ? [lat, lng] : [HK_CENTER.lat, HK_CENTER.lng]}
        zoom={valid ? 14 : DEFAULT_ZOOM}
        style={{ height: "100%", width: "100%" }}
        scrollWheelZoom={false}
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        {valid && (
          <>
            <MapCenter lat={lat} lng={lng} />
            <CircleMarker
              center={[lat, lng]}
              radius={8}
              pathOptions={{
                fillColor: "#2196f3",
                fillOpacity: 0.8,
                weight: 2,
                color: "#fff",
              }}
            >
              <Tooltip>
                <strong>{detectorId || "Detector"}</strong>
              </Tooltip>
            </CircleMarker>
          </>
        )}
      </MapContainer>
    </div>
  );
}
