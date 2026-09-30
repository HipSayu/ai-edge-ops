import { Cpu, CheckCircle2 } from 'lucide-react'
import { useEffect, useState } from 'react'
import type { EdgeDevice } from '@/modules/agent/types'
import { agentService } from '@/modules/agent/services/agent'

export default function EdgeDeviceCard({ compact }: { compact?: boolean }) {
  const [edgeDevice, setEdgeDevice] = useState<EdgeDevice | null>(null)
  useEffect(() => { agentService.listDevices().then((items) => setEdgeDevice(items[0] ?? null)) }, [])
  if (!edgeDevice) return <div className="av-panel">No edge device data.</div>
  const memPct = edgeDevice.ramTotalGb ? Math.round((edgeDevice.ramUsedGb / edgeDevice.ramTotalGb) * 100) : 0

  return (
    <section className="av-panel">
      <div className="av-panel-header">
        <span className="av-panel-title">
          <Cpu size={15} />
          <span>Edge Computing Hardware</span>
        </span>
        <span className={`av-live-badge ${edgeDevice.status === 'online' ? 'good-badge' : ''}`}>
          <CheckCircle2 size={12} />
          <span>{edgeDevice.status}</span>
        </span>
      </div>
      <div className="av-panel-body">
        <div className="av-device-name">
          <span>{edgeDevice.name}</span>
        </div>
        <div className={`av-telemetry-grid${compact ? ' compact' : ''}`}>
          <TelemetryTile
            label="GPU Utilization"
            value={`${edgeDevice.gpuUsage}%`}
            bar={edgeDevice.gpuUsage}
          />
          <TelemetryTile
            label="GPU Memory"
            value={`${edgeDevice.ramUsedGb} / ${edgeDevice.ramTotalGb} GB`}
            bar={memPct}
          />
          <TelemetryTile
            label="Core Temperature"
            value={`${edgeDevice.tempC}°C`}
            bar={edgeDevice.tempC}
            max={100}
            warn={edgeDevice.tempC > 75}
          />
          <TelemetryTile
            label="Inference FPS"
            value="Unavailable"
          />
          <TelemetryTile
            label="Inference Latency"
            value="Unavailable"
          />
          <TelemetryTile
            label="Power Profile"
            value="Unavailable"
          />
          <TelemetryTile
            label="Model Pipeline"
            value={edgeDevice.modelRunning}
          />
          <TelemetryTile
            label="Engine Runtime"
            value={edgeDevice.agentVersion}
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
