import { useEffect, useState } from 'react'
import { Outlet, useLocation } from 'react-router-dom'
import Sidebar from '@/shared/components/Sidebar'
import Header from '@/shared/components/Header'
import ChatWidget from '@/modules/assistant/components/ChatWidget'

export type Theme = 'dark' | 'light'

export default function Layout() {
  const [collapsed, setCollapsed] = useState(false)
  const [mobileOpen, setMobileOpen] = useState(false)
  const location = useLocation()

  // Default to 'light' for a bright, clean, modern UI
  const [theme, setTheme] = useState<Theme>(() => {
    const saved = localStorage.getItem('av-theme') as Theme
    return saved === 'dark' ? 'dark' : 'light'
  })

  useEffect(() => {
    localStorage.setItem('av-theme', theme)
    document.documentElement.setAttribute('data-theme', theme)
  }, [theme])

  // Close mobile drawer whenever route changes
  useEffect(() => {
    setMobileOpen(false)
  }, [location.pathname])

  function toggleTheme() {
    setTheme((prev) => (prev === 'dark' ? 'light' : 'dark'))
  }

  return (
    <div className="av-root" data-theme={theme}>
      <div className={`av-shell${collapsed ? ' collapsed' : ''}`}>
        <Sidebar
          collapsed={collapsed}
          onToggle={() => setCollapsed((c) => !c)}
          mobileOpen={mobileOpen}
          onCloseMobile={() => setMobileOpen(false)}
        />

        {mobileOpen && (
          <div
            className="av-mobile-backdrop"
            onClick={() => setMobileOpen(false)}
            aria-hidden="true"
          />
        )}

        <div className="av-content">
          <Header
            theme={theme}
            onToggleTheme={toggleTheme}
            onToggleMobileMenu={() => setMobileOpen((prev) => !prev)}
            mobileOpen={mobileOpen}
          />
          <div className="av-body">
            <main className="av-main">
              <Outlet context={{ theme, toggleTheme }} />
            </main>
          </div>
        </div>
      </div>
      {location.pathname !== '/chat' && <ChatWidget />}
    </div>
  )
}

