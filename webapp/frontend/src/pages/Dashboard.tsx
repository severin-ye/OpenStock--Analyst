import { useState } from 'react'
import { Link } from 'react-router-dom'
import { 
  TrendingUp, 
  TrendingDown, 
  Minus,
  ChevronRight,
  RefreshCw,
  Filter,
  BarChart3
} from 'lucide-react'
import { clsx } from 'clsx'
import { useRankings, useRefresh } from '../hooks/useApi'
import { RankingChart } from '../components/RankingChart'
import type { RankingData } from '../lib/api'

const markets = [
  { id: '', label: '全部市场', emoji: '🌍' },
  { id: 'US', label: '美股', emoji: '🇺🇸' },
  { id: 'HK', label: '港股', emoji: '🇭🇰' },
  { id: 'KR', label: '韩股', emoji: '🇰🇷' },
  { id: 'CN', label: 'A股', emoji: '🇨🇳' },
  { id: 'Crypto', label: '加密', emoji: '₿' },
]

function getScoreColor(score: number): string {
  if (score >= 7.5) return 'text-emerald-600 bg-emerald-50'
  if (score >= 6.0) return 'text-blue-600 bg-blue-50'
  if (score >= 4.5) return 'text-amber-600 bg-amber-50'
  return 'text-red-600 bg-red-50'
}

function getRankBadgeClass(rank: number): string {
  if (rank === 1) return 'rank-1'
  if (rank === 2) return 'rank-2'
  if (rank === 3) return 'rank-3'
  return 'rank-other'
}

function parseRank(rankStr: string): number {
  const match = rankStr.match(/#(\d+)/)
  return match ? parseInt(match[1]) : 0
}

function TrendIcon({ value }: { value: string }) {
  if (!value || value === 'N/A') return <Minus className="w-4 h-4 text-slate-400" />
  const num = parseFloat(value.replace(/[^-\d.]/g, ''))
  if (num > 0) return <TrendingUp className="w-4 h-4 text-emerald-500" />
  if (num < 0) return <TrendingDown className="w-4 h-4 text-red-500" />
  return <Minus className="w-4 h-4 text-slate-400" />
}

export function Dashboard() {
  const [selectedMarket, setSelectedMarket] = useState('')
  const { data: rankings, loading, error, refetch } = useRankings(selectedMarket || undefined)
  const { refresh, loading: refreshing } = useRefresh()

  const handleRefresh = async () => {
    try {
      await refresh()
      refetch()
    } catch (err) {
      console.error('刷新失败:', err)
    }
  }

  return (
    <div className="space-y-8">
      {/* 页面标题 */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-navy">投资标的排名</h1>
          <p className="text-slate-500 mt-1">
            Greenblatt 四层加权排名体系 · L1 EBIT/EV 40% · L2 ROIC 25% · L3 F-Score 25% · L4 PEG 10%
          </p>
        </div>
        <button
          onClick={handleRefresh}
          disabled={refreshing}
          className={clsx(
            'btn-secondary flex items-center gap-2',
            refreshing && 'opacity-50 cursor-not-allowed'
          )}
        >
          <RefreshCw className={clsx('w-4 h-4', refreshing && 'animate-spin')} />
          {refreshing ? '刷新中...' : '刷新数据'}
        </button>
      </div>

      {/* 市场过滤器 */}
      <div className="flex flex-wrap gap-2">
        {markets.map((market) => (
          <button
            key={market.id}
            onClick={() => setSelectedMarket(market.id)}
            className={clsx(
              'px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200',
              selectedMarket === market.id
                ? 'bg-accent text-white shadow-lg shadow-accent/25'
                : 'bg-white text-slate-600 hover:bg-slate-50 border border-slate-200'
            )}
          >
            <span className="mr-1">{market.emoji}</span>
            {market.label}
          </button>
        ))}
      </div>

      {/* 图表区域 */}
      {rankings.length > 0 && (
        <div className="glass-card rounded-2xl p-6">
          <div className="flex items-center gap-2 mb-4">
            <BarChart3 className="w-5 h-5 text-accent" />
            <h2 className="text-lg font-semibold text-navy">评分分布</h2>
          </div>
          <RankingChart data={rankings} />
        </div>
      )}

      {/* 排名表格 */}
      <div className="glass-card rounded-2xl overflow-hidden">
        {loading ? (
          <div className="flex items-center justify-center py-20">
            <div className="loading-spinner" />
            <span className="ml-3 text-slate-500">加载排名数据...</span>
          </div>
        ) : error ? (
          <div className="flex flex-col items-center justify-center py-20 text-center">
            <div className="w-16 h-16 rounded-full bg-red-50 flex items-center justify-center mb-4">
              <span className="text-2xl">⚠️</span>
            </div>
            <p className="text-slate-600 mb-4">{error}</p>
            <button onClick={refetch} className="btn-primary">
              重试
            </button>
          </div>
        ) : rankings.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-20 text-center">
            <div className="w-16 h-16 rounded-full bg-slate-50 flex items-center justify-center mb-4">
              <span className="text-2xl">📊</span>
            </div>
            <p className="text-slate-600 mb-2">暂无排名数据</p>
            <p className="text-sm text-slate-400">请点击"刷新数据"获取最新排名</p>
          </div>
        ) : (
          <div className="table-container">
            <table className="ranking-table">
              <thead>
                <tr>
                  <th className="w-16">排名</th>
                  <th>标的</th>
                  <th className="text-right">价格</th>
                  <th className="text-center">评分</th>
                  <th className="text-center">L1 EBIT/EV</th>
                  <th className="text-center">L2 ROIC</th>
                  <th className="text-center">L3 F-Score</th>
                  <th className="text-center">L4 PEG</th>
                  <th className="w-10"></th>
                </tr>
              </thead>
              <tbody>
                {rankings.map((item, index) => {
                  const rank = index + 1
                  return (
                    <tr key={item.ticker} className={rank <= 3 ? 'highlight' : ''}>
                      <td>
                        <span className={clsx('rank-badge', getRankBadgeClass(rank))}>
                          {rank}
                        </span>
                      </td>
                      <td>
                        <Link 
                          to={`/company/${item.ticker}`}
                          className="flex flex-col group"
                        >
                          <span className="font-semibold text-navy group-hover:text-accent transition-colors">
                            {item.name_zh}
                          </span>
                          <span className="text-xs text-slate-500">
                            {item.ticker} · {item.market_cap}
                          </span>
                        </Link>
                      </td>
                      <td className="text-right font-mono">
                        {item.currency}{item.price.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                      </td>
                      <td className="text-center">
                        <span className={clsx(
                          'inline-flex items-center justify-center w-16 py-1 rounded-lg text-sm font-bold',
                          getScoreColor(item.score_10)
                        )}>
                          {item.score_10.toFixed(1)}
                        </span>
                      </td>
                      <td className="text-center">
                        <div className="flex flex-col items-center">
                          <span className="text-sm font-medium">{item.l1_value}</span>
                          <span className="text-xs text-slate-500">{item.l1_rank}</span>
                        </div>
                      </td>
                      <td className="text-center">
                        <div className="flex flex-col items-center">
                          <span className="text-sm font-medium">{item.l2_value}</span>
                          <span className="text-xs text-slate-500">{item.l2_rank}</span>
                        </div>
                      </td>
                      <td className="text-center">
                        <div className="flex flex-col items-center">
                          <span className="text-sm font-medium">{item.l3_value}</span>
                          <span className="text-xs text-slate-500">{item.l3_rank}</span>
                        </div>
                      </td>
                      <td className="text-center">
                        <div className="flex flex-col items-center">
                          <span className="text-sm font-medium">{item.l4_value}</span>
                          <span className="text-xs text-slate-500">{item.l4_rank}</span>
                        </div>
                      </td>
                      <td>
                        <Link 
                          to={`/company/${item.ticker}`}
                          className="p-2 rounded-lg text-slate-400 hover:text-accent hover:bg-accent/5 transition-colors"
                        >
                          <ChevronRight className="w-4 h-4" />
                        </Link>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* 方法论说明 */}
      <div className="glass-card rounded-2xl p-6 border-l-4 border-accent">
        <h3 className="font-semibold text-navy mb-3">📊 排名方法论</h3>
        <div className="grid md:grid-cols-2 gap-4 text-sm text-slate-600">
          <div>
            <p className="font-medium text-navy mb-1">股票四层排名</p>
            <ul className="space-y-1">
              <li>• <strong>L1 (40%)</strong>: EBIT/EV — 便不便宜 (越高越好)</li>
              <li>• <strong>L2 (25%)</strong>: ROIC — 赚不赚钱 (越高越好)</li>
              <li>• <strong>L3 (25%)</strong>: F-Score — 会不会崩 (越高越好)</li>
              <li>• <strong>L4 (10%)</strong>: PEG — 增长值不值 (越低越好)</li>
            </ul>
          </div>
          <div>
            <p className="font-medium text-navy mb-1">加密资产适配</p>
            <ul className="space-y-1">
              <li>• <strong>BTC</strong>: MVRV + Hash Rate + 链上 F-Score + 减半周期</li>
              <li>• <strong>PoS</strong>: MCap/TVL + Staking + Crypto F-Score + 通胀率</li>
            </ul>
          </div>
        </div>
        <p className="text-xs text-slate-400 mt-4">
          综合分 = L1排名×0.40 + L2×0.25 + L3×0.25 + L4×0.10 (越小越好)
        </p>
      </div>
    </div>
  )
}
