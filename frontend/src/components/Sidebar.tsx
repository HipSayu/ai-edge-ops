import { NavLink } from 'react-router-dom'

const NAV_ITEMS = [
  { to: '/', label: 'Tổng quan', icon: '◧', end: true },
  { to: '/live', label: 'Giám sát trực tiếp', icon: '▶' },
  { to: '/cameras', label: 'Camera', icon: '⌘' },
  { to: '/incidents', label: 'Sự cố', icon: '⚠' },
  { to: '/analytics', label: 'Phân tích', icon: '▤' },
  { to: '/assistant', label: 'Trợ lý AI', icon: '✦' },
  { to: '/edge-devices', label: 'Thiết bị Edge', icon: '◨' },
  { to: '/settings', label: 'Cài đặt', icon: '⚙' },
]

interface Props {
  collapsed: boolean
  onToggle: () => void
}

export default function Sidebar({ collapsed, onToggle }: Props) {
  return (
    <aside className="av-sidebar">
      <div className="av-sidebar-logo">
        <span className="av-logo-mark">🛡</span>
        <span>AI Vision</span>
      </div>

      <nav className="av-nav">
        {NAV_ITEMS.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.end}
            className={({ isActive }) => `av-nav-item${isActive ? ' active' : ''}`}
          >
            <span className="av-nav-icon">{item.icon}</span>
            <span className="av-nav-label">{item.label}</span>
          </NavLink>
        ))}
      </nav>

      <div className="av-sidebar-footer">
        <div className="av-system-status">
          <span className="av-dot good pulse" />
          <span className="av-sidebar-footer-text">HỆ THỐNG HOẠT ĐỘNG BÌNH THƯỜNG</span>
        </div>
        <div className="av-user">
          <div className="av-avatar">AH</div>
          <div className="av-user-text">
            <span className="av-user-name">A. Hợp</span>
            <span className="av-user-role">Nhân viên vận hành</span>
          </div>
        </div>
      </div>

      <button className="av-collapse-btn" onClick={onToggle} aria-label="Thu gọn/mở rộng thanh bên">
        {collapsed ? '›' : '‹'}
      </button>
    </aside>
  )
}
