import { useEffect, useState } from 'react'
import { mockCameras } from '../mock/cameras'

export default function Header() {
  const [now, setNow] = useState(new Date())

  useEffect(() => {
    const id = setInterval(() => setNow(new Date()), 1000)
    return () => clearInterval(id)
  }, [])

  const onlineCount = mockCameras.filter((c) => c.online).length

  return (
    <header className="av-header">
      <div>
        <div className="av-header-title">Trung tâm điều hành AI Vision</div>
        <div className="av-header-sub">
          {now.toLocaleDateString('vi-VN', { day: '2-digit', month: '2-digit', year: 'numeric' })} ·{' '}
          {now.toLocaleTimeString('vi-VN', { hour12: false })}
        </div>
      </div>

      <div className="av-header-right">
        <div className="av-header-stat">
          <span className="av-dot good" />
          {onlineCount} camera đang hoạt động
        </div>
        <div className="av-header-stat">
          <span className="av-dot good pulse" />
          Đang hoạt động
        </div>
        <button className="av-icon-btn" aria-label="Thông báo">
          🔔
          <span className="av-notif-dot" />
        </button>
        <div className="av-avatar">AH</div>
      </div>
    </header>
  )
}
