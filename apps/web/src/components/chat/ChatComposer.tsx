import { useEffect, useMemo, useRef, useState, type ClipboardEvent, type DragEvent, type KeyboardEvent, type ReactNode } from 'react'
import { ArrowUp, Check, ChevronDown, Command, ImagePlus, Plus, X } from 'lucide-react'
import { chatService } from '@/services/chat.service'
import { storage } from '@/helpers/storage'

// The message box of the chat, laid out like a modern assistant's: attached pictures on top, the text, and a bar below
// with "+" (attach), "/" (commands), the model to talk to, and send.

export interface SlashCommand {
  name: string // typed after the slash
  title: string // what the list shows
  hint: string
  icon: ReactNode
  /** an action runs at once; a prompt replaces the typed command in the box, for the user to read and send */
  run?: () => void
  prompt?: string
}

const MODEL_KEY = 'ppe_chat_model'
const MAX_IMAGES = 4
const MAX_ROWS_PX = 140

// "openai/gpt-4o-mini" -> "gpt-4o-mini"
const shortName = (model: string) => model.split('/').pop() ?? model

export default function ChatComposer({
  busy,
  commands,
  onSend,
}: {
  busy: boolean
  commands: SlashCommand[]
  onSend: (text: string, options: { files: File[]; model?: string }) => void
}) {
  const [text, setText] = useState('')
  const [files, setFiles] = useState<File[]>([])
  const [models, setModels] = useState<string[]>([])
  const [model, setModel] = useState<string>(() => storage.get(MODEL_KEY) ?? '')
  const [menu, setMenu] = useState<'model' | 'plus' | null>(null)
  const [pick, setPick] = useState(0)
  const [dragging, setDragging] = useState(false)
  const area = useRef<HTMLTextAreaElement>(null)
  const picker = useRef<HTMLInputElement>(null)

  useEffect(() => {
    chatService.models().then(
      ({ default: fallback, models: list }) => {
        setModels(list)
        setModel((current) => (list.includes(current) ? current : fallback))
      },
      () => undefined, // without the list the assistant still answers with its default model
    )
  }, [])

  // The box grows with its text, up to a few lines
  useEffect(() => {
    const el = area.current
    if (!el) return
    el.style.height = 'auto'
    el.style.height = `${Math.min(el.scrollHeight, MAX_ROWS_PX)}px`
  }, [text])

  const previews = useMemo(() => files.map((file) => URL.createObjectURL(file)), [files])
  useEffect(() => () => previews.forEach((url) => URL.revokeObjectURL(url)), [previews])

  // A "/word" at the start of the box opens the list of commands
  const typed = /^\/(\S*)$/.exec(text)
  const matches = typed ? commands.filter((c) => c.name.startsWith(typed[1].toLowerCase())) : []
  const slashOpen = matches.length > 0

  const addFiles = (incoming: File[]) => {
    const images = incoming.filter((f) => f.type.startsWith('image/'))
    if (images.length) setFiles((current) => [...current, ...images].slice(0, MAX_IMAGES))
  }

  const choose = (command: SlashCommand) => {
    if (command.run) {
      setText('')
      command.run()
    } else {
      setText(command.prompt ?? '')
      area.current?.focus()
    }
    setPick(0)
  }

  const submit = () => {
    if (busy || (!text.trim() && files.length === 0)) return
    onSend(text.trim() || 'Please look at this image', { files, model: model || undefined })
    setText('')
    setFiles([])
  }

  const onKeyDown = (event: KeyboardEvent<HTMLTextAreaElement>) => {
    if (slashOpen) {
      if (event.key === 'ArrowDown' || event.key === 'ArrowUp') {
        event.preventDefault()
        setPick((i) => (i + (event.key === 'ArrowDown' ? 1 : matches.length - 1)) % matches.length)
        return
      }
      if (event.key === 'Enter' || event.key === 'Tab') {
        event.preventDefault()
        choose(matches[Math.min(pick, matches.length - 1)])
        return
      }
      if (event.key === 'Escape') {
        setText('')
        return
      }
    }
    if (event.key === 'Enter' && !event.shiftKey && !event.nativeEvent.isComposing) {
      event.preventDefault()
      submit()
    }
  }

  const onPaste = (event: ClipboardEvent) => {
    const pasted = [...event.clipboardData.files]
    if (pasted.some((f) => f.type.startsWith('image/'))) {
      event.preventDefault()
      addFiles(pasted)
    }
  }

  const onDrop = (event: DragEvent) => {
    event.preventDefault()
    setDragging(false)
    addFiles([...event.dataTransfer.files])
  }

  const canSend = !busy && (text.trim().length > 0 || files.length > 0)

  return (
    <div className="relative shrink-0 border-t border-line bg-panel2/40 p-2">
      {slashOpen && (
        <ul className="absolute inset-x-2 bottom-full mb-1 max-h-52 overflow-y-auto rounded-lg border border-line bg-panel p-1 shadow-xl" role="listbox">
          {matches.map((c, i) => (
            <li key={c.name} role="option" aria-selected={i === pick}>
              <button
                type="button"
                onMouseEnter={() => setPick(i)}
                onClick={() => choose(c)}
                className={`flex w-full cursor-pointer items-start gap-2.5 rounded-md px-2 py-1.5 text-left ${i === pick ? 'bg-panel2' : ''}`}
              >
                <span className="grid size-6 shrink-0 place-items-center self-center rounded-md bg-cyan-500/10 text-cyan-300">{c.icon}</span>
                <span className="min-w-0 flex-1">
                  <span className="block truncate text-xs font-semibold text-ink">{c.title}</span>
                  <span className="block truncate text-[10px] text-dim">{c.hint}</span>
                </span>
                <span className="shrink-0 font-mono text-[10px] text-dim/70">/{c.name}</span>
              </button>
            </li>
          ))}
        </ul>
      )}

      <div
        onDragOver={(e) => {
          e.preventDefault()
          setDragging(true)
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={onDrop}
        className={`rounded-xl border bg-panel transition-colors focus-within:border-cyan-500/60 ${dragging ? 'border-cyan-400 bg-cyan-500/5' : 'border-line'}`}
      >
        {files.length > 0 && (
          <div className="flex flex-wrap gap-1.5 border-b border-line/60 p-2">
            {files.map((file, i) => (
              <div key={`${file.name}-${i}`} className="group relative size-12 overflow-hidden rounded-md border border-line bg-black">
                <img src={previews[i]} alt={file.name} className="size-full object-cover" />
                <button
                  type="button"
                  onClick={() => setFiles((current) => current.filter((_, j) => j !== i))}
                  aria-label={`Remove ${file.name}`}
                  className="absolute right-0.5 top-0.5 grid size-4 cursor-pointer place-items-center rounded-full bg-black/70 text-white opacity-0 transition-opacity group-hover:opacity-100"
                >
                  <X size={10} />
                </button>
              </div>
            ))}
          </div>
        )}

        <textarea
          ref={area}
          value={text}
          rows={1}
          onChange={(e) => {
            setText(e.target.value)
            setPick(0)
          }}
          onKeyDown={onKeyDown}
          onPaste={onPaste}
          placeholder="Ask the PPE assistant… type / for commands"
          className="block max-h-36 w-full resize-none bg-transparent px-3 pb-1 pt-2.5 text-xs text-ink outline-none placeholder:text-dim/60"
        />

        <div className="relative flex items-center gap-1 px-1.5 pb-1.5">
          <div className="relative">
            <button
              type="button"
              onClick={() => setMenu(menu === 'plus' ? null : 'plus')}
              title="Attach"
              className="grid size-7 cursor-pointer place-items-center rounded-md text-dim transition-colors hover:bg-panel2 hover:text-ink"
            >
              <Plus size={15} />
            </button>
            {menu === 'plus' && (
              <div className="absolute bottom-full left-0 z-20 mb-1 w-44 rounded-lg border border-line bg-panel p-1 shadow-xl">
                <button
                  type="button"
                  onClick={() => {
                    setMenu(null)
                    picker.current?.click()
                  }}
                  className="flex w-full cursor-pointer items-center gap-2 rounded px-2 py-1.5 text-left text-[11px] text-ink hover:bg-panel2"
                >
                  <ImagePlus size={13} className="text-cyan-300" /> Upload an image
                </button>
              </div>
            )}
            <input
              ref={picker}
              type="file"
              accept="image/jpeg,image/png,image/webp"
              multiple
              hidden
              onChange={(e) => {
                addFiles([...(e.target.files ?? [])])
                e.target.value = ''
              }}
            />
          </div>

          <button
            type="button"
            onClick={() => {
              setText('/')
              area.current?.focus()
            }}
            title="Commands"
            className="grid size-7 cursor-pointer place-items-center rounded-md text-dim transition-colors hover:bg-panel2 hover:text-ink"
          >
            <Command size={14} />
          </button>

          <div className="flex-1" />

          {models.length > 1 && (
            <div className="relative">
              <button
                type="button"
                onClick={() => setMenu(menu === 'model' ? null : 'model')}
                title="Choose a model"
                className="flex h-7 max-w-40 cursor-pointer items-center gap-1 rounded-md px-2 text-[11px] text-dim transition-colors hover:bg-panel2 hover:text-ink"
              >
                <span className="truncate">{shortName(model)}</span>
                <ChevronDown size={12} />
              </button>
              {menu === 'model' && (
                <ul className="absolute bottom-full right-0 z-20 mb-1 w-56 rounded-lg border border-line bg-panel p-1 shadow-xl" role="listbox">
                  {models.map((m) => (
                    <li key={m}>
                      <button
                        type="button"
                        onClick={() => {
                          setModel(m)
                          storage.set(MODEL_KEY, m)
                          setMenu(null)
                        }}
                        className="flex w-full cursor-pointer items-center justify-between gap-2 rounded px-2 py-1.5 text-left text-[11px] text-ink hover:bg-panel2"
                      >
                        <span className="truncate">{shortName(m)}</span>
                        {m === model && <Check size={12} className="shrink-0 text-cyan-300" />}
                      </button>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          )}

          <button
            type="button"
            onClick={submit}
            disabled={!canSend}
            aria-label="Send"
            className="grid size-7 cursor-pointer place-items-center rounded-lg bg-blue-600 text-white shadow-xs transition-all hover:bg-blue-500 disabled:cursor-not-allowed disabled:opacity-40"
          >
            <ArrowUp size={15} />
          </button>
        </div>
      </div>
    </div>
  )
}
