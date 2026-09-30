import { useState } from 'react'
import { X, Rocket, Sliders, Check } from 'lucide-react'

interface ModelOption {
  id: string
  name: string
  tag: string
  latency: string
  fps: string
  size: string
  recommendedPrecision: string
}

const AVAILABLE_MODELS: ModelOption[] = [
  {
    id: 'yolov8n-safety',
    name: 'YOLOv8n Safety PPE',
    tag: 'yolov8n-safety:v2.4.0',
    latency: '8.2 ms',
    fps: '122 FPS',
    size: '6.2 MB',
    recommendedPrecision: 'FP16',
  },
  {
    id: 'yolov8s-ppe',
    name: 'YOLOv8s Multi-Zone Guard',
    tag: 'yolov8s-guard:v2.1.0',
    latency: '14.5 ms',
    fps: '68 FPS',
    size: '22.5 MB',
    recommendedPrecision: 'FP16',
  },
  {
    id: 'yolov8-pose',
    name: 'YOLOv8x Worker Pose & Fall',
    tag: 'yolov8x-pose:v1.9.0',
    latency: '24.1 ms',
    fps: '41 FPS',
    size: '68.2 MB',
    recommendedPrecision: 'FP16',
  },
  {
    id: 'yolov11n-detect',
    name: 'YOLO11n Edge Detector',
    tag: 'yolo11n-core:latest',
    latency: '7.1 ms',
    fps: '140 FPS',
    size: '5.4 MB',
    recommendedPrecision: 'INT8',
  },
]

interface Props {
  isOpen: boolean
  onClose: () => void
  nodeId?: string
  nodeName: string
  currentModel?: string
  onDeploy: (payload: {
    nodeId: string
    modelName: string
    tag: string
    precision: string
    confidenceThreshold: number
  }) => void
}

export default function ModelDeploymentModal({
  isOpen,
  onClose,
  nodeId,
  nodeName,
  onDeploy,
}: Props) {
  const [selectedModelId, setSelectedModelId] = useState(AVAILABLE_MODELS[0].id)
  const [precision, setPrecision] = useState('FP16')
  const [confThreshold, setConfThreshold] = useState(0.5)
  const [iouThreshold, setIouThreshold] = useState(0.45)
  const [inputResolution, setInputResolution] = useState('640x640')
  const [rolloutStrategy, setRolloutStrategy] = useState('hot-swap')
  const [isDeploying, setIsDeploying] = useState(false)

  if (!isOpen) return null

  const selectedModel = AVAILABLE_MODELS.find((m) => m.id === selectedModelId) || AVAILABLE_MODELS[0]

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    setIsDeploying(true)

    setTimeout(() => {
      onDeploy({
        nodeId: nodeId || 'node-01',
        modelName: selectedModel.name,
        tag: selectedModel.tag,
        precision,
        confidenceThreshold: confThreshold,
      })
      setIsDeploying(false)
      onClose()
    }, 600)
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4 backdrop-blur-xs animate-in fade-in duration-150">
      <div className="w-full max-w-xl rounded-2xl border border-border bg-card overflow-hidden animate-in zoom-in-95 duration-150">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-border px-5 py-4 bg-muted/20">
          <div className="flex items-center gap-2.5">
            <div className="flex size-8 items-center justify-center rounded-lg bg-purple-500/10 text-purple-500">
              <Rocket size={16} />
            </div>
            <div>
              <h3 className="text-sm font-bold text-foreground">Deploy Vision AI Model</h3>
              <p className="text-[11px] text-muted-foreground">Flash neural weights onto [{nodeName}] Vision Runtime</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="rounded-md p-1 text-muted-foreground hover:bg-muted hover:text-foreground transition-colors cursor-pointer"
          >
            <X size={16} />
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="p-5 flex flex-col gap-4 text-xs max-h-[80vh] overflow-y-auto">
          {/* Model Catalog */}
          <div>
            <label className="block text-[11px] font-semibold text-muted-foreground tracking-wider mb-2">
              Select Model from Model Zoo
            </label>
            <div className="grid gap-2 sm:grid-cols-2">
              {AVAILABLE_MODELS.map((model) => {
                const isSelected = selectedModelId === model.id
                return (
                  <div
                    key={model.id}
                    onClick={() => setSelectedModelId(model.id)}
                    className={`flex flex-col justify-between rounded-xl border p-3 cursor-pointer transition-all ${
                      isSelected
                        ? 'border-brand bg-brand/5'
                        : 'border-border bg-muted/20 hover:border-brand/40 hover:bg-muted/40'
                    }`}
                  >
                    <div>
                      <div className="flex items-start justify-between gap-1">
                        <span className="font-bold text-foreground text-xs">{model.name}</span>
                        {isSelected && <Check size={14} className="text-brand shrink-0" />}
                      </div>
                      <span className="font-mono text-[10px] text-muted-foreground mt-0.5 block">{model.tag}</span>
                    </div>

                    <div className="mt-2.5 flex items-center justify-between border-t border-border/50 pt-2 text-[10.5px]">
                      <span className="text-info font-semibold">{model.latency}</span>
                      <span className="text-success font-bold font-mono">{model.fps}</span>
                      <span className="text-muted-foreground">{model.size}</span>
                    </div>
                  </div>
                )
              })}
            </div>
          </div>

          {/* Inference Hyperparameters */}
          <div className="rounded-xl border border-border bg-muted/15 p-4 flex flex-col gap-3.5">
            <div className="flex items-center gap-1.5 font-bold text-foreground text-[11.5px]">
              <Sliders size={13} className="text-brand" />
              <span>Inference Parameters &amp; Engine</span>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-[10.5px] font-semibold text-muted-foreground mb-1">
                  TensorRT Precision
                </label>
                <select
                  value={precision}
                  onChange={(e) => setPrecision(e.target.value)}
                  className="w-full h-8 rounded-lg border border-border bg-background px-2.5 text-xs text-foreground outline-none focus:border-brand font-semibold"
                >
                  <option value="FP16">FP16 (Recommended - Balanced)</option>
                  <option value="INT8">INT8 Quantization (Max FPS)</option>
                  <option value="FP32">FP32 (Original Precision)</option>
                </select>
              </div>

              <div>
                <label className="block text-[10.5px] font-semibold text-muted-foreground mb-1">
                  Input Frame Resolution
                </label>
                <select
                  value={inputResolution}
                  onChange={(e) => setInputResolution(e.target.value)}
                  className="w-full h-8 rounded-lg border border-border bg-background px-2.5 font-mono text-xs text-foreground outline-none focus:border-brand font-semibold"
                >
                  <option value="640x640">640 × 640 (Standard)</option>
                  <option value="480x480">480 × 480 (High Speed)</option>
                  <option value="1280x1280">1280 × 1280 (Small Objects / Far-field)</option>
                </select>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <div className="flex justify-between text-[11px] mb-1">
                  <span className="text-muted-foreground font-semibold">Confidence Threshold</span>
                  <span className="font-mono font-bold text-brand">{confThreshold.toFixed(2)}</span>
                </div>
                <input
                  type="range"
                  min="0.10"
                  max="0.95"
                  step="0.05"
                  value={confThreshold}
                  onChange={(e) => setConfThreshold(parseFloat(e.target.value))}
                  className="w-full accent-brand cursor-pointer"
                />
              </div>

              <div>
                <div className="flex justify-between text-[11px] mb-1">
                  <span className="text-muted-foreground font-semibold">IoU / NMS Threshold</span>
                  <span className="font-mono font-bold text-purple-400">{iouThreshold.toFixed(2)}</span>
                </div>
                <input
                  type="range"
                  min="0.20"
                  max="0.80"
                  step="0.05"
                  value={iouThreshold}
                  onChange={(e) => setIouThreshold(parseFloat(e.target.value))}
                  className="w-full accent-purple-500 cursor-pointer"
                />
              </div>
            </div>

            <div>
              <label className="block text-[10.5px] font-semibold text-muted-foreground mb-1">
                Rollout Strategy
              </label>
              <select
                value={rolloutStrategy}
                onChange={(e) => setRolloutStrategy(e.target.value)}
                className="w-full h-8 rounded-lg border border-border bg-background px-2.5 text-xs text-foreground outline-none focus:border-brand font-medium"
              >
                <option value="hot-swap">Immediate Hot-swap (In-memory VRAM Flash)</option>
                <option value="blue-green">Zero-downtime Blue/Green Process</option>
                <option value="gradual">Canary Deployment (Single Camera Pilot)</option>
              </select>
            </div>
          </div>

          {/* Footer */}
          <div className="flex items-center justify-end gap-2.5 pt-2 border-t border-border mt-1">
            <button
              type="button"
              onClick={onClose}
              className="rounded-lg border border-border px-4 py-2 text-xs font-semibold text-muted-foreground hover:bg-muted hover:text-foreground transition-colors cursor-pointer"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isDeploying}
              className="flex items-center gap-1.5 rounded-lg bg-purple-600 px-4 py-2 text-xs font-bold text-white hover:opacity-90 transition-opacity disabled:opacity-50 cursor-pointer"
            >
              <Rocket size={14} />
              <span>{isDeploying ? 'Deploying TensorRT Engine...' : `Deploy ${selectedModel.name.split(' (')[0]}`}</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
