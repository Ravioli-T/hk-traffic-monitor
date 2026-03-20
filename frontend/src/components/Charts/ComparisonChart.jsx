import ReactECharts from "echarts-for-react";
import { useMemo } from "react";

const STRATEGIC_COLOR = "#1976d2";
const LAMPPOST_COLOR = "#ff9800";

export default function ComparisonChart({
  strategicData = {},
  lamppostData = {},
}) {
  const option = useMemo(() => {
    const categories = [
      "Detector Count",
      "Valid Rate %",
      "Coverage Districts",
      "Avg Speed km/h",
    ];
    const strategic = [
      strategicData.count ?? 0,
      strategicData.valid_rate ?? 0,
      strategicData.coverage_districts ?? 0,
      strategicData.avg_speed ?? 0,
    ];
    const lamppost = [
      lamppostData.count ?? 0,
      lamppostData.valid_rate ?? 0,
      lamppostData.coverage_districts ?? 0,
      lamppostData.avg_speed ?? 0,
    ];

    return {
      tooltip: {
        trigger: "axis",
        axisPointer: { type: "shadow" },
      },
      legend: {
        data: ["Strategic", "Lamppost"],
        top: 0,
      },
      grid: {
        left: "3%",
        right: "4%",
        bottom: "3%",
        top: "12%",
        containLabel: true,
      },
      xAxis: {
        type: "category",
        data: categories,
        axisLabel: { rotate: 30 },
      },
      yAxis: {
        type: "value",
      },
      series: [
        {
          name: "Strategic",
          type: "bar",
          data: strategic,
          itemStyle: { color: STRATEGIC_COLOR },
        },
        {
          name: "Lamppost",
          type: "bar",
          data: lamppost,
          itemStyle: { color: LAMPPOST_COLOR },
        },
      ],
    };
  }, [strategicData, lamppostData]);

  return (
    <ReactECharts option={option} style={{ height: 400 }} notMerge />
  );
}
