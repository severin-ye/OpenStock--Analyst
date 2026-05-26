const API_BASE = '/api'

export interface Company {
  ticker: string
  name_zh: string
  name_en: string
  exchange: string
  sector: string
  market: string
  asset_category: string
}

export interface RankingData {
  ticker: string
  name_zh: string
  price: number
  currency: string
  market_cap: string
  score_10: number
  composite_score: number
  composite_rank: string
  l1_value: string
  l1_rank: string
  l2_value: string
  l2_rank: string
  l3_value: string
  l3_rank: string
  l4_value: string
  l4_rank: string
  asset_category: string
}

export interface CompanyDetail {
  ticker: string
  name_zh: string
  name_en: string
  exchange: string
  sector: string
  market: string
  price: number
  currency: string
  market_cap: string
  pe_ratio: string
  forward_pe: string
  peg_ratio: string
  ebit_ev: string
  roic: string
  f_score: number
  fcf_yield: string
  revenue_growth: string
  week52_low: string
  week52_high: string
  beta: string
  source: string
  ranking: {
    score_10: number
    composite_score: number
    composite_rank: string
    rows: Array<{
      layer: string
      dimension: string
      metric: string
      value: string
      rank: string
      weight: string
      verdict: string
    }>
  }
  reports: Array<{
    filename: string
    path: string
    size: number
    modified: string
  }>
}

export interface Report {
  filename: string
  path: string
  size: number
  modified: string
}

async function fetchJson<T>(url: string): Promise<T> {
  const res = await fetch(url)
  if (!res.ok) {
    throw new Error(`API error: ${res.status} ${res.statusText}`)
  }
  return res.json()
}

export const api = {
  // 获取排名数据
  getRankings: (market?: string) =>
    fetchJson<RankingData[]>(`${API_BASE}/rankings${market ? `?market=${market}` : ''}`),

  // 获取所有公司
  getCompanies: () =>
    fetchJson<Company[]>(`${API_BASE}/companies`),

  // 获取公司详情
  getCompanyDetail: (ticker: string) =>
    fetchJson<CompanyDetail>(`${API_BASE}/company/${ticker}`),

  // 获取报告列表
  getReports: (ticker?: string) =>
    fetchJson<{ reports: Record<string, Report[]> | Report[] }>(`${API_BASE}/reports${ticker ? `?ticker=${ticker}` : ''}`),

  // 刷新数据
  refreshData: () =>
    fetchJson<{ status: string; count: number; message: string }>(`${API_BASE}/refresh`, {
      method: 'POST',
    }),

  // 触发分析
  triggerAnalysis: (companyName: string, dryRun = false) =>
    fetchJson<{ status: string; message: string }>(`${API_BASE}/analyze`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ company_name: companyName, dry_run: dryRun }),
    }),

  // 获取市场分组
  getMarketGroups: () =>
    fetchJson<{ markets: Record<string, string[]> }>(`${API_BASE}/markets`),
}
