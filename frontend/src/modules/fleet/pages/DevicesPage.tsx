import { useState } from 'react'
import {
  Server,
  Search,
  RotateCw,
  Power,
  Sliders,
  CheckCircle2,
  AlertTriangle,
  WifiOff,
  Activity,
  Plus,
  X} from 'lucide-react'
import KpiCard from '@/components\KpiCard'
import { mockDevices, type EdgeDevice } from '@/mock\fleet'

export default function DevicesPage() {
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState('all')
  const [deviceList, setDeviceList] = useState<EdgeDevice[]>(mockDevices)
  const [actionNotice, setActionNotice] = useState<string | null>(null)

  // Add Device Modal state
  const [showAddModal, setShowAddModal] = useState(false)
  const [newDevice, setNewDevice] = useState({
    id: '',
    name: '',
    ip: '',
    hardware: 'Jetson Orin Nano'
  })

  const filtered = deviceList.filter((dev) => {
    const matchSearch =
      search === '' ||
      dev.name.toLowerCase().includes(search.toLowerCase()) ||
      dev.hardware.toLowerCase().includes(search.toLowerCase()) ||
      dev.ip.includes(search) ||
      dev.id.toLowerCase().includes(search.toLowerCase())

    const matchStatus = statusFilter === 'all' || dev.status === statusFilter
    return matchSearch && matchStatus
  })

  function handleReboot(devId: string) {
    setActionNotice(`Reboot command dispatched to node ${devId}`)
    setTimeout(() => setActionNotice(null), 3000)
  }

  function handleRestartAgent(devId: string) {
    setActionNotice(`Edge Agent daemon restarting on ${devId}...`)
    setTimeout(() => setActionNotice(null), 3000)
  }

  function handleAddDevice(e: React.FormEvent) {
    e.preventDefault()
    const devId = newDevice.id.trim() || `EDG-${Math.floor(Math.random() * 9000) + 1000}`
    
    const addedDev: EdgeDevice = {
      id: devId,
      name: newDevice.name.trim() || 'Unnamed Device',
      ip: newDevice.ip.trim() || '192.168.x.x',
      hardware: newDevice.hardware,
      status: 'online',
      gpuUsage: 0,
      cpuUsage: 0,
      ramUsedGb: 0,
      ramTotalGb: 8,
      tempC: 35,
      assignedCameras: 0,
      modelRunning: 'Awaiting deployment',
      agentVersion: 'v2.4.1',
      uptime: '0m',
      lastHeartbeat: 'Just now'
    }

    setDeviceList([addedDev, ...deviceList])
    setShowAddModal(false)
    setNewDevice({ id: '', name: '', ip: '', hardware: 'Jetson Orin Nano' })
    
    setActionNotice(`Successfully added device ${addedDev.name} (${devId})`)
    setTimeout(() => setActionNotice(null), 3000)
  }

  const onlineCount = deviceList.filter((d) => d.status === 'online').length
  const avgGpu = deviceList.length > 0 ? Math.round(deviceList.reduce((acc, d) => acc + d.gpuUsage, 0) / deviceList.length) : 0

  return (
    <div>
      {actionNotice && (
        <div
          style={{
            padding: '10px 16px',
            borderRadius: 'var(--radius-md)',
            background: 'var(--accent-dim)',
            border: '1px solid var(--accent)',
            color: 'var(--accent)',
            fontSize: 13,
            fontWeight: 600,
            display: 'flex',
            alignItems: 'center',
            gap: 8,
            marginBottom: 16,
            animation: 'av-fade-in 0.2s ease'}}
        >
          <CheckCircle2 size={15} />
          <span>{actionNotice}</span>
        </div>
      )}

      {/* Metrics Row */}
      <div className="av-kpi-row">
        <KpiCard
          label="Total Nodes"
          value={String(deviceList.length)}
          sub="Deployed"
          icon={<Server size={22} />}
          iconBg="rgba(59, 130, 246, 0.12)"
          iconColor="#2563eb"
          deltaText={`${onlineCount} online`}
          isUp={true}
          chartType="sparkline"
          chartColor="#2563eb"
        />
        <KpiCard
          label="Fleet GPU Load"
          value={`${avgGpu}%`}
          sub="Average"
          icon={<Activity size={22} />}
          iconBg="rgba(14, 165, 233, 0.12)"
          iconColor="#0ea5e9"
          deltaText="Normal capacity"
          isUp={true}
          chartType="bars"
          chartColor="#0ea5e9"
        />
        <KpiCard
          label="Edge Agent Sync"
          value="v2.4.1"
          sub="Latest"
          icon={<CheckCircle2 size={22} />}
          iconBg="rgba(16, 185, 129, 0.12)"
          iconColor="#10b981"
          deltaText={`${deviceList.length} up-to-date`}
          isUp={true}
          chartType="sparkline"
          chartColor="#10b981"
        />
        <KpiCard
          label="Thermal Health"
          value="63°C"
          sub="Mean temp"
          icon={<Sliders size={22} />}
          iconBg="rgba(245, 158, 11, 0.14)"
          iconColor="#d97706"
          deltaText="< 75°C threshold"
          isUp={true}
          chartType="bars"
          chartColor="#f59e0b"
        />
      </div>

      {/* Filter and Search */}
      <section className="av-panel">
        <div className="av-filter-row" style={{ display: 'flex', justifyContent: 'space-between', flexWrap: 'wrap', gap: 12 }}>
          <div style={{ display: 'flex', gap: 12, flex: 1, minWidth: 300 }}>
            <div className="av-search-box" style={{ flex: 1 }}>
              <Search size={14} color="var(--text-faint)" />
              <input
                type="text"
                placeholder="Search by device name, hardware, IP, or ID..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
              />
            </div>

            <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}>
              <option value="all">All Statuses</option>
              <option value="online">Online</option>
              <option value="degraded">Degraded</option>
              <option value="offline">Offline</option>
            </select>
          </div>
          
          <button className="av-btn-primary" onClick={() => setShowAddModal(true)}>
            <Plus size={16} />
            <span>Add Device</span>
          </button>
        </div>

        {/* Device Cards Grid */}
        <div style={{ padding: 18, display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(360px, 1fr))', gap: 16 }}>
          {filtered.map((dev) => (
            <div
              key={dev.id}
              style={{
                background: 'var(--panel-2)',
                border: '1px solid var(--border)',
                borderRadius: 'var(--radius-md)',
                padding: 18,
                display: 'flex',
                flexDirection: 'column',
                gap: 14,
                position: 'relative'}}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <span className="av-mono" style={{ fontSize: 12, fontWeight: 700, color: 'var(--accent)' }}>
                      {dev.id}
                    </span>
                    <span style={{ fontSize: 14, fontWeight: 800 }}>{dev.name}</span>
                  </div>
                  <div style={{ fontSize: 11.5, color: 'var(--text-faint)', marginTop: 2 }}>
                    {dev.hardware}
                  </div>
                </div>

                <span
                  className={`av-status-pill ${
                    dev.status === 'online' ? 'reviewed' : dev.status === 'degraded' ? 'new' : 'escalated'
                  }`}
                >
                  {dev.status === 'online' ? <CheckCircle2 size={12} /> : dev.status === 'degraded' ? <AlertTriangle size={12} /> : <WifiOff size={12} />}
                  <span style={{ textTransform: 'capitalize' }}>{dev.status}</span>
                </span>
              </div>

              {/* Hardware Gauges */}
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 11, marginBottom: 3, fontWeight: 600 }}>
                    <span style={{ color: 'var(--text-dim)' }}>GPU Load</span>
                    <span className="av-mono">{dev.gpuUsage}%</span>
                  </div>
                  <div className="av-telemetry-bar-track">
                    <div
                      className={`av-telemetry-bar-fill${dev.gpuUsage > 85 ? ' warn' : ''}`}
                      style={{ width: `${dev.gpuUsage}%` }}
                    />
                  </div>
                </div>

                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 11, marginBottom: 3, fontWeight: 600 }}>
                    <span style={{ color: 'var(--text-dim)' }}>CPU Load</span>
                    <span className="av-mono">{dev.cpuUsage}%</span>
                  </div>
                  <div className="av-telemetry-bar-track">
                    <div
                      className={`av-telemetry-bar-fill${dev.cpuUsage > 80 ? ' warn' : ''}`}
                      style={{ width: `${dev.cpuUsage}%` }}
                    />
                  </div>
                </div>

                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 11, marginBottom: 3, fontWeight: 600 }}>
                    <span style={{ color: 'var(--text-dim)' }}>RAM</span>
                    <span className="av-mono">{dev.ramUsedGb} / {dev.ramTotalGb}GB</span>
                  </div>
                  <div className="av-telemetry-bar-track">
                    <div
                      className="av-telemetry-bar-fill"
                      style={{ width: `${(dev.ramUsedGb / Math.max(dev.ramTotalGb, 1)) * 100}%` }}
                    />
                  </div>
                </div>

                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 11, marginBottom: 3, fontWeight: 600 }}>
                    <span style={{ color: 'var(--text-dim)' }}>Thermal</span>
                    <span className="av-mono">{dev.tempC}°C</span>
                  </div>
                  <div className="av-telemetry-bar-track">
                    <div
                      className={`av-telemetry-bar-fill${dev.tempC > 75 ? ' crit' : dev.tempC > 65 ? ' warn' : ''}`}
                      style={{ width: `${Math.min((dev.tempC / 100) * 100, 100)}%` }}
                    />
                  </div>
                </div>
              </div>

              {/* Specs and Details */}
              <div style={{ fontSize: 11.5, color: 'var(--text-dim)', display: 'flex', flexDirection: 'column', gap: 4, background: 'var(--panel)', padding: '10px 12px', borderRadius: 6, border: '1px solid var(--border)' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span>IP Address:</span>
                  <span className="av-mono" style={{ fontWeight: 600, color: 'var(--text)' }}>{dev.ip}</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span>Running Model:</span>
                  <span style={{ fontWeight: 600, color: 'var(--text)' }}>{dev.modelRunning}</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span>Agent Version:</span>
                  <span className="av-mono" style={{ fontWeight: 600, color: 'var(--text)' }}>{dev.agentVersion}</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span>Uptime:</span>
                  <span className="av-mono" style={{ fontWeight: 600, color: 'var(--text)' }}>{dev.uptime}</span>
                </div>
              </div>

              {/* Action Buttons */}
              <div style={{ display: 'flex', gap: 8, marginTop: 'auto' }}>
                <button
                  className="av-btn-secondary"
                  style={{ flex: 1, padding: '6px 10px', fontSize: 12 }}
                  onClick={() => handleRestartAgent(dev.id)}
                >
                  <RotateCw size={13} />
                  <span>Restart Agent</span>
                </button>
                <button
                  className="av-btn-secondary danger"
                  style={{ padding: '6px 10px', fontSize: 12 }}
                  onClick={() => handleReboot(dev.id)}
                  title="Reboot hardware"
                >
                  <Power size={13} />
                  <span>Reboot</span>
                </button>
              </div>
            </div>
          ))}

          {filtered.length === 0 && (
            <div style={{ gridColumn: '1 / -1', textAlign: 'center', padding: 36, color: 'var(--text-faint)' }}>
              No edge devices match the selected filters.
            </div>
          )}
        </div>
      </section>

      {/* Add Device Modal */}
      {showAddModal && (
        <div className="av-modal-backdrop" onClick={() => setShowAddModal(false)}>
          <div className="av-incident-modal" onClick={(e) => e.stopPropagation()} style={{ maxWidth: 450 }}>
            <div style={{ padding: '16px 20px', borderBottom: '1px solid var(--border)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <h3 style={{ margin: 0, fontSize: 16 }}>Provision New Edge Device</h3>
              <button className="av-icon-btn" onClick={() => setShowAddModal(false)}><X size={18}/></button>
            </div>
            <form onSubmit={handleAddDevice} style={{ padding: 20 }}>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
                <div>
                  <label style={{ display: 'block', marginBottom: 6, fontSize: 13, fontWeight: 600 }}>Device ID (Optional)</label>
                  <input
                    type="text"
                    placeholder="e.g. EDG-9021"
                    value={newDevice.id}
                    onChange={(e) => setNewDevice({...newDevice, id: e.target.value})}
                    style={{ width: '100%', padding: '8px 12px', background: 'var(--bg)', border: '1px solid var(--border)', borderRadius: 6, color: 'var(--text-main)' }}
                  />
                </div>
                <div>
                  <label style={{ display: 'block', marginBottom: 6, fontSize: 13, fontWeight: 600 }}>Device Name</label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. Factory Floor Node A"
                    value={newDevice.name}
                    onChange={(e) => setNewDevice({...newDevice, name: e.target.value})}
                    style={{ width: '100%', padding: '8px 12px', background: 'var(--bg)', border: '1px solid var(--border)', borderRadius: 6, color: 'var(--text-main)' }}
                  />
                </div>
                <div>
                  <label style={{ display: 'block', marginBottom: 6, fontSize: 13, fontWeight: 600 }}>IP Address</label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. 192.168.1.50"
                    value={newDevice.ip}
                    onChange={(e) => setNewDevice({...newDevice, ip: e.target.value})}
                    style={{ width: '100%', padding: '8px 12px', background: 'var(--bg)', border: '1px solid var(--border)', borderRadius: 6, color: 'var(--text-main)' }}
                  />
                </div>
                <div>
                  <label style={{ display: 'block', marginBottom: 6, fontSize: 13, fontWeight: 600 }}>Hardware Platform</label>
                  <select
                    value={newDevice.hardware}
                    onChange={(e) => setNewDevice({...newDevice, hardware: e.target.value})}
                    style={{ width: '100%', padding: '8px 12px', background: 'var(--bg)', border: '1px solid var(--border)', borderRadius: 6, color: 'var(--text-main)' }}
                  >
                    <option value="Jetson Orin Nano">NVIDIA Jetson Orin Nano</option>
                    <option value="Jetson AGX Orin">NVIDIA Jetson AGX Orin</option>
                    <option value="Intel NUC (OpenVINO)">Intel NUC (OpenVINO)</option>
                    <option value="Raspberry Pi 5 + Hailo">Raspberry Pi 5 + Hailo</option>
                  </select>
                </div>
              </div>
              <div style={{ marginTop: 24, display: 'flex', justifyContent: 'flex-end', gap: 12 }}>
                <button type="button" className="av-btn-secondary" onClick={() => setShowAddModal(false)}>Cancel</button>
                <button type="submit" className="av-btn-primary">Provision Device</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}

