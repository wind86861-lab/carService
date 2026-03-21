import React, { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import AdminLayout from '../../components/AdminLayout'
import StatusBadge from '../../components/StatusBadge'
import ConfirmDialog from '../../components/ConfirmDialog'
import { getAdminClientProfile, blockUser, unblockUser, promoteToMaster } from '../../api/admin'
import { ArrowLeft, Ban, CheckCircle, UserPlus } from 'lucide-react'

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
      else if (confirmAction.type === 'unblock') await unblockUser(Number(id), 'clients')
      else if (confirmAction.type === 'promote') {
        const result = await promoteToMaster(Number(id))
        showToast(`Ustaga ko'tarildi! ${result.password_generated ? 'Login ma\'lumotlari Telegram orqali yuborildi.' : ''}`)
      }
      setConfirmAction(null)
      reload()
      if (confirmAction.type !== 'promote') {
        showToast(confirmAction.type === 'block' ? 'Foydalanuvchi bloklandi.' : 'Foydalanuvchi blokdan chiqarildi.')
      }
    } catch (e) {
      showToast(e.response?.data?.detail || 'Action failed')
    } finally { setActionLoading(false) }
  }

  if (loading) return <AdminLayout><div className="p-8 text-center text-gray-400">Yuklanmoqda…</div></AdminLayout>
  if (!profile) return <AdminLayout><div className="p-8 text-center text-gray-400">Mijoz topilmadi.</div></AdminLayout>

  const { user, orders = [], feedbacks = [] } = profile

  return (
    <AdminLayout>
      {toast && <div className="fixed top-4 right-4 z-50 bg-gray-900 text-white text-sm px-4 py-2 rounded-lg shadow-lg">{toast}</div>}
      <div className="p-3 sm:p-6 max-w-5xl space-y-4 sm:space-y-6">
        <div className="flex flex-wrap items-center gap-2 sm:gap-3">
          <button onClick={() => navigate('/admin/clients')} className="btn-secondary p-2"><ArrowLeft size={16} /></button>
          <h1 className="text-lg sm:text-xl font-bold">{user.full_name}</h1>
          {user.is_active
            ? <span className="text-xs bg-green-100 text-green-700 px-2 py-0.5 rounded-full">Faol</span>
            : <span className="text-xs bg-red-100 text-red-700 px-2 py-0.5 rounded-full">Bloklangan</span>
          }
        </div>

        <div className="card">
          <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4">
            <div className="grid grid-cols-2 gap-x-4 sm:gap-x-8 gap-y-1 text-sm">
              <span className="text-gray-500">Telefon</span><span>{user.phone || '—'}</span>
              <span className="text-gray-500">Telegram ID</span><span className="font-mono text-xs">{user.telegram_id}</span>
              <span className="text-gray-500">Ro'yxatdan o'tgan</span><span>{fmtDate(user.registered_at)}</span>
              <span className="text-gray-500">Jami buyurtmalar</span><span>{orders.length}</span>
            </div>
            <div className="flex flex-wrap gap-2">
              <button
                onClick={() => setConfirmAction({ type: 'promote' })}
                className="btn-primary text-xs sm:text-sm"
              >
                <UserPlus size={14} /> Ustaga ko'tarish
              </button>
              {user.is_active
                ? <button onClick={() => setConfirmAction({ type: 'block' })} className="btn-danger text-xs sm:text-sm"><Ban size={14} /> Bloklash</button>
                : <button onClick={() => setConfirmAction({ type: 'unblock' })} className="btn-success text-xs sm:text-sm"><CheckCircle size={14} /> Blokdan chiqarish</button>
              }
            </div>
          </div>
        </div>

        <div className="flex gap-2 border-b border-gray-100 pb-0">
          {['orders', 'feedbacks'].map(t => (
            <button key={t} onClick={() => setTab(t)}
              className={`px-4 py-2 text-sm font-medium capitalize border-b-2 transition-colors ${tab === t ? 'border-blue-600 text-blue-600' : 'border-transparent text-gray-500 hover:text-gray-700'
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
                    <th className="px-4 py-3">Buyurtma №</th>
                    <th className="px-4 py-3">Mashina</th>
                    <th className="px-4 py-3">Holat</th>
                    <th className="px-4 py-3 text-right">Narx</th>
                    <th className="px-4 py-3">Sana</th>
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
              ? <div className="card text-center text-gray-400 py-8">Hali fikr-mulohaza yo'q.</div>
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
          title={
            confirmAction.type === 'promote' ? 'Ustaga ko\'tarish' :
              confirmAction.type === 'block' ? 'Mijozni bloklash' : 'Blokdan chiqarish'
          }
          message={
            confirmAction.type === 'promote'
              ? `${user.full_name} ni ustaga ko'tarasizmi? Login ma'lumotlari Telegram orqali yuboriladi.`
              : `${user.full_name} ni ${confirmAction.type === 'block' ? 'bloklash' : 'blokdan chiqarish'}ni tasdiqlaysizmi?`
          }
          confirmLabel={
            confirmAction.type === 'promote' ? 'Ko\'tarish' :
              confirmAction.type === 'block' ? 'Bloklash' : 'Blokdan chiqarish'
          }
          onClose={() => setConfirmAction(null)}
          onConfirm={handleAction}
          loading={actionLoading}
        />
      )}
    </AdminLayout>
  )
}
