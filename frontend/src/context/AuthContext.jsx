import { createContext, useContext, useState } from 'react'
import posthog from 'posthog-js'
import { authApi } from '../services/api'

const AuthContext = createContext(null)

function _identify(owner) {
  posthog.identify(owner.id, {
    email: owner.email,
    restaurant_name: owner.restaurant_name,
    plan: owner.plan || 'essential',
  })
}

export function AuthProvider({ children }) {
  const [owner, setOwner] = useState(() => {
    const stored = localStorage.getItem('owner')
    return stored ? JSON.parse(stored) : null
  })
  const [loading, setLoading] = useState(false)

  const loginRequest = async (email, password) => {
    const res = await authApi.loginRequest({ email, password })
    // If SMTP not configured, backend issues token directly (no OTP step)
    if (res.data.access_token) {
      localStorage.setItem('token', res.data.access_token)
      localStorage.setItem('owner', JSON.stringify(res.data.owner))
      setOwner(res.data.owner)
      _identify(res.data.owner)
      posthog.capture('login', { method: 'direct' })
    }
    return res.data // { message, otp?, dev_mode? } OR { access_token, owner }
  }

  const login = async (email, otp_code) => {
    const res = await authApi.loginVerify({ email, otp_code })
    localStorage.setItem('token', res.data.access_token)
    localStorage.setItem('owner', JSON.stringify(res.data.owner))
    setOwner(res.data.owner)
    _identify(res.data.owner)
    posthog.capture('login', { method: 'otp' })
    return res.data
  }

  const signup = async (email, password, restaurantName) => {
    const res = await authApi.signup({ email, password, restaurant_name: restaurantName })
    localStorage.setItem('token', res.data.access_token)
    localStorage.setItem('owner', JSON.stringify(res.data.owner))
    setOwner(res.data.owner)
    _identify(res.data.owner)
    posthog.capture('signup', { restaurant_name: restaurantName })
    return res.data
  }

  const logout = () => {
    authApi.logout().catch(() => {})
    localStorage.removeItem('token')
    localStorage.removeItem('owner')
    setOwner(null)
    posthog.capture('logout')
    posthog.reset()  // Clears identity so next user starts fresh
  }

  return (
    <AuthContext.Provider value={{ owner, setOwner, loginRequest, login, signup, logout, loading }}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => useContext(AuthContext)
