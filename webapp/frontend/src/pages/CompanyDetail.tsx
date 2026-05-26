import { useParams, Link } from 'react-router-dom'
import { 
  ArrowLeft, 
  TrendingUp, 
  TrendingDown, 
  Minus,
  ExternalLink,
  FileText,
  BarChart3,
  Shield,
  Target
} from 'lucide-react'
import { clsx } from 'clsx'
import { useCompanyDetail } from '../hooks/useApi'
import { RankingRadar } from '../components/RankingRadar'

function MetricCard({ label, value, sub, icon: Icon }: { 
  label: string
  value: string
  sub?: string
  icon?: React.ElementType
}) {
  return (
    <div className="metric-card">
      <div className="flex items-center gap-2 mb-1">
        {Icon && <Icon className="w-4 h-4 text-slate-400" />}
        <span className="text-xs text-slate-500 uppercase tracking-wider">{label}</span>
      </div>
      <p className="text-xl font-bold text-navy">{value}</p>
      {sub && <p className="text-xs text-slate-400 mt-1">{sub}</p>}
    </div>
  )
}

function VerdictBadge({ verdict }: { verdict: string }) {
  const isPositive = verdict.includes('优秀') || verdict.includes('核心') || verdict.includes('划算') || verdict.includes('安全')
  const isNegative = verdict.includes('偏贵') || verdict.includes('风险') || verdict.includes('已定价')
  
  return (
    <span className={clsx(
      'px-2 py-0.5 rounded-full text-xs font-medium',
      isPositive && 'bg-emerald-50 text-emerald-700',
      isNegative && 'bg-red-50 text-red-700',
      !isPositive && !isNegative && 'bg-slate-50 text-slate-700'
    )}>
      {verdict}
    </span>
  )
}

export function CompanyDetail() {
  const { ticker } = useParams<{ ticker: string }>()
  const { data, loading, error } = useCompanyDetail(ticker || '')

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="loading-spinner" />
        <span className="ml-3 text-slate-500">加载公司数据...</span>
      </div>
    )
  }

  if (error || !data) {
    return (
      <div className="flex flex-col items-center justify-center py-20 text-center">
        <div className="w-16 h-16 rounded-full bg-red-50 flex items-center justify-center mb-4">
          <span className="text-2xl">⚠️</span>
        </div>
        <p className="text-slate-600 mb-4">{error || '未找到公司数据'}</p>
        <Link to="/" className="btn-primary">返回排名</Link>
      </div>
    )
  }

  const scoreColor = data.ranking.score_10 >= 7.5 ? 'text-emerald-600' 
    : data.ranking.score_10 >= 6.0 ? 'text-blue-600'
    : data.ranking.score_10 >= 4.5 ? 'text-amber-600'
    : 'text-red-600'

  return (
    <div className="space-y-8">
      {/* 返回按钮 + 标题 */}
      <div className="flex items-start gap-4">
        <Link 
          to="/" 
          className="p-2 rounded-lg text-slate-400 hover:text-navy hover:bg-slate-100 transition-colors mt-1"
        >
          <ArrowLeft className="w-5 h-5" />
        </Link>
        <div className="flex-1">
          <div className="flex items-center gap-3">
            <h1 className="text-3xl font-bold text-navy">{data.name_zh}</h1>
            <span className="px-3 py-1 rounded-full bg-slate-100 text-sm text-slate-600">
              {data.ticker}
            </span>
          </div>
          <p className="text-slate-500 mt-1">
            {data.name_en} · {data.exchange} · {data.sector}
          </p>
        </div>
        <div className="text-right">
          <p className={clsx('text-5xl font-bold', scoreColor)}>
            {data.ranking.score_10.toFixed(1)}
          </p>
          <p className="text-sm text-slate-500">十分制评分</p>
          <p className="text-lg font-semibold text-navy mt-1">
            {data.ranking.composite_rank}
          </p>
        </div>
      </div>

      {/* KPI 卡片 */}
      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
        <MetricCard 
          label="当前价格" 
          value={`${data.currency}${data.price.toLocaleString(undefined, { minimumFractionDigits: 2 })}`}
          icon={Target}
        />
        <MetricCard 
          label="市值" 
          value={data.market_cap}
          icon={BarChart3}
        />
        <MetricCard 
          label="EBIT/EV" 
          value={data.ebit_ev || '—'}
          sub={data.ranking.rows[0]?.rank}
          icon={TrendingUp}
        />
        <MetricCard 
          label="ROIC" 
          value={data.roic || '—'}
          sub={data.ranking.rows[1]?.rank}
          icon={Shield}
        />
        <MetricCard 
          label="F-Score" 
          value={`${data.f_score}/9`}
          sub={data.ranking.rows[2]?.rank}
          icon={Shield}
        />
        <MetricCard 
          label="PEG" 
          value={data.peg_ratio || '—'}
          sub={data.ranking.rows[3]?.rank}
          icon={TrendingUp}
        />
      </div>

      {/* 排名详情 + 雷达图 */}
      <div className="grid lg:grid-cols-2 gap-8">
        {/* 排名表格 */}
        <div className="glass-card rounded-2xl p-6">
          <h2 className="text-lg font-semibold text-navy mb-4">四层排名详情</h2>
          <div className="space-y-4">
            {data.ranking.rows.map((row) => (
              <div key={row.layer} className="flex items-center gap-4 p-4 rounded-xl bg-slate-50">
                <div className="w-12 h-12 rounded-xl bg-accent/10 flex items-center justify-center">
                  <span className="text-lg font-bold text-accent">{row.layer}</span>
                </div>
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-medium text-navy">{row.dimension}</span>
                    <span className="text-xs text-slate-500">{row.weight}</span>
                  </div>
                  <div className="flex items-center gap-2 mt-1">
                    <span className="font-mono text-sm">{row.metric}: {row.value}</span>
                    <span className="text-xs text-slate-500">{row.rank}</span>
                  </div>
                </div>
                <VerdictBadge verdict={row.verdict} />
              </div>
            ))}
          </div>
          <div className="mt-4 p-4 rounded-xl bg-accent/5 border border-accent/10">
            <p className="text-sm text-slate-600">
              综合分: <span className="font-mono font-bold text-accent">{data.ranking.composite_score.toFixed(2)}</span>
              <span className="text-xs text-slate-400 ml-2">(越小越好)</span>
            </p>
          </div>
        </div>

        {/* 雷达图 */}
        <div className="glass-card rounded-2xl p-6">
          <h2 className="text-lg font-semibold text-navy mb-4">估值雷达图</h2>
          <RankingRadar rows={data.ranking.rows} />
        </div>
      </div>

      {/* 详细指标 */}
      <div className="glass-card rounded-2xl p-6">
        <h2 className="text-lg font-semibold text-navy mb-4">详细指标</h2>
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
          <div className="flex justify-between py-2 border-b border-slate-100">
            <span className="text-sm text-slate-500">PE (TTM)</span>
            <span className="text-sm font-medium">{data.pe_ratio || '—'}</span>
          </div>
          <div className="flex justify-between py-2 border-b border-slate-100">
            <span className="text-sm text-slate-500">Forward PE</span>
            <span className="text-sm font-medium">{data.forward_pe || '—'}</span>
          </div>
          <div className="flex justify-between py-2 border-b border-slate-100">
            <span className="text-sm text-slate-500">FCF Yield</span>
            <span className="text-sm font-medium">{data.fcf_yield || '—'}</span>
          </div>
          <div className="flex justify-between py-2 border-b border-slate-100">
            <span className="text-sm text-slate-500">营收增速</span>
            <span className="text-sm font-medium">{data.revenue_growth || '—'}</span>
          </div>
          <div className="flex justify-between py-2 border-b border-slate-100">
            <span className="text-sm text-slate-500">52周范围</span>
            <span className="text-sm font-medium">{data.week52_low} - {data.week52_high}</span>
          </div>
          <div className="flex justify-between py-2 border-b border-slate-100">
            <span className="text-sm text-slate-500">Beta</span>
            <span className="text-sm font-medium">{data.beta || '—'}</span>
          </div>
        </div>
        <p className="text-xs text-slate-400 mt-4">数据来源: {data.source}</p>
      </div>

      {/* 历史报告 */}
      {data.reports.length > 0 && (
        <div className="glass-card rounded-2xl p-6">
          <h2 className="text-lg font-semibold text-navy mb-4">历史报告</h2>
          <div className="space-y-2">
            {data.reports.map((report) => (
              <a
                key={report.filename}
                href={report.path}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center justify-between p-3 rounded-lg hover:bg-slate-50 transition-colors group"
              >
                <div className="flex items-center gap-3">
                  <FileText className="w-5 h-5 text-slate-400 group-hover:text-accent transition-colors" />
                  <div>
                    <p className="text-sm font-medium text-navy">{report.filename}</p>
                    <p className="text-xs text-slate-400">
                      {new Date(report.modified).toLocaleDateString('zh-CN')} · 
                      {(report.size / 1024).toFixed(1)} KB
                    </p>
                  </div>
                </div>
                <ExternalLink className="w-4 h-4 text-slate-400 group-hover:text-accent transition-colors" />
              </a>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
