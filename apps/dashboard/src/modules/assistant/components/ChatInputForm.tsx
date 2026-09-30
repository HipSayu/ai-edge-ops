import { useRef } from 'react'
import { Send, Cpu, Rocket, Power, Terminal, Sparkles, Camera, AlertTriangle } from 'lucide-react'

export const SLASH_COMMANDS = [
  { cmd: '/diagnose', desc: 'Run full edge cluster & node diagnostics', icon: Cpu },
  { cmd: '/cameras', desc: 'Inspect live RTSP camera feeds & FPS', icon: Camera },
  { cmd: '/deploy', desc: 'Review active Vision AI model deployments', icon: Rocket },
  { cmd: '/safety', desc: 'Scan recent PPE & zone violation alerts', icon: AlertTriangle },
  { cmd: '/restart', desc: 'Restart node agent / inference worker', icon: Power },
  { cmd: '/clear', desc: 'Clear the current conversation thread', icon: Terminal },
]

interface Props {
  input: string
  setInput: (v: string) => void
  onSend: () => void
  disabled?: boolean
  compact?: boolean
}

export default function ChatInputForm({ input, setInput, onSend, disabled = false, compact = false }: Props) {
  const inputRef = useRef<HTMLTextAreaElement>(null)
  const showCommands = input.startsWith('/')

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      if (!disabled && input.trim()) {
        onSend()
      }
    }
  }

  const selectCommand = (cmd: string) => {
    setInput(cmd + ' ')
    inputRef.current?.focus()
  }

  return (
    <div className="relative w-full">
      {/* Slash Commands Popup */}
      {showCommands && (
        <div className="absolute bottom-full left-0 right-0 z-20 mb-2 overflow-hidden rounded-xl border border-border bg-card animate-in fade-in slide-in-from-bottom-2 duration-150">
          <div className="flex items-center justify-between border-b border-border bg-muted/40 px-3.5 py-2 text-[10.5px] font-bold tracking-wider text-muted-foreground">
            <span className="flex items-center gap-1.5">
              <Sparkles size={12} className="text-brand" />
              <span>Available Slash Commands</span>
            </span>
            <span className="text-[9.5px] font-mono">Press Tab or Click</span>
          </div>
          <div className="flex max-h-56 flex-col gap-0.5 overflow-y-auto p-1.5">
            {SLASH_COMMANDS.map((cmd) => {
              const Icon = cmd.icon
              return (
                <button
                  key={cmd.cmd}
                  type="button"
                  onClick={() => selectCommand(cmd.cmd)}
                  className="flex items-center gap-2.5 rounded-lg px-2.5 py-2 text-left transition-colors hover:bg-muted/70 cursor-pointer"
                >
                  <div className="flex size-7 shrink-0 items-center justify-center rounded-md border border-border bg-background text-brand">
                    <Icon size={14} />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="text-xs font-bold font-mono text-brand">{cmd.cmd}</div>
                    <div className="text-[11px] text-muted-foreground truncate">{cmd.desc}</div>
                  </div>
                </button>
              )
            })}
          </div>
        </div>
      )}

      {/* Main Input Box */}
      <form
        onSubmit={(e) => {
          e.preventDefault()
          if (!disabled && input.trim()) onSend()
        }}
        className="flex flex-col gap-2 rounded-2xl border border-border bg-card p-3 transition-all focus-within:border-brand/70 focus-within:ring-2 focus-within:ring-brand/15"
      >
        <textarea
          ref={inputRef}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask Copilot (e.g. 'Check cluster health', 'Any offline cameras?'). Type '/' for commands..."
          rows={compact ? 1 : 2}
          className="w-full resize-none bg-transparent px-1 text-sm text-foreground placeholder:text-muted-foreground outline-none leading-relaxed"
        />

        <div className="flex items-center justify-between gap-2 border-t border-border/50 pt-2">
          <div className="flex min-w-0 items-center gap-1.5">
            {/* Quick Slash Button */}
            <button
              type="button"
              onClick={() => {
                setInput('/')
                inputRef.current?.focus()
              }}
              title="View slash commands"
              className="flex size-7 shrink-0 items-center justify-center rounded-lg border border-border bg-muted/40 font-mono text-xs font-bold text-muted-foreground hover:bg-muted hover:text-foreground transition-colors cursor-pointer"
            >
              /
            </button>
          </div>

          <div className="flex shrink-0 items-center gap-2">
            <button
              type="submit"
              disabled={disabled || !input.trim()}
              className="flex h-7 shrink-0 items-center gap-1.5 whitespace-nowrap rounded-lg bg-brand px-3 text-xs font-semibold text-white hover:bg-brand/90 disabled:opacity-40 disabled:cursor-not-allowed transition-all cursor-pointer"
            >
              <Send size={13} />
              <span>Send</span>
            </button>
          </div>
        </div>
      </form>
    </div>
  )
}
