export type SystemRole = 'Admin' | 'Edge Operator' | 'MLOps Engineer' | 'Safety Auditor' | 'Viewer'
export interface UserAccount { id: string; name: string; email: string; role: SystemRole; status: 'active' | 'invited' | 'suspended'; lastActive: string; avatarInitials: string; assignedSites: string[] }
