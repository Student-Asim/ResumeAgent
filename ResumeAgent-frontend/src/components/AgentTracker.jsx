const AGENTS = [
  { key: "ats",      label: "ATS Scorer",      step: 1, color: "#6366f1", desc: "Keyword matching + semantic scoring" },
  { key: "ai",       label: "AI Detector",     step: 2, color: "#f59e0b", desc: "Perplexity + burstiness analysis" },
  { key: "enhancer", label: "Resume Enhancer", step: 3, color: "#10b981", desc: "STAR format bullet rewrites" },
  { key: "coach",    label: "Interview Coach", step: 4, color: "#c084fc", desc: "Question + cheatsheet generation" },
];

const s = {
  sidebar: {
    width: 260, flexShrink: 0, background: "#1e2535",
    border: "1px solid #2d3748", borderRadius: 12, padding: "1.25rem",
    height: "fit-content", position: "sticky", top: "2rem",
  },
  title: { fontSize: "0.75rem", textTransform: "uppercase", letterSpacing: "0.08em", color: "#64748b", marginBottom: "1.25rem" },
  item: { display: "flex", alignItems: "flex-start", gap: "0.75rem", marginBottom: "1.25rem" },
  iconWrap: { display: "flex", flexDirection: "column", alignItems: "center" },
  icon: (status, color) => ({
    width: 32, height: 32, borderRadius: "50%", display: "flex", alignItems: "center",
    justifyContent: "center", fontSize: "0.85rem", fontWeight: 600, flexShrink: 0,
    background: status === "done"    ? color + "33" :
                status === "running" ? color + "22" : "#0f1117",
    border: `2px solid ${status === "done" ? color : status === "running" ? color : "#334155"}`,
    color: status === "done" ? color : status === "running" ? color : "#475569",
    transition: "all 0.3s",
  }),
  connector: (isLast, status, color) => ({
    width: 2, flex: 1, minHeight: 24, margin: "2px 0",
    background: status === "done" ? color : "#334155",
    transition: "background 0.4s",
    display: isLast ? "none" : "block",
  }),
  info: { flex: 1 },
  label: (status, color) => ({
    fontSize: "0.9rem", fontWeight: 500,
    color: status === "idle" ? "#64748b" : status === "running" ? color : "#f1f5f9",
    transition: "color 0.3s",
  }),
  desc: { fontSize: "0.78rem", color: "#64748b", marginTop: "0.15rem" },
  summary: (color) => ({ fontSize: "0.78rem", color, marginTop: "0.25rem", fontWeight: 500 }),
  spinner: { display: "inline-block", width: 10, height: 10, border: "2px solid transparent",
             borderTopColor: "currentColor", borderRadius: "50%",
             animation: "spin 0.7s linear infinite", marginRight: 4 },
  statusRow: { display: "flex", alignItems: "center", gap: "0.3rem", marginTop: "0.2rem" },
};

export default function AgentTracker({ agentStates }) {
  return (
    <div style={s.sidebar}>
      <style>{`@keyframes spin { to { transform: rotate(360deg); } } @keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.5} }`}</style>
      <p style={s.title}>Agent pipeline</p>

      {AGENTS.map((agent, idx) => {
        const state = agentStates[agent.key] || { status: "idle" };
        const isLast = idx === AGENTS.length - 1;

        return (
          <div key={agent.key} style={s.item}>
            <div style={s.iconWrap}>
              <div style={s.icon(state.status, agent.color)}>
                {state.status === "done"    ? "✓" :
                 state.status === "running" ? "…" : agent.step}
              </div>
              {!isLast && (
                <div style={s.connector(isLast, state.status, agent.color)} />
              )}
            </div>

            <div style={s.info}>
              <div style={s.label(state.status, agent.color)}>{agent.label}</div>
              <div style={s.desc}>{agent.desc}</div>

              {state.status === "running" && (
                <div style={s.statusRow}>
                  <div style={{ ...s.spinner, borderTopColor: agent.color }} />
                  <span style={{ fontSize: "0.75rem", color: agent.color }}>Running...</span>
                </div>
              )}
              {state.status === "done" && state.summary && (
                <div style={s.summary(agent.color)}>{state.summary}</div>
              )}
              {state.status === "idle" && (
                <div style={{ fontSize: "0.75rem", color: "#334155", marginTop: "0.2rem" }}>Waiting</div>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}