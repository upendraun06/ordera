import { useState, useEffect } from 'react'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, Legend } from 'recharts'
import { inventoryApi } from '../../services/inventoryApi'

const DAYS_OPTIONS = [7, 14, 30]

function SummaryCard({ label, value, color }) {
  return (
    <div style={{
      flex: 1,
      background: 'var(--surface-2)',
      border: '1px solid var(--border)',
      borderRadius: 10,
      padding: '14px 18px',
    }}>
      <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--text-3)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: 6 }}>
        {label}
      </div>
      <div style={{ fontSize: 22, fontWeight: 700, color }}>${value.toFixed(2)}</div>
    </div>
  )
}

function CustomTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null
  return (
    <div style={{ background: '#fff', border: '1px solid var(--border)', borderRadius: 10, padding: '10px 14px', boxShadow: '0 4px 16px rgba(0,0,0,0.08)', fontSize: 12 }}>
      <div style={{ fontWeight: 700, marginBottom: 6, color: 'var(--text-1)' }}>{label}</div>
      {payload.map((p, i) => (
        <div key={i} style={{ color: p.color, marginTop: 3 }}>
          {p.name}: <strong>${p.value.toFixed(2)}</strong>
        </div>
      ))}
    </div>
  )
}

export default function ProfitCard() {
  const [days, setDays] = useState(7)
  const [data, setData] = useState([])
  const [loading, setLoading] = useState(true)
  const [totals, setTotals] = useState({ revenue: 0, cost: 0, profit: 0 })

  useEffect(() => {
    setLoading(true)
    inventoryApi.getAnalytics(days)
      .then((r) => {
        const daily = r.data.daily_profit || []
        setData(daily.map((d) => ({
          date: d.date.slice(5),
          Revenue: d.revenue,
          Cost: d.cost,
          Profit: d.profit,
        })))
        setTotals({
          revenue: daily.reduce((s, d) => s + d.revenue, 0),
          cost: daily.reduce((s, d) => s + d.cost, 0),
          profit: daily.reduce((s, d) => s + d.profit, 0),
        })
      })
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [days])

  return (
    <div>
      {/* Day range selector */}
      <div style={{ display: 'flex', gap: 6, marginBottom: 20 }}>
        {DAYS_OPTIONS.map((d) => (
          <button
            key={d}
            onClick={() => setDays(d)}
            style={{
              padding: '5px 16px',
              borderRadius: 20,
              fontSize: 12,
              fontWeight: 600,
              border: `1px solid ${days === d ? 'var(--primary)' : 'var(--border)'}`,
              cursor: 'pointer',
              background: days === d ? 'var(--primary-light)' : 'var(--surface-2)',
              color: days === d ? 'var(--primary)' : 'var(--text-2)',
            }}
          >
            {d} days
          </button>
        ))}
      </div>

      {/* Summary cards */}
      <div style={{ display: 'flex', gap: 12, marginBottom: 24 }}>
        <SummaryCard label="Revenue" value={totals.revenue} color="#094cb2" />
        <SummaryCard label="Cost" value={totals.cost} color="#dc2626" />
        <SummaryCard label="Profit" value={totals.profit} color={totals.profit >= 0 ? '#15803d' : '#dc2626'} />
      </div>

      {loading ? (
        <div style={{ color: 'var(--text-3)', fontSize: 13 }}>Loading...</div>
      ) : data.length === 0 ? (
        <div style={{ color: 'var(--text-3)', fontSize: 13, padding: '32px 0', textAlign: 'center' }}>
          No order data in this period. Once orders come in and ingredients are mapped, profit will appear here.
        </div>
      ) : (
        <ResponsiveContainer width="100%" height={240}>
          <BarChart data={data} margin={{ top: 4, right: 4, left: 0, bottom: 4 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" vertical={false} />
            <XAxis dataKey="date" tick={{ fill: 'var(--text-3)', fontSize: 11 }} axisLine={false} tickLine={false} />
            <YAxis tick={{ fill: 'var(--text-3)', fontSize: 11 }} axisLine={false} tickLine={false} width={56} tickFormatter={(v) => `$${v}`} />
            <Tooltip content={<CustomTooltip />} />
            <Legend wrapperStyle={{ fontSize: 12, color: 'var(--text-2)' }} />
            <Bar dataKey="Revenue" fill="#094cb2" radius={[4, 4, 0, 0]} maxBarSize={28} />
            <Bar dataKey="Cost" fill="#ef4444" radius={[4, 4, 0, 0]} maxBarSize={28} />
            <Bar dataKey="Profit" fill="#22c55e" radius={[4, 4, 0, 0]} maxBarSize={28} />
          </BarChart>
        </ResponsiveContainer>
      )}
    </div>
  )
}
