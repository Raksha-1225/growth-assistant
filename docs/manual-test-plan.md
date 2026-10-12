# Manual test plan (UI)

Prereqs: `docker compose up`, Ollama running, ≥30 episodes ingested, open http://localhost:5173.

| # | Scenario | Steps | Expected |
|---|----------|-------|----------|
| 1 | Grounded answer | Ask "What do guests say about finding product-market fit?" | Streams an answer with [n] citations; "Sources" dropdown lists episodes; provider/model shown under the answer |
| 2 | Honest refusal | Ask "What is the capital of France?" | Says the transcripts don't cover it; no model call, instant |
| 3 | Follow-up memory | After #1 ask "Can you give an example?" | Answer stays on the same topic |
| 4 | Session isolation | Click "+ New chat", ask "what did I just ask?" | No knowledge of the previous chat; old chat reopens intact from the sidebar |
| 5 | Essay skill | Ask "Write a Ship 30 essay on improving onboarding" | Viewer opens, live text, final Markdown: title, hook, headings, bullets, takeaway, Sources list, ~1,250 words |
| 6 | HTML artifact | Ask "Create an HTML page with a checklist for a growth experiment" | Rendered in sandboxed preview; Code tab shows source; Copy and Download work |
| 7 | Artifact safety | Ask for an HTML page containing `<script>alert(1)</script>` and an external image | No alert; image not loaded; page still renders |
| 8 | Mode override | Set Mode = Q&A and ask for an essay | Answers as chat Q&A, no artifact |
| 9 | Provider toggle | Pick "cloud" without a key | Button disabled with a hint; with a key set, answers show provider "cloud" |
| 10 | Fallback | Set LLM_PROVIDER=cloud, FALLBACK_PROVIDER=ollama, no key; ask a question | Answer comes from Ollama; label shows "(fallback)" |
| 11 | Ollama down | Quit Ollama, send a message | Red banner: "Ollama is not reachable…"; app stays usable |
| 12 | DB down | `docker compose stop db`, send a message | Clear "database unavailable" error; recovers after `docker compose start db` |
| 13 | Empty KB | Fresh DB, open the app | Warning banner with the ingest command |
| 14 | Stop button | Start a long essay, press Stop | Generation stops; UI becomes usable again |
| 15 | Responsive | Resize below 960px | Sidebar becomes ☰ drawer; artifact opens full screen with a back arrow |
| 16 | Keyboard/a11y | Tab through the UI; Enter sends, Shift+Enter adds a newline | Visible focus on every control; tabs/radios are operable by keyboard |
