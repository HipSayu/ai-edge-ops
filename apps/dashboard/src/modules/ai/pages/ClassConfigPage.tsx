import { useState, useMemo } from 'react'
import {
  Search, Trash2, Eye, EyeOff, Save,
  Check, Tags, ShieldAlert, SlidersHorizontal, AlertTriangle,
} from 'lucide-react'
import Pagination from '@/shared/components/Pagination'
import type { ClassCategory } from '@/modules/ai/types/ai'
import { useEdgeOps } from '@/core/edge-ops/EdgeOpsContext'


const CATEGORY_COLORS: Record<ClassCategory, string> = {
  PPE: 'text-cyan-400 bg-cyan-500/10 border-cyan-500/20',
  Vehicle: 'text-amber-400 bg-amber-500/10 border-amber-500/20',
  Person: 'text-blue-400 bg-blue-500/10 border-blue-500/20',
  Hazard: 'text-red-400 bg-red-500/10 border-red-500/20',
  Object: 'text-purple-400 bg-purple-500/10 border-purple-500/20',
  Custom: 'text-zinc-400 bg-zinc-500/10 border-zinc-500/20',
}


export default function ClassConfigPage() {
  const { classConfig: classes, setClassConfig: setClasses } = useEdgeOps()
  const [search, setSearch] = useState('')
  const [categoryFilter, setCategoryFilter] = useState<string>('all')
  const [actionNotice, setActionNotice] = useState<string | null>(null)

  // Pagination
  const [currentPage, setCurrentPage] = useState(1)
  const [pageSize, setPageSize] = useState(8)

  // Filter logic
  const filtered = useMemo(() => {
    return classes.filter((c) => {
      const matchSearch =
        !search ||
        c.name.toLowerCase().includes(search.toLowerCase()) ||
        c.displayName.toLowerCase().includes(search.toLowerCase())
      const matchCat = categoryFilter === 'all' || c.category === categoryFilter
      return matchSearch && matchCat
    })
  }, [classes, search, categoryFilter])

  // Pagination slice
  const paginatedClasses = useMemo(() => {
    const start = (currentPage - 1) * pageSize
    return filtered.slice(start, start + pageSize)
  }, [filtered, currentPage, pageSize])

  const totalPages = Math.ceil(filtered.length / pageSize)

  const handleToggleEnable = (id: number) => {
    setClasses((prev) =>
      prev.map((c) => (c.id === id ? { ...c, enabled: !c.enabled } : c))
    )
  }

  const handleToggleAlert = (id: number) => {
    setClasses((prev) =>
      prev.map((c) => (c.id === id ? { ...c, alertOnDetection: !c.alertOnDetection } : c))
    )
  }

  const handleConfidenceChange = (id: number, val: number) => {
    setClasses((prev) =>
      prev.map((c) => (c.id === id ? { ...c, minConfidence: val } : c))
    )
  }

  const handleDeleteClass = (id: number) => {
    setClasses((prev) => prev.filter((c) => c.id !== id))
    setActionNotice(`Class ID #${id} removed from detection schema`)
    setTimeout(() => setActionNotice(null), 3000)
  }

  const handleSaveProfile = () => {
    setActionNotice('Detection Class Profile synchronized across all edge nodes.')
    setTimeout(() => setActionNotice(null), 3500)
  }

  return (
    <div className="flex flex-col gap-4">
      {/* Action Notice */}
      {actionNotice && (
        <div className="flex items-center justify-between rounded-lg border border-success/30 bg-success/10 px-4 py-2 text-xs font-medium text-success animate-in fade-in duration-150">
          <span>{actionNotice}</span>
          <button onClick={() => setActionNotice(null)} className="text-success/70 hover:text-success">✕</button>
        </div>
      )}

      {/* ── 1. KPI SUMMARY STRIP (Compact) ── */}
      <div className="grid grid-cols-2 gap-2.5 sm:grid-cols-4">
        <div className="flex items-center gap-2.5 rounded-lg border border-border bg-card p-2.5">
          <div className="flex size-7 shrink-0 items-center justify-center rounded-md bg-brand/10 text-brand">
            <Tags size={14} />
          </div>
          <div className="min-w-0">
            <div className="text-base font-bold leading-tight text-foreground">{classes.length} Classes</div>
            <div className="text-[10px] text-muted-foreground">Configured Schemas</div>
          </div>
        </div>

        <div className="flex items-center gap-2.5 rounded-lg border border-border bg-card p-2.5">
          <div className="flex size-7 shrink-0 items-center justify-center rounded-md bg-success/10 text-success">
            <Check size={14} />
          </div>
          <div className="min-w-0">
            <div className="text-base font-bold leading-tight text-success">
              {classes.filter((c) => c.enabled).length} Enabled
            </div>
            <div className="text-[10px] text-muted-foreground">Inference Filters</div>
          </div>
        </div>

        <div className="flex items-center gap-2.5 rounded-lg border border-border bg-card p-2.5">
          <div className="flex size-7 shrink-0 items-center justify-center rounded-md bg-destructive/10 text-destructive">
            <AlertTriangle size={14} />
          </div>
          <div className="min-w-0">
            <div className="text-base font-bold leading-tight text-destructive">
              {classes.filter((c) => c.alertOnDetection).length} Incident Triggers
            </div>
            <div className="text-[10px] text-muted-foreground">Violation Classes</div>
          </div>
        </div>

        <div className="flex items-center gap-2.5 rounded-lg border border-border bg-card p-2.5">
          <div className="flex size-7 shrink-0 items-center justify-center rounded-md bg-purple-500/10 text-purple-500">
            <SlidersHorizontal size={14} />
          </div>
          <div className="min-w-0">
            <div className="text-base font-bold leading-tight text-foreground">58% Avg</div>
            <div className="text-[10px] text-muted-foreground">Min Confidence Bar</div>
          </div>
        </div>
      </div>

      {/* ── 2. TOOLBAR: Search + Category Filter + Save Sync ── */}
      <div className="flex flex-wrap items-center justify-between gap-2.5">
        <div className="flex flex-wrap items-center gap-2">
          <div className="relative flex items-center">
            <Search size={13} className="absolute left-2.5 text-muted-foreground" />
            <input
              type="text"
              placeholder="Search class name, category..."
              value={search}
              onChange={(e) => {
                setSearch(e.target.value)
                setCurrentPage(1)
              }}
              className="h-7.5 w-48 rounded-lg border border-border bg-card pl-7.5 pr-2.5 text-xs text-foreground placeholder:text-muted-foreground focus:w-60 focus:border-brand transition-all outline-none"
            />
          </div>

          <select
            value={categoryFilter}
            onChange={(e) => {
              setCategoryFilter(e.target.value)
              setCurrentPage(1)
            }}
            className="h-7.5 rounded-lg border border-border bg-card px-2.5 text-xs text-foreground outline-none font-medium"
          >
            <option value="all">All Categories</option>
            <option value="PPE">PPE / Safety</option>
            <option value="Vehicle">Vehicles & Transport</option>
            <option value="Person">Person & Pedestrian</option>
            <option value="Hazard">Hazards & Fire</option>
            <option value="Object">Objects & OCR</option>
          </select>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={handleSaveProfile}
            className="flex items-center gap-1.5 rounded-lg bg-brand px-3 py-1.5 text-xs font-semibold text-white transition-opacity hover:opacity-90"
          >
            <Save size={13} />
            <span>Sync to Edge Nodes</span>
          </button>
        </div>
      </div>

      {/* ── 3. CLASS CONFIGURATION TABLE ── */}
      <div className="overflow-hidden rounded-xl border border-border bg-card">
        <table className="w-full text-left text-xs">
          <thead className="border-b border-border bg-muted/20 text-[10.5px] font-semibold text-muted-foreground">
            <tr>
              <th className="px-4 py-2.5">Status</th>
              <th className="px-4 py-2.5">Class / Identifier</th>
              <th className="px-4 py-2.5">Category</th>
              <th className="px-4 py-2.5">Bounding Box Color</th>
              <th className="px-4 py-2.5">Min Confidence Threshold</th>
              <th className="px-4 py-2.5">Alert Trigger</th>
              <th className="px-4 py-2.5 text-right">24h Detections</th>
              <th className="px-4 py-2.5 text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border/60">
            {paginatedClasses.map((cls) => (
              <tr key={cls.id} className="hover:bg-muted/10 transition-colors">
                {/* Enable toggle */}
                <td className="px-4 py-2.5">
                  <button
                    onClick={() => handleToggleEnable(cls.id)}
                    className={`flex size-6 items-center justify-center rounded transition-colors ${
                      cls.enabled ? 'bg-success/10 text-success' : 'bg-muted text-muted-foreground'
                    }`}
                    title={cls.enabled ? 'Enabled' : 'Disabled'}
                  >
                    {cls.enabled ? <Eye size={13} /> : <EyeOff size={13} />}
                  </button>
                </td>

                {/* Name */}
                <td className="px-4 py-2.5 font-medium text-foreground">
                  <div>{cls.displayName}</div>
                  <div className="font-mono text-[10px] text-muted-foreground">{cls.name}</div>
                </td>

                {/* Category */}
                <td className="px-4 py-2.5">
                  <span className={`rounded-full border px-2 py-0.5 font-mono text-[9.5px] font-bold ${CATEGORY_COLORS[cls.category]}`}>
                    {cls.category}
                  </span>
                </td>

                {/* Color Dot & Hex */}
                <td className="px-4 py-2.5">
                  <div className="flex items-center gap-2">
                    <span className="size-3.5 rounded-full border border-border/80" style={{ backgroundColor: cls.color }} />
                    <span className="font-mono text-[10.5px] text-muted-foreground">{cls.color}</span>
                  </div>
                </td>

                {/* Confidence Slider */}
                <td className="px-4 py-2.5 min-w-[180px]">
                  <div className="flex items-center gap-2">
                    <input
                      type="range"
                      min={0.2}
                      max={0.95}
                      step={0.05}
                      value={cls.minConfidence}
                      onChange={(e) => handleConfidenceChange(cls.id, parseFloat(e.target.value))}
                      className="w-full accent-brand"
                    />
                    <span className="font-mono text-xs font-bold text-foreground w-10 text-right">
                      {Math.round(cls.minConfidence * 100)}%
                    </span>
                  </div>
                </td>

                {/* Incident Alert Trigger */}
                <td className="px-4 py-2.5">
                  <button
                    onClick={() => handleToggleAlert(cls.id)}
                    className={`flex items-center gap-1 rounded px-2 py-0.5 text-[10px] font-bold transition-colors ${
                      cls.alertOnDetection
                        ? 'bg-destructive/10 text-destructive border border-destructive/20'
                        : 'bg-muted/30 text-muted-foreground border border-border/40'
                    }`}
                  >
                    <ShieldAlert size={11} />
                    <span>{cls.alertOnDetection ? 'Alert Active' : 'Off'}</span>
                  </button>
                </td>

                {/* Detections count */}
                <td className="px-4 py-2.5 text-right font-mono text-muted-foreground">
                  {cls.detectionCount24h.toLocaleString()}
                </td>

                {/* Delete */}
                <td className="px-4 py-2.5 text-right">
                  <button
                    onClick={() => handleDeleteClass(cls.id)}
                    className="rounded p-1 text-muted-foreground hover:bg-destructive/10 hover:text-destructive transition-colors"
                    title="Remove class from schema"
                  >
                    <Trash2 size={13} />
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* ── 4. PAGINATION ── */}
      <Pagination
        currentPage={currentPage}
        totalPages={totalPages}
        totalItems={filtered.length}
        pageSize={pageSize}
        pageSizeOptions={[8, 16, 32]}
        onPageChange={setCurrentPage}
        onPageSizeChange={(size) => {
          setPageSize(size)
          setCurrentPage(1)
        }}
      />
    </div>
  )
}
