import { useState, type FormEvent } from 'react'
import { Network, Pencil, Plus, Search, Trash2 } from 'lucide-react'
import type { Cluster, NodeItem } from '@/api/types'
import { Button, ErrorText, Input, Modal, Pagination, Select } from '@/components/ui'
import { useResource } from '@/hooks/useResource'
import { clusterService } from '@/services/cluster.service'
import { nodeService } from '@/services/node.service'

const NO_NODES: NodeItem[] = []
const NO_CLUSTERS: Cluster[] = []

type Draft = {
  id: number | null
  cluster_id: number | null
  name: string
  description: string
  ip_address: string
}

const EMPTY: Draft = {
  id: null,
  cluster_id: null,
  name: '',
  description: '',
  ip_address: '',
}

export default function NodesTab() {
  const nodes = useResource(nodeService.list, NO_NODES)
  const { data: clusters } = useResource(clusterService.list, NO_CLUSTERS)
  const [draft, setDraft] = useState<Draft | null>(null)
  const [error, setError] = useState<string | null>(null)

  // Search, Filter & Pagination States
  const [clusterFilter, setClusterFilter] = useState<number | null>(null)
  const [search, setSearch] = useState('')
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(10)

  async function run(action: () => Promise<unknown>) {
    setError(null)
    try {
      await action()
      await nodes.reload()
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Operation failed')
    }
  }

  async function save(event: FormEvent) {
    event.preventDefault()
    if (!draft || draft.cluster_id === null) return
    const input = {
      cluster_id: draft.cluster_id,
      name: draft.name.trim(),
      description: draft.description.trim() || null,
      ip_address: draft.ip_address.trim() || undefined,
    }
    await run(() => (draft.id === null ? nodeService.create(input) : nodeService.update(draft.id, input)))
    setDraft(null)
  }

  const getClusterName = (id: number) => clusters.find((c) => c.id === id)?.name ?? '—'

  const filteredNodes = nodes.data.filter((n) => {
    const matchCluster = clusterFilter === null || n.cluster_id === clusterFilter
    const matchSearch =
      n.name.toLowerCase().includes(search.toLowerCase()) ||
      (n.ip_address ?? '').toLowerCase().includes(search.toLowerCase()) ||
      getClusterName(n.cluster_id).toLowerCase().includes(search.toLowerCase())
    return matchCluster && matchSearch
  })

  const paginatedNodes = filteredNodes.slice((page - 1) * pageSize, page * pageSize)

  return (
    <div className="space-y-3">
      <ErrorText message={error ?? nodes.error} />

      {/* Table Container */}
      <div className="rounded-xl border border-line bg-panel shadow-xs overflow-hidden">
        {/* Table Toolbar */}
        <div className="flex flex-wrap items-center justify-between gap-2 border-b border-line px-4 py-2 bg-panel2/40">
          <div className="flex items-center gap-2">
            <div className="relative w-56">
              <Search size={13} className="pointer-events-none absolute left-2.5 top-1/2 -translate-y-1/2 text-dim" />
              <input
                type="text"
                value={search}
                onChange={(e) => {
                  setSearch(e.target.value)
                  setPage(1)
                }}
                placeholder="Search nodes, IP..."
                className="w-full rounded-lg border border-line bg-panel pl-8 pr-3 py-1 text-xs text-ink outline-none focus:border-brand"
              />
            </div>

            {/* Cluster Filter dropdown */}
            <select
              value={clusterFilter ?? ''}
              onChange={(e) => {
                setClusterFilter(e.target.value ? Number(e.target.value) : null)
                setPage(1)
              }}
              className="rounded-lg border border-line bg-panel px-2.5 py-1 text-xs text-ink outline-none focus:border-brand cursor-pointer"
            >
              <option value="">All Clusters ({clusters.length})</option>
              {clusters.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name}
                </option>
              ))}
            </select>
          </div>

          <Button
            variant="primary"
            size="sm"
            onClick={() => setDraft({ ...EMPTY, cluster_id: clusters[0]?.id ?? null })}
            disabled={clusters.length === 0}
            className="h-7 text-xs gap-1.5 font-semibold"
          >
            <Plus size={13} /> Add Edge Node
          </Button>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="border-b border-line bg-panel2/60 font-semibold uppercase tracking-wider text-dim">
              <tr>
                <th className="px-4 py-2.5">Node Name</th>
                <th className="px-4 py-2.5">Belongs to Cluster</th>
                <th className="px-4 py-2.5">IP Address</th>
                <th className="px-4 py-2.5">Description</th>
                <th className="px-4 py-2.5 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-line/60">
              {paginatedNodes.length === 0 && (
                <tr>
                  <td colSpan={5} className="py-8 text-center text-dim">
                    {clusters.length === 0
                      ? 'Please add at least one Cluster before deploying Nodes.'
                      : 'No nodes found. Add a node under a cluster to attach cameras.'}
                  </td>
                </tr>
              )}
              {paginatedNodes.map((n) => (
                <tr key={n.id} className="transition-colors hover:bg-panel2/30">
                  <td className="px-4 py-2.5 font-semibold text-ink font-mono">
                    <div className="flex items-center gap-2">
                      <Network size={13} className="text-emerald-400 shrink-0" />
                      <span>{n.name}</span>
                    </div>
                  </td>
                  <td className="px-4 py-2.5">
                    <span className="rounded bg-panel2 px-2 py-0.5 text-xs text-dim">
                      {getClusterName(n.cluster_id)}
                    </span>
                  </td>
                  <td className="px-4 py-2.5 font-mono text-[11px] text-blue-400">
                    {n.ip_address ?? '—'}
                  </td>
                  <td className="px-4 py-2.5 text-dim">{n.description ?? '—'}</td>
                  <td className="px-4 py-2.5 text-right space-x-1">
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() =>
                        setDraft({
                          id: n.id,
                          cluster_id: n.cluster_id,
                          name: n.name,
                          description: n.description ?? '',
                          ip_address: n.ip_address ?? '',
                        })
                      }
                      aria-label="Edit"
                      className="size-7 p-0"
                    >
                      <Pencil size={13} />
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => window.confirm(`Delete node "${n.name}"?`) && run(() => nodeService.remove(n.id))}
                      aria-label="Delete"
                      className="size-7 p-0 text-dim hover:text-rose-500 hover:bg-rose-500/10"
                    >
                      <Trash2 size={13} />
                    </Button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Pagination Controls */}
        <Pagination
          page={page}
          totalItems={filteredNodes.length}
          pageSize={pageSize}
          onPageChange={setPage}
          onPageSizeChange={(s) => {
            setPageSize(s)
            setPage(1)
          }}
        />
      </div>

      {draft && (
        <Modal title={draft.id === null ? 'Add New Edge Node' : `Edit Node: ${draft.name}`} onClose={() => setDraft(null)}>
          <form onSubmit={save} className="space-y-4">
            <Select
              label="Select Parent Cluster"
              value={draft.cluster_id ?? ''}
              onChange={(e) => setDraft({ ...draft, cluster_id: Number(e.target.value) })}
              required
            >
              <option value="">Select a cluster...</option>
              {clusters.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name}
                </option>
              ))}
            </Select>

            <Input
              label="Node Name"
              value={draft.name}
              onChange={(e) => setDraft({ ...draft, name: e.target.value })}
              placeholder="e.g. Node 101 - Processing Hub"
              required
              autoFocus
            />

            <Input
              label="IP Address (Optional)"
              value={draft.ip_address}
              onChange={(e) => setDraft({ ...draft, ip_address: e.target.value })}
              placeholder="e.g. 192.168.1.101"
            />

            <Input
              label="Description"
              value={draft.description}
              onChange={(e) => setDraft({ ...draft, description: e.target.value })}
              placeholder="Server location or edge device specs"
            />

            <Button type="submit" variant="primary" className="w-full h-8 text-xs mt-2">
              Save Node
            </Button>
          </form>
        </Modal>
      )}
    </div>
  )
}

