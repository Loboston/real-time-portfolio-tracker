import { api } from './client'

export const listPortfolios = () => api.get('/portfolios')

export const createPortfolio = (name, description) =>
  api.post('/portfolios', { name, description })

export const getPortfolio = (id) => api.get(`/portfolios/${id}`)

export const deletePortfolio = (id) => api.delete(`/portfolios/${id}`)

export const addPosition = (portfolioId, symbol, quantity, averageCost) =>
  api.post(`/portfolios/${portfolioId}/positions`, {
    symbol,
    quantity,
    average_cost: averageCost,
  })

export const deletePosition = (portfolioId, positionId) =>
  api.delete(`/portfolios/${portfolioId}/positions/${positionId}`)
