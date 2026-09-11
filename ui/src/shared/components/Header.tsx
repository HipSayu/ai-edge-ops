import { useEffect, useState } from 'react'
import { Bell, Moon, Sun, Radio, Activity, Menu, X } from 'lucide-react'
import { agentService } from '@/shared/api/services/agent'

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
  const [isScrolled, setIsScrolled] = useState(false)
  const [cameraCounts, setCameraCounts] = useState({ online: 0, total: 0 })

  useEffect(() => {
    agentService.listCameras().then((cameras) => {
      setCameraCounts({ online: cameras.filter((camera) => camera.online).length, total: cameras.length })
    }).catch(() => setCameraCounts({ online: 0, total: 0 }))
  }, [])

  useEffect(() => {
    const id = setInterval(() => setNow(new Date()), 1000)
    return () => clearInterval(id)
  }, [])

  useEffect(() => {
    // The body owns scrolling so the header stays fixed in the viewport.
    const handleScroll = (e: Event) => {
      const target = e.target as HTMLElement | Document
      const scrollTop = target === document ? window.scrollY : (target as HTMLElement).scrollTop
      setIsScrolled(scrollTop > 10)
    }

    window.addEventListener('scroll', handleScroll, { passive: true })
    const bodyEl = document.querySelector('.av-body')
    bodyEl?.addEventListener('scroll', handleScroll, { passive: true })

    setIsScrolled(window.scrollY > 10 || (bodyEl?.scrollTop ?? 0) > 10)

    return () => {
      window.removeEventListener('scroll', handleScroll)
      bodyEl?.removeEventListener('scroll', handleScroll)
    }
  }, [])

  return (
    <header className={`av-header ${isScrolled ? 'scrolled' : ''}`}>
      <div className="av-header-left">
        {onToggleMobileMenu && (
          <button
            className="av-mobile-menu-btn"
            onClick={onToggleMobileMenu}
            aria-label={mobileOpen ? 'Close menu' : 'Open navigation menu'}
            title="Navigation Menu"
          >
            {mobileOpen ? <X size={20} /> : <Menu size={20} />}
          </button>
        )}

        <div>
          <div className="av-header-title">
            <span>AI Vision Operations Center</span>
          </div>
          <div className="av-header-sub">
            <span>
              {now.toLocaleDateString('en-US', {
                weekday: 'short',
                month: 'short',
                day: '2-digit',
                year: 'numeric',
              })}
            </span>
            <span className="av-header-dot-sep">·</span>
            <span>{now.toLocaleTimeString('en-US', { hour12: false })}</span>
          </div>
        </div>
      </div>

      <div className="av-header-right">
        <div className="av-header-stat-group">
          <div className="av-header-stat">
            <Radio size={14} color="var(--good)" />
            <span>
              <strong>{cameraCounts.online}</strong> / {cameraCounts.total} Online
            </span>
          </div>
          <div className="av-header-divider" />
          <div className="av-header-stat">
            <Activity size={14} color="var(--accent)" />
            <span>30 FPS • 42ms</span>
          </div>
        </div>

        {onToggleTheme && (
          <button
            className="av-icon-btn"
            onClick={onToggleTheme}
            aria-label={`Switch to ${theme === 'dark' ? 'Light' : 'Dark'} mode`}
            title={`Switch to ${theme === 'dark' ? 'Light' : 'Dark'} mode`}
          >
            {theme === 'dark' ? <Sun size={17} /> : <Moon size={17} />}
          </button>
        )}

        <button className="av-icon-btn" aria-label="Notifications" title="5 Unread Alerts">
          <Bell size={17} />
          <span className="av-notif-dot" />
        </button>

        <div className="av-avatar" title="Hop Do — Lead Operations">
          HD
        </div>
      </div>
    </header>
  )
}
