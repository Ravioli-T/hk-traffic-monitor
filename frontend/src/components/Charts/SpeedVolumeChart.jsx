import ReactECharts from "echarts-for-react";
import { useMemo } from "react";
import dayjs from "dayjs";

export default function SpeedVolumeChart({
  data = [],
  title = "",
  anomalyPoints = [],
}) {
  const option = useMemo(() => {
    const sorted = [...data].sort(
      (a, b) => new Date(a.timestamp) - new Date(b.timestamp)
    );
    const timestamps = sorted.map((d) => d.timestamp);
    const speeds = sorted.map((d) => d.speed ?? null);
    const volumes = sorted.map((d) => d.volume ?? null);

    const series = [
      {
        name: "Speed",
        type: "line",
        yAxisIndex: 0,
        data: speeds,
        smooth: true,
        itemStyle: { color: "#2196f3" },
        lineStyle: { color: "#2196f3" },
      },
      {
        name: "Volume",
        type: "line",
        yAxisIndex: 1,
        data: volumes,
        smooth: true,
        itemStyle: { color: "#4caf50" },
        lineStyle: { color: "#4caf50" },
      },
    ];

    if (anomalyPoints && anomalyPoints.length > 0) {
      const anomalyData = anomalyPoints.map((p) => {
        const ts = typeof p === "object" ? p.timestamp : p;
        const idx = timestamps.findIndex((t) => t === ts || t?.includes?.(ts));
        const speed = idx >= 0 ? speeds[idx] : null;
        return [ts, speed];
      }).filter(([, v]) => v != null);
      series.push({
        name: "Anomaly",
        type: "scatter",
        yAxisIndex: 0,
        data: anomalyData,
        symbolSize: 10,
        itemStyle: { color: "#f44336" },
      });
    }

    return {
      title: title ? { text: title, left: 0, top: 0 } : undefined,
      tooltip: {
        trigger: "axis",
        axisPointer: { type: "cross" },
      },
      legend: {
        data: series.map((s) => s.name),
        top: 0,
        right: 0,
      },
      grid: {
        left: "3%",
        right: "4%",
        bottom: "15%",
        top: "15%",
        containLabel: true,
      },
      dataZoom: [
        { type: "inside", start: 0, end: 100 },
        { type: "slider", start: 0, end: 100, bottom: 10 },
      ],
      xAxis: {
        type: "category",
        boundaryGap: false,
        data: timestamps.map((t) => dayjs(t).format("HH:mm")),
        axisLabel: { rotate: 45 },
      },
      yAxis: [
        {
          type: "value",
          name: "Speed (km/h)",
          position: "left",
          axisLine: { show: true, lineStyle: { color: "#2196f3" } },
          splitLine: { show: false },
        },
        {
          type: "value",
          name: "Volume",
          position: "right",
          axisLine: { show: true, lineStyle: { color: "#4caf50" } },
          splitLine: { show: false },
        },
      ],
      series,
    };
  }, [data, title, anomalyPoints]);

  return (
    <ReactECharts
      option={option}
      style={{ height: 400 }}
      notMerge
    />
  );
}
