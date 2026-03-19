import React, { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import AdminLayout from '../../components/AdminLayout'
import StatusBadge from '../../components/StatusBadge'
import ConfirmDialog from '../../components/ConfirmDialog'
import { getAdminMasterProfile, blockUser, unblockUser, setUserRole } from '../../api/admin'
import { ArrowLeft, Ban, CheckCircle, ArrowUp, ArrowDown } from 'lucide-react'

function fmt(n) { return Number(n || 0).toLocaleString('ru-RU') + ' UZS' }
function fmtDate(d) {
  if (!d) return '—'
  return new Date(d).toLocaleDateString('ru-RU', { day: '2-digit', month: '2-digit', year: 'numeric' })
}
const STARS = r => '★'.repeat(r) + '☆'.repeat(10 - r)
const PERIODS = [{ value: 'month', label: 'This Month' }, { value: 'week', label: 'This Week' }, { value: 'all', label: 'All Time' }]

function periodDates(p) {
  const now = new Date()
  if (p === 'week') {
    const from = new Date(now); from.setDate(now.getDate() - 7)
    return { date_from: from.toISOString().slice(0, 10), date_to: now.toISOString().slice(0, 10) }
  }
  if (p === 'month') {
    const from = new Date(now.getFullYear(), now.getMonth(), 1)
    return { date_from: from.toISOString().slice(0, 10), date_to: now.toISOString().slice(0, 10) }
  }
  return {}
}

export default function AdminMasterProfile() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [profile, setProfile] = useState(null)
  const [loading, setLoading] = useState(true)
  const [period, setPeriod] = useState('month')
  const [tab, setTab] = useState('orders')
  const [confirmAction, setConfirmAction] = useState(null)
  const [actionLoading, setActionLoading] = useState(false)
  const [toast, setToast] = useState('')

  const load = () => {
    const { date_from, date_to } = periodDates(period)
    setLoading(true)
    getAdminMasterProfile(Number(id), date_from, date_to)
      .then(setProfile).catch(console.error).finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [id, period])
  const showToast = (msg) => { setToast(msg); setTimeout(() => setToast(''), 3000) }

  const handleAction = async () => {
    setActionLoading(true)
    try {
      const { type } = confirmAction
      if (type === 'block') await blockUser(Number(id), 'masters')
      else if (type === 'unblock') await unblockUser(Number(id), 'masters')
      else if (type === 'promote') await setUserRole(Number(id), 'master')
      else if (type === 'demote') await setUserRole(Number(id), 'client')
      setConfirmAction(null); load()
      showToast('Action completed.')
    } catch (e) {
      showToast(e.response?.data?.detail || 'Action failed')
    } finally { setActionLoading(false) }
  }

  if (!profile && !loading) return <AdminLayout><div className="p-8 text-center text-gray-400">Master not found.</div></AdminLayout>

  const user = profile?.user || {}
  const stats = profile?.stats || {}
  const orders = profile?.orders || []
  const feedbacks = profile?.feedbacks || []

  const kpis = [
    { label: 'Orders', value: stats.order_count ?? 0 },
    { label: 'Revenue', value: fmt(stats.revenue) },
    { label: 'Profit', value: fmt(stats.profit) },
    { label: 'Master Earned', value: fmt(stats.master_earned) },
  ]

  return (
    <AdminLayout>
      {toast && <div className="fixed top-4 right-4 z-50 bg-gray-900 text-white text-sm px-4 py-2 rounded-lg shadow-lg">{toast}</div>}
      <div className="p-6 max-w-5xl space-y-6">
        <div className="flex items-center gap-3">
          <button onClick={() => navigate('/admin/masters')} className="btn-secondary p-2"><ArrowLeft size={16} /></button>
          <h1 className="text-xl font-bold">{user.full_name || '…'}</h1>
          {user.role && <span className={`text-xs px-2 py-0.5 rounded-full ${user.role === 'admin' ? 'bg-purple-100 text-purple-700' : 'bg-blue-100 text-blue-700'}`}>{user.role}</span>}
          {!user.is_active && <span className="text-xs bg-red-100 text-red-700 px-2 py-0.5 rounded-full">Blocked</span>}
        </div>

        {!loading && (
          <div className="card">
            <div className="flex items-start justify-between">
              <div className="grid grid-cols-2 gap-x-8 gap-y-1 text-sm">
                <span className="text-gray-500">Username</span><span className="font-mono">{user.username || '—'}</span>
                <span className="text-gray-500">Phone</span><span>{user.phone || '—'}</span>
                <span className="text-gray-500">Telegram ID</span><span className="font-mono">{user.telegram_id || '—'}</span>
              </div>
              <div className="flex gap-2">
                {user.role === 'master' && (
                  <button onClick={() => setConfirmAction({ type: 'demote' })} className="btn-secondary"><ArrowDown size={14} /> Demote</button>
                )}
                {user.role === 'client' && (
                  <button onClick={() => setConfirmAction({ type: 'promote' })} className="btn-primary"><ArrowUp size={14} /> Promote</button>
                )}
                {user.is_active
                  ? <button onClick={() => setConfirmAction({ type: 'block' })} className="btn-danger"><Ban size={14} /> Block</button>
                  : <button onClick={() => setConfirmAction({ type: 'unblock' })} className="btn-success"><CheckCircle size={14} /> Unblock</button>
                }
              </div>
            </div>
          </div>
        )}

        <div className="flex gap-1 flex-wrap">
          {PERIODS.map(p => (
            <button key={p.value} onClick={() => setPeriod(p.value)}
              className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${period === p.value ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'}`}
            >{p.label}</button>
          ))}
        </div>

        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          {kpis.map(({ label, value }) => (
            <div key={label} className="card text-center">
              <p className="text-xl font-bold">{loading ? '…' : value}</p>
              <p className="text-xs text-gray-500 mt-0.5">{label}</p>
            </div>
          ))}
        </div>

        <div className="flex gap-2 border-b border-gray-100">
          {['orders', 'feedbacks'].map(t => (
            <button key={t} onClick={() => setTab(t)}
              className={`px-4 py-2 text-sm font-medium capitalize border-b-2 transition-colors ${tab === t ? 'border-blue-600 text-blue-600' : 'border-transparent text-gray-500 hover:text-gray-700'}`}
            >{t} ({t === 'orders' ? orders.length : feedbacks.length})</button>
          ))}
        </div>

        {tab === 'orders' && (
          <div className="card p-0 overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="bg-gray-50 text-xs font-medium text-gray-500 uppercase text-left">
                    <th className="px-4 py-3">Order #</th>
                    <th className="px-4 py-3">Car</th>
                    <th className="px-4 py-3">Status</th>
                    <th className="px-4 py-3 text-right">Revenue</th>
                    <th className="px-4 py-3 text-right">Profit</th>
                    <th className="px-4 py-3 text-right">M.Share</th>
                    <th className="px-4 py-3">Date</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-50">
                  {orders.map(o => (
                    <tr key={o.order_number}
                      onClick={() => navigate(`/admin/orders/${o.order_number}`)}
                      className="hover:bg-blue-50/40 cursor-pointer"
                    >
                      <td className="px-4 py-3 font-mono font-bold text-blue-700">{o.order_number}</td>
                      <td className="px-4 py-3">{`${o.brand || ''} ${o.model || ''}`.trim() || '—'}</td>
                      <td className="px-4 py-3"><StatusBadge status={o.status} /></td>
                      <td className="px-4 py-3 text-right">{fmt(o.agreed_price)}</td>
                      <td className={`px-4 py-3 text-right ${Number(o.profit) < 0 ? 'text-red-600' : ''}`}>{fmt(o.profit)}</td>
                      <td className="px-4 py-3 text-right text-green-700">{fmt(o.master_share)}</td>
                      <td className="px-4 py-3 text-gray-400 text-xs">{fmtDate(o.created_at)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {tab === 'feedbacks' && (
          <div className="space-y-3">
            {feedbacks.length === 0
              ? <div className="card text-center text-gray-400 py-8">No feedbacks yet.</div>
              : feedbacks.map(f => (
                <div key={f.id} className="card">
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-yellow-500 text-sm">{STARS(f.rating)}</span>
                    <span className="text-xs text-gray-400">{f.client_name} · {f.order_number}</span>
                  </div>
                  {f.category && <span className="text-xs bg-blue-100 text-blue-700 px-2 py-0.5 rounded-full">{f.category}</span>}
                  {f.comment && <p className="mt-2 text-sm text-gray-600">{f.comment}</p>}
                </div>
              ))
            }
          </div>
        )}
      </div>

      {confirmAction && (
        <ConfirmDialog
          title={confirmAction.type.charAt(0).toUpperCase() + confirmAction.type.slice(1)}
          message={`Are you sure you want to ${confirmAction.type} ${user.full_name}?`}
          confirmLabel={confirmAction.type.charAt(0).toUpperCase() + confirmAction.type.slice(1)}
          onClose={() => setConfirmAction(null)}
          onConfirm={handleAction}
          loading={actionLoading}
          danger={['block', 'demote'].includes(confirmAction.type)}
        />
      )}
    </AdminLayout>
  )
}
