import { useState, useEffect } from 'react'
import { 
  FileText, 
  ExternalLink, 
  Calendar, 
  HardDrive,
  Search,
  FolderOpen
} from 'lucide-react'
import { clsx } from 'clsx'
import { api, type Report } from '../lib/api'

export function Reports() {
  const [reports, setReports] = useState<Record<string, Report[]>>({})
  const [loading, setLoading] = useState(true)
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedCompany, setSelectedCompany] = useState<string | null>(null)

  useEffect(() => {
    api.getReports()
      .then((res) => {
        if (res.reports && typeof res.reports === 'object' && !Array.isArray(res.reports)) {
          setReports(res.reports as Record<string, Report[]>)
        }
      })
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [])

  const companies = Object.keys(reports).sort()
  const filteredCompanies = companies.filter((c) =>
    c.includes(searchQuery)
  )

  const displayReports = selectedCompany 
    ? { [selectedCompany]: reports[selectedCompany] }
    : reports

  return (
    <div className="space-y-8">
      {/* 页面标题 */}
      <div>
        <h1 className="text-3xl font-bold text-navy">历史报告</h1>
        <p className="text-slate-500 mt-1">
          查看所有已生成的投资分析报告
        </p>
      </div>

      {/* 搜索和过滤 */}
      <div className="flex flex-col md:flex-row gap-4">
        <div className="relative flex-1">
          <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
          <input
            type="text"
            placeholder="搜索公司..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-12 pr-4 py-3 rounded-xl border border-slate-200 focus:border-accent focus:ring-2 focus:ring-accent/20 transition-all outline-none"
          />
        </div>
        <div className="flex flex-wrap gap-2">
          <button
            onClick={() => setSelectedCompany(null)}
            className={clsx(
              'px-4 py-2 rounded-lg text-sm font-medium transition-all',
              !selectedCompany
                ? 'bg-accent text-white'
                : 'bg-white text-slate-600 border border-slate-200 hover:border-accent/30'
            )}
          >
            全部
          </button>
          {filteredCompanies.map((company) => (
            <button
              key={company}
              onClick={() => setSelectedCompany(company)}
              className={clsx(
                'px-4 py-2 rounded-lg text-sm font-medium transition-all',
                selectedCompany === company
                  ? 'bg-accent text-white'
                  : 'bg-white text-slate-600 border border-slate-200 hover:border-accent/30'
              )}
            >
              {company}
              <span className="ml-1 text-xs opacity-60">({reports[company]?.length || 0})</span>
            </button>
          ))}
        </div>
      </div>

      {/* 报告列表 */}
      {loading ? (
        <div className="flex items-center justify-center py-20">
          <div className="loading-spinner" />
          <span className="ml-3 text-slate-500">加载报告列表...</span>
        </div>
      ) : Object.keys(displayReports).length === 0 ? (
        <div className="flex flex-col items-center justify-center py-20 text-center">
          <div className="w-16 h-16 rounded-full bg-slate-50 flex items-center justify-center mb-4">
            <FolderOpen className="w-8 h-8 text-slate-400" />
          </div>
          <p className="text-slate-600 mb-2">暂无报告</p>
          <p className="text-sm text-slate-400">运行分析后，报告将显示在这里</p>
        </div>
      ) : (
        <div className="space-y-8">
          {Object.entries(displayReports).map(([company, companyReports]) => (
            <div key={company} className="glass-card rounded-2xl overflow-hidden">
              <div className="px-6 py-4 bg-gradient-to-r from-slate-50 to-white border-b border-slate-200">
                <h2 className="text-lg font-semibold text-navy">{company}</h2>
                <p className="text-sm text-slate-500">{companyReports.length} 份报告</p>
              </div>
              <div className="divide-y divide-slate-100">
                {companyReports.map((report) => (
                  <a
                    key={report.filename}
                    href={report.path}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center justify-between px-6 py-4 hover:bg-blue-50/50 transition-colors group"
                  >
                    <div className="flex items-center gap-4">
                      <div className="w-10 h-10 rounded-xl bg-accent/10 flex items-center justify-center group-hover:bg-accent/20 transition-colors">
                        <FileText className="w-5 h-5 text-accent" />
                      </div>
                      <div>
                        <p className="font-medium text-navy group-hover:text-accent transition-colors">
                          {report.filename}
                        </p>
                        <div className="flex items-center gap-4 mt-1">
                          <span className="flex items-center gap-1 text-xs text-slate-500">
                            <Calendar className="w-3 h-3" />
                            {new Date(report.modified).toLocaleDateString('zh-CN', {
                              year: 'numeric',
                              month: 'long',
                              day: 'numeric',
                            })}
                          </span>
                          <span className="flex items-center gap-1 text-xs text-slate-500">
                            <HardDrive className="w-3 h-3" />
                            {(report.size / 1024).toFixed(1)} KB
                          </span>
                        </div>
                      </div>
                    </div>
                    <ExternalLink className="w-5 h-5 text-slate-400 group-hover:text-accent transition-colors" />
                  </a>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
