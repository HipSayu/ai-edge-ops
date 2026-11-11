import { useEffect, useState, type CSSProperties, type ReactNode } from 'react'
import { ChevronDown, ChevronLeft, ChevronRight, ChevronUp, Maximize2, Minimize2 } from 'lucide-react'

const ICON_BUTTON = 'rounded p-1 text-dim hover:bg-panel hover:text-ink cursor-pointer transition-colors'
const BASE = 'flex min-h-0 min-w-0 flex-col overflow-hidden bg-panel text-xs'
// Maximized: fills the whole work area (the nearest positioned ancestor); the page header stays visible
const FILLING = 'absolute inset-0 z-30'

// One frame for every block of the monitor: a title bar with maximize and collapse, and a body.
// The parent decides the size (width, height, flex); this decides what the block does when asked to
// collapse (`collapseAxis`) or to maximize (it fills the work area and leaves its slot in place).
export default function PanelFrame({
  title,
  icon,
  badge,
  actions,
  collapsed,
  onToggleCollapse,
  collapseAxis = 'vertical',
  className = '',
  style,
  children,
}: {
  title: string
  icon: ReactNode
  badge?: ReactNode
  actions?: ReactNode
  collapsed: boolean
  onToggleCollapse: () => void
  /** vertical: only the title bar stays. horizontal: a narrow strip with the title written sideways. */
  collapseAxis?: 'vertical' | 'horizontal'
  className?: string
  style?: CSSProperties
  children: ReactNode
}) {
  const [maximized, setMaximized] = useState(false)

  useEffect(() => {
    if (!maximized) return
    const onKey = (event: KeyboardEvent) => event.key === 'Escape' && setMaximized(false)
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [maximized])

  const toggleMaximize = () => {
    if (collapsed) onToggleCollapse() // a collapsed block would open as an empty window
    setMaximized(!maximized)
  }

  if (collapsed && collapseAxis === 'horizontal' && !maximized) {
    return (
      <section style={style} className={`flex min-h-0 flex-col bg-panel ${className}`}>
        <button
          onClick={onToggleCollapse}
          title={`Expand ${title}`}
          className="flex h-full w-full cursor-pointer flex-col items-center gap-2 py-2 text-dim transition-colors hover:bg-panel2 hover:text-ink"
        >
          <ChevronRight size={13} />
          {icon}
          <span className="text-[10px] font-bold uppercase tracking-wider [writing-mode:vertical-rl]">{title}</span>
        </button>
      </section>
    )
  }

  const CollapseIcon =
    collapseAxis === 'horizontal' ? (collapsed ? ChevronRight : ChevronLeft) : collapsed ? ChevronUp : ChevronDown

  // The same <section> keeps its place in the tree whether maximized or not, so its content is not remounted.
  return (
    <>
      {maximized && <div aria-hidden className={className} style={style} />}
      <section style={maximized ? undefined : style} className={`${BASE} ${maximized ? FILLING : className}`}>
        <header className="flex min-h-8 shrink-0 select-none flex-wrap items-center justify-between gap-x-2 gap-y-1 border-b border-line bg-panel2/80 px-2.5 py-0.5">
          <div className="flex min-w-0 items-center gap-1.5 text-[11px] font-bold uppercase tracking-wider text-ink">
            {icon}
            <span className="truncate">{title}</span>
            {badge}
          </div>
          <div className="flex shrink-0 items-center gap-1">
            {actions}
            <button
              onClick={toggleMaximize}
              title={maximized ? 'Minimize' : 'Maximize'}
              className={ICON_BUTTON}
            >
              {maximized ? <Minimize2 size={12} /> : <Maximize2 size={12} />}
            </button>
            {!maximized && (
              <button
                onClick={onToggleCollapse}
                title={collapsed ? `Expand ${title}` : `Collapse ${title}`}
                className={ICON_BUTTON}
              >
                <CollapseIcon size={13} />
              </button>
            )}
          </div>
        </header>
        {!collapsed && <div className="flex min-h-0 flex-1 flex-col overflow-hidden">{children}</div>}
      </section>
    </>
  )
}
