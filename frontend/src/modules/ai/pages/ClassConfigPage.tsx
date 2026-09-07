import { useState, useMemo } from 'react'
import {
  Plus,
  Search,
  Tag,
  Sliders,
  Trash2,
  Eye,
  EyeOff,
  Copy,
  Save,
  ChevronDown,
  Circle,
  AlertTriangle,
  Check,
  X,
} from 'lucide-react'
import {
  DEFAULT_COLORS,
  type ClassProfile,
  type PredictionClass,
  type ClassCategory,
} from '@/modules/ai/types'

const CATEGORY_COLORS: Record<ClassCategory, string> = {
  PPE: '#06b6d4',
  Vehicle: '#f59e0b',
  Person: '#3b82f6',
  Hazard: '#ef4444',
  Object: '#8b5cf6',
  Custom: '#94a3b8',
}

const CATEGORIES: ClassCategory[] = ['PPE', 'Vehicle', 'Person', 'Hazard', 'Object', 'Custom']

function formatCount(n: number) {
  if (n >= 1000000) return (n / 1000000).toFixed(1) + 'M'
  if (n >= 1000) return (n / 1000).toFixed(1) + 'K'
  return n.toString()
}

function formatTime(iso: string | null) {
  if (!iso) return '—'
  const d = new Date(iso)
  const diff = Date.now() - d.getTime()
  const mins = Math.floor(diff / 60000)
  if (mins < 60) return `${mins}m ago`
  const hrs = Math.floor(mins / 60)
  if (hrs < 24) return `${hrs}h ago`
  return d.toLocaleDateString()
}

/* ──────────────── CLASS ROW ──────────────── */
interface ClassRowProps {
  cls: PredictionClass
  onChange: (updated: PredictionClass) => void
  onDelete: (id: number) => void
  editingId: number | null
  setEditingId: (id: number | null) => void
}

function ClassRow({ cls, onChange, onDelete, editingId, setEditingId }: ClassRowProps) {
  const isEditing = editingId === cls.id
  const [draft, setDraft] = useState<PredictionClass>(cls)

  function startEdit() {
    setDraft(cls)
    setEditingId(cls.id)
  }
  function cancelEdit() {
    setDraft(cls)
    setEditingId(null)
  }
  function saveEdit() {
    onChange(draft)
    setEditingId(null)
  }

  return (
    <div
      style={{
        background: isEditing ? 'var(--accent-dim)' : 'var(--panel)',
        border: `1px solid ${isEditing ? 'var(--accent)' : 'var(--border)'}`,
        borderRadius: 'var(--radius-md)',
        padding: '12px 16px',
        display: 'flex',
        flexDirection: 'column',
        gap: 10,
        transition: 'all 0.15s ease',
      }}
    >
      {/* Row header */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap' }}>
        {/* Color dot + toggle */}
        <button
          title={cls.enabled ? 'Disable class' : 'Enable class'}
          onClick={() => onChange({ ...cls, enabled: !cls.enabled })}
          style={{
            background: 'none',
            border: 'none',
            cursor: 'pointer',
            padding: 0,
            display: 'flex',
            alignItems: 'center',
          }}
        >
          <Circle
            size={14}
            fill={cls.enabled ? cls.color : 'transparent'}
            stroke={cls.enabled ? cls.color : 'var(--text-faint)'}
            strokeWidth={2}
          />
        </button>

        {/* Class ID badge */}
        <span
          className="av-mono"
          style={{
            fontSize: 11,
            fontWeight: 700,
            background: 'var(--surface)',
            border: '1px solid var(--border)',
            borderRadius: 4,
            padding: '1px 7px',
            color: 'var(--text-faint)',
            minWidth: 34,
            textAlign: 'center',
          }}
        >
          #{cls.id}
        </span>

        {/* Label */}
        {isEditing ? (
          <input
            value={draft.label}
            onChange={(e) => setDraft({ ...draft, label: e.target.value })}
            style={{
              fontSize: 13,
              fontWeight: 700,
              background: 'var(--surface)',
              border: '1px solid var(--accent)',
              borderRadius: 6,
              padding: '3px 8px',
              color: 'var(--text)',
              width: 160,
            }}
          />
        ) : (
          <span className="av-mono" style={{ fontSize: 13, fontWeight: 700, color: 'var(--text)' }}>
            {cls.label}
          </span>
        )}

        {/* Category chip */}
        {isEditing ? (
          <select
            value={draft.category}
            onChange={(e) => setDraft({ ...draft, category: e.target.value as ClassCategory })}
            style={{ fontSize: 11, padding: '2px 6px', borderRadius: 6 }}
          >
            {CATEGORIES.map((c) => (
              <option key={c} value={c}>{c}</option>
            ))}
          </select>
        ) : (
          <span
            style={{
              fontSize: 11,
              fontWeight: 600,
              padding: '2px 8px',
              borderRadius: 10,
              background: CATEGORY_COLORS[cls.category] + '22',
              color: CATEGORY_COLORS[cls.category],
              border: `1px solid ${CATEGORY_COLORS[cls.category]}55`,
            }}
          >
            {cls.category}
          </span>
        )}

        {/* Enabled / Disabled badge */}
        {!cls.enabled && (
          <span style={{ fontSize: 11, color: 'var(--text-faint)', fontStyle: 'italic' }}>
            disabled
          </span>
        )}

        {/* Hazard warning */}
        {cls.category === 'Hazard' && cls.enabled && (
          <AlertTriangle size={13} color="#ef4444" aria-label="Hazard class triggers alerts" />
        )}

        {/* Detection count */}
        <span style={{ marginLeft: 'auto', fontSize: 12, color: 'var(--text-dim)' }}>
          {formatCount(cls.detectionCount)} detections
        </span>
        <span style={{ fontSize: 11, color: 'var(--text-faint)' }}>
          {formatTime(cls.lastDetected)}
        </span>

        {/* Actions */}
        <div style={{ display: 'flex', gap: 6 }}>
          {isEditing ? (
            <>
              <button
                className="av-btn-primary"
                onClick={saveEdit}
                style={{ padding: '3px 10px', fontSize: 12 }}
              >
                <Check size={12} /> Save
              </button>
              <button
                className="av-btn-secondary"
                onClick={cancelEdit}
                style={{ padding: '3px 8px', fontSize: 12 }}
              >
                <X size={12} />
              </button>
            </>
          ) : (
            <>
              <button
                className="av-btn-secondary"
                onClick={startEdit}
                style={{ padding: '3px 8px', fontSize: 12 }}
                title="Edit class"
              >
                <Sliders size={12} />
              </button>
              <button
                className="av-btn-secondary"
                onClick={() => onDelete(cls.id)}
                style={{ padding: '3px 8px', fontSize: 12, color: '#ef4444' }}
                title="Remove class"
              >
                <Trash2 size={12} />
              </button>
            </>
          )}
        </div>
      </div>

      {/* Edit form: color, confidence, description */}
      {isEditing && (
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'auto 1fr auto 1fr',
            gap: '8px 16px',
            alignItems: 'center',
            fontSize: 12,
          }}
        >
          {/* Color */}
          <span style={{ color: 'var(--text-dim)', fontWeight: 600 }}>Color</span>
          <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
            {DEFAULT_COLORS.map((c) => (
              <button
                key={c}
                onClick={() => setDraft({ ...draft, color: c })}
                style={{
                  width: 18,
                  height: 18,
                  borderRadius: '50%',
                  background: c,
                  border: draft.color === c ? '2px solid var(--text)' : '2px solid transparent',
                  cursor: 'pointer',
                  padding: 0,
                }}
              />
            ))}
          </div>

          {/* Confidence threshold */}
          <span style={{ color: 'var(--text-dim)', fontWeight: 600, whiteSpace: 'nowrap' }}>
            Confidence
          </span>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <input
              type="range"
              min={0.1}
              max={0.99}
              step={0.01}
              value={draft.confidenceThreshold}
              onChange={(e) =>
                setDraft({ ...draft, confidenceThreshold: parseFloat(e.target.value) })
              }
              style={{ flex: 1, accentColor: 'var(--accent)' }}
            />
            <span
              className="av-mono"
              style={{
                fontSize: 13,
                fontWeight: 700,
                color: 'var(--accent)',
                minWidth: 38,
                textAlign: 'right',
              }}
            >
              {(draft.confidenceThreshold * 100).toFixed(0)}%
            </span>
          </div>

          {/* Description */}
          <span style={{ color: 'var(--text-dim)', fontWeight: 600 }}>Description</span>
          <input
            value={draft.description}
            onChange={(e) => setDraft({ ...draft, description: e.target.value })}
            style={{
              gridColumn: '2 / 5',
              fontSize: 12,
              background: 'var(--surface)',
              border: '1px solid var(--border)',
              borderRadius: 6,
              padding: '4px 10px',
              color: 'var(--text)',
            }}
          />
        </div>
      )}

      {/* Confidence bar (view mode) */}
      {!isEditing && (
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <span style={{ fontSize: 11, color: 'var(--text-faint)', minWidth: 68 }}>
            Confidence
          </span>
          <div
            style={{
              flex: 1,
              height: 4,
              background: 'var(--border)',
              borderRadius: 2,
              overflow: 'hidden',
            }}
          >
            <div
              style={{
                width: `${cls.confidenceThreshold * 100}%`,
                height: '100%',
                background: cls.enabled ? cls.color : 'var(--text-faint)',
                borderRadius: 2,
                transition: 'width 0.3s ease',
              }}
            />
          </div>
          <span
            className="av-mono"
            style={{ fontSize: 12, fontWeight: 700, color: cls.enabled ? cls.color : 'var(--text-faint)', minWidth: 36 }}
          >
            {(cls.confidenceThreshold * 100).toFixed(0)}%
          </span>
          {cls.description && (
            <span style={{ fontSize: 11, color: 'var(--text-faint)', flex: '0 0 auto', maxWidth: 300, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
              {cls.description}
            </span>
          )}
        </div>
      )}
    </div>
  )
}

/* ──────────────── ADD CLASS MODAL ──────────────── */
interface AddClassModalProps {
  nextId: number
  onAdd: (cls: PredictionClass) => void
  onClose: () => void
}

function AddClassModal({ nextId, onAdd, onClose }: AddClassModalProps) {
  const [draft, setDraft] = useState<PredictionClass>({
    id: nextId,
    label: '',
    category: 'Custom',
    color: DEFAULT_COLORS[nextId % DEFAULT_COLORS.length],
    confidenceThreshold: 0.5,
    enabled: true,
    detectionCount: 0,
    lastDetected: null,
    description: '',
  })

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!draft.label.trim()) return
    onAdd({ ...draft, label: draft.label.trim().toLowerCase().replace(/\s+/g, '_') })
    onClose()
  }

  return (
    <div className="av-modal-backdrop" onClick={onClose}>
      <div className="av-modal" onClick={(e) => e.stopPropagation()}>
        <div className="av-modal-header">
          <h3 style={{ margin: 0, fontSize: 15, fontWeight: 700 }}>Add Prediction Class</h3>
          <button className="av-btn-icon" onClick={onClose}><X size={16} /></button>
        </div>
        <form onSubmit={handleSubmit} className="av-modal-body" style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
          {/* Class ID */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <label style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-dim)', minWidth: 110 }}>Class ID</label>
            <span className="av-mono" style={{ fontSize: 13, fontWeight: 700 }}>#{draft.id}</span>
          </div>

          {/* Label */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <label style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-dim)', minWidth: 110 }}>Label *</label>
            <input
              required
              placeholder="e.g. safety_boots"
              value={draft.label}
              onChange={(e) => setDraft({ ...draft, label: e.target.value })}
              style={{ flex: 1, fontSize: 13 }}
            />
          </div>

          {/* Category */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <label style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-dim)', minWidth: 110 }}>Category</label>
            <select
              value={draft.category}
              onChange={(e) => setDraft({ ...draft, category: e.target.value as ClassCategory })}
              style={{ flex: 1 }}
            >
              {CATEGORIES.map((c) => <option key={c} value={c}>{c}</option>)}
            </select>
          </div>

          {/* Color */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <label style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-dim)', minWidth: 110 }}>Color</label>
            <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
              {DEFAULT_COLORS.map((c) => (
                <button
                  key={c}
                  type="button"
                  onClick={() => setDraft({ ...draft, color: c })}
                  style={{
                    width: 20,
                    height: 20,
                    borderRadius: '50%',
                    background: c,
                    border: draft.color === c ? '2px solid var(--text)' : '2px solid transparent',
                    cursor: 'pointer',
                    padding: 0,
                  }}
                />
              ))}
            </div>
          </div>

          {/* Confidence */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <label style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-dim)', minWidth: 110 }}>
              Confidence Threshold
            </label>
            <input
              type="range"
              min={0.1}
              max={0.99}
              step={0.01}
              value={draft.confidenceThreshold}
              onChange={(e) => setDraft({ ...draft, confidenceThreshold: parseFloat(e.target.value) })}
              style={{ flex: 1, accentColor: 'var(--accent)' }}
            />
            <span className="av-mono" style={{ fontWeight: 700, color: 'var(--accent)', minWidth: 38 }}>
              {(draft.confidenceThreshold * 100).toFixed(0)}%
            </span>
          </div>

          {/* Description */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <label style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-dim)', minWidth: 110 }}>Description</label>
            <input
              placeholder="Optional description..."
              value={draft.description}
              onChange={(e) => setDraft({ ...draft, description: e.target.value })}
              style={{ flex: 1, fontSize: 12 }}
            />
          </div>

          <div className="av-modal-footer" style={{ marginTop: 6 }}>
            <button type="button" className="av-btn-secondary" onClick={onClose}>Cancel</button>
            <button type="submit" className="av-btn-primary">
              <Plus size={14} /> Add Class
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

/* ──────────────── MAIN PAGE ──────────────── */
export default function ClassConfigPage() {
  const [profiles, setProfiles] = useState<ClassProfile[]>([])
  const [activeProfileId, setActiveProfileId] = useState('')
  const [search, setSearch] = useState('')
  const [filterCategory, setFilterCategory] = useState<ClassCategory | 'all'>('all')
  const [filterEnabled, setFilterEnabled] = useState<'all' | 'enabled' | 'disabled'>('all')
  const [editingId, setEditingId] = useState<number | null>(null)
  const [showAddModal, setShowAddModal] = useState(false)
  const [savedNotice, setSavedNotice] = useState(false)
  const [profileDropdown, setProfileDropdown] = useState(false)

  const activeProfile = profiles.find((p) => p.id === activeProfileId)!

  const filteredClasses = useMemo(() => {
    return activeProfile.classes.filter((c) => {
      const matchSearch =
        search === '' ||
        c.label.includes(search.toLowerCase()) ||
        c.description.toLowerCase().includes(search.toLowerCase()) ||
        String(c.id) === search
      const matchCategory = filterCategory === 'all' || c.category === filterCategory
      const matchEnabled =
        filterEnabled === 'all' ||
        (filterEnabled === 'enabled' && c.enabled) ||
        (filterEnabled === 'disabled' && !c.enabled)
      return matchSearch && matchCategory && matchEnabled
    })
  }, [activeProfile.classes, search, filterCategory, filterEnabled])

  function updateClass(updated: PredictionClass) {
    setProfiles((prev) =>
      prev.map((p) =>
        p.id === activeProfileId
          ? { ...p, classes: p.classes.map((c) => (c.id === updated.id ? updated : c)) }
          : p,
      ),
    )
  }

  function deleteClass(id: number) {
    setProfiles((prev) =>
      prev.map((p) =>
        p.id === activeProfileId
          ? { ...p, classes: p.classes.filter((c) => c.id !== id) }
          : p,
      ),
    )
  }

  function addClass(cls: PredictionClass) {
    setProfiles((prev) =>
      prev.map((p) =>
        p.id === activeProfileId
          ? { ...p, classes: [...p.classes, cls] }
          : p,
      ),
    )
  }

  function toggleAll(enabled: boolean) {
    setProfiles((prev) =>
      prev.map((p) =>
        p.id === activeProfileId
          ? { ...p, classes: p.classes.map((c) => ({ ...c, enabled })) }
          : p,
      ),
    )
  }

  function handleSave() {
    setSavedNotice(true)
    setTimeout(() => setSavedNotice(false), 2500)
  }

  const enabledCount = activeProfile.classes.filter((c) => c.enabled).length
  const totalCount = activeProfile.classes.length
  const nextId = Math.max(...activeProfile.classes.map((c) => c.id), -1) + 1

  return (
    <div className="av-page-layout">

      {/* Page header */}
      <div className="av-page-header" style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 12 }}>
        <div>
          <h2 style={{ margin: 0, fontSize: 18, fontWeight: 800 }}>Prediction Class Config</h2>
          <p style={{ margin: '4px 0 0', fontSize: 13, color: 'var(--text-dim)' }}>
            Manage detection labels, confidence thresholds and enable/disable classes per model profile.
          </p>
        </div>
        <div style={{ display: 'flex', gap: 8 }}>
          <button className="av-btn-secondary" onClick={() => setShowAddModal(true)}>
            <Plus size={14} /> Add Class
          </button>
          <button className="av-btn-primary" onClick={handleSave}>
            {savedNotice ? <><Check size={14} /> Saved</> : <><Save size={14} /> Save Profile</>}
          </button>
        </div>
      </div>

      {/* Profile selector */}
      <section className="av-panel" style={{ padding: '12px 16px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12, flexWrap: 'wrap' }}>
          <Tag size={14} color="var(--accent)" />
          <span style={{ fontSize: 12, fontWeight: 700, color: 'var(--text-dim)', letterSpacing: '0.06em' }}>
            ACTIVE PROFILE
          </span>

          <div style={{ position: 'relative' }}>
            <button
              className="av-btn-secondary"
              onClick={() => setProfileDropdown((v) => !v)}
              style={{ display: 'flex', alignItems: 'center', gap: 8, minWidth: 260 }}
            >
              <span style={{ fontWeight: 700, fontSize: 13, flex: 1, textAlign: 'left' }}>
                {activeProfile.name}
              </span>
              <ChevronDown size={13} />
            </button>
            {profileDropdown && (
              <div
                style={{
                  position: 'absolute',
                  top: '100%',
                  left: 0,
                  zIndex: 100,
                  background: 'var(--panel)',
                  border: '1px solid var(--border)',
                  borderRadius: 'var(--radius-md)',
                  boxShadow: '0 8px 24px rgba(0,0,0,0.15)',
                  minWidth: 300,
                  marginTop: 4,
                  overflow: 'hidden',
                }}
              >
                {profiles.map((p) => (
                  <button
                    key={p.id}
                    onClick={() => { setActiveProfileId(p.id); setProfileDropdown(false) }}
                    style={{
                      display: 'block',
                      width: '100%',
                      textAlign: 'left',
                      padding: '10px 14px',
                      background: p.id === activeProfileId ? 'var(--accent-dim)' : 'transparent',
                      border: 'none',
                      cursor: 'pointer',
                      fontSize: 13,
                      fontWeight: p.id === activeProfileId ? 700 : 400,
                      color: p.id === activeProfileId ? 'var(--accent)' : 'var(--text)',
                      borderBottom: '1px solid var(--border)',
                    }}
                  >
                    <div style={{ fontWeight: 700 }}>{p.name}</div>
                    <div style={{ fontSize: 11, color: 'var(--text-faint)', marginTop: 2 }}>
                      {p.modelName} · {p.classes.length} classes
                    </div>
                  </button>
                ))}
              </div>
            )}
          </div>

          <div style={{ marginLeft: 'auto', display: 'flex', gap: 20, alignItems: 'center' }}>
            <span style={{ fontSize: 12, color: 'var(--text-dim)' }}>
              Model: <strong style={{ color: 'var(--text)' }}>{activeProfile.modelName}</strong>
            </span>
            <span style={{ fontSize: 12, color: 'var(--text-dim)' }}>
              <strong style={{ color: 'var(--accent)' }}>{enabledCount}</strong>
              <span style={{ color: 'var(--text-faint)' }}>/{totalCount}</span> enabled
            </span>
            <span style={{ fontSize: 12, color: 'var(--text-faint)' }}>
              Updated {activeProfile.updatedAt}
            </span>
          </div>
        </div>
      </section>

      {/* Stats bar */}
      <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
        {CATEGORIES.map((cat) => {
          const count = activeProfile.classes.filter((c) => c.category === cat).length
          if (count === 0) return null
          return (
            <button
              key={cat}
              onClick={() => setFilterCategory(filterCategory === cat ? 'all' : cat)}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 6,
                padding: '5px 12px',
                borderRadius: 20,
                border: `1px solid ${filterCategory === cat ? CATEGORY_COLORS[cat] : 'var(--border)'}`,
                background: filterCategory === cat ? CATEGORY_COLORS[cat] + '22' : 'var(--panel)',
                color: filterCategory === cat ? CATEGORY_COLORS[cat] : 'var(--text-dim)',
                cursor: 'pointer',
                fontSize: 12,
                fontWeight: 600,
                transition: 'all 0.15s',
              }}
            >
              <Circle size={8} fill={CATEGORY_COLORS[cat]} stroke="none" />
              {cat}
              <span style={{ fontWeight: 800 }}>{count}</span>
            </button>
          )
        })}
      </div>

      {/* Filter bar */}
      <section className="av-panel" style={{ marginBottom: 4 }}>
        <div className="av-filter-row">
          <div className="av-search-box">
            <Search size={14} color="var(--text-faint)" />
            <input
              type="text"
              placeholder="Search by label, ID or description..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>

          <select
            value={filterCategory}
            onChange={(e) => setFilterCategory(e.target.value as ClassCategory | 'all')}
          >
            <option value="all">All Categories</option>
            {CATEGORIES.map((c) => (
              <option key={c} value={c}>{c}</option>
            ))}
          </select>

          <select
            value={filterEnabled}
            onChange={(e) => setFilterEnabled(e.target.value as typeof filterEnabled)}
          >
            <option value="all">All States</option>
            <option value="enabled">Enabled only</option>
            <option value="disabled">Disabled only</option>
          </select>

          <div style={{ marginLeft: 'auto', display: 'flex', gap: 8 }}>
            <button
              className="av-btn-secondary"
              onClick={() => toggleAll(true)}
              title="Enable all classes"
              style={{ fontSize: 12 }}
            >
              <Eye size={13} /> Enable All
            </button>
            <button
              className="av-btn-secondary"
              onClick={() => toggleAll(false)}
              title="Disable all classes"
              style={{ fontSize: 12 }}
            >
              <EyeOff size={13} /> Disable All
            </button>
            <button className="av-btn-secondary" title="Duplicate profile" style={{ fontSize: 12 }}>
              <Copy size={13} /> Duplicate
            </button>
          </div>
        </div>
      </section>

      {/* Class list */}
      </div>
      <div className="av-page-content" style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
        {filteredClasses.length === 0 ? (
          <div
            style={{
              textAlign: 'center',
              padding: 48,
              color: 'var(--text-faint)',
              background: 'var(--panel)',
              borderRadius: 'var(--radius-md)',
              border: '1px solid var(--border)',
            }}
          >
            No classes match the current filters.
          </div>
        ) : (
          filteredClasses.map((cls) => (
            <ClassRow
              key={cls.id}
              cls={cls}
              onChange={updateClass}
              onDelete={deleteClass}
              editingId={editingId}
              setEditingId={setEditingId}
            />
          ))
        )}
      </div>

      {/* Add Class Modal */}
      {showAddModal && (
        <AddClassModal
          nextId={nextId}
          onAdd={addClass}
          onClose={() => setShowAddModal(false)}
        />
      )}
    </div>
  )
}
