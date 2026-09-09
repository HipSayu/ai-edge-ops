export interface Camera {
	id: string
	name: string
	zone: string
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
	id: number; name: string; hardware: string; ip_address: string | null
	status: 'online' | 'degraded' | 'offline' | 'provisioning'; last_seen_at: string | null
	agent_version: string | null; uptime_s: number | null; active_image: string | null
}
export type BackendMetricSample = {
	id: number; device_id: number; recorded_at: string
	cpu_percent: number | null; gpu_percent: number | null; mem_percent: number | null
	mem_used_mb: number | null; mem_total_mb: number | null; disk_percent: number | null
	temperature_c: number | null; fps: number | null; inference_latency_ms: number | null
}
export type BackendCamera = { id: number; name: string; source: string; zone: string; enabled: boolean }
export type BackendCameraGroup = { id: number; name: string; description: string | null; site: string; camera_ids: number[] }
export type CreateDevicePayload = { name: string; site: string; hardware: string; ip_address?: string }
