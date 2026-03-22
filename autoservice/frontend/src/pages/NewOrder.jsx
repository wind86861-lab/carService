import React, { useState, useCallback, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { createOrder, uploadPhotos, getCarHistory } from '../api/client'
import PhotoUpload from '../components/PhotoUpload'
import { ArrowLeft, Copy, Check, ExternalLink } from 'lucide-react'
import { formatWithSpaces, stripSpaces } from '../utils/formatNumber'

const CURRENT_YEAR = new Date().getFullYear()
const BOT_USERNAME = import.meta.env.VITE_BOT_USERNAME || 'your_bot'

function Field({ label, error, children }) {
  return (
    <div>
      <label className="label">{label}</label>
      {children}
      {error && <p className="mt-1 text-xs text-red-600">{error}</p>}
    </div>
  )
}

export default function NewOrder() {
  const navigate = useNavigate()
  const debounceRef = useRef(null)

  const [form, setForm] = useState({
    brand: '', model: '', plate: '', color: '', year: '',
    client_name: '', client_phone: '+998', problem: '', work_desc: '',
    agreed_price: '', paid_amount: '',
  })
  const [photos, setPhotos] = useState([])
  const [errors, setErrors] = useState({})
  const [submitting, setSubmitting] = useState(false)
  const [success, setSuccess] = useState(null)
  const [copied, setCopied] = useState(false)
  const [history, setHistory] = useState([])
  const [historyLoading, setHistoryLoading] = useState(false)

  const set = (field) => (e) => {
    let val = field === 'plate' ? e.target.value.toUpperCase() : e.target.value
    if (field === 'agreed_price' || field === 'paid_amount') {
      val = formatWithSpaces(val)
    }
    setForm(f => ({ ...f, [field]: val }))
    setErrors(err => ({ ...err, [field]: '' }))

    if (field === 'plate' && val.length >= 4) {
      clearTimeout(debounceRef.current)
      debounceRef.current = setTimeout(() => {
        setHistoryLoading(true)
        getCarHistory(val).then(setHistory).catch(() => setHistory([])).finally(() => setHistoryLoading(false))
      }, 500)
    } else if (field === 'plate') {
      setHistory([])
    }
  }

  const validate = () => {
    const e = {}
    if (form.brand.trim().length < 2) e.brand = 'Minimum 2 characters'
    if (form.model.trim().length < 2) e.model = 'Minimum 2 characters'
    if (form.plate.trim().length < 4) e.plate = 'Minimum 4 characters'
    if (!form.color.trim()) e.color = 'Required'
    const yr = parseInt(form.year)
    if (!form.year || isNaN(yr) || yr < 1950 || yr > CURRENT_YEAR + 1) e.year = `Year must be 1950–${CURRENT_YEAR + 1}`
    if (form.client_name.trim().length < 2) e.client_name = 'Minimum 2 characters'
    if (!/^\+998\d{9}$/.test(form.client_phone.trim())) e.client_phone = 'Format: +998XXXXXXXXX'
    if (form.problem.trim().length < 10) e.problem = 'Minimum 10 characters'
    if (form.work_desc.trim().length < 10) e.work_desc = 'Minimum 10 characters'
    const price = parseFloat(stripSpaces(form.agreed_price))
    if (!form.agreed_price || isNaN(price) || price <= 0) e.agreed_price = 'Must be a positive number'
    const paid = parseFloat(stripSpaces(form.paid_amount))
    if (form.paid_amount === '' || isNaN(paid) || paid < 0) e.paid_amount = 'Cannot be negative'
    if (!isNaN(price) && !isNaN(paid) && paid > price) e.paid_amount = 'Cannot exceed agreed price'
    if (photos.length === 0) e.photos = 'At least one photo required'
    return e
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    const errs = validate()
    if (Object.keys(errs).length) { setErrors(errs); return }

    setSubmitting(true)
    try {
      const body = {
        ...form,
        year: parseInt(form.year),
        agreed_price: parseFloat(stripSpaces(form.agreed_price)),
        paid_amount: parseFloat(stripSpaces(form.paid_amount)),
      }
      const result = await createOrder(body)
      if (photos.length > 0) {
        await uploadPhotos(result.order_number, photos)
      }
      setSuccess(result.order_number)
    } catch (err) {
      const msg = err.response?.data?.detail
      if (typeof msg === 'string') setErrors({ _global: msg })
      else if (Array.isArray(msg)) setErrors({ _global: msg.map(m => m.msg).join(', ') })
      else setErrors({ _global: 'Failed to create order. Please try again.' })
    } finally {
      setSubmitting(false)
    }
  }

  const inviteLink = success ? `https://t.me/${BOT_USERNAME}?start=${success}` : ''

  const copyLink = () => {
    navigator.clipboard.writeText(inviteLink)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  if (success) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
        <div className="card max-w-md w-full text-center">
          <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <Check className="text-green-600 w-8 h-8" />
          </div>
          <h2 className="text-xl font-bold mb-1">Order Created!</h2>
          <p className="text-3xl font-mono font-bold text-blue-700 my-4">{success}</p>
          <p className="text-sm text-gray-500 mb-4">Share this link with the client so they can connect to the order in the bot:</p>
          <div className="bg-gray-50 rounded-lg p-3 text-sm font-mono text-gray-700 break-all mb-3">{inviteLink}</div>
          <div className="flex gap-2">
            <button onClick={copyLink} className="btn-primary flex-1">
              {copied ? <><Check size={16} /> Copied!</> : <><Copy size={16} /> Copy Link</>}
            </button>
            <a href={`https://t.me/share/url?url=${encodeURIComponent(inviteLink)}`} target="_blank" rel="noopener noreferrer" className="btn-secondary flex-1">
              <ExternalLink size={16} /> Share
            </a>
          </div>
          <div className="mt-4 flex gap-2">
            <button onClick={() => navigate(`/orders/${success}`)} className="btn-secondary flex-1">View Order</button>
            <button onClick={() => navigate('/dashboard')} className="btn-secondary flex-1">Dashboard</button>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b border-gray-100 sticky top-0 z-10">
        <div className="max-w-2xl mx-auto px-3 sm:px-4 py-2 sm:py-3 flex items-center gap-3">
          <button onClick={() => navigate('/dashboard')} className="btn-secondary p-2"><ArrowLeft size={16} /></button>
          <h1 className="text-lg font-bold">New Order</h1>
        </div>
      </header>

      <form onSubmit={handleSubmit} className="max-w-2xl mx-auto px-3 sm:px-4 py-4 sm:py-6 space-y-4 sm:space-y-6">
        {errors._global && (
          <div className="bg-red-50 border border-red-200 rounded-lg px-4 py-3 text-sm text-red-700">{errors._global}</div>
        )}

        <div className="card space-y-4">
          <h2 className="font-semibold text-gray-700">Photos</h2>
          <PhotoUpload files={photos} onChange={setPhotos} />
          {errors.photos && <p className="text-xs text-red-600">{errors.photos}</p>}
        </div>

        <div className="card space-y-4">
          <h2 className="font-semibold text-gray-700">Car Information</h2>
          <div className="grid grid-cols-2 gap-4">
            <Field label="Brand *" error={errors.brand}>
              <input className="input" value={form.brand} onChange={set('brand')} placeholder="e.g. Chevrolet" />
            </Field>
            <Field label="Model *" error={errors.model}>
              <input className="input" value={form.model} onChange={set('model')} placeholder="e.g. Gentra" />
            </Field>
          </div>
          <Field label="License Plate *" error={errors.plate}>
            <input className="input font-mono" value={form.plate} onChange={set('plate')} placeholder="01 A 123 BB" />
            {history.length > 0 && (
              <div className="mt-2 bg-yellow-50 border border-yellow-200 rounded-lg p-3 text-sm">
                <p className="font-medium text-yellow-800">⚠️ This car has been here {history.length} time(s) before.</p>
                <div className="mt-2 space-y-1 max-h-32 overflow-y-auto">
                  {history.map(h => (
                    <div key={h.order_number} className="text-xs text-yellow-700 flex justify-between">
                      <span className="font-mono">{h.order_number}</span>
                      <span className="truncate ml-2">{h.problem?.slice(0, 40) || '—'}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </Field>
          <div className="grid grid-cols-2 gap-4">
            <Field label="Color *" error={errors.color}>
              <input className="input" value={form.color} onChange={set('color')} placeholder="e.g. White" />
            </Field>
            <Field label="Year *" error={errors.year}>
              <input className="input" type="number" min="1950" max={CURRENT_YEAR + 1} value={form.year} onChange={set('year')} placeholder={String(CURRENT_YEAR)} />
            </Field>
          </div>
        </div>

        <div className="card space-y-4">
          <h2 className="font-semibold text-gray-700">Client Information</h2>
          <Field label="Client Name *" error={errors.client_name}>
            <input className="input" value={form.client_name} onChange={set('client_name')} placeholder="Full name" />
          </Field>
          <Field label="Client Phone *" error={errors.client_phone}>
            <input className="input" type="tel" value={form.client_phone} onChange={set('client_phone')} placeholder="+998901234567" />
          </Field>
        </div>

        <div className="card space-y-4">
          <h2 className="font-semibold text-gray-700">Order Details</h2>
          <Field label="Problem Description *" error={errors.problem}>
            <textarea className="input resize-none" rows={3} value={form.problem} onChange={set('problem')} placeholder="Describe the problem (min 10 chars)" />
          </Field>
          <Field label="Work Description *" error={errors.work_desc}>
            <textarea className="input resize-none" rows={3} value={form.work_desc} onChange={set('work_desc')} placeholder="Describe the work to be done (min 10 chars)" />
          </Field>
        </div>

        <div className="card space-y-4">
          <h2 className="font-semibold text-gray-700">Financials</h2>
          <div className="grid grid-cols-2 gap-4">
            <Field label="Agreed Price (UZS) *" error={errors.agreed_price}>
              <input className="input" type="text" inputMode="numeric" value={form.agreed_price} onChange={set('agreed_price')} placeholder="0" />
            </Field>
            <Field label="Initial Payment (UZS) *" error={errors.paid_amount}>
              <input className="input" type="text" inputMode="numeric" value={form.paid_amount} onChange={set('paid_amount')} placeholder="0" />
            </Field>
          </div>
        </div>

        <div className="flex gap-3">
          <button type="button" onClick={() => navigate('/dashboard')} className="btn-secondary flex-1">Cancel</button>
          <button type="submit" disabled={submitting} className="btn-primary flex-1">
            {submitting ? 'Creating…' : 'Create Order'}
          </button>
        </div>
      </form>
    </div>
  )
}
