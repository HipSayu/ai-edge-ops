import { useState, type FormEvent } from 'react'
import { Pencil, Plus, Search, Trash2 } from 'lucide-react'
import type { Cluster, Role, User } from '@/api/types'
import { Badge, Button, ErrorText, Input, Modal, Pagination, Select } from '@/components/ui'
import { ROLE_LABEL, ROLES } from '@/constants/labels'
import { useResource } from '@/hooks/useResource'
import { clusterService } from '@/services/cluster.service'
import { userService } from '@/services/user.service'

const NO_USERS: User[] = []
const NO_CLUSTERS: Cluster[] = []

interface Draft {
  id: number | null
  username: string
  password: string
  full_name: string
  role: Role
  is_active: boolean
  cluster_ids: number[]
}

const EMPTY: Draft = {
  id: null,
  username: '',
  password: '',
  full_name: '',
  role: 'VIEWER',
  is_active: true,
  cluster_ids: [],
}

export default function UsersTab() {
  const users = useResource(userService.list, NO_USERS)
  const { data: clusters } = useResource(clusterService.list, NO_CLUSTERS)
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
      await users.reload()
      return true
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Operation failed')
      return false
    }
  }

  async function save(event: FormEvent) {
    event.preventDefault()
    if (!draft) return
    const { id, password, ...fields } = draft
    const input = { ...fields, ...(password ? { password } : {}) }
    const ok = await run(() =>
      id === null ? userService.create(input) : userService.update(id, input)
    )
    if (ok) setDraft(null)
  }

  const toggleCluster = (id: number) =>
    setDraft(
      (d) =>
        d && {
          ...d,
          cluster_ids: d.cluster_ids.includes(id)
            ? d.cluster_ids.filter((x) => x !== id)
            : [...d.cluster_ids, id],
        }
    )

  const filteredUsers = users.data.filter((u) =>
    u.full_name.toLowerCase().includes(search.toLowerCase()) ||
    u.username.toLowerCase().includes(search.toLowerCase()) ||
    ROLE_LABEL[u.role].toLowerCase().includes(search.toLowerCase())
  )

  const paginatedUsers = filteredUsers.slice((page - 1) * pageSize, page * pageSize)

  return (
    <div className="space-y-3">
      <ErrorText message={error ?? users.error} />

      {/* Table Container */}
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
              placeholder="Search users, usernames..."
              className="w-full rounded-lg border border-line bg-panel pl-8 pr-3 py-1 text-xs text-ink outline-none focus:border-brand"
            />
          </div>

          <Button variant="primary" size="sm" onClick={() => setDraft(EMPTY)} className="h-7 text-xs gap-1.5 font-semibold">
            <Plus size={13} /> Add User
          </Button>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="border-b border-line bg-panel2/60 font-semibold uppercase tracking-wider text-dim">
              <tr>
                <th className="px-4 py-2.5">User & Username</th>
                <th className="px-4 py-2.5">Role</th>
                <th className="px-4 py-2.5">Assigned Clusters</th>
                <th className="px-4 py-2.5">Status</th>
                <th className="px-4 py-2.5 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-line/60">
              {paginatedUsers.length === 0 && (
                <tr>
                  <td colSpan={5} className="py-8 text-center text-dim">
                    No users found.
                  </td>
                </tr>
              )}
              {paginatedUsers.map((u) => (
                <tr key={u.id} className="transition-colors hover:bg-panel2/30">
                  <td className="px-4 py-2.5 font-semibold text-ink">
                    <p>{u.full_name}</p>
                    <p className="font-mono text-[11px] text-dim">@{u.username}</p>
                  </td>
                  <td className="px-4 py-2.5">
                    <Badge
                      tone={
                        u.role === 'ADMIN'
                          ? 'danger'
                          : u.role === 'OPERATOR'
                            ? 'brand'
                            : 'neutral'
                      }
                      dot
                    >
                      {ROLE_LABEL[u.role]}
                    </Badge>
                  </td>
                  <td className="px-4 py-2.5 text-dim">
                    {u.role === 'ADMIN' ? (
                      <span className="font-semibold text-rose-500">All Clusters & Nodes</span>
                    ) : (
                      (u.cluster_ids ?? [])
                        .map((id) => clusters.find((c) => c.id === id)?.name)
                        .filter(Boolean)
                        .join(', ') || '—'
                    )}
                  </td>
                  <td className="px-4 py-2.5">
                    <Badge tone={u.is_active ? 'ok' : 'neutral'} dot>
                      {u.is_active ? 'Active' : 'Locked'}
                    </Badge>
                  </td>
                  <td className="px-4 py-2.5 text-right space-x-1">
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => setDraft({ ...u, cluster_ids: u.cluster_ids ?? [], password: '' })}
                      aria-label="Edit"
                      className="size-7 p-0"
                    >
                      <Pencil size={13} />
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() =>
                        window.confirm(`Delete user @${u.username}?`) &&
                        run(() => userService.remove(u.id))
                      }
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
          totalItems={filteredUsers.length}
          pageSize={pageSize}
          onPageChange={setPage}
          onPageSizeChange={(s) => {
            setPageSize(s)
            setPage(1)
          }}
        />
      </div>

      {draft && (
        <Modal
          title={draft.id === null ? 'Add New User' : `Edit User: @${draft.username}`}
          onClose={() => setDraft(null)}
        >
          <form onSubmit={save} className="space-y-4">
            <Input
              label="Username"
              value={draft.username}
              onChange={(e) => setDraft({ ...draft, username: e.target.value })}
              placeholder="e.g. operator_1"
              disabled={draft.id !== null}
              required
            />
            <Input
              label={draft.id === null ? 'Password' : 'New Password (leave empty to keep current)'}
              type="password"
              value={draft.password}
              onChange={(e) => setDraft({ ...draft, password: e.target.value })}
              placeholder="••••••••"
              required={draft.id === null}
            />
            <Input
              label="Full Name"
              value={draft.full_name}
              onChange={(e) => setDraft({ ...draft, full_name: e.target.value })}
              placeholder="e.g. John Doe"
              required
            />
            <Select
              label="System Role"
              value={draft.role}
              onChange={(e) => setDraft({ ...draft, role: e.target.value as Role })}
            >
              {ROLES.map((r) => (
                <option key={r} value={r}>
                  {ROLE_LABEL[r]}
                </option>
              ))}
            </Select>

            {draft.role !== 'ADMIN' && (
              <div>
                <span className="mb-1.5 block text-xs font-semibold text-dim">
                  Accessible Clusters
                </span>
                <div className="flex flex-wrap gap-1.5">
                  {clusters.map((c) => {
                    const selected = draft.cluster_ids.includes(c.id)
                    return (
                      <button
                        type="button"
                        key={c.id}
                        onClick={() => toggleCluster(c.id)}
                        className={`rounded px-2.5 py-1 text-xs font-semibold transition-all cursor-pointer ${
                          selected
                            ? 'bg-blue-600 text-white'
                            : 'bg-panel2 text-dim hover:text-ink border border-line'
                        }`}
                      >
                        {c.name}
                      </button>
                    )
                  })}
                </div>
              </div>
            )}

            <label className="flex items-center gap-2 text-xs font-semibold cursor-pointer select-none pt-1">
              <input
                type="checkbox"
                checked={draft.is_active}
                onChange={(e) => setDraft({ ...draft, is_active: e.target.checked })}
                className="size-4 rounded text-brand focus:ring-brand"
              />
              <span>Account is Active</span>
            </label>

            <Button type="submit" variant="primary" className="w-full h-8 text-xs mt-2">
              Save User
            </Button>
          </form>
        </Modal>
      )}
    </div>
  )
}
