import { useState } from 'react'
import { Plus, Check, X as XIcon, Search } from 'lucide-react'
import { mockUsers, type UserAccount, type SystemRole } from '@/modules/system/mock/system'

const ROLES_MATRIX: { permission: string; admin: boolean; mlops: boolean; operator: boolean; auditor: boolean; viewer: boolean }[] = [
  { permission: 'Deploy AI Models to Edge Fleet', admin: true, mlops: true, operator: false, auditor: false, viewer: false },
  { permission: 'Trigger Hardware Reboot & Reset', admin: true, mlops: true, operator: true, auditor: false, viewer: false },
  { permission: 'Modify AI Confidence & IoU Thresholds', admin: true, mlops: true, operator: false, auditor: false, viewer: false },
  { permission: 'Acknowledge & Triage Safety Incidents', admin: true, mlops: false, operator: true, auditor: true, viewer: false },
  { permission: 'View Real-time RTSP & WebRTC Feeds', admin: true, mlops: true, operator: true, auditor: true, viewer: true },
  { permission: 'Export System Audit & Compliance Logs', admin: true, mlops: false, operator: false, auditor: true, viewer: false },
]

export default function UsersPage() {
  const [users, setUsers] = useState<UserAccount[]>(mockUsers)
  const [search, setSearch] = useState('')
  const [roleFilter, setRoleFilter] = useState('all')
  const [showInviteModal, setShowInviteModal] = useState(false)
  const [newUserName, setNewUserName] = useState('')
  const [newUserEmail, setNewUserEmail] = useState('')
  const [newUserRole, setNewUserRole] = useState<SystemRole>('Edge Operator')

  const filtered = users.filter((u) => {
    const matchSearch =
      search === '' ||
      u.name.toLowerCase().includes(search.toLowerCase()) ||
      u.email.toLowerCase().includes(search.toLowerCase())

    const matchRole = roleFilter === 'all' || u.role === roleFilter
    return matchSearch && matchRole
  })

  function handleInvite(e: React.FormEvent) {
    e.preventDefault()
    if (!newUserName.trim() || !newUserEmail.trim()) return

    const newUser: UserAccount = {
      id: `USR-0${users.length + 1}`,
      name: newUserName,
      email: newUserEmail,
      role: newUserRole,
      status: 'invited',
      lastActive: 'Never',
      avatarInitials: newUserName.split(' ').map((n) => n[0]).join('').slice(0, 2).toUpperCase(),
      assignedSites: ['Plant A']}

    setUsers([...users, newUser])
    setNewUserName('')
    setNewUserEmail('')
    setShowInviteModal(false)
  }

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
        
        <button className="av-btn-primary" onClick={() => setShowInviteModal(true)}>
          <Plus size={15} />
          <span>Invite Team Member</span>
        </button>
      </div>

      {/* Filter and Search */}
      <section className="av-panel" style={{ marginBottom: 18 }}>
        <div className="av-filter-row">
          <div className="av-search-box">
            <Search size={14} color="var(--text-faint)" />
            <input
              type="text"
              placeholder="Search users by name or email address..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>

          <select value={roleFilter} onChange={(e) => setRoleFilter(e.target.value)}>
            <option value="all">All Roles</option>
            <option value="Admin">Admin</option>
            <option value="MLOps Engineer">MLOps Engineer</option>
            <option value="Edge Operator">Edge Operator</option>
            <option value="Safety Auditor">Safety Auditor</option>
            <option value="Viewer">Viewer</option>
          </select>
        </div>

        {/* Users Table */}
        <div className="av-table-wrap">
          <table className="av-table">
            <thead>
              <tr>
                <th>User</th>
                <th>Role</th>
                <th>Assigned Facilities</th>
                <th>Account Status</th>
                <th>Last Active</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((user) => (
                <tr key={user.id}>
                  <td>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                      <div className="av-avatar">{user.avatarInitials}</div>
                      <div>
                        <div style={{ fontWeight: 700 }}>{user.name}</div>
                        <div style={{ fontSize: 11, color: 'var(--text-faint)' }}>{user.email}</div>
                      </div>
                    </div>
                  </td>
                  <td>
                    <span
                      style={{
                        fontSize: 11,
                        fontWeight: 700,
                        padding: '3px 8px',
                        borderRadius: 4,
                        background: 'var(--panel-2)',
                        border: '1px solid var(--border)',
                        color: user.role === 'Admin' ? 'var(--accent)' : 'var(--text)'}}
                    >
                      {user.role}
                    </span>
                  </td>
                  <td>{user.assignedSites.join(', ')}</td>
                  <td>
                    <span
                      className={`av-status-pill ${
                        user.status === 'active' ? 'reviewed' : user.status === 'invited' ? 'new' : 'escalated'
                      }`}
                    >
                      {user.status.toUpperCase()}
                    </span>
                  </td>
                  <td className="av-mono">{user.lastActive}</td>
                  <td>
                    <button className="av-btn-secondary" style={{ padding: '4px 10px', fontSize: 11 }}>
                      Edit Role
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* RBAC Permissions Matrix */}
      

      <section className="av-panel">
        <div className="av-table-wrap">
          <table className="av-table">
            <thead>
              <tr>
                <th>Capability / Action</th>
                <th style={{ textAlign: 'center' }}>Admin</th>
                <th style={{ textAlign: 'center' }}>MLOps</th>
                <th style={{ textAlign: 'center' }}>Operator</th>
                <th style={{ textAlign: 'center' }}>Auditor</th>
                <th style={{ textAlign: 'center' }}>Viewer</th>
              </tr>
            </thead>
            <tbody>
              {ROLES_MATRIX.map((row, idx) => (
                <tr key={idx}>
                  <td style={{ fontWeight: 600 }}>{row.permission}</td>
                  <td style={{ textAlign: 'center' }}>{row.admin ? <Check size={16} color="var(--good)" /> : <XIcon size={14} color="var(--text-faint)" />}</td>
                  <td style={{ textAlign: 'center' }}>{row.mlops ? <Check size={16} color="var(--good)" /> : <XIcon size={14} color="var(--text-faint)" />}</td>
                  <td style={{ textAlign: 'center' }}>{row.operator ? <Check size={16} color="var(--good)" /> : <XIcon size={14} color="var(--text-faint)" />}</td>
                  <td style={{ textAlign: 'center' }}>{row.auditor ? <Check size={16} color="var(--good)" /> : <XIcon size={14} color="var(--text-faint)" />}</td>
                  <td style={{ textAlign: 'center' }}>{row.viewer ? <Check size={16} color="var(--good)" /> : <XIcon size={14} color="var(--text-faint)" />}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* Invite User Modal */}
      {showInviteModal && (
        <div className="av-modal-backdrop" onClick={() => setShowInviteModal(false)}>
          <div className="av-incident-modal" onClick={(e) => e.stopPropagation()} style={{ maxWidth: 480 }}>
            <div style={{ padding: 18, borderBottom: '1px solid var(--border)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div style={{ fontSize: 16, fontWeight: 800 }}>Invite Team Member</div>
              <button className="av-icon-btn" onClick={() => setShowInviteModal(false)} style={{ width: 30, height: 30 }}>✕</button>
            </div>
            <form onSubmit={handleInvite} style={{ padding: 20, display: 'flex', flexDirection: 'column', gap: 14 }}>
              <div>
                <label style={{ display: 'block', fontSize: 12, fontWeight: 700, marginBottom: 6 }}>Full Name</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Rachel Adams"
                  value={newUserName}
                  onChange={(e) => setNewUserName(e.target.value)}
                  style={{ width: '100%', padding: '9px 12px', borderRadius: 8, border: '1px solid var(--border-strong)', background: 'var(--panel-2)', color: 'var(--text)', outline: 'none' }}
                />
              </div>

              <div>
                <label style={{ display: 'block', fontSize: 12, fontWeight: 700, marginBottom: 6 }}>Email Address</label>
                <input
                  type="email"
                  required
                  placeholder="name@company.io"
                  value={newUserEmail}
                  onChange={(e) => setNewUserEmail(e.target.value)}
                  style={{ width: '100%', padding: '9px 12px', borderRadius: 8, border: '1px solid var(--border-strong)', background: 'var(--panel-2)', color: 'var(--text)', outline: 'none' }}
                />
              </div>

              <div>
                <label style={{ display: 'block', fontSize: 12, fontWeight: 700, marginBottom: 6 }}>Select Role</label>
                <select
                  value={newUserRole}
                  onChange={(e) => setNewUserRole(e.target.value as SystemRole)}
                  style={{ width: '100%', padding: '9px 12px', borderRadius: 8, border: '1px solid var(--border-strong)', background: 'var(--panel-2)', color: 'var(--text)', outline: 'none' }}
                >
                  <option value="Edge Operator">Edge Operator</option>
                  <option value="MLOps Engineer">MLOps Engineer</option>
                  <option value="Safety Auditor">Safety Auditor</option>
                  <option value="Viewer">Viewer</option>
                  <option value="Admin">Admin</option>
                </select>
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10, marginTop: 10 }}>
                <button type="button" className="av-btn-secondary" onClick={() => setShowInviteModal(false)}>Cancel</button>
                <button type="submit" className="av-btn-primary">Send Invitation</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
