import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts'
import type { RankingData } from '../lib/api'

interface RankingChartProps {
  data: RankingData[]
}

const COLORS = [
  '#059669', '#10b981', '#34d399', '#6ee7b7', '#a7f3d0',
  '#2563eb', '#3b82f6', '#60a5fa', '#93c5fd', '#bfdbfe',
  '#d97706', '#f59e0b', '#fbbf24', '#fcd34d', '#fde68a',
  '#dc2626', '#ef4444', '#f87171', '#fca5a5',
]

export function RankingChart({ data }: RankingChartProps) {
  const chartData = data.map((item, index) => ({
    name: item.name_zh,
    score: item.score_10,
    rank: index + 1,
    fill: COLORS[index % COLORS.length],
  }))

  return (
    <div className="chart-container">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart
          data={chartData}
          layout="vertical"
          margin={{ top: 5, right: 30, left: 100, bottom: 5 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
          <XAxis 
            type="number" 
            domain={[0, 10]}
            tick={{ fontSize: 12, fill: '#64748b' }}
            axisLine={{ stroke: '#e2e8f0' }}
          />
          <YAxis 
            type="category" 
            dataKey="name"
            tick={{ fontSize: 12, fill: '#0f172a' }}
            axisLine={{ stroke: '#e2e8f0' }}
            width={90}
          />
          <Tooltip
            content={({ active, payload }) => {
              if (!active || !payload?.[0]) return null
              const data = payload[0].payload
              return (
                <div className="bg-white/95 backdrop-blur-sm rounded-xl shadow-xl border border-slate-200 p-4">
                  <p className="font-semibold text-navy">{data.name}</p>
                  <p className="text-sm text-slate-500">排名 #{data.rank}</p>
                  <p className="text-2xl font-bold text-accent mt-1">{data.score.toFixed(1)}</p>
                  <p className="text-xs text-slate-400">十分制评分</p>
                </div>
              )
            }}
          />
          <Bar 
            dataKey="score" 
            radius={[0, 6, 6, 0]}
            maxBarSize={32}
          >
            {chartData.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={entry.fill} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}
