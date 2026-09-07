import { useEffect, useState } from 'react'
import { Camera, Search, Download, Maximize2, RotateCcw } from 'lucide-react'
import { agentService } from '@/shared/api/services/agent'

type Snapshot = { id: number; camera_id: number | null; image_path: string; captured_at: string; labels: string[] }

export default function SnapshotsPage() {
  const [search, setSearch] = useState('')
  const [classFilter, setClassFilter] = useState('all')
  const [cameraFilter, setCameraFilter] = useState('all')
  const [fromDate, setFromDate] = useState('')
  const [toDate, setToDate] = useState('')
  const [snapshots, setSnapshots] = useState<Snapshot[]>([])

  useEffect(() => { agentService.listSnapshots().then(setSnapshots as never).catch(() => setSnapshots([])) }, [])
  const imageClasses = [...new Set(snapshots.flatMap((img) => img.labels))]
  const imageCameras = [...new Set(snapshots.map((img) => String(img.camera_id ?? 'unknown')))]

  const filtered = snapshots.filter(img => {
    const date = img.captured_at.slice(0, 10)
    const label = img.labels[0] ?? 'Unclassified'
    const camera = String(img.camera_id ?? 'unknown')
    const matchSearch = search === '' || label.toLowerCase().includes(search.toLowerCase()) || camera.includes(search.toLowerCase())
    const matchClass = classFilter === 'all' || img.labels.includes(classFilter)
    const matchCamera = cameraFilter === 'all' || camera === cameraFilter
    const matchFromDate = fromDate === '' || date >= fromDate
    const matchToDate = toDate === '' || date <= toDate
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
              {imageClasses.map(label => <option key={label} value={label}>{label}</option>)}
            </select>
            <select value={cameraFilter} onChange={e => setCameraFilter(e.target.value)} aria-label="Filter by camera">
              <option value="all">All Cameras</option>
              {imageCameras.map(camera => <option key={camera} value={camera}>{camera}</option>)}
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
        {filtered.map(img => {
          const label = img.labels[0] ?? 'Unclassified'
          const camera = String(img.camera_id ?? 'unknown')
          return (
          <div key={img.id} className="av-panel" style={{ overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
            <div style={{ position: 'relative', aspectRatio: '16/9', background: '#000' }}>
              <img src={img.image_path} alt={label} style={{ width: '100%', height: '100%', objectFit: 'cover', opacity: 0.85 }} />
              <div style={{ position: 'absolute', top: 8, right: 8, display: 'flex', gap: 6 }}>
                <button className="av-icon-btn" style={{ background: 'rgba(0,0,0,0.6)', border: '1px solid rgba(255,255,255,0.2)', color: '#fff' }}><Maximize2 size={14} /></button>
                <button className="av-icon-btn" style={{ background: 'rgba(0,0,0,0.6)', border: '1px solid rgba(255,255,255,0.2)', color: '#fff' }}><Download size={14} /></button>
              </div>
              <div style={{ position: 'absolute', bottom: 8, left: 8 }}>
                <span className="av-status-pill reviewed" style={{ background: 'rgba(16, 185, 129, 0.9)', color: '#fff', border: 'none' }}>{label}</span>
              </div>
            </div>
            <div style={{ padding: '12px 16px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <Camera size={14} color="var(--text-faint)" />
                <span style={{ fontSize: 13, fontWeight: 700 }}>{camera}</span>
              </div>
              <span className="av-mono" style={{ fontSize: 11, color: 'var(--text-faint)' }}>{img.captured_at}</span>
            </div>
          </div>
          )
        })}
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
