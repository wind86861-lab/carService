import React, { useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../App'
import { authTelegram } from '../api/client'

export default function Login() {
  const { login, token } = useAuth()
  const navigate = useNavigate()
  const widgetRef = useRef(null)

  useEffect(() => {
    if (token) { navigate('/dashboard'); return }

    window.onTelegramAuth = async (user) => {
      try {
        const data = await authTelegram(user)
        login(data.access_token, data.role)
        navigate('/dashboard')
      } catch (e) {
        alert('Authentication failed. Make sure your Telegram account is registered with the bot.')
      }
    }

    const script = document.createElement('script')
    script.src = 'https://telegram.org/js/telegram-widget.js?22'
    script.setAttribute('data-telegram-login', import.meta.env.VITE_BOT_USERNAME || 'your_bot')
    script.setAttribute('data-size', 'large')
    script.setAttribute('data-onauth', 'onTelegramAuth(user)')
    script.setAttribute('data-request-access', 'write')
    script.async = true
    if (widgetRef.current) widgetRef.current.appendChild(script)

    return () => { delete window.onTelegramAuth }
  }, [token])

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-600 to-blue-800 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-2xl p-8 w-full max-w-md">
        <div className="text-center mb-8">
          <div className="w-16 h-16 bg-blue-600 rounded-2xl flex items-center justify-center mx-auto mb-4">
            <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" />
            </svg>
          </div>
          <h1 className="text-2xl font-bold text-gray-900">AutoService</h1>
          <p className="text-gray-500 mt-1">Master Panel — sign in with Telegram</p>
        </div>
        <div className="flex justify-center" ref={widgetRef} />
        <p className="text-center text-xs text-gray-400 mt-6">
          Only registered masters can access this panel.
        </p>
      </div>
    </div>
  )
}
