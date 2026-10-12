const BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";
const unreachable = () => new Error(`Can't reach the API at ${BASE}. Is the backend running?`);

async function errorMessage(res) {
  try {
    const j = await res.json();
    return j.error?.message || `Request failed (${res.status})`;
  } catch {
    return `Request failed (${res.status})`;
  }
}

async function req(path, opts = {}) {
  let res;
  try {
    res = await fetch(BASE + path, { headers: { "Content-Type": "application/json" }, ...opts });
  } catch {
    throw unreachable();
  }
  if (!res.ok) throw new Error(await errorMessage(res));
  return res.status === 204 ? null : res.json();
}

export const api = {
  config: () => req("/llm/config"),
  stats: () => req("/knowledge/stats"),
  sessions: () => req("/sessions"),
  newSession: () => req("/sessions", { method: "POST", body: "{}" }),
  deleteSession: (id) => req(`/sessions/${id}`, { method: "DELETE" }),
  messages: (id) => req(`/sessions/${id}/messages`),
  artifacts: (id) => req(`/sessions/${id}/artifacts`),
};

// POST + read the SSE stream, calling onEvent for every "data:" frame.
export async function streamChat(id, body, onEvent, signal) {
  let res;
  try {
    res = await fetch(`${BASE}/sessions/${id}/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
      signal,
    });
  } catch (e) {
    if (e.name === "AbortError") return;
    throw unreachable();
  }
  if (!res.ok) throw new Error(await errorMessage(res));

  const reader = res.body.getReader();
  const dec = new TextDecoder();
  let buf = "";
  try {
    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      buf += dec.decode(value, { stream: true });
      let i;
      while ((i = buf.indexOf("\n\n")) !== -1) {
        const frame = buf.slice(0, i);
        buf = buf.slice(i + 2);
        const line = frame.split("\n").find((l) => l.startsWith("data:"));
        if (line) onEvent(JSON.parse(line.slice(5).trim()));
      }
    }
  } catch (e) {
    if (e.name !== "AbortError") throw e;
  }
}