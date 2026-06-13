const s = {
  card: { background: '#1e2535', border: '1px solid #2d3748', borderRadius: 12, padding: '1.25rem' },
  title: { fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.08em', color: '#64748b', marginBottom: '0.75rem' },
  q: { padding: '0.6rem 0.75rem', background: '#0f1117', borderRadius: 8, borderLeft: '3px solid #c084fc',
       fontSize: '0.85rem', color: '#e2e8f0', marginBottom: '0.4rem' },
  btn: { display: 'inline-block', marginTop: '0.75rem', padding: '0.4rem 0.8rem',
         background: '#6366f1', color: '#fff', borderRadius: 6, fontSize: '0.8rem',
         textDecoration: 'none', border: 'none', cursor: 'pointer' },
}

export default function InterviewCoachCard({ data, practiceUrl }) {
  if (!data) return null
  const topQ = data.technical_questions?.slice(0, 2) || []
  return (
    <div style={s.card}>
      <p style={s.title}>Interview Coach</p>
      <p style={{ fontSize: '0.85rem', color: '#94a3b8', marginBottom: '1rem' }}>
        {data.technical_questions?.length || 0} technical · {data.behavioral_questions?.length || 0} behavioral
      </p>

      {topQ.map((q, i) => (
        <div key={i} style={s.q}>{q.question}</div>
      ))}

      {practiceUrl && (
        <a href={practiceUrl} target="_blank" rel="noreferrer" style={{ textDecoration: 'none' }}>
          <button style={s.btn}>Open Practice UI →</button>
        </a>
      )}
    </div>
  )
}