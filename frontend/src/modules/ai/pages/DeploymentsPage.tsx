import { useEffect, useState } from 'react'
import { Plus, RotateCcw, RotateCw } from 'lucide-react'
import { type Deployment } from '@/modules/ai/types'
import type { ModelArtifact } from '@/modules/ai/types'
import { aiService } from '@/shared/api/services/ai'

export default function DeploymentsPage() {
  const [deployments, setDeployments] = useState<Deployment[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [loadError, setLoadError] = useState<string | null>(null)
  const [showDeployModal, setShowDeployModal] = useState(false)
  const [models, setModels] = useState<ModelArtifact[]>([])
  const [selectedModel, setSelectedModel] = useState('')
  const [selectedVersion, setSelectedVersion] = useState('')
  const [selectedStrategy, setSelectedStrategy] = useState<'Rolling Update' | 'Canary (20%)' | 'Immediate'>('Rolling Update')
  const [actionNotice, setActionNotice] = useState<string | null>(null)

  useEffect(() => {
    aiService.listDeployments()
      .then(setDeployments)
      .catch(() => setLoadError('Unable to load deployments from the backend.'))
      .finally(() => setIsLoading(false))
  }, [])

  useEffect(() => {
    aiService.listModels().then((items) => {
      setModels(items)
      if (items[0]) {
        setSelectedModel(items[0].name)
        setSelectedVersion(items[0].version)
      }
    })
  }, [])

  function handleRollback(depId: string, version?: string) {
    setActionNotice(`Initiated automated rollback of ${depId} to ${version || 'previous stable build'}`)
    setDeployments((prev) =>
      prev.map((d) => (d.id === depId ? { ...d, status: 'Rolled Back', progressPct: 100 } : d))
    )
    setTimeout(() => setActionNotice(null), 3500)
  }

  function handleRetry(depId: string) {
    setActionNotice(`Retrying deployment ${depId}... Verifying edge node connection`)
    setDeployments((prev) =>
      prev.map((d) => (d.id === depId ? { ...d, status: 'In Progress', progressPct: 50 } : d))
    )
    setTimeout(() => setActionNotice(null), 3500)
  }

  function handleCreateDeploy(e: React.FormEvent) {
    e.preventDefault()
    const newDep: Deployment = {
      id: `DEP-${Math.floor(8400 + Math.random() * 100)}`,
      modelName: selectedModel,
      modelVersion: selectedVersion,
      targetDevices: ['EDGE-NX-01', 'EDGE-AGX-02'],
      strategy: selectedStrategy,
      status: 'In Progress',
      progressPct: 15,
      deployedBy: 'Hop Do (Lead Operations)',
      deployedAt: 'Just now',
      rollbackVersion: 'v2.0.0'}

    setDeployments([newDep, ...deployments])
    setShowDeployModal(false)
    setActionNotice(`Deployment ${newDep.id} queued for target nodes`)
    setTimeout(() => setActionNotice(null), 3500)
  }

  return (
    <div className="av-page-layout">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
        
        <button className="av-btn-primary" onClick={() => setShowDeployModal(true)}>
          <Plus size={15} />
          <span>Deploy Model Version</span>
        </button>
      </div>

      {actionNotice && (
        <div
          style={{
            padding: '10px 16px',
            borderRadius: 'var(--radius-md)',
            background: 'var(--accent-dim)',
            border: '1px solid var(--accent)',
            color: 'var(--accent)',
            fontSize: 13,
            fontWeight: 600,
            display: 'flex',
            alignItems: 'center',
            gap: 8,
            marginBottom: 16,
            animation: 'av-fade-in 0.2s ease'}}
        >
          <RotateCw size={15} className="av-dot pulse" />
          <span>{actionNotice}</span>
        </div>
      )}

      {/* Active Rollout Pipelines */}
      <div className="av-page-content" style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
        {loadError && <div className="av-panel">{loadError}</div>}
        {isLoading && <div className="av-panel">Loading deployments...</div>}
        {deployments.map((dep) => (
          <div
            key={dep.id}
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
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 10 }}>
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <span className="av-mono" style={{ fontSize: 12, fontWeight: 700, color: 'var(--accent)' }}>
                    {dep.id}
                  </span>
                  <span style={{ fontSize: 16, fontWeight: 800 }}>{dep.modelName}</span>
                  <span className="av-mono" style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-faint)' }}>
                    {dep.modelVersion}
                  </span>
                </div>
                <div style={{ fontSize: 12, color: 'var(--text-dim)', marginTop: 4 }}>
                  Target Nodes: <strong>{dep.targetDevices.join(', ')}</strong> • Strategy: <strong>{dep.strategy}</strong>
                </div>
              </div>

              <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                <span
                  className={`av-status-pill ${
                    dep.status === 'Active' ? 'reviewed' : dep.status === 'In Progress' ? 'new' : 'escalated'
                  }`}
                >
                  {dep.status}
                </span>

                {dep.status === 'Failed' && (
                  <button className="av-btn-secondary" style={{ padding: '6px 12px', fontSize: 12 }} onClick={() => handleRetry(dep.id)}>
                    <RotateCw size={13} />
                    <span>Retry Rollout</span>
                  </button>
                )}

                {dep.rollbackVersion && dep.status !== 'Rolled Back' && (
                  <button
                    className="av-btn-secondary danger"
                    style={{ padding: '6px 12px', fontSize: 12 }}
                    onClick={() => handleRollback(dep.id, dep.rollbackVersion)}
                  >
                    <RotateCcw size={13} />
                    <span>Rollback to {dep.rollbackVersion}</span>
                  </button>
                )}
              </div>
            </div>

            {/* Progress Bar */}
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12, fontWeight: 600, marginBottom: 4 }}>
                <span style={{ color: 'var(--text-dim)' }}>Agent Sync Progress</span>
                <span className="av-mono">{dep.progressPct}% Completed</span>
              </div>
              <div className="av-telemetry-bar-track" style={{ height: 8 }}>
                <div
                  className={`av-telemetry-bar-fill${dep.status === 'Failed' ? ' crit' : ''}`}
                  style={{ width: `${dep.progressPct}%` }}
                />
              </div>
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 11.5, color: 'var(--text-faint)', borderTop: '1px solid var(--border)', paddingTop: 10 }}>
              <span>Operator: {dep.deployedBy}</span>
              <span>Dispatched: {dep.deployedAt}</span>
            </div>
          </div>
        ))}
      </div>

      {/* New Deployment Modal */}
      {showDeployModal && (
        <div className="av-modal-backdrop" onClick={() => setShowDeployModal(false)}>
          <div className="av-incident-modal" onClick={(e) => e.stopPropagation()} style={{ maxWidth: 500 }}>
            <div style={{ padding: 18, borderBottom: '1px solid var(--border)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div style={{ fontSize: 16, fontWeight: 800 }}>Deploy Model Version to Agent</div>
              <button className="av-icon-btn" onClick={() => setShowDeployModal(false)} style={{ width: 30, height: 30 }}>✕</button>
            </div>
            <form onSubmit={handleCreateDeploy} style={{ padding: 20, display: 'flex', flexDirection: 'column', gap: 14 }}>
              <div>
                <label style={{ display: 'block', fontSize: 12, fontWeight: 700, marginBottom: 6 }}>Select Model Artifact</label>
                <select
                  value={selectedModel}
                  onChange={(e) => setSelectedModel(e.target.value)}
                  style={{ width: '100%', padding: '9px 12px', borderRadius: 8, border: '1px solid var(--border-strong)', background: 'var(--panel-2)', color: 'var(--text)', outline: 'none' }}
                >
                  {models.map((m) => (
                    <option key={m.id} value={m.name}>
                      {m.name} ({m.format})
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label style={{ display: 'block', fontSize: 12, fontWeight: 700, marginBottom: 6 }}>Model Version</label>
                <input
                  type="text"
                  value={selectedVersion}
                  onChange={(e) => setSelectedVersion(e.target.value)}
                  style={{ width: '100%', padding: '9px 12px', borderRadius: 8, border: '1px solid var(--border-strong)', background: 'var(--panel-2)', color: 'var(--text)', outline: 'none' }}
                />
              </div>

              <div>
                <label style={{ display: 'block', fontSize: 12, fontWeight: 700, marginBottom: 6 }}>Rollout Strategy</label>
                <select
                  value={selectedStrategy}
                  onChange={(e) => setSelectedStrategy(e.target.value as any)}
                  style={{ width: '100%', padding: '9px 12px', borderRadius: 8, border: '1px solid var(--border-strong)', background: 'var(--panel-2)', color: 'var(--text)', outline: 'none' }}
                >
                  <option value="Rolling Update">Rolling Update (Zero Downtime)</option>
                  <option value="Canary (20%)">Canary (20% Agent Testing)</option>
                  <option value="Immediate">Immediate Flash Rollout</option>
                </select>
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10, marginTop: 10 }}>
                <button type="button" className="av-btn-secondary" onClick={() => setShowDeployModal(false)}>Cancel</button>
                <button type="submit" className="av-btn-primary">Initiate Rollout</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
