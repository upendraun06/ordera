import { useEffect, useRef, useState } from 'react'

/* Animated number that counts up on mount */
function AnimatedNumber({ value }) {
  const [display, setDisplay] = useState('0')
  const rafRef = useRef(null)

  useEffect(() => {
    const str = String(value)
    const prefix = str.startsWith('$') ? '$' : ''
    const suffix = str.endsWith('%') ? '%'  : ''
    const raw    = parseFloat(str.replace(/[$,%]/g, ''))

    if (isNaN(raw)) { setDisplay(str); return }

    const duration = 700  // ms
    const start    = performance.now()
    const isFloat  = str.includes('.')

    const tick = (now) => {
      const elapsed  = now - start
      const progress = Math.min(elapsed / duration, 1)
      // ease-out-cubic
      const eased    = 1 - Math.pow(1 - progress, 3)
      const current  = raw * eased

      if (isFloat) {
        setDisplay(`${prefix}${current.toFixed(2)}${suffix}`)
      } else {
        setDisplay(`${prefix}${Math.round(current)}${suffix}`)
      }

      if (progress < 1) {
        rafRef.current = requestAnimationFrame(tick)
      }
    }

    rafRef.current = requestAnimationFrame(tick)
    return () => cancelAnimationFrame(rafRef.current)
  }, [value])

  return <span>{display}</span>
}

const ICON_CLASSES = {
  blue:   'stat-icon stat-icon-blue',
  green:  'stat-icon stat-icon-green',
  yellow: 'stat-icon stat-icon-yellow',
  purple: 'stat-icon stat-icon-purple',
  red:    'stat-icon stat-icon-red',
}

export default function StatCard({ label, value, icon: Icon, color = 'blue', sub, trend }) {
  return (
    <div className="card animate-fade-in-up flex items-center gap-4">
      {/* Icon */}
      <div className={ICON_CLASSES[color] || ICON_CLASSES.blue}>
        {typeof Icon === 'string' ? (
          <span style={{ fontSize: 22 }}>{Icon}</span>
        ) : Icon ? (
          <Icon size={22} />
        ) : null}
      </div>

      {/* Text */}
      <div className="min-w-0 flex-1">
        <div
          className="text-2xl font-bold tracking-tight"
          style={{ color: 'var(--text-1)' }}
        >
          <AnimatedNumber value={value} />
        </div>
        <div className="text-sm mt-0.5" style={{ color: 'var(--text-3)' }}>
          {label}
        </div>
        {sub && (
          <div className="text-xs mt-0.5" style={{ color: 'var(--text-3)' }}>
            {sub}
          </div>
        )}
      </div>

      {/* Optional trend badge */}
      {trend !== undefined && (
        <div
          className="flex-shrink-0 text-xs font-semibold px-2 py-0.5 rounded-full"
          style={
            trend >= 0
              ? { background: '#dcfce7', color: '#166534' }
              : { background: '#fee2e2', color: '#b91c1c' }
          }
        >
          {trend >= 0 ? '↑' : '↓'} {Math.abs(trend)}%
        </div>
      )}
    </div>
  )
}
