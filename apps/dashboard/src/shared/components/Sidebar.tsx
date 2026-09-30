import { NavLink, useLocation } from 'react-router-dom'
import {
  MessageSquare,
  LayoutDashboard,
  Camera,
  Boxes,
  Tags,
  ShieldAlert,
  ChevronLeft,
  ChevronRight,
  X,
  LogOut,
  Network,
  Server,
} from 'lucide-react'

interface NavItem {
  to: string
  label: string
  icon: React.ComponentType<{ size?: number; className?: string }>
  badge?: string
  end?: boolean
  dotColor?: 'red' | 'amber' | 'blue'
}

interface NavGroup {
  title?: string
  items: NavItem[]
}

const DOT_COLOR_MAP: Record<string, string> = {
  red: 'bg-destructive animate-pulse-dot',
  amber: 'bg-warning',
  blue: 'bg-info',
}

const NAVIGATION_GROUPS: NavGroup[] = [
  {
    items: [
      { to: '/', label: 'Overview', icon: LayoutDashboard, end: true },
      { to: '/chat', label: 'AI Assistant', icon: MessageSquare, dotColor: 'blue' },
    ],
  },
  {
    title: 'Agent',
    items: [
      { to: '/agent/clusters', label: 'Clusters', icon: Network },
      { to: '/agent/nodes', label: 'Nodes', icon: Server, badge: '9', dotColor: 'amber' },
      { to: '/agent/cameras', label: 'Cameras', icon: Camera, badge: 'Live', dotColor: 'red' },
    ],
  },
  {
    title: 'Model',
    items: [
      { to: '/models/registry', label: 'Models', icon: Boxes },
      { to: '/models/class-config', label: 'Class Config', icon: Tags },
    ],
  },
]

interface SidebarUser {
  name: string
  subtitle: string
}

interface Props {
  collapsed: boolean
  onToggle: () => void
  mobileOpen: boolean
  onCloseMobile: () => void
  user?: SidebarUser | null
  onLogout?: () => void
}

function initials(name?: string) {
  const parts = (name ?? '').trim().split(/[\s._-]+/).filter(Boolean)
  return (parts.length > 1 ? parts[0][0] + parts[parts.length - 1][0] : (parts[0] ?? '?').slice(0, 2)).toUpperCase()
}

export default function Sidebar({ collapsed: _collapsed, onToggle, mobileOpen, onCloseMobile, user, onLogout }: Props) {
  const collapsed = _collapsed && !mobileOpen
  const location = useLocation()

  return (
    <>
      {/* Mobile backdrop */}
      {mobileOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/40 backdrop-blur-sm lg:hidden"
          onClick={onCloseMobile}
          aria-hidden="true"
        />
      )}

      <aside
        data-collapsed={collapsed}
        className={[
          'group/sidebar',
          // Floating card: inset from the viewport edges, full border, rounded
          'm-2 flex h-[calc(100%-1rem)] flex-none flex-col overflow-hidden',
          'rounded-xl border border-sidebar-border bg-sidebar text-sidebar-foreground',
          'transition-[width] duration-200 ease-in-out',
          collapsed ? 'w-[56px]' : 'w-[160px]',
          // Mobile: fixed overlay
          mobileOpen
            ? 'fixed left-0 top-0 z-50 w-[150px] lg:static'
            : mobileOpen === false && !collapsed
            ? 'hidden lg:flex'
            : '',
        ].join(' ')}
      >
        {/* ── Header / Brand ── */}
        <div className={`flex flex-none items-center ${collapsed ? 'flex-col justify-center py-2.5 px-1 gap-2' : 'h-[46px] justify-between px-2.5'}`}>
          {/* 8px margin + 1px border + 46px = divider lands on the h-14 page header's bottom border */}
          {/* Logo mark + brand text */}
          <div className={`flex min-w-0 items-center gap-2 overflow-hidden ${collapsed ? 'justify-center w-full' : ''}`}>
            <div
              onClick={collapsed ? onToggle : undefined}
              title={collapsed ? 'AI Edge Ops - Click to expand' : undefined}
              className={`flex size-8 shrink-0 items-center justify-center rounded-lg bg-brand text-brand-foreground ${collapsed ? 'cursor-pointer hover:opacity-90' : ''}`}
            >
              <ShieldAlert size={16} />
            </div>

            {!collapsed && (
              <div className="flex min-w-0 flex-col leading-tight">
                <span className="truncate text-xs font-bold tracking-tight text-sidebar-foreground">
                  AI Edge Ops
                </span>
                <span className="truncate text-[9.5px] font-semibold tracking-wider text-brand">
                  Control Center
                </span>
              </div>
            )}
          </div>

          {/* Collapse toggle */}
          <button
            onClick={onToggle}
            aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
            title={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
            className={[
              'flex size-5.5 shrink-0 items-center justify-center cursor-pointer',
              'rounded-full border border-sidebar-border bg-sidebar',
              'text-muted-foreground transition-colors',
              'hover:border-sidebar-primary hover:text-sidebar-primary hover:bg-sidebar-accent',
            ].join(' ')}
          >
            {collapsed ? <ChevronRight size={12} /> : <ChevronLeft size={12} />}
          </button>

          {/* Mobile close button */}
          {mobileOpen && (
            <button
              onClick={onCloseMobile}
              aria-label="Close navigation"
              className="flex size-7 items-center justify-center rounded-md text-muted-foreground hover:text-foreground lg:hidden"
            >
              <X size={17} />
            </button>
          )}
        </div>

        {/* Divider */}
        <div className="mx-2 h-px bg-sidebar-border" />

        {/* ── Navigation ── */}
        <nav className={`flex min-h-0 flex-1 flex-col gap-0.5 overflow-y-auto ${collapsed ? 'px-1.5' : 'px-2'} py-2 no-scrollbar`} aria-label="Main Navigation">
          {NAVIGATION_GROUPS.map((group, gIdx) => (
            <div key={gIdx} className="flex flex-col gap-0.5 py-0.5">
              {/* Group label */}
              {!collapsed && group.title && (
                <div className="px-2 pb-1 pt-2.5 text-[9.5px] font-bold tracking-wide text-muted-foreground/80">
                  {group.title}
                </div>
              )}

              {/* Nav items */}
              {group.items.map((item) => {
                const Icon = item.icon
                const isActive =
                  item.end
                    ? location.pathname === item.to
                    : location.pathname.startsWith(item.to)

                return (
                  <NavLink
                    key={item.to}
                    to={item.to}
                    end={item.end}
                    onClick={onCloseMobile}
                    title={collapsed ? item.label : undefined}
                    className={[
                      'relative flex w-full items-center gap-2 overflow-hidden rounded-md text-xs font-medium no-underline',
                      'outline-none transition-colors',
                      collapsed
                        ? 'mx-auto size-8 justify-center gap-0 px-0'
                        : 'h-[32px] px-2',
                      isActive
                        ? 'bg-sidebar-accent text-sidebar-accent-foreground font-semibold before:absolute before:inset-y-1.5 before:left-0 before:w-[3px] before:rounded-r-full before:bg-sidebar-primary'
                        : 'text-sidebar-foreground/70 hover:bg-sidebar-accent hover:text-sidebar-accent-foreground',
                    ].join(' ')}
                  >
                    {/* Icon wrapper with optional dot badge */}
                    <div className="relative shrink-0">
                      <Icon size={16} />
                      {collapsed && item.dotColor && (
                        <span
                          className={[
                            'absolute -right-0.5 -top-0.5 size-2 rounded-full ring-1 ring-sidebar',
                            DOT_COLOR_MAP[item.dotColor],
                          ].join(' ')}
                        />
                      )}
                    </div>

                    {/* Label */}
                    {!collapsed && (
                      <span className="min-w-0 flex-1 truncate">{item.label}</span>
                    )}

                    {/* Badge */}
                    {!collapsed && item.badge && (
                      <span
                        className={[
                          'ml-auto flex-none rounded-full px-1.5 py-px text-[9.5px] font-semibold tabular-nums',
                          item.badge === 'Live'
                            ? 'animate-pulse-dot bg-destructive/15 text-destructive'
                            : 'bg-sidebar-primary/10 text-sidebar-primary',
                        ].join(' ')}
                      >
                        {item.badge}
                      </span>
                    )}
                  </NavLink>
                )
              })}

              {/* Group separator */}
              {gIdx < NAVIGATION_GROUPS.length - 1 && (
                <div className="mx-1.5 my-1 h-px bg-sidebar-border" />
              )}
            </div>
          ))}
        </nav>

        {/* ── Footer / User ── */}
        <div className={`flex flex-none items-center border-t border-sidebar-border ${collapsed ? 'flex-col justify-center gap-1.5 p-2' : 'gap-2 px-2.5 py-2.5'}`}>
          <div
            className="flex size-7.5 shrink-0 items-center justify-center rounded-full bg-brand text-[11px] font-bold text-brand-foreground"
            title={user ? `${user.name} — ${user.subtitle}` : undefined}
          >
            {initials(user?.name)}
          </div>
          {!collapsed && user && (
            <div className="flex min-w-0 flex-1 flex-col leading-tight">
              <span className="truncate text-xs font-semibold text-sidebar-foreground">{user.name}</span>
              <span className="truncate text-[10px] text-muted-foreground">{user.subtitle}</span>
            </div>
          )}
          {onLogout && (
            <button
              onClick={onLogout}
              aria-label="Sign out"
              title="Sign out"
              className="flex size-7 shrink-0 cursor-pointer items-center justify-center rounded-md text-muted-foreground transition-colors hover:bg-sidebar-accent hover:text-destructive"
            >
              <LogOut size={14} />
            </button>
          )}
        </div>
      </aside>
    </>
  )
}
