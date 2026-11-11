import { Link, Outlet, useLocation } from 'react-router-dom'
import {
  Camera,
  ChevronRight,
  Network,
  Server,
  Users,
} from 'lucide-react'
import TopBar from '@/components/layout/TopBar'
import { useAuth } from '@/contexts/AuthContext'

const TABS = [
  { path: '/admin/clusters', label: 'Clusters', icon: Server, step: '1', desc: 'Worksite plants & facilities' },
  { path: '/admin/nodes', label: 'Edge Nodes', icon: Network, step: '2', desc: 'Edge processing units per cluster' },
  { path: '/admin/cameras', label: 'Cameras', icon: Camera, step: '3', desc: 'Video streams attached to nodes' },
  { path: '/admin/users', label: 'Users & Roles', icon: Users, step: '4', desc: 'Access rights & permissions' },
]

export default function AdminPage() {
  const { user } = useAuth()
  const location = useLocation()

  return (
    <div className="flex h-dvh w-screen flex-col overflow-hidden bg-bg text-ink">
      {/* 1. VMS Top Navigation Bar */}
      <TopBar />

      {/* 2. Full-Width Administration Master Workspace */}
      <div className="flex min-h-0 flex-1 flex-col overflow-hidden lg:flex-row">
        {/* Left Sidebar Navigation - Compact VMS Style */}
        <aside className="w-full shrink-0 border-b border-line bg-panel flex flex-col justify-between text-xs select-none lg:w-52 lg:border-b-0 lg:border-r">
          <div className="flex flex-col min-h-0 flex-1 overflow-hidden">
            <nav className="flex gap-1 overflow-x-auto p-1.5 no-scrollbar lg:block lg:space-y-0.5 lg:overflow-y-auto">
              {TABS.map((t) => {
                const Icon = t.icon
                const active = location.pathname.startsWith(t.path)
                return (
                  <Link
                    key={t.path}
                    to={t.path}
                    className={`group relative flex shrink-0 items-center justify-between whitespace-nowrap rounded px-2 py-1.5 text-left transition-all ${
                      active
                        ? 'bg-panel2 text-ink font-semibold border border-line-strong shadow-xs'
                        : 'text-dim hover:text-ink hover:bg-panel2/50 border border-transparent'
                    }`}
                  >
                    {active && (
                      <span className="absolute left-0 inset-y-1 w-0.5 bg-cyan-400" />
                    )}
                    <div className="flex items-center gap-2 min-w-0 pl-1">
                      <Icon
                        size={13}
                        className={active ? 'text-cyan-400' : 'text-dim group-hover:text-ink'}
                      />
                      <span className="truncate text-xs font-medium">{t.label}</span>
                    </div>
                    <ChevronRight size={11} className={`shrink-0 ${active ? 'text-cyan-400' : 'text-dim/20'}`} />
                  </Link>
                )
              })}
            </nav>
          </div>

          {/* Sidebar System Diagnostic Footer */}
          <div className="hidden p-2.5 border-t border-line bg-panel2/40 text-[10px] space-y-1.5 font-mono lg:block">
            <div className="flex items-center justify-between text-dim">
              <span>Engine Status:</span>
              <span className="text-emerald-400 font-bold flex items-center gap-1.5">
                <span className="size-1.5 rounded-full bg-emerald-400 animate-pulse" />
                ONLINE
              </span>
            </div>
            <div className="flex items-center justify-between text-dim">
              <span>Model PPE:</span>
              <span className="text-cyan-400 font-semibold truncate">YOLOv8x-PPE</span>
            </div>
            <div className="flex items-center justify-between text-dim">
              <span>Operator:</span>
              <span className="text-ink truncate max-w-[120px]">{user?.full_name ?? 'Administrator'}</span>
            </div>
          </div>
        </aside>

        {/* Full-Width Sub-Route Content Canvas */}
        <main className="scroll-thin min-h-0 flex-1 min-w-0 overflow-y-auto bg-bg p-3 lg:p-4">
          <div className="w-full">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  )
}
