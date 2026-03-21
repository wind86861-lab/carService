import React, { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import AdminLayout from '../../components/AdminLayout'
import StatusBadge from '../../components/StatusBadge'
import { getDashboard, getAdminOrders, getFeedbackStats } from '../../api/admin'
import { Activity, Clock, TrendingUp, DollarSign, Users, Wrench } from 'lucide-react'

function fmt(n) { return Number(n || 0).toLocaleString('ru-RU') + ' UZS' }
function fmtDate(d) {
  if (!d) return '—'
  return new Date(d).toLocaleDateString('ru-RU', { day: '2-digit', month: '2-digit', year: '2-digit', hour: '2-digit', minute: '2-digit' })
}

export default function AdminDashboard() {
  const navigate = useNavigate()
  const [stats, setStats] = useState(null)
  const [recentOrders, setRecentOrders] = useState([])
  const [lowRatings, setLowRatings] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([
      getDashboard(),
      getAdminOrders({}, 1),
    ]).then(([s, o]) => {
      setStats(s)
      setRecentOrders((o.items || []).slice(0, 10))
    }).catch(console.error).finally(() => setLoading(false))
  }, [])

  const kpis = stats ? [
    { label: 'Faol buyurtmalar', value: stats.active_orders, icon: Activity, color: 'text-blue-600', bg: 'bg-blue-50' },
    { label: 'Tayyor (olishga)', value: stats.ready_orders, icon: Clock, color: 'text-yellow-600', bg: 'bg-yellow-50' },
    { label: 'Oylik daromad', value: fmt(stats.month_revenue), icon: TrendingUp, color: 'text-green-600', bg: 'bg-green-50' },
    { label: 'Oylik foyda', value: fmt(stats.month_profit), icon: DollarSign, color: 'text-purple-600', bg: 'bg-purple-50' },
    { label: 'Faol mijozlar', value: stats.total_clients, icon: Users, color: 'text-cyan-600', bg: 'bg-cyan-50' },
    { label: 'Faol ustalar', value: stats.total_masters, icon: Wrench, color: 'text-orange-600', bg: 'bg-orange-50' },
  ] : []

  return (
    <AdminLayout>
      <div className="p-3 sm:p-6 space-y-4 sm:space-y-6">
        <h1 className="text-xl font-bold text-gray-900">Boshqaruv paneli</h1>

        <div className="grid grid-cols-1 xs:grid-cols-2 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-3 sm:gap-4">
          {loading
            ? Array(6).fill(0).map((_, i) => <div key={i} className="card h-28 animate-pulse bg-gray-100" />)
            : kpis.map(({ label, value, icon: Icon, color, bg }) => (
              <div key={label} className="card">
                <div className={`w-9 h-9 ${bg} rounded-xl flex items-center justify-center mb-2`}>
                  <Icon size={18} className={color} />
                </div>
                <p className="text-lg sm:text-xl font-bold text-gray-900">{value}</p>
                <p className="text-xs text-gray-500 mt-0.5">{label}</p>
              </div>
            ))
          }
        </div>

        <div className="card p-0 overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-50">
            <h2 className="font-semibold text-gray-800">So'nggi buyurtmalar</h2>
          </div>
          {loading ? (
            <div className="p-8 text-center text-gray-400">Yuklanmoqda…</div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="bg-gray-50 text-xs font-medium text-gray-500 uppercase text-left">
                    <th className="px-4 py-3">Buyurtma №</th>
                    <th className="px-4 py-3">Mashina</th>
                    <th className="px-4 py-3">Mijoz</th>
                    <th className="px-4 py-3">Usta</th>
                    <th className="px-4 py-3">Holat</th>
                    <th className="px-4 py-3">Sana</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-50">
                  {recentOrders.map(o => (
                    <tr key={o.order_number}
                      onClick={() => navigate(`/admin/orders/${o.order_number}`)}
                      className="hover:bg-blue-50/40 cursor-pointer transition-colors"
                    >
                      <td className="px-4 py-3 font-mono font-bold text-blue-700">{o.order_number}</td>
                      <td className="px-4 py-3">{`${o.brand || ''} ${o.model || ''}`.trim() || '—'}</td>
                      <td className="px-4 py-3 text-gray-600">{o.client_name || '—'}</td>
                      <td className="px-4 py-3 text-gray-600">{o.master_name || '—'}</td>
                      <td className="px-4 py-3"><StatusBadge status={o.status} /></td>
                      <td className="px-4 py-3 text-gray-400">{fmtDate(o.created_at)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </AdminLayout>
  )
}
