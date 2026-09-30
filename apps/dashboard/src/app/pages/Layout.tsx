import { useEffect, useState } from 'react'
import { Outlet, useLocation, useNavigate } from 'react-router-dom'
import { authService } from '@/modules/auth/services/auth'
import type { AuthUser } from '@/modules/auth/types/auth'
import Sidebar from '@/shared/components/Sidebar'
import Header from '@/app/components/Header'
import ChatWidget from '@/modules/assistant/components/ChatWidget'

export type Theme = 'dark' | 'light'

export default function Layout() {
  const [collapsed, setCollapsed] = useState(false)
  const [mobileOpen, setMobileOpen] = useState(false)
  const [isNavigating, setIsNavigating] = useState(false)
  const location = useLocation()
  const navigate = useNavigate()
  const isChat = location.pathname === '/chat' || location.pathname.startsWith('/chat/')
  const [user, setUser] = useState<AuthUser | null>(() => authService.currentUser())

  const [theme, setTheme] = useState<Theme>(() => {
    const saved = localStorage.getItem('av-theme') as Theme
    return saved === 'dark' ? 'dark' : 'light'
  })

  useEffect(() => {
    localStorage.setItem('av-theme', theme)
    // Tailwind dark mode uses class on <html>
    if (theme === 'dark') {
      document.documentElement.classList.add('dark')
    } else {
      document.documentElement.classList.remove('dark')
    }
  }, [theme])

  // Close mobile drawer whenever route changes
  useEffect(() => {
    setMobileOpen(false)
    setIsNavigating(true)
    const timer = window.setTimeout(() => setIsNavigating(false), 350)
    return () => window.clearTimeout(timer)
  }, [location.pathname])

  // Refresh the account once per session (role/name may have changed server-side)
  useEffect(() => {
    authService.me().then(setUser).catch(() => undefined)
  }, [])

  async function handleLogout() {
    await authService.logout().catch(() => undefined)
    navigate('/login', { replace: true })
  }

  function toggleTheme() {
    setTheme((prev) => (prev === 'dark' ? 'light' : 'dark'))
  }

  return (
    // Full-viewport shell: flex row, no overflow
    <div className="flex h-full overflow-hidden bg-background text-foreground font-sans" data-theme={theme}>
      {/* ── Sidebar ── */}
      <Sidebar
        collapsed={collapsed}
        onToggle={() => setCollapsed((c) => !c)}
        mobileOpen={mobileOpen}
        onCloseMobile={() => setMobileOpen(false)}
        user={user && { name: user.displayName || user.username, subtitle: `${user.role} · ${user.email}` }}
        onLogout={handleLogout}
      />

      {/* ── Main content column ── */}
      <div className="flex min-w-0 flex-1 flex-col overflow-hidden">
        {/* Top header bar */}
        <Header
          theme={theme}
          onToggleTheme={toggleTheme}
          onToggleMobileMenu={() => setMobileOpen((prev) => !prev)}
          mobileOpen={mobileOpen}
        />

        {/* Scrollable page body */}
        {/* Chat fits one screen: only its message list scrolls */}
        <main className={`relative min-h-0 flex-1 ${isChat ? 'overflow-hidden' : 'overflow-y-auto'}`}>
          {/* Route transition loading bar */}
          {isNavigating && (
            <div className="absolute inset-x-0 top-0 z-10 h-0.5 overflow-hidden">
              <div className="route-loading-bar h-full w-full bg-brand" />
            </div>
          )}
          <div className={isChat ? 'h-full' : 'p-6'}>
            <Outlet context={{ theme, toggleTheme }} />
          </div>
        </main>
      </div>

      {/* Floating chat widget (hidden on /chat route) */}
      {!isChat && <ChatWidget />}
    </div>
  )
}
