import { AlertTriangle, Camera, Check, X, ShieldAlert, Activity } from 'lucide-react'

// No need to import React explicitly; using automatic JSX runtime

export interface EventLog {
  id: string | number
  worker: string
  cam: string
  time: string
  status: 'UNSAFE' | 'SAFE' | 'WARNING'
  aiImage: string
  regImage: string
  equipment: {
    hardHat?: boolean
    safetyVest?: boolean
    safetyStrap?: boolean
    safetyWand?: boolean
    wireHook?: boolean
  }
}

interface LogsEventSidebarProps {
  events: EventLog[]
  title?: string
}

export default function LogsEventSidebar({ events, title = 'Live event logs' }: LogsEventSidebarProps) {
  return (
    <section 
      className="av-panel" 
      style={{ 
        width: 380, 
        flexShrink: 0, 
        display: 'flex', 
        flexDirection: 'column', 
        padding: 0, 
        overflow: 'hidden',
        border: '1px solid var(--border)',
      }}
    >
      <div 
        className="av-panel-header" 
        style={{ 
          borderBottom: '1px solid var(--border)', 
          padding: '14px 20px', 
          background: 'var(--panel-2)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between'
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <Activity size={16} color="var(--accent)" className="pulse" />
          <span className="av-panel-title" style={{ fontSize: 13, fontWeight: 800, letterSpacing: '0.06em', margin: 0 }}>
            {title}
          </span>
        </div>
        <span style={{ fontSize: 11, fontWeight: 700, color: 'var(--text-faint)', background: 'var(--panel-3)', padding: '2px 8px', borderRadius: 12 }}>
          {events.length} Events
        </span>
      </div>

      <div style={{ 
        flex: 1, 
        overflowY: 'auto', 
        padding: '16px', 
        display: 'flex', 
        flexDirection: 'column', 
        gap: 16, 
        background: 'var(--bg)' 
      }}>
        {events.length === 0 ? (
          <div style={{ textAlign: 'center', color: 'var(--text-faint)', padding: '40px 0', fontSize: 13 }}>
            No recent events detected.
          </div>
        ) : (
          events.map((ev) => (
            <EventCard key={ev.id} event={ev} />
          ))
        )}
      </div>
    </section>
  )
}

function EventCard({ event }: { event: EventLog }) {
  const isUnsafe = event.status === 'UNSAFE'
  const statusColor = isUnsafe ? 'var(--critical)' : event.status === 'WARNING' ? 'var(--warning)' : 'var(--good)'
  
  return (
    <div style={{ 
      display: 'flex', 
      background: 'var(--panel)', 
      border: `1px solid ${isUnsafe ? 'rgba(239,68,68,0.3)' : 'var(--border)'}`, 
      borderRadius: 12,
      padding: 14,
      gap: 14,
      transition: 'transform 0.2s ease, box-shadow 0.2s ease',
      cursor: 'pointer'
    }}
    onMouseEnter={(e) => {
      e.currentTarget.style.transform = 'translateY(-2px)'
    }}
    onMouseLeave={(e) => {
      e.currentTarget.style.transform = 'none'
    }}
    >
      {/* Images Column */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 10, width: 84 }}>
        <div style={{ position: 'relative', borderRadius: 8, overflow: 'hidden', border: '1px solid var(--border)' }}>
          <img src={event.aiImage} alt="AI Overlay" style={{ width: '100%', height: 110, objectFit: 'cover', display: 'block' }} />
          <div style={{ 
            position: 'absolute', 
            bottom: 0, left: 0, right: 0, 
            textAlign: 'center', 
            fontSize: 9, 
            fontWeight: 700,
            background: 'rgba(0,0,0,0.7)', 
            color: '#fff',
            padding: '4px 2px',
            backdropFilter: 'blur(4px)'
          }}>
            AI Overlay
          </div>
        </div>
        <div style={{ position: 'relative', borderRadius: 8, overflow: 'hidden', border: '1px solid var(--border)' }}>
          <img src={event.regImage} alt="Registered" style={{ width: '100%', height: 84, objectFit: 'cover', display: 'block' }} />
          <div style={{ 
            position: 'absolute', 
            bottom: 0, left: 0, right: 0, 
            textAlign: 'center', 
            fontSize: 9, 
            fontWeight: 700,
            background: 'rgba(0,0,0,0.7)', 
            color: '#fff',
            padding: '4px 2px',
            backdropFilter: 'blur(4px)'
          }}>
            Registered
          </div>
        </div>
      </div>

      {/* Info Column */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 6, color: statusColor, fontWeight: 800, fontSize: 13, letterSpacing: '0.05em' }}>
            {isUnsafe ? <ShieldAlert size={16} /> : <AlertTriangle size={16} />} 
            {event.status}
          </div>
          <div style={{ color: 'var(--text-faint)', fontSize: 11, display: 'flex', alignItems: 'center', gap: 4, fontFamily: 'var(--font-mono)' }}>
            <Camera size={11} /> {event.cam}
          </div>
        </div>
        
        <div style={{ color: 'var(--text)', fontWeight: 700, fontSize: 15, marginTop: 6, marginBottom: 2 }}>
          {event.worker}
        </div>
        <div style={{ color: 'var(--text-dim)', fontSize: 11, fontFamily: 'var(--font-mono)', marginBottom: 12 }}>
          Captured at {event.time}
        </div>
        
        <div style={{ fontSize: 11, fontWeight: 700, color: 'var(--text-faint)', letterSpacing: '0.04em', marginBottom: 8, borderBottom: '1px solid var(--border)', paddingBottom: 6 }}>
          Safety Equipment
        </div>
        
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px 4px', fontSize: 11.5, fontWeight: 600 }}>
          <EquipmentItem label="Hard Hat" checked={event.equipment.hardHat} />
          <EquipmentItem label="Safety Vest" checked={event.equipment.safetyVest} />
          <EquipmentItem label="Safety Strap" checked={event.equipment.safetyStrap} />
          <EquipmentItem label="Safety Wand" checked={event.equipment.safetyWand} />
          <EquipmentItem label="Wire Hook" checked={event.equipment.wireHook} />
        </div>
      </div>
    </div>
  )
}

function EquipmentItem({ label, checked }: { label: string, checked?: boolean }) {
  if (checked === undefined) return null;
  const isOk = checked;
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 6, color: isOk ? 'var(--good)' : 'var(--critical)' }}>
      {isOk ? <Check size={14} /> : <X size={14} strokeWidth={3} />} 
      <span style={{ color: 'var(--text-dim)' }}>{label}</span>
    </div>
  )
}

