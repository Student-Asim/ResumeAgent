import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { streamAnalysis } from "../api/client";
import AgentTracker from "../components/AgentTracker";

const s = {
  layout: { display: "flex", gap: "2rem", maxWidth: 900, margin: "60px auto", padding: "0 1rem", alignItems: "flex-start" },
  main: { flex: 1 },
  title: { fontSize: "2rem", fontWeight: 600, marginBottom: "0.4rem" },
  sub: { color: "#94a3b8", marginBottom: "2rem", fontSize: "0.95rem" },
  card: { background: "#1e2535", border: "1px solid #2d3748", borderRadius: 12, padding: "1.5rem" },
  label: { display: "block", fontSize: "0.85rem", color: "#94a3b8", marginBottom: "0.4rem" },
  input: { width: "100%", padding: "0.6rem 0.8rem", background: "#0f1117", border: "1px solid #334155", borderRadius: 8, color: "#e2e8f0", fontSize: "0.9rem", marginBottom: "1rem", boxSizing: "border-box" },
  btn: (disabled) => ({ width: "100%", padding: "0.75rem", background: disabled ? "#334155" : "#6366f1", border: "none", borderRadius: 8, color: disabled ? "#64748b" : "#fff", fontSize: "1rem", fontWeight: 500, cursor: disabled ? "not-allowed" : "pointer" }),
  err: { color: "#f87171", fontSize: "0.85rem", marginTop: "0.75rem", padding: "0.6rem 0.8rem", background: "#450a0a22", borderRadius: 6 },
  progress: { marginTop: "1rem", fontSize: "0.85rem", color: "#94a3b8", textAlign: "center" },
};

const INITIAL_STATES = { ats: { status: "idle" }, ai: { status: "idle" }, enhancer: { status: "idle" }, coach: { status: "idle" } };

export default function UploadPage({ onResult }) {
  const navigate = useNavigate();
  const [file, setFile] = useState(null);
  const [jd, setJd] = useState("");
  const [jobTitle, setJobTitle] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [agentStates, setAgentStates] = useState(INITIAL_STATES);
  const [statusMsg, setStatusMsg] = useState("");

  const setAgent = (key, patch) =>
    setAgentStates((prev) => ({ ...prev, [key]: { ...prev[key], ...patch } }));

  async function handleSubmit() {
    if (!file) return setError("Please upload a resume PDF");
    if (!jd)   return setError("Please paste a job description");

    setError("");
    setLoading(true);
    setAgentStates(INITIAL_STATES);
    setStatusMsg("Starting analysis...");

    const form = new FormData();
    form.append("resume", file);
    form.append("job_description", jd);
    form.append("job_title", jobTitle);

    try {
      const result = await streamAnalysis(form, (event, data) => {
        if (event === "agent_start") {
          setAgent(data.agent, { status: "running" });
          setStatusMsg(`Running ${data.label}...`);
        }
        if (event === "agent_done") {
          setAgent(data.agent, { status: "done", summary: data.summary });
        }
        if (event === "error") {
          setError(data.message || "Analysis failed");
          setLoading(false);
        }
      });

      setStatusMsg("Complete!");
      onResult(result);
      setTimeout(() => navigate("/results"), 600);
    } catch (e) {
      setError("Analysis failed — make sure all servers are running");
      setLoading(false);
      setAgentStates(INITIAL_STATES);
    }
  }

  return (
    <div style={s.layout}>
      <div style={s.main}>
        <h1 style={s.title}>CareerForge</h1>
        <p style={s.sub}>ATS scoring · AI detection · Resume enhancer · Interview prep</p>

        <div style={s.card}>
          <label style={s.label}>Resume PDF</label>
          <input style={s.input} type="file" accept=".pdf" onChange={(e) => setFile(e.target.files[0])} />

          <label style={s.label}>Target job title</label>
          <input style={s.input} type="text" placeholder="e.g. Junior AI/ML Engineer" value={jobTitle} onChange={(e) => setJobTitle(e.target.value)} />

          <label style={s.label}>Job description</label>
          <textarea style={{ ...s.input, height: 160, resize: "vertical" }} placeholder="Paste the full job description here..." value={jd} onChange={(e) => setJd(e.target.value)} />

          <button style={s.btn(loading)} onClick={handleSubmit} disabled={loading}>
            {loading ? "Analyzing..." : "Analyze Resume"}
          </button>

          {statusMsg && loading && <p style={s.progress}>{statusMsg}</p>}
          {error && <p style={s.err}>{error}</p>}
        </div>
      </div>

      {/* Live agent tracker sidebar — always visible, lights up during analysis */}
      <AgentTracker agentStates={agentStates} />
    </div>
  );
}