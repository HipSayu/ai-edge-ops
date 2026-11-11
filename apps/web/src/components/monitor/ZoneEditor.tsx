import { useCallback, useEffect, useMemo, useState, type MouseEvent } from 'react'
import { Eye, EyeOff, PenLine, Save, Trash2, Undo2, X } from 'lucide-react'
import type { Zone, ZonePoint } from '@/api/types'
import { Button, ErrorText, Input } from '@/components/ui'
import { publishZones } from '@/components/monitor/ZoneOverlay'
import { cameraService } from '@/services/camera.service'

// Corners are fractions (0..1) of the picture, so the zones do not depend on the resolution the edge decodes at.
// The layer is stretched over the stream, which is drawn 16:9: a camera with another ratio is cropped by the stream
// and the zones are drawn against what is visible.
const CLOSE_DISTANCE = 0.03 // clicking this close to the first corner closes the zone

const same = (a: Zone[], b: Zone[]) => JSON.stringify(a) === JSON.stringify(b)

export interface ZoneEditorState {
  zones: Zone[]
  drawing: boolean
  draft: ZonePoint[]
  name: string
  busy: boolean
  error: string | null
  dirty: boolean
  setName: (name: string) => void
  startDrawing: () => void
  cancelDrawing: () => void
  undoPoint: () => void
  addPoint: (point: ZonePoint) => void
  finish: () => void
  remove: (index: number) => void
  toggle: (index: number) => void
  save: () => Promise<void>
}

export function useZoneEditor(cameraId: number): ZoneEditorState {
  const [zones, setZones] = useState<Zone[]>([])
  const [saved, setSaved] = useState<Zone[]>([])
  const [drawing, setDrawing] = useState(false)
  const [draft, setDraft] = useState<ZonePoint[]>([])
  const [name, setName] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let alive = true
    cameraService
      .zones(cameraId)
      .then((z) => {
        if (!alive) return
        setZones(z)
        setSaved(z)
      })
      .catch((e: Error) => alive && setError(e.message))
    return () => {
      alive = false
    }
  }, [cameraId])

  const stopDrawing = useCallback(() => {
    setDrawing(false)
    setDraft([])
    setName('')
  }, [])

  const finish = useCallback(() => {
    if (draft.length < 3) return
    setZones((z) => [...z, { name: name.trim() || `Zone ${z.length + 1}`, polygon: draft, enabled: true }])
    stopDrawing()
  }, [draft, name, stopDrawing])

  const addPoint = useCallback(
    (point: ZonePoint) => {
      const [fx, fy] = draft[0] ?? [-1, -1]
      if (draft.length >= 3 && Math.hypot(point[0] - fx, point[1] - fy) < CLOSE_DISTANCE) finish()
      else setDraft((d) => [...d, point])
    },
    [draft, finish],
  )

  const save = useCallback(async () => {
    setBusy(true)
    setError(null)
    try {
      const result = await cameraService.saveZones(
        cameraId,
        zones.map(({ name: n, polygon, enabled }) => ({ name: n, polygon, enabled })),
      )
      setZones(result)
      setSaved(result)
      publishZones(cameraId, result) // the tiles on the wall show the new zones at once
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Could not save the zones')
    } finally {
      setBusy(false)
    }
  }, [cameraId, zones])

  return {
    zones,
    drawing,
    draft,
    name,
    busy,
    error,
    dirty: !same(zones, saved),
    setName,
    startDrawing: () => {
      setError(null)
      setDrawing(true)
    },
    cancelDrawing: stopDrawing,
    undoPoint: () => setDraft((d) => d.slice(0, -1)),
    addPoint,
    finish,
    remove: (index) => setZones((z) => z.filter((_, i) => i !== index)),
    toggle: (index) => setZones((z) => z.map((zone, i) => (i === index ? { ...zone, enabled: !zone.enabled } : zone))),
    save,
  }
}

const centroid = (polygon: ZonePoint[]): ZonePoint => [
  polygon.reduce((s, p) => s + p[0], 0) / polygon.length,
  polygon.reduce((s, p) => s + p[1], 0) / polygon.length,
]

const asPoints = (polygon: ZonePoint[]) => polygon.map(([x, y]) => `${x},${y}`).join(' ')

// Drawn over the stream: the zones, and while drawing the corners placed so far. Clicks add corners only while drawing.
export function ZoneLayer({ editor }: { editor: ZoneEditorState }) {
  const onClick = (event: MouseEvent<HTMLDivElement>) => {
    const box = event.currentTarget.getBoundingClientRect()
    const x = Math.min(Math.max((event.clientX - box.left) / box.width, 0), 1)
    const y = Math.min(Math.max((event.clientY - box.top) / box.height, 0), 1)
    editor.addPoint([Number(x.toFixed(4)), Number(y.toFixed(4))])
  }
  const shown = useMemo(() => editor.zones.filter((z) => z.enabled), [editor.zones])

  return (
    <div
      className={`absolute inset-0 ${editor.drawing ? 'cursor-crosshair' : 'pointer-events-none'}`}
      onClick={editor.drawing ? onClick : undefined}
    >
      <svg className="absolute inset-0 size-full" viewBox="0 0 1 1" preserveAspectRatio="none">
        {shown.map((z, i) => (
          <polygon
            key={z.id ?? `new-${i}`}
            points={asPoints(z.polygon)}
            fill="rgba(244,63,94,0.18)"
            stroke="#f43f5e"
            strokeWidth={0.004}
            strokeDasharray="0.012 0.008"
          />
        ))}
        {editor.draft.length > 1 && (
          <polyline points={asPoints(editor.draft)} fill="none" stroke="#fbbf24" strokeWidth={0.004} />
        )}
      </svg>
      {shown.map((z, i) => {
        const [cx, cy] = centroid(z.polygon)
        return (
          <span
            key={`label-${z.id ?? i}`}
            className="absolute -translate-x-1/2 -translate-y-1/2 rounded bg-rose-600/80 px-1.5 py-0.5 text-[10px] font-bold text-white"
            style={{ left: `${cx * 100}%`, top: `${cy * 100}%` }}
          >
            {z.name}
          </span>
        )
      })}
      {editor.draft.map(([x, y], i) => (
        <span
          key={i}
          className={`absolute size-2.5 -translate-x-1/2 -translate-y-1/2 rounded-full border border-black/50 ${i === 0 ? 'bg-emerald-400' : 'bg-amber-300'}`}
          style={{ left: `${x * 100}%`, top: `${y * 100}%` }}
        />
      ))}
    </div>
  )
}

// The list of zones and the controls to draw them. Everyone with access sees the list; only an operator changes it.
export function ZonePanel({ editor, canEdit }: { editor: ZoneEditorState; canEdit: boolean }) {
  return (
    <div className="space-y-2.5">
      <div className="flex items-center justify-between border-b border-line pb-2">
        <h3 className="text-xs font-bold uppercase tracking-wider text-ink">Restricted zones</h3>
        <span className="text-xs font-semibold text-dim">{editor.zones.length}</span>
      </div>

      {editor.zones.length === 0 && !editor.drawing && (
        <p className="text-[11px] text-dim">
          No zone is set. When someone walks into one, the edge sounds its alarm on the spot and reports the entry here.
        </p>
      )}

      <ul className="space-y-1.5">
        {editor.zones.map((z, i) => (
          <li key={z.id ?? `new-${i}`} className="flex items-center gap-2 rounded-lg border border-line bg-panel2/40 px-2 py-1.5">
            <span className={`min-w-0 flex-1 truncate text-xs font-semibold ${z.enabled ? 'text-ink' : 'text-dim line-through'}`}>
              {z.name}
            </span>
            {canEdit && (
              <>
                <button
                  type="button"
                  title={z.enabled ? 'Switch off' : 'Switch on'}
                  className="text-dim hover:text-ink"
                  onClick={() => editor.toggle(i)}
                >
                  {z.enabled ? <Eye size={14} /> : <EyeOff size={14} />}
                </button>
                <button type="button" title="Delete" className="text-dim hover:text-rose-400" onClick={() => editor.remove(i)}>
                  <Trash2 size={14} />
                </button>
              </>
            )}
          </li>
        ))}
      </ul>

      {canEdit && editor.drawing && (
        <div className="space-y-2 rounded-lg border border-amber-400/40 bg-amber-400/5 p-2">
          <Input label="Zone name" value={editor.name} onChange={(e) => editor.setName(e.target.value)} placeholder="e.g. Tower crane" />
          <p className="text-[11px] text-dim">
            Click on the picture to place the corners. Click the first (green) corner again, or press Finish, to close the zone.
          </p>
          <div className="flex flex-wrap gap-1.5">
            <Button size="sm" variant="primary" disabled={editor.draft.length < 3} onClick={editor.finish}>
              Finish
            </Button>
            <Button size="sm" icon={<Undo2 size={12} />} disabled={editor.draft.length === 0} onClick={editor.undoPoint}>
              Undo
            </Button>
            <Button size="sm" variant="ghost" icon={<X size={12} />} onClick={editor.cancelDrawing}>
              Cancel
            </Button>
          </div>
        </div>
      )}

      {canEdit && !editor.drawing && (
        <div className="flex flex-wrap gap-1.5">
          <Button size="sm" icon={<PenLine size={12} />} onClick={editor.startDrawing}>
            Draw zone
          </Button>
          {editor.dirty && (
            <Button size="sm" variant="primary" icon={<Save size={12} />} disabled={editor.busy} onClick={() => void editor.save()}>
              {editor.busy ? 'Saving' : 'Save and send to edge'}
            </Button>
          )}
        </div>
      )}
      <ErrorText message={editor.error} />
    </div>
  )
}
