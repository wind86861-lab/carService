import React, { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import AdminLayout from '../../components/AdminLayout'
import Pagination from '../../components/Pagination'
import ConfirmDialog from '../../components/ConfirmDialog'
import { getAdminClients, blockUser, unblockUser } from '../../api/admin'
import { Search, Ban, CheckCircle } from 'lucide-react'

function fmtDate(d) {
  if (!d) return '—'
  return new Date(d).toLocaleDateString('ru-RU', { day: '2-digit', month: '2-digit', year: 'numeric' })
}

export default function AdminClients() {
  const navigate = useNavigate()
  const [clients, setClients] = useState([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [search, setSearch] = useState('')
  const [showBlocked, setShowBlocked] = useState(false)
  const [loading, setLoading] = useState(false)
  const [confirmAction, setConfirmAction] = useState(null)
  const [actionLoading, setActionLoading] = useState(false)
  const [toast, setToast] = useState('')

  const load = (p = 1) => {
    setLoading(true)
    const isActive = showBlocked ? undefined : true
    getAdminClients(search || undefined, isActive, p)
      .then(d => { setClients(d.items || []); setTotal(d.total || 0); setPage(p) })
      .catch(console.error)
      .finally(() => setLoading(false))
  }

  useEffect(() => { load(1) }, [showBlocked])

  const showToast = (msg) => { setToast(msg); setTimeout(() => setToast(''), 3000) }

  const handleAction = async () => {
    setActionLoading(true)
    try {
      if (confirmAction.type === 'block') await blockUser(confirmAction.id, 'clients')
      else await unblockUser(confirmAction.id, 'clients')
      setConfirmAction(null)
      load(page)
      showToast(confirmAction.type === 'block' ? 'Foydalanuvchi bloklandi.' : 'Foydalanuvchi blokdan chiqarildi.')
    } catch (e) {
      showToast(e.response?.data?.detail || 'Action failed')
    } finally { setActionLoading(false) }
  }

  return (
    <AdminLayout>
      {toast && <div className="fixed top-4 right-4 z-50 bg-gray-900 text-white text-sm px-4 py-2 rounded-lg shadow-lg">{toast}</div>}
      <div className="p-3 sm:p-6 space-y-3 sm:space-y-4">
        <h1 className="text-xl font-bold text-gray-900">Mijozlar</h1>

        <div className="card p-3 sm:p-4 flex flex-col sm:flex-row flex-wrap items-stretch sm:items-center gap-3">
          <div className="flex gap-2 flex-1">
            <input
              className="input flex-1" placeholder="Ism yoki telefon bo'yicha qidirish…"
              value={search} onChange={e => setSearch(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && load(1)}
            />
            <button onClick={() => load(1)} className="btn-primary px-3"><Search size={16} /></button>
          </div>
          <label className="flex items-center gap-2 text-sm text-gray-600 cursor-pointer select-none">
            <input type="checkbox" className="rounded" checked={showBlocked} onChange={e => setShowBlocked(e.target.checked)} />
            Bloklangan foydalanuvchilarni ko'rsatish
          </label>
        </div>

        <div className="card p-0 overflow-hidden">
          <div className="px-4 py-3 border-b border-gray-50 text-sm text-gray-500">{total} ta mijoz</div>
          {loading ? (
            <div className="p-8 text-center text-gray-400">Yuklanmoqda…</div>
          ) : clients.length === 0 ? (
            <div className="p-8 text-center text-gray-400">Mijozlar topilmadi.</div>
          ) : (
            <>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="bg-gray-50 text-xs font-medium text-gray-500 uppercase text-left">
                      <th className="px-4 py-3">Ism</th>
                      <th className="px-4 py-3">Telefon</th>
                      <th className="px-4 py-3">Telegram ID</th>
                      <th className="px-4 py-3 text-right">Buyurtmalar</th>
                      <th className="px-4 py-3 text-right">O'rtacha baho</th>
                      <th className="px-4 py-3">Oxirgi tashrif</th>
                      <th className="px-4 py-3">Holat</th>
                      <th className="px-4 py-3" />
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-50">
                    {clients.map(c => (
                      <tr key={c.id}
                        onClick={() => navigate(`/admin/clients/${c.id}`)}
                        className="hover:bg-blue-50/40 cursor-pointer transition-colors group"
                      >
                        <td className="px-4 py-3 font-medium">{c.full_name}</td>
                        <td className="px-4 py-3 text-gray-600">{c.phone || '—'}</td>
                        <td className="px-4 py-3 font-mono text-xs text-gray-400">{c.telegram_id}</td>
                        <td className="px-4 py-3 text-right">{c.order_count}</td>
                        <td className="px-4 py-3 text-right">{c.avg_rating ? Number(c.avg_rating).toFixed(1) : '—'}</td>
                        <td className="px-4 py-3 text-gray-400 text-xs">{fmtDate(c.last_order_date)}</td>
                        <td className="px-4 py-3">
                          {c.is_active
                            ? <span className="text-xs bg-green-100 text-green-700 px-2 py-0.5 rounded-full">Faol</span>
                            : <span className="text-xs bg-red-100 text-red-700 px-2 py-0.5 rounded-full">Bloklangan</span>
                          }
                        </td>
                        <td className="px-4 py-3" onClick={e => e.stopPropagation()}>
                          <div className="opacity-0 group-hover:opacity-100 transition-opacity flex gap-1">
                            {c.is_active
                              ? <button onClick={() => setConfirmAction({ id: c.id, type: 'block', name: c.full_name })}
                                className="p-1.5 text-red-500 hover:bg-red-50 rounded"><Ban size={14} /></button>
                              : <button onClick={() => setConfirmAction({ id: c.id, type: 'unblock', name: c.full_name })}
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
          title={confirmAction.type === 'block' ? 'Foydalanuvchini bloklash' : 'Blokdan chiqarish'}
          message={`${confirmAction.name} ni ${confirmAction.type === 'block' ? 'bloklash' : 'blokdan chiqarish'}ni tasdiqlaysizmi?`}
          confirmLabel={confirmAction.type === 'block' ? 'Bloklash' : 'Blokdan chiqarish'}
          onClose={() => setConfirmAction(null)}
          onConfirm={handleAction}
          loading={actionLoading}
        />
      )}
    </AdminLayout>
  )
}
