import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { PhoneIcon, SpinnerIcon } from '../components/Icons'

export default function Login() {
  const [email,    setEmail]    = useState('')
  const [password, setPassword] = useState('')
  const [error,    setError]    = useState('')
  const [loading,  setLoading]  = useState(false)
  const { login }  = useAuth()
  const navigate   = useNavigate()

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      await login(email, password)
      navigate('/dashboard')
    } catch (err) {
      setError(err.response?.data?.detail || 'Invalid email or password.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div
      className="min-h-screen flex items-center justify-center auth-bg px-4"
    >
      {/* Card */}
      <div
        className="w-full max-w-md animate-scale-in"
        style={{
          background: 'rgba(255,255,255,0.03)',
          border: '1px solid rgba(255,255,255,0.1)',
          borderRadius: 20,
          padding: '40px 36px',
          backdropFilter: 'blur(20px)',
        }}
      >
        {/* Logo mark */}
        <div className="flex flex-col items-center mb-8">
          <div
            className="flex items-center justify-center rounded-2xl mb-4"
            style={{
              width: 52,
              height: 52,
              background: 'linear-gradient(135deg, #6366f1, #8b5cf6)',
              boxShadow: '0 8px 24px rgba(99,102,241,0.45)',
            }}
          >
            <PhoneIcon size={24} className="text-white" />
          </div>
          <h1
            className="text-2xl font-bold"
            style={{ color: 'rgba(255,255,255,0.92)', letterSpacing: '-0.03em' }}
          >
            Welcome back
          </h1>
          <p className="text-sm mt-1" style={{ color: 'rgba(255,255,255,0.38)' }}>
            Sign in to your restaurant dashboard
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Email */}
          <div>
            <label
              className="block text-xs font-semibold mb-1.5"
              style={{ color: 'rgba(255,255,255,0.55)' }}
            >
              Email
            </label>
            <input
              type="email"
              value={email}
              onChange={e => setEmail(e.target.value)}
              required
              autoFocus
              placeholder="you@restaurant.com"
              className="input"
              style={{
                background: 'rgba(255,255,255,0.06)',
                borderColor: 'rgba(255,255,255,0.1)',
                color: 'rgba(255,255,255,0.88)',
              }}
            />
          </div>

          {/* Password */}
          <div>
            <label
              className="block text-xs font-semibold mb-1.5"
              style={{ color: 'rgba(255,255,255,0.55)' }}
            >
              Password
            </label>
            <input
              type="password"
              value={password}
              onChange={e => setPassword(e.target.value)}
              required
              placeholder="••••••••"
              className="input"
              style={{
                background: 'rgba(255,255,255,0.06)',
                borderColor: 'rgba(255,255,255,0.1)',
                color: 'rgba(255,255,255,0.88)',
              }}
            />
          </div>

          {/* Error */}
          {error && (
            <div
              className="text-sm rounded-xl px-4 py-3 animate-shake"
              style={{
                background: 'rgba(239,68,68,0.12)',
                border: '1px solid rgba(239,68,68,0.3)',
                color: '#fca5a5',
              }}
            >
              {error}
            </div>
          )}

          {/* Submit */}
          <button
            type="submit"
            disabled={loading}
            className="btn-primary w-full mt-2"
            style={{ height: 44, fontSize: 14 }}
          >
            {loading ? (
              <span className="flex items-center gap-2">
                <SpinnerIcon size={16} />
                Signing in...
              </span>
            ) : (
              'Sign In'
            )}
          </button>
        </form>

        <p
          className="text-center text-xs mt-6"
          style={{ color: 'rgba(255,255,255,0.3)' }}
        >
          Don't have an account?{' '}
          <Link
            to="/signup"
            className="font-semibold transition-colors"
            style={{ color: '#a5b4fc' }}
            onMouseEnter={e => e.target.style.color = '#c7d2fe'}
            onMouseLeave={e => e.target.style.color = '#a5b4fc'}
          >
            Start free trial
          </Link>
        </p>
      </div>
    </div>
  )
}
