import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { listPortfolios, createPortfolio, deletePortfolio } from '../api/portfolios'
import { useAuth } from '../store/AuthContext'

export default function PortfoliosPage() {
  const [portfolios, setPortfolios] = useState([])
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [error, setError] = useState(null)
  const [creating, setCreating] = useState(false)
  const { logout } = useAuth()
  const navigate = useNavigate()

  useEffect(() => {
    listPortfolios().then(setPortfolios).catch(() => setError('Failed to load portfolios'))
  }, [])

  async function handleCreate(e) {
    e.preventDefault()
    setError(null)
    setCreating(true)
    try {
      const p = await createPortfolio(name, description)
      setPortfolios((prev) => [...prev, p])
      setName('')
      setDescription('')
    } catch (err) {
      setError(err.message)
    } finally {
      setCreating(false)
    }
  }

  async function handleDelete(id) {
    await deletePortfolio(id)
    setPortfolios((prev) => prev.filter((p) => p.id !== id))
  }

  return (
    <div className="min-h-screen p-6 max-w-2xl mx-auto">
      <div className="flex items-center justify-between mb-8">
        <h1 className="text-2xl font-bold">My Portfolios</h1>
        <button
          onClick={logout}
          className="text-sm text-slate-400 hover:text-slate-200 transition-colors"
        >
          Sign out
        </button>
      </div>

      {/* Create form */}
      <form onSubmit={handleCreate} className="bg-slate-800 rounded-2xl p-6 mb-6 space-y-3">
        <h2 className="text-sm font-semibold text-slate-300 mb-2">New portfolio</h2>
        <input
          placeholder="Name"
          value={name}
          onChange={(e) => setName(e.target.value)}
          required
          className="w-full bg-slate-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
        />
        <input
          placeholder="Description (optional)"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          className="w-full bg-slate-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
        />
        {error && <p className="text-red-400 text-sm">{error}</p>}
        <button
          type="submit"
          disabled={creating}
          className="bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 rounded-lg px-4 py-2 text-sm font-semibold transition-colors"
        >
          {creating ? 'Creating…' : 'Create'}
        </button>
      </form>

      {/* Portfolio list */}
      <div className="space-y-3">
        {portfolios.length === 0 && (
          <p className="text-slate-500 text-sm text-center py-8">No portfolios yet.</p>
        )}
        {portfolios.map((p) => (
          <div
            key={p.id}
            className="bg-slate-800 rounded-2xl px-6 py-4 flex items-center justify-between hover:bg-slate-700 transition-colors cursor-pointer"
            onClick={() => navigate(`/portfolios/${p.id}`)}
          >
            <div>
              <p className="font-medium">{p.name}</p>
              {p.description && (
                <p className="text-sm text-slate-400 mt-0.5">{p.description}</p>
              )}
            </div>
            <button
              onClick={(e) => { e.stopPropagation(); handleDelete(p.id) }}
              className="text-slate-500 hover:text-red-400 text-sm transition-colors ml-4"
            >
              Delete
            </button>
          </div>
        ))}
      </div>
    </div>
  )
}
