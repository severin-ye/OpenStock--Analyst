import { Radar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, ResponsiveContainer, Tooltip } from 'recharts'

interface RankingRow {
  layer: string
  dimension: string
  metric: string
  value: string
  rank: string
  weight: string
  verdict: string
}

interface RankingRadarProps {
  rows: RankingRow[]
}

function parseRankPercentage(rankStr: string): number {
  const match = rankStr.match(/#(\d+)\/(\d+)/)
  if (!match) return 50
  const rank = parseInt(match[1])
  const total = parseInt(match[2])
  return Math.round((total - rank + 1) / total * 100)
}

export function RankingRadar({ rows }: RankingRadarProps) {
  const data = rows.map((row) => ({
    metric: row.metric,
    score: parseRankPercentage(row.rank),
    fullMark: 100,
  }))

  return (
    <div className="w-full h-[300px]">
      <ResponsiveContainer width="100%" height="100%">
        <RadarChart cx="50%" cy="50%" outerRadius="70%" data={data}>
          <PolarGrid stroke="#e2e8f0" />
          <PolarAngleAxis 
            dataKey="metric" 
            tick={{ fontSize: 12, fill: '#0f172a' }}
          />
          <PolarRadiusAxis 
            angle={30} 
            domain={[0, 100]}
            tick={{ fontSize: 10, fill: '#94a3b8' }}
          />
          <Tooltip
            content={({ active, payload }) => {
              if (!active || !payload?.[0]) return null
              const data = payload[0].payload
              return (
                <div className="bg-white/95 backdrop-blur-sm rounded-xl shadow-xl border border-slate-200 p-3">
                  <p className="font-semibold text-navy text-sm">{data.metric}</p>
                  <p className="text-lg font-bold text-accent">{data.score}%</p>
                  <p className="text-xs text-slate-400">排名百分位</p>
                </div>
              )
            }}
          />
          <Radar
            name="排名百分位"
            dataKey="score"
            stroke="#2563eb"
            fill="#2563eb"
            fillOpacity={0.25}
            strokeWidth={2}
          />
        </RadarChart>
      </ResponsiveContainer>
    </div>
  )
}
