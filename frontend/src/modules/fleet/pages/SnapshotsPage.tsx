import { useState } from 'react'
import { Camera, Search, Download, Maximize2, RotateCcw } from 'lucide-react'

const MOCK_IMAGES = [
  { id: 'IMG-1', cam: 'CAM-A1', date: '2026-09-04', url: 'https://images.unsplash.com/photo-1581091226825-a6a2a5aee158?w=600&q=80', time: '10:42:15', label: 'Person / Worker', conf: '92%' },
  { id: 'IMG-2', cam: 'CAM-B3', date: '2026-09-04', url: 'https://images.unsplash.com/photo-1504917595217-d4dc5ebe6122?w=600&q=80', time: '10:41:05', label: 'Safety Vest', conf: '98%' },
  { id: 'IMG-3', cam: 'CAM-A2', date: '2026-09-03', url: 'https://images.unsplash.com/photo-1616423640778-28d1b53229bd?w=600&q=80', time: '10:39:22', label: 'Forklift', conf: '87%' },
  { id: 'IMG-4', cam: 'CAM-A1', date: '2026-09-03', url: 'https://images.unsplash.com/photo-1540553016722-983e48a2cd10?w=600&q=80', time: '10:38:10', label: 'Hard Hat', conf: '95%' },
  { id: 'IMG-5', cam: 'CAM-C1', date: '2026-09-02', url: 'https://images.unsplash.com/photo-1611162617474-5b21e879e113?w=600&q=80', time: '10:35:45', label: 'Zone Intrusion', conf: '89%' },
  { id: 'IMG-6', cam: 'CAM-B2', date: '2026-09-02', url: 'https://images.unsplash.com/photo-1581092160607-ee22621dd758?w=600&q=80', time: '10:31:20', label: 'Person / Worker', conf: '91%' },
  { id: 'IMG-7', cam: 'CAM-A2', date: '2026-09-01', url: 'https://images.unsplash.com/photo-1504328345606-18bbc8c9d7d1?w=600&q=80', time: '10:28:15', label: 'Forklift', conf: '94%' },
  { id: 'IMG-8', cam: 'CAM-C2', date: '2026-09-01', url: 'https://images.unsplash.com/photo-1581092580497-e0d23cbdf1dc?w=600&q=80', time: '10:25:50', label: 'Safety Vest', conf: '96%' },
]

const IMAGE_CLASSES = [...new Set(MOCK_IMAGES.map((img) => img.label))]
const IMAGE_CAMERAS = [...new Set(MOCK_IMAGES.map((img) => img.cam))]

export default function SnapshotsPage() {
  const [search, setSearch] = useState('')
  const [classFilter, setClassFilter] = useState('all')
  const [cameraFilter, setCameraFilter] = useState('all')
  const [fromDate, setFromDate] = useState('')
  const [toDate, setToDate] = useState('')

  const filtered = MOCK_IMAGES.filter(img => {
    const matchSearch = search === '' || img.label.toLowerCase().includes(search.toLowerCase()) || img.cam.toLowerCase().includes(search.toLowerCase())
    const matchClass = classFilter === 'all' || img.label === classFilter
    const matchCamera = cameraFilter === 'all' || img.cam === cameraFilter
    const matchFromDate = fromDate === '' || img.date >= fromDate
    const matchToDate = toDate === '' || img.date <= toDate
    return matchSearch && matchClass && matchCamera && matchFromDate && matchToDate
  })

  function resetFilters() {
    setSearch('')
    setClassFilter('all')
    setCameraFilter('all')
    setFromDate('')
    setToDate('')
  }

  return (
    <div className="av-page-layout">
      <section className="av-page-header av-panel" style={{ marginBottom: 0 }}>
        <div className="av-filter-row" style={{ display: 'flex', justifyContent: 'space-between', flexWrap: 'wrap', gap: 12 }}>
          <div style={{ display: 'flex', gap: 12, flex: 1, minWidth: 300, flexWrap: 'wrap' }}>
            <div className="av-search-box" style={{ flex: 1 }}>
              <Search size={14} color="var(--text-faint)" />
              <input type="text" placeholder="Search by class or camera ID..." value={search} onChange={e => setSearch(e.target.value)} />
            </div>
            <select value={classFilter} onChange={e => setClassFilter(e.target.value)} aria-label="Filter by class">
              <option value="all">All Classes</option>
              {IMAGE_CLASSES.map(label => <option key={label} value={label}>{label}</option>)}
            </select>
            <select value={cameraFilter} onChange={e => setCameraFilter(e.target.value)} aria-label="Filter by camera">
              <option value="all">All Cameras</option>
              {IMAGE_CAMERAS.map(camera => <option key={camera} value={camera}>{camera}</option>)}
            </select>
            <label style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 12, color: 'var(--text-dim)' }}>
              From
              <input type="date" value={fromDate} onChange={e => setFromDate(e.target.value)} aria-label="From date" />
            </label>
            <label style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 12, color: 'var(--text-dim)' }}>
              To
              <input type="date" value={toDate} onChange={e => setToDate(e.target.value)} aria-label="To date" />
            </label>
          </div>
          <button className="av-btn-secondary" onClick={resetFilters} type="button">
            <RotateCcw size={15} />
            <span>Reset</span>
          </button>
        </div>
      </section>

      <div className="av-page-content">
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: 16 }}>
        {filtered.map(img => (
          <div key={img.id} className="av-panel" style={{ overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
            <div style={{ position: 'relative', aspectRatio: '16/9', background: '#000' }}>
              <img src={img.url} alt={img.label} style={{ width: '100%', height: '100%', objectFit: 'cover', opacity: 0.85 }} />
              <div style={{ position: 'absolute', top: 8, right: 8, display: 'flex', gap: 6 }}>
                <button className="av-icon-btn" style={{ background: 'rgba(0,0,0,0.6)', border: '1px solid rgba(255,255,255,0.2)', color: '#fff' }}><Maximize2 size={14} /></button>
                <button className="av-icon-btn" style={{ background: 'rgba(0,0,0,0.6)', border: '1px solid rgba(255,255,255,0.2)', color: '#fff' }}><Download size={14} /></button>
              </div>
              <div style={{ position: 'absolute', bottom: 8, left: 8 }}>
                <span className="av-status-pill reviewed" style={{ background: 'rgba(16, 185, 129, 0.9)', color: '#fff', border: 'none' }}>{img.label} ({img.conf})</span>
              </div>
            </div>
            <div style={{ padding: '12px 16px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <Camera size={14} color="var(--text-faint)" />
                <span style={{ fontSize: 13, fontWeight: 700 }}>{img.cam}</span>
              </div>
              <span className="av-mono" style={{ fontSize: 11, color: 'var(--text-faint)' }}>{img.date} {img.time}</span>
            </div>
          </div>
        ))}
          {filtered.length === 0 && (
          <div className="av-panel" style={{ gridColumn: '1 / -1', padding: 36, textAlign: 'center', color: 'var(--text-faint)' }}>
            No snapshots match the selected filters.
          </div>
          )}
        </div>
      </div>
    </div>
  )
}
