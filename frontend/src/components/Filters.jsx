import { useRef } from 'react'
import ui from '../styles/ui.module.css'
import { fromPickerValue, toPickerValue } from '../utils/format'
import { CalendarIcon } from './Icons'

export function Field({ label, children, grow }) {
  return (
    <label className={`${ui.field} ${grow ? ui.fieldGrow : ''}`}>
      <span className={ui.fieldLabel}>{label}</span>
      {children}
    </label>
  )
}

export function DateTimeInput({ value, onChange, invalid, placeholder }) {
  const picker = useRef(null)

  const openPicker = () => {
    const el = picker.current
    if (!el) return
    el.value = toPickerValue(value) // mở lịch ngay tại mốc đang gõ dở
    // showPicker() cần phần tử thật sự được render — ô ẩn chỉ để opacity:0, không display:none.
    if (typeof el.showPicker === 'function') el.showPicker()
    else el.focus()
  }

  return (
    <div className={ui.dtBox}>
      <input
        type="text"
        inputMode="numeric"
        autoComplete="off"
        className={`${ui.input} ${invalid ? ui.invalid : ''}`}
        value={value}
        placeholder={placeholder}
        onChange={(e) => onChange(e.target.value)}
      />
      <button type="button" className={ui.dtBtn} onClick={openPicker} title="Chọn từ lịch" aria-label="Chọn từ lịch">
        <CalendarIcon />
      </button>
      <input
        ref={picker}
        type="datetime-local"
        step="1"
        className={ui.dtPicker}
        tabIndex={-1}
        aria-hidden="true"
        onChange={(e) => onChange(fromPickerValue(e.target.value))}
      />
    </div>
  )
}

export function EmptyState({ filtered, onClear }) {
  return (
    <div className={ui.empty}>
      {filtered ? (
        <>
          <div>Không tìm thấy bản ghi nào khớp bộ lọc</div>
          <button type="button" className={ui.btn} onClick={onClear}>
            Xóa bộ lọc
          </button>
        </>
      ) : (
        <div>Không có dữ liệu</div>
      )}
    </div>
  )
}
