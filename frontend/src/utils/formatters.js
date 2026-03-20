/**
 * Formatting utilities for HK Traffic Monitor.
 */

import dayjs from "dayjs";
import { SPEED_COLORS } from "./constants";

export function formatTimestamp(ts) {
  return dayjs(ts).format("YYYY-MM-DD HH:mm:ss");
}

export function formatSpeed(speed) {
  return `${speed ?? 0} km/h`;
}

export function formatVolume(vol) {
  return `${vol ?? 0} veh/30s`;
}

export function getSpeedColor(speed, valid) {
  if (valid === "N" || valid === false) {
    return SPEED_COLORS.offline;
  }
  const s = Number(speed);
  if (s >= 60) return SPEED_COLORS.good;
  if (s >= 30) return SPEED_COLORS.moderate;
  return SPEED_COLORS.slow;
}

export function getStatusIcon(status) {
  const icons = {
    Normal: "✅",
    "Normal Congestion": "⚠️",
    "Abnormal Event": "🚨",
    "Abnormal Congestion": "🔴",
  };
  return icons[status] ?? "❓";
}
