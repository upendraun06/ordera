import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { PhoneIcon, SpinnerIcon, CheckIcon } from '../components/Icons'

const FEATURES = [
  'Answers calls 24/7 automatically',
  'Takes orders with full menu knowledge',
  'Handles allergy & dietary questions',
]

export default function Signup() {
  const [form,    setForm]    = useState({ email: '', password: '', restaurantName: '' })
  const [error,   setError]   = useState('')
  const [loading, setLoading] = useState(false)
  const { signup } = useAuth()
  const navigate   = useNavigate()

  const handleChange = (e) => setForm({ ...form, [e.target.name]: e.target.value })

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      await signup(form.email, form.password, form.restaurantName)
      navigate('/dashboard')
    } catch (err) {
      setError(err.response?.data?.detail || 'Signup failed. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center auth-bg px-4 py-8">
      <div className="w-full max-w-md animate-scale-in">

        {/* Logo */}
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
            Create your account
          </h1>
          <p className="text-sm mt-1" style={{ color: 'rgba(255,255,255,0.38)' }}>
            Start answering calls with AI in minutes
          </p>
        </div>

        {/* Feature pills */}
        <div className="flex flex-col gap-2 mb-6">
          {FEATURES.map((f, i) => (
            <div
              key={i}
              className="flex items-center gap-2.5 px-4 py-2.5 rounded-xl"
              style={{
                background: 'rgba(99,102,241,0.08)',
                border: '1px solid rgba(99,102,241,0.2)',
                animationDelay: `${i * 80}ms`,
              }}
            >
              <div
                className="flex items-center justify-center rounded-full flex-shrink-0"
                style={{ width: 18, height: 18, background: 'rgba(99,102,241,0.25)' }}
              >
                <CheckIcon size={10} className="text-indigo-400" style={{ color: '#a5b4fc' }} />
              </div>
              <span className="text-xs font-medium" style={{ color: 'rgba(255,255,255,0.65)' }}>
                {f}
              </span>
            </div>
          ))}
        </div>

        {/* Form card */}
        <div
          style={{
            background: 'rgba(255,255,255,0.04)',
            border: '1px solid rgba(255,255,255,0.1)',
            borderRadius: 20,
            padding: '28px 28px',
            backdropFilter: 'blur(20px)',
          }}
        >
          <form onSubmit={handleSubmit} className="space-y-4">

            <div>
              <label className="block text-xs font-semibold mb-1.5" style={{ color: 'rgba(255,255,255,0.55)' }}>
                Restaurant Name
              </label>
              <input
                name="restaurantName"
                value={form.restaurantName}
                onChange={handleChange}
                required
                autoFocus
                placeholder="e.g. Mario's Pizza"
                className="input"
                style={{ background: 'rgba(255,255,255,0.06)', borderColor: 'rgba(255,255,255,0.1)', color: 'rgba(255,255,255,0.88)' }}
              />
            </div>

            <div>
              <label className="block text-xs font-semibold mb-1.5" style={{ color: 'rgba(255,255,255,0.55)' }}>
                Email
              </label>
              <input
                type="email"
                name="email"
                value={form.email}
                onChange={handleChange}
                required
                placeholder="you@restaurant.com"
                className="input"
                style={{ background: 'rgba(255,255,255,0.06)', borderColor: 'rgba(255,255,255,0.1)', color: 'rgba(255,255,255,0.88)' }}
              />
            </div>

            <div>
              <label className="block text-xs font-semibold mb-1.5" style={{ color: 'rgba(255,255,255,0.55)' }}>
                Password
              </label>
              <input
                type="password"
                name="password"
                value={form.password}
                onChange={handleChange}
                required
                placeholder="8+ characters"
                minLength={8}
                className="input"
                style={{ background: 'rgba(255,255,255,0.06)', borderColor: 'rgba(255,255,255,0.1)', color: 'rgba(255,255,255,0.88)' }}
              />
            </div>

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

            <button
              type="submit"
              disabled={loading}
              className="btn-primary w-full mt-1"
              style={{ height: 44, fontSize: 14 }}
            >
              {loading ? (
                <span className="flex items-center gap-2">
                  <SpinnerIcon size={16} />
                  Creating account...
                </span>
              ) : (
                'Create Account — Free Trial'
              )}
            </button>

          </form>
        </div>

        <p className="text-center text-xs mt-5" style={{ color: 'rgba(255,255,255,0.3)' }}>
          Already have an account?{' '}
          <Link
            to="/login"
            className="font-semibold"
            style={{ color: '#a5b4fc' }}
            onMouseEnter={e => e.target.style.color = '#c7d2fe'}
            onMouseLeave={e => e.target.style.color = '#a5b4fc'}
          >
            Sign in
          </Link>
        </p>

      </div>
    </div>
  )
}
