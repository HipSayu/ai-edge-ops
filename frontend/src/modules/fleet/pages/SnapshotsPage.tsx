import { useState } from 'react'
import { Camera, Search, Filter, Download, Maximize2 } from 'lucide-react'
import { mockCameras } from '@/mock\cameras'

const MOCK_IMAGES = [
  { id: 'IMG-1', cam: 'CAM-A1', url: 'https://images.unsplash.com/photo-1581091226825-a6a2a5aee158?w=600&q=80', time: '10:42:15', label: 'Person / Worker', conf: '92%' },
  { id: 'IMG-2', cam: 'CAM-B3', url: 'https://images.unsplash.com/photo-1504917595217-d4dc5ebe6122?w=600&q=80', time: '10:41:05', label: 'Safety Vest', conf: '98%' },
  { id: 'IMG-3', cam: 'CAM-A2', url: 'https://images.unsplash.com/photo-1616423640778-28d1b53229bd?w=600&q=80', time: '10:39:22', label: 'Forklift', conf: '87%' },
  { id: 'IMG-4', cam: 'CAM-A1', url: 'https://images.unsplash.com/photo-1540553016722-983e48a2cd10?w=600&q=80', time: '10:38:10', label: 'Hard Hat', conf: '95%' },
  { id: 'IMG-5', cam: 'CAM-C1', url: 'https://images.unsplash.com/photo-1611162617474-5b21e879e113?w=600&q=80', time: '10:35:45', label: 'Zone Intrusion', conf: '89%' },
  { id: 'IMG-6', cam: 'CAM-B2', url: 'https://images.unsplash.com/photo-1581092160607-ee22621dd758?w=600&q=80', time: '10:31:20', label: 'Person / Worker', conf: '91%' },
  { id: 'IMG-7', cam: 'CAM-A2', url: 'https://images.unsplash.com/photo-1504328345606-18bbc8c9d7d1?w=600&q=80', time: '10:28:15', label: 'Forklift', conf: '94%' },
  { id: 'IMG-8', cam: 'CAM-C2', url: 'https://images.unsplash.com/photo-1581092580497-e0d23cbdf1dc?w=600&q=80', time: '10:25:50', label: 'Safety Vest', conf: '96%' },
]

export default function SnapshotsPage() {
  const [search, setSearch] = useState('')
  const [filter, setFilter] = useState('all')

  const filtered = MOCK_IMAGES.filter(img => {
    const matchSearch = search === '' || img.label.toLowerCase().includes(search.toLowerCase()) || img.cam.toLowerCase().includes(search.toLowerCase())
    const matchFilter = filter === 'all' || img.cam === filter
    return matchSearch && matchFilter
  })

  return (
    <div>
      <section className="av-panel" style={{ marginBottom: 20 }}>
        <div className="av-filter-row" style={{ display: 'flex', justifyContent: 'space-between', flexWrap: 'wrap', gap: 12 }}>
          <div style={{ display: 'flex', gap: 12, flex: 1, minWidth: 300 }}>
            <div className="av-search-box" style={{ flex: 1 }}>
              <Search size={14} color="var(--text-faint)" />
              <input type="text" placeholder="Search by class or camera ID..." value={search} onChange={e => setSearch(e.target.value)} />
            </div>
            <select value={filter} onChange={e => setFilter(e.target.value)}>
              <option value="all">All Cameras</option>
              {mockCameras.map(c => <option key={c.id} value={c.id}>{c.id} - {c.name}</option>)}
            </select>
          </div>
          <button className="av-btn-secondary">
            <Filter size={16} />
            <span>Advanced</span>
          </button>
        </div>
      </section>

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
              <span className="av-mono" style={{ fontSize: 11, color: 'var(--text-faint)' }}>{img.time}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
