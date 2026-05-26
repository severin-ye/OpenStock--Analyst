import { useState, useEffect, useCallback } from 'react'
import { api, type RankingData, type Company, type CompanyDetail } from '../lib/api'

export function useRankings(market?: string) {
  const [data, setData] = useState<RankingData[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchData = useCallback(async () => {
    try {
      setLoading(true)
      setError(null)
      const result = await api.getRankings(market)
      setData(result)
    } catch (err) {
      setError(err instanceof Error ? err.message : '加载失败')
    } finally {
      setLoading(false)
    }
  }, [market])

  useEffect(() => {
    fetchData()
  }, [fetchData])

  return { data, loading, error, refetch: fetchData }
}

export function useCompanies() {
  const [data, setData] = useState<Company[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    api.getCompanies()
      .then(setData)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false))
  }, [])

  return { data, loading, error }
}

export function useCompanyDetail(ticker: string) {
  const [data, setData] = useState<CompanyDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!ticker) return

    setLoading(true)
    api.getCompanyDetail(ticker)
      .then(setData)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false))
  }, [ticker])

  return { data, loading, error }
}

export function useRefresh() {
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<{ count: number; message: string } | null>(null)

  const refresh = async () => {
    try {
      setLoading(true)
      const res = await api.refreshData()
      setResult(res)
      return res
    } catch (err) {
      throw err
    } finally {
      setLoading(false)
    }
  }

  return { refresh, loading, result }
}
