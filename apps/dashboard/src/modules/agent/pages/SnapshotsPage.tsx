import { useState } from 'react'
import { Camera, Search, Download, Maximize2, RotateCcw } from 'lucide-react'
import { useEdgeOps } from '@/core/edge-ops/EdgeOpsContext'

const FIELD = 'rounded-lg border border-border bg-background px-3 py-2 text-sm text-foreground outline-none focus:border-brand'
const OVERLAY_BTN = 'flex size-7 cursor-pointer items-center justify-center rounded-md border border-white/20 bg-black/60 text-white hover:bg-black/80'

export default function SnapshotsPage() {
  const [search, setSearch] = useState('')
  const [classFilter, setClassFilter] = useState('all')
  const [cameraFilter, setCameraFilter] = useState('all')
  const [fromDate, setFromDate] = useState('')
  const [toDate, setToDate] = useState('')
  const { snapshots } = useEdgeOps()
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
    <div className="flex flex-col gap-4">
      <section className="rounded-xl border border-border bg-card p-4">
        <div className="flex flex-wrap justify-between gap-3">
          <div className="flex min-w-[300px] flex-1 flex-wrap gap-3">
            <div className="flex flex-1 items-center gap-2 rounded-lg border border-border bg-background px-3">
              <Search size={14} className="text-muted-foreground" />
              <input
                type="text"
                placeholder="Search by class or camera ID..."
                value={search}
                onChange={e => setSearch(e.target.value)}
                className="w-full bg-transparent py-2 text-sm outline-none"
              />
            </div>
            <select value={classFilter} onChange={e => setClassFilter(e.target.value)} aria-label="Filter by class" className={FIELD}>
              <option value="all">All Classes</option>
              {imageClasses.map(label => <option key={label} value={label}>{label}</option>)}
            </select>
            <select value={cameraFilter} onChange={e => setCameraFilter(e.target.value)} aria-label="Filter by camera" className={FIELD}>
              <option value="all">All Cameras</option>
              {imageCameras.map(camera => <option key={camera} value={camera}>{camera}</option>)}
            </select>
            <label className="flex items-center gap-1.5 text-xs text-muted-foreground">
              From
              <input type="date" value={fromDate} onChange={e => setFromDate(e.target.value)} aria-label="From date" className={FIELD} />
            </label>
            <label className="flex items-center gap-1.5 text-xs text-muted-foreground">
              To
              <input type="date" value={toDate} onChange={e => setToDate(e.target.value)} aria-label="To date" className={FIELD} />
            </label>
          </div>
          <button
            onClick={resetFilters}
            type="button"
            className="flex cursor-pointer items-center gap-1.5 rounded-lg border border-border bg-background px-3 py-2 text-sm font-semibold transition-colors hover:bg-muted"
          >
            <RotateCcw size={15} />
            <span>Reset</span>
          </button>
        </div>
      </section>

      <div className="grid grid-cols-[repeat(auto-fill,minmax(280px,1fr))] gap-4">
        {filtered.map(img => {
          const label = img.labels[0] ?? 'Unclassified'
          const camera = String(img.camera_id ?? 'unknown')
          return (
            <div key={img.id} className="flex flex-col overflow-hidden rounded-xl border border-border bg-card">
              <div className="relative aspect-video bg-black">
                <img src={img.image_path} alt={label} className="size-full object-cover opacity-85" />
                <div className="absolute right-2 top-2 flex gap-1.5">
                  <button className={OVERLAY_BTN}><Maximize2 size={14} /></button>
                  <button className={OVERLAY_BTN}><Download size={14} /></button>
                </div>
                <div className="absolute bottom-2 left-2">
                  <span className="rounded-full bg-emerald-500/90 px-2 py-0.5 text-[11px] font-semibold text-white">{label}</span>
                </div>
              </div>
              <div className="flex items-center justify-between px-4 py-3">
                <div className="flex items-center gap-2">
                  <Camera size={14} className="text-muted-foreground" />
                  <span className="text-[13px] font-bold">{camera}</span>
                </div>
                <span className="font-mono text-[11px] text-muted-foreground">{img.captured_at}</span>
              </div>
            </div>
          )
        })}
        {filtered.length === 0 && (
          <div className="col-span-full rounded-xl border border-border bg-card p-9 text-center text-muted-foreground">
            No snapshots match the selected filters.
          </div>
        )}
      </div>
    </div>
  )
}
