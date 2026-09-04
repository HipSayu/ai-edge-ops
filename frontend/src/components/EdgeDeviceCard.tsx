import { edgeDevice } from '../mock/incidents'

export default function EdgeDeviceCard({ compact }: { compact?: boolean }) {
  const memPct = Math.round((edgeDevice.gpuMemUsedGb / edgeDevice.gpuMemTotalGb) * 100)

  return (
    <section className="av-panel">
      <div className="av-panel-header">
        <span className="av-panel-title">Thiết bị Edge</span>
        <span className="av-live-badge good-badge">
          <span className="av-dot good pulse" /> HOẠT ĐỘNG
        </span>
      </div>
      <div className="av-panel-body">
        <div className="av-device-name">{edgeDevice.name}</div>
        <div className={`av-telemetry-grid${compact ? ' compact' : ''}`}>
          <TelemetryTile label="Mức sử dụng GPU" value={`${edgeDevice.gpuUtilization}%`} bar={edgeDevice.gpuUtilization} />
          <TelemetryTile
            label="Bộ nhớ GPU"
            value={`${edgeDevice.gpuMemUsedGb} / ${edgeDevice.gpuMemTotalGb} GB`}
            bar={memPct}
          />
          <TelemetryTile label="Nhiệt độ" value={`${edgeDevice.temperatureC}°C`} bar={edgeDevice.temperatureC} max={100} warn={edgeDevice.temperatureC > 75} />
          <TelemetryTile label="FPS suy luận" value={String(edgeDevice.inferenceFps)} />
          <TelemetryTile label="Độ trễ suy luận" value={`${edgeDevice.inferenceLatencyMs}ms`} />
          <TelemetryTile label="Chế độ nguồn" value={edgeDevice.powerMode} />
          <TelemetryTile label="Mô hình" value={edgeDevice.model} />
          <TelemetryTile label="Runtime" value={edgeDevice.runtime} />
        </div>
      </div>
    </section>
  )
}

function TelemetryTile({
  label,
  value,
  bar,
  max = 100,
  warn,
}: {
  label: string
  value: string
  bar?: number
  max?: number
  warn?: boolean
}) {
  return (
    <div className="av-telemetry-tile">
      <span className="av-telemetry-label">{label}</span>
      <span className="av-telemetry-value av-mono">{value}</span>
      {bar !== undefined && (
        <div className="av-telemetry-bar-track">
          <div
            className={`av-telemetry-bar-fill${warn ? ' warn' : ''}`}
            style={{ width: `${Math.min((bar / max) * 100, 100)}%` }}
          />
        </div>
      )}
    </div>
  )
}
