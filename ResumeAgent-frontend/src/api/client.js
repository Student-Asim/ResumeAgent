const BASE = "http://localhost:8000";

export function streamAnalysis(formData, onEvent) {
  return new Promise(async (resolve, reject) => {
    try {
      const res = await fetch(`${BASE}/analyze-stream`, {
        method: "POST",
        body: formData,
      });

      if (!res.ok) throw new Error("Server error");

      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const parts = buffer.split("\n\n");
        buffer = parts.pop(); // keep incomplete chunk

        for (const part of parts) {
          const lines = part.trim().split("\n");
          let event = "message";
          let data = null;

          for (const line of lines) {
            if (line.startsWith("event: ")) event = line.slice(7);
            if (line.startsWith("data: ")) {
              try { data = JSON.parse(line.slice(6)); } catch {}
            }
          }

          if (data) onEvent(event, data);
          if (event === "complete") resolve(data.result);
          if (event === "error") reject(new Error(data.message));
        }
      }
    } catch (e) {
      reject(e);
    }
  });
}


export async function getPracticeData(sessionId) {
  const res = await fetch(`http://localhost:8000/practice-data?session=${sessionId}`)
  if (!res.ok) throw new Error("Session not found")
  return res.json()
}