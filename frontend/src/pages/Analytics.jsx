import { useState, useEffect } from 'react'
import {
  BarChart, Bar, XAxis, YAxis, Tooltip,
  ResponsiveContainer, CartesianGrid, LineChart, Line, Legend,
} from 'recharts'
import Layout from '../components/Layout'
import StatCard from '../components/StatCard'
import { dashboardApi } from '../services/api'
import { generateReportPDF } from '../utils/generatePDF'
import { AnalyticsIcon, PhoneIcon, SpinnerIcon } from '../components/Icons'

/* Download period options */
const PERIODS = [
  { value: 'week',  label: 'Last 7 Days'   },
  { value: 'month', label: 'Last 30 Days'  },
  { value: 'year',  label: 'Last 12 Months'},
]

/* Chart display options */
const CHART_DAYS = [
  { value: 7,  label: '7d'  },
  { value: 14, label: '14d' },
  { value: 30, label: '30d' },
]

/* Printer / download icon */
function DownloadIcon({ size = 16 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none"
      stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
      <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
      <polyline points="7 10 12 15 17 10"/>
      <line x1="12" y1="15" x2="12" y2="3"/>
    </svg>
  )
}

/* Custom tooltip for charts */
function CustomTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null
  return (
    <div style={{
      background: '#fff', border: '1px solid #e4e9f0',
      borderRadius: 10, padding: '10px 14px',
      boxShadow: '0 4px 16px rgba(0,0,0,0.08)',
      fontSize: 12,
    }}>
      <div style={{ fontWeight: 600, marginBottom: 4, color: '#0f172a' }}>{label}</div>
      {payload.map((p, i) => (
        <div key={i} style={{ color: p.color, marginTop: 2 }}>
          {p.name}: <strong>{p.value}</strong>
        </div>
      ))}
    </div>
  )
}

export default function Analytics() {
  const [callData,    setCallData]    = useState(null)
  const [statsData,   setStatsData]   = useState(null)
  const [days,        setDays]        = useState(7)
  const [loading,     setLoading]     = useState(true)
  const [dlPeriod,    setDlPeriod]    = useState('week')
  const [downloading, setDownloading] = useState(false)
  const [dlSuccess,   setDlSuccess]   = useState(false)

  useEffect(() => {
    setLoading(true)
    Promise.all([dashboardApi.calls(days), dashboardApi.stats()])
      .then(([callsRes, statsRes]) => {
        setCallData(callsRes.data)
        setStatsData(statsRes.data)
      })
      .finally(() => setLoading(false))
  }, [days])

  const handleDownload = async () => {
    setDownloading(true)
    setDlSuccess(false)
    try {
      const res = await dashboardApi.report(dlPeriod)
      await generateReportPDF(res.data)
      setDlSuccess(true)
      setTimeout(() => setDlSuccess(false), 3000)
    } catch (err) {
      console.error('PDF generation failed:', err)
      alert('Failed to generate report. Please try again.')
    } finally {
      setDownloading(false)
    }
  }

  return (
    <Layout>
      <div className="p-6 max-w-5xl mx-auto">

        {/* ── Header ── */}
        <div className="flex items-center justify-between mb-6 flex-wrap gap-4">
          <div className="flex items-center gap-3">
            <div
              className="flex items-center justify-center rounded-xl"
              style={{ width: 40, height: 40, background: 'var(--primary-light)' }}
            >
              <AnalyticsIcon size={18} className="text-indigo-600" />
            </div>
            <div>
              <h1 className="text-xl font-bold" style={{ color: 'var(--text-1)' }}>Analytics</h1>
              <p className="text-xs mt-0.5" style={{ color: 'var(--text-3)' }}>
                Call performance & order revenue
              </p>
            </div>
          </div>

          {/* Chart range pills */}
          <div className="flex items-center gap-1.5">
            {CHART_DAYS.map(d => (
              <button
                key={d.value}
                onClick={() => setDays(d.value)}
                className="px-3 py-1.5 rounded-lg text-xs font-semibold transition-all duration-150"
                style={days === d.value
                  ? { background: 'var(--primary)', color: '#fff', boxShadow: '0 2px 8px rgba(99,102,241,0.35)' }
                  : { background: '#f1f5f9', color: 'var(--text-2)' }
                }
              >
                {d.label}
              </button>
            ))}
          </div>
        </div>

        {/* ── Stat cards ── */}
        {loading ? (
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
            {[...Array(4)].map((_, i) => (
              <div key={i} className="card flex items-center gap-4">
                <div className="skeleton rounded-2xl flex-shrink-0" style={{ width: 48, height: 48 }} />
                <div className="flex-1 space-y-2">
                  <div className="skeleton h-7 w-14 rounded-md" />
                  <div className="skeleton h-3 w-20 rounded" />
                </div>
              </div>
            ))}
          </div>
        ) : callData && (
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
            <StatCard label="Total Calls"      value={callData.total_calls}      icon={PhoneIcon}    color="blue"   />
            <StatCard label="Completed"        value={callData.completed_calls}  icon={AnalyticsIcon} color="green" />
            <StatCard label="Abandoned"        value={callData.abandoned_calls}  icon={PhoneIcon}    color="red"    />
            <StatCard
              label="Completion Rate"
              value={`${callData.completion_rate}%`}
              icon={AnalyticsIcon}
              color="purple"
              sub={`Avg ${callData.avg_duration_seconds}s / call`}
            />
          </div>
        )}

        {/* ── Calls per day bar chart ── */}
        {callData && (
          <div className="card mb-5">
            <div className="flex items-center justify-between mb-5">
              <h2 className="font-semibold text-sm" style={{ color: 'var(--text-1)' }}>Calls per Day</h2>
              <span className="text-xs" style={{ color: 'var(--text-3)' }}>
                {callData.total_calls} total over {days} days
              </span>
            </div>
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={callData.calls_by_date} barSize={22}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" vertical={false} />
                <XAxis dataKey="date" tick={{ fontSize: 11, fill: '#94a3b8' }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fontSize: 11, fill: '#94a3b8' }} axisLine={false} tickLine={false} />
                <Tooltip content={<CustomTooltip />} />
                <Bar dataKey="count" name="Calls" fill="#6366f1" radius={[5, 5, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        )}

        {/* ── Today's orders summary ── */}
        {statsData && (
          <div className="card mb-5">
            <h2 className="font-semibold text-sm mb-5" style={{ color: 'var(--text-1)' }}>Today's Orders</h2>
            <div className="grid grid-cols-3 gap-4 text-center">
              {[
                { label: 'Active',    value: statsData.active_orders,              color: '#d97706' },
                { label: 'Completed', value: statsData.completed_orders,           color: '#059669' },
                { label: 'Revenue',   value: `$${statsData.revenue_today?.toFixed(2)}`, color: '#6366f1' },
              ].map(item => (
                <div key={item.label} className="py-3 rounded-xl" style={{ background: '#f8fafc' }}>
                  <div className="text-2xl font-bold" style={{ color: item.color }}>{item.value}</div>
                  <div className="text-xs mt-1" style={{ color: 'var(--text-3)' }}>{item.label}</div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            DOWNLOAD REPORT SECTION
        ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */}
        <div
          className="card"
          style={{
            background: 'linear-gradient(135deg, #eef2ff 0%, #f5f3ff 100%)',
            border: '1px solid #c7d2fe',
          }}
        >
          <div className="flex items-start justify-between gap-6 flex-wrap">
            <div>
              <div className="flex items-center gap-2 mb-1">
                <DownloadIcon size={16} />
                <h2 className="font-bold text-sm" style={{ color: 'var(--text-1)' }}>
                  Download Business Report
                </h2>
              </div>
              <p className="text-xs" style={{ color: 'var(--text-2)', maxWidth: 380 }}>
                Export a full PDF report including order history, revenue breakdown, call analytics,
                and daily performance — ready to share with your team or accountant.
              </p>

              {/* Period options */}
              <div className="flex gap-2 mt-4 flex-wrap">
                {PERIODS.map(p => (
                  <button
                    key={p.value}
                    onClick={() => setDlPeriod(p.value)}
                    className="px-3 py-1.5 rounded-lg text-xs font-semibold transition-all duration-150 border"
                    style={dlPeriod === p.value
                      ? { background: '#6366f1', color: '#fff', borderColor: '#6366f1', boxShadow: '0 2px 8px rgba(99,102,241,0.35)' }
                      : { background: '#fff', color: '#475569', borderColor: '#c7d2fe' }
                    }
                  >
                    {p.label}
                  </button>
                ))}
              </div>

              {/* What's included */}
              <div className="mt-4 grid grid-cols-2 gap-1" style={{ maxWidth: 360 }}>
                {[
                  'Order summary & revenue',
                  'AI call analytics',
                  'Daily call volume table',
                  'Revenue by date',
                  'Full order history',
                  'Payment status breakdown',
                ].map(item => (
                  <div key={item} className="flex items-center gap-1.5 text-xs" style={{ color: '#4338ca' }}>
                    <svg width={10} height={10} viewBox="0 0 24 24" fill="none" stroke="#6366f1" strokeWidth={3} strokeLinecap="round" strokeLinejoin="round">
                      <polyline points="20 6 9 17 4 12"/>
                    </svg>
                    {item}
                  </div>
                ))}
              </div>
            </div>

            {/* Download button */}
            <div className="flex flex-col items-center gap-2 flex-shrink-0">
              <button
                onClick={handleDownload}
                disabled={downloading}
                className="btn-primary"
                style={{ padding: '12px 24px', fontSize: 14, minWidth: 160 }}
              >
                {downloading ? (
                  <span className="flex items-center gap-2">
                    <SpinnerIcon size={15} />
                    Generating...
                  </span>
                ) : dlSuccess ? (
                  <span className="flex items-center gap-2">
                    <svg width={14} height={14} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2.5} strokeLinecap="round" strokeLinejoin="round">
                      <polyline points="20 6 9 17 4 12"/>
                    </svg>
                    Downloaded!
                  </span>
                ) : (
                  <span className="flex items-center gap-2">
                    <DownloadIcon size={14} />
                    Download PDF
                  </span>
                )}
              </button>

              <span className="text-xs" style={{ color: '#818cf8' }}>
                {PERIODS.find(p => p.value === dlPeriod)?.label}
              </span>
            </div>
          </div>
        </div>

      </div>
    </Layout>
  )
}
