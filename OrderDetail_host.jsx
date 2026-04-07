import React, { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { getOrderDetail, updateOrderStatus, closeOrder, recordPayment, addOrderExpense } from '../api/client'
import StatusBadge from '../components/StatusBadge'
import CloseOrderModal from '../components/CloseOrderModal'
import { closeOrder } from '../api/client'
import { ArrowLeft, ChevronLeft, ChevronRight } from 'lucide-react'
import { formatWithSpaces, stripSpaces } from '../utils/formatNumber'

const ALL_STATUSES = [
  { value: 'new', label: 'Yangi' },
  { value: 'preparation', label: 'Tayyorlash' },
  { value: 'in_process', label: 'Jarayonda' },
  { value: 'ready', label: 'Tayyor' },
]

const STATUS_LABELS = { new: 'Yangi', preparation: 'Tayyorlash', in_process: 'Jarayonda', ready: 'Tayyor', closed: 'Yopilgan' }

function translateNote(note) {
  if (!note) return note
  return note
    .replace('Order created', 'Buyurtma yaratildi')
    .replace('Master changed status to preparation', 'Usta holatni Tayyorlashga o\'zgartirdi')
    .replace('Master changed status to in_process', 'Usta holatni Jarayonga o\'zgartirdi')
    .replace('Master changed status to ready', 'Usta holatni Tayyorga o\'zgartirdi')
    .replace('Master changed status to new', 'Usta holatni Yangiga o\'zgartirdi')
    .replace('Master changed status to closed', 'Usta buyurtmani yopdi')
    .replace(/Master changed status to (\w+)/g, 'Usta holatni $1 ga o\'zgartirdi')
    .replace(/Status changed to (\w+)/g, 'Holat $1 ga o\'zgartildi')
}

function fmt(n) { return Number(n || 0).toLocaleString('ru-RU') + ' UZS' }
function fmtDate(d) {
  if (!d) return '—'
  return new Date(d).toLocaleDateString('ru-RU', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' })
}

function InfoRow({ label, value }) {
  return (
    <div className="flex justify-between py-2 border-b border-gray-50 last:border-0 text-sm">
      <span className="text-gray-500">{label}</span>
      <span className="font-medium text-right max-w-[60%]">{value || '—'}</span>
    </div>
  )
}

export default function OrderDetail() {
  const { orderNumber } = useParams()
  const navigate = useNavigate()
  const [order, setOrder] = useState(null)
  const [loading, setLoading] = useState(true)
  const [statusLoading, setStatusLoading] = useState(false)
  const [closeModal, setCloseModal] = useState(false)
  const [closeLoading, setCloseLoading] = useState(false)
  const [photoIdx, setPhotoIdx] = useState(0)
  const [paymentDesc, setPaymentDesc] = useState('')
  const [paymentAmount, setPaymentAmount] = useState('')
  const [paymentReceipt, setPaymentReceipt] = useState(null)
  const [paymentLoading, setPaymentLoading] = useState(false)
  const [toast, setToast] = useState('')
  const [selectedStatus, setSelectedStatus] = useState('')
  const [expenseName, setExpenseName] = useState('')
  const [expenseAmount, setExpenseAmount] = useState('')
  const [expenseFile, setExpenseFile] = useState(null)
  const [expenseLoading, setExpenseLoading] = useState(false)

  const reload = () => {
    getOrderDetail(orderNumber).then(setOrder).catch(console.error).finally(() => setLoading(false))
  }

  useEffect(() => { reload() }, [orderNumber])

  const showToast = (msg) => { setToast(msg); setTimeout(() => setToast(''), 3000) }

  const handleStatusUpdate = async (newStatus) => {
    if (!newStatus || newStatus === order.status) return
    setStatusLoading(true)
    try {
      await updateOrderStatus(orderNumber, { status: newStatus })
      setSelectedStatus('')
      await reload()
      showToast('Holat yangilandi')
    } catch (e) {
      showToast(e.response?.data?.detail || 'Holatni yangilab bo\'lmadi')
    } finally { setStatusLoading(false) }
  }

  const handleClose = async (partsCost) => {
    setCloseLoading(true)
    try {
      await closeOrder(orderNumber, { parts_cost: partsCost })
      setCloseModal(false)
      await reload()
      showToast('Buyurtma yopildi. Mijozga xabar yuborildi.')
    } catch (e) {
      showToast(e.response?.data?.detail || 'Buyurtmani yopib bo\'lmadi')
    } finally { setCloseLoading(false) }
  }

  const handlePayment = async () => {
    if (!paymentDesc.trim()) { showToast('To\'lov nomini kiriting'); return }
    const amt = parseFloat(stripSpaces(paymentAmount))
    if (!amt || amt <= 0) { showToast('To\'g\'ri summa kiriting'); return }
    if (!paymentReceipt) { showToast('Chek rasmini yuklang'); return }
    setPaymentLoading(true)
    try {
      await recordPayment(orderNumber, paymentDesc.trim(), amt, paymentReceipt)
      setPaymentDesc('')
      setPaymentAmount('')
      setPaymentReceipt(null)
      await reload()
      showToast('To\'lov qayd etildi')
    } catch (e) {
      showToast(e.response?.data?.detail || 'To\'lovni qayd etib bo\'lmadi')
    } finally { setPaymentLoading(false) }
  }

  if (loading) return <div className="min-h-screen flex items-center justify-center text-gray-400">Yuklanmoqda…</div>
  if (!order) return <div className="min-h-screen flex items-center justify-center text-gray-400">Buyurtma topilmadi</div>

  const photos = order.photos || []
  const logs = order.logs || []
  const availableStatuses = ALL_STATUSES.filter(s => s.value !== order.status)
  const remaining = Number(order.agreed_price) - Number(order.paid_amount)

  return (
    <div className="min-h-screen bg-gray-50">
      {toast && (
        <div className="fixed top-4 right-4 z-50 bg-gray-900 text-white text-sm px-4 py-2 rounded-lg shadow-lg">{toast}</div>
      )}

      <header className="bg-white border-b border-gray-100 sticky top-0 z-10">
        <div className="max-w-5xl mx-auto px-3 sm:px-4 py-2 sm:py-3 flex items-center gap-3">
          <button onClick={() => navigate('/dashboard')} className="btn-secondary p-2"><ArrowLeft size={16} /></button>
          <span className="font-mono font-bold text-blue-700 text-lg">{order.order_number}</span>
          <StatusBadge status={order.status} size="lg" />
          {order.client_confirmed && (
            <span className="ml-auto text-xs text-green-700 bg-green-50 px-2 py-1 rounded-full">Mijoz tasdiqlagan</span>
          )}
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-3 sm:px-4 py-4 sm:py-6 space-y-4 sm:space-y-6">
        {photos.length > 0 && (
          <div className="card p-0 overflow-hidden">
            <div className="relative bg-black aspect-video max-h-72">
              <img src={photos[photoIdx]?.url} alt="" className="w-full h-full object-contain" />
              {photos.length > 1 && (
                <>
                  <button onClick={() => setPhotoIdx(i => (i - 1 + photos.length) % photos.length)}
                    className="absolute left-2 top-1/2 -translate-y-1/2 bg-black/40 text-white rounded-full p-1 hover:bg-black/60">
                    <ChevronLeft size={20} />
                  </button>
                  <button onClick={() => setPhotoIdx(i => (i + 1) % photos.length)}
                    className="absolute right-2 top-1/2 -translate-y-1/2 bg-black/40 text-white rounded-full p-1 hover:bg-black/60">
                    <ChevronRight size={20} />
                  </button>
                  <div className="absolute bottom-2 left-1/2 -translate-x-1/2 flex gap-1">
                    {photos.map((_, i) => (
                      <button key={i} onClick={() => setPhotoIdx(i)}
                        className={`w-2 h-2 rounded-full transition-colors ${i === photoIdx ? 'bg-white' : 'bg-white/40'}`} />
                    ))}
                  </div>
                </>
              )}
            </div>
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 sm:gap-6">
          <div className="card">
            <h2 className="font-semibold text-gray-700 mb-3">Mashina va Mijoz</h2>
            <InfoRow label="Mashina" value={`${order.brand || ''} ${order.model || ''}`.trim()} />
            <InfoRow label="Davlat raqami" value={order.plate} />
            <InfoRow label="Rang" value={order.color} />
            <InfoRow label="Yil" value={order.year} />
            {order.visit_count > 1 && (
              <div className="mt-2 text-xs text-yellow-700 bg-yellow-50 px-3 py-1.5 rounded-lg">
                Bu mashina {order.visit_count}-marta kelgan
              </div>
            )}
            <div className="mt-4 border-t border-gray-50 pt-4">
              <InfoRow label="Mijoz" value={order.client_name || order.client_full_name} />
              <InfoRow label="Telefon" value={order.client_phone || order.client_phone_num} />
            </div>
          </div>

          <div className="card">
            <h2 className="font-semibold text-gray-700 mb-3">Moliyaviy</h2>
            <InfoRow label="Kelishilgan narx" value={fmt(order.agreed_price)} />
            <InfoRow label="To'langan" value={fmt(order.paid_amount)} />
            <InfoRow label="Qoldiq" value={remaining > 0 ? fmt(remaining) : '✅ To\'liq to\'langan'} />
            {order.status === 'closed' && (
              <>
                <InfoRow label="Ehtiyot qismlar" value={fmt(order.parts_cost)} />
                <InfoRow label="Foyda" value={fmt(order.profit)} />
                <InfoRow label="Usta ulushi (40%)" value={fmt(order.master_share)} />
                <InfoRow label="Servis ulushi (60%)" value={fmt(order.service_share)} />
              </>
            )}
            <div className="mt-4 border-t border-gray-50 pt-4">
              <InfoRow label="Yaratilgan" value={fmtDate(order.created_at)} />
              {order.ready_at && <InfoRow label="Tayyor bo'lgan" value={fmtDate(order.ready_at)} />}
              {order.closed_at && <InfoRow label="Yopilgan" value={fmtDate(order.closed_at)} />}
            </div>
          </div>
        </div>

        <div className="card">
          <h2 className="font-semibold text-gray-700 mb-3">Muammo va Ish</h2>
          <div className="space-y-3 text-sm">
            <div>
              <p className="text-gray-500 text-xs uppercase tracking-wide mb-1">Muammo</p>
              <p className="text-gray-800">{order.problem || '—'}</p>
            </div>
            <div>
              <p className="text-gray-500 text-xs uppercase tracking-wide mb-1">Bajarilgan ish</p>
              <p className="text-gray-800">{order.work_desc || '—'}</p>
            </div>
          </div>
        </div>

        {(order.expenses || []).length > 0 && (
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
                  {(order.expenses || []).map(e => (
                    <tr key={e.id} className="border-b border-gray-50 last:border-0">
                      <td className="py-2 pr-3 font-medium">{e.item_name}</td>
                      <td className="py-2 pr-3 text-right text-blue-700 font-semibold whitespace-nowrap">{fmt(e.amount)}</td>
                      <td className="py-2 pr-3 text-gray-500 text-xs text-center">{e.added_by_name} ({e.added_by_role === 'admin' ? 'Admin' : 'Usta'})</td>
                      <td className="py-2">
                        {e.receipt_url
                          ? <a href={e.receipt_url} target="_blank" rel="noreferrer"
                            className="inline-block">
                            <img src={e.receipt_url} alt="receipt" className="h-10 w-14 object-cover rounded border border-gray-200 hover:opacity-80" />
                          </a>
                          : <span className="text-gray-300 text-xs">—</span>
                        }
                      </td>
                    </tr>
                  ))}
                </tbody>
                <tfoot>
                  <tr className="border-t-2 border-gray-200">
                    <td className="py-2 font-semibold text-gray-700">Jami</td>
                    <td className="py-2 text-right font-bold text-blue-800">{fmt((order.expenses || []).reduce((s, e) => s + e.amount, 0))}</td>
                    <td /><td />
                  </tr>
                </tfoot>
              </table>
            </div>

            {order.status !== 'closed' && (
              <div className="mt-4 pt-4 border-t border-gray-100">
                <p className="text-sm font-medium text-gray-700 mb-3 text-center sm:text-left">Yangi xarajat qo'shish</p>
                <div className="space-y-3">
                  <div className="flex flex-col sm:flex-row gap-2">
                    <input
                      type="text"
                      className="input flex-1"
                      placeholder="Ehtiyot qism yoki xarajat nomi *"
                      value={expenseName}
                      onChange={e => setExpenseName(e.target.value)}
                    />
                    <input
                      type="text"
                      inputMode="numeric"
                      className="input sm:w-48"
                      placeholder="Summa (UZS) *"
                      value={expenseAmount}
                      onChange={e => setExpenseAmount(formatWithSpaces(e.target.value))}
                    />
                  </div>
                  <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-2">
                    <label className="flex items-center gap-2 cursor-pointer border border-gray-300 rounded-lg px-3 py-2 text-sm text-gray-600 hover:border-blue-400 transition-colors flex-1">
                      <svg className="w-4 h-4 text-gray-400 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" /></svg>
                      <span className="truncate">{expenseFile ? expenseFile.name : 'Chek rasmi (ixtiyoriy)'}</span>
                      <input
                        type="file" accept="image/*" className="hidden"
                        onChange={e => setExpenseFile(e.target.files[0] || null)}
                      />
                    </label>
                    <button
                      className="btn-primary whitespace-nowrap"
                      disabled={expenseLoading}
                      onClick={async () => {
                        if (!expenseName.trim()) { showToast('Nomini kiriting'); return }
                        const amt = parseFloat(stripSpaces(expenseAmount))
                        if (!amt || amt <= 0) { showToast('To\'g\'ri summa kiriting'); return }
                        setExpenseLoading(true)
                        try {
                          await addOrderExpense(orderNumber, expenseName.trim(), amt, expenseFile)
                          setExpenseName('')
                          setExpenseAmount('')
                          setExpenseFile(null)
                          await reload()
                          showToast('Xarajat qo\'shildi')
                        } catch (e) {
                          showToast(e.response?.data?.detail || 'Xarajatni qo\'shib bo\'lmadi')
                        } finally { setExpenseLoading(false) }
                      }}
                    >
                      {expenseLoading ? '…' : 'Qo\'shish'}
                    </button>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {order.status !== 'closed' && (
          <div className="card space-y-3">
            <h2 className="font-semibold text-gray-700">Amallar</h2>
            <div className="flex flex-wrap items-center gap-3">
              <select
                value={selectedStatus}
                onChange={e => setSelectedStatus(e.target.value)}
                className="input w-auto min-w-[180px]"
              >
                <option value="">Holatni tanlang...</option>
                {availableStatuses.map(s => (
                  <option key={s.value} value={s.value}>{s.label}</option>
                ))}
              </select>
              <button
                onClick={() => handleStatusUpdate(selectedStatus)}
                disabled={statusLoading || !selectedStatus}
                className="btn-primary"
              >
                {statusLoading ? 'Yangilanmoqda…' : 'O\'zgartirish'}
              </button>
              {order.status === 'ready' && (
                <button onClick={() => setCloseModal(true)} className="btn-danger">
                  Buyurtmani yopish
                </button>
              )}
            </div>

            {order.status !== 'closed' && (
              <div className="border-t border-gray-50 pt-3">
                <p className="text-sm font-medium text-gray-700 mb-2">To'lov qayd etish</p>
                <div className="space-y-2">
                  <div className="flex flex-col sm:flex-row gap-2">
                    <input
                      type="text" placeholder="To'lov nomi *"
                      className="input flex-1"
                      value={paymentDesc}
                      onChange={e => setPaymentDesc(e.target.value)}
                    />
                    <input
                      type="text" inputMode="numeric" placeholder="Summa (UZS) *"
                      className="input sm:w-40"
                      value={paymentAmount}
                      onChange={e => setPaymentAmount(formatWithSpaces(e.target.value))}
                    />
                  </div>
                  <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-2">
                    <label className="flex items-center gap-2 cursor-pointer border border-gray-300 rounded-lg px-3 py-2 text-sm text-gray-600 hover:border-blue-400 transition-colors flex-1">
                      <svg className="w-4 h-4 text-gray-400 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" /></svg>
                      <span>{paymentReceipt ? paymentReceipt.name : 'Chek rasmi *'}</span>
                      <input
                        type="file" accept="image/*" className="hidden"
                        onChange={e => setPaymentReceipt(e.target.files[0] || null)}
                      />
                    </label>
                    <button onClick={handlePayment} disabled={paymentLoading} className="btn-success whitespace-nowrap">
                      {paymentLoading ? '…' : 'Qayd etish'}
                    </button>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {logs.length > 0 && (
          <div className="card">
            <h2 className="font-semibold text-gray-700 mb-4">Buyurtma tarixi</h2>
            <div className="relative">
              <div className="absolute left-3 top-0 bottom-0 w-0.5 bg-gray-100" />
              <div className="space-y-4">
                {logs.map((log, i) => (
                  <div key={log.id} className="relative pl-8">
                    <div className="absolute left-1.5 top-1.5 w-3 h-3 rounded-full bg-blue-500 border-2 border-white" />
                    <div className="flex items-start justify-between gap-2">
                      <div>
                        {log.status && <span className="text-sm font-medium"><StatusBadge status={log.status} /></span>}
                        {log.note && <p className="text-sm text-gray-600 mt-0.5">{translateNote(log.note)}</p>}
                        {log.receipt_url && (
                          <a href={log.receipt_url} target="_blank" rel="noreferrer" className="inline-block mt-1">
                            <img src={log.receipt_url} alt="chek" className="h-12 w-16 object-cover rounded border border-gray-200 hover:opacity-80" />
                          </a>
                        )}
                        {log.changed_by_name && <p className="text-xs text-gray-400 mt-0.5">by {log.changed_by_name}</p>}
                      </div>
                      <span className="text-xs text-gray-400 whitespace-nowrap">{fmtDate(log.changed_at)}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </main>

      {closeModal && (
        <CloseOrderModal
          order={order}
          onClose={() => setCloseModal(false)}
          onConfirm={handleClose}
          loading={closeLoading}
        />
      )}
    </div>
  )
}
