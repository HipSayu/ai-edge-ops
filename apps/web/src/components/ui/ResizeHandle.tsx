import type { PointerEvent as ReactPointerEvent, ReactNode } from 'react'

// The line between two panels: 1px to look, with a wider invisible strip around it to grab.
// `col` splits left from right (drag sideways), `row` splits top from bottom. `grip` adds a pill for touch.
export default function ResizeHandle({
  axis,
  dragging,
  onPointerDown,
  title,
  grip = false,
  className = '',
  children,
}: {
  axis: 'col' | 'row'
  dragging: boolean
  onPointerDown: (event: ReactPointerEvent) => void
  title: string
  grip?: boolean
  className?: string
  children?: ReactNode
}) {
  const sizing =
    axis === 'col'
      ? 'w-px cursor-col-resize before:absolute before:inset-y-0 before:-inset-x-1'
      : 'h-px cursor-row-resize before:absolute before:inset-x-0 before:-inset-y-1'
  return (
    <div
      onPointerDown={onPointerDown}
      title={title}
      className={`group relative z-20 flex shrink-0 touch-none select-none items-center justify-center transition-colors ${sizing} ${
        dragging ? 'bg-blue-500' : 'bg-line hover:bg-blue-500'
      } ${className}`}
    >
      {grip && <div className="h-0.5 w-8 rounded-full bg-dim/40" />}
      {children}
    </div>
  )
}
