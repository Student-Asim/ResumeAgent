const riskColor = { LOW: '#4ade80', MEDIUM: '#fbbf24', HIGH: '#f87171' }

const s = {
  card: { background: '#1e2535', border: '1px solid #2d3748', borderRadius: 12, padding: '1.25rem' },
  title: { fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.08em', color: '#64748b', marginBottom: '0.75rem' },
  score: { fontSize: '3rem', fontWeight: 700, marginBottom: '0.25rem' },
  tip: { padding: '0.5rem 0.75rem', background: '#0f1117', borderRadius: 8, borderLeft: '3px solid #f59e0b',
         fontSize: '0.85rem', color: '#cbd5e1', marginBottom: '0.4rem' },
}

export default function AiDetectionCard({ data }) {
  if (!data) return null
  const color = riskColor[data.risk_level] || '#94a3b8'
  return (
    <div style={s.card}>
      <p style={s.title}>AI Detection</p>
      <p style={{ ...s.score, color }}>{data.score}<span style={{ fontSize: '1rem', color: '#64748b' }}>/100</span></p>
      <p style={{ fontSize: '0.85rem', color: '#94a3b8', marginBottom: '1rem' }}>
        {data.verdict} · risk: <span style={{ color }}>{data.risk_level}</span>
        {' '}· {data.flagged_count} sentences flagged
      </p>
      {data.top_tips?.map((t, i) => <div key={i} style={s.tip}>{t}</div>)}
    </div>
  )
}