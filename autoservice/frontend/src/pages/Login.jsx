import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../App'
import axios from 'axios'

export default function Login({ mode = 'master' }) {
  const isAdmin = mode === 'admin'
  const { login, logout, token, role } = useAuth()
  const navigate = useNavigate()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (token) {
      if (isAdmin && role === 'admin') navigate('/admin', { replace: true })
      else if (!isAdmin && role !== 'admin') navigate('/dashboard', { replace: true })
      else { logout() }
    }
  }, [token, role, navigate, isAdmin])

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      const res = await axios.post('/api/auth/login', { username, password })
      const userRole = res.data.role
      if (isAdmin && userRole !== 'admin') {
        setError('Bu sahifa faqat admin uchun. Usta kirish: /login')
        setLoading(false)
        return
      }
      if (!isAdmin && userRole === 'admin') {
        login(res.data.access_token, userRole)
        navigate('/admin', { replace: true })
        return
      }
      login(res.data.access_token, userRole)
      navigate(userRole === 'admin' ? '/admin' : '/dashboard', { replace: true })
    } catch (err) {
      setError(err.response?.data?.detail || 'Noto\'g\'ri foydalanuvchi nomi yoki parol')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className={`min-h-screen flex items-center justify-center p-2 sm:p-4 ${isAdmin ? 'bg-gradient-to-br from-purple-700 to-purple-900' : 'bg-gradient-to-br from-blue-600 to-blue-800'}`}>
      <div className="bg-white rounded-2xl shadow-2xl p-5 sm:p-8 w-full max-w-md">
        <div className="text-center mb-8">
          <div className={`w-16 h-16 rounded-2xl flex items-center justify-center mx-auto mb-4 ${isAdmin ? 'bg-purple-600' : 'bg-blue-600'}`}>
            <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              {isAdmin
                ? <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                : <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" />
              }
            </svg>
          </div>
          <h1 className="text-2xl font-bold text-gray-900">AutoService</h1>
          <p className="text-gray-500 mt-1">{isAdmin ? 'Admin paneli' : 'Usta paneli'}</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Foydalanuvchi nomi</label>
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="Foydalanuvchi nomini kiriting"
              required
              autoFocus
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Parol</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="Parolni kiriting"
              required
            />
          </div>

          {error && (
            <div className="bg-red-50 text-red-600 px-4 py-2 rounded-lg text-sm">
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className={`w-full text-white py-2 px-4 rounded-lg font-medium disabled:opacity-50 disabled:cursor-not-allowed transition-colors ${isAdmin ? 'bg-purple-600 hover:bg-purple-700' : 'bg-blue-600 hover:bg-blue-700'}`}
          >
            {loading ? 'Kirish...' : 'Kirish'}
          </button>
        </form>

        <p className="text-center text-xs text-gray-400 mt-6">
          {isAdmin ? 'Faqat admin kirishi mumkin.' : 'Faqat ro\'yxatdan o\'tgan ustalar kirishi mumkin.'}
        </p>
      </div>
    </div>
  )
}
