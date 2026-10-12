# The Lenny Growth Assistant

A grounded chat assistant over Lenny's Podcast transcripts. It answers product and growth questions with citations, writes Ship 30 for 30 style essays, and generates Markdown/HTML artifacts shown in a sandboxed side viewer. Runs fully locally and free with Ollama; a cloud model can be toggled in.

**Stack:** FastAPI · PostgreSQL + pgvector · Ollama (`qwen2.5:3b`, `nomic-embed-text`) · React (Vite) · Docker Compose

## Architecture (short)
`React UI → FastAPI → router (qa | essay | artifact) → pgvector retrieval → LLM provider (Ollama | cloud) → SSE stream`.
Sessions, messages, artifacts and transcript chunks live in Postgres. Details: [docs/architecture.md](docs/architecture.md). Also: [PRD](docs/PRD.md), [design](docs/design.md), [manual test plan](docs/manual-test-plan.md).

## Prerequisites
Docker Desktop, [Ollama](https://ollama.com), Git. Node 20 only if you run the frontend outside Docker. About 8 GB RAM is enough with a 3B model.

## Quick start
```bash
git clone <this-repo-url> && cd lenny-growth-assistant
cp .env.example .env                       # Windows: copy .env.example .env

ollama pull qwen2.5:3b
ollama pull nomic-embed-text

git clone --depth 1 https://github.com/ChatPRD/lennys-podcast-transcripts.git data/transcripts

docker compose up --build                  # db + api (:8000) + ui (:5173)
docker compose exec backend python -m app.rag.ingest --limit 30
```
Open http://localhost:5173 (use `localhost`, which the API's CORS allows). API docs: http://localhost:8000/docs

Re-run ingest with `--force` to refresh episodes, or without `--limit` to index everything (slow on CPU).

## Configuration (`.env`)
| Variable | Default | Notes |
|---|---|---|
| `LLM_PROVIDER` | `ollama` | `ollama` or `cloud`; also selectable per request from the UI |
| `FALLBACK_PROVIDER` | empty | If the chosen provider fails *before streaming starts*, retry with this one |
| `OLLAMA_BASE_URL` | `http://host.docker.internal:11434` | Ollama runs on the host |
| `OLLAMA_CHAT_MODEL` | `qwen2.5:3b` | Any model from `ollama list` |
| `OLLAMA_EMBED_MODEL` | `nomic-embed-text` | Embeddings always use Ollama |
| `CLOUD_API_KEY` | empty | Optional. Any OpenAI-compatible API |
| `CLOUD_BASE_URL` / `CLOUD_MODEL` | Gemini endpoint / `gemini-2.0-flash` | e.g. Groq: `https://api.groq.com/openai/v1`, OpenAI: `https://api.openai.com/v1` |
| `RETRIEVAL_TOP_K` / `RETRIEVAL_MIN_SCORE` | `4` / `0.45` | Below the score threshold the assistant says it can't answer |
| `LLM_TIMEOUT_SECONDS` | `120` | |
| `DATABASE_URL` | compose Postgres | |

Switching models needs no code change: edit `.env`, then `docker compose restart backend`.

## Local vs cloud
- **Local (demo default):** Ollama. Free and private, but slower. An essay takes several minutes on CPU.
- **Cloud (optional):** add `CLOUD_API_KEY`. The UI enables the "cloud" toggle once a key is present.
- **Fallback:** with `FALLBACK_PROVIDER` set, a failure before the first token (down, key missing, rate-limited) retries on the fallback and labels the answer "(fallback)". After the first token, errors surface instead, so one answer never mixes two models.

## Tests
```bash
docker compose exec backend pytest -q
```
Covers routing, chunking, retrieval ranking, provider fallback, the chat API, sessions and persistence, and artifact handling. LLM and embeddings are mocked, so only Postgres is needed. UI checks: [docs/manual-test-plan.md](docs/manual-test-plan.md).

## Project layout
