export default function Sidebar({ sessions, activeId, onSelect, onNew, onDelete, stats, open, onClose }) {
  return (
    <>
      {open && <div className="scrim" onClick={onClose} aria-hidden="true" />}
      <nav className={`sidebar ${open ? "open" : ""}`} aria-label="Chat sessions">
        <button className="btn primary block" onClick={() => { onNew(); onClose(); }}>+ New chat</button>
        <ul className="session-list">
          {sessions.map((s) => (
            <li key={s.id} className={s.id === activeId ? "active" : ""}>
              <button className="session-btn" aria-current={s.id === activeId ? "true" : undefined}
                      onClick={() => { onSelect(s.id); onClose(); }}>
                {s.title}
              </button>
              <button className="icon-btn" aria-label={`Delete chat: ${s.title}`} onClick={() => onDelete(s.id)}>✕</button>
            </li>
          ))}
          {!sessions.length && <li className="muted pad">No chats yet</li>}
        </ul>
        <p className="muted small pad">
          {stats ? `${stats.episodes} episodes · ${stats.chunks} chunks indexed` : ""}
        </p>
      </nav>
    </>
  );
}