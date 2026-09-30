import { useState, useMemo } from 'react'
import {
  Boxes, Search, Plus, Rocket, Cpu,
  ShieldCheck,
} from 'lucide-react'
import { useEdgeOps } from '@/core/edge-ops/EdgeOpsContext'
import Pagination from '@/shared/components/Pagination'
import ModelDeploymentModal from '@/modules/agent/components/ModelDeploymentModal'
import type { ModelRegistryItem } from '@/modules/ai/types/ai'


export default function ModelsPage() {
  const { clusters, models, deployModelToNode } = useEdgeOps()
  const [search, setSearch] = useState('')
  const [taskFilter, setTaskFilter] = useState<'all' | 'detection' | 'pose' | 'segmentation'>('all')

  // Pagination
  const [currentPage, setCurrentPage] = useState(1)
  const [pageSize, setPageSize] = useState(6)

  // Deploy Modal
  const [deployTargetModel, setDeployTargetModel] = useState<ModelRegistryItem | null>(null)
  const [actionNotice, setActionNotice] = useState<string | null>(null)

  // Filter logic
  const filtered = useMemo(() => {
    return models.filter((m) => {
      const matchSearch =
        !search ||
        m.name.toLowerCase().includes(search.toLowerCase()) ||
        m.version.toLowerCase().includes(search.toLowerCase()) ||
        m.description.toLowerCase().includes(search.toLowerCase()) ||
        m.classes.some((c) => c.toLowerCase().includes(search.toLowerCase()))

      const matchTask = taskFilter === 'all' || m.task === taskFilter
      return matchSearch && matchTask
    })
  }, [models, search, taskFilter])

  // Pagination slice
  const paginatedModels = useMemo(() => {
    const start = (currentPage - 1) * pageSize
    return filtered.slice(start, start + pageSize)
  }, [filtered, currentPage, pageSize])

  const totalPages = Math.ceil(filtered.length / pageSize)

  const handleDeploySuccess = (modelConfig: { modelName: string; tag: string; precision: string; confidenceThreshold: number }) => {
    if (clusters[0]?.nodes[0]) {
      deployModelToNode({
        nodeId: clusters[0].nodes[0].id,
        modelName: modelConfig.modelName,
        tag: modelConfig.tag,
        precision: modelConfig.precision,
        confidenceThreshold: modelConfig.confidenceThreshold,
      })
      setActionNotice(`Model ${modelConfig.tag} deployed successfully`)
      setTimeout(() => setActionNotice(null), 3500)
    }
  }

  return (
    <div className="flex flex-col gap-4">
      {/* Deploy Modal */}
      {deployTargetModel && (
        <ModelDeploymentModal
          isOpen={true}
          onClose={() => setDeployTargetModel(null)}
          nodeName={clusters[0]?.nodes[0]?.name || 'Target Node'}
          onDeploy={(cfg) => {
            handleDeploySuccess(cfg as { modelName: string; tag: string; precision: string; confidenceThreshold: number })
            setDeployTargetModel(null)
          }}
        />
      )}

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
            <Boxes size={14} />
          </div>
          <div className="min-w-0">
            <div className="text-base font-bold leading-tight text-foreground">{models.length} Models</div>
            <div className="text-[10px] text-muted-foreground">Registered Artifacts</div>
          </div>
        </div>

        <div className="flex items-center gap-2.5 rounded-lg border border-border bg-card p-2.5">
          <div className="flex size-7 shrink-0 items-center justify-center rounded-md bg-success/10 text-success">
            <Rocket size={14} />
          </div>
          <div className="min-w-0">
            <div className="text-base font-bold leading-tight text-success">
              {models.reduce((s, m) => s + m.activeDeployments, 0)} Active
            </div>
            <div className="text-[10px] text-muted-foreground">Edge Deployments</div>
          </div>
        </div>

        <div className="flex items-center gap-2.5 rounded-lg border border-border bg-card p-2.5">
          <div className="flex size-7 shrink-0 items-center justify-center rounded-md bg-purple-500/10 text-purple-500">
            <Cpu size={14} />
          </div>
          <div className="min-w-0">
            <div className="text-base font-bold leading-tight text-foreground">6.4 ms</div>
            <div className="text-[10px] text-muted-foreground">Avg TensorRT Latency</div>
          </div>
        </div>

        <div className="flex items-center gap-2.5 rounded-lg border border-border bg-card p-2.5">
          <div className="flex size-7 shrink-0 items-center justify-center rounded-md bg-info/10 text-info">
            <ShieldCheck size={14} />
          </div>
          <div className="min-w-0">
            <div className="text-base font-bold leading-tight text-foreground">94.8%</div>
            <div className="text-[10px] text-muted-foreground">Mean Average Precision</div>
          </div>
        </div>
      </div>

      {/* ── 2. TOOLBAR: Search + Task Filter + Register Model ── */}
      <div className="flex flex-wrap items-center justify-between gap-2.5">
        <div className="flex flex-wrap items-center gap-2">
          <div className="relative flex items-center">
            <Search size={13} className="absolute left-2.5 text-muted-foreground" />
            <input
              type="text"
              placeholder="Search model, version, class..."
              value={search}
              onChange={(e) => {
                setSearch(e.target.value)
                setCurrentPage(1)
              }}
              className="h-7.5 w-48 rounded-lg border border-border bg-card pl-7.5 pr-2.5 text-xs text-foreground placeholder:text-muted-foreground focus:w-60 focus:border-brand transition-all outline-none"
            />
          </div>

          {/* Task Buttons */}
          <div className="flex items-center gap-1 rounded-lg border border-border bg-card p-0.5">
            {(['all', 'detection', 'pose', 'segmentation'] as const).map((t) => (
              <button
                key={t}
                onClick={() => {
                  setTaskFilter(t)
                  setCurrentPage(1)
                }}
                className={`rounded px-2.5 py-0.5 text-[11px] font-semibold capitalize transition-colors ${
                  taskFilter === t ? 'bg-foreground text-background' : 'text-muted-foreground hover:bg-muted/60'
                }`}
              >
                {t}
              </button>
            ))}
          </div>
        </div>

        <button
          onClick={() => {
            setActionNotice('Model Registry Sync: Connected to YOLO hub.')
            setTimeout(() => setActionNotice(null), 3000)
          }}
          className="flex items-center gap-1.5 rounded-lg bg-brand px-3 py-1.5 text-xs font-semibold text-white transition-opacity hover:opacity-90"
        >
          <Plus size={13} />
          <span>Register New Model</span>
        </button>
      </div>

      {/* ── 3. MODELS GRID ── */}
      <div className="grid grid-cols-1 items-start gap-3.5 sm:grid-cols-2 lg:grid-cols-3">
        {paginatedModels.map((model) => (
          <div
            key={model.id}
            className="flex flex-col justify-between rounded-xl border border-border bg-card p-4 transition-all hover:border-border/80"
          >
            <div>
              {/* Header */}
              <div className="flex items-start justify-between gap-2">
                <div>
                  <div className="flex items-center gap-1.5">
                    <h3 className="text-xs font-bold text-foreground">{model.name}</h3>
                    <span className="rounded bg-brand/10 px-1.5 py-0.2 font-mono text-[9.5px] font-bold text-brand">
                      {model.version}
                    </span>
                  </div>
                  <span className="rounded bg-muted/50 px-1.5 py-0.2 font-mono text-[9px] text-muted-foreground">
                    {model.task}
                  </span>
                </div>

                <span className="rounded-full bg-success/10 px-2 py-0.5 font-mono text-[9.5px] font-bold text-success">
                  {model.activeDeployments} Active
                </span>
              </div>

              <p className="mt-2 text-xs text-muted-foreground leading-relaxed line-clamp-2">
                {model.description}
              </p>

              {/* Hardware Specs Matrix */}
              <div className="mt-3 grid grid-cols-3 gap-2 rounded-lg border border-border/60 bg-muted/10 p-2 text-center text-xs font-mono">
                <div>
                  <span className="block text-[9.5px] text-muted-foreground">Latency (Orin)</span>
                  <strong className="text-success text-[11px]">{model.latencyOrinMs} ms</strong>
                </div>
                <div>
                  <span className="block text-[9.5px] text-muted-foreground">mAP @ .50</span>
                  <strong className="text-foreground text-[11px]">{model.mAP}%</strong>
                </div>
                <div>
                  <span className="block text-[9.5px] text-muted-foreground">Size</span>
                  <strong className="text-foreground text-[11px]">{model.fileSizeMb} MB</strong>
                </div>
              </div>

              {/* Framework & Classes */}
              <div className="mt-3 space-y-1.5 text-xs">
                <div className="flex items-center justify-between text-[11px]">
                  <span className="text-muted-foreground">Engine:</span>
                  <span className="font-mono text-foreground">{model.framework} ({model.precision})</span>
                </div>
                <div>
                  <span className="text-[10.5px] text-muted-foreground block mb-1">Target Classes ({model.classes.length}):</span>
                  <div className="flex flex-wrap gap-1">
                    {model.classes.slice(0, 4).map((c) => (
                      <span key={c} className="rounded bg-muted/40 px-1.5 py-0.2 font-mono text-[9.5px] text-muted-foreground border border-border/40">
                        {c}
                      </span>
                    ))}
                    {model.classes.length > 4 && (
                      <span className="rounded bg-muted/20 px-1 py-0.2 font-mono text-[9px] text-muted-foreground">
                        +{model.classes.length - 4} more
                      </span>
                    )}
                  </div>
                </div>
              </div>
            </div>

            {/* Actions */}
            <div className="mt-4 flex items-center justify-between border-t border-border/60 pt-3">
              <span className="text-[10px] text-muted-foreground font-mono">Updated {model.updatedAt}</span>
              <div className="flex items-center gap-1.5">
                <button
                  onClick={() => setDeployTargetModel(model)}
                  className="flex items-center gap-1 rounded bg-brand px-2.5 py-1 text-xs font-semibold text-white hover:opacity-90 transition-opacity"
                >
                  <Rocket size={12} />
                  <span>Deploy</span>
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* ── 4. PAGINATION ── */}
      <Pagination
        currentPage={currentPage}
        totalPages={totalPages}
        totalItems={filtered.length}
        pageSize={pageSize}
        pageSizeOptions={[6, 12, 24]}
        onPageChange={setCurrentPage}
        onPageSizeChange={(size) => {
          setPageSize(size)
          setCurrentPage(1)
        }}
      />
    </div>
  )
}
