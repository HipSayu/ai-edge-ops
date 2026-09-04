import { useState } from 'react'
import { Outlet } from 'react-router-dom'
import Sidebar from '../components/Sidebar'
import Header from '../components/Header'

export default function Layout() {
  const [collapsed, setCollapsed] = useState(false)

  return (
    <div className="av-root">
      <div className={`av-shell${collapsed ? ' collapsed' : ''}`}>
        <Sidebar collapsed={collapsed} onToggle={() => setCollapsed((c) => !c)} />
        <div className="av-content">
          <Header />
          <main className="av-main">
            <Outlet />
          </main>
        </div>
      </div>
    </div>
  )
}
