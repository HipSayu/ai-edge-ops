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
