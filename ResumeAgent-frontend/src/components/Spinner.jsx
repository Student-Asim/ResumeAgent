export default function Spinner() {
  return (
    <div style={{ textAlign: 'center', padding: '1rem', color: '#94a3b8', fontSize: '0.9rem' }}>
      <div style={{
        width: 32, height: 32, border: '3px solid #334155',
        borderTop: '3px solid #6366f1', borderRadius: '50%',
        animation: 'spin 0.8s linear infinite', margin: '0 auto 0.5rem',
      }} />
      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
      Analyzing with 4 agents...
    </div>
  )
}