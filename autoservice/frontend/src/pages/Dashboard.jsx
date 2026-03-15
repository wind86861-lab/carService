import React, { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { getOrders, getFinancialSummary } from '../api/client'
import { useAuth } from '../App'
import StatusBadge from '../components/StatusBadge'
import { Plus, LogOut, BarChart2, Car, Clock, CheckCircle, DollarSign } from 'lucide-react'

function fmt(n) {
  return Number(n || 0).toLocaleString('ru-RU') + ' UZS'
}
function fmtDate(d) {
  if (!d) return '—'
  return new Date(d).toLocaleDateString('ru-RU', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' })
}

export default function Dashboard() {
  const navigate = useNavigate()
  const { logout } = useAuth()
  const [orders, setOrders] = useState([])
  const [summary, setSummary] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([getOrders(), getFinancialSummary({ period: 'month' })])
      .then(([ords, sum]) => { setOrders(ords); setSummary(sum) })
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [])

  const active = orders.filter(o => ['new','preparation','in_process'].includes(o.status))
  const ready = orders.filter(o => o.status === 'ready')
  const closed = orders.filter(o => o.status === 'closed')

  const cards = [
    { label: 'Active Orders', value: active.length, icon: Clock, color: 'text-blue-600', bg: 'bg-blue-50' },
    { label: 'Ready for Pickup', value: ready.length, icon: Car, color: 'text-green-600', bg: 'bg-green-50' },
    { label: 'Closed This Month', value: summary?.order_count ?? 0, icon: CheckCircle, color: 'text-purple-600', bg: 'bg-purple-50' },
    { label: 'Earned This Month', value: fmt(summary?.total_master_share), icon: DollarSign, color: 'text-yellow-600', bg: 'bg-yellow-50' },
  ]

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b border-gray-100 sticky top-0 z-10">
        <div className="max-w-6xl mx-auto px-4 py-3 flex items-center justify-between">
          <h1 className="text-lg font-bold text-gray-900">AutoService Dashboard</h1>
          <div className="flex items-center gap-2">
            <button onClick={() => navigate('/statistics')} className="btn-secondary">
              <BarChart2 size={16} /> Statistics
            </button>
            <button onClick={() => navigate('/new-order')} className="btn-primary">
              <Plus size={16} /> New Order
            </button>
            <button onClick={() => { logout(); navigate('/login') }} className="btn-secondary text-red-600">
              <LogOut size={16} />
            </button>
          </div>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-4 py-6 space-y-6">
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          {cards.map(({ label, value, icon: Icon, color, bg }) => (
            <div key={label} className="card">
              <div className={`w-10 h-10 ${bg} rounded-xl flex items-center justify-center mb-3`}>
                <Icon size={20} className={color} />
              </div>
              <p className="text-2xl font-bold text-gray-900">{loading ? '…' : value}</p>
              <p className="text-sm text-gray-500 mt-0.5">{label}</p>
            </div>
          ))}
        </div>

        <div className="card p-0 overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-50 flex items-center justify-between">
            <h2 className="font-semibold text-gray-800">All Orders</h2>
            <span className="text-sm text-gray-500">{orders.length} total</span>
          </div>
          {loading ? (
            <div className="p-8 text-center text-gray-400">Loading…</div>
          ) : orders.length === 0 ? (
            <div className="p-8 text-center">
              <p className="text-gray-500 mb-4">No orders yet.</p>
              <button onClick={() => navigate('/new-order')} className="btn-primary">Create First Order</button>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="bg-gray-50 text-left text-xs font-medium text-gray-500 uppercase tracking-wide">
                    <th className="px-6 py-3">Order #</th>
                    <th className="px-6 py-3">Car</th>
                    <th className="px-6 py-3">Client</th>
                    <th className="px-6 py-3">Status</th>
                    <th className="px-6 py-3">Price</th>
                    <th className="px-6 py-3">Created</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-50">
                  {orders.map(o => (
                    <tr
                      key={o.order_number}
                      onClick={() => navigate(`/orders/${o.order_number}`)}
                      className="hover:bg-blue-50/50 cursor-pointer transition-colors"
                    >
                      <td className="px-6 py-3 font-mono font-bold text-blue-700">{o.order_number}</td>
                      <td className="px-6 py-3">
                        <div>{`${o.brand||''} ${o.model||''}`.trim() || '—'}</div>
                        {o.plate && <div className="text-xs text-gray-400 font-mono">{o.plate}</div>}
                      </td>
                      <td className="px-6 py-3 text-gray-600">{o.client_name || '—'}</td>
                      <td className="px-6 py-3"><StatusBadge status={o.status} /></td>
                      <td className="px-6 py-3 font-medium">{fmt(o.agreed_price)}</td>
                      <td className="px-6 py-3 text-gray-500">{fmtDate(o.created_at)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </main>
    </div>
  )
}
