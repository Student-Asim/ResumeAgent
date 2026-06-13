const s = {
  card: { background: '#1e2535', border: '1px solid #2d3748', borderRadius: 12, padding: '1.25rem' },
  title: { fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.08em', color: '#64748b', marginBottom: '0.75rem' },
  bullet: { marginBottom: '0.75rem', fontSize: '0.85rem' },
  orig: { color: '#64748b', textDecoration: 'line-through', marginBottom: '0.2rem' },
  improved: { color: '#4ade80', borderLeft: '3px solid #4ade80', paddingLeft: '0.5rem' },
}

export default function ResumeEnhancerCard({ data }) {
  if (!data) return null
  const bullets = data.enhanced_bullets?.slice(0, 3) || []
  return (
    <div style={s.card}>
      <p style={s.title}>Resume Enhancer</p>
      <p style={{ fontSize: '0.85rem', color: '#94a3b8', marginBottom: '1rem' }}>
        {data.enhanced_bullets?.length || 0} bullets rewritten in STAR format
      </p>

      {bullets.map((b, i) => (
        <div key={i} style={s.bullet}>
          <div style={s.orig}>{b.original?.slice(0, 80)}...</div>
          <div style={s.improved}>{b.improved}</div>
        </div>
      ))}

      {data.overleaf_url && (
        <a href={data.overleaf_url} target="_blank" rel="noreferrer"
           style={{ display: 'inline-block', marginTop: '0.75rem', padding: '0.4rem 0.8rem',
                    background: '#4CAF50', color: '#fff', borderRadius: 6, fontSize: '0.8rem', textDecoration: 'none' }}>
          Open Overleaf template
        </a>
      )}
    </div>
  )
}