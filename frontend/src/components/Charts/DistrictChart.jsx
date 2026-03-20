import ReactECharts from "echarts-for-react";
import { useMemo } from "react";

function getSpeedColor(speed) {
  const s = Number(speed) || 0;
  if (s >= 60) return "#4caf50";
  if (s >= 30) return "#ff9800";
  return "#f44336";
}

export default function DistrictChart({
  districtData = [],
}) {
  const option = useMemo(() => {
    const districts = districtData.map((d) => d.district || "—");
    const counts = districtData.map((d) => d.detector_count ?? 0);
    const colors = districtData.map((d) => getSpeedColor(d.avg_speed));

    return {
      tooltip: {
        trigger: "axis",
        formatter: (params) => {
          const idx = params[0]?.dataIndex;
          if (idx == null) return "";
          const d = districtData[idx];
          return [
            `<strong>${d?.district || "—"}</strong>`,
            `Detectors: ${d?.detector_count ?? 0}`,
            `Avg Speed: ${(d?.avg_speed ?? 0).toFixed(1)} km/h`,
            `Valid Rate: ${(d?.valid_rate ?? 0).toFixed(1)}%`,
          ].join("<br/>");
        },
      },
      grid: {
        left: "15%",
        right: "10%",
        bottom: "3%",
        top: "5%",
        containLabel: true,
      },
      xAxis: {
        type: "value",
        name: "Detector Count",
      },
      yAxis: {
        type: "category",
        data: districts,
        inverse: true,
      },
      series: [
        {
          type: "bar",
          data: counts.map((v, i) => ({
            value: v,
            itemStyle: { color: colors[i] },
          })),
        },
      ],
    };
  }, [districtData]);

  return (
    <ReactECharts option={option} style={{ height: 500 }} notMerge />
  );
}
