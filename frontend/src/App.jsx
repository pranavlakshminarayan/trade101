import { useState } from 'react'
import Welcome from './components/Welcome.jsx'
import Research from './components/Research.jsx'
import { research as fetchResearch } from './api.js'

export default function App() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [recent, setRecent] = useState([])

  async function runSearch(ticker) {
    setLoading(true); setError(null); setData(null)
    try {
      const bundle = await fetchResearch(ticker)
      setData(bundle)
      setRecent((r) => [bundle.ticker, ...r.filter((x) => x !== bundle.ticker)].slice(0, 6))
    } catch (e) {
      setError(e.message || 'Something went wrong')
    } finally {
      setLoading(false)
    }
  }

  const goHome = () => { setData(null); setError(null) }

  if (loading) {
    return (
      <div className="loading">
        <div className="spinner" />
        Pulling live data…
      </div>
    )
  }

  if (data) return <Research data={data} onBack={goHome} />

  return (
    <>
      <Welcome onSearch={runSearch} recent={recent} />
      {error && (
        <div style={{ position: 'fixed', left: 0, right: 0, bottom: 20, display: 'flex', justifyContent: 'center' }}>
          <div className="err" style={{ maxWidth: 560 }}>⚠️ {error}</div>
        </div>
      )}
    </>
  )
}
