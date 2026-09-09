import { useEffect, useState } from 'react'
import { Search, Database, Loader2 } from 'lucide-react'
import type { ModelArtifact } from '@/modules/ai/types'
import { aiService } from '@/shared/api/services/ai'
import EmptyState from '@/shared/components/EmptyState'

export default function ModelsPage() {
  const [search, setSearch] = useState('')
  const [models, setModels] = useState<ModelArtifact[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [loadError, setLoadError] = useState<string | null>(null)

  useEffect(() => {
    aiService.listModels()
      .then(setModels)
      .catch(() => setLoadError('Unable to load the model catalog from the registry. Check MODEL_REGISTRY__* on the server.'))
      .finally(() => setIsLoading(false))
  }, [])

  const filtered = models.filter((m) =>
    search === '' ||
    m.name.toLowerCase().includes(search.toLowerCase()) ||
    m.version.toLowerCase().includes(search.toLowerCase()) ||
    m.tags.some((t) => t.toLowerCase().includes(search.toLowerCase())),
  )

  return (
    <div className="av-page-layout">
      <div className="av-page-header">
        {/* Filter and Search */}
        <section className="av-panel" style={{ marginBottom: 0 }}>
          <div className="av-filter-row">
            <div className="av-search-box">
              <Search size={14} color="var(--text-faint)" />
              <input
                type="text"
                placeholder="Search by model name, tag, or class..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
              />
            </div>
          </div>
        </section>
      </div>

      {/* Models Grid */}
      <div className="av-page-content">
        {loadError && <EmptyState message={loadError} icon={<Database size={32} opacity={0.5} color="var(--critical)" />} />}
        {isLoading && !loadError && <EmptyState message="Loading models..." icon={<Loader2 size={32} opacity={0.5} className="spin" />} />}
        
        {!loadError && !isLoading && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(360px, 1fr))', gap: 16 }}>
          {filtered.length === 0 ? (
            <EmptyState message="No model images in the registry yet." />
          ) : (
          filtered.map((model) => (
          <div
            key={model.id}
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
                  {model.id}
                </span>
                <span
                  className={`av-status-pill ${
                    model.status === 'production' ? 'reviewed' : model.status === 'staging' ? 'new' : 'escalated'
                  }`}
                >
                  {model.status}
                </span>
              </div>
              <div style={{ display: 'flex', alignItems: 'baseline', gap: 8 }}>
                <h3 style={{ fontSize: 17, fontWeight: 800, margin: '4px 0 2px' }}>{model.name}</h3>
                <span className="av-mono" style={{ fontSize: 12, color: 'var(--text-faint)', fontWeight: 600 }}>
                  {model.version}
                </span>
              </div>
              <div style={{ fontSize: 12, color: 'var(--text-dim)', marginTop: 2 }}>
                {model.architecture}
              </div>
            </div>

            <div
              style={{
                background: 'var(--panel-2)',
                padding: '12px 14px',
                borderRadius: 'var(--radius-md)',
                border: '1px solid var(--border)',
                display: 'grid',
                gridTemplateColumns: '1fr 1fr',
                gap: 10,
                fontSize: 12}}
            >
              <div>
                <span style={{ color: 'var(--text-faint)', fontSize: 10, textTransform: 'uppercase' }}>Format</span>
                <div style={{ fontWeight: 700, marginTop: 2, color: 'var(--accent)' }}>{model.format}</div>
              </div>
              <div>
                <span style={{ color: 'var(--text-faint)', fontSize: 10, textTransform: 'uppercase' }}>Artifact Size</span>
                <div className="av-mono" style={{ fontWeight: 700, marginTop: 2 }}>{model.sizeMb} MB</div>
              </div>
              <div>
                <span style={{ color: 'var(--text-faint)', fontSize: 10, textTransform: 'uppercase' }}>Accuracy (mAP50)</span>
                <div className="av-mono" style={{ fontWeight: 700, color: 'var(--good)', marginTop: 2 }}>{model.mAP50}%</div>
              </div>
              <div>
                <span style={{ color: 'var(--text-faint)', fontSize: 10, textTransform: 'uppercase' }}>Latency Bench</span>
                <div className="av-mono" style={{ fontWeight: 700, marginTop: 2 }}>{model.latencyBenchmarkMs} ms</div>
              </div>
              <div style={{ gridColumn: '1 / -1' }}>
                <span style={{ color: 'var(--text-faint)', fontSize: 10, textTransform: 'uppercase' }}>Target Hardware</span>
                <div style={{ fontWeight: 600, marginTop: 2 }}>{model.targetHardware}</div>
              </div>
            </div>

            {/* Tags */}
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
              {model.tags.map((t) => (
                <span
                  key={t}
                  style={{
                    fontSize: 10.5,
                    fontWeight: 600,
                    padding: '3px 8px',
                    borderRadius: 4,
                    background: 'var(--panel-2)',
                    color: 'var(--text-dim)',
                    border: '1px solid var(--border)'}}
                >
                  #{t}
                </span>
              ))}
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: 'auto', paddingTop: 8 }}>
              <span style={{ fontSize: 11, color: 'var(--text-faint)' }}>Registered: {model.registeredAt}</span>
              <button className="av-btn-primary" style={{ padding: '6px 14px', fontSize: 12 }}>
                Deploy Version
              </button>
            </div>
          </div>
          )))}
        </div>
        )}
      </div>
    </div>
  )
}
