import React, { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import AdminLayout from '../../components/AdminLayout'
import StatusBadge from '../../components/StatusBadge'
import ConfirmDialog from '../../components/ConfirmDialog'
import { getAdminOrderDetail, forceCloseOrder, adminRecordPayment } from '../../api/admin'
import { ArrowLeft, AlertTriangle, ChevronLeft, ChevronRight } from 'lucide-react'
import { formatWithSpaces, stripSpaces } from '../../utils/formatNumber'

function fmt(n) { return Number(n || 0).toLocaleString('ru-RU') + ' UZS' }
function fmtDate(d) {
  if (!d) return '—'
  return new Date(d).toLocaleDateString('ru-RU', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' })
}

function InfoRow({ label, value, highlight }) {
  return (
    <div className={`flex justify-between py-2 border-b border-gray-50 last:border-0 text-sm ${highlight ? 'font-semibold' : ''}`}>
      <span className="text-gray-500">{label}</span>
      <span className="text-right max-w-[60%]">{value || '—'}</span>
    </div>
  )
}

export default function AdminOrderDetail() {
  const { orderNumber } = useParams()
  const navigate = useNavigate()
  const [order, setOrder] = useState(null)
  const [loading, setLoading] = useState(true)
  const [showForceClose, setShowForceClose] = useState(false)
  const [partsCost, setPartsCost] = useState('')
  const [closeLoading, setCloseLoading] = useState(false)
  const [toast, setToast] = useState('')
  const [photoIdx, setPhotoIdx] = useState(0)
  const [receiptUrl, setReceiptUrl] = useState(null)
  const [paymentDesc, setPaymentDesc] = useState('')
  const [paymentAmount, setPaymentAmount] = useState('')
  const [paymentLoading, setPaymentLoading] = useState(false)

  const reload = () => {
    getAdminOrderDetail(orderNumber).then(setOrder).catch(console.error).finally(() => setLoading(false))
  }
  useEffect(() => { reload() }, [orderNumber])

  const showToast = (msg) => { setToast(msg); setTimeout(() => setToast(''), 3000) }

  const handleForceClose = async () => {
    setCloseLoading(true)
    try {
      await forceCloseOrder(orderNumber, parseFloat(stripSpaces(partsCost)) || 0)
      setShowForceClose(false)
      await reload()
      showToast('Buyurtma majburiy yopildi. Mijoz xabardor qilindi.')
    } catch (e) {
      showToast(e.response?.data?.detail || 'Failed to force-close order')
    } finally { setCloseLoading(false) }
  }

  if (loading) return <AdminLayout><div className="p-8 text-center text-gray-400">Yuklanmoqda…</div></AdminLayout>
  if (!order) return <AdminLayout><div className="p-8 text-center text-gray-400">Buyurtma topilmadi.</div></AdminLayout>

  const logs = order.logs || []
  const photos = order.photos || []
  const expenses = order.expenses || []

  return (
    <AdminLayout>
      {toast && (
        <div className="fixed top-4 right-4 z-50 bg-gray-900 text-white text-sm px-4 py-2 rounded-lg shadow-lg">{toast}</div>
      )}
      <div className="p-3 sm:p-6 space-y-4 sm:space-y-6 max-w-5xl">
        {photos.length > 0 && (
          <div className="card p-0 overflow-hidden">
            <div className="relative bg-black aspect-video max-h-64">
              <img src={photos[photoIdx]?.url} alt="" className="w-full h-full object-contain" />
              {photos.length > 1 && (
                <>
                  <button onClick={() => setPhotoIdx(i => (i - 1 + photos.length) % photos.length)}
                    className="absolute left-2 top-1/2 -translate-y-1/2 bg-black/40 text-white rounded-full p-1">
                    <ChevronLeft size={18} />
                  </button>
                  <button onClick={() => setPhotoIdx(i => (i + 1) % photos.length)}
                    className="absolute right-2 top-1/2 -translate-y-1/2 bg-black/40 text-white rounded-full p-1">
                    <ChevronRight size={18} />
                  </button>
                </>
              )}
              <div className="absolute bottom-2 left-1/2 -translate-x-1/2 text-white text-xs bg-black/40 px-2 py-0.5 rounded-full">
                {photoIdx + 1} / {photos.length}
              </div>
            </div>
          </div>
        )}

        <div className="flex flex-wrap items-center gap-2 sm:gap-3">
          <button onClick={() => navigate('/admin/orders')} className="btn-secondary p-2"><ArrowLeft size={16} /></button>
          <span className="font-mono font-bold text-blue-700 text-base sm:text-lg">{order.order_number}</span>
          <StatusBadge status={order.status} size="lg" />
          {order.client_confirmed && <span className="text-xs bg-green-100 text-green-700 px-2 py-0.5 rounded-full">Mijoz tasdiqlagan</span>}
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-3 sm:gap-4">
          <div className="card">
            <h2 className="font-semibold text-gray-700 mb-3">Mashina va Mijoz</h2>
            <InfoRow label="Mashina" value={`${order.brand || ''} ${order.model || ''}`.trim()} />
            <InfoRow label="Davlat raqami" value={order.plate} />
            <InfoRow label="Rang / Yil" value={`${order.color || ''} ${order.year || ''}`.trim()} />
            <InfoRow label="Mijoz" value={order.client_name || order.client_full_name} />
            <InfoRow label="Telefon" value={order.client_phone} />
            <InfoRow label="Usta" value={order.master_name} />
          </div>

          <div className="card">
            <h2 className="font-semibold text-gray-700 mb-3">Moliyaviy ma'lumotlar</h2>
            <InfoRow label="Kelishilgan narx" value={fmt(order.agreed_price)} />
            <InfoRow label="To'langan" value={fmt(order.paid_amount)} />
            <InfoRow label="Ehtiyot qismlar" value={fmt(order.parts_cost)} />
            <InfoRow label="Foyda" value={fmt(order.profit)} highlight />
            <InfoRow label="Usta ulushi (40%)" value={fmt(order.master_share)} />
            <InfoRow label="Servis ulushi (60%)" value={fmt(order.service_share)} />
            <InfoRow label="Yaratilgan" value={fmtDate(order.created_at)} />
            {order.closed_at && <InfoRow label="Yopilgan" value={fmtDate(order.closed_at)} />}
          </div>
        </div>

        <div className="card">
          <h2 className="font-semibold text-gray-700 mb-3">Muammo va Ish</h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-sm">
            <div>
              <p className="text-xs text-gray-400 uppercase tracking-wide mb-1">Muammo</p>
              <p>{order.problem || '—'}</p>
            </div>
            <div>
              <p className="text-xs text-gray-400 uppercase tracking-wide mb-1">Bajarilgan ish</p>
              <p>{order.work_desc || '—'}</p>
            </div>
          </div>
        </div>

        {expenses.length > 0 && (
          <div className="card">
            <h2 className="font-semibold text-gray-700 mb-3">🔩 Ehtiyot qismlar va Xarajatlar</h2>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-gray-100 text-gray-500 text-xs uppercase">
                    <th className="text-left py-2 pr-3">Nomi</th>
                    <th className="text-right py-2 pr-3">Summa</th>
                    <th className="text-left py-2 pr-3">Qo'shgan</th>
                    <th className="text-left py-2">Chek</th>
                  </tr>
                </thead>
                <tbody>
                  {expenses.map(e => (
                    <tr key={e.id} className="border-b border-gray-50 last:border-0">
                      <td className="py-2 pr-3 font-medium">{e.item_name}</td>
                      <td className="py-2 pr-3 text-right font-semibold text-blue-700 whitespace-nowrap">{fmt(e.amount)}</td>
                      <td className="py-2 pr-3 text-gray-500 text-xs">{e.added_by_name || '—'}</td>
                      <td className="py-2">
                        {e.receipt_url
                          ? <button onClick={() => setReceiptUrl(e.receipt_url)} className="cursor-pointer">
                            <img src={e.receipt_url} alt="chek" className="h-10 w-14 object-cover rounded border border-gray-200 hover:opacity-80" />
                          </button>
                          : <span className="text-gray-300 text-xs">—</span>
                        }
                      </td>
                    </tr>
                  ))}
                </tbody>
                <tfoot>
                  <tr className="border-t-2 border-gray-200">
                    <td className="py-2 font-semibold">Jami</td>
                    <td className="py-2 text-right font-bold text-blue-800">{fmt(expenses.reduce((s, e) => s + e.amount, 0))}</td>
                    <td /><td />
                  </tr>
                </tfoot>
              </table>
            </div>
          </div>
        )}

        {order.status !== 'closed' && (
          <div className="card">
            <h2 className="font-semibold text-gray-700 mb-3">To'lov qayd etish</h2>
            <div className="flex flex-col sm:flex-row items-stretch sm:items-end gap-3">
              <div className="flex-1">
                <label className="block text-xs text-gray-500 mb-1">To'lov nomi *</label>
                <input
                  type="text"
                  placeholder="masalan, Oldindan to'lov"
                  className="input w-full"
                  value={paymentDesc}
                  onChange={e => setPaymentDesc(e.target.value)}
                />
              </div>
              <div className="sm:w-48">
                <label className="block text-xs text-gray-500 mb-1">Summa (UZS) *</label>
                <input
                  type="text"
                  inputMode="numeric"
                  placeholder="0"
                  className="input w-full"
                  value={paymentAmount}
                  onChange={e => setPaymentAmount(formatWithSpaces(e.target.value))}
                />
              </div>
              <button
                onClick={async () => {
                  if (!paymentDesc.trim()) { showToast('To\'lov nomini kiriting'); return }
                  const amt = parseFloat(stripSpaces(paymentAmount))
                  if (!amt || amt <= 0) { showToast('To\'g\'ri summa kiriting'); return }
                  setPaymentLoading(true)
                  try {
                    await adminRecordPayment(orderNumber, paymentDesc.trim(), amt)
                    setPaymentDesc('')
                    setPaymentAmount('')
                    await reload()
                    showToast('To\'lov qayd etildi')
                  } catch (e) {
                    showToast(e.response?.data?.detail || 'To\'lovni qayd etib bo\'lmadi')
                  } finally { setPaymentLoading(false) }
                }}
                disabled={paymentLoading}
                className="btn-success whitespace-nowrap"
              >
                {paymentLoading ? '…' : 'Qayd etish'}
              </button>
            </div>
          </div>
        )}

        {order.status !== 'closed' && (
          <div className="card border-2 border-red-100">
            <div className="flex items-center gap-2 mb-3">
              <AlertTriangle size={16} className="text-red-600" />
              <h2 className="font-semibold text-red-700">Admin amallari</h2>
            </div>
            <p className="text-sm text-gray-500 mb-4">Bu buyurtmani joriy holatidan qat'i nazar majburiy yopish.</p>
            <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-3">
              <input
                type="text" inputMode="numeric" placeholder="Qismlar narxi (UZS)"
                className="input w-full sm:w-52"
                value={partsCost}
                onChange={e => setPartsCost(formatWithSpaces(e.target.value))}
              />
              <button onClick={() => setShowForceClose(true)} className="btn-danger">Majburiy yopish</button>
            </div>
          </div>
        )}

        {logs.length > 0 && (
          <div className="card">
            <h2 className="font-semibold text-gray-700 mb-4">Buyurtma tarixi</h2>
            <div className="relative">
              <div className="absolute left-3 top-0 bottom-0 w-0.5 bg-gray-100" />
              <div className="space-y-4">
                {logs.map(log => (
                  <div key={log.id} className="relative pl-8">
                    <div className="absolute left-1.5 top-1.5 w-3 h-3 rounded-full bg-blue-500 border-2 border-white" />
                    <div className="flex items-start justify-between gap-2">
                      <div>
                        {log.status && <StatusBadge status={log.status} />}
                        {log.note && <p className="text-sm text-gray-600 mt-0.5">{log.note}</p>}
                        {log.changed_by_name && <p className="text-xs text-gray-400">by {log.changed_by_name}</p>}
                      </div>
                      <span className="text-xs text-gray-400 whitespace-nowrap">{fmtDate(log.changed_at)}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>

      {showForceClose && (
        <ConfirmDialog
          title="Buyurtmani majburiy yopish"
          message={`${orderNumber} buyurtma admin sifatida yopilmoqda. Qismlar narxi: ${partsCost || 0} UZS. Bu amalni qaytarib bo'lmaydi.`}
          confirmLabel="Yopish"
          onClose={() => setShowForceClose(false)}
          onConfirm={handleForceClose}
          loading={closeLoading}
        />
      )}

      {receiptUrl && (
        <div className="fixed inset-0 z-50 flex flex-col items-center justify-center bg-black/60 backdrop-blur-sm p-4"
          onClick={() => setReceiptUrl(null)}>
          <div className="relative" onClick={e => e.stopPropagation()}>
            <button onClick={() => setReceiptUrl(null)}
              className="absolute -top-4 -right-4 w-10 h-10 bg-white rounded-full shadow-lg flex items-center justify-center text-gray-700 hover:text-red-600 z-50 text-lg font-bold">
              ✕
            </button>
            <img src={receiptUrl} alt="Chek"
              className="max-w-[90vw] max-h-[85vh] rounded-xl shadow-2xl object-contain bg-white"
              onError={(e) => { e.target.onerror = null; e.target.src = ''; e.target.alt = 'Rasm yuklanmadi'; e.target.className = 'p-12 text-white text-sm' }}
            />
          </div>
        </div>
      )}
    </AdminLayout>
  )
}
