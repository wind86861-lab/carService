import React, { useEffect, useState } from 'react'
import AdminLayout from '../../components/AdminLayout'
import ConfirmDialog from '../../components/ConfirmDialog'
import { sendBroadcast, getBroadcasts } from '../../api/admin'
import { Send, Users, User, Wrench } from 'lucide-react'

function fmtDate(d) {
  if (!d) return '—'
  return new Date(d).toLocaleDateString('ru-RU', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' })
}

const TARGETS = [
  { value: 'all', label: 'All Users', desc: 'Send to all clients and masters', icon: Users, color: 'text-blue-600', bg: 'bg-blue-50' },
  { value: 'clients', label: 'Clients Only', desc: 'Send only to registered clients', icon: User, color: 'text-green-600', bg: 'bg-green-50' },
  { value: 'masters', label: 'Masters Only', desc: 'Send only to registered masters', icon: Wrench, color: 'text-orange-600', bg: 'bg-orange-50' },
]

export default function AdminBroadcast() {
  const [target, setTarget] = useState('all')
  const [message, setMessage] = useState('')
  const [showConfirm, setShowConfirm] = useState(false)
  const [sending, setSending] = useState(false)
  const [result, setResult] = useState(null)
  const [history, setHistory] = useState([])
  const [historyLoading, setHistoryLoading] = useState(true)

  useEffect(() => {
    getBroadcasts().then(setHistory).catch(console.error).finally(() => setHistoryLoading(false))
  }, [])

  const handleSend = async () => {
    setSending(true)
    try {
      const res = await sendBroadcast(target, message)
      setResult(res)
      setShowConfirm(false)
      setMessage('')
      getBroadcasts().then(setHistory).catch(console.error)
    } catch (e) {
      setResult({ error: e.response?.data?.detail || 'Send failed' })
      setShowConfirm(false)
    } finally { setSending(false) }
  }

  return (
    <AdminLayout>
      <div className="p-6 space-y-6">
        <h1 className="text-xl font-bold text-gray-900">Broadcast</h1>

        <div className="grid lg:grid-cols-2 gap-6">
          <div className="space-y-4">
            <div className="card space-y-3">
              <h2 className="font-semibold text-gray-700">Select Audience</h2>
              {TARGETS.map(t => (
                <button key={t.value} onClick={() => setTarget(t.value)}
                  className={`w-full flex items-center gap-3 p-3 rounded-xl border-2 transition-colors text-left ${
                    target === t.value ? 'border-blue-500 bg-blue-50' : 'border-gray-100 hover:border-gray-200'
                  }`}
                >
                  <div className={`w-10 h-10 ${t.bg} rounded-xl flex items-center justify-center shrink-0`}>
                    <t.icon size={18} className={t.color} />
                  </div>
                  <div>
                    <p className="font-medium text-sm">{t.label}</p>
                    <p className="text-xs text-gray-500">{t.desc}</p>
                  </div>
                </button>
              ))}
            </div>

            <div className="card space-y-3">
              <div className="flex items-center justify-between">
                <h2 className="font-semibold text-gray-700">Message</h2>
                <span className="text-xs text-gray-400">{message.length}/4096</span>
              </div>
              <textarea
                className="input resize-none h-36"
                placeholder="Type your message here… (HTML supported: <b>, <i>, <a>)"
                value={message}
                onChange={e => setMessage(e.target.value)}
                maxLength={4096}
              />
              {result && (
                <div className={`rounded-lg px-4 py-3 text-sm ${result.error ? 'bg-red-50 text-red-700' : 'bg-green-50 text-green-700'}`}>
                  {result.error || `✅ Sent: ${result.sent_count} · Failed: ${result.failed_count}`}
                </div>
              )}
              <button
                onClick={() => setShowConfirm(true)}
                disabled={!message.trim() || sending}
                className="btn-primary w-full justify-center"
              >
                <Send size={16} /> Send Broadcast
              </button>
            </div>
          </div>

          <div className="card space-y-3">
            <h2 className="font-semibold text-gray-700">Message Preview</h2>
            <div className="bg-gray-100 rounded-xl p-4 min-h-24">
              <div className="bg-blue-500 text-white rounded-2xl rounded-tl-none px-4 py-3 inline-block max-w-xs text-sm shadow-sm">
                {message
                  ? <span dangerouslySetInnerHTML={{ __html: message.replace(/\n/g, '<br>') }} />
                  : <span className="opacity-50 italic">Your message will appear here…</span>
                }
              </div>
            </div>
            <p className="text-xs text-gray-400">HTML tags like &lt;b&gt;, &lt;i&gt;, &lt;a&gt; are rendered by Telegram.</p>
          </div>
        </div>

        <div className="card p-0 overflow-hidden">
          <div className="px-4 py-3 border-b border-gray-50 font-semibold text-gray-700 text-sm">Broadcast History</div>
          {historyLoading ? (
            <div className="p-6 text-center text-gray-400">Loading…</div>
          ) : history.length === 0 ? (
            <div className="p-6 text-center text-gray-400">No broadcasts yet.</div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="bg-gray-50 text-xs font-medium text-gray-500 uppercase text-left">
                    <th className="px-4 py-3">Date</th>
                    <th className="px-4 py-3">Sent By</th>
                    <th className="px-4 py-3">Target</th>
                    <th className="px-4 py-3">Message</th>
                    <th className="px-4 py-3 text-right">Sent</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-50">
                  {history.map((b, i) => (
                    <tr key={i}>
                      <td className="px-4 py-3 text-gray-400 text-xs whitespace-nowrap">{fmtDate(b.sent_at)}</td>
                      <td className="px-4 py-3 text-gray-600">{b.sender_name || '—'}</td>
                      <td className="px-4 py-3">
                        <span className="text-xs bg-gray-100 text-gray-700 px-2 py-0.5 rounded-full capitalize">{b.target}</span>
                      </td>
                      <td className="px-4 py-3 text-gray-600 max-w-xs truncate">{b.message}</td>
                      <td className="px-4 py-3 text-right font-medium">{b.sent_count}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>

      {showConfirm && (
        <ConfirmDialog
          title="Send Broadcast"
          message={`Send this message to all ${TARGETS.find(t => t.value === target)?.label}?`}
          confirmLabel="Send"
          onClose={() => setShowConfirm(false)}
          onConfirm={handleSend}
          loading={sending}
          danger={false}
        />
      )}
    </AdminLayout>
  )
}
