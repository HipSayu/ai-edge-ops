export type SystemRole = 'Admin' | 'Edge Operator' | 'MLOps Engineer' | 'Safety Auditor' | 'Viewer'

export interface UserAccount {
  id: string
  name: string
  email: string
  role: SystemRole
  status: 'active' | 'invited' | 'suspended'
  lastActive: string
  avatarInitials: string
  assignedSites: string[]
}

export const mockUsers: UserAccount[] = [
  {
    id: 'USR-01',
    name: 'Hop Do',
    email: 'hop.do@company.io',
    role: 'Admin',
    status: 'active',
    lastActive: 'Just now',
    avatarInitials: 'HD',
    assignedSites: ['All Facilities'],
  },
  {
    id: 'USR-02',
    name: 'Alex Chen',
    email: 'alex.chen@company.io',
    role: 'MLOps Engineer',
    status: 'active',
    lastActive: '12m ago',
    avatarInitials: 'AC',
    assignedSites: ['Plant A', 'Site 2 Secure'],
  },
  {
    id: 'USR-03',
    name: 'Elena Rostova',
    email: 'elena.r@company.io',
    role: 'Edge Operator',
    status: 'active',
    lastActive: '2h ago',
    avatarInitials: 'ER',
    assignedSites: ['Logistics Hub'],
  },
  {
    id: 'USR-04',
    name: 'David Miller',
    email: 'david.m@company.io',
    role: 'Safety Auditor',
    status: 'active',
    lastActive: 'Yesterday',
    avatarInitials: 'DM',
    assignedSites: ['All Facilities'],
  },
  {
    id: 'USR-05',
    name: 'Sarah Jenkins',
    email: 'sarah.j@contractor.com',
    role: 'Viewer',
    status: 'invited',
    lastActive: 'Never',
    avatarInitials: 'SJ',
    assignedSites: ['Plant A'],
  },
]

export interface AuditLog {
  id: string
  timestamp: string
  actor: string
  actorEmail: string
  action: string
  category: 'Deployment' | 'Hardware' | 'Security' | 'Config' | 'Triage'
  targetResource: string
  ipAddress: string
  status: 'SUCCESS' | 'FAILED' | 'DENIED'
  detail: string
}

export const mockAuditLogs: AuditLog[] = [
  {
    id: 'AUD-8901',
    timestamp: '2026-09-04 11:40:15',
    actor: 'Hop Do',
    actorEmail: 'hop.do@company.io',
    action: 'DEPLOY_MODEL_CANARY',
    category: 'Deployment',
    targetResource: 'YOLOv11-HazardDetection -> EDGE-NX-01',
    ipAddress: '192.168.1.45',
    status: 'SUCCESS',
    detail: 'Initiated 20% canary deployment of engine yolo11_hazard_rc1.engine',
  },
  {
    id: 'AUD-8902',
    timestamp: '2026-09-04 11:15:20',
    actor: 'System Daemon',
    actorEmail: 'system@internal',
    action: 'RESTART_STREAM_DAEMON',
    category: 'Hardware',
    targetResource: 'CAM-02 (Assembly Line Alpha)',
    ipAddress: '127.0.0.1',
    status: 'SUCCESS',
    detail: 'Auto-restarted dead RTSP socket after dropped packets timeout',
  },
  {
    id: 'AUD-8903',
    timestamp: '2026-09-04 10:20:00',
    actor: 'Alex Chen',
    actorEmail: 'alex.chen@company.io',
    action: 'MODIFY_AI_THRESHOLD',
    category: 'Config',
    targetResource: 'Inference Parameters (Facility 1)',
    ipAddress: '192.168.1.52',
    status: 'SUCCESS',
    detail: 'Changed confidence threshold from 60% to 65% for false-positive reduction',
  },
  {
    id: 'AUD-8904',
    timestamp: '2026-09-04 09:12:45',
    actor: 'Elena Rostova',
    actorEmail: 'elena.r@company.io',
    action: 'TRIAGE_ALERT_ACKNOWLEDGE',
    category: 'Triage',
    targetResource: 'Alert #91 (No Safety Vest)',
    ipAddress: '192.168.1.70',
    status: 'SUCCESS',
    detail: 'Marked incident reviewed and confirmed false alarm due to worker jacket reflection',
  },
  {
    id: 'AUD-8905',
    timestamp: '2026-09-03 18:40:12',
    actor: 'Unknown API Key',
    actorEmail: 'external_probe@unknown',
    action: 'ACCESS_RESTRICTED_STREAM',
    category: 'Security',
    targetResource: 'CAM-05 (Server Vault)',
    ipAddress: '203.0.113.195',
    status: 'DENIED',
    detail: 'Unauthorized token attempt on secure RTSP relay — IP automatically blacklisted',
  },
]
