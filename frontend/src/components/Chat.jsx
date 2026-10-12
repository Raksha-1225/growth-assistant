import { useEffect, useRef, useState } from "react";
import Markdown from "./Markdown";

const STARTERS = [
  "What do top PMs say about finding product-market fit?",
  "How should I prioritize a product roadmap?",
  "Write a Ship 30 essay on improving user onboarding",
];
const MODES = [["auto", "Auto"], ["qa", "Q&A"], ["essay", "Essay"], ["artifact", "Artifact"]];

function Sources({ sources }) {
  if (!sources?.length) return null;
  return (
    <details className="sources">
      <summary>Sources ({sources.length})</summary>
      <ol>
        {sources.map((s) => (
          <li key={s.n}>
            <strong>[{s.n}] {s.title}</strong> <span className="muted small">{Math.round(s.score * 100)}% match</span>
            <p className="small muted">{s.snippet}…</p>
          </li>
        ))}
      </ol>
    </details>
  );
}

function Bubble({ role, content, sources, provider, model, fallback }) {
  return (
    <article className={`bubble ${role}`}>
      {role === "assistant" ? <Markdown text={content} /> : <p>{content}</p>}
      {role === "assistant" && <Sources sources={sources} />}
      {role === "assistant" && provider && provider !== "none" && (
        <p className="meta small muted">
          {provider} · {model}{fallback ? " (fallback)" : ""}
        </p>
      )}
    </article>
  );
}

export default function Chat({ messages, stream, busy, error, onSend, onStop, mode, setMode, kbEmpty }) {
  const [text, setText] = useState("");
  const endRef = useRef(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [messages, stream]);

  function submit(e) {
    e?.preventDefault();
    if (!text.trim() || busy) return;
    onSend(text.trim());
    setText("");
  }

  const empty = !messages.length && !stream;
  return (
    <div className="chat">
      {kbEmpty && (
        <div className="banner warn" role="status">
          Knowledge base is empty. Run: <code>docker compose exec backend python -m app.rag.ingest --limit 30</code>
        </div>
      )}
      <div className="messages" role="log" aria-live="polite" aria-label="Conversation">
        {empty && (
          <div className="empty">
            <h2>Ask Lenny's archive anything</h2>
            <p className="muted">Answers are grounded in Lenny's Podcast transcripts, with sources.</p>
            <div className="starters">
              {STARTERS.map((s) => (
                <button key={s} className="btn ghost" onClick={() => onSend(s)} disabled={busy}>{s}</button>
              ))}
            </div>
          </div>
        )}
        {messages.map((m) => <Bubble key={m.id} {...m} />)}
        {stream && (
          <>
            {stream.content ? (
              <Bubble role="assistant" content={stream.content} sources={stream.sources}
                      provider={stream.meta?.provider} model={stream.meta?.model} fallback={stream.meta?.fallback} />
            ) : (
              <p className="status muted">{stream.status}</p>
            )}
          </>
        )}
        <div ref={endRef} />
      </div>

      {error && <div className="banner err" role="alert">{error}</div>}

      <form className="composer" onSubmit={submit}>
        <label className="sr-only" htmlFor="msg">Message</label>
        <textarea
          id="msg" rows={2} value={text} placeholder="Ask a question, or request an essay / HTML / Markdown…"
          onChange={(e) => setText(e.target.value)}
          onKeyDown={(e) => { if (e.key === "Enter" && !e.shiftKey) submit(e); }}
        />
        <div className="composer-row">
          <label className="small muted" htmlFor="mode">Mode</label>
          <select id="mode" value={mode} onChange={(e) => setMode(e.target.value)}>
            {MODES.map(([v, l]) => <option key={v} value={v}>{l}</option>)}
          </select>
          {busy
            ? <button type="button" className="btn" onClick={onStop}>Stop</button>
            : <button type="submit" className="btn primary" disabled={!text.trim()}>Send</button>}
        </div>
      </form>
    </div>
  );
}