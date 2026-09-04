import { useState } from 'react'
import { Plus, MapPin, Camera, AlertTriangle, Activity, CheckCircle2, Layers } from 'lucide-react'
import { mockCameraGroups, type CameraGroup } from '@/modules/fleet/mock/fleet'

export default function CameraGroupsPage() {
  const [groups, setGroups] = useState<CameraGroup[]>(mockCameraGroups)
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [newGroupName, setNewGroupName] = useState('')
  const [newGroupSite, setNewGroupSite] = useState('')

  function handleCreateGroup(e: React.FormEvent) {
    e.preventDefault()
    if (!newGroupName.trim()) return

    const newGroup: CameraGroup = {
      id: `GRP-0${groups.length + 1}`,
      name: newGroupName,
      description: 'Custom monitored zone created by operator',
      site: newGroupSite || 'Main Facility',
      cameraIds: ['CAM-01'],
      totalCameras: 1,
      onlineCameras: 1,
      activeAlerts: 0,
      aggregateFps: 30,
      primaryModel: 'YOLOv11-Enterprise'}

    setGroups([...groups, newGroup])
    setNewGroupName('')
    setNewGroupSite('')
    setShowCreateModal(false)
  }

  return (
    <div className="av-page-layout">
      <div className="av-page-header">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        
        <button className="av-btn-primary" onClick={() => setShowCreateModal(true)}>
          <Plus size={15} />
          <span>New Camera Group</span>
        </button>
        </div>
      </div>

      <div className="av-page-content">
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(340px, 1fr))', gap: 16 }}>
        {groups.map((grp) => (
          <div
            key={grp.id}
            style={{
              background: 'var(--panel)',
              border: '1px solid var(--border)',
              borderRadius: 'var(--radius-lg)',
              padding: 20,
              boxShadow: 'none',
              display: 'flex',
              flexDirection: 'column',
              gap: 14}}
          >
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 4 }}>
                <span className="av-mono" style={{ fontSize: 11, fontWeight: 700, color: 'var(--accent)' }}>
                  {grp.id}
                </span>
                <span
                  className={`av-status-pill ${
                    grp.onlineCameras === grp.totalCameras ? 'reviewed' : grp.onlineCameras > 0 ? 'new' : 'escalated'
                  }`}
                >
                  {grp.onlineCameras} / {grp.totalCameras} Online
                </span>
              </div>
              <h3 style={{ fontSize: 16, fontWeight: 800, margin: '4px 0 6px' }}>{grp.name}</h3>
              <p style={{ fontSize: 12, color: 'var(--text-dim)', margin: 0, lineHeight: 1.5 }}>
                {grp.description}
              </p>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 12, color: 'var(--text-faint)' }}>
              <MapPin size={13} color="var(--accent)" />
              <span>{grp.site}</span>
            </div>

            <div
              style={{
                background: 'var(--panel-2)',
                padding: '12px 14px',
                borderRadius: 'var(--radius-md)',
                border: '1px solid var(--border)',
                display: 'grid',
                gridTemplateColumns: '1fr 1fr',
                gap: 8,
                fontSize: 12}}
            >
              <div>
                <span style={{ color: 'var(--text-faint)', fontSize: 10, textTransform: 'uppercase' }}>Cameras</span>
                <div style={{ fontWeight: 700, marginTop: 2, display: 'flex', alignItems: 'center', gap: 4 }}>
                  <Camera size={13} />
                  <span>{grp.cameraIds.join(', ')}</span>
                </div>
              </div>

              <div>
                <span style={{ color: 'var(--text-faint)', fontSize: 10, textTransform: 'uppercase' }}>Throughput</span>
                <div className="av-mono" style={{ fontWeight: 700, marginTop: 2, display: 'flex', alignItems: 'center', gap: 4 }}>
                  <Activity size={13} color="var(--good)" />
                  <span>{grp.aggregateFps} FPS</span>
                </div>
              </div>

              <div style={{ gridColumn: '1 / -1' }}>
                <span style={{ color: 'var(--text-faint)', fontSize: 10, textTransform: 'uppercase' }}>Primary Inference Model</span>
                <div style={{ fontWeight: 700, color: 'var(--accent)', marginTop: 2, display: 'flex', alignItems: 'center', gap: 4 }}>
                  <Layers size={13} />
                  <span>{grp.primaryModel}</span>
                </div>
              </div>
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: 'auto', paddingTop: 8 }}>
              {grp.activeAlerts > 0 ? (
                <span className="av-alert-pill has-alerts" style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                  <AlertTriangle size={12} />
                  <span>{grp.activeAlerts} Active Alerts</span>
                </span>
              ) : (
                <span style={{ fontSize: 12, color: 'var(--good)', fontWeight: 600, display: 'flex', alignItems: 'center', gap: 4 }}>
                  <CheckCircle2 size={13} />
                  <span>Normal Operations</span>
                </span>
              )}

              <button className="av-btn-secondary" style={{ padding: '6px 12px', fontSize: 12 }}>
                Configure Group
              </button>
            </div>
          </div>
          ))}
        </div>
      </div>

      {/* Create Camera Group Modal */}
      {showCreateModal && (
        <div className="av-modal-backdrop" onClick={() => setShowCreateModal(false)}>
          <div className="av-incident-modal" onClick={(e) => e.stopPropagation()} style={{ maxWidth: 480 }}>
            <div style={{ padding: 18, borderBottom: '1px solid var(--border)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div style={{ fontSize: 16, fontWeight: 800 }}>Create New Camera Group</div>
              <button className="av-icon-btn" onClick={() => setShowCreateModal(false)} style={{ width: 30, height: 30 }}>✕</button>
            </div>
            <form onSubmit={handleCreateGroup} style={{ padding: 20, display: 'flex', flexDirection: 'column', gap: 14 }}>
              <div>
                <label style={{ display: 'block', fontSize: 12, fontWeight: 700, marginBottom: 6 }}>Group Name</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Loading Dock North"
                  value={newGroupName}
                  onChange={(e) => setNewGroupName(e.target.value)}
                  style={{ width: '100%', padding: '9px 12px', borderRadius: 8, border: '1px solid var(--border-strong)', background: 'var(--panel-2)', color: 'var(--text)', outline: 'none' }}
                />
              </div>
              <div>
                <label style={{ display: 'block', fontSize: 12, fontWeight: 700, marginBottom: 6 }}>Facility Site / Project</label>
                <input
                  type="text"
                  placeholder="e.g. Warehouse 3B"
                  value={newGroupSite}
                  onChange={(e) => setNewGroupSite(e.target.value)}
                  style={{ width: '100%', padding: '9px 12px', borderRadius: 8, border: '1px solid var(--border-strong)', background: 'var(--panel-2)', color: 'var(--text)', outline: 'none' }}
                />
              </div>
              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10, marginTop: 10 }}>
                <button type="button" className="av-btn-secondary" onClick={() => setShowCreateModal(false)}>Cancel</button>
                <button type="submit" className="av-btn-primary">Create Group</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
