import { useState } from 'react'
import { MessagesSquare, SquarePen, SquarePlus, Trash2 } from 'lucide-react'
import type { Conversation } from '@/modules/assistant/types/assistant'

const DAY = 24 * 60 * 60 * 1000

function groupLabel(updatedAt: string): string {
  const startOfToday = new Date().setHours(0, 0, 0, 0)
  const t = new Date(updatedAt).getTime()
  if (t >= startOfToday) return 'Today'
  if (t >= startOfToday - DAY) return 'Yesterday'
  if (t >= startOfToday - 7 * DAY) return 'Previous 7 days'
  return 'Older'
}

function Row({ conversation, active, onSelect, onRename, onDelete }: {
  conversation: Conversation
  active: boolean
  onSelect: () => void
  onRename: (title: string) => void
  onDelete: () => void
}) {
  const [editing, setEditing] = useState(false)
  const [draft, setDraft] = useState('')
  const title = conversation.title || 'New Conversation'

  if (editing) {
    const commit = () => {
      setEditing(false)
      if (draft.trim() && draft.trim() !== conversation.title) onRename(draft.trim())
    }
    return (
      <input
        autoFocus
        value={draft}
        onChange={(e) => setDraft(e.target.value)}
        onBlur={commit}
        onKeyDown={(e) => {
          if (e.key === 'Enter') commit()
          if (e.key === 'Escape') setEditing(false)
        }}
        className="w-full rounded-lg border border-brand/60 bg-background px-2.5 py-1.5 text-[13px] text-foreground outline-none"
      />
    )
  }

  return (
    <div
      onClick={onSelect}
      className={`group flex cursor-pointer items-center gap-1 rounded-lg px-2.5 py-1.5 text-[13px] transition-colors ${
        active ? 'bg-muted font-medium text-foreground' : 'text-muted-foreground hover:bg-muted/60 hover:text-foreground'
      }`}
    >
      <span className="min-w-0 flex-1 truncate" title={title}>{title}</span>
      <span className={`flex shrink-0 items-center gap-0.5 ${active ? '' : 'opacity-0 group-hover:opacity-100'}`}>
        <button
          type="button"
          title="Rename"
          onClick={(e) => { e.stopPropagation(); setDraft(conversation.title ?? ''); setEditing(true) }}
          className="rounded p-1 hover:bg-background hover:text-foreground cursor-pointer"
        >
          <SquarePen size={12} />
        </button>
        <button
          type="button"
          title="Delete"
          onClick={(e) => { e.stopPropagation(); if (window.confirm(`Delete conversation "${title}"?`)) onDelete() }}
          className="rounded p-1 hover:bg-background hover:text-destructive cursor-pointer"
        >
          <Trash2 size={12} />
        </button>
      </span>
    </div>
  )
}

/** The user's conversations, most recent first and grouped by day, with new / rename / delete. */
export default function ConversationList({
  conversations,
  activeId,
  onSelect,
  onNew,
  onRename,
  onDelete,
  isOpen = true,
  onToggle,
}: {
  conversations: Conversation[]
  activeId?: string
  onSelect: (id: string) => void
  onNew: () => void
  onRename: (id: string, title: string) => void
  onDelete: (id: string) => void
  isOpen?: boolean
  onToggle?: () => void
}) {
  const groups: { label: string; items: Conversation[] }[] = []
  for (const c of conversations) {
    const label = groupLabel(c.updatedAt)
    const group = groups.find((g) => g.label === label)
    if (group) group.items.push(c)
    else groups.push({ label, items: [c] })
  }

  if (!isOpen) return null

  return (
    <aside className="w-64 shrink-0 flex-col border-r border-border bg-muted/20 flex">
      {/* Sidebar header — same height as the main toolbar (h-11) */}
      <div className="flex h-11 shrink-0 items-center border-b border-border/50 px-2">
        <button
          type="button"
          onClick={onNew}
          className="flex w-full items-center gap-2 rounded-md px-2 py-1.5 text-[13px] font-medium text-muted-foreground hover:bg-muted hover:text-foreground transition-colors cursor-pointer"
        >
          <SquarePlus size={14} className="shrink-0" />
          <span>New chat</span>
        </button>
      </div>
      <nav className="min-h-0 flex-1 overflow-y-auto px-2 pb-3">
        {conversations.length === 0 && (
          <div className="flex flex-col items-center gap-2 px-4 py-10 text-center text-xs text-muted-foreground">
            <MessagesSquare size={20} className="opacity-40" />
            <span>No conversations yet</span>
          </div>
        )}
        {groups.map((group) => (
          <div key={group.label} className="mb-3">
            <div className="px-2.5 pb-1 pt-2 text-[11px] font-semibold uppercase tracking-wider text-muted-foreground/60">{group.label}</div>
            <div className="flex flex-col gap-0.5">
              {group.items.map((c) => (
                <Row
                  key={c.id}
                  conversation={c}
                  active={c.id === activeId}
                  onSelect={() => onSelect(c.id)}
                  onRename={(title) => onRename(c.id, title)}
                  onDelete={() => onDelete(c.id)}
                />
              ))}
            </div>
          </div>
        ))}
      </nav>
    </aside>
  )
}
