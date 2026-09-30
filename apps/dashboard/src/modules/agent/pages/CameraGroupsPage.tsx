import { useState } from 'react'
import { Plus, MapPin, Camera, AlertTriangle, Activity, CheckCircle2, Layers, X } from 'lucide-react'
import { useEdgeOps } from '@/core/edge-ops/EdgeOpsContext'

const BTN_PRIMARY = 'flex cursor-pointer items-center gap-1.5 rounded-lg bg-brand px-3 py-2 text-sm font-semibold text-brand-foreground transition-opacity hover:opacity-90'
const BTN_SECONDARY = 'flex cursor-pointer items-center gap-1.5 rounded-lg border border-border bg-background px-3 py-1.5 text-xs font-semibold text-foreground transition-colors hover:bg-muted'
const INPUT = 'w-full rounded-lg border border-border bg-background px-3 py-2 text-sm text-foreground outline-none focus:border-brand'

export default function CameraGroupsPage() {
  const { cameraGroups: groups, createCameraGroup } = useEdgeOps()
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [newGroupName, setNewGroupName] = useState('')
  const [newGroupSite, setNewGroupSite] = useState('')

  function handleCreateGroup(e: React.FormEvent) {
    e.preventDefault()
    if (!newGroupName.trim()) return

    createCameraGroup({ name: newGroupName.trim(), site: newGroupSite.trim() || 'default' })
    setNewGroupName('')
    setNewGroupSite('')
    setShowCreateModal(false)
  }

  return (
    <div className="flex flex-col gap-4">
      <div className="flex justify-end">
        <button className={BTN_PRIMARY} onClick={() => setShowCreateModal(true)}>
          <Plus size={15} />
          <span>New Camera Group</span>
        </button>
      </div>

      <div className="grid grid-cols-[repeat(auto-fill,minmax(340px,1fr))] gap-4">
        {groups.map((grp) => {
          const pill =
            grp.onlineCameras === grp.totalCameras
              ? 'bg-success/10 text-success'
              : grp.onlineCameras > 0
              ? 'bg-warning/10 text-warning'
              : 'bg-destructive/10 text-destructive'
          return (
            <div key={grp.id} className="flex flex-col gap-3.5 rounded-xl border border-border bg-card p-5">
              <div>
                <div className="mb-1 flex items-center justify-between">
                  <span className="font-mono text-[11px] font-bold text-brand">{grp.id}</span>
                  <span className={`rounded-full px-2 py-0.5 text-[11px] font-semibold ${pill}`}>
                    {grp.onlineCameras} / {grp.totalCameras} Online
                  </span>
                </div>
                <h3 className="mb-1.5 mt-1 text-base font-extrabold text-foreground">{grp.name}</h3>
                <p className="text-xs leading-normal text-muted-foreground">{grp.description}</p>
              </div>

              <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
                <MapPin size={13} className="text-brand" />
                <span>{grp.site}</span>
              </div>

              <div className="grid grid-cols-2 gap-2 rounded-lg border border-border bg-muted/40 px-3.5 py-3 text-xs">
                <div>
                  <span className="text-[10px] text-muted-foreground">Cameras</span>
                  <div className="mt-0.5 flex items-center gap-1 font-bold">
                    <Camera size={13} />
                    <span>{grp.cameraIds.join(', ')}</span>
                  </div>
                </div>

                <div>
                  <span className="text-[10px] text-muted-foreground">Throughput</span>
                  <div className="mt-0.5 flex items-center gap-1 font-mono font-bold">
                    <Activity size={13} className="text-success" />
                    <span>{grp.aggregateFps} FPS</span>
                  </div>
                </div>

                <div className="col-span-2">
                  <span className="text-[10px] text-muted-foreground">Primary Inference Model</span>
                  <div className="mt-0.5 flex items-center gap-1 font-bold text-brand">
                    <Layers size={13} />
                    <span>{grp.primaryModel}</span>
                  </div>
                </div>
              </div>

              <div className="mt-auto flex items-center justify-between pt-2">
                {grp.activeAlerts > 0 ? (
                  <span className="flex items-center gap-1 rounded-full bg-destructive/10 px-2 py-0.5 text-xs font-semibold text-destructive">
                    <AlertTriangle size={12} />
                    <span>{grp.activeAlerts} Active Alerts</span>
                  </span>
                ) : (
                  <span className="flex items-center gap-1 text-xs font-semibold text-success">
                    <CheckCircle2 size={13} />
                    <span>Normal Operations</span>
                  </span>
                )}

                <button className={BTN_SECONDARY}>Configure Group</button>
              </div>
            </div>
          )
        })}
      </div>

      {/* Create Camera Group Modal */}
      {showCreateModal && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4 backdrop-blur-sm"
          onClick={() => setShowCreateModal(false)}
        >
          <div
            className="w-full max-w-[480px] overflow-hidden rounded-xl border border-border bg-card"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between border-b border-border p-4">
              <div className="text-base font-extrabold">Create New Camera Group</div>
              <button
                className="flex size-7 cursor-pointer items-center justify-center rounded-md text-muted-foreground hover:bg-muted hover:text-foreground"
                onClick={() => setShowCreateModal(false)}
              >
                <X size={16} />
              </button>
            </div>
            <form onSubmit={handleCreateGroup} className="flex flex-col gap-3.5 p-5">
              <div>
                <label className="mb-1.5 block text-xs font-bold">Group Name</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Loading Dock North"
                  value={newGroupName}
                  onChange={(e) => setNewGroupName(e.target.value)}
                  className={INPUT}
                />
              </div>
              <div>
                <label className="mb-1.5 block text-xs font-bold">Facility Site / Project</label>
                <input
                  type="text"
                  placeholder="e.g. Warehouse 3B"
                  value={newGroupSite}
                  onChange={(e) => setNewGroupSite(e.target.value)}
                  className={INPUT}
                />
              </div>
              <div className="mt-2.5 flex justify-end gap-2.5">
                <button type="button" className={BTN_SECONDARY} onClick={() => setShowCreateModal(false)}>Cancel</button>
                <button type="submit" className={BTN_PRIMARY}>Create Group</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
