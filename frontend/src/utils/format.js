// API luôn trả giờ UTC có hậu tố Z; đổi sang giờ Việt Nam là việc của Frontend (05-API.md §2.4).
const TZ = 'Asia/Ho_Chi_Minh'

const timeFormat = new Intl.DateTimeFormat('vi-VN', {
  timeZone: TZ,
  hour: '2-digit',
  minute: '2-digit',
  second: '2-digit',
  hour12: false,
})
const dateFormat = new Intl.DateTimeFormat('vi-VN', {
  timeZone: TZ,
  day: '2-digit',
  month: '2-digit',
  year: 'numeric',
})

export const fmtTime = (iso) => (iso ? timeFormat.format(new Date(iso)) : '—')

// Ngày trước, giờ sau — cùng chiều với ô lọc "Thời điểm" để chép thẳng từ bảng vào ô lọc được.
export const fmtDateTime = (iso) =>
  iso ? `${dateFormat.format(new Date(iso))} · ${timeFormat.format(new Date(iso))}` : '—'

export const fmtCount = (n) => Number(n).toLocaleString('vi-VN')

// Cột value dùng chung double precision cho cả ba đại lượng; ánh sáng làm tròn (05-API.md §4.1).
export function fmtValue(value, metricType) {
  if (value == null) return '--'
  return metricType === 'LIGHT' ? String(Math.round(value)) : Number(value).toFixed(1)
}

export function fmtDelta(delta, metricType) {
  if (delta == null) return null
  const abs = Math.abs(delta)
  const text = metricType === 'LIGHT' ? String(Math.round(abs)) : abs.toFixed(1)
  if (Number(text) === 0) return text
  return `${delta < 0 ? '−' : '+'}${text}`
}

// ── Ô lọc "Thời điểm" ────────────────────────────────────────────────────────
// Nhận nhập GẦN ĐÚNG: gõ tới đâu thì lọc trọn đơn vị tới đó.
//   29/10/2026           → cả ngày hôm đó
//   29/10/2026 17        → trọn giờ 17
//   29/10/2026 17:29     → trọn phút đó
//   29/10/2026 17:29:24  → đúng giây đó (một chu kỳ = 3 dòng)
// Dấu ngăn cách nào cũng được (/ - . : dấu cách), nên "29/10/2026-17/29/24" cũng hợp lệ.
// Thứ tự nào cũng nhận — năm-trước (ô lịch trả về 2026-10-29T17:29:24) lẫn giờ-trước
// (17:29:24 · 29/10/2026, dạng bảng từng hiển thị) — nhận diện qua vị trí nhóm 4 chữ số.
const DATETIME_CHARS = /^[\d\s/\-.:,·tT]+$/
const PRECISIONS = ['day', 'hour', 'minute', 'second']
const pad = (n, width = 2) => String(n).padStart(width, '0')
const daysInMonth = (y, m) => new Date(Date.UTC(y, m, 0)).getUTCDate()

export function parseApproxVN(input) {
  const text = String(input ?? '').trim()
  if (!text || !DATETIME_CHARS.test(text)) return null

  const groups = text.match(/\d+/g) ?? []
  if (groups.length < 3 || groups.length > 6) return null
  const n = groups.map(Number)

  const yearAt = groups.findIndex((g) => g.length === 4)
  let year
  let month
  let day
  let time
  if (yearAt === 0) {
    ;[year, month, day] = n // 2026-10-29T17:29:24 — ô lịch
    time = n.slice(3)
  } else if (yearAt === 2) {
    ;[day, month, year] = n // 29/10/2026 17:29:24 — gõ tay
    time = n.slice(3)
  } else if (yearAt === groups.length - 1) {
    ;[day, month, year] = n.slice(-3) // 17:29:24 · 29/10/2026 — chép từ bảng
    time = n.slice(0, -3)
  } else return null

  const [hour, minute, second] = time
  if (month < 1 || month > 12 || day < 1 || day > daysInMonth(year, month)) return null
  if (hour > 23 || minute > 59 || second > 59) return null // undefined so sánh luôn cho false

  const date = `${pad(year, 4)}-${pad(month)}-${pad(day)}`
  // Bộ lọc thời gian BẮT BUỘC kèm múi giờ — thiếu +07:00 là lệch 7 tiếng mà không báo lỗi (05-API.md §2.4).
  // Cận trên phải lấy hết phần lẻ của giây: recorded_at lưu tới micro-giây (17:29:54.451), nên
  // ...__lte=17:29:54+07:00 loại sạch chính giây đó — lọc "đúng giây" ra bảng rỗng.
  const at = (h, m, s, frac = '') => `${date}T${pad(h)}:${pad(m)}:${pad(s)}${frac}+07:00`

  return {
    precision: PRECISIONS[groups.length - 3],
    date: `${pad(day)}/${pad(month)}/${pad(year, 4)}`,
    hms: [hour, minute, second],
    start: at(hour ?? 0, minute ?? 0, second ?? 0),
    end: at(hour ?? 23, minute ?? 59, second ?? 59, '.999999'),
  }
}

// Bắc cầu sang ô <input type="datetime-local"> của trình duyệt (chuỗi 2026-10-29T17:29:24).
export const toPickerValue = (text) => parseApproxVN(text)?.start.slice(0, 19) ?? ''

export function fromPickerValue(value) {
  if (!value) return ''
  const [date, time = ''] = value.split('T')
  const [y, m, d] = date.split('-')
  return `${d}/${m}/${y}${time ? ` ${time}` : ''}`
}

export function shortUrl(url) {
  try {
    const u = new URL(url)
    const path = u.pathname === '/' ? '' : u.pathname
    return `${u.host}${path}`
  } catch {
    return url
  }
}
