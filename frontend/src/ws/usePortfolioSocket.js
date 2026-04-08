import { useEffect, useRef, useState } from 'react'

const RECONNECT_DELAY_MS = 3000

export function usePortfolioSocket(portfolioId, token) {
  const [data, setData] = useState(null)
  const [status, setStatus] = useState('connecting') // connecting | live | reconnecting | error
  const wsRef = useRef(null)
  const retryTimer = useRef(null)
  const unmounted = useRef(false)

  useEffect(() => {
    if (!portfolioId || !token) return
    unmounted.current = false

    function connect() {
      setStatus('connecting')
      const ws = new WebSocket(
        `ws://${window.location.host}/ws/portfolios/${portfolioId}?token=${token}`
      )
      wsRef.current = ws

      ws.onopen = () => {
        if (!unmounted.current) setStatus('live')
      }

      ws.onmessage = (event) => {
        if (!unmounted.current) {
          setData(JSON.parse(event.data))
        }
      }

      ws.onclose = () => {
        if (unmounted.current) return
        setStatus('reconnecting')
        retryTimer.current = setTimeout(connect, RECONNECT_DELAY_MS)
      }

      ws.onerror = () => {
        ws.close()
      }
    }

    connect()

    return () => {
      unmounted.current = true
      clearTimeout(retryTimer.current)
      wsRef.current?.close()
    }
  }, [portfolioId, token])

  return { data, status }
}
