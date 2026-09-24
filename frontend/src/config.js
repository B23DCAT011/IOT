export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api'
export const WS_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000/ws/realtime/'
export const USE_MOCK = import.meta.env.VITE_USE_MOCK === 'true'

export const CHART_POINTS = 20 // BR-10
export const PAGE_SIZE = 10 // BR-08 — mặc định
// Cho chọn từ danh sách cố định thay vì gõ tay: page_size sai kiểu bị DRF im lặng bỏ qua
// (05-API.md §7.1, ca A-05), và mọi ví dụ trong tài liệu tính theo 10 dòng/trang.
export const PAGE_SIZE_OPTIONS = [8, 10, 12, 20]
export const OFFLINE_AFTER_MS = 30_000 // BR-07
export const WS_RETRY_MS = 5_000 // 05-API.md §5.4 quy tắc 2
export const CONTROL_FALLBACK_MS = 7_000 // 05-API.md §5.4 quy tắc 5
export const WS_CLOSE_UNAUTHORIZED = 4401 // 05-API.md §5.1
