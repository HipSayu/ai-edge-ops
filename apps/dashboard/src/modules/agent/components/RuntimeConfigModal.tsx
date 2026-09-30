import { useState } from 'react'
import { X, Sliders, Save } from 'lucide-react'
import type { RuntimeProcess } from '@/modules/agent/types/logs'

interface Props {
  isOpen: boolean
  onClose: () => void
  runtime: RuntimeProcess | null
  nodeName: string
  onSaveConfig: (runtimeId: string, newConfig: Record<string, unknown>) => void
}

export default function RuntimeConfigModal({
  isOpen,
  onClose,
  runtime,
  nodeName,
  onSaveConfig,
}: Props) {
  const [batchSize, setBatchSize] = useState('4')
  const [queueDepth, setQueueDepth] = useState('16')
  const [accelBackend, setAccelBackend] = useState('CUDA TensorRT (FP16)')
  const [restartPolicy, setRestartPolicy] = useState('always')
  const [logLevel, setLogLevel] = useState('INFO')
  const [maxMemMb, setMaxMemMb] = useState('2048')
  const [isSaving, setIsSaving] = useState(false)

  if (!isOpen || !runtime) return null

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    setIsSaving(true)
    setTimeout(() => {
      onSaveConfig(runtime.id, {
        batchSize: Number(batchSize),
        queueDepth: Number(queueDepth),
        accelBackend,
        restartPolicy,
        logLevel,
        maxMemMb: Number(maxMemMb),
      })
      setIsSaving(false)
      onClose()
    }, 400)
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4 backdrop-blur-xs animate-in fade-in duration-150">
      <div className="w-full max-w-lg rounded-2xl border border-border bg-card overflow-hidden animate-in zoom-in-95 duration-150">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-border px-5 py-4 bg-muted/20">
          <div className="flex items-center gap-2.5">
            <div className="flex size-8 items-center justify-center rounded-lg bg-brand/10 text-brand">
              <Sliders size={16} />
            </div>
            <div>
              <h3 className="text-sm font-bold text-foreground">Configure Runtime Process</h3>
              <p className="text-[11px] text-muted-foreground">{runtime.name} on [{nodeName}]</p>
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
        <form onSubmit={handleSubmit} className="p-5 flex flex-col gap-4 text-xs">
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-[11px] font-semibold text-muted-foreground tracking-wider mb-1.5">
                Batch Size
              </label>
              <select
                value={batchSize}
                onChange={(e) => setBatchSize(e.target.value)}
                className="w-full h-9 rounded-lg border border-border bg-muted/30 px-3 font-mono text-foreground outline-none focus:border-brand font-medium"
              >
                <option value="1">Batch 1 (Ultra-low Latency)</option>
                <option value="2">Batch 2 (Dual Stream Sync)</option>
                <option value="4">Batch 4 (Recommended Standard)</option>
                <option value="8">Batch 8 (High Throughput)</option>
                <option value="16">Batch 16 (Max Pipeline Load)</option>
              </select>
            </div>

            <div>
              <label className="block text-[11px] font-semibold text-muted-foreground tracking-wider mb-1.5">
                Queue Buffer Depth
              </label>
              <select
                value={queueDepth}
                onChange={(e) => setQueueDepth(e.target.value)}
                className="w-full h-9 rounded-lg border border-border bg-muted/30 px-3 font-mono text-foreground outline-none focus:border-brand font-medium"
              >
                <option value="4">4 Frames (Low Memory Footprint)</option>
                <option value="8">8 Frames (Balanced)</option>
                <option value="16">16 Frames (Smooth - Recommended)</option>
                <option value="32">32 Frames (Zero-drop Ring Buffer)</option>
              </select>
            </div>
          </div>

          <div>
            <label className="block text-[11px] font-semibold text-muted-foreground tracking-wider mb-1.5">
              Hardware Acceleration Engine
            </label>
            <select
              value={accelBackend}
              onChange={(e) => setAccelBackend(e.target.value)}
              className="w-full h-9 rounded-lg border border-border bg-muted/30 px-3 text-foreground outline-none focus:border-brand font-semibold"
            >
              <option value="CUDA TensorRT (FP16)">NVIDIA TensorRT Engine (FP16 Precision) - Best</option>
              <option value="CUDA TensorRT (INT8)">NVIDIA TensorRT Engine (INT8 Quantized) - Max FPS</option>
              <option value="CUDA PyTorch (FP32)">CUDA PyTorch Backend (FP32)</option>
              <option value="OpenVINO (Intel)">Intel OpenVINO Toolkit (GPU/VPU)</option>
              <option value="CPU Multithreading">CPU Native SIMD (AVX-512)</option>
            </select>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-[11px] font-semibold text-muted-foreground tracking-wider mb-1.5">
                Restart Policy
              </label>
              <select
                value={restartPolicy}
                onChange={(e) => setRestartPolicy(e.target.value)}
                className="w-full h-9 rounded-lg border border-border bg-muted/30 px-3 text-foreground outline-none focus:border-brand font-medium"
              >
                <option value="always">Always Restart</option>
                <option value="on-failure">On Failure Only</option>
                <option value="never">Manual Restart</option>
              </select>
            </div>

            <div>
              <label className="block text-[11px] font-semibold text-muted-foreground tracking-wider mb-1.5">
                Log Verbosity
              </label>
              <select
                value={logLevel}
                onChange={(e) => setLogLevel(e.target.value)}
                className="w-full h-9 rounded-lg border border-border bg-muted/30 px-3 font-mono font-bold text-foreground outline-none focus:border-brand"
              >
                <option value="DEBUG">DEBUG (Verbose Trace)</option>
                <option value="INFO">INFO (Standard)</option>
                <option value="WARN">WARN (Warnings Only)</option>
                <option value="ERROR">ERROR (Errors Only)</option>
              </select>
            </div>
          </div>

          <div>
            <label className="block text-[11px] font-semibold text-muted-foreground tracking-wider mb-1.5">
              Process Memory Limit (MB)
            </label>
            <input
              type="number"
              min={256}
              max={16384}
              step={256}
              value={maxMemMb}
              onChange={(e) => setMaxMemMb(e.target.value)}
              className="w-full h-9 rounded-lg border border-border bg-muted/30 px-3 font-mono text-foreground outline-none focus:border-brand"
            />
          </div>

          {/* Footer */}
          <div className="flex items-center justify-end gap-2.5 pt-2 border-t border-border mt-2">
            <button
              type="button"
              onClick={onClose}
              className="rounded-lg border border-border px-4 py-2 text-xs font-semibold text-muted-foreground hover:bg-muted hover:text-foreground transition-colors cursor-pointer"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSaving}
              className="flex items-center gap-1.5 rounded-lg bg-brand px-4 py-2 text-xs font-bold text-white hover:opacity-90 transition-opacity disabled:opacity-50 cursor-pointer"
            >
              <Save size={14} />
              <span>{isSaving ? 'Applying Config...' : 'Apply & Restart'}</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
