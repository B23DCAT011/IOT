import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { fmtTime, fmtValue } from '../../utils/format'

// Thuộc tính trình bày của SVG không nhận var(--...), nên màu chữ trục phải là mã hex.
const TICK = { fill: '#8A9AA7', fontSize: 12, fontFamily: "'Cascadia Mono', Consolas, monospace" }

const TOOLTIP_STYLE = {
  border: '1px solid #D3DBE2',
  borderRadius: 3,
  fontSize: 12,
  padding: '8px 12px',
  boxShadow: 'none',
}

/**
 * Hai trục tung giống bản vẽ: trái 20→100 cho °C và %, phải 0→500 cho lux.
 * connectNulls = false → chu kỳ thiếu số đo làm đường đứt một đoạn (05-API.md §4.2).
 */
export default function SensorChart({ data, series }) {
  const byKey = Object.fromEntries(series.map((item) => [item.key, item]))

  return (
    <ResponsiveContainer width="100%" height="100%">
      <LineChart data={data} margin={{ top: 8, right: 4, bottom: 0, left: 4 }}>
        <CartesianGrid vertical={false} stroke="#E6EBEF" />
        <XAxis
          dataKey="recorded_at"
          tickFormatter={fmtTime}
          tick={TICK}
          tickLine={false}
          axisLine={false}
          minTickGap={48}
          interval="preserveStartEnd"
        />
        <YAxis
          yAxisId="left"
          domain={[20, 100]}
          ticks={[20, 40, 60, 80, 100]}
          tick={TICK}
          tickLine={false}
          axisLine={false}
          width={40}
        />
        <YAxis
          yAxisId="right"
          orientation="right"
          domain={[0, 500]}
          ticks={[0, 125, 250, 375, 500]}
          tick={TICK}
          tickLine={false}
          axisLine={false}
          width={40}
        />
        <Tooltip
          contentStyle={TOOLTIP_STYLE}
          labelFormatter={(label) => fmtTime(label)}
          formatter={(value, name, item) => {
            const meta = byKey[item.dataKey]
            return [value == null ? '—' : `${fmtValue(value, meta?.metricType)} ${meta?.unit ?? ''}`, name]
          }}
        />
        {series.map((item) => (
          <Line
            key={item.key}
            yAxisId={item.axis}
            type="linear"
            dataKey={item.key}
            name={item.name}
            stroke={item.color}
            strokeWidth={2.5}
            dot={false}
            activeDot={{ r: 4 }}
            connectNulls={false}
            isAnimationActive={false}
          />
        ))}
      </LineChart>
    </ResponsiveContainer>
  )
}
