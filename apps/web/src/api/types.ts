export type Role = 'VIEWER' | 'OPERATOR' | 'ADMIN'

export type ViolationType = 'no_helmet' | 'no_vest' | 'no_gloves' | 'no_safety_boots' | 'zone_intrusion'

export interface User {
  id: number
  username: string
  full_name: string
  role: Role
  is_active: boolean
  cluster_ids: number[]
  node_ids?: number[]
}

export interface Cluster {
  id: number
  name: string
  description: string | null
}

export interface NodeItem {
  id: number
  cluster_id: number
  cluster_name?: string
  name: string
  description: string | null
  ip_address?: string | null
  max_cameras?: number
  camera_count?: number
}

// Backward compatibility alias
export type Area = Cluster

export interface Camera {
  id: number
  name: string
  cluster_id: number | null
  node_id: number | null
  node_name?: string | null
  cluster_name?: string | null
  zone: string | null
  videos: string[]
  enabled: boolean
}

export interface GridItem {
  camera_id: number
  name: string
  cluster_id: number | null
  cluster_name: string | null
  node_id: number | null
  node_name: string | null
  zone: string | null
  person_count: number
  violation_count_recent: number
  score: number
  online: boolean
  stream_url: string
}

export interface ViolationEvent {
  id: number
  camera_id: number
  violation_type: ViolationType
  confidence: number
  created_at: string
}

export interface Stats {
  total: number
  by_type: Partial<Record<ViolationType, number>>
}

export interface LoginResult {
  access_token: string
  user: User
}

export interface UserInput {
  username: string
  password?: string
  full_name: string
  role: Role
  is_active: boolean
  cluster_ids: number[]
  node_ids?: number[]
}

export interface DetectedObject {
  label: string
  confidence: number
  box: [number, number, number, number]
}

export interface DetectionResult {
  detections: DetectedObject[]
  annotated_jpeg_b64: string
}

export type ChatEvent =
  | { type: 'token'; content: string }
  | { type: 'tool_start'; name: string }
  | { type: 'tool_end' }
  | { type: 'report'; url: string }
  | { type: 'approval_required'; id: string; summary: string; tool?: string; args?: Record<string, unknown> }
  | { type: 'done'; session_id: string; reply: string }
  | { type: 'error'; message: string }

// A corner of a zone: (x, y) as fractions (0..1) of the picture's width and height
export type ZonePoint = [number, number]

// A forbidden zone drawn on a camera's picture; id is missing until the cloud has saved it
export interface Zone {
  id?: number
  name: string
  polygon: ZonePoint[]
  enabled: boolean
}
