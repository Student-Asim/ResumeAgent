import { useState, useEffect, useRef } from "react";
import { useSearchParams, useNavigate } from "react-router-dom";
import { getPracticeData } from "../api/client";

const s = {
  page: { maxWidth: 800, margin: "0 auto", padding: "2rem 1rem" },
  header: { marginBottom: "1.5rem" },
  title: { fontSize: "1.4rem", fontWeight: 600, marginBottom: "0.25rem" },
  sub: { color: "#94a3b8", fontSize: "0.9rem" },
  tabs: { display: "flex", gap: "0.5rem", marginBottom: "1.5rem", flexWrap: "wrap" },
  tab: (active) => ({
    padding: "0.4rem 1rem", borderRadius: 6, border: "1px solid",
    borderColor: active ? "#6366f1" : "#334155",
    background: active ? "#6366f1" : "transparent",
    color: active ? "#fff" : "#94a3b8", cursor: "pointer", fontSize: "0.85rem",
  }),
  card: { background: "#1e2535", border: "1px solid #2d3748", borderRadius: 12, padding: "1.25rem", marginBottom: "1rem" },
  badge: (color) => ({ display: "inline-block", padding: "0.2rem 0.6rem", borderRadius: 20, fontSize: "0.75rem", fontWeight: 500, background: color + "22", color, marginRight: "0.4rem", marginBottom: "0.4rem" }),
  question: { fontSize: "1rem", fontWeight: 500, color: "#f1f5f9", marginBottom: "1rem", lineHeight: 1.5 },
  revealBtn: { padding: "0.45rem 1rem", background: "#334155", border: "none", color: "#94a3b8", borderRadius: 6, cursor: "pointer", fontSize: "0.85rem" },
  answer: { marginTop: "1rem", padding: "1rem", background: "#0f1117", borderLeft: "3px solid #6366f1", borderRadius: "0 8px 8px 0", fontSize: "0.9rem", color: "#cbd5e1", lineHeight: 1.6 },
  hint: { fontSize: "0.8rem", color: "#64748b", fontStyle: "italic", marginTop: "0.5rem" },
  rating: { display: "flex", gap: "0.5rem", marginTop: "1rem", alignItems: "center" },
  rateBtn: (bg, selected) => ({ padding: "0.3rem 0.8rem", borderRadius: 6, border: selected ? "2px solid #fff" : "none", background: bg, color: "#fff", cursor: "pointer", fontSize: "0.8rem" }),
  timerBox: { textAlign: "center", marginBottom: "1.5rem" },
  timerNum: { fontSize: "2.5rem", fontWeight: 700, color: "#6366f1", display: "block" },
  timerBtns: { display: "flex", gap: "0.5rem", justifyContent: "center", marginTop: "0.5rem" },
  timerBtn: { padding: "0.35rem 0.9rem", background: "#1e2535", border: "1px solid #334155", borderRadius: 6, color: "#e2e8f0", cursor: "pointer", fontSize: "0.8rem" },
  progress: { background: "#1e2535", borderRadius: 999, height: 6, marginBottom: "1.5rem" },
  progressBar: (pct) => ({ width: `${pct}%`, height: 6, background: "#6366f1", borderRadius: 999, transition: "width 0.3s" }),
  chip: (color) => ({ padding: "0.5rem 0.75rem", background: "#1e2535", borderRadius: 8, borderLeft: `3px solid ${color}`, marginBottom: "0.5rem", fontSize: "0.9rem", color: "#cbd5e1" }),
  empty: { textAlign: "center", color: "#64748b", padding: "3rem", fontSize: "0.9rem" },
  backBtn: { padding: "0.4rem 0.9rem", background: "#334155", border: "none", color: "#e2e8f0", borderRadius: 6, cursor: "pointer", fontSize: "0.85rem", marginBottom: "1rem" },
  overleafBtn: { display: "inline-flex", alignItems: "center", gap: "0.4rem", padding: "0.45rem 1rem", background: "#4CAF50", color: "#fff", borderRadius: 8, textDecoration: "none", fontSize: "0.85rem", fontWeight: 500, marginBottom: "1.5rem" },
};

function Timer() {
  const [seconds, setSeconds] = useState(120);
  const [running, setRunning] = useState(false);
  const intervalRef = useRef(null);

  const fmt = (s) => `${String(Math.floor(s / 60)).padStart(2, "0")}:${String(s % 60).padStart(2, "0")}`;

  const start = () => {
    if (running) return;
    setRunning(true);
    intervalRef.current = setInterval(() => setSeconds((s) => { if (s <= 0) { clearInterval(intervalRef.current); return 0; } return s - 1; }), 1000);
  };
  const pause = () => { clearInterval(intervalRef.current); setRunning(false); };
  const reset = (v = 120) => { pause(); setSeconds(v); };

  return (
    <div style={s.timerBox}>
      <span style={s.timerNum}>{fmt(seconds)}</span>
      <div style={s.timerBtns}>
        <button style={s.timerBtn} onClick={start}>Start</button>
        <button style={s.timerBtn} onClick={pause}>Pause</button>
        <button style={s.timerBtn} onClick={() => reset(120)}>Reset</button>
        <select style={s.timerBtn} onChange={(e) => reset(Number(e.target.value))}>
          <option value={120}>2 min</option>
          <option value={180}>3 min</option>
          <option value={300}>5 min</option>
        </select>
      </div>
    </div>
  );
}

function TechnicalPanel({ questions }) {
  const [revealed, setRevealed] = useState({});
  const [ratings, setRatings] = useState({});

  if (!questions?.length) return <p style={s.empty}>No technical questions.</p>;

  return questions.map((q, i) => (
    <div key={i} style={s.card}>
      <div style={{ marginBottom: "0.75rem" }}>
        <span style={s.badge("#60a5fa")}>{q.topic || "Technical"}</span>
        <span style={s.badge(q.difficulty === "easy" ? "#4ade80" : q.difficulty === "hard" ? "#f87171" : "#fbbf24")}>
          {q.difficulty || "medium"}
        </span>
      </div>
      <p style={s.question}>{i + 1}. {q.question}</p>
      <button style={s.revealBtn} onClick={() => setRevealed((r) => ({ ...r, [i]: !r[i] }))}>
        {revealed[i] ? "Hide answer" : "Show ideal answer"}
      </button>
      {revealed[i] && (
        <div style={s.answer}>
          <strong>Ideal answer:</strong><br />{q.ideal_answer}
          {q.follow_up && <p style={s.hint}>Follow-up: {q.follow_up}</p>}
          <div style={s.rating}>
            <span style={{ fontSize: "0.8rem", color: "#64748b" }}>Rate yourself:</span>
            {[["Needs work", "#450a0a", 1], ["Ok", "#713f12", 2], ["Nailed it", "#14532d", 3]].map(([label, bg, val]) => (
              <button key={val} style={s.rateBtn(bg, ratings[i] === val)} onClick={() => setRatings((r) => ({ ...r, [i]: val }))}>{label}</button>
            ))}
          </div>
        </div>
      )}
    </div>
  ));
}

function BehavioralPanel({ questions }) {
  const [revealed, setRevealed] = useState({});
  const [ratings, setRatings] = useState({});

  if (!questions?.length) return <p style={s.empty}>No behavioral questions.</p>;

  return questions.map((q, i) => (
    <div key={i} style={s.card}>
      <span style={s.badge("#c084fc")}>{q.theme || "Behavioral"}</span>
      <p style={s.question}>{i + 1}. {q.question}</p>
      {q.star_hint && <p style={s.hint}>STAR hint: {q.star_hint}</p>}
      <button style={{ ...s.revealBtn, marginTop: "0.75rem" }} onClick={() => setRevealed((r) => ({ ...r, [i]: !r[i] }))}>
        {revealed[i] ? "Hide answer" : "Show ideal answer"}
      </button>
      {revealed[i] && (
        <div style={s.answer}>
          <strong>Ideal answer outline:</strong><br />{q.ideal_answer}
          <div style={s.rating}>
            <span style={{ fontSize: "0.8rem", color: "#64748b" }}>Rate yourself:</span>
            {[["Needs work", "#450a0a", 1], ["Ok", "#713f12", 2], ["Nailed it", "#14532d", 3]].map(([label, bg, val]) => (
              <button key={val} style={s.rateBtn(bg, ratings[i] === val)} onClick={() => setRatings((r) => ({ ...r, [i]: val }))}>{label}</button>
            ))}
          </div>
        </div>
      )}
    </div>
  ));
}

function CheatsheetPanel({ data }) {
  return (
    <div style={s.card}>
      <p style={{ fontSize: "0.75rem", color: "#64748b", textTransform: "uppercase", letterSpacing: "0.08em", marginBottom: "0.75rem" }}>Company culture</p>
      <p style={{ color: "#94a3b8", fontSize: "0.9rem", marginBottom: "1.25rem" }}>{data.company_culture?.join(", ") || "Not detected"}</p>

      <p style={{ fontSize: "0.75rem", color: "#64748b", textTransform: "uppercase", letterSpacing: "0.08em", marginBottom: "0.75rem" }}>Talking points — emphasize these</p>
      {data.talking_points?.map((t, i) => <div key={i} style={s.chip("#10b981")}>{t}</div>)}

      <p style={{ fontSize: "0.75rem", color: "#64748b", textTransform: "uppercase", letterSpacing: "0.08em", margin: "1rem 0 0.75rem" }}>Red flags — avoid these</p>
      {data.red_flags_to_avoid?.map((r, i) => <div key={i} style={s.chip("#ef4444")}>{r}</div>)}
    </div>
  );
}

function AskPanel({ questions }) {
  return (
    <div style={s.card}>
      <p style={{ fontSize: "0.75rem", color: "#64748b", textTransform: "uppercase", letterSpacing: "0.08em", marginBottom: "0.75rem" }}>Questions to ask your interviewer</p>
      {questions?.length
        ? questions.map((q, i) => <div key={i} style={s.chip("#f59e0b")}>{q}</div>)
        : <p style={s.empty}>None generated.</p>}
    </div>
  );
}

export default function PracticePage({ sessionId: propSessionId }) {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [activeTab, setActiveTab] = useState("technical");

  // session can come from URL param or prop
  const sessionId = searchParams.get("session") || propSessionId;

  useEffect(() => {
    if (!sessionId) { setError("No session ID found."); setLoading(false); return; }
    getPracticeData(sessionId)
      .then((d) => { setData(d); setLoading(false); })
      .catch(() => { setError("Session not found or expired."); setLoading(false); });
  }, [sessionId]);

  const tabs = [
    { key: "technical",  label: `Technical (${data?.technical_questions?.length || 0})` },
    { key: "behavioral", label: `Behavioral (${data?.behavioral_questions?.length || 0})` },
    { key: "cheatsheet", label: "Cheatsheet" },
    { key: "ask",        label: "Ask interviewer" },
  ];

  const total = (data?.technical_questions?.length || 0) + (data?.behavioral_questions?.length || 0);

  if (loading) return <div style={{ ...s.empty, marginTop: "4rem" }}>Loading session...</div>;
  if (error)   return <div style={{ ...s.empty, marginTop: "4rem" }}>{error}<br /><button style={{ ...s.backBtn, marginTop: "1rem" }} onClick={() => navigate("/")}>Go back</button></div>;

  return (
    <div style={s.page}>
      <button style={s.backBtn} onClick={() => navigate("/results")}>← Back to results</button>

      <div style={s.header}>
        <h1 style={s.title}>Interview Practice — {data.job_title || "Role"}</h1>
        <p style={s.sub}>{data.seniority} · {total} questions total</p>
      </div>

      <a href="https://www.overleaf.com/latex/templates/jakes-resume/syzfjbzwjncs" target="_blank" rel="noreferrer" style={s.overleafBtn}>
        Open cheatsheet in Overleaf
      </a>

      <Timer />

      <div style={s.progress}>
        <div style={s.progressBar(0)} />
      </div>

      <div style={s.tabs}>
        {tabs.map((t) => (
          <button key={t.key} style={s.tab(activeTab === t.key)} onClick={() => setActiveTab(t.key)}>
            {t.label}
          </button>
        ))}
      </div>

      {activeTab === "technical"  && <TechnicalPanel  questions={data.technical_questions} />}
      {activeTab === "behavioral" && <BehavioralPanel questions={data.behavioral_questions} />}
      {activeTab === "cheatsheet" && <CheatsheetPanel data={data} />}
      {activeTab === "ask"        && <AskPanel        questions={data.questions_to_ask_interviewer} />}
    </div>
  );
}