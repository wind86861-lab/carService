import React, { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import AdminLayout from '../../components/AdminLayout'
import Pagination from '../../components/Pagination'
import ConfirmDialog from '../../components/ConfirmDialog'
import { getAdminMasters, blockUser, unblockUser, setUserRole } from '../../api/admin'
import { Ban, CheckCircle, ArrowUp, ArrowDown } from 'lucide-react'

function fmt(n) { return Number(n || 0).toLocaleString('ru-RU') + ' UZS' }

export default function AdminMasters() {
  const navigate = useNavigate()
  const [masters, setMasters] = useState([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [loading, setLoading] = useState(false)
  const [confirmAction, setConfirmAction] = useState(null)
  const [actionLoading, setActionLoading] = useState(false)
  const [toast, setToast] = useState('')

  const load = (p = 1) => {
    setLoading(true)
    getAdminMasters(p).then(d => { setMasters(d.items || []); setTotal(d.total || 0); setPage(p) })
      .catch(console.error).finally(() => setLoading(false))
  }

  useEffect(() => { load(1) }, [])
  const showToast = (msg) => { setToast(msg); setTimeout(() => setToast(''), 3000) }

  const handleAction = async () => {
    setActionLoading(true)
    try {
      const { id, type } = confirmAction
      if (type === 'block') await blockUser(id, 'masters')
      else if (type === 'unblock') await unblockUser(id, 'masters')
      else if (type === 'promote') await setUserRole(id, 'master')
      else if (type === 'demote') await setUserRole(id, 'client')
      setConfirmAction(null)
      load(page)
      showToast('Amal bajarildi.')
    } catch (e) {
      showToast(e.response?.data?.detail || 'Action failed')
    } finally { setActionLoading(false) }
  }

  return (
    <AdminLayout>
      {toast && <div className="fixed top-4 right-4 z-50 bg-gray-900 text-white text-sm px-4 py-2 rounded-lg shadow-lg">{toast}</div>}
      <div className="p-3 sm:p-6 space-y-3 sm:space-y-4">
        <h1 className="text-xl font-bold text-gray-900">Ustalar</h1>
        <div className="card p-0 overflow-hidden">
          <div className="px-4 py-3 border-b border-gray-50 text-sm text-gray-500">{total} ta usta</div>
          {loading ? (
            <div className="p-8 text-center text-gray-400">Yuklanmoqda…</div>
          ) : (
            <>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="bg-gray-50 text-xs font-medium text-gray-500 uppercase text-left">
                      <th className="px-4 py-3">Ism</th>
                      <th className="px-4 py-3">Telefon</th>
                      <th className="px-4 py-3 text-right">Faol</th>
                      <th className="px-4 py-3 text-right">Yopilgan</th>
                      <th className="px-4 py-3 text-right">Jami daromad</th>
                      <th className="px-4 py-3 text-right">O'rtacha baho</th>
                      <th className="px-4 py-3">Rol / Holat</th>
                      <th className="px-4 py-3" />
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-50">
                    {masters.map(m => (
                      <tr key={m.id}
                        onClick={() => navigate(`/admin/masters/${m.id}`)}
                        className="hover:bg-blue-50/40 cursor-pointer transition-colors group"
                      >
                        <td className="px-4 py-3 font-medium">{m.full_name}</td>
                        <td className="px-4 py-3 text-gray-500">{m.phone || '—'}</td>
                        <td className="px-4 py-3 text-right">{m.active_orders}</td>
                        <td className="px-4 py-3 text-right">{m.closed_orders}</td>
                        <td className="px-4 py-3 text-right text-green-700 font-medium">{fmt(m.total_earned)}</td>
                        <td className="px-4 py-3 text-right">{m.avg_rating ? Number(m.avg_rating).toFixed(1) : '—'}</td>
                        <td className="px-4 py-3">
                          <div className="flex items-center gap-1">
                            <span className={`text-xs px-2 py-0.5 rounded-full ${m.role === 'admin' ? 'bg-purple-100 text-purple-700' : 'bg-blue-100 text-blue-700'}`}>{m.role}</span>
                            {!m.is_active && <span className="text-xs bg-red-100 text-red-700 px-2 py-0.5 rounded-full">Bloklangan</span>}
                          </div>
                        </td>
                        <td className="px-4 py-3" onClick={e => e.stopPropagation()}>
                          <div className="opacity-0 group-hover:opacity-100 transition-opacity flex gap-1">
                            {m.role === 'client' && (
                              <button title="Promote to master" onClick={() => setConfirmAction({ id: m.id, type: 'promote', name: m.full_name })}
                                className="p-1.5 text-blue-500 hover:bg-blue-50 rounded"><ArrowUp size={14} /></button>
                            )}
                            {m.role === 'master' && (
                              <button title="Demote to client" onClick={() => setConfirmAction({ id: m.id, type: 'demote', name: m.full_name })}
                                className="p-1.5 text-orange-500 hover:bg-orange-50 rounded"><ArrowDown size={14} /></button>
                            )}
                            {m.is_active
                              ? <button title="Block" onClick={() => setConfirmAction({ id: m.id, type: 'block', name: m.full_name })}
                                className="p-1.5 text-red-500 hover:bg-red-50 rounded"><Ban size={14} /></button>
                              : <button title="Unblock" onClick={() => setConfirmAction({ id: m.id, type: 'unblock', name: m.full_name })}
                                className="p-1.5 text-green-500 hover:bg-green-50 rounded"><CheckCircle size={14} /></button>
                            }
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <div className="px-4 border-t border-gray-50">
                <Pagination total={total} page={page} pageSize={20} onChange={p => load(p)} />
              </div>
            </>
          )}
        </div>
      </div>

      {confirmAction && (
        <ConfirmDialog
          title={({ block: 'Bloklash', unblock: 'Blokdan chiqarish', promote: 'Ustaga ko\'tarish', demote: 'Mijozga tushirish' })[confirmAction.type]}
          message={`${confirmAction.name} uchun amalni tasdiqlaysizmi?`}
          confirmLabel={({ block: 'Bloklash', unblock: 'Blokdan chiqarish', promote: 'Ko\'tarish', demote: 'Tushirish' })[confirmAction.type]}
          onClose={() => setConfirmAction(null)}
          onConfirm={handleAction}
          loading={actionLoading}
          danger={['block', 'demote'].includes(confirmAction.type)}
        />
      )}
    </AdminLayout>
  )
}
