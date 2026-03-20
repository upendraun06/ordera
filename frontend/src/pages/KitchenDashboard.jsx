import { useState, useEffect, useCallback, useRef } from 'react'
import Layout from '../components/Layout'
import StatCard from '../components/StatCard'
import OrderCard from '../components/OrderCard'
import { dashboardApi } from '../services/api'
import { useAuth } from '../context/AuthContext'
import { printKitchenTicket } from '../utils/printTicket'
import {
  DashboardIcon, RefreshIcon,
  OrdersIcon, CheckIcon, AnalyticsIcon, PhoneIcon,
} from '../components/Icons'

const REFRESH_INTERVAL = 5000
const TABS = ['Active', 'Ready', 'Completed', 'All']

/* Skeleton loaders */
function StatSkeleton() {
  return (
    <div className="card flex items-center gap-4">
      <div className="skeleton rounded-2xl flex-shrink-0" style={{ width: 48, height: 48 }} />
      <div className="flex-1 space-y-2">
        <div className="skeleton h-7 w-16 rounded-md" />
        <div className="skeleton h-3.5 w-24 rounded" />
      </div>
    </div>
  )
}
function OrderSkeleton() {
  return (
    <div className="card space-y-3">
      <div className="flex justify-between">
        <div className="space-y-2">
          <div className="skeleton h-4 w-28 rounded" />
          <div className="skeleton h-3 w-20 rounded" />
        </div>
        <div className="skeleton h-6 w-16 rounded-full" />
      </div>
      <div className="divider" />
      <div className="space-y-2">
        <div className="skeleton h-3.5 w-36 rounded" />
        <div className="skeleton h-3.5 w-28 rounded" />
      </div>
      <div className="skeleton h-9 rounded-xl" />
    </div>
  )
}

/* Toast notification for new orders */
function NewOrderToast({ order, onClose }) {
  useEffect(() => {
    const t = setTimeout(onClose, 5000)
    return () => clearTimeout(t)
  }, [onClose])

  return (
    <div
      className="animate-slide-in"
      style={{
        position: 'fixed',
        top: 20,
        right: 20,
        zIndex: 9999,
        background: '#0d1117',
        border: '1px solid rgba(99,102,241,0.5)',
        borderLeft: '4px solid #6366f1',
        borderRadius: 12,
        padding: '14px 18px',
        boxShadow: '0 8px 32px rgba(0,0,0,0.3)',
        minWidth: 280,
        display: 'flex',
        alignItems: 'flex-start',
        gap: 12,
      }}
    >
      {/* Pulse ring */}
      <div style={{ position: 'relative', flexShrink: 0, marginTop: 2 }}>
        <span className="live-dot" style={{ background: '#6366f1' }} />
      </div>
      <div style={{ flex: 1 }}>
        <div style={{ color: '#fff', fontWeight: 600, fontSize: 13 }}>
          New Order — {order.customer_name}
        </div>
        <div style={{ color: 'rgba(255,255,255,0.45)', fontSize: 12, marginTop: 2 }}>
          {order.items?.length} item{order.items?.length !== 1 ? 's' : ''} · ${order.total?.toFixed(2)}
        </div>
        <div style={{ color: '#a5b4fc', fontSize: 11, marginTop: 4 }}>
          Ticket printed automatically
        </div>
      </div>
      <button
        onClick={onClose}
        style={{ color: 'rgba(255,255,255,0.3)', fontSize: 16, background: 'none', border: 'none', cursor: 'pointer', lineHeight: 1, padding: 0, marginTop: 1 }}
      >
        ×
      </button>
    </div>
  )
}

export default function KitchenDashboard() {
  const { owner }                       = useAuth()
  const [data,        setData]          = useState(null)
  const [activeTab,   setActiveTab]     = useState('Active')
  const [loading,     setLoading]       = useState(true)
  const [lastRefresh, setLastRefresh]   = useState(null)
  const [spinning,    setSpinning]      = useState(false)
  const [toasts,      setToasts]        = useState([])   // [{id, order}]

  // Track order IDs we've already seen so we only auto-print new arrivals
  const seenOrderIds = useRef(new Set())
  const isFirstLoad  = useRef(true)

  const restaurantName = owner?.restaurant_name || "Mario's Pizza"

  const dismissToast = (id) => setToasts(prev => prev.filter(t => t.id !== id))

  const fetchStats = useCallback(async (manual = false) => {
    if (manual) setSpinning(true)
    try {
      const res = await dashboardApi.stats()
      const orders = res.data?.orders || []

      // Detect brand-new orders (status='new') not seen before
      if (!isFirstLoad.current) {
        const freshOrders = orders.filter(
          o => o.status === 'new' && !seenOrderIds.current.has(o.id)
        )
        freshOrders.forEach(order => {
          // Auto-print ticket
          printKitchenTicket(order, restaurantName)
          // Show toast
          const toastId = order.id
          setToasts(prev => [...prev, { id: toastId, order }])
        })
      }

      // Update seen IDs
      orders.forEach(o => seenOrderIds.current.add(o.id))
      isFirstLoad.current = false

      setData(res.data)
      setLastRefresh(new Date())
    } catch (e) {
      console.error('Dashboard fetch error', e)
    } finally {
      setLoading(false)
      if (manual) setTimeout(() => setSpinning(false), 600)
    }
  }, [restaurantName])

  useEffect(() => {
    fetchStats()
    const interval = setInterval(() => fetchStats(), REFRESH_INTERVAL)
    return () => clearInterval(interval)
  }, [fetchStats])

  const filterOrders = (orders) => {
    if (!orders) return []
    switch (activeTab) {
      case 'Active':    return orders.filter(o => ['new', 'confirmed', 'preparing'].includes(o.status))
      case 'Ready':     return orders.filter(o => o.status === 'ready')
      case 'Completed': return orders.filter(o => ['picked_up', 'cancelled'].includes(o.status))
      default:          return orders
    }
  }

  const filtered = filterOrders(data?.orders)
  const newCount = data?.orders?.filter(o => o.status === 'new').length || 0

  return (
    <Layout>
      {/* ── Auto-print toast stack ── */}
      <div style={{ position: 'fixed', top: 0, right: 0, zIndex: 9999, display: 'flex', flexDirection: 'column', gap: 10, padding: 20 }}>
        {toasts.map(t => (
          <NewOrderToast key={t.id} order={t.order} onClose={() => dismissToast(t.id)} />
        ))}
      </div>

      <div className="p-6 max-w-7xl mx-auto">

        {/* ── Header ── */}
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-3">
            <div
              className="flex items-center justify-center rounded-xl"
              style={{ width: 40, height: 40, background: 'var(--primary-light)' }}
            >
              <DashboardIcon size={18} className="text-indigo-600" />
            </div>
            <div>
              <h1 className="text-xl font-bold" style={{ color: 'var(--text-1)' }}>
                Kitchen Dashboard
              </h1>
              <div className="flex items-center gap-2 mt-0.5">
                <span className="live-dot" />
                <span className="text-xs" style={{ color: 'var(--text-3)' }}>
                  {lastRefresh
                    ? `Updated ${lastRefresh.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}`
                    : 'Loading...'}
                </span>
              </div>
            </div>
          </div>

          <button
            onClick={() => fetchStats(true)}
            className="btn-secondary"
            style={{ padding: '8px 14px' }}
          >
            <RefreshIcon size={14} className={spinning ? 'animate-spin-slow' : ''} />
            Refresh
          </button>
        </div>

        {/* ── Stat Cards ── */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
          {loading ? (
            <><StatSkeleton /><StatSkeleton /><StatSkeleton /><StatSkeleton /></>
          ) : data ? (
            <>
              <StatCard label="Active Orders"    value={data.active_orders}   icon={OrdersIcon}   color="yellow" />
              <StatCard label="Ready for Pickup" value={data.ready_orders}    icon={CheckIcon}    color="green"  />
              <StatCard label="Completed Today"  value={data.completed_orders} icon={AnalyticsIcon} color="blue" />
              <StatCard
                label="Revenue Today"
                value={`$${(data.revenue_today || 0).toFixed(2)}`}
                icon={PhoneIcon}
                color="purple"
                sub={`${data.total_orders_today} total orders`}
              />
            </>
          ) : null}
        </div>

        {/* ── Tabs ── */}
        <div className="flex items-center gap-2 mb-5">
          {TABS.map(tab => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`tab-btn ${activeTab === tab ? 'active' : ''}`}
            >
              {tab}
              {tab === 'Active' && newCount > 0 && (
                <span
                  className="ml-1.5 inline-flex items-center justify-center text-xs font-bold rounded-full"
                  style={{
                    width: 18, height: 18,
                    background: activeTab === tab ? 'rgba(255,255,255,0.25)' : '#fef9c3',
                    color: activeTab === tab ? 'white' : '#92400e',
                    fontSize: 10,
                  }}
                >
                  {newCount}
                </span>
              )}
            </button>
          ))}
        </div>

        {/* ── Orders grid ── */}
        {loading ? (
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
            <OrderSkeleton /><OrderSkeleton /><OrderSkeleton />
          </div>
        ) : filtered.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-20 animate-fade-in">
            <div
              className="flex items-center justify-center rounded-2xl mb-4"
              style={{ width: 64, height: 64, background: 'var(--primary-light)' }}
            >
              <OrdersIcon size={28} className="text-indigo-400" />
            </div>
            <div className="font-semibold text-base" style={{ color: 'var(--text-2)' }}>
              No {activeTab.toLowerCase()} orders
            </div>
            <div className="text-sm mt-1" style={{ color: 'var(--text-3)' }}>
              {activeTab === 'Active'
                ? 'New orders will appear here automatically'
                : 'Nothing to show for this filter'}
            </div>
          </div>
        ) : (
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
            {filtered.map((order, i) => (
              <div key={order.id} style={{ animationDelay: `${i * 50}ms` }}>
                <OrderCard
                  order={order}
                  onStatusChange={fetchStats}
                  restaurantName={restaurantName}
                />
              </div>
            ))}
          </div>
        )}

      </div>
    </Layout>
  )
}
