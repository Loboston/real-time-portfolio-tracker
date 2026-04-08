import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { getPortfolio, addPosition, deletePosition } from '../api/portfolios'
import { useAuth } from '../store/AuthContext'
import { usePortfolioSocket } from '../ws/usePortfolioSocket'

function StatusBadge({ status }) {
  const styles = {
    live: 'bg-emerald-500/20 text-emerald-400',
    connecting: 'bg-yellow-500/20 text-yellow-400',
    reconnecting: 'bg-yellow-500/20 text-yellow-400',
    error: 'bg-red-500/20 text-red-400',
  }
  const labels = {
    live: 'Live',
    connecting: 'Connecting…',
    reconnecting: 'Reconnecting…',
    error: 'Disconnected',
  }
  return (
    <span className={`text-xs font-medium px-2 py-1 rounded-full ${styles[status] ?? styles.error}`}>
      {labels[status] ?? status}
    </span>
  )
}

function fmt(value, decimals = 2) {
  return Number(value ?? 0).toFixed(decimals)
}

function PnlCell({ value }) {
  const n = Number(value ?? 0)
  const color = n >= 0 ? 'text-emerald-400' : 'text-red-400'
  return <span className={color}>{n >= 0 ? '+' : ''}{fmt(n)}</span>
}

export default function PortfolioDetailPage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const { token } = useAuth()

  const [portfolio, setPortfolio] = useState(null)
  const [loadError, setLoadError] = useState(null)

  // Add-position form state
  const [symbol, setSymbol] = useState('')
  const [quantity, setQuantity] = useState('')
  const [avgCost, setAvgCost] = useState('')
  const [addError, setAddError] = useState(null)
  const [adding, setAdding] = useState(false)

  const { data: liveData, status } = usePortfolioSocket(id, token)

  // Initial load via REST
  useEffect(() => {
    getPortfolio(id)
      .then(setPortfolio)
      .catch(() => setLoadError('Failed to load portfolio'))
  }, [id])

  // Merge live WebSocket updates into displayed data
  const display = liveData ?? portfolio

  async function handleAddPosition(e) {
    e.preventDefault()
    setAddError(null)
    setAdding(true)
    try {
      await addPosition(id, symbol.toUpperCase(), Number(quantity), Number(avgCost))
      // Refresh via REST to get updated positions list
      const updated = await getPortfolio(id)
      setPortfolio(updated)
      setSymbol('')
      setQuantity('')
      setAvgCost('')
    } catch (err) {
      setAddError(err.message)
    } finally {
      setAdding(false)
    }
  }

  async function handleDeletePosition(positionId) {
    await deletePosition(id, positionId)
    const updated = await getPortfolio(id)
    setPortfolio(updated)
  }

  if (loadError) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <p className="text-red-400">{loadError}</p>
      </div>
    )
  }

  if (!display) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <p className="text-slate-400">Loading…</p>
      </div>
    )
  }

  const positions = display.positions ?? []

  return (
    <div className="min-h-screen p-6 max-w-4xl mx-auto">
      {/* Header */}
      <div className="flex items-center gap-3 mb-2">
        <button
          onClick={() => navigate('/portfolios')}
          className="text-slate-400 hover:text-slate-200 text-sm transition-colors"
        >
          ← Back
        </button>
      </div>

      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold">{display.name}</h1>
        <StatusBadge status={status} />
      </div>

      {/* Summary cards */}
      <div className="grid grid-cols-2 gap-4 mb-8">
        <div className="bg-slate-800 rounded-2xl p-5">
          <p className="text-xs text-slate-400 mb-1">Total Value</p>
          <p className="text-2xl font-semibold">${fmt(display.total_value)}</p>
        </div>
        <div className="bg-slate-800 rounded-2xl p-5">
          <p className="text-xs text-slate-400 mb-1">Total P&amp;L</p>
          <p className="text-2xl font-semibold">
            <PnlCell value={display.total_pnl} />
          </p>
        </div>
      </div>

      {/* Positions table */}
      <div className="bg-slate-800 rounded-2xl overflow-hidden mb-6">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-slate-400 text-xs border-b border-slate-700">
              <th className="text-left px-5 py-3">Symbol</th>
              <th className="text-right px-5 py-3">Qty</th>
              <th className="text-right px-5 py-3">Avg Cost</th>
              <th className="text-right px-5 py-3">Price</th>
              <th className="text-right px-5 py-3">Value</th>
              <th className="text-right px-5 py-3">P&amp;L</th>
              <th className="text-right px-5 py-3">P&amp;L %</th>
              <th className="px-5 py-3"></th>
            </tr>
          </thead>
          <tbody>
            {positions.length === 0 && (
              <tr>
                <td colSpan={8} className="text-center text-slate-500 py-8">
                  No positions yet.
                </td>
              </tr>
            )}
            {positions.map((pos) => (
              <tr key={pos.id ?? pos.symbol} className="border-t border-slate-700/50 hover:bg-slate-700/30">
                <td className="px-5 py-3 font-medium">{pos.symbol}</td>
                <td className="px-5 py-3 text-right">{fmt(pos.quantity, 4)}</td>
                <td className="px-5 py-3 text-right">${fmt(pos.average_cost)}</td>
                <td className="px-5 py-3 text-right">${fmt(pos.current_price)}</td>
                <td className="px-5 py-3 text-right">${fmt(pos.market_value)}</td>
                <td className="px-5 py-3 text-right"><PnlCell value={pos.unrealized_pnl} /></td>
                <td className="px-5 py-3 text-right"><PnlCell value={pos.pnl_pct} /></td>
                <td className="px-5 py-3 text-right">
                  <button
                    onClick={() => handleDeletePosition(pos.id)}
                    className="text-slate-500 hover:text-red-400 transition-colors"
                  >
                    ✕
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Add position form */}
      <div className="bg-slate-800 rounded-2xl p-6">
        <h2 className="text-sm font-semibold text-slate-300 mb-3">Add position</h2>
        <form onSubmit={handleAddPosition} className="flex flex-wrap gap-3 items-end">
          <div>
            <label className="block text-xs text-slate-400 mb-1">Symbol</label>
            <input
              value={symbol}
              onChange={(e) => setSymbol(e.target.value)}
              placeholder="AAPL"
              required
              className="w-28 bg-slate-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 uppercase"
            />
          </div>
          <div>
            <label className="block text-xs text-slate-400 mb-1">Quantity</label>
            <input
              type="number"
              value={quantity}
              onChange={(e) => setQuantity(e.target.value)}
              placeholder="10"
              required
              min="0.0001"
              step="any"
              className="w-28 bg-slate-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
          </div>
          <div>
            <label className="block text-xs text-slate-400 mb-1">Avg Cost ($)</label>
            <input
              type="number"
              value={avgCost}
              onChange={(e) => setAvgCost(e.target.value)}
              placeholder="150.00"
              required
              min="0.01"
              step="any"
              className="w-32 bg-slate-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
          </div>
          <button
            type="submit"
            disabled={adding}
            className="bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 rounded-lg px-4 py-2 text-sm font-semibold transition-colors"
          >
            {adding ? 'Adding…' : 'Add'}
          </button>
        </form>
        {addError && <p className="text-red-400 text-sm mt-2">{addError}</p>}
      </div>
    </div>
  )
}
