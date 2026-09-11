import React from 'react'

interface PageLayoutProps {
  header?: React.ReactNode
  children: React.ReactNode
}

export default function PageLayout({ header, children }: PageLayoutProps) {
  return (
    <div className="av-page-layout" style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      {header && (
        <div className="av-page-header">
          {header}
        </div>
      )}
      <div className="av-page-content" style={{ flex: 1, minHeight: 0, overflowY: 'auto' }}>
        {children}
      </div>
    </div>
  )
}

