export const formatTime = (iso: string) => new Date(iso).toLocaleTimeString('vi-VN')

export const formatPercent = (ratio: number) => `${Math.round(ratio * 100)}%`
