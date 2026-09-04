import { NavLink } from 'react-router-dom'
import {
  MessageSquare,
  LayoutDashboard,
  Cpu,
  Camera,
  Image as ImageIcon,
  FolderTree,
  Boxes,
  Rocket,
  Target,
  Activity,
  AlertTriangle,
  Zap,
  Terminal,
  Users,
  Settings as SettingsIcon,
  ClipboardList,
  ShieldAlert,
  ChevronLeft,
  ChevronRight,
  X,
} from 'lucide-react'

interface NavItem {
  to: string
  label: string
  icon: typeof LayoutDashboard
  end?: boolean
  badge?: string
  dotColor?: 'red' | 'amber' | 'blue'
}

interface NavGroup {
  title?: string
  items: NavItem[]
}

const NAVIGATION_GROUPS: NavGroup[] = [
  {
    items: [
      { to: '/', label: 'Overview', icon: LayoutDashboard, end: true },
      { to: '/chat', label: 'AI Assistant', icon: MessageSquare, dotColor: 'blue' },
    ],
  },
  {
    title: 'FLEET',
    items: [
      { to: '/fleet/devices', label: 'Devices', icon: Cpu, badge: '5', dotColor: 'amber' },
      { to: '/fleet/cameras', label: 'Cameras', icon: Camera, badge: 'LIVE', dotColor: 'red' },
      { to: '/fleet/snapshots', label: 'Gallery', icon: ImageIcon },
      { to: '/fleet/camera-groups', label: 'Camera Groups', icon: FolderTree },
    ],
  },
  {
    title: 'AI',
    items: [
      { to: '/ai/models', label: 'Models', icon: Boxes },
      { to: '/ai/deployments', label: 'Deployments', icon: Rocket, badge: '1', dotColor: 'blue' },
      { to: '/ai/inference', label: 'Inference', icon: Target },
    ],
  },
  {
    title: 'OBSERVABILITY',
    items: [
      { to: '/observability/monitoring', label: 'Monitoring', icon: Activity },
      { to: '/observability/alerts', label: 'Alerts', icon: AlertTriangle, badge: '3', dotColor: 'red' },
      { to: '/observability/events', label: 'Events', icon: Zap },
      { to: '/observability/logs', label: 'Logs', icon: Terminal },
    ],
  },
  {
    title: 'SYSTEM',
    items: [
      { to: '/system/users', label: 'Users & Roles', icon: Users, dotColor: 'amber' },
      { to: '/system/settings', label: 'Settings', icon: SettingsIcon },
      { to: '/system/audit-logs', label: 'Audit Logs', icon: ClipboardList },
    ],
  },
]

interface Props {
  collapsed: boolean
  onToggle: () => void
  mobileOpen: boolean
  onCloseMobile: () => void
}

export default function Sidebar({ collapsed: _collapsed, onToggle, mobileOpen, onCloseMobile }: Props) {
  // Always render full sidebar when opened on mobile
  const collapsed = _collapsed && !mobileOpen

  return (
    <aside className={`av-sidebar${mobileOpen ? ' mobile-open' : ''}${collapsed ? ' collapsed' : ''}`}>
      {/* Sidebar Header with Brand & Circular Toggle Button */}
      <div className="av-sidebar-top">
        <div className="av-sidebar-brand-wrapper">
          <div className="av-logo-mark" title="AI EDGE OPS Fleet Control">
            <ShieldAlert size={19} />
          </div>
          {!collapsed && (
            <div className="av-logo-brand">
              <span className="av-logo-title">AI EDGE OPS</span>
              <span className="av-logo-subtitle">Fleet & AI Control</span>
            </div>
          )}
        </div>

        {/* Circular toggle button matching reference image */}
        <button
          className="av-sidebar-toggle-btn"
          onClick={onToggle}
          aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
          title={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
        >
          {collapsed ? <ChevronRight size={14} /> : <ChevronLeft size={14} />}
        </button>

        {mobileOpen && (
          <button
            className="av-sidebar-mobile-close"
            onClick={onCloseMobile}
            aria-label="Close navigation"
          >
            <X size={18} />
          </button>
        )}
      </div>

      <div className="av-sidebar-divider" />

      {/* Navigation list */}
      <nav className="av-nav" aria-label="Main Navigation">
        {NAVIGATION_GROUPS.map((group, gIdx) => (
          <div key={gIdx} className="av-nav-group">
            {!collapsed && group.title && (
              <div className="av-nav-section-title">{group.title}</div>
            )}
            {group.items.map((item) => {
              const Icon = item.icon
              return (
                <NavLink
                  key={item.to}
                  to={item.to}
                  end={item.end}
                  onClick={onCloseMobile}
                  title={collapsed ? item.label : undefined}
                  className={({ isActive }) =>
                    `av-nav-item${isActive ? ' active' : ''}${collapsed ? ' icon-only' : ''}`
                  }
                >
                  <div className="av-nav-icon-container">
                    <Icon size={18} />
                    {/* Collapsed dot badge matching reference image */}
                    {collapsed && item.dotColor && (
                      <span className={`av-icon-dot-badge ${item.dotColor}`} />
                    )}
                  </div>

                  {!collapsed && <span className="av-nav-label">{item.label}</span>}

                  {!collapsed && item.badge && (
                    <span
                      className={`av-nav-badge${item.badge === 'LIVE' ? ' pulse-badge' : ''}`}
                    >
                      {item.badge}
                    </span>
                  )}
                </NavLink>
              )
            })}

            {/* Subtle group separator */}
            {gIdx < NAVIGATION_GROUPS.length - 1 && (
              <div className="av-sidebar-divider" />
            )}
          </div>
        ))}
      </nav>

      {/* Bottom User Avatar Section */}
      <div className="av-sidebar-footer">
        <div
          className="av-user-avatar-badge"
          title="Hop Do — Platform Lead"
        >
          S
        </div>
        {!collapsed && (
          <div className="av-user-text">
            <span className="av-user-name">Hop Do</span>
            <span className="av-user-role">Platform Lead</span>
          </div>
        )}
      </div>
    </aside>
  )
}



