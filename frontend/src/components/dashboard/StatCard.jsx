import { fmtDelta, fmtValue } from '../../utils/format'
import s from './Dashboard.module.css'

function Sparkline({ values, color }) {
  const points = values.filter((v) => v != null)
  if (points.length < 2) return null

  const min = Math.min(...points)
  const max = Math.max(...points)
  const span = max - min || 1
  const step = 72 / (points.length - 1)
  const coords = points.map((v, i) => [+(i * step).toFixed(1), +(18 - ((v - min) / span) * 16).toFixed(1)])
  const [lastX, lastY] = coords[coords.length - 1]

  return (
    <svg viewBox="0 0 72 20" fill="none" aria-hidden="true">
      <polyline points={coords.map((c) => c.join(',')).join(' ')} stroke={color} strokeWidth="1.5" />
      <circle cx={lastX} cy={lastY} r="2.2" fill={color} />
    </svg>
  )
}

export default function StatCard({ sensor, color, value, delta, spark, offline }) {
  const noValue = value == null

  let footText
  if (noValue) footText = 'chưa có số liệu'
  else if (offline) footText = 'không có số liệu mới'
  else if (delta != null) footText = `${fmtDelta(delta, sensor.metric_type)} trong 20 giây`
  else footText = '—'

  return (
    <div className={s.stat}>
      <div className={s.tick} style={{ background: color }} />
      <div className={s.statMain}>
        <div className={s.statLabel}>{sensor.name}</div>
        <div className={`${s.statVal} ${noValue ? s.statValNil : ''}`}>
          {fmtValue(value, sensor.metric_type)}
          <span className={s.statUnit}>{sensor.unit}</span>
        </div>
        <div className={s.statFoot}>
          <span className={s.statDelta}>{footText}</span>
          {!noValue && !offline && <Sparkline values={spark} color={color} />}
        </div>
      </div>
    </div>
  )
}
