// Khóa của biểu đồ và sự kiện sensor.data là metric_type viết thường (05-API.md §4.2, §5.2).
export const METRIC_KEYS = ['temperature', 'humidity', 'light']
export const metricKey = (metricType) => metricType.toLowerCase()

export const METRIC_COLOR = {
  temperature: '#C0492F',
  humidity: '#1C7B8E',
  light: '#C98A16',
}

// API không trả nhãn tiếng Việt cho enum — Frontend tự giữ (05-API.md §2.3).
export const ROLE_LABEL = {
  ADMIN: 'Quản trị',
  OPERATOR: 'Người vận hành',
  VIEWER: 'Chỉ xem',
}

export const STATUS_OPTIONS = ['PENDING', 'SUCCESS', 'FAILED']
export const ACTION_OPTIONS = ['ON', 'OFF']
