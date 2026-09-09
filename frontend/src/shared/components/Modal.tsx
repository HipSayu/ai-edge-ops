import React from 'react'
import { X } from 'lucide-react'

interface ModalProps {
  isOpen: boolean
  onClose: () => void
  title: string
  children: React.ReactNode
  maxWidth?: number
}

export default function Modal({ isOpen, onClose, title, children, maxWidth = 480 }: ModalProps) {
  if (!isOpen) return null

  return (
    <div className="av-modal-backdrop" onClick={onClose} style={{ zIndex: 999 }}>
      <div 
        className="av-incident-modal" 
        onClick={(e) => e.stopPropagation()} 
        style={{ maxWidth, width: '100%' }}
      >
        <div style={{ 
          padding: '16px 20px', 
          borderBottom: '1px solid var(--border)', 
          display: 'flex', 
          justifyContent: 'space-between', 
          alignItems: 'center',
          background: 'var(--panel-2)',
          borderTopLeftRadius: 'var(--radius-lg)',
          borderTopRightRadius: 'var(--radius-lg)'
        }}>
          <h3 style={{ margin: 0, fontSize: 16, fontWeight: 700 }}>{title}</h3>
          <button className="av-icon-btn" onClick={onClose} style={{ width: 32, height: 32 }}>
            <X size={16}/>
          </button>
        </div>
        <div style={{ padding: 20 }}>
          {children}
        </div>
      </div>
    </div>
  )
}
