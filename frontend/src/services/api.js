/**
 * API client for HK Traffic Backend.
 */

import axios from "axios";
import { API_BASE_URL } from "../utils/constants";

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: { "Content-Type": "application/json" },
});

export async function fetchDetectors(sourceType) {
  const params = sourceType ? { source_type: sourceType } : {};
  const { data } = await api.get("/detectors/", { params });
  return data;
}

export async function fetchDetectorById(detectorId) {
  const { data } = await api.get(`/detectors/${detectorId}`);
  return data;
}

export async function fetchLatestReadings(sourceType) {
  const params = sourceType ? { source_type: sourceType } : {};
  const { data } = await api.get("/readings/latest", { params });
  return data;
}

export async function fetchReadingsHistory(
  detectorId,
  startTime,
  endTime,
  laneId
) {
  const params = { start_time: startTime, end_time: endTime };
  if (laneId) params.lane_id = laneId;
  const { data } = await api.get(`/readings/${detectorId}`, { params });
  return data;
}

export async function fetchDetectorLatest(detectorId) {
  const { data } = await api.get(`/readings/${detectorId}/latest`);
  return data;
}

export async function fetchOverviewStats() {
  const { data } = await api.get("/stats/overview");
  return data;
}

export async function fetchDistrictStats(sourceType) {
  const params = sourceType ? { source_type: sourceType } : {};
  const { data } = await api.get("/stats/district", { params });
  return data;
}

export async function fetchComparisonStats() {
  const { data } = await api.get("/stats/comparison");
  return data;
}

export async function fetchPrediction(detectorId, laneId) {
  const body = laneId ? { lane_id: laneId } : {};
  const { data } = await api.post(`/predict/${detectorId}`, body);
  return data;
}

export async function fetchRecentAnomalies(hours) {
  // Placeholder: use fetchLatestReadings until anomaly API exists
  const { data } = await api.get("/readings/latest");
  return data;
}
