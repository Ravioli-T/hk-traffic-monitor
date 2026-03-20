import ReactECharts from "echarts-for-react";
import { useMemo } from "react";
import dayjs from "dayjs";

export default function PredictionChart({
  forecast = [],
  currentSpeed = 0,
  futureCongestion = [],
}) {
  const option = useMemo(() => {
    const times = forecast.map((f) => dayjs(f.time).format("HH:mm"));
    const predSpeeds = forecast.map((f) => f.pred_speed);
    const predVolumes = forecast.map((f) => f.pred_volume);
    const speedLower = forecast.map((f) => f.speed_lower);
    const speedUpper = forecast.map((f) => f.speed_upper);

    const markAreaData = [];
    for (let i = 0; i < futureCongestion.length; i++) {
      if (futureCongestion[i] === 1 && i < times.length) {
        const start = i;
        let end = i;
        while (end < futureCongestion.length && futureCongestion[end] === 1) {
          end++;
        }
        markAreaData.push([
          { xAxis: start, itemStyle: { color: "rgba(244,67,54,0.2)" } },
          { xAxis: Math.min(end, times.length - 1), itemStyle: { color: "rgba(244,67,54,0.2)" } },
        ]);
        i = end - 1;
      }
    }

    const predSpeedSeries = {
      name: "Pred Speed",
      type: "line",
      yAxisIndex: 0,
      data: predSpeeds,
      smooth: true,
      itemStyle: { color: "#2196f3" },
      lineStyle: { color: "#2196f3", width: 2 },
      markLine: {
        data: [
          {
            yAxis: currentSpeed,
            lineStyle: { type: "dashed", color: "#9e9e9e" },
            label: { formatter: `Current: ${currentSpeed} km/h` },
          },
        ],
      },
      markArea: markAreaData.length > 0 ? { data: markAreaData } : undefined,
    };

    const series = [
      {
        name: "Conf (lower)",
        type: "line",
        yAxisIndex: 0,
        data: speedLower,
        lineStyle: { width: 0 },
        stack: "band",
        areaStyle: { color: "transparent" },
        symbol: "none",
      },
      {
        name: "Conf (upper)",
        type: "line",
        yAxisIndex: 0,
        data: speedUpper.map((u, i) => (u || 0) - (speedLower[i] || 0)),
        lineStyle: { width: 0 },
        stack: "band",
        areaStyle: { color: "rgba(33, 150, 243, 0.3)" },
        symbol: "none",
      },
      predSpeedSeries,
      {
        name: "Pred Volume",
        type: "line",
        yAxisIndex: 1,
        data: predVolumes,
        smooth: true,
        lineStyle: { color: "#4caf50", type: "dashed", width: 2 },
        itemStyle: { color: "#4caf50" },
      },
    ];

    return {
      tooltip: {
        trigger: "axis",
        axisPointer: { type: "cross" },
      },
      legend: {
        data: ["Pred Speed", "Pred Volume"],
        top: 0,
      },
      grid: {
        left: "3%",
        right: "4%",
        bottom: "12%",
        top: "12%",
        containLabel: true,
      },
      xAxis: {
        type: "category",
        boundaryGap: false,
        data: times,
        axisLabel: { formatter: (v) => v },
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
  }, [forecast, currentSpeed, futureCongestion]);

  return (
    <ReactECharts
      option={option}
      style={{ height: 350 }}
      notMerge
    />
  );
}
