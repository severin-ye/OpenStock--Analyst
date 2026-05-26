import { useState } from 'react'
import { 
  Search, 
  Play, 
  Loader2, 
  CheckCircle2, 
  XCircle,
  Zap
} from 'lucide-react'
import { clsx } from 'clsx'
import { useCompanies } from '../hooks/useApi'
import { api } from '../lib/api'

export function Analysis() {
  const { data: companies, loading: companiesLoading } = useCompanies()
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedCompany, setSelectedCompany] = useState<string | null>(null)
  const [analyzing, setAnalyzing] = useState(false)
  const [result, setResult] = useState<{ success: boolean; message: string } | null>(null)

  const filteredCompanies = companies.filter((c) =>
    c.name_zh.includes(searchQuery) ||
    c.ticker.toLowerCase().includes(searchQuery.toLowerCase()) ||
    c.name_en.toLowerCase().includes(searchQuery.toLowerCase())
  )

  const handleAnalyze = async () => {
    if (!selectedCompany) return

    setAnalyzing(true)
    setResult(null)

    try {
      const res = await api.triggerAnalysis(selectedCompany)
      setResult({ success: true, message: res.message })
    } catch (err) {
      setResult({ 
        success: false, 
        message: err instanceof Error ? err.message : '分析失败' 
      })
    } finally {
      setAnalyzing(false)
    }
  }

  return (
    <div className="max-w-4xl mx-auto space-y-8">
      {/* 页面标题 */}
      <div className="text-center">
        <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-gradient-to-br from-accent to-purple-600 shadow-lg shadow-accent/25 mb-4">
          <Zap className="w-8 h-8 text-white" />
        </div>
        <h1 className="text-3xl font-bold text-navy">交互式分析工具</h1>
        <p className="text-slate-500 mt-2">
          选择标的，触发实时分析，生成投资报告
        </p>
      </div>

      {/* 搜索和选择 */}
      <div className="glass-card rounded-2xl p-6 space-y-4">
        <div className="relative">
          <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
          <input
            type="text"
            placeholder="搜索公司名称、代码..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-12 pr-4 py-3 rounded-xl border border-slate-200 focus:border-accent focus:ring-2 focus:ring-accent/20 transition-all outline-none"
          />
        </div>

        {/* 公司列表 */}
        <div className="max-h-[400px] overflow-y-auto space-y-2">
          {companiesLoading ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="w-6 h-6 text-accent animate-spin" />
              <span className="ml-2 text-slate-500">加载公司列表...</span>
            </div>
          ) : filteredCompanies.length === 0 ? (
            <p className="text-center py-8 text-slate-500">未找到匹配的公司</p>
          ) : (
            filteredCompanies.map((company) => (
              <button
                key={company.ticker}
                onClick={() => setSelectedCompany(company.name_zh)}
                className={clsx(
                  'w-full flex items-center justify-between p-4 rounded-xl transition-all duration-200 text-left',
                  selectedCompany === company.name_zh
                    ? 'bg-accent text-white shadow-lg shadow-accent/25'
                    : 'bg-white hover:bg-slate-50 border border-slate-200'
                )}
              >
                <div>
                  <p className={clsx(
                    'font-semibold',
                    selectedCompany === company.name_zh ? 'text-white' : 'text-navy'
                  )}>
                    {company.name_zh}
                  </p>
                  <p className={clsx(
                    'text-sm',
                    selectedCompany === company.name_zh ? 'text-white/80' : 'text-slate-500'
                  )}>
                    {company.ticker} · {company.exchange}
                  </p>
                </div>
                <div className={clsx(
                  'px-3 py-1 rounded-full text-xs font-medium',
                  selectedCompany === company.name_zh
                    ? 'bg-white/20 text-white'
                    : 'bg-slate-100 text-slate-600'
                )}>
                  {company.market}
                </div>
              </button>
            ))
          )}
        </div>
      </div>

      {/* 分析按钮 */}
      <div className="flex flex-col items-center gap-4">
        <button
          onClick={handleAnalyze}
          disabled={!selectedCompany || analyzing}
          className={clsx(
            'btn-primary flex items-center gap-2 text-lg px-8 py-4',
            (!selectedCompany || analyzing) && 'opacity-50 cursor-not-allowed'
          )}
        >
          {analyzing ? (
            <>
              <Loader2 className="w-5 h-5 animate-spin" />
              分析中...
            </>
          ) : (
            <>
              <Play className="w-5 h-5" />
              开始分析
            </>
          )}
        </button>

        {!selectedCompany && (
          <p className="text-sm text-slate-400">请先选择一个标的</p>
        )}
      </div>

      {/* 结果显示 */}
      {result && (
        <div className={clsx(
          'glass-card rounded-2xl p-6 flex items-start gap-4',
          result.success ? 'border-l-4 border-emerald-500' : 'border-l-4 border-red-500'
        )}>
          {result.success ? (
            <CheckCircle2 className="w-6 h-6 text-emerald-500 flex-shrink-0 mt-0.5" />
          ) : (
            <XCircle className="w-6 h-6 text-red-500 flex-shrink-0 mt-0.5" />
          )}
          <div>
            <p className={clsx(
              'font-semibold',
              result.success ? 'text-emerald-700' : 'text-red-700'
            )}>
              {result.success ? '分析已启动' : '分析失败'}
            </p>
            <p className="text-sm text-slate-600 mt-1">{result.message}</p>
            {result.success && (
              <p className="text-xs text-slate-400 mt-2">
                分析任务正在后台运行，完成后将自动刷新。您可以在"历史报告"页面查看结果。
              </p>
            )}
          </div>
        </div>
      )}

      {/* 使用说明 */}
      <div className="glass-card rounded-2xl p-6 border-l-4 border-accent">
        <h3 className="font-semibold text-navy mb-3">💡 使用说明</h3>
        <ul className="space-y-2 text-sm text-slate-600">
          <li>• 选择标的后点击"开始分析"，系统将自动运行完整的分析流程</li>
          <li>• 分析包括：数据采集 → 四层排名计算 → LLM 报告生成 → HTML 渲染</li>
          <li>• 整个过程约需 1-3 分钟，完成后报告将保存到"历史报告"页面</li>
          <li>• 您也可以使用 CLI 命令：<code className="px-2 py-0.5 bg-slate-100 rounded text-xs font-mono">stock-analysis 公司名</code></li>
        </ul>
      </div>
    </div>
  )
}
