import { VideoOff } from 'lucide-react'

// A cell of the wall with no camera to show: the layout keeps its shape instead of leaving a black hole.
export default function EmptySlot() {
  return (
    <div className="grid size-full place-items-center border border-line bg-panel/40 select-none">
      <div className="flex flex-col items-center gap-1.5 text-dim">
        <VideoOff size={20} className="opacity-60" />
        <span className="text-[11px] uppercase tracking-wider">Camera unavailable</span>
      </div>
    </div>
  )
}
