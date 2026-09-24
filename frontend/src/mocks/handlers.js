/**
 * Giả lập backend theo đúng hợp đồng 05-API.md v2.1 — đường dẫn, tham số, mã lỗi, hình dạng JSON.
 * Mục đích: khi có Django thật chỉ cần đặt VITE_USE_MOCK=false, không sửa dòng code gọi API nào.
 *
 * Công tắc giả lập lỗi (gõ trong Console của trình duyệt rồi tải lại trang nếu cần):
 *   localStorage.setItem('room01.mock.deviceOffline', '1')  // thiết bị không phản hồi → FAILED sau 5–6 s
 *   localStorage.setItem('room01.mock.brokerDown', '1')     // POST control → 503 BROKER_UNAVAILABLE
 *   localStorage.setItem('room01.mock.sensorOffline', '1')  // ngừng sensor.data → sau 30 s báo ngoại tuyến
 *   localStorage.removeItem('room01.mock.brokerDown')       // tắt công tắc
 */
import { delay, http, HttpResponse, ws } from 'msw'
import { API_BASE_URL, WS_URL } from '../config'
import * as db from './db'

const LATENCY_MS = 120
const url = (path) => `${API_BASE_URL}${path}`

const flag = (name) => {
  try {
    return localStorage.getItem(`room01.mock.${name}`) === '1'
  } catch {
    return false
  }
}

/* ---------------- lỗi thống nhất {error:{code,message,details}} — §2.6 ---------------- */

function errorResponse(status, code, message, details = null) {
  const headers = status === 401 ? { 'WWW-Authenticate': 'Token' } : undefined
  return HttpResponse.json({ error: { code, message, details } }, { status, headers })
}
const invalid = (details) => errorResponse(400, 'VALIDATION_ERROR', 'Dữ liệu gửi lên không hợp lệ.', details)
const unauthenticated = () =>
  errorResponse(401, 'UNAUTHENTICATED', 'Bạn chưa đăng nhập hoặc phiên đăng nhập đã hết.')

function tokenOf(request) {
  const match = (request.headers.get('Authorization') || '').match(/^Token ([0-9a-f]{40})$/)
  return match ? match[1] : null
}

// Mọi endpoint trừ đăng nhập đều yêu cầu token (BR-13).
const authed = (resolver) => async (info) => {
  await delay(LATENCY_MS)
  const user = db.userByToken(tokenOf(info.request))
  if (!user) return unauthenticated()
  return resolver({ ...info, user })
}

/* ---------------- tham số truy vấn ---------------- */

function parseNumber(query, name, errors) {
  const raw = query.get(name)
  if (raw == null || raw === '') return null
  const value = Number(raw)
  if (!Number.isFinite(value)) {
    errors[name] = ['Phải là một số hợp lệ.']
    return null
  }
  return value
}

function parseDate(query, name, errors) {
  const raw = query.get(name)
  if (!raw) return null
  const value = Date.parse(raw)
  if (Number.isNaN(value)) {
    errors[name] = ['Sai định dạng thời gian ISO-8601.']
    return null
  }
  return value
}

function rangeError(field, gte, lte) {
  if (gte == null || lte == null || gte <= lte) return null
  return errorResponse(400, 'INVALID_RANGE', 'Khoảng lọc không hợp lệ.', {
    [`${field}__gte`]: ['Giá trị đầu khoảng phải nhỏ hơn hoặc bằng giá trị cuối khoảng.'],
  })
}

const compare = (x, y) => {
  if (x === y) return 0
  if (x == null) return -1
  if (y == null) return 1
  return x < y ? -1 : 1
}

// Tham số ordering + cột phá hòa để lật trang không lặp/mất dòng (05-API.md §4.3, §7.3).
function sortRows(rows, ordering, fields, fallback, tiebreakers) {
  const requested = (ordering || '').split(',')[0].trim()
  const name = requested.replace(/^-/, '')
  const [field, desc] = fields[name]
    ? [name, requested.startsWith('-')]
    : [fallback.replace(/^-/, ''), fallback.startsWith('-')]
  const get = fields[field]

  return [...rows].sort((a, b) => {
    const d = compare(get(a), get(b))
    if (d !== 0) return desc ? -d : d
    for (const tiebreak of tiebreakers) {
      const t = compare(tiebreak(a), tiebreak(b))
      if (t !== 0) return t
    }
    return 0
  })
}

// PageNumberPagination: page_size tối đa 100, sai kiểu → 400, vượt trang → 404 PAGE_NOT_FOUND (§2.8).
function paginate(requestUrl, items) {
  const pageRaw = requestUrl.searchParams.get('page') ?? '1'
  const sizeRaw = requestUrl.searchParams.get('page_size') ?? '10'
  if (!/^\d+$/.test(sizeRaw) || Number(sizeRaw) < 1) return { error: invalid({ page_size: ['Phải là số nguyên dương.'] }) }
  if (!/^\d+$/.test(pageRaw) || Number(pageRaw) < 1) return { error: invalid({ page: ['Phải là số nguyên dương.'] }) }

  const size = Math.min(Number(sizeRaw), 100)
  const page = Number(pageRaw)
  const pages = Math.max(1, Math.ceil(items.length / size))
  if (page > pages) return { error: errorResponse(404, 'PAGE_NOT_FOUND', 'Trang không tồn tại.') }

  const link = (p) => {
    const next = new URL(requestUrl)
    next.searchParams.set('page', String(p))
    return next.toString()
  }
  return {
    count: items.length,
    next: page < pages ? link(page + 1) : null,
    previous: page > 1 ? link(page - 1) : null,
    slice: items.slice((page - 1) * size, page * size),
  }
}

/* ---------------- WebSocket — §5 ---------------- */

const escapeRegExp = (text) => text.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
export const realtime = ws.link(new RegExp(`^${escapeRegExp(WS_URL)}(\\?.*)?$`))
const broadcast = (event) => realtime.broadcast(JSON.stringify(event))

const wsHandler = realtime.addEventListener('connection', ({ client }) => {
  const token = new URL(String(client.url)).searchParams.get('token')
  if (!db.userByToken(token)) {
    // Nhận kết nối rồi mới đóng mã 4401 — đóng trước khi nhận thì trình duyệt chỉ thấy 1006 (§5.1).
    setTimeout(() => client.close(4401, 'Unauthorized'), 0)
    return
  }
  client.addEventListener('message', (event) => {
    console.info('[mock ws] Bỏ qua message từ client:', event.data) // kênh một chiều
  })
})

let loopsStarted = false
export function startMockLoops() {
  if (loopsStarted) return
  loopsStarted = true
  // BR-01: ESP8266 gửi số đo 2 giây/lần
  setInterval(() => {
    if (!flag('sensorOffline')) broadcast(db.appendLiveCycle())
  }, 2000)
  // Vòng quét timeout mỗi giây (SD-05)
  setInterval(() => {
    db.sweepTimeouts().forEach(broadcast)
  }, 1000)
}

/* ---------------- REST ---------------- */

const httpHandlers = [
  // §4.8
  http.post(url('/auth/login'), async ({ request }) => {
    await delay(LATENCY_MS)
    let body = {}
    try {
      body = await request.json()
    } catch {
      /* thân rỗng */
    }
    const errors = {}
    if (typeof body.username !== 'string' || body.username === '') errors.username = ['Trường này là bắt buộc.']
    if (typeof body.password !== 'string' || body.password === '') errors.password = ['Trường này là bắt buộc.']
    if (Object.keys(errors).length) return invalid(errors)

    const user = db.authenticate(body.username, body.password)
    if (!user) return errorResponse(400, 'INVALID_CREDENTIALS', 'Tên đăng nhập hoặc mật khẩu không đúng.')
    return HttpResponse.json({ token: db.tokenFor(user), user: db.loginUser(user) })
  }),

  // §4.9
  http.post(url('/auth/logout'), async ({ request }) => {
    await delay(LATENCY_MS)
    const token = tokenOf(request)
    if (!db.userByToken(token)) return unauthenticated()
    db.revokeToken(token)
    return new HttpResponse(null, { status: 204 })
  }),

  // §4.0
  http.get(url('/sensors/devices'), authed(() => HttpResponse.json(db.sensorCatalog()))),

  // §4.1
  http.get(url('/sensors/latest'), authed(() => HttpResponse.json(db.latestReadings()))),

  // §4.2
  http.get(
    url('/sensors/chart'),
    authed(({ request }) => {
      const raw = new URL(request.url).searchParams.get('limit')
      let limit = 20
      if (raw != null) {
        if (!/^\d+$/.test(raw) || Number(raw) < 1) return invalid({ limit: ['Phải là số nguyên dương.'] })
        limit = Math.min(Number(raw), 100)
      }
      return HttpResponse.json(db.chartCycles(limit))
    }),
  ),

  // §4.3
  http.get(
    url('/sensors'),
    authed(({ request }) => {
      const requestUrl = new URL(request.url)
      const q = requestUrl.searchParams
      const errors = {}

      const sensorCode = q.get('sensor') || null
      const gte = parseNumber(q, 'value__gte', errors)
      const lte = parseNumber(q, 'value__lte', errors)
      const from = parseDate(q, 'recorded_at__gte', errors)
      const to = parseDate(q, 'recorded_at__lte', errors)
      if (!sensorCode && (q.get('value__gte') || q.get('value__lte'))) {
        const key = q.get('value__gte') ? 'value__gte' : 'value__lte'
        errors[key] = ['Phải chọn một cảm biến trước khi lọc theo khoảng giá trị.'] // UC-04 E4
      }
      if (Object.keys(errors).length) return invalid(errors)
      const badRange = rangeError('recorded_at', from, to) || rangeError('value', gte, lte)
      if (badRange) return badRange

      const sensor = sensorCode ? db.sensorByCode(sensorCode) : null
      const node = q.get('node')
      const search = (q.get('search') || '').trim().toLowerCase()

      const rows = db.sensorRows.filter((row) => {
        if (sensorCode && (!sensor || row.sensor_id !== sensor.id)) return false
        if (gte != null && row.value < gte) return false
        if (lte != null && row.value > lte) return false
        if (from != null && row.t < from) return false
        if (to != null && row.t > to) return false
        if (node && db.sensorById(row.sensor_id).node_id !== node) return false
        if (search) {
          const s = db.sensorById(row.sensor_id)
          if (!s.code.toLowerCase().includes(search) && !s.name.toLowerCase().includes(search)) return false
        }
        return true
      })

      const sorted = sortRows(
        rows,
        q.get('ordering'),
        { recorded_at: (r) => r.t, value: (r) => r.value, id: (r) => r.id },
        '-recorded_at',
        [(r) => r.sensor_id, (r) => r.id],
      )
      const page = paginate(requestUrl, sorted)
      if (page.error) return page.error
      return HttpResponse.json({
        count: page.count,
        next: page.next,
        previous: page.previous,
        results: page.slice.map(db.serializeReading),
      })
    }),
  ),

  // §4.4
  http.get(url('/devices'), authed(() => HttpResponse.json(db.devices.map((d) => ({ ...d }))))),

  // §4.5
  http.post(
    url('/devices/:id/control'),
    authed(async ({ request, params, user }) => {
      const device = db.devices.find((d) => d.id === Number(params.id))
      if (!device) return errorResponse(404, 'NOT_FOUND', 'Không tìm thấy thiết bị.')

      let body = {}
      try {
        body = await request.json()
      } catch {
        /* thân rỗng */
      }
      if (typeof body.action !== 'string' || body.action.trim() === '') {
        return invalid({ action: ['Trường này là bắt buộc.'] })
      }
      const action = body.action.trim().toUpperCase()
      if (action !== 'ON' && action !== 'OFF') return invalid({ action: ['Giá trị phải là "ON" hoặc "OFF".'] })

      if (db.isBusy(device.id)) {
        return errorResponse(
          409,
          'DEVICE_BUSY',
          'Thiết bị đang chờ phản hồi cho lệnh trước đó, vui lòng thử lại sau vài giây.',
        )
      }
      if (flag('brokerDown')) {
        return errorResponse(503, 'BROKER_UNAVAILABLE', 'Không kết nối được tới hệ thống điều khiển (MQTT broker).')
      }

      const record = db.createAction(device, action, user)
      if (!flag('deviceOffline')) {
        setTimeout(() => {
          const event = db.completeAction(record.id)
          if (event) broadcast(event)
        }, 350 + Math.random() * 200)
      }

      const accepted = db.serializeAction(record)
      return HttpResponse.json(
        {
          request_id: accepted.request_id,
          device_id: device.id,
          device: device.code,
          action: accepted.action,
          user: accepted.user,
          status: accepted.status,
          created_at: accepted.created_at,
        },
        { status: 202 },
      )
    }),
  ),

  // §4.6
  http.get(
    url('/actions'),
    authed(({ request }) => {
      const requestUrl = new URL(request.url)
      const q = requestUrl.searchParams
      const errors = {}

      const deviceRaw = q.get('device')
      if (deviceRaw && !/^\d+$/.test(deviceRaw)) errors.device = ['Phải là số nguyên.']
      const userRaw = q.get('user')
      if (userRaw && userRaw !== 'none' && !/^\d+$/.test(userRaw)) errors.user = ['Phải là số nguyên hoặc "none".']
      const status = q.get('status')
      if (status && !['PENDING', 'SUCCESS', 'FAILED'].includes(status)) errors.status = ['Giá trị không hợp lệ.']
      const action = q.get('action')
      if (action && !['ON', 'OFF'].includes(action)) errors.action = ['Giá trị không hợp lệ.']
      const from = parseDate(q, 'created_at__gte', errors)
      const to = parseDate(q, 'created_at__lte', errors)
      if (Object.keys(errors).length) return invalid(errors)
      const badRange = rangeError('created_at', from, to)
      if (badRange) return badRange

      const search = (q.get('search') || '').trim().toLowerCase()
      const rows = db.actions
        .map((record) => ({ record, view: db.serializeAction(record) }))
        .filter(({ record, view }) => {
          if (deviceRaw && record.device_id !== Number(deviceRaw)) return false
          if (userRaw === 'none' && record.user_id != null) return false
          if (userRaw && userRaw !== 'none' && record.user_id !== Number(userRaw)) return false
          if (status && record.status !== status) return false
          if (action && record.action !== action) return false
          if (from != null && record.created_at < from) return false
          if (to != null && record.created_at > to) return false
          if (search) {
            const haystack = [view.device.name, view.device.code, view.user?.full_name, view.error_message]
              .filter(Boolean)
              .join(' ')
              .toLowerCase()
            if (!haystack.includes(search)) return false
          }
          return true
        })

      const sorted = sortRows(
        rows,
        q.get('ordering'),
        {
          created_at: (r) => r.record.created_at,
          responded_at: (r) => r.record.responded_at,
          status: (r) => r.record.status,
          action: (r) => r.record.action,
          id: (r) => r.record.id,
        },
        '-created_at',
        [(r) => -r.record.id],
      )
      const page = paginate(requestUrl, sorted)
      if (page.error) return page.error
      return HttpResponse.json({
        count: page.count,
        next: page.next,
        previous: page.previous,
        results: page.slice.map((r) => r.view),
      })
    }),
  ),

  // §4.7
  http.get(url('/profile'), authed(() => HttpResponse.json(db.PROFILE))),
]

export const handlers = [...httpHandlers, wsHandler]
