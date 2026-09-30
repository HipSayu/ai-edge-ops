import { useEffect, useState, useMemo } from 'react'
import { Bell, Moon, Sun, Radio, Activity, Menu, X, ChevronRight, Home } from 'lucide-react'
import { agentService } from '@/modules/agent/services/agent'
import { useLocation, Link } from 'react-router-dom'
import { useEdgeOps } from '@/core/edge-ops/EdgeOpsContext'
import { conversationService } from '@/modules/assistant/services/conversations'
import type { Conversation } from '@/modules/assistant/types/assistant'

// Map segment to human-readable label
const SEGMENT_LABELS: Record<string, string> = {
  '': 'Overview',
  'chat': 'AI Assistant',
  'agent': 'Edge Agent',
  'clusters': 'Clusters',
  'nodes': 'Nodes',
  'devices': 'Nodes',
  'cameras': 'Cameras',
  'logs': 'Runtime Logs',
  'snapshots': 'Gallery',
  'camera-groups': 'Camera Groups',
  'ai': 'Vision AI Engine',
  'models': 'Models',
  'registry': 'Model Registry',
  'deployments': 'Deployments',
  'class-config': 'Class Config',
  'system': 'System',
  'users': 'Users & Roles',
  'settings': 'Settings',
  'audit-logs': 'Audit Logs',
}

interface Props {
  theme?: 'dark' | 'light'
  onToggleTheme?: () => void
  onToggleMobileMenu?: () => void
  mobileOpen?: boolean
}

export default function Header({
  theme = 'light',
  onToggleTheme,
  onToggleMobileMenu,
  mobileOpen = false,
}: Props) {
  const [now, setNow] = useState(new Date())
  const [cameraCounts, setCameraCounts] = useState({ online: 0, total: 0 })
  const [conversations, setConversations] = useState<Conversation[]>([])
  const location = useLocation()
  const { clusters } = useEdgeOps()

  // Fetch conversations only when inside the /chat route to resolve IDs → titles
  useEffect(() => {
    if (!location.pathname.startsWith('/chat')) return
    conversationService.list().then(setConversations).catch(() => undefined)
  }, [location.pathname])

  // Generate dynamic breadcrumbs array
  const breadcrumbs = useMemo(() => {
    // Filter out group prefixes like 'agent' to keep breadcrumbs concise and uncluttered
    const segments = location.pathname.split('/').filter(Boolean).filter((s) => s !== 'agent')
    if (segments.length === 0) {
      return [{ path: '/', label: 'Overview', isLast: true }]
    }

    const crumbs: { path: string; label: string; isLast: boolean }[] = []
    let currentPath = ''

    segments.forEach((seg, idx) => {
      // Re-add agent prefix in target path if relevant
      if (['clusters', 'nodes', 'devices', 'cameras', 'logs'].includes(seg) && idx === 0) {
        currentPath = `/agent/${seg}`
      } else {
        currentPath += `/${seg}`
      }
      const isLast = idx === segments.length - 1

      // Resolve label: static map → cluster → node → conversation → raw segment
      let label = SEGMENT_LABELS[seg]
      if (!label) {
        // Try cluster name
        const matchedCluster = clusters.find((c) => c.id === seg)
        if (matchedCluster) {
          label = matchedCluster.name
        } else {
          // Try node name
          for (const c of clusters) {
            const matchedNode = c.nodes.find((n) => n.id === seg || n.name.toLowerCase() === seg.toLowerCase())
            if (matchedNode) {
              label = matchedNode.name
              break
            }
          }
        }
        // Try conversation title
        if (!label) {
          const matchedConversation = conversations.find((c) => c.id === seg)
          if (matchedConversation) {
            label = matchedConversation.title || 'Untitled'
          }
        }
        if (!label) label = seg
      }

      crumbs.push({
        path: currentPath,
        label,
        isLast,
      })
    })

    return crumbs
  }, [location.pathname, clusters, conversations])

  useEffect(() => {
    agentService.listCameras().then((cameras) => {
      setCameraCounts({ online: cameras.filter((c) => c.online).length, total: cameras.length })
    }).catch(() => setCameraCounts({ online: 0, total: 0 }))
  }, [])

  useEffect(() => {
    const id = setInterval(() => setNow(new Date()), 1000)
    return () => clearInterval(id)
  }, [])

  return (
    <header className="flex h-14 flex-none items-center justify-between gap-4 border-b border-border bg-background px-4">
      {/* ── Left: mobile menu + dynamic breadcrumb router ── */}
      <div className="flex min-w-0 items-center gap-2.5">
        {/* Mobile hamburger */}
        {onToggleMobileMenu && (
          <button
            onClick={onToggleMobileMenu}
            aria-label={mobileOpen ? 'Close menu' : 'Open navigation menu'}
            className="flex size-8 items-center justify-center rounded-md text-muted-foreground transition-colors hover:bg-accent hover:text-accent-foreground lg:hidden"
          >
            {mobileOpen ? <X size={18} /> : <Menu size={18} />}
          </button>
        )}

        {/* Dynamic Breadcrumbs */}
        <nav aria-label="Breadcrumb" className="flex min-w-0 items-center gap-1.5 text-xs">
          <Link
            to="/"
            title="Overview"
            className="flex items-center text-muted-foreground transition-colors hover:text-foreground"
          >
            <Home size={14} />
          </Link>

          {breadcrumbs.map((crumb) => (
            <div key={crumb.path} className="flex items-center gap-1.5 min-w-0">
              <ChevronRight size={13} className="text-muted-foreground/40 shrink-0" />
              {crumb.isLast ? (
                <span className="font-bold text-foreground truncate max-w-[240px]">
                  {crumb.label}
                </span>
              ) : (
                <Link
                  to={crumb.path}
                  className="text-muted-foreground transition-colors hover:text-foreground truncate max-w-[160px]"
                >
                  {crumb.label}
                </Link>
              )}
            </div>
          ))}
        </nav>
      </div>

      {/* ── Right: stats + actions ── */}
      <div className="flex flex-none items-center gap-1">
        {/* Camera online stat */}
        <div className="hidden items-center gap-4 rounded-md border border-border px-3 py-1.5 text-xs text-muted-foreground sm:flex">
          <div className="flex items-center gap-1.5">
            <Radio size={12} className="text-success" />
            <span>
              <strong className="font-semibold text-foreground">{cameraCounts.online}</strong>
              &nbsp;/&nbsp;{cameraCounts.total} online
            </span>
          </div>
          <div className="h-3.5 w-px bg-border" />
          <div className="flex items-center gap-1.5">
            <Activity size={12} className="text-info" />
            <span>30 FPS · 42ms</span>
          </div>
        </div>

        {/* Separator */}
        <div className="mx-1 hidden h-5 w-px bg-border sm:block" />

        {/* Date/time */}
        <span className="hidden font-mono text-xs text-muted-foreground md:inline">
          {now.toLocaleTimeString('en-US', { hour12: false })}
        </span>

        {/* Theme toggle button */}
        {onToggleTheme && (
          <button
            onClick={onToggleTheme}
            aria-label={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
            className="flex size-8 items-center justify-center rounded-md text-muted-foreground transition-colors hover:bg-accent hover:text-accent-foreground"
          >
            {theme === 'dark' ? <Sun size={16} /> : <Moon size={16} />}
          </button>
        )}

        {/* Notification button */}
        <button
          aria-label="Notifications"
          className="relative flex size-8 items-center justify-center rounded-md text-muted-foreground transition-colors hover:bg-accent hover:text-accent-foreground"
        >
          <Bell size={16} />
          <span className="absolute top-1.5 right-1.5 size-2 rounded-full bg-destructive" />
        </button>
      </div>
    </header>
  )
}
