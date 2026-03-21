import React, { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { getOrderDetail, updateOrderStatus, recordPayment } from '../api/client'
import StatusBadge from '../components/StatusBadge'
import CloseOrderModal from '../components/CloseOrderModal'
import { closeOrder } from '../api/client'
import { ArrowLeft, ChevronLeft, ChevronRight } from 'lucide-react'

const TRANSITIONS = { new: 'preparation', preparation: 'in_process', in_process: 'ready' }
const NEXT_LABELS = { preparation: 'Mark as Preparation', in_process: 'Mark as In Process', ready: 'Mark as Ready' }

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
  const [paymentAmount, setPaymentAmount] = useState('')
  const [paymentLoading, setPaymentLoading] = useState(false)
  const [toast, setToast] = useState('')

  const reload = () => {
    getOrderDetail(orderNumber).then(setOrder).catch(console.error).finally(() => setLoading(false))
  }

  useEffect(() => { reload() }, [orderNumber])

  const showToast = (msg) => { setToast(msg); setTimeout(() => setToast(''), 3000) }

  const handleStatusUpdate = async () => {
    const next = TRANSITIONS[order.status]
    if (!next) return
    setStatusLoading(true)
    try {
      await updateOrderStatus(orderNumber, { status: next })
      await reload()
      showToast(`Status updated to ${next}`)
    } catch (e) {
      showToast(e.response?.data?.detail || 'Failed to update status')
    } finally { setStatusLoading(false) }
  }

  const handleClose = async (partsCost) => {
    setCloseLoading(true)
    try {
      await closeOrder(orderNumber, { parts_cost: partsCost })
      setCloseModal(false)
      await reload()
      showToast('Order closed. Client notified.')
    } catch (e) {
      showToast(e.response?.data?.detail || 'Failed to close order')
    } finally { setCloseLoading(false) }
  }

  const handlePayment = async () => {
    const amt = parseFloat(paymentAmount)
    if (!amt || amt <= 0) { showToast('Enter a valid amount'); return }
    setPaymentLoading(true)
    try {
      await recordPayment(orderNumber, amt)
      setPaymentAmount('')
      await reload()
      showToast('Payment recorded')
    } catch (e) {
      showToast(e.response?.data?.detail || 'Failed to record payment')
    } finally { setPaymentLoading(false) }
  }

  if (loading) return <div className="min-h-screen flex items-center justify-center text-gray-400">Loading…</div>
  if (!order) return <div className="min-h-screen flex items-center justify-center text-gray-400">Order not found</div>

  const photos = order.photos || []
  const logs = order.logs || []
  const nextStatus = TRANSITIONS[order.status]
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
            <span className="ml-auto text-xs text-green-700 bg-green-50 px-2 py-1 rounded-full">Client confirmed</span>
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
            <h2 className="font-semibold text-gray-700 mb-3">Car & Client</h2>
            <InfoRow label="Car" value={`${order.brand || ''} ${order.model || ''}`.trim()} />
            <InfoRow label="Plate" value={order.plate} />
            <InfoRow label="Color" value={order.color} />
            <InfoRow label="Year" value={order.year} />
            {order.visit_count > 1 && (
              <div className="mt-2 text-xs text-yellow-700 bg-yellow-50 px-3 py-1.5 rounded-lg">
                Visit #{order.visit_count} for this plate
              </div>
            )}
            <div className="mt-4 border-t border-gray-50 pt-4">
              <InfoRow label="Client" value={order.client_name || order.client_full_name} />
              <InfoRow label="Phone" value={order.client_phone || order.client_phone_num} />
            </div>
          </div>

          <div className="card">
            <h2 className="font-semibold text-gray-700 mb-3">Financials</h2>
            <InfoRow label="Agreed Price" value={fmt(order.agreed_price)} />
            <InfoRow label="Paid" value={fmt(order.paid_amount)} />
            <InfoRow label="Remaining" value={remaining > 0 ? fmt(remaining) : '✅ Fully paid'} />
            {order.status === 'closed' && (
              <>
                <InfoRow label="Parts Cost" value={fmt(order.parts_cost)} />
                <InfoRow label="Profit" value={fmt(order.profit)} />
                <InfoRow label="Your Share (40%)" value={fmt(order.master_share)} />
                <InfoRow label="Service Share (60%)" value={fmt(order.service_share)} />
              </>
            )}
            <div className="mt-4 border-t border-gray-50 pt-4">
              <InfoRow label="Created" value={fmtDate(order.created_at)} />
              {order.ready_at && <InfoRow label="Ready at" value={fmtDate(order.ready_at)} />}
              {order.closed_at && <InfoRow label="Closed at" value={fmtDate(order.closed_at)} />}
            </div>
          </div>
        </div>

        <div className="card">
          <h2 className="font-semibold text-gray-700 mb-3">Problem & Work</h2>
          <div className="space-y-3 text-sm">
            <div>
              <p className="text-gray-500 text-xs uppercase tracking-wide mb-1">Problem</p>
              <p className="text-gray-800">{order.problem || '—'}</p>
            </div>
            <div>
              <p className="text-gray-500 text-xs uppercase tracking-wide mb-1">Work Performed</p>
              <p className="text-gray-800">{order.work_desc || '—'}</p>
            </div>
          </div>
        </div>

        {(order.expenses || []).length > 0 && (
          <div className="card">
            <h2 className="font-semibold text-gray-700 mb-3">🔩 Parts & Expenses</h2>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-gray-100 text-gray-500 text-xs uppercase">
                    <th className="text-left py-2 pr-3">Item</th>
                    <th className="text-right py-2 pr-3">Amount</th>
                    <th className="text-left py-2">Receipt</th>
                  </tr>
                </thead>
                <tbody>
                  {(order.expenses || []).map(e => (
                    <tr key={e.id} className="border-b border-gray-50 last:border-0">
                      <td className="py-2 pr-3 font-medium">{e.item_name}</td>
                      <td className="py-2 pr-3 text-right text-blue-700 font-semibold whitespace-nowrap">{fmt(e.amount)}</td>
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
                    <td className="py-2 font-semibold text-gray-700">Total</td>
                    <td className="py-2 text-right font-bold text-blue-800">{fmt((order.expenses || []).reduce((s, e) => s + e.amount, 0))}</td>
                    <td />
                  </tr>
                </tfoot>
              </table>
            </div>
          </div>
        )}

        {order.status !== 'closed' && (
          <div className="card space-y-3">
            <h2 className="font-semibold text-gray-700">Actions</h2>
            <div className="flex flex-wrap gap-3">
              {nextStatus && nextStatus !== 'closed' && (
                <button onClick={handleStatusUpdate} disabled={statusLoading} className="btn-primary">
                  {statusLoading ? 'Updating…' : NEXT_LABELS[nextStatus]}
                </button>
              )}
              {order.status === 'ready' && (
                <button onClick={() => setCloseModal(true)} className="btn-danger">
                  Close Order
                </button>
              )}
            </div>

            {order.status !== 'closed' && (
              <div className="border-t border-gray-50 pt-3">
                <p className="text-sm font-medium text-gray-700 mb-2">Record Payment</p>
                <div className="flex gap-2">
                  <input
                    type="number" min="1" placeholder="Amount (UZS)"
                    className="input flex-1"
                    value={paymentAmount}
                    onChange={e => setPaymentAmount(e.target.value)}
                  />
                  <button onClick={handlePayment} disabled={paymentLoading} className="btn-success whitespace-nowrap">
                    {paymentLoading ? '…' : 'Record'}
                  </button>
                </div>
              </div>
            )}
          </div>
        )}

        {logs.length > 0 && (
          <div className="card">
            <h2 className="font-semibold text-gray-700 mb-4">Order Log</h2>
            <div className="relative">
              <div className="absolute left-3 top-0 bottom-0 w-0.5 bg-gray-100" />
              <div className="space-y-4">
                {logs.map((log, i) => (
                  <div key={log.id} className="relative pl-8">
                    <div className="absolute left-1.5 top-1.5 w-3 h-3 rounded-full bg-blue-500 border-2 border-white" />
                    <div className="flex items-start justify-between gap-2">
                      <div>
                        {log.status && <span className="text-sm font-medium"><StatusBadge status={log.status} /></span>}
                        {log.note && <p className="text-sm text-gray-600 mt-0.5">{log.note}</p>}
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
