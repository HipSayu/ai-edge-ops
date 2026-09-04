export interface Camera {
  id: string
  name: string
  zone: string
  online: boolean
  alertCount: number
  thumbHue: number
  runtime: {
    resolution: string
    protocol: string
    model: string
    fps: number
    roiZones: number
    lastHeartbeat: string
  }
}

export const mockCameras: Camera[] = [
  {
    id: 'CAM-01',
    name: 'Cổng A',
    zone: 'Vành đai',
    online: true,
    alertCount: 2,
    thumbHue: 205,
    runtime: { resolution: '1920×1080', protocol: 'RTSP/H.264', model: 'YOLO26n-pruned', fps: 30, roiZones: 1, lastHeartbeat: '2s trước' },
  },
  {
    id: 'CAM-02',
    name: 'Khu sản xuất',
    zone: 'Khu B',
    online: true,
    alertCount: 0,
    thumbHue: 165,
    runtime: { resolution: '1920×1080', protocol: 'RTSP/H.264', model: 'YOLO26n-pruned', fps: 30, roiZones: 2, lastHeartbeat: '1s trước' },
  },
  {
    id: 'CAM-03',
    name: 'Sàn nhà máy',
    zone: 'Khu C',
    online: true,
    alertCount: 5,
    thumbHue: 20,
    runtime: { resolution: '1920×1080', protocol: 'RTSP/H.264', model: 'YOLO26n-pruned', fps: 28, roiZones: 3, lastHeartbeat: '1s trước' },
  },
  {
    id: 'CAM-04',
    name: 'Kho hàng',
    zone: 'Khu lưu trữ',
    online: true,
    alertCount: 0,
    thumbHue: 260,
    runtime: { resolution: '1280×720', protocol: 'RTSP/H.265', model: 'YOLO26n-pruned', fps: 25, roiZones: 0, lastHeartbeat: '3s trước' },
  },
  {
    id: 'CAM-05',
    name: 'Khu vực hạn chế',
    zone: 'Khu D',
    online: false,
    alertCount: 0,
    thumbHue: 0,
    runtime: { resolution: '1920×1080', protocol: 'RTSP/H.264', model: 'YOLO26n-pruned', fps: 0, roiZones: 1, lastHeartbeat: '14 phút trước' },
  },
]
