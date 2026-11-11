import { useRef, useState } from 'react'
import { AlertTriangle, CheckCircle2, ImageOff, Loader2, Upload, X } from 'lucide-react'
import { ApiError } from '@/api/client'
import type { DetectionResult } from '@/api/types'
import TopBar from '@/components/layout/TopBar'
import { detectService } from '@/services/detect.service'

export default function DetectPage() {
  const [preview, setPreview] = useState<string | null>(null)
  const [result, setResult] = useState<DetectionResult | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [dragOver, setDragOver] = useState(false)
  const inputRef = useRef<HTMLInputElement>(null)

  const run = async (file: File) => {
    setPreview(URL.createObjectURL(file))
    setResult(null)
    setError(null)
    setLoading(true)
    try {
      setResult(await detectService.run(file))
    } catch (e) {
      setError(e instanceof ApiError ? e.message : 'Could not reach the PPE detector')
    } finally {
      setLoading(false)
    }
  }

  const onFile = (files: FileList | null) => {
    const file = files?.[0]
    if (file) void run(file)
  }

  const reset = () => {
    setPreview(null)
    setResult(null)
    setError(null)
    if (inputRef.current) inputRef.current.value = ''
  }

  const violations = result?.detections.filter((d) => d.label.startsWith('no_')) ?? []
  const ok = result ? result.detections.length - violations.length : 0

  return (
    <div className="flex h-dvh w-screen flex-col overflow-hidden bg-bg text-ink">
      <TopBar />

      <div className="flex min-h-0 flex-1 flex-col gap-3 overflow-auto p-4">
        {/* Section 1: upload — always visible, compact */}
        <label
          htmlFor="detect-file"
          onDragOver={(e) => {
            e.preventDefault()
            setDragOver(true)
          }}
          onDragLeave={() => setDragOver(false)}
          onDrop={(e) => {
            e.preventDefault()
            setDragOver(false)
            onFile(e.dataTransfer.files)
          }}
          className={`flex shrink-0 cursor-pointer items-center justify-between gap-3 rounded-xl border-2 border-dashed px-4 py-3 transition-colors ${
            dragOver ? 'border-accent bg-accent/5' : 'border-line bg-panel hover:border-line-strong hover:bg-panel2'
          }`}
        >
          <div className="flex items-center gap-3">
            <div className="grid size-9 shrink-0 place-items-center rounded-full bg-panel2 text-dim">
              <Upload size={16} />
            </div>
            <div>
              <p className="text-[12.5px] font-medium text-ink">Drag and drop an image here, or click to choose</p>
              <p className="text-[11px] text-dim">JPEG, PNG or WebP, up to 8 MB</p>
            </div>
            <input
              id="detect-file"
              ref={inputRef}
              type="file"
              accept="image/jpeg,image/png,image/webp"
              className="hidden"
              onChange={(e) => onFile(e.target.files)}
            />
          </div>

          {(preview || result) && (
            <button
              onClick={(e) => {
                e.preventDefault()
                reset()
              }}
              className="flex shrink-0 items-center gap-1 rounded-md border border-line px-2.5 py-1 text-[11px] text-dim transition-colors hover:border-line-strong hover:text-ink"
            >
              <X size={12} /> Reset
            </button>
          )}
        </label>

        {error && (
          <div className="flex shrink-0 items-center gap-2 rounded-lg border border-danger/30 bg-danger/10 px-3 py-2.5 text-[12px] text-danger">
            <AlertTriangle size={14} className="shrink-0" />
            {error}
          </div>
        )}

        {/* Section 2: stats — always visible, dashed placeholders before a result */}
        <div className="grid shrink-0 grid-cols-2 gap-3 sm:grid-cols-4">
          <StatCard label="Detections" value={result?.detections.length} tone="neutral" />
          <StatCard label="Compliant" value={result ? ok : undefined} tone="ok" />
          <StatCard label="Violations" value={result ? violations.length : undefined} tone="danger" />
          <StatCard
            label="Status"
            value={result ? (violations.length > 0 ? 'Violation' : 'Safe') : undefined}
            tone={result && violations.length > 0 ? 'danger' : result ? 'ok' : 'neutral'}
          />
        </div>

        {/* Section 3 & 4: original picture / detection result — always visible */}
        <div className="grid min-h-0 flex-1 grid-cols-1 gap-3 lg:grid-cols-2">
          <Panel title="Original picture">
            {preview ? (
              <img src={preview} alt="Original" className="max-h-[55vh] w-full rounded-lg object-contain" />
            ) : (
              <EmptyState text="No picture chosen yet" />
            )}
          </Panel>

          <Panel title="Detection result">
            {loading && (
              <div className="flex flex-1 flex-col items-center justify-center gap-2 py-10 text-dim">
                <Loader2 size={20} className="animate-spin text-accent" />
                <span className="text-[12px]">Running the model...</span>
              </div>
            )}

            {!loading && !result && <EmptyState text="Results will appear here once you pick a picture" />}

            {!loading && result && (
              <div className="flex flex-col gap-3">
                <img
                  src={`data:image/jpeg;base64,${result.annotated_jpeg_b64}`}
                  alt="Detection result"
                  className="max-h-[42vh] w-full rounded-lg object-contain"
                />
                {result.detections.length === 0 ? (
                  <div className="flex items-center gap-2 rounded-lg border border-line bg-panel2 px-3 py-2.5 text-[12px] text-dim">
                    <ImageOff size={14} /> No objects detected in this picture
                  </div>
                ) : (
                  <ul className="flex flex-col gap-1.5">
                    {result.detections.map((d, i) => {
                      const violation = d.label.startsWith('no_')
                      return (
                        <li
                          key={i}
                          className={`flex items-center justify-between rounded-lg border px-3 py-1.5 text-[12px] ${
                            violation ? 'border-danger/25 bg-danger/5 text-danger' : 'border-ok/25 bg-ok/5 text-ok'
                          }`}
                        >
                          <span className="flex items-center gap-1.5 font-medium">
                            {violation ? <AlertTriangle size={13} /> : <CheckCircle2 size={13} />}
                            {d.label}
                          </span>
                          <span className="font-mono text-[11px] opacity-80">{Math.round(d.confidence * 100)}%</span>
                        </li>
                      )
                    })}
                  </ul>
                )}
              </div>
            )}
          </Panel>
        </div>
      </div>
    </div>
  )
}

function Panel({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="flex min-h-[220px] flex-col gap-2 rounded-xl border border-line bg-panel p-3">
      <span className="text-[10px] font-semibold uppercase tracking-wide text-dim">{title}</span>
      {children}
    </div>
  )
}

function EmptyState({ text }: { text: string }) {
  return (
    <div className="flex flex-1 flex-col items-center justify-center gap-2 py-10 text-dim">
      <ImageOff size={22} className="opacity-50" />
      <span className="text-[12px]">{text}</span>
    </div>
  )
}

const TONE_CLASS = {
  neutral: 'border-line text-ink',
  ok: 'border-ok/25 text-ok',
  danger: 'border-danger/25 text-danger',
} as const

function StatCard({
  label, value, tone,
}: { label: string; value: string | number | undefined; tone: keyof typeof TONE_CLASS }) {
  return (
    <div className={`rounded-xl border bg-panel px-3 py-2.5 ${TONE_CLASS[tone]}`}>
      <div className="text-[10px] font-medium uppercase tracking-wide text-dim">{label}</div>
      <div className="mt-0.5 text-lg font-bold">{value ?? <span className="text-dim">—</span>}</div>
    </div>
  )
}
