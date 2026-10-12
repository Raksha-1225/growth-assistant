import { useEffect, useRef, useState } from "react";
import { api, streamChat } from "./api";
import Sidebar from "./components/Sidebar";
import Chat from "./components/Chat";
import ArtifactViewer from "./components/ArtifactViewer";

export default function App() {
  const [sessions, setSessions] = useState([]);
  const [activeId, setActiveId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [artifacts, setArtifacts] = useState([]);
  const [artifactId, setArtifactId] = useState(null);
  const [live, setLive] = useState(null); // text of an artifact being written, else null
  const [cfg, setCfg] = useState(null);
  const [stats, setStats] = useState(null);
  const [provider, setProvider] = useState(() => localStorage.getItem("provider") || "");
  const [mode, setMode] = useState("auto");
  const [busy, setBusy] = useState(false);
  const [stream, setStream] = useState(null);
  const [error, setError] = useState("");
  const [navOpen, setNavOpen] = useState(false);
  const [viewerOpen, setViewerOpen] = useState(false);
  const abortRef = useRef(null);

  useEffect(() => {
    api.config().then(setCfg).catch((e) => setError(e.message));
    api.stats().then(setStats).catch(() => {});
    api.sessions().then(setSessions).catch((e) => setError(e.message));
  }, []);

  const effective = provider || cfg?.default || "ollama";
  const artifact = artifacts.find((a) => a.id === artifactId) || null;
  const hasViewer = live !== null || artifacts.length > 0;

  function pickProvider(p) {
    setProvider(p);
    localStorage.setItem("provider", p);
  }

  function resetChat() {
    setActiveId(null); setMessages([]); setArtifacts([]); setArtifactId(null);
    setLive(null); setStream(null); setError(""); setViewerOpen(false);
  }

  async function selectSession(id) {
    if (busy) return;
    resetChat();
    setActiveId(id);
    try {
      const [msgs, arts] = await Promise.all([api.messages(id), api.artifacts(id)]);
      setMessages(msgs);
      setArtifacts(arts);
      setArtifactId(arts[0]?.id ?? null);
    } catch (e) { setError(e.message); }
  }

  async function removeSession(id) {
    try {
      await api.deleteSession(id);
      setSessions((s) => s.filter((x) => x.id !== id));
      if (id === activeId) resetChat();
    } catch (e) { setError(e.message); }
  }

  async function send(text) {
    if (busy || !text.trim()) return;
    setError(""); setBusy(true);
    const ctrl = new AbortController();
    abortRef.current = ctrl;
    try {
      let id = activeId;
      if (!id) {
        const s = await api.newSession();
        id = s.id;
        setActiveId(id);
      }
      setMessages((m) => [...m, { id: `tmp-${Date.now()}`, role: "user", content: text, sources: [] }]);
      const acc = { content: "", sources: [], meta: null, status: "Starting…" };
      let liveText = "";
      setStream({ ...acc });

      await streamChat(id, { message: text, provider: provider || null, mode }, (ev) => {
        switch (ev.type) {
          case "route":
            if (ev.intent !== "qa") { liveText = ""; setLive(""); setViewerOpen(true); }
            break;
          case "status": acc.status = ev.text; break;
          case "sources": acc.sources = ev.sources; break;
          case "meta": acc.meta = ev; break;
          case "token": acc.content += ev.text; break;
          case "artifact_delta": liveText += ev.text; setLive(liveText); break;
          case "artifact":
            setArtifacts((a) => [ev.artifact, ...a]);
            setArtifactId(ev.artifact.id);
            setLive(null);
            break;
          case "done":
            setMessages((m) => [...m, {
              id: ev.message_id, role: "assistant", content: acc.content, sources: ev.sources,
              provider: acc.meta?.provider, model: acc.meta?.model, fallback: acc.meta?.fallback,
            }]);
            break;
          case "error":
            setError(`${ev.message} (${ev.code})`);
            setLive(null);
            break;
        }
        setStream({ ...acc });
      }, ctrl.signal);
    } catch (e) {
      setError(e.message);
      setLive(null);
    } finally {
      setStream(null);
      setBusy(false);
      api.sessions().then(setSessions).catch(() => {});
      api.stats().then(setStats).catch(() => {});
    }
  }

  return (
    <div className={`app ${hasViewer ? "with-viewer" : ""}`}>
      <Sidebar sessions={sessions} activeId={activeId} onSelect={selectSession} onNew={() => !busy && resetChat()}
               onDelete={removeSession} stats={stats} open={navOpen} onClose={() => setNavOpen(false)} />

      <main className="chat-col">
        <header className="topbar">
          <button className="icon-btn only-mobile" aria-label="Open chat list" onClick={() => setNavOpen(true)}>☰</button>
          <h1>Lenny Growth Assistant</h1>
          <div className="provider" role="radiogroup" aria-label="Model provider">
            {(cfg?.providers || []).map((p) => (
              <button key={p.name} role="radio" aria-checked={effective === p.name}
                      className={effective === p.name ? "on" : ""} disabled={!p.configured || busy}
                      title={p.configured ? p.model : "Set CLOUD_API_KEY in .env to enable"}
                      onClick={() => pickProvider(p.name)}>
                {p.name} <span className="small">· {p.model}</span>
              </button>
            ))}
          </div>
          {hasViewer && (
            <button className="btn ghost only-mobile" onClick={() => setViewerOpen(true)}>Artifact</button>
          )}
        </header>

        <Chat messages={messages} stream={stream} busy={busy} error={error} mode={mode} setMode={setMode}
              onSend={send} onStop={() => abortRef.current?.abort()}
              kbEmpty={stats && stats.chunks === 0} />
      </main>

      {hasViewer && (
        <aside className={`viewer-col ${viewerOpen ? "open" : ""}`}>
          <ArtifactViewer artifact={artifact} live={live} list={artifacts}
                          onSelect={setArtifactId} onClose={() => setViewerOpen(false)} />
        </aside>
      )}
    </div>
  );
}