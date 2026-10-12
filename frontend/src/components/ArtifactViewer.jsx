import { useMemo, useState } from "react";
import DOMPurify from "dompurify";
import Markdown from "./Markdown";

// No network at all: no remote images, fonts, scripts, frames or form posts.
const CSP = "default-src 'none'; style-src 'unsafe-inline'; img-src data:; font-src data:";

function buildSrcDoc(html) {
  const clean = DOMPurify.sanitize(html, {
    WHOLE_DOCUMENT: true,
    FORBID_TAGS: ["script", "iframe", "object", "embed", "form", "input", "button",
                  "textarea", "select", "link", "meta", "base"],
    FORBID_ATTR: ["srcset", "formaction", "action"],
  });
  return `<!doctype html><meta charset="utf-8"><meta http-equiv="Content-Security-Policy" content="${CSP}">${clean}`;
}

function download(a) {
  const ext = a.kind === "html" ? "html" : "md";
  const name = (a.title || "artifact").toLowerCase()
    .replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "").slice(0, 60) || "artifact";
  const blob = new Blob([a.content], { type: a.kind === "html" ? "text/html" : "text/markdown" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = `${name}.${ext}`;
  link.click();
  URL.revokeObjectURL(url);
}

export default function ArtifactViewer({ artifact, live, list, onSelect, onClose }) {
  const [tab, setTab] = useState("preview");
  const [copied, setCopied] = useState(false);
  const srcDoc = useMemo(
    () => (artifact?.kind === "html" ? buildSrcDoc(artifact.content) : null),
    [artifact]
  );

  async function copy() {
    try {
      await navigator.clipboard.writeText(artifact.content);
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    } catch { /* clipboard blocked: ignore */ }
  }

  const writing = live !== null;
  return (
    <section className="viewer" aria-label="Artifact viewer">
      <div className="viewer-head">
        <button className="icon-btn only-mobile" onClick={onClose} aria-label="Close artifact viewer">←</button>
        {writing ? (
          <strong>Writing…</strong>
        ) : (
          <select aria-label="Choose artifact" value={artifact?.id ?? ""} onChange={(e) => onSelect(e.target.value)}>
            {list.map((a) => <option key={a.id} value={a.id}>{a.title} ({a.kind})</option>)}
          </select>
        )}
        {!writing && artifact && (
          <>
            <div className="tabs" role="tablist" aria-label="View mode">
              {["preview", "code"].map((t) => (
                <button key={t} role="tab" aria-selected={tab === t}
                        className={tab === t ? "on" : ""} onClick={() => setTab(t)}>
                  {t === "preview" ? "Preview" : "Code"}
                </button>
              ))}
            </div>
            <button className="btn ghost" onClick={copy}>{copied ? "Copied" : "Copy"}</button>
            <button className="btn ghost" onClick={() => download(artifact)}>Download</button>
          </>
        )}
      </div>

      <div className="viewer-body">
        {writing ? (
          <pre className="code">{live || "Starting…"}</pre>
        ) : !artifact ? (
          <p className="muted pad">No artifact yet.</p>
        ) : tab === "code" ? (
          <pre className="code">{artifact.content}</pre>
        ) : artifact.kind === "html" ? (
          <iframe title={`Preview of ${artifact.title}`} sandbox="" referrerPolicy="no-referrer" srcDoc={srcDoc} />
        ) : (
          <div className="doc"><Markdown text={artifact.content} /></div>
        )}
      </div>

      {!writing && artifact && (
        <p className="viewer-note">
          🔒 Sandboxed preview: scripts, forms, remote images/fonts, network calls and navigation are blocked.
        </p>
      )}
    </section>
  );
}