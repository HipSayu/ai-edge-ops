export type Severity = 'critical' | 'warning' | 'info'
export type IncidentStatus = 'New' | 'Reviewed' | 'Escalated'

export const SEVERITY_LABEL: Record<Severity, string> = {
  critical: 'CRITICAL',
  warning: 'WARNING',
  info: 'INFO',
}

export const STATUS_LABEL: Record<IncidentStatus, string> = {
  New: 'New',
  Reviewed: 'Reviewed',
  Escalated: 'Escalated',
}

export interface Incident {
  id: number
  time: string
  camera: string
  event: string
  confidence: number
  severity: Severity
  status: IncidentStatus
  personId: string
  location: string
  explanation: string
}

export const mockIncidents: Incident[] = [
  {
    id: 128,
    time: '11:45:32',
    camera: 'CAM-03',
    event: 'No Hard Hat',
    confidence: 96.2,
    severity: 'critical',
    status: 'New',
    personId: '#128',
    location: 'Main Factory Floor — Sector C, Bay 4',
    explanation:
      'Person detected with 98.7% confidence; head region classified as missing protective hard hat with 96.2% confidence over 3 consecutive frames, exceeding the 5-frame persistence threshold for false positive rejection.',
  },
  {
    id: 91,
    time: '11:44:17',
    camera: 'CAM-01',
    event: 'No Safety Vest',
    confidence: 94.8,
    severity: 'warning',
    status: 'Reviewed',
    personId: '#091',
    location: 'Gate 01 — Perimeter Access',
    explanation:
      'Upper torso feature embeddings failed high-visibility vest classification (color + retroreflective striping) with 94.8% confidence; subject stationary near access lane for 12 seconds.',
  },
  {
    id: 77,
    time: '11:43:02',
    camera: 'CAM-02',
    event: 'Perimeter Intrusion',
    confidence: 98.1,
    severity: 'critical',
    status: 'New',
    personId: '#077',
    location: 'Assembly Line Alpha — Sector B, Zone 2',
    explanation:
      'Subject centroid crossed virtual geofenced boundary without valid RFID authentication badge event logged within the previous 60 seconds.',
  },
  {
    id: 112,
    time: '11:39:51',
    camera: 'CAM-03',
    event: 'No Safety Gloves',
    confidence: 91.4,
    severity: 'warning',
    status: 'Reviewed',
    personId: '#112',
    location: 'Main Factory Floor — Sector C, Machine Bay 2',
    explanation:
      'Hand region classifier detected bare skin pattern without required nitrile/kevlar protective gloves at 91.4% confidence during machinery operation.',
  },
  {
    id: 78,
    time: '11:31:08',
    camera: 'CAM-01',
    event: 'No Face Mask',
    confidence: 89.6,
    severity: 'warning',
    status: 'Escalated',
    personId: '#078',
    location: 'Gate 01 — Perimeter Access',
    explanation:
      'Facial feature classifier detected absence of mandatory surgical/particulate respirator at 89.6% confidence in active cleanroom corridor.',
  },
]

export const kpi = {
  totalPeople: { value: 124, delta: 6.4 },
  compliant: { value: 112, rate: 90.3, delta: 2.1 },
  violations: { value: 12, delta: -8.3 },
  critical: { value: 3, delta: 50 },
}

export const liveTelemetry = {
  fps: 30,
  latencyMs: 42,
  objects: 8,
  aiConfidence: 96.2,
  resolution: '1080p60',
}

export interface AnalyticsPoint {
  time: string
  violations: number
  people: number
  complianceRate: number
}

function seededRandom(seed: number) {
  let s = seed
  return () => {
    s = (s * 9301 + 49297) % 233280
    return s / 233280
  }
}

const rand = seededRandom(11)

export const analyticsTimeline: AnalyticsPoint[] = Array.from({ length: 22 }, (_, i) => {
  const totalMinutes = i * 5
  const h = 10 + Math.floor(totalMinutes / 60)
  const m = totalMinutes % 60
  const people = Math.round(90 + rand() * 60)
  const violations = Math.round(rand() * 14)
  return {
    time: `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}`,
    people,
    violations,
    complianceRate: Math.round((1 - violations / people) * 1000) / 10,
  }
})

export const edgeDevice = {
  name: 'NVIDIA Jetson Orin NX 16GB',
  online: true,
  gpuUtilization: 78,
  gpuMemUsedGb: 11.2,
  gpuMemTotalGb: 16,
  temperatureC: 68,
  inferenceFps: 30,
  inferenceLatencyMs: 42,
  powerMode: '15W MAXN',
  model: 'YOLOv11-Enterprise',
  runtime: 'TensorRT 10.3 FP16',
}

export interface ChatMessage {
  id: number
  role: 'user' | 'assistant'
  text: string
}

export const suggestedQuestions = [
  'Show all critical safety incidents',
  'Which camera has the highest violation rate?',
  'How many people are currently detected?',
  'Focus live monitor on CAM-03',
  'Summarize events in the last 15 minutes',
]

export const initialChat: ChatMessage[] = [
  {
    id: 1,
    role: 'user',
    text: 'Which camera logged the highest number of safety violations in the past 30 minutes?',
  },
  {
    id: 2,
    role: 'assistant',
    text: 'CAM-03 (Main Factory Floor) logged the highest violation frequency with 5 PPE non-compliance events in the past 30 minutes — primarily missing hard hats and protective gloves across Sector C, Bays 2–4. Overall facility compliance is at 90.3%.',
  },
]
