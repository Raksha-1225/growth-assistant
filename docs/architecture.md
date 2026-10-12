# Architecture Decisions — Lenny Growth Assistant

## 1. Database and ORM

The application uses PostgreSQL with SQLAlchemy's asynchronous API. The `asyncpg` driver provides asynchronous database connectivity, while SQLAlchemy models define the structure of sessions, messages, artifacts, and transcript chunks.

The pgvector extension supports vector storage for semantic retrieval over podcast transcripts.

## 2. Database initialization

For the initial development version, database tables are initialized at application startup using SQLAlchemy's `create_all`.

**Trade-off:** This reduces setup complexity and allows rapid iteration. However, `create_all` does not migrate existing tables when the schema changes. A migration tool such as Alembic should be introduced before production deployment.

## 3. Session and message identifiers

Chat sessions use UUIDs, while messages use auto-incrementing integer IDs. Integer message IDs provide a simple ordering key for retrieving messages within a session.

## 4. API error handling

The backend returns structured errors for application failures, invalid requests, and database errors. Request IDs help correlate API responses with structured application logs.

## 5. Local LLM execution

The initial configuration uses Ollama to run a local language model. This reduces dependence on paid API services and keeps model inference on the developer's machine.

The application uses a lightweight custom agent layer rather than adding a separate coding-agent runtime. This keeps the architecture simpler for the available hardware.

## 6. Development versus production

The current setup is intended for local development. Production readiness will require database migrations, stronger secret management, authentication and authorization, appropriate rate limits, and deployment-specific configuration.
