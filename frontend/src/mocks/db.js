/**
 * Dữ liệu giả dựng lại đúng BỘ DỮ LIỆU MẪU CHUẨN (CLAUDE.md §0.2f) — không bịa số mới.
 *
 * - 12.045 chu kỳ, mỗi chu kỳ 3 bản ghi, riêng chu kỳ 17:29:54 thiếu độ ẩm → 36.134 bản ghi.
 * - 20 chu kỳ mới nhất đổi ngược từ toạ độ đường vẽ của docs/wireframe/01-dashboard.html,
 *   nên biểu đồ, bảng và thẻ số liệu khớp bản vẽ tới từng con số.
 * - Các chu kỳ cũ hơn là số tổng hợp, được chỉnh để bộ lọc mẫu
 *   "room01_temp, giá trị ≥ 28, ngày 17/08" ra đúng 1.284 bản ghi.
 * - Hai đồng hồ ảo chạy từ lúc tải trang: số đo mới tiếp nối 17:30:02, còn lệnh điều khiển mới
 *   tiếp nối 17:31:45 — sau lệnh id 88 (17:31:44) — để lệnh vừa bấm luôn đứng đầu bảng lịch sử.
 */

const BOOT = Date.now()
const CYCLE_MS = 2000
const NEWEST_T = Date.parse('2026-08-17T10:30:02.451Z') // 17:30:02 giờ Việt Nam
const TOTAL_CYCLES = 12045
const WINDOW_START = TOTAL_CYCLES - 20
const MISSING_HUMI_CYCLE = TOTAL_CYCLES - 5 // 17:29:54 — DHT11 đọc lỗi độ ẩm (UC-07 A2)
const SAMPLE_FILTER_MATCHES = 1284
export const TIMEOUT_MS = 5000 // BR-03; vòng quét 1 giây → thực tế 5–6 giây
const TIMEOUT_MESSAGE = 'Timeout: không nhận được device_respond trong 5 giây'

const iso = (t) => new Date(t).toISOString()
const round1 = (v) => Math.round(v * 10) / 10

/* ======================= Danh mục cảm biến ======================= */

export const SENSORS = [
  { id: 1, code: 'room01_temp', name: 'Nhiệt độ phòng', metric_type: 'TEMPERATURE', unit: '°C', node_id: 'esp8266_room01', key: 'temperature' },
  { id: 2, code: 'room01_humi', name: 'Độ ẩm phòng', metric_type: 'HUMIDITY', unit: '%', node_id: 'esp8266_room01', key: 'humidity' },
  { id: 3, code: 'room01_lux', name: 'Ánh sáng phòng', metric_type: 'LIGHT', unit: 'lux', node_id: 'esp8266_room01', key: 'light' },
]
const SENSOR_BY_ID = new Map(SENSORS.map((s) => [s.id, s]))

export const sensorById = (id) => SENSOR_BY_ID.get(id)
export const sensorByCode = (code) => SENSORS.find((s) => s.code === code) ?? null
export const sensorCatalog = () =>
  SENSORS.map(({ id, code, name, metric_type, unit, node_id }) => ({ id, code, name, metric_type, unit, node_id }))

/* ======================= Số đo ======================= */

// Toạ độ y của 3 polyline trong 01-dashboard.html (x = 48 → 671, mỗi bước một chu kỳ).
// Trục trái: y 356 → 20 ứng với 20 → 100; trục phải: y 356 → 20 ứng với 0 → 500 lux.
const WINDOW_Y = {
  temperature: [324.1, 323.2, 322.8, 322, 322.4, 321.6, 320.7, 321.1, 320.3, 319.9, 320.7, 321.1, 320.3, 319.5, 319.9, 320.7, 320.3, 319.9, 320.3, 320.3],
  humidity: [145.2, 143.9, 142.6, 141.8, 140.1, 128.4, 105.7, 82.6, 69.1, 77.1, 95.6, 111.6, 123.3, 130.9, 135.5, null, 138.4, 139.3, 138, 137.6],
  light: [119.5, 121.5, 120.1, 122.1, 120.8, 122.8, 124.8, 275.4, 294.2, 296.9, 292.2, 235, 154.4, 126.8, 121.5, 119.5, 120.8, 122.1, 120.1, 120.8],
}
const leftAxis = (y) => round1(20 + ((356 - y) * 80) / 336)
const rightAxis = (y) => Math.round(((356 - y) * 500) / 336)

const windowValues = (i) => ({
  temperature: leftAxis(WINDOW_Y.temperature[i]),
  humidity: WINDOW_Y.humidity[i] == null ? null : leftAxis(WINDOW_Y.humidity[i]),
  light: rightAxis(WINDOW_Y.light[i]),
})

// Số chu kỳ ≥ 28 °C cần thêm ngay trước cửa sổ 20 chu kỳ để bộ lọc mẫu ra đúng 1.284.
const HOT_CYCLES_BEFORE_WINDOW =
  SAMPLE_FILTER_MATCHES - WINDOW_Y.temperature.filter((y) => leftAxis(y) >= 28).length

function syntheticValues(c) {
  const hot = c >= WINDOW_START - HOT_CYCLES_BEFORE_WINDOW
  return {
    temperature: hot
      ? round1(28 + 0.6 * Math.abs(Math.sin(c / 9)))
      : round1(26.2 + 1.2 * Math.sin(c / 300) + 0.3 * Math.sin(c / 7)), // luôn < 28
    humidity: round1(70 + 6 * Math.sin(c / 250) + 1.5 * Math.sin(c / 11)),
    light: Math.round(330 + 40 * Math.sin(c / 400) + 10 * Math.sin(c / 13)),
  }
}

export const sensorRows = [] // { id, sensor_id, value, t, recorded_at } — tăng dần theo id
export const cycles = [] // { t, recorded_at, temperature, humidity, light }
let nextReadingId = 1

function pushCycle(t, values) {
  const recorded_at = iso(t) // một mốc thời gian chung cho cả chu kỳ (BR-11)
  for (const sensor of SENSORS) {
    const value = values[sensor.key]
    if (value == null) continue // không đo được thì không có dòng
    sensorRows.push({ id: nextReadingId++, sensor_id: sensor.id, value, t, recorded_at })
  }
  cycles.push({ t, recorded_at, ...values })
}

for (let c = 0; c < TOTAL_CYCLES; c++) {
  const values = c >= WINDOW_START ? windowValues(c - WINDOW_START) : syntheticValues(c)
  if (c === MISSING_HUMI_CYCLE) values.humidity = null
  pushCycle(NEWEST_T - (TOTAL_CYCLES - 1 - c) * CYCLE_MS, values)
}

export const serializeReading = (row) => {
  const s = SENSOR_BY_ID.get(row.sensor_id)
  return {
    id: row.id,
    sensor: { id: s.id, code: s.code, name: s.name, unit: s.unit },
    value: row.value,
    recorded_at: row.recorded_at,
  }
}

export function latestReadings() {
  const result = []
  for (const sensor of SENSORS) {
    for (let i = sensorRows.length - 1; i >= 0; i--) {
      if (sensorRows[i].sensor_id !== sensor.id) continue
      const { sensor: brief, value, recorded_at } = serializeReading(sensorRows[i])
      result.push({ sensor: brief, value, recorded_at })
      break
    }
  }
  return result
}

export const chartCycles = (limit) =>
  cycles.slice(-limit).map(({ recorded_at, temperature, humidity, light }) => ({ recorded_at, temperature, humidity, light }))

let liveCycleCount = 0
const walk = (value, step, min, max, digits) => {
  const next = Math.min(max, Math.max(min, value + (Math.random() * 2 - 1) * step))
  return digits === 0 ? Math.round(next) : round1(next)
}

export function appendLiveCycle() {
  const last = cycles[cycles.length - 1]
  liveCycleCount += 1
  const t = NEWEST_T + liveCycleCount * CYCLE_MS
  const values = {
    temperature: walk(last.temperature, 0.15, 24, 34, 1),
    humidity: walk(last.humidity ?? 72, 0.4, 50, 90, 1),
    light: walk(last.light, 4, 60, 600, 0),
  }
  pushCycle(t, values)
  return { type: 'sensor.data', device_id: 'esp8266_room01', ...values, recorded_at: iso(t) }
}

/* ======================= Người dùng + token ======================= */

// Mật khẩu trùng dữ liệu khởi tạo ở 04-Database.md §10.
const USERS = [
  { id: 1, username: 'admin', password: 'doi-mat-khau-nay', full_name: 'Lưu Đức Anh', role: 'ADMIN', is_active: true },
  { id: 2, username: 'operator', password: 'doi-mat-khau-nay', full_name: 'Người vận hành', role: 'OPERATOR', is_active: true },
]

// Lưu token giả vào localStorage để tải lại trang không bị đăng xuất.
const TOKEN_STORE = 'room01.mock.tokens'
let tokens = (() => {
  try {
    return JSON.parse(localStorage.getItem(TOKEN_STORE)) || {}
  } catch {
    return {}
  }
})()
const saveTokens = () => {
  try {
    localStorage.setItem(TOKEN_STORE, JSON.stringify(tokens))
  } catch {
    /* bỏ qua */
  }
}
const randomHex = (length) =>
  Array.from(crypto.getRandomValues(new Uint8Array(length / 2)), (b) => b.toString(16).padStart(2, '0')).join('')

export const authenticate = (username, password) =>
  USERS.find((u) => u.username === username && u.password === password && u.is_active) ?? null

// Mỗi người dùng một token, đăng nhập lại trả đúng token cũ (get_or_create — 05-API.md §4.8).
export function tokenFor(user) {
  const existing = Object.keys(tokens).find((key) => tokens[key] === user.id)
  if (existing) return existing
  const key = randomHex(40)
  tokens[key] = user.id
  saveTokens()
  return key
}

export function userByToken(key) {
  if (!key || !(key in tokens)) return null
  const user = USERS.find((u) => u.id === tokens[key])
  return user?.is_active ? user : null
}

export function revokeToken(key) {
  delete tokens[key]
  saveTokens()
}

export const loginUser = (u) => ({ id: u.id, username: u.username, full_name: u.full_name, role: u.role })
const userBrief = (id) => {
  const u = USERS.find((x) => x.id === id)
  return u ? { id: u.id, full_name: u.full_name } : null
}

/* ======================= Thiết bị + lịch sử thao tác ======================= */

// Dashboard lúc 17:30:02: đèn OFF (lệnh thành công cuối: id 84), quạt ON (id 87).
export const devices = [
  { id: 1, code: 'room01_lamp', name: 'Đèn phòng', device_type: 'LIGHT', node_id: 'esp8266_room01', gpio_pin: 'D5', current_state: 'OFF', updated_at: '2026-08-17T10:15:33.921Z' },
  { id: 2, code: 'room01_fan', name: 'Quạt trần', device_type: 'FAN', node_id: 'esp8266_room01', gpio_pin: 'D6', current_state: 'ON', updated_at: '2026-08-17T10:28:07.884Z' },
]

const vn = (hms, ms = 500) => Date.parse(`2026-08-17T${hms}.${String(ms).padStart(3, '0')}+07:00`)
const syntheticRequestId = (id) => `00000000-0000-4000-8000-${id.toString(16).padStart(12, '0')}`

// [id, thiết bị, lệnh, người, kết quả, giờ VN, độ trễ ms, phần nghìn giây của created_at]
const KNOWN_ACTIONS = [
  [79, 2, 'OFF', null, 'SUCCESS', '16:55:07', 421], // user null — BR-12
  [80, 1, 'ON', 1, 'SUCCESS', '16:58:12', 396],
  [81, 1, 'OFF', 1, 'SUCCESS', '17:02:40', 377],
  [82, 2, 'ON', 2, 'SUCCESS', '17:08:51', 443],
  [83, 1, 'ON', 1, 'SUCCESS', '17:12:19', 401],
  [84, 1, 'OFF', 2, 'SUCCESS', '17:15:33', 388, 533],
  [85, 2, 'OFF', 2, 'SUCCESS', '17:17:26', 455],
  [86, 2, 'ON', 1, 'FAILED', '17:20:02', 5523, 117],
  [87, 2, 'ON', 1, 'SUCCESS', '17:28:07', 412, 472],
  [88, 1, 'ON', 1, 'PENDING', '17:31:44', null, 902],
]
const KNOWN_REQUEST_IDS = {
  86: 'b7c1d2e3-1122-4a5b-9c8d-77e6f5a4b3c2',
  87: '9d4e5f60-7a8b-4c1d-9e2f-3a4b5c6d7e8f',
  88: '3f2b8c1e-9a4d-4f7b-8c21-0e5d6a7b8c90',
}

export const actions = []

;(function seedActions() {
  const start = vn('08:05:00')
  const step = (vn('16:50:00') - start) / 77
  const state = { 1: 'OFF', 2: 'OFF' }
  const lastSuccess = {}

  for (let id = 1; id <= 78; id++) {
    const deviceId = id % 3 === 0 ? 2 : (id % 2) + 1
    const failed = id === 23 || id === 57
    const action = state[deviceId] === 'ON' ? 'OFF' : 'ON'
    const created = Math.floor((start + step * (id - 1)) / 1000) * 1000 + 500
    const latency = failed ? 5000 + ((id * 37) % 900) : 370 + ((id * 53) % 90)
    const record = {
      id,
      device_id: deviceId,
      action,
      user_id: id % 4 === 0 ? 2 : 1,
      status: failed ? 'FAILED' : 'SUCCESS',
      error_message: failed ? TIMEOUT_MESSAGE : null,
      request_id: syntheticRequestId(id),
      created_at: created,
      responded_at: created + latency,
      deadline: null,
    }
    actions.push(record)
    if (!failed) {
      state[deviceId] = action
      lastSuccess[deviceId] = record
    }
  }
  // Nối mạch với chuỗi 79→88: trước đó quạt đang ON (79 tắt quạt), đèn đang OFF (80 bật đèn).
  lastSuccess[2].action = 'ON'
  lastSuccess[1].action = 'OFF'

  for (const [id, deviceId, action, userId, status, hms, latency, ms] of KNOWN_ACTIONS) {
    const created = vn(hms, ms ?? 500)
    actions.push({
      id,
      device_id: deviceId,
      action,
      user_id: userId,
      status,
      error_message: status === 'FAILED' ? TIMEOUT_MESSAGE : null,
      request_id: KNOWN_REQUEST_IDS[id] ?? syntheticRequestId(id),
      created_at: created,
      responded_at: latency == null ? null : created + latency,
      // id 88 đang PENDING trong bộ dữ liệu mẫu → hết giờ sau 5–6 giây kể từ lúc tải trang
      deadline: status === 'PENDING' ? BOOT + TIMEOUT_MS : null,
    })
  }
})()

let nextActionId = 89
// Lệnh id 88 lúc 17:31:44 là mốc muộn nhất của bộ dữ liệu mẫu; lệnh mới phải đứng sau nó.
const actionNow = () => vn('17:31:45') + (Date.now() - BOOT)

export function serializeAction(a) {
  const device = devices.find((d) => d.id === a.device_id)
  return {
    id: a.id,
    device: { id: device.id, code: device.code, name: device.name },
    action: a.action,
    user: a.user_id == null ? null : userBrief(a.user_id),
    status: a.status,
    error_message: a.error_message,
    request_id: a.request_id,
    created_at: iso(a.created_at),
    responded_at: a.responded_at == null ? null : iso(a.responded_at),
    latency_ms: a.responded_at == null ? null : a.responded_at - a.created_at,
  }
}

export const isBusy = (deviceId) => actions.some((a) => a.device_id === deviceId && a.status === 'PENDING')

export function createAction(device, action, user) {
  const record = {
    id: nextActionId++,
    device_id: device.id,
    action,
    user_id: user.id, // lấy từ token, không từ thân yêu cầu (05-API.md §4.5)
    status: 'PENDING',
    error_message: null,
    request_id: crypto.randomUUID(),
    created_at: actionNow(),
    responded_at: null,
    deadline: Date.now() + TIMEOUT_MS,
  }
  actions.push(record)
  return record
}

const deviceStateEvent = (a, d) => ({
  type: 'device.state',
  device_id: d.id,
  device: d.code,
  current_state: d.current_state,
  request_id: a.request_id,
  status: a.status,
  error_message: a.error_message,
})

// Mô phỏng ESP8266 gửi device_respond. Chỉ đổi current_state khi SUCCESS.
export function completeAction(id) {
  const record = actions.find((a) => a.id === id)
  if (!record || record.status !== 'PENDING') return null
  const device = devices.find((d) => d.id === record.device_id)
  record.status = 'SUCCESS'
  record.responded_at = actionNow()
  record.deadline = null
  device.current_state = record.action
  device.updated_at = iso(record.responded_at)
  return deviceStateEvent(record, device)
}

// Vòng quét timeout mỗi giây (SD-05). FAILED thì current_state giữ nguyên.
export function sweepTimeouts() {
  const now = Date.now()
  const events = []
  for (const record of actions) {
    if (record.status !== 'PENDING' || record.deadline == null || now < record.deadline) continue
    const device = devices.find((d) => d.id === record.device_id)
    record.status = 'FAILED'
    record.error_message = TIMEOUT_MESSAGE
    record.responded_at = record.created_at + (now - (record.deadline - TIMEOUT_MS))
    record.deadline = null
    events.push(deviceStateEvent(record, device))
  }
  return events
}

/* ======================= Profile ======================= */

export const PROFILE = {
  student: {
    full_name: 'Lưu Đức Anh',
    student_id: 'B23DCAT011',
    class_name: 'D23CQAT01-B',
    email: 'ducanhyeutoan@gmail.com',
    avatar_url: null,
  },
  project: {
    title: 'Hệ thống giám sát và điều khiển môi trường phòng dựa trên IoT',
    subject: 'IoT & Ứng dụng',
    supervisor: 'TS. Nguyễn Quốc Uy',
  },
  links: {
    github: 'https://github.com/B23DCAT011/IOT',
    report_pdf: 'https://github.com/B23DCAT011/IOT/blob/main/docs/BaoCao.pdf',
    figma: 'https://www.figma.com/design/2oR8lFM04tyK7kjpxGrILX/Untitled?node-id=0-1',
    api_docs: 'http://localhost:8000/api/schema/swagger-ui/',
  },
}
