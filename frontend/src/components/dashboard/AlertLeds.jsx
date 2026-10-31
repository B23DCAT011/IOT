import { ALERT_LABEL, metricKey } from '../../constants'
import { GearIcon } from '../Icons'
import AlertEditor from './AlertEditor'
import s from './Dashboard.module.css'

// "10 – 25 °C", "> 25 °C", "< 100 lux" — ngưỡng đang canh, hoặc lý do đèn không bao giờ sáng.
function thresholdText(sensor) {
  const { alert_enabled: on, alert_low: low, alert_high: high, unit } = sensor
  if (!on) return 'chưa bật'
  if (low != null && high != null) return `${low} – ${high} ${unit}`
  if (high != null) return `> ${high} ${unit}`
  return `< ${low} ${unit}`
}

/**
 * Ba "thiết bị" đại diện cho 3 LED cảnh báo trên mạch (D1/D2/D7), nằm cuối panel Thiết bị.
 * Không có công tắc: đèn do backend bật theo ngưỡng, giao diện chỉ phản chiếu lại — box nháy
 * đúng lúc LED thật nháy. Nút ⚙ mở khung chỉnh ngưỡng của cảm biến tương ứng.
 *
 * `alerts`: { temperature: 'HIGH' | 'LOW' | null, … } — lấy từ sự kiện sensor.data.
 * Thiết bị ngoại tuyến thì không nháy: trạng thái cảnh báo đã cũ.
 */
export default function AlertLeds({ catalog, devices, alerts, offline, editingId, onEdit, onClose, onSaved }) {
  if (catalog.length === 0) return null
  // sensor.alert_device là id thiết bị đèn cảnh báo trong GET /api/devices — lấy chân GPIO từ đó.
  const deviceById = new Map(devices.map((device) => [device.id, device]))

  return (
    <>
      <div className={s.devSection}>Đèn cảnh báo</div>
      {catalog.map((sensor) => {
        const key = metricKey(sensor.metric_type)
        const state = alerts[key]
        const blinking = Boolean(state) && sensor.alert_enabled && !offline
        const editing = editingId === sensor.id
        const led = deviceById.get(sensor.alert_device)
        return (
          <div
            key={sensor.id}
            className={`${s.dev} ${s.led} ${blinking ? s.ledOn : ''}`}
            role={blinking ? 'alert' : undefined}
          >
            <div className={s.devIc}>
              <span className={s.ledDot} />
            </div>
            <div className={s.devMeta}>
              <div className={s.devName}>Cảnh báo {sensor.name.toLowerCase()}</div>
              <div className={s.devCode}>
                {led?.gpio_pin ?? '—'} · {blinking ? `${ALERT_LABEL[state]} ${state === 'HIGH' ? sensor.alert_high : sensor.alert_low} ${sensor.unit}` : thresholdText(sensor)}
              </div>
            </div>
            <div className={s.swWrap}>
              <button
                type="button"
                className={`${s.gear} ${editing ? s.gearActive : ''}`}
                onClick={editing ? onClose : () => onEdit(sensor.id)}
                // Khung đang mở đóng khi bấm ra ngoài (mousedown ở document). Chặn ở đây để bấm
                // chính nút này thì chỉ đóng một lần, không đóng rồi mở lại ngay.
                onMouseDown={(e) => e.stopPropagation()}
                title="Chỉnh ngưỡng cảnh báo"
                aria-label={`Ngưỡng cảnh báo ${sensor.name.toLowerCase()}`}
                aria-expanded={editing}
              >
                <GearIcon />
              </button>
              <span className={s.swState}>{blinking ? 'NHÁY' : 'TẮT'}</span>
            </div>
            {editing && <AlertEditor sensor={sensor} onSaved={onSaved} onClose={onClose} />}
          </div>
        )
      })}
    </>
  )
}
