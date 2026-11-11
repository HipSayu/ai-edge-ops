import type { ReactNode } from 'react'
import { Maximize2, Minimize2, X } from 'lucide-react'

export default function Modal({
  title,
  onClose,
  children,
  wide = false,
  isMaximized = false,
  onToggleMaximize,
}: {
  title: string
  onClose: () => void
  children: ReactNode
  wide?: boolean
  isMaximized?: boolean
  onToggleMaximize?: () => void
}) {
  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4 animate-in fade-in duration-200"
      onMouseDown={onClose}
    >
      <div
        className={`flex w-full flex-col border border-line bg-panel shadow-2xl shadow-black/30 transition-all ${
          isMaximized
            ? 'h-[96vh] max-h-[96vh] max-w-[98vw] rounded-xl'
            : `max-h-[92vh] rounded-2xl ${wide ? 'max-w-5xl' : 'max-w-md'}`
        }`}
        onMouseDown={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between border-b border-line px-5 py-3.5 bg-panel2/50 rounded-t-xl">
          <div className="flex items-center gap-2">
            <span className="size-2 rounded-full bg-brand animate-pulse" />
            <h2 className="font-semibold text-ink text-sm sm:text-base tracking-tight">{title}</h2>
          </div>
          <div className="flex items-center gap-1">
            {onToggleMaximize && (
              <button
                onClick={onToggleMaximize}
                className="rounded-lg p-1.5 text-dim hover:bg-panel2 hover:text-ink transition-colors cursor-pointer"
                title={isMaximized ? 'Minimize window' : 'Maximize window'}
                aria-label={isMaximized ? 'Minimize' : 'Maximize'}
              >
                {isMaximized ? <Minimize2 size={16} /> : <Maximize2 size={16} />}
              </button>
            )}
            <button
              onClick={onClose}
              className="rounded-lg p-1.5 text-dim hover:bg-panel2 hover:text-ink transition-colors cursor-pointer"
              aria-label="Close"
              title="Close"
            >
              <X size={18} />
            </button>
          </div>
        </div>
        <div className="scroll-thin overflow-y-auto p-5 flex-1">{children}</div>
      </div>
    </div>
  )
}
