import { useState, useRef } from 'react'
import { Send, Cpu, Rocket, Power, Terminal, ChevronDown } from 'lucide-react'

export const SLASH_COMMANDS = [
  { cmd: '/diagnose', desc: 'Run full diagnostics', icon: Cpu },
  { cmd: '/deploy', desc: 'Roll out a new AI model', icon: Rocket },
  { cmd: '/restart', desc: 'Restart the agent daemon', icon: Power },
  { cmd: '/clear', desc: 'Clear the current chat', icon: Terminal }
]

const MODELS = [
  { id: 'gpt-4o', name: 'GPT-4o' },
  { id: 'claude-3-5', name: 'Claude 3.5 Sonnet' },
  { id: 'llama-3', name: 'Llama 3 8B (Edge)' },
]

interface Props {
  input: string
  setInput: (v: string) => void
  onSend: () => void
  compact?: boolean
}

export default function ChatInputForm({ input, setInput, onSend, compact = false }: Props) {
  const [selectedModel, setSelectedModel] = useState(MODELS[0])
  const [showModels, setShowModels] = useState(false)
  const inputRef = useRef<HTMLTextAreaElement>(null)
  const showCommands = input.startsWith('/')

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      onSend()
    }
  }

  const selectCommand = (cmd: string) => {
    setInput(cmd + ' ')
    inputRef.current?.focus()
  }

  return (
    <div style={{ position: 'relative', width: '100%' }}>
      {/* Slash Commands Popup */}
      {showCommands && (
        <div style={{ 
          position: 'absolute', bottom: '100%', left: 0, right: 0, marginBottom: 8, 
          background: 'var(--panel-2)', border: '1px solid var(--border)', borderRadius: 12, 
          boxShadow: 'none', overflow: 'hidden', zIndex: 10,
          animation: 'av-fade-in 0.2s cubic-bezier(0.16, 1, 0.3, 1)'
        }}>
          <div style={{ padding: '8px 12px', fontSize: 10, fontWeight: 700, color: 'var(--text-faint)', textTransform: 'uppercase', letterSpacing: '0.05em', borderBottom: '1px solid var(--border)' }}>
            Slash Commands
          </div>
          <div style={{ padding: 6, display: 'flex', flexDirection: 'column', gap: 2, maxHeight: 180, overflowY: 'auto' }}>
            {SLASH_COMMANDS.map(cmd => {
              const Icon = cmd.icon
              return (
                <button 
                  key={cmd.cmd}
                  onClick={() => selectCommand(cmd.cmd)}
                  type="button"
                  style={{ 
                    display: 'flex', alignItems: 'center', gap: 10, width: '100%', padding: compact ? '8px' : '10px 12px', 
                    background: 'transparent', border: 'none', borderRadius: 6, textAlign: 'left', cursor: 'pointer',
                    color: 'var(--text)'
                  }}
                  onMouseEnter={e => e.currentTarget.style.background = 'var(--panel)'}
                  onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
                >
                  <div style={{ width: 24, height: 24, borderRadius: 6, background: 'var(--bg-raised)', display: 'flex', alignItems: 'center', justifyContent: 'center', border: '1px solid var(--border)', flexShrink: 0 }}>
                    <Icon size={12} color="var(--text-main)" />
                  </div>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ fontSize: 13, fontWeight: 700, color: 'var(--accent)' }}>{cmd.cmd}</div>
                    {!compact && <div style={{ fontSize: 11, color: 'var(--text-dim)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{cmd.desc}</div>}
                  </div>
                </button>
              )
            })}
          </div>
        </div>
      )}

      {/* Main Input Form */}
      <form onSubmit={e => { e.preventDefault(); onSend(); }} style={{ 
        display: 'flex', flexDirection: 'column', gap: 8, 
        background: 'var(--panel)', border: '1px solid var(--border)', borderRadius: compact ? 16 : 20, 
        padding: compact ? '10px 12px' : '14px 16px 12px',
        boxShadow: 'none'
      }}>
        <textarea
          ref={inputRef}
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask Copilot or type '/'..."
          style={{ 
            width: '100%', background: 'transparent', border: 'none', color: 'var(--text)', 
            fontSize: 14, padding: '0', outline: 'none', resize: 'none', minHeight: compact ? 32 : 48,
            lineHeight: '1.5', fontFamily: 'var(--font-ui)'
          }}
        />
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: compact ? 0 : 4 }}>
          <div style={{ display: 'flex', gap: 8, alignItems: 'center', position: 'relative' }}>
            {/* Slash Command Button */}
            <button 
              type="button" 
              onClick={() => { setInput('/'); inputRef.current?.focus() }}
              className="av-icon-btn"
              title="Commands"
              style={{ width: compact ? 28 : 34, height: compact ? 28 : 34, borderRadius: '50%', background: 'var(--bg-raised)', border: '1px solid var(--border)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}
            >
              <span style={{ fontSize: compact ? 14 : 16, fontWeight: 700, color: 'var(--text-main)', fontFamily: 'var(--font-mono)' }}>/</span>
            </button>

            {/* Model Selector */}
            <div style={{ position: 'relative' }}>
              <button
                type="button"
                onClick={() => setShowModels(!showModels)}
                style={{ 
                  display: 'flex', alignItems: 'center', gap: 6, padding: compact ? '4px 8px' : '6px 12px',
                  background: 'var(--panel-2)', border: '1px solid var(--border)', borderRadius: 16,
                  color: 'var(--text-dim)', fontSize: 12, fontWeight: 600, cursor: 'pointer'
                }}
              >
                <span>{selectedModel.name}</span>
                <ChevronDown size={14} />
              </button>

              {/* Model Dropdown */}
              {showModels && (
                <div style={{
                  position: 'absolute', bottom: '100%', left: 0, marginBottom: 8,
                  background: 'var(--panel-2)', border: '1px solid var(--border)', borderRadius: 12,
                  boxShadow: 'none', overflow: 'hidden', zIndex: 20, minWidth: 160
                }}>
                  {MODELS.map(m => (
                    <button
                      key={m.id}
                      type="button"
                      onClick={() => { setSelectedModel(m); setShowModels(false); inputRef.current?.focus(); }}
                      style={{
                        display: 'block', width: '100%', padding: '10px 14px', textAlign: 'left',
                        background: selectedModel.id === m.id ? 'var(--bg-raised)' : 'transparent',
                        border: 'none', color: selectedModel.id === m.id ? 'var(--accent)' : 'var(--text)',
                        fontSize: 13, fontWeight: 600, cursor: 'pointer'
                      }}
                      onMouseEnter={e => { if (selectedModel.id !== m.id) e.currentTarget.style.background = 'var(--panel)' }}
                      onMouseLeave={e => { if (selectedModel.id !== m.id) e.currentTarget.style.background = 'transparent' }}
                    >
                      {m.name}
                    </button>
                  ))}
                </div>
              )}
            </div>
          </div>
          
          <button 
            type="submit" 
            className="av-btn-primary" 
            style={{ borderRadius: 14, padding: compact ? '6px 14px' : '8px 20px', fontSize: compact ? 13 : 14 }} 
            disabled={!input.trim()}
          >
            <Send size={14} />
            {!compact && <span style={{ marginLeft: 6 }}>Send</span>}
          </button>
        </div>
      </form>
    </div>
  )
}
