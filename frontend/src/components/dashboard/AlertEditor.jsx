import { useEffect, useRef, useState } from 'react'
import { sensorApi } from '../../api/endpoints'
import ui from '../../styles/ui.module.css'
import { fmtDateTime } from '../../utils/format'
import s from './Dashboard.module.css'

const toText = (value) => (value == null ? '' : String(value))

// Ô trống → null; có chữ → số, hoặc NaN nếu gõ sai (ô type=number vẫn gõ được "-" hay "1e").
const toNumber = (text) => (text.trim() === '' ? null : Number(text))

// Kiểm tra giống hệt AlertConfigSerializer ở backend — sai thì báo ngay, không gọi API.
function validate({ enabled, low, high }, sensor) {
  const errors = {}
  const range = `${sensor.min_value} … ${sensor.max_value} ${sensor.unit}`
  ;[
    ['low', low],
    ['high', high],
  ].forEach(([field, value]) => {
    if (Number.isNaN(value)) errors[field] = 'Không phải số.'
    else if (value != null && (value < sensor.min_value || value > sensor.max_value))
      errors[field] = `Phải trong khoảng ${range}.`
  })
  if (!errors.low && !errors.high && low != null && high != null && low >= high)
    errors.high = 'Phải lớn hơn ngưỡng dưới.'
  if (enabled && low == null && high == null) errors.form = 'Bật cảnh báo thì phải đặt ít nhất một ngưỡng.'
  return errors
}

// Lỗi 400 của máy chủ: details theo tên trường của API → đổi về tên ô trên form.
function serverErrors(err) {
  const d = err?.details ?? {}
  const first = (v) => (Array.isArray(v) ? v[0] : v)
  const errors = {}
  if (d.alert_low) errors.low = first(d.alert_low)
  if (d.alert_high) errors.high = first(d.alert_high)
  if (d.non_field_errors) errors.form = first(d.non_field_errors)
  if (!Object.keys(errors).length) errors.form = err?.message ?? 'Không lưu được.'
  return errors
}

/**
 * Khung chỉnh ngưỡng cảnh báo, mở ngay dưới thẻ số liệu.
 * Lưu xong gọi onSaved(sensor mới) — các tab khác nhận cùng dữ liệu qua sự kiện sensor.alert.
 */
export default function AlertEditor({ sensor, onSaved, onClose }) {
  const [enabled, setEnabled] = useState(sensor.alert_enabled)
  const [lowText, setLowText] = useState(toText(sensor.alert_low))
  const [highText, setHighText] = useState(toText(sensor.alert_high))
  const [errors, setErrors] = useState({})
  const [saving, setSaving] = useState(false)
  const boxRef = useRef(null)
  const firstInput = useRef(null)
  // Người dùng đã tự gạt công tắc trong lần mở khung này chưa — chưa thì gõ ngưỡng là tự bật.
  const switchTouched = useRef(false)

  // Gõ một ngưỡng mà công tắc đang tắt → tự bật. Không có bước này thì nhập số rồi bấm Lưu
  // sẽ lưu được ngưỡng nhưng không cảnh báo gì (người dùng đã gặp đúng chuyện này 29/10/2026).
  const editThreshold = (setText) => (e) => {
    setText(e.target.value)
    if (!enabled && !switchTouched.current && e.target.value.trim() !== '') setEnabled(true)
  }

  useEffect(() => {
    firstInput.current?.focus()
    const onKey = (e) => e.key === 'Escape' && onClose()
    const onDown = (e) => {
      // Bấm ra ngoài khung (kể cả nút ⚙ của thẻ khác) thì đóng, giống một menu thả xuống.
      if (boxRef.current && !boxRef.current.contains(e.target)) onClose()
    }
    document.addEventListener('keydown', onKey)
    document.addEventListener('mousedown', onDown)
    return () => {
      document.removeEventListener('keydown', onKey)
      document.removeEventListener('mousedown', onDown)
    }
  }, [onClose])

  const submit = (e) => {
    e.preventDefault()
    const form = { enabled, low: toNumber(lowText), high: toNumber(highText) }
    const found = validate(form, sensor)
    setErrors(found)
    if (Object.keys(found).length) return

    setSaving(true)
    sensorApi
      .saveAlert(sensor.id, { alert_enabled: form.enabled, alert_low: form.low, alert_high: form.high })
      .then((saved) => {
        onSaved(saved)
        onClose()
      })
      .catch((err) => {
        setErrors(serverErrors(err))
        setSaving(false)
      })
  }

  const who = sensor.alert_updated_by?.full_name ?? '—'

  return (
    <form ref={boxRef} className={s.alertBox} onSubmit={submit} aria-label={`Ngưỡng cảnh báo — ${sensor.name}`}>
      <div className={s.alertHead}>
        <span className={s.alertTitle}>Cảnh báo {sensor.name.toLowerCase()}</span>
        <button
          type="button"
          role="switch"
          aria-checked={enabled}
          aria-label="Bật cảnh báo"
          className={`${s.sw} ${enabled ? s.swOn : ''}`}
          onClick={() => {
            switchTouched.current = true
            setEnabled((v) => !v)
            setErrors((prev) => ({ ...prev, form: undefined }))
          }}
        >
          <span className={s.knob} />
        </button>
      </div>

      <label className={s.alertRow}>
        <span className={s.alertRowLabel}>Dưới</span>
        <input
          ref={firstInput}
          type="number"
          step="any"
          inputMode="decimal"
          className={`${ui.input} ${s.alertInput} ${errors.low ? ui.invalid : ''}`}
          value={lowText}
          placeholder="không đặt"
          onChange={editThreshold(setLowText)}
        />
        <span className={s.alertUnit}>{sensor.unit}</span>
      </label>
      {errors.low && <div className={s.alertErr}>{errors.low}</div>}

      <label className={s.alertRow}>
        <span className={s.alertRowLabel}>Trên</span>
        <input
          type="number"
          step="any"
          inputMode="decimal"
          className={`${ui.input} ${s.alertInput} ${errors.high ? ui.invalid : ''}`}
          value={highText}
          placeholder="không đặt"
          onChange={editThreshold(setHighText)}
        />
        <span className={s.alertUnit}>{sensor.unit}</span>
      </label>
      {errors.high && <div className={s.alertErr}>{errors.high}</div>}

      <div className={s.alertHint}>
        Cho phép: {sensor.min_value} … {sensor.max_value} {sensor.unit}
      </div>
      {sensor.alert_updated_at && (
        <div className={s.alertHint}>
          Sửa lần cuối: {who}, {fmtDateTime(sensor.alert_updated_at)}
        </div>
      )}
      {errors.form && <div className={s.alertErr}>{errors.form}</div>}

      <div className={s.alertActions}>
        <button type="button" className={ui.btn} onClick={onClose} disabled={saving}>
          Huỷ
        </button>
        <button type="submit" className={`${ui.btn} ${ui.btnPrimary}`} disabled={saving}>
          {saving ? 'Đang lưu…' : 'Lưu'}
        </button>
      </div>
    </form>
  )
}
