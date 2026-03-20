/**
 * Constants for HK Traffic Monitor frontend.
 */

export const API_BASE_URL = "http://localhost:8080/api";

export const HK_CENTER = { lat: 22.35, lng: 114.15 };

export const DEFAULT_ZOOM = 11;

export const STATUS_COLORS = {
  Normal: "#4caf50",
  "Normal Congestion": "#ff9800",
  "Abnormal Event": "#f44336",
  "Abnormal Congestion": "#d32f2f",
};

export const SPEED_COLORS = {
  good: "#4caf50",    // speed >= 60
  moderate: "#ff9800", // 30 <= speed < 60
  slow: "#f44336",    // speed < 30
  offline: "#9e9e9e", // valid="N"
};
