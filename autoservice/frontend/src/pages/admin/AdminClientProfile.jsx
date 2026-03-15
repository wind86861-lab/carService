import React, { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import AdminLayout from '../../components/AdminLayout'
import StatusBadge from '../../components/StatusBadge'
import ConfirmDialog from '../../components/ConfirmDialog'
import { getAdminClientProfile, blockUser, unblockUser } from '../../api/admin'
import { ArrowLeft, Ban, CheckCircle } from 'lucide-react'

function fmt(n) { return Number(n || 0).toLocaleString('ru-RU') + ' UZS' }
function fmtDate(d) {
  if (!d) return '—'
  return new Date(d).toLocaleDateString('ru-RU', { day: '2-digit', month: '2-digit', year: 'numeric' })
}
const STARS = r => '★'.repeat(r) + '☆'.repeat(10 - r)

export default function AdminClientProfile() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [profile, setProfile] = useState(null)
  const [loading, setLoading] = useState(true)
  const [tab, setTab] = useState('orders')
  const [confirmAction, setConfirmAction] = useState(null)
  const [actionLoading, setActionLoading] = useState(false)
  const [toast, setToast] = useState('')

  const reload = () => {
    getAdminClientProfile(Number(id)).then(setProfile).catch(console.error).finally(() => setLoading(false))
  }
  useEffect(() => { reload() }, [id])

  const showToast = (msg) => { setToast(msg); setTimeout(() => setToast(''), 3000) }

  const handleAction = async () => {
    setActionLoading(true)
    try {
      if (confirmAction.type === 'block') await blockUser(Number(id), 'clients')
      else await unblockUser(Number(id), 'clients')
      setConfirmAction(null)
      reload()
      showToast(confirmAction.type === 'block' ? 'User blocked.' : 'User unblocked.')
    } catch (e) {
      showToast(e.response?.data?.detail || 'Action failed')
    } finally { setActionLoading(false) }
  }

  if (loading) return <AdminLayout><div className="p-8 text-center text-gray-400">Loading…</div></AdminLayout>
  if (!profile) return <AdminLayout><div className="p-8 text-center text-gray-400">Client not found.</div></AdminLayout>

  const { user, orders = [], feedbacks = [] } = profile

  return (
    <AdminLayout>
      {toast && <div className="fixed top-4 right-4 z-50 bg-gray-900 text-white text-sm px-4 py-2 rounded-lg shadow-lg">{toast}</div>}
      <div className="p-6 max-w-5xl space-y-6">
        <div className="flex items-center gap-3">
          <button onClick={() => navigate('/admin/clients')} className="btn-secondary p-2"><ArrowLeft size={16} /></button>
          <h1 className="text-xl font-bold">{user.full_name}</h1>
          {user.is_active
            ? <span className="text-xs bg-green-100 text-green-700 px-2 py-0.5 rounded-full">Active</span>
            : <span className="text-xs bg-red-100 text-red-700 px-2 py-0.5 rounded-full">Blocked</span>
          }
        </div>

        <div className="card">
          <div className="flex items-start justify-between">
            <div className="grid grid-cols-2 gap-x-8 gap-y-1 text-sm">
              <span className="text-gray-500">Phone</span><span>{user.phone || '—'}</span>
              <span className="text-gray-500">Telegram ID</span><span className="font-mono">{user.telegram_id}</span>
              <span className="text-gray-500">Registered</span><span>{fmtDate(user.registered_at)}</span>
              <span className="text-gray-500">Total Orders</span><span>{orders.length}</span>
            </div>
            <div>
              {user.is_active
                ? <button onClick={() => setConfirmAction({ type: 'block' })} className="btn-danger"><Ban size={14} /> Block</button>
                : <button onClick={() => setConfirmAction({ type: 'unblock' })} className="btn-success"><CheckCircle size={14} /> Unblock</button>
              }
            </div>
          </div>
        </div>

        <div className="flex gap-2 border-b border-gray-100 pb-0">
          {['orders', 'feedbacks'].map(t => (
            <button key={t} onClick={() => setTab(t)}
              className={`px-4 py-2 text-sm font-medium capitalize border-b-2 transition-colors ${
                tab === t ? 'border-blue-600 text-blue-600' : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
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
                    <th className="px-4 py-3 text-right">Price</th>
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
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-yellow-500 text-sm">{STARS(f.rating)}</span>
                    <span className="font-mono text-xs text-gray-400">{f.order_number}</span>
                  </div>
                  {f.category && <span className="text-xs bg-blue-100 text-blue-700 px-2 py-0.5 rounded-full">{f.category}</span>}
                  {f.comment && <p className="mt-2 text-sm text-gray-600">{f.comment}</p>}
                  <p className="text-xs text-gray-400 mt-2">{fmtDate(f.created_at)}</p>
                </div>
              ))
            }
          </div>
        )}
      </div>

      {confirmAction && (
        <ConfirmDialog
          title={confirmAction.type === 'block' ? 'Block Client' : 'Unblock Client'}
          message={`Are you sure you want to ${confirmAction.type} ${user.full_name}?`}
          confirmLabel={confirmAction.type === 'block' ? 'Block' : 'Unblock'}
          onClose={() => setConfirmAction(null)}
          onConfirm={handleAction}
          loading={actionLoading}
        />
      )}
    </AdminLayout>
  )
}
