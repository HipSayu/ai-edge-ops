export interface Camera {
	id: string
	name: string
	zone: string
	deviceId: string | null
	online: boolean
	alertCount: number
	thumbHue: number
	runtime: { resolution: string; protocol: string; model: string; fps: number; roiZones: number; lastHeartbeat: string; streamUrl?: string }
}
export interface EdgeDevice {
	id: string; name: string; hardware: string; status: 'online' | 'degraded' | 'offline'; ip: string
	agentVersion: string; uptime: string; cpuUsage: number; gpuUsage: number; ramUsedGb: number; ramTotalGb: number
	diskUsage: number; tempC: number; assignedCameras: number; modelRunning: string; lastHeartbeat: string
}
export interface CameraGroup {
	id: string; name: string; description: string; site: string; cameraIds: string[]; totalCameras: number
	onlineCameras: number; activeAlerts: number; aggregateFps: number; primaryModel: string
}
export type BackendDevice = {
	device_id: string; name: string; site: string; labels: Record<string, string>
	desired_image: string | null; cameras: unknown[]; inference: Record<string, unknown>
	agent_config: Record<string, unknown>; known: boolean
	status: 'online' | 'degraded' | 'offline' | 'provisioning'; last_seen_at: string | null
	agent_version: string | null; ip_address: string | null; uptime_s: number | null
	backend: string | null; arch: string | null; active_image: string | null
	runtime_status: string; in_sync: boolean
}
export type BackendMetricSample = {
	recorded_at: string
	cpu_percent: number | null; gpu_percent: number | null; mem_percent: number | null
	mem_used_mb: number | null; mem_total_mb: number | null; disk_percent: number | null
	temperature_c: number | null; fps: number | null; inference_latency_ms: number | null
}
export type BackendCamera = { id: number; name: string; source: string; zone: string; enabled: boolean; device_id: string | null }
export type BackendCameraGroup = { id: number; name: string; description: string | null; site: string; camera_ids: number[] }
export type CreateDevicePayload = { device_id: string; name: string; site: string; labels?: Record<string, string>; desired_image?: string | null }
