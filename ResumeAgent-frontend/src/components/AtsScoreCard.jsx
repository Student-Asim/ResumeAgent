const s = {
  card: { background: '#1e2535', border: '1px solid #2d3748', borderRadius: 12, padding: '1.25rem' },
  title: { fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.08em', color: '#64748b', marginBottom: '0.75rem' },
  score: { fontSize: '3rem', fontWeight: 700, color: '#6366f1', marginBottom: '0.25rem' },
  verdict: { fontSize: '0.85rem', color: '#94a3b8', marginBottom: '1rem' },
  row: { display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem', marginBottom: '0.35rem' },
  bar: { height: 6, background: '#334155', borderRadius: 4, marginTop: 2 },
  fill: (pct) => ({ width: `${pct}%`, height: 6, background: '#6366f1', borderRadius: 4 }),
  chip: { display: 'inline-block', padding: '0.2rem 0.5rem', background: '#450a0a', color: '#f87171',
          borderRadius: 20, fontSize: '0.75rem', marginRight: '0.3rem', marginBottom: '0.3rem' },
}

export default function AtsScoreCard({ data }) {
  if (!data) return null
  const b = data.breakdown || {}
  return (
    <div style={s.card}>
      <p style={s.title}>ATS Score</p>
      <p style={s.score}>{data.score}<span style={{ fontSize: '1rem', color: '#64748b' }}>/100</span></p>
      <p style={s.verdict}>{data.verdict}</p>

      {Object.entries(b).map(([k, v]) => (
        <div key={k} style={{ marginBottom: '0.6rem' }}>
          <div style={s.row}><span style={{ color: '#cbd5e1' }}>{k.replace(/_/g, ' ')}</span><span>{v}%</span></div>
          <div style={s.bar}><div style={s.fill(v)} /></div>
        </div>
      ))}

      {data.missing?.required?.length > 0 && (
        <div style={{ marginTop: '0.75rem' }}>
          <p style={{ ...s.title, marginBottom: '0.4rem' }}>Missing required</p>
          {data.missing.required.map(k => <span key={k} style={s.chip}>{k}</span>)}
        </div>
      )}
    </div>
  )
}