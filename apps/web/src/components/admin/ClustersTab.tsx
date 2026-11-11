import { useState, type FormEvent } from 'react'
import { Pencil, Plus, Search, Server, Trash2 } from 'lucide-react'
import type { Cluster } from '@/api/types'
import { Button, ErrorText, Input, Modal, Pagination } from '@/components/ui'
import { useResource } from '@/hooks/useResource'
import { clusterService } from '@/services/cluster.service'

const NO_CLUSTERS: Cluster[] = []
type Draft = { id: number | null; name: string; description: string }
const EMPTY: Draft = { id: null, name: '', description: '' }

export default function ClustersTab() {
  const clusters = useResource(clusterService.list, NO_CLUSTERS)
  const [draft, setDraft] = useState<Draft | null>(null)
  const [error, setError] = useState<string | null>(null)

  // Search & Pagination States
  const [search, setSearch] = useState('')
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(10)

  async function run(action: () => Promise<unknown>) {
    setError(null)
    try {
      await action()
      await clusters.reload()
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Operation failed')
    }
  }

  async function save(event: FormEvent) {
    event.preventDefault()
    if (!draft) return
    const input = { name: draft.name.trim(), description: draft.description.trim() || null }
    await run(() => (draft.id === null ? clusterService.create(input) : clusterService.update(draft.id, input)))
    setDraft(null)
  }

  const filteredClusters = clusters.data.filter((c) =>
    c.name.toLowerCase().includes(search.toLowerCase()) ||
    (c.description ?? '').toLowerCase().includes(search.toLowerCase())
  )

  const paginatedClusters = filteredClusters.slice((page - 1) * pageSize, page * pageSize)

  return (
    <div className="space-y-2.5">
      <ErrorText message={error ?? clusters.error} />

      {/* Table Container - VMS Console Card */}
      <div className="rounded-lg border border-line bg-panel shadow-sm overflow-hidden">
        {/* Table Toolbar */}
        <div className="flex flex-wrap items-center justify-between gap-2 border-b border-line px-3 py-2 bg-panel2/40">
          <div className="relative w-72">
            <Search size={12} className="pointer-events-none absolute left-2.5 top-1/2 -translate-y-1/2 text-dim" />
            <input
              type="text"
              value={search}
              onChange={(e) => {
                setSearch(e.target.value)
                setPage(1)
              }}
              placeholder="Filter clusters by name or description..."
              className="w-full h-7 rounded border border-line bg-panel pl-7.5 pr-2.5 text-xs text-ink placeholder:text-dim/60 outline-none focus:border-cyan-500/60 focus:ring-1 focus:ring-cyan-500/30 transition-all font-mono"
            />
          </div>

          <button
            onClick={() => setDraft(EMPTY)}
            className="flex h-7 items-center gap-1.5 rounded bg-blue-600 px-3 text-xs font-semibold text-white hover:bg-blue-500 shadow-xs cursor-pointer transition-all"
          >
            <Plus size={12} />
            <span>Add Cluster</span>
          </button>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="border-b border-line bg-panel2/70 font-mono text-[10px] font-bold uppercase tracking-wider text-dim">
              <tr>
                <th className="px-3.5 py-2">Cluster Name</th>
                <th className="px-3.5 py-2">Description</th>
                <th className="px-3.5 py-2 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-line/40 font-mono">
              {paginatedClusters.length === 0 && (
                <tr>
                  <td colSpan={3} className="py-12 text-center text-dim font-sans text-xs">
                    No clusters found. Click &quot;Add Cluster&quot; to configure a new site plant.
                  </td>
                </tr>
              )}
              {paginatedClusters.map((c) => (
                <tr key={c.id} className="transition-colors hover:bg-panel2/50 group">
                  <td className="px-3.5 py-2 font-semibold text-ink">
                    <div className="flex items-center gap-2">
                      <div className="grid size-5.5 place-items-center rounded bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
                        <Server size={11} />
                      </div>
                      <span className="font-sans font-medium text-xs text-ink">{c.name}</span>
                    </div>
                  </td>
                  <td className="px-3.5 py-2 text-dim font-sans">{c.description ?? '—'}</td>
                  <td className="px-3.5 py-2 text-right space-x-1">
                    <button
                      onClick={() => setDraft({ id: c.id, name: c.name, description: c.description ?? '' })}
                      aria-label="Edit"
                      title="Edit Cluster"
                      className="inline-flex size-6.5 items-center justify-center rounded border border-line bg-panel2/60 text-dim hover:text-cyan-400 hover:border-cyan-500/40 cursor-pointer transition-colors"
                    >
                      <Pencil size={11} />
                    </button>
                    <button
                      onClick={() => window.confirm(`Delete cluster "${c.name}"?`) && run(() => clusterService.remove(c.id))}
                      aria-label="Delete"
                      title="Delete Cluster"
                      className="inline-flex size-6.5 items-center justify-center rounded border border-line bg-panel2/60 text-dim hover:text-rose-400 hover:border-rose-500/40 hover:bg-rose-500/10 cursor-pointer transition-colors"
                    >
                      <Trash2 size={11} />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Pagination Controls */}
        <Pagination
          page={page}
          totalItems={filteredClusters.length}
          pageSize={pageSize}
          onPageChange={setPage}
          onPageSizeChange={(s) => {
            setPageSize(s)
            setPage(1)
          }}
        />
      </div>

      {draft && (
        <Modal title={draft.id === null ? 'Add New Cluster' : `Edit Cluster: ${draft.name}`} onClose={() => setDraft(null)}>
          <form onSubmit={save} className="space-y-3.5">
            <Input
              label="Cluster Name"
              value={draft.name}
              onChange={(e) => setDraft({ ...draft, name: e.target.value })}
              placeholder="e.g. Cluster Alpha (Main Plant)"
              required
              autoFocus
            />
            <Input
              label="Description"
              value={draft.description}
              onChange={(e) => setDraft({ ...draft, description: e.target.value })}
              placeholder="Facility region or industrial zone notes"
            />
            <div className="flex justify-end gap-2 pt-2">
              <Button type="button" variant="ghost" onClick={() => setDraft(null)} className="h-8 text-xs">
                Cancel
              </Button>
              <Button type="submit" variant="primary" className="h-8 text-xs font-semibold px-4 bg-blue-600">
                Save Cluster
              </Button>
            </div>
          </form>
        </Modal>
      )}
    </div>
  )
}

