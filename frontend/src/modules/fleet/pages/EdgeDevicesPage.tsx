import { Server, CheckCircle2, WifiOff } from 'lucide-react'
import EdgeDeviceCard from '@/modules/fleet/components/EdgeDeviceCard'
import { mockCameras } from '@/modules/fleet/mock/cameras'

export default function EdgeDevicesPage() {
  return (
    <div>
      
      <EdgeDeviceCard />

      
      <section className="av-panel">
        <div className="av-panel-header">
          <span className="av-panel-title">
            <Server size={15} />
            <span>Active Inference Streams</span>
          </span>
          <span className="av-panel-sub">{mockCameras.length} Channels Allocated</span>
        </div>
        <div className="av-table-wrap">
          <table className="av-table">
            <thead>
              <tr>
                <th>Camera Node</th>
                <th>Inference Status</th>
                <th>Resolution</th>
                <th>Protocol</th>
                <th>Model Architecture</th>
                <th>Throughput</th>
                <th>ROI Zones</th>
                <th>Heartbeat Sync</th>
              </tr>
            </thead>
            <tbody>
              {mockCameras.map((cam) => (
                <tr key={cam.id}>
                  <td>
                    <strong>{cam.id}</strong> · {cam.name}
                  </td>
                  <td>
                    {cam.online ? (
                      <span className="av-status-pill reviewed">
                        <CheckCircle2 size={12} />
                        <span>Operational</span>
                      </span>
                    ) : (
                      <span className="av-status-pill escalated">
                        <WifiOff size={12} />
                        <span>Disconnected</span>
                      </span>
                    )}
                  </td>
                  <td className="av-mono">{cam.runtime.resolution}</td>
                  <td className="av-mono">{cam.runtime.protocol}</td>
                  <td>{cam.runtime.model}</td>
                  <td className="av-mono">{cam.online ? `${cam.runtime.fps} FPS` : '—'}</td>
                  <td className="av-mono">{cam.runtime.roiZones}</td>
                  <td className="av-mono">{cam.runtime.lastHeartbeat}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  )
}
