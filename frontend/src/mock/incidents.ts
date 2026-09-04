export type Severity = 'critical' | 'warning' | 'info'
export type IncidentStatus = 'New' | 'Reviewed' | 'Escalated'

export const SEVERITY_LABEL: Record<Severity, string> = {
  critical: 'NGHIÊM TRỌNG',
  warning: 'CẢNH BÁO',
  info: 'THÔNG TIN',
}

export const STATUS_LABEL: Record<IncidentStatus, string> = {
  New: 'Mới',
  Reviewed: 'Đã xem xét',
  Escalated: 'Đã chuyển cấp',
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
    event: 'Không mũ bảo hộ',
    confidence: 96.2,
    severity: 'critical',
    status: 'New',
    personId: '#128',
    location: 'Sàn nhà máy — Khu C, Gian 4',
    explanation:
      'Phát hiện người với độ tin cậy 98.7%; vùng đầu được phân loại là không đội mũ bảo hộ với độ tin cậy 96.2% trong 3 khung hình liên tiếp, vượt ngưỡng bền vững 5 khung hình dùng để loại bỏ báo động giả.',
  },
  {
    id: 91,
    time: '11:44:17',
    camera: 'CAM-01',
    event: 'Không áo phản quang',
    confidence: 94.8,
    severity: 'warning',
    status: 'Reviewed',
    personId: '#091',
    location: 'Cổng A — Lối vào vành đai',
    explanation:
      'Vùng thân không khớp với đặc trưng áo phản quang (màu sắc + dải phản quang) với độ tin cậy 94.8%; người này đứng yên gần lối vào trong 12 giây.',
  },
  {
    id: 77,
    time: '11:43:02',
    camera: 'CAM-02',
    event: 'Xâm nhập khu vực hạn chế',
    confidence: 98.1,
    severity: 'critical',
    status: 'New',
    personId: '#077',
    location: 'Khu sản xuất — Khu B, vùng hạn chế 2',
    explanation: 'Tâm điểm của người đã vượt qua ranh giới ảo khu vực hạn chế mà không có sự kiện quẹt thẻ hợp lệ trong 60 giây gần nhất.',
  },
  {
    id: 112,
    time: '11:39:51',
    camera: 'CAM-03',
    event: 'Không găng tay',
    confidence: 91.4,
    severity: 'warning',
    status: 'Reviewed',
    personId: '#112',
    location: 'Sàn nhà máy — Khu C, Gian 2',
    explanation: 'Bộ phân loại vùng bàn tay không phát hiện đặc trưng kết cấu/màu sắc của găng tay với độ tin cậy 91.4% trong lúc người này vận hành máy móc.',
  },
  {
    id: 78,
    time: '11:31:08',
    camera: 'CAM-01',
    event: 'Không khẩu trang',
    confidence: 89.6,
    severity: 'warning',
    status: 'Escalated',
    personId: '#078',
    location: 'Cổng A — Lối vào vành đai',
    explanation: 'Bộ phân loại vùng mặt không phát hiện khẩu trang che phủ với độ tin cậy 89.6% tại khu vực bắt buộc đeo khẩu trang.',
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
  resolution: '1080p',
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
  powerMode: 'MAXN',
  model: 'YOLO26n-pruned',
  runtime: 'TensorRT FP16',
}

export interface ChatMessage {
  id: number
  role: 'user' | 'assistant'
  text: string
}

export const suggestedQuestions = [
  'Hiển thị các sự cố nghiêm trọng',
  'Camera nào có nhiều vi phạm nhất?',
  'Hiện có bao nhiêu người được phát hiện?',
  'Xem CAM-03',
  'Điều gì đã xảy ra trong 10 phút qua?',
]

export const initialChat: ChatMessage[] = [
  { id: 1, role: 'user', text: 'Camera nào có nhiều vi phạm nhất trong 30 phút qua?' },
  {
    id: 2,
    role: 'assistant',
    text: 'CAM-03 có số lượng vi phạm cao nhất với 5 sự cố PPE trong 30 phút qua — chủ yếu là thiếu mũ bảo hộ và găng tay tại Sàn nhà máy, Gian 2-4.',
  },
]
