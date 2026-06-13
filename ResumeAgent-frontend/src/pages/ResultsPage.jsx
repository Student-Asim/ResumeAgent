import { useNavigate } from 'react-router-dom'
import AtsScoreCard from '../components/AtsScoreCard'
import AiDetectionCard from '../components/AiDetectionCard'
import ResumeEnhancerCard from '../components/ResumeEnhancerCard'
import InterviewCoachCard from '../components/InterviewCoachCard'

const s = {
  page: { maxWidth: 900, margin: '0 auto', padding: '2rem 1rem' },
  header: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' },
  title: { fontSize: '1.4rem', fontWeight: 600 },
  verdict: { padding: '0.5rem 1rem', background: '#1e2535', borderRadius: 8,
             border: '1px solid #334155', fontSize: '0.85rem', color: '#94a3b8' },
  grid: { display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' },
  btn: { padding: '0.6rem 1.2rem', background: '#6366f1', border: 'none', borderRadius: 8,
         color: '#fff', cursor: 'pointer', fontSize: '0.9rem' },
  actions: { display: 'flex', gap: '0.75rem', marginTop: '1.5rem' },
  empty: { textAlign: 'center', color: '#64748b', marginTop: '4rem' },
}

export default function ResultsPage({ result }) {
  const navigate = useNavigate()

  if (!result) return (
    <div style={s.page}>
      <p style={s.empty}>No results yet. <button style={s.btn} onClick={() => navigate('/')}>Upload a resume</button></p>
    </div>
  )

  function downloadLatex() {
    const tex = result.resume_enhancer?.latex
    if (!tex) return
    const blob = new Blob([tex], { type: 'text/plain' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a'); a.href = url
    a.download = 'resume_enhanced.tex'; a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <div style={s.page}>
      <div style={s.header}>
        <h1 style={s.title}>Analysis Results</h1>
        <span style={s.verdict}>{result.overall_verdict}</span>
      </div>

      {/* Priority actions */}
      {result.priority_actions?.length > 0 && (
        <div style={{ background: '#1e2535', border: '1px solid #334155', borderRadius: 12, padding: '1rem', marginBottom: '1.5rem' }}>
          <p style={{ fontSize: '0.75rem', color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: '0.75rem' }}>Priority actions</p>
          {result.priority_actions.map((a, i) => (
            <div key={i} style={{ borderLeft: '3px solid #6366f1', paddingLeft: '0.75rem', marginBottom: '0.5rem', fontSize: '0.9rem', color: '#cbd5e1' }}>{a}</div>
          ))}
        </div>
      )}

      {/* 4 result cards in a 2x2 grid */}
      <div style={s.grid}>
        <AtsScoreCard data={result.ats} />
        <AiDetectionCard data={result.ai_detection} />
        <ResumeEnhancerCard data={result.resume_enhancer} />
        <InterviewCoachCard data={result.interview_coach} practiceUrl={result.practice_url} />
      </div>

      {/* Action buttons */}
      <div style={s.actions}>
        <button style={s.btn} onClick={downloadLatex}>Download .tex for Overleaf</button>
        <a href={result.practice_url} target="_blank" rel="noreferrer">
          <button style={{ ...s.btn, background: '#10b981' }}>Open Practice UI</button>
        </a>
        <button style={{ ...s.btn, background: '#334155' }} onClick={() => navigate('/')}>Analyze another</button>
      </div>
    </div>
  )
}