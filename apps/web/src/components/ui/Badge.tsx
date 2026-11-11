import type { ReactNode } from 'react'

// Status tags, not pills: square, uppercase, a solid state colour.
const TONE = {
  neutral: 'bg-panel2 text-dim border border-line-strong',
  danger: 'bg-danger/15 text-rose-400 border border-danger/60',
  ok: 'bg-ok/15 text-emerald-400 border border-ok/60',
  brand: 'bg-brand/15 text-blue-400 border border-brand/60',
  warning: 'bg-warning/15 text-amber-400 border border-warning/60',
}

export default function Badge({
  tone = 'neutral',
  dot = false,
  children,
  className = '',
}: {
  tone?: keyof typeof TONE
  dot?: boolean
  children: ReactNode
  className?: string
}) {
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-sm px-2 py-0.5 text-[11px] font-semibold uppercase tracking-wider ${TONE[tone]} ${className}`}
    >
      {dot && (
        <span
          className={`size-1.5 ${
            tone === 'danger'
              ? 'bg-rose-500 animate-pulse'
              : tone === 'ok'
                ? 'bg-emerald-500'
                : tone === 'brand'
                  ? 'bg-blue-500'
                  : 'bg-dim'
          }`}
        />
      )}
      {children}
    </span>
  )
}
