import React, { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { getProfile, changePassword } from '../api/client'
import { useAuth } from '../App'
import { User, Phone, Shield, Hash, Briefcase, CheckCircle, DollarSign, ArrowLeft, Lock, Eye, EyeOff } from 'lucide-react'

function fmt(n) {
  return Number(n || 0).toLocaleString('ru-RU') + ' UZS'
}

export default function Profile() {
  const navigate = useNavigate()
  const { logout } = useAuth()
  const [profile, setProfile] = useState(null)
  const [loading, setLoading] = useState(true)
  const [showPwd, setShowPwd] = useState(false)
  const [currentPwd, setCurrentPwd] = useState('')
  const [newPwd, setNewPwd] = useState('')
  const [showCurrent, setShowCurrent] = useState(false)
  const [showNew, setShowNew] = useState(false)
  const [pwdMsg, setPwdMsg] = useState('')
  const [pwdErr, setPwdErr] = useState('')
  const [pwdLoading, setPwdLoading] = useState(false)

  useEffect(() => {
    getProfile()
      .then(setProfile)
      .catch((err) => {
        if (err.response?.status === 401) { logout(); navigate('/login') }
      })
      .finally(() => setLoading(false))
  }, [])

  const handleChangePwd = async (e) => {
    e.preventDefault()
    setPwdMsg('')
    setPwdErr('')
    if (newPwd.length < 4) { setPwdErr('Parol kamida 4 ta belgidan iborat bo\'lishi kerak'); return }
    setPwdLoading(true)
    try {
      await changePassword({ current_password: currentPwd, new_password: newPwd })
      setPwdMsg('Parol muvaffaqiyatli o\'zgartirildi!')
      setCurrentPwd('')
      setNewPwd('')
      setShowPwd(false)
    } catch (err) {
      setPwdErr(err.response?.data?.detail || 'Parolni o\'zgartirib bo\'lmadi')
    } finally {
      setPwdLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <p className="text-gray-400">Yuklanmoqda…</p>
      </div>
    )
  }

  if (!profile) return null

  const infoItems = [
    { icon: User, label: 'To\'liq ism', value: profile.full_name || '—' },
    { icon: Shield, label: 'Rol', value: profile.role === 'master' ? 'Usta' : profile.role === 'admin' ? 'Admin' : 'Mijoz' },
    { icon: Phone, label: 'Telefon', value: profile.phone || '—' },
    { icon: Hash, label: 'Foydalanuvchi', value: profile.username || '—' },
    { icon: Hash, label: 'Telegram ID', value: profile.telegram_id || '—' },
  ]

  const statCards = [
    { label: 'Jami buyurtmalar', value: profile.total_orders, icon: Briefcase, color: 'text-blue-600', bg: 'bg-blue-50' },
    { label: 'Yopilgan buyurtmalar', value: profile.closed_orders, icon: CheckCircle, color: 'text-green-600', bg: 'bg-green-50' },
    { label: 'Jami tushum', value: fmt(profile.total_revenue), icon: DollarSign, color: 'text-purple-600', bg: 'bg-purple-50' },
    { label: 'Jami daromad', value: fmt(profile.total_earnings), icon: DollarSign, color: 'text-yellow-600', bg: 'bg-yellow-50' },
  ]

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b border-gray-100 sticky top-0 z-10">
        <div className="max-w-3xl mx-auto px-3 sm:px-4 py-2 sm:py-3 flex items-center gap-3">
          <button onClick={() => navigate('/dashboard')} className="btn-secondary">
            <ArrowLeft size={16} />
          </button>
          <h1 className="text-lg font-bold text-gray-900">Mening profilim</h1>
        </div>
      </header>

      <main className="max-w-3xl mx-auto px-3 sm:px-4 py-4 sm:py-6 space-y-4 sm:space-y-6">
        {/* Stats */}
        <div className="grid grid-cols-2 gap-4">
          {statCards.map(({ label, value, icon: Icon, color, bg }) => (
            <div key={label} className="card">
              <div className={`w-10 h-10 ${bg} rounded-xl flex items-center justify-center mb-3`}>
                <Icon size={20} className={color} />
              </div>
              <p className="text-xl font-bold text-gray-900">{value}</p>
              <p className="text-sm text-gray-500 mt-0.5">{label}</p>
            </div>
          ))}
        </div>

        {/* Info */}
        <div className="card">
          <h2 className="font-semibold text-gray-800 mb-4">Shaxsiy ma'lumotlar</h2>
          <dl className="space-y-3">
            {infoItems.map(({ icon: Icon, label, value }) => (
              <div key={label} className="flex items-center gap-3 py-2 border-b border-gray-50 last:border-0">
                <Icon size={18} className="text-gray-400 shrink-0" />
                <dt className="text-sm text-gray-500 w-32">{label}</dt>
                <dd className="text-sm font-medium text-gray-900">{value}</dd>
              </div>
            ))}
          </dl>
        </div>

        {/* Change Password */}
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h2 className="font-semibold text-gray-800">Xavfsizlik</h2>
            {!showPwd && (
              <button onClick={() => setShowPwd(true)} className="btn-secondary text-sm">
                <Lock size={14} /> Parolni o'zgartirish
              </button>
            )}
          </div>

          {showPwd && (
            <form onSubmit={handleChangePwd} className="space-y-3">
              <div className="relative">
                <input
                  type={showCurrent ? 'text' : 'password'}
                  value={currentPwd}
                  onChange={(e) => setCurrentPwd(e.target.value)}
                  placeholder="Joriy parol"
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent pr-10"
                  required
                />
                <button type="button" onClick={() => setShowCurrent(!showCurrent)} className="absolute right-3 top-2.5 text-gray-400">
                  {showCurrent ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </div>
              <div className="relative">
                <input
                  type={showNew ? 'text' : 'password'}
                  value={newPwd}
                  onChange={(e) => setNewPwd(e.target.value)}
                  placeholder="Yangi parol"
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent pr-10"
                  required
                />
                <button type="button" onClick={() => setShowNew(!showNew)} className="absolute right-3 top-2.5 text-gray-400">
                  {showNew ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </div>

              {pwdErr && <p className="text-red-600 text-sm">{pwdErr}</p>}
              {pwdMsg && <p className="text-green-600 text-sm">{pwdMsg}</p>}

              <div className="flex gap-2">
                <button type="submit" disabled={pwdLoading} className="btn-primary text-sm">
                  {pwdLoading ? 'Saqlanmoqda…' : 'Saqlash'}
                </button>
                <button type="button" onClick={() => { setShowPwd(false); setPwdErr(''); setPwdMsg('') }} className="btn-secondary text-sm">
                  Bekor qilish
                </button>
              </div>
            </form>
          )}
        </div>
      </main>
    </div>
  )
}
