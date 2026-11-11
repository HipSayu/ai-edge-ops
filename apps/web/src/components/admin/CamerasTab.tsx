import { useState, type FormEvent } from 'react'
import {
  Check,
  FolderSync,
  Network,
  Pencil,
  Search,
  Trash2,
  Upload,
  Video,
} from 'lucide-react'
import type { Camera, Cluster, NodeItem } from '@/api/types'
import { Badge, Button, ErrorText, Input, Modal, Pagination, Select } from '@/components/ui'
import { useResource } from '@/hooks/useResource'
import { cameraService } from '@/services/camera.service'
import { clusterService } from '@/services/cluster.service'
import { nodeService } from '@/services/node.service'

const NO_CAMERAS: Camera[] = []
const NO_CLUSTERS: Cluster[] = []
const NO_NODES: NodeItem[] = []

export default function CamerasTab({ canManage }: { canManage: boolean }) {
  const cameras = useResource(cameraService.list, NO_CAMERAS)
  const { data: clusters } = useResource(clusterService.list, NO_CLUSTERS)
  const { data: nodes } = useResource(nodeService.list, NO_NODES)

  const [file, setFile] = useState<File | null>(null)
  const [name, setName] = useState('')
  const [selectedClusterId, setSelectedClusterId] = useState<number | null>(null)
  const [selectedNodeId, setSelectedNodeId] = useState<number | null>(null)

  const [editing, setEditing] = useState<Camera | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [notice, setNotice] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  // Search & Pagination States
  const [search, setSearch] = useState('')
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(10)

  // Nodes filtered by currently selected cluster for modal / upload
  const availableNodesForUpload = selectedClusterId
    ? nodes.filter((n) => n.cluster_id === selectedClusterId)
    : nodes

  async function run(action: () => Promise<unknown>, done?: string) {
    setBusy(true)
    setError(null)
    setNotice(null)
    try {
      await action()
      if (done) setNotice(done)
      await cameras.reload()
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Operation failed')
    } finally {
      setBusy(false)
    }
  }

  async function upload(event: FormEvent) {
    event.preventDefault()
    if (!file || !selectedNodeId) return
    const chosenNode = nodes.find((n) => n.id === selectedNodeId)
    const clusterId = chosenNode ? chosenNode.cluster_id : selectedClusterId
    await run(
      () => cameraService.upload(file, name.trim() || file.name, selectedNodeId, clusterId),
      'Camera stream attached to node successfully.'
    )
    setFile(null)
    setName('')
  }

  async function sync() {
    await run(async () => {
      const result = await cameraService.sync()
      const extra = result.unmatched_folders.length ? `, ${result.unmatched_folders.length} unmatched folder(s)` : ''
      setNotice(`Video directory synchronized: ${result.cameras} camera(s), ${result.videos} video(s)${extra}.`)
    })
  }

  async function saveEdit(event: FormEvent) {
    event.preventDefault()
    if (!editing) return
    await run(() =>
      cameraService.update(editing.id, { name: editing.name, zone: editing.zone, enabled: editing.enabled })
    )
    setEditing(null)
  }

  const getNodeName = (id: number | null) => nodes.find((n) => n.id === id)?.name ?? '—'
  const getClusterName = (id: number | null) => clusters.find((c) => c.id === id)?.name ?? '—'

  const filteredCameras = cameras.data.filter((c) =>
    c.name.toLowerCase().includes(search.toLowerCase()) ||
    c.videos.join(' ').toLowerCase().includes(search.toLowerCase()) ||
    getNodeName(c.node_id).toLowerCase().includes(search.toLowerCase()) ||
    getClusterName(c.cluster_id).toLowerCase().includes(search.toLowerCase())
  )

  const paginatedCameras = filteredCameras.slice((page - 1) * pageSize, page * pageSize)

  return (
    <div className="space-y-3">
      {/* Upload and Sync Panel with Hierarchy: Cluster -> Node -> Camera */}
      <form
        onSubmit={upload}
        className="rounded-xl border border-line bg-panel p-3.5 shadow-xs"
      >
        <div className="mb-2.5 flex items-center justify-between border-b border-line pb-2">
          <div className="flex items-center gap-2">
            <Upload size={13} className="text-blue-500" />
            <h3 className="text-xs font-bold uppercase tracking-wider text-ink">
              Add Camera Feed (Hierarchy: Cluster &rarr; Node &rarr; Camera)
            </h3>
          </div>
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={sync}
            disabled={busy}
            title="Scan video directory and add camera entries"
            className="text-xs gap-1.5 h-6.5"
          >
            <FolderSync size={12} />
            <span className="hidden sm:inline">Sync Directory</span>
          </Button>
        </div>

        <div className="grid items-end gap-3 md:grid-cols-[1.2fr_1fr_1fr_1fr_auto]">
          <label className="block text-xs">
            <span className="mb-1 block font-semibold text-dim">Video Source File</span>
            <input
              type="file"
              accept="video/*"
              onChange={(e) => setFile(e.target.files?.[0] ?? null)}
              className="w-full text-xs text-dim file:mr-2 file:cursor-pointer file:rounded file:border-0 file:bg-panel2 file:px-2.5 file:py-1 file:text-xs file:font-semibold file:text-ink hover:file:bg-line"
            />
          </label>

          <Input
            label="Camera Name"
            value={name}
            onChange={(e) => {
              setName(e.target.value)
              setPage(1)
            }}
            placeholder={file?.name ?? 'Camera 01'}
          />

          {/* 1. Select Cluster */}
          <Select
            label="1. Parent Cluster"
            value={selectedClusterId ?? ''}
            onChange={(e) => {
              const cid = e.target.value ? Number(e.target.value) : null
              setSelectedClusterId(cid)
              setSelectedNodeId(null)
            }}
            required
          >
            <option value="">Select Cluster...</option>
            {clusters.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name}
              </option>
            ))}
          </Select>

          {/* 2. Select Node belonging to Cluster */}
          <Select
            label="2. Edge Node"
            value={selectedNodeId ?? ''}
            onChange={(e) => setSelectedNodeId(e.target.value ? Number(e.target.value) : null)}
            disabled={!selectedClusterId || availableNodesForUpload.length === 0}
            required
          >
            <option value="">
              {!selectedClusterId
                ? 'Select cluster first...'
                : availableNodesForUpload.length === 0
                  ? 'No nodes in cluster'
                  : 'Select Node...'}
            </option>
            {availableNodesForUpload.map((n) => (
              <option key={n.id} value={n.id}>
                {n.name}
              </option>
            ))}
          </Select>

          <Button
            type="submit"
            variant="primary"
            disabled={!file || !selectedNodeId || busy}
            className="w-full md:w-auto h-7 px-4 text-xs font-semibold gap-1.5"
          >
            <Upload size={13} /> Add Camera
          </Button>
        </div>
      </form>

      <ErrorText message={error ?? cameras.error} />
      {notice && (
        <div className="flex items-center gap-2 rounded-lg bg-emerald-500/10 border border-emerald-500/20 px-3 py-1.5 text-xs font-medium text-emerald-400">
          <Check size={14} />
          <span>{notice}</span>
        </div>
      )}

      {/* Camera List with Hierarchy Columns */}
      <div className="rounded-xl border border-line bg-panel shadow-xs overflow-hidden">
        {/* Table Toolbar */}
        <div className="flex flex-wrap items-center justify-between gap-2 border-b border-line px-4 py-2 bg-panel2/40">
          <div className="relative w-full sm:w-64">
            <Search size={13} className="pointer-events-none absolute left-2.5 top-1/2 -translate-y-1/2 text-dim" />
            <input
              type="text"
              value={search}
              onChange={(e) => {
                setSearch(e.target.value)
                setPage(1)
              }}
              placeholder="Search cameras, nodes, clusters..."
              className="w-full rounded-lg border border-line bg-panel pl-8 pr-3 py-1 text-xs text-ink outline-none focus:border-brand"
            />
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="border-b border-line bg-panel2/60 font-semibold uppercase tracking-wider text-dim">
              <tr>
                <th className="px-4 py-2.5">Camera Name</th>
                <th className="px-4 py-2.5">Assigned Node</th>
                <th className="px-4 py-2.5">Parent Cluster</th>
                <th className="px-4 py-2.5">Source Video</th>
                <th className="px-4 py-2.5">Status</th>
                {canManage && <th className="px-4 py-2.5 text-right">Actions</th>}
              </tr>
            </thead>
            <tbody className="divide-y divide-line/60">
              {paginatedCameras.length === 0 && (
                <tr>
                  <td colSpan={6} className="py-8 text-center text-dim">
                    No matching cameras found. Make sure you have created a Cluster and at least one Node first.
                  </td>
                </tr>
              )}
              {paginatedCameras.map((c) => (
                <tr key={c.id} className="transition-colors hover:bg-panel2/30">
                  <td className="px-4 py-2.5 font-semibold text-ink font-mono">
                    <div className="flex items-center gap-2">
                      <Video size={13} className="text-blue-400 shrink-0" />
                      <span>{c.name}</span>
                    </div>
                  </td>
                  <td className="px-4 py-2.5">
                    <span className="flex items-center gap-1 rounded bg-panel2 px-2 py-0.5 text-xs text-emerald-400 font-mono">
                      <Network size={11} />
                      {getNodeName(c.node_id)}
                    </span>
                  </td>
                  <td className="px-4 py-2.5">
                    <span className="rounded bg-panel2 px-2 py-0.5 text-xs text-dim">
                      {getClusterName(c.cluster_id)}
                    </span>
                  </td>
                  <td className="px-4 py-2.5 font-mono text-[11px] text-dim max-w-xs truncate">
                    {c.videos.join(', ') || '—'}
                  </td>
                  <td className="px-4 py-2.5">
                    <Badge tone={c.enabled ? 'ok' : 'neutral'} dot>
                      {c.enabled ? 'Active' : 'Stopped'}
                    </Badge>
                  </td>
                  {canManage && (
                    <td className="px-4 py-2.5 text-right space-x-1">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => setEditing(c)}
                        aria-label="Edit"
                        className="size-7 p-0"
                      >
                        <Pencil size={13} />
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() =>
                          window.confirm(`Delete camera "${c.name}"?`) &&
                          run(() => cameraService.remove(c.id), 'Camera deleted.')
                        }
                        aria-label="Delete"
                        className="size-7 p-0 text-dim hover:text-rose-500 hover:bg-rose-500/10"
                      >
                        <Trash2 size={13} />
                      </Button>
                    </td>
                  )}
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Pagination Controls */}
        <Pagination
          page={page}
          totalItems={filteredCameras.length}
          pageSize={pageSize}
          onPageChange={setPage}
          onPageSizeChange={(s) => {
            setPageSize(s)
            setPage(1)
          }}
        />
      </div>

      {/* Edit Camera Modal */}
      {editing && (
        <Modal title={`Edit Camera: ${editing.name}`} onClose={() => setEditing(null)}>
          <form onSubmit={saveEdit} className="space-y-4">
            <Input
              label="Camera Name"
              value={editing.name}
              onChange={(e) => setEditing({ ...editing, name: e.target.value })}
              required
            />

            <Select
              label="Assigned Edge Node"
              value={editing.node_id ?? ''}
              onChange={(e) => {
                const nid = e.target.value ? Number(e.target.value) : null
                const n = nodes.find((item) => item.id === nid)
                setEditing({
                  ...editing,
                  node_id: nid,
                  cluster_id: n ? n.cluster_id : editing.cluster_id,
                })
              }}
              required
            >
              <option value="">Select Node...</option>
              {nodes.map((n) => (
                <option key={n.id} value={n.id}>
                  {n.name} ({getClusterName(n.cluster_id)})
                </option>
              ))}
            </Select>

            <label className="flex items-center gap-2 text-xs font-semibold cursor-pointer select-none">
              <input
                type="checkbox"
                checked={editing.enabled}
                onChange={(e) => setEditing({ ...editing, enabled: e.target.checked })}
                className="size-4 rounded text-brand focus:ring-brand"
              />
              <span>Enable detection stream</span>
            </label>

            <Button type="submit" variant="primary" className="w-full h-8 text-xs mt-2">
              Save Changes
            </Button>
          </form>
        </Modal>
      )}
    </div>
  )
}
