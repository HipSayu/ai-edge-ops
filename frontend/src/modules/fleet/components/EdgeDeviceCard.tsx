import { Cpu, CheckCircle2 } from 'lucide-react'
import { edgeDevice } from '@/mock\incidents'

export default function EdgeDeviceCard({ compact }: { compact?: boolean }) {
  const memPct = Math.round((edgeDevice.gpuMemUsedGb / edgeDevice.gpuMemTotalGb) * 100)

  return (
    <section className="av-panel">
      <div className="av-panel-header">
        <span className="av-panel-title">
          <Cpu size={15} />
          <span>Edge Computing Hardware</span>
        </span>
        <span className="av-live-badge good-badge">
          <CheckCircle2 size={12} />
          <span>ONLINE • OPTIMAL</span>
        </span>
      </div>
      <div className="av-panel-body">
        <div className="av-device-name">
          <span>{edgeDevice.name}</span>
        </div>
        <div className={`av-telemetry-grid${compact ? ' compact' : ''}`}>
          <TelemetryTile
            label="GPU Utilization"
            value={`${edgeDevice.gpuUtilization}%`}
            bar={edgeDevice.gpuUtilization}
          />
          <TelemetryTile
            label="GPU Memory"
            value={`${edgeDevice.gpuMemUsedGb} / ${edgeDevice.gpuMemTotalGb} GB`}
            bar={memPct}
          />
          <TelemetryTile
            label="Core Temperature"
            value={`${edgeDevice.temperatureC}°C`}
            bar={edgeDevice.temperatureC}
            max={100}
            warn={edgeDevice.temperatureC > 75}
          />
          <TelemetryTile
            label="Inference FPS"
            value={`${edgeDevice.inferenceFps} FPS`}
          />
          <TelemetryTile
            label="Inference Latency"
            value={`${edgeDevice.inferenceLatencyMs}ms`}
          />
          <TelemetryTile
            label="Power Profile"
            value={edgeDevice.powerMode}
          />
          <TelemetryTile
            label="Model Pipeline"
            value={edgeDevice.model}
          />
          <TelemetryTile
            label="Engine Runtime"
            value={edgeDevice.runtime}
          />
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
