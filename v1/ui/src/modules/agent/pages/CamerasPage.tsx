import { useEffect, useState } from 'react'
import { Radio, Search, Grid2X2, Grid3X3, LayoutGrid } from 'lucide-react'
import type { Camera } from '@/modules/agent/types'
import { agentService } from '@/shared/api/services/agent'
import LiveMonitorPanel from '@/modules/agent/components/LiveMonitorPanel'
import CameraCard from '@/modules/agent/components/CameraCard'

type ViewMode = 'cards' | 'grid4' | 'grid9'

export default function CamerasPage() {
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState('all')
  const [selectedCamera, setSelectedCamera] = useState<Camera | null>(null)
  const [viewMode, setViewMode] = useState<ViewMode>('cards')
  const [cameras, setCameras] = useState<Camera[]>([])

  useEffect(() => { agentService.listCameras().then(setCameras).catch(() => setCameras([])) }, [])

  const filtered = cameras.filter((cam) => {
    const matchSearch =
      search === '' ||
      cam.name.toLowerCase().includes(search.toLowerCase()) ||
      cam.id.toLowerCase().includes(search.toLowerCase()) ||
      cam.zone.toLowerCase().includes(search.toLowerCase()) ||
      cam.runtime.model.toLowerCase().includes(search.toLowerCase())

    const matchStatus =
      statusFilter === 'all' ||
      (statusFilter === 'online' && cam.online) ||
      (statusFilter === 'offline' && !cam.online)

    return matchSearch && matchStatus
  })

  // Pagination/Slicing for Grid modes
  const displayLimit = viewMode === 'grid4' ? 4 : viewMode === 'grid9' ? 9 : filtered.length
  const displayedCameras = filtered.slice(0, displayLimit)

  return (
    <div className="av-page-layout">
      {/* Camera Filter Bar */}
      <section className="av-page-header av-panel" style={{ marginBottom: 0 }}>
        <div className="av-filter-row" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px' }}>
          <div style={{ display: 'flex', gap: '12px', flex: 1, minWidth: '300px' }}>
            <div className="av-search-box" style={{ flex: 1 }}>
              <Search size={14} color="var(--text-faint)" />
              <input
                type="text"
                placeholder="Search cameras by ID, name, location..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
              />
            </div>
            <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}>
              <option value="all">All Camera Feeds</option>
              <option value="online">Streaming (Online)</option>
              <option value="offline">Signal Lost (Offline)</option>
            </select>
          </div>

          {/* Layout Controls */}
          <div style={{ display: 'flex', gap: '8px', background: 'var(--bg-raised)', padding: '4px', borderRadius: '8px', border: '1px solid var(--border)' }}>
            <button
              className={`av-icon-btn ${viewMode === 'cards' ? 'active' : ''}`}
              onClick={() => setViewMode('cards')}
              title="Card View"
            >
              <LayoutGrid size={18} />
            </button>
            <button
              className={`av-icon-btn ${viewMode === 'grid4' ? 'active' : ''}`}
              onClick={() => setViewMode('grid4')}
              title="2x2 Grid View"
            >
              <Grid2X2 size={18} />
            </button>
            <button
              className={`av-icon-btn ${viewMode === 'grid9' ? 'active' : ''}`}
              onClick={() => setViewMode('grid9')}
              title="3x3 Grid View"
            >
              <Grid3X3 size={18} />
            </button>
          </div>
        </div>
      </section>

      {/* Grid Mode Render */}
      <div className="av-page-content">
      {viewMode !== 'cards' && (
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: viewMode === 'grid4' ? 'repeat(2, 1fr)' : 'repeat(3, 1fr)',
            gap: '16px',
            marginBottom: '24px'
          }}
        >
          {displayedCameras.map((cam) => (
            <div key={cam.id} className="av-panel" style={{ display: 'flex', flexDirection: 'column', height: '100%', overflow: 'hidden' }}>
              <div style={{ padding: '8px 12px', borderBottom: '1px solid var(--border)', display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: 'var(--bg-raised)' }}>
                <span style={{ fontWeight: 600, fontSize: '13px' }}>{cam.id} • {cam.name}</span>
                {cam.online ? (
                  <span style={{ fontSize: '11px', color: 'var(--good)', display: 'flex', alignItems: 'center', gap: '4px' }}>
                    <Radio size={12} className="pulse" /> LIVE
                  </span>
                ) : (
                  <span style={{ fontSize: '11px', color: 'var(--critical)' }}>OFFLINE</span>
                )}
              </div>
              <div style={{ flex: 1, minHeight: viewMode === 'grid4' ? '280px' : '180px', position: 'relative' }}>
                <LiveMonitorPanel camera={cam} />
              </div>
            </div>
          ))}
          {displayedCameras.length === 0 && (
            <div style={{ gridColumn: '1 / -1', padding: '40px', textAlign: 'center', color: 'var(--text-faint)' }}>
              No cameras matched your filter criteria.
            </div>
          )}
        </div>
      )}

      {/* Cards Mode Render */}
      {viewMode === 'cards' && (
        <div className="av-cameras-grid">
          {filtered.map((cam) => (
            <CameraCard key={cam.id} camera={cam} onOpen={setSelectedCamera} />
          ))}
          {filtered.length === 0 && (
            <div style={{ gridColumn: '1 / -1', padding: '40px', textAlign: 'center', color: 'var(--text-faint)' }}>
              No cameras matched your filter criteria.
            </div>
          )}
        </div>
      )}
      </div>

      {/* Camera Live Stream Dialog (only used in Card mode) */}
      {selectedCamera && viewMode === 'cards' && (
        <div className="av-modal-backdrop" onClick={() => setSelectedCamera(null)}>
          <div
            className="av-incident-modal"
            onClick={(e) => e.stopPropagation()}
            style={{ maxWidth: 840 }}
          >
            <div style={{ padding: 18, borderBottom: '1px solid var(--border)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div style={{ fontSize: 16, fontWeight: 800 }}>
                {selectedCamera.id} • {selectedCamera.name} ({selectedCamera.zone})
              </div>
              <button
                className="av-icon-btn"
                onClick={() => setSelectedCamera(null)}
                style={{ width: 30, height: 30 }}
              >
                ✕
              </button>
            </div>
            <div style={{ padding: 18 }}>
              <LiveMonitorPanel camera={selectedCamera} />
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
