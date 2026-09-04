import EdgeDeviceCard from '../components/EdgeDeviceCard'
import { mockCameras } from '../mock/cameras'

export default function EdgeDevicesPage() {
  return (
    <div>
      <div className="av-section-title">Thiết bị Edge</div>
      <EdgeDeviceCard />

      <div className="av-section-title">Cấu hình camera trên Edge Service</div>
      <section className="av-panel">
        <div className="av-panel-header">
          <span className="av-panel-title">Cấu hình thực tế theo camera</span>
        </div>
        <div className="av-table-wrap">
          <table className="av-table">
            <thead>
              <tr>
                <th>Camera</th>
                <th>Trạng thái</th>
                <th>Độ phân giải</th>
                <th>Giao thức</th>
                <th>Mô hình</th>
                <th>FPS</th>
                <th>Vùng ROI</th>
                <th>Heartbeat cuối</th>
              </tr>
            </thead>
            <tbody>
              {mockCameras.map((cam) => (
                <tr key={cam.id}>
                  <td>{cam.id} · {cam.name}</td>
                  <td>
                    {cam.online ? (
                      <span className="av-status-pill reviewed">Hoạt động</span>
                    ) : (
                      <span className="av-status-pill escalated">Mất kết nối</span>
                    )}
                  </td>
                  <td className="av-mono">{cam.runtime.resolution}</td>
                  <td className="av-mono">{cam.runtime.protocol}</td>
                  <td>{cam.runtime.model}</td>
                  <td className="av-mono">{cam.online ? cam.runtime.fps : '—'}</td>
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
