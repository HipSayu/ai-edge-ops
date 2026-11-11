import type { Role, ViolationType } from '@/api/types'

export const VIOLATION_LABEL: Record<ViolationType, string> = {
  no_helmet: 'No Safety Helmet',
  no_vest: 'No Hi-Vis Vest',
  no_gloves: 'No Safety Gloves',
  no_safety_boots: 'No Safety Boots',
  zone_intrusion: 'Restricted Zone Entry',
}

export const ROLE_LABEL: Record<Role, string> = {
  VIEWER: 'Viewer',
  OPERATOR: 'Operator',
  ADMIN: 'Administrator',
}

export const ROLES: Role[] = ['VIEWER', 'OPERATOR', 'ADMIN']

// What the assistant is up to, in words a person uses, while a reply is being prepared. The names of its tools and agents
// stay out of sight: the user sees the kind of work, never how the system does it.
export function activityLabel(tool: string | null): string {
  if (!tool) return 'Thinking'
  if (tool === 'search_knowledge') return 'Checking the regulations'
  if (tool === 'detect_ppe') return 'Looking at the image'
  if (tool === 'export_safety_report') return 'Writing the report'
  if (/^(create|update|delete)_/.test(tool)) return 'Preparing a proposal'
  return 'Looking at the data' // every tool that reads the system's data
}
