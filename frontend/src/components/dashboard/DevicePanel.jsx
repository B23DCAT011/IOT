import { useCallback, useEffect, useRef, useState } from 'react'
import { deviceApi } from '../../api/endpoints'
import { CONTROL_FALLBACK_MS } from '../../config'
import { useRealtimeEvent } from '../../realtime/RealtimeContext'
import ui from '../../styles/ui.module.css'
import { errorChip } from '../../utils/errors'
import { DeviceIcon } from '../Icons'
import s from './Dashboard.module.css'

/**
 * Điều khiển thiết bị — UC-02, 05-API.md §4.5 "Điều gì xảy ra sau khi nhận 202".
 * pending[deviceId] = { target, requestId } trong lúc chờ device.state.
 */
export default function DevicePanel({ devices, setDevices, loading, onNotice, onFallback }) {
  const [pending, setPending] = useState({})
  const pendingRef = useRef({})
  const timers = useRef({})

  const updatePending = useCallback((update) => {
    const next = update(pendingRef.current)
    pendingRef.current = next
    setPending(next)
  }, [])

  const unlock = useCallback(
    (deviceId) => {
      clearTimeout(timers.current[deviceId])
      delete timers.current[deviceId]
      updatePending((current) => {
        if (!(deviceId in current)) return current
        const next = { ...current }
        delete next[deviceId]
        return next
      })
    },
    [updatePending],
  )

  useEffect(() => {
    const active = timers.current
    return () => Object.values(active).forEach(clearTimeout)
  }, [])

  useRealtimeEvent((event) => {
    if (event.type !== 'device.state') return

    // Luôn cập nhật trạng thái thật, kể cả lệnh do tab khác gửi (§5.4 quy tắc 4).
    setDevices((list) =>
      list.map((d) => (d.id === event.device_id ? { ...d, current_state: event.current_state } : d)),
    )

    const mine = pendingRef.current[event.device_id]
    if (!mine) return
    // Chưa nhận 202 thì chưa biết request_id — chấp nhận sự kiện đầu tiên của thiết bị này.
    if (mine.requestId && mine.requestId !== event.request_id) return

    unlock(event.device_id)
    if (event.status === 'FAILED') {
      onNotice({
        chip: 'Timeout',
        text: 'Thiết bị không phản hồi — công tắc đã trả về trạng thái cũ, thao tác được ghi lại với trạng thái FAILED.',
      })
    }
  })

  const toggle = async (device) => {
    if (pendingRef.current[device.id]) return // BR-04: đang chờ thì không nhận lệnh mới

    const target = device.current_state === 'ON' ? 'OFF' : 'ON'
    updatePending((current) => ({ ...current, [device.id]: { target, requestId: null } }))

    // Bộ đếm dự phòng: WebSocket đứt đúng lúc lệnh đang chạy thì device.state không bao giờ tới.
    timers.current[device.id] = setTimeout(() => {
      unlock(device.id)
      onFallback()
    }, CONTROL_FALLBACK_MS)

    try {
      const accepted = await deviceApi.control(device.id, target)
      updatePending((current) =>
        current[device.id]
          ? { ...current, [device.id]: { ...current[device.id], requestId: accepted.request_id } }
          : current,
      )
    } catch (err) {
      unlock(device.id)
      if (err.status !== 401) onNotice({ chip: errorChip(err), text: err.message })
    }
  }

  return (
    <section className={ui.card}>
      <div className={ui.cardHead}>
        <div className={ui.cardTitle}>Thiết bị</div>
        <div className={ui.cardSub}>{devices.length} thiết bị</div>
      </div>

      {devices.length === 0 && (
        <div className={s.devEmpty}>{loading ? 'Đang tải…' : 'Chưa có thiết bị nào.'}</div>
      )}

      {devices.map((device) => {
        const wait = pending[device.id]
        const shown = wait ? wait.target : device.current_state
        return (
          <div key={device.id} className={s.dev}>
            <div className={s.devIc}>
              <DeviceIcon type={device.device_type} />
            </div>
            <div className={s.devMeta}>
              <div className={s.devName}>{device.name}</div>
              <div className={s.devCode}>
                {device.code} · {device.gpio_pin}
              </div>
            </div>
            <div className={s.swWrap}>
              <button
                type="button"
                role="switch"
                aria-checked={shown === 'ON'}
                aria-busy={Boolean(wait)}
                aria-label={device.name}
                disabled={Boolean(wait)}
                className={`${s.sw} ${shown === 'ON' ? s.swOn : ''} ${wait ? s.swBusy : ''}`}
                onClick={() => toggle(device)}
              >
                <span className={s.knob} />
              </button>
              <span className={s.swState}>{wait ? 'ĐANG GỬI…' : device.current_state}</span>
            </div>
          </div>
        )
      })}
    </section>
  )
}
