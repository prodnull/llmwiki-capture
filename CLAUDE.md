# llmwiki-capture

Minimal HTTP capture service for llm-wiki. Accepts URLs and text via POST, writes markdown inbox files.

## Stack

- Python 3.11+ with FastAPI + uvicorn
- No database, no ORM — filesystem only
- Pydantic for validation, PyYAML for config

## Architecture

Two endpoints (`POST /inbox`, `GET /health`), one config module, one test file. The service is intentionally simple — it's a dumb pipe to the filesystem. Wiki processing is handled by the llm-wiki plugin, not this service.

## Key constraints

- No user input in filenames (path traversal prevention)
- Sanitize all strings before writing YAML frontmatter
- Bearer token auth with constant-time comparison
- JSON-only request bodies
- Files written to the configured wiki inbox path

## Commands

```bash
# Run
llmwiki-capture

# Test
pytest tests/ -v

# Lint + format
ruff check capture/ tests/
ruff format capture/ tests/
```

## Config

Env vars take precedence over `config.yml`. Key vars: `WIKI_PATH`, `CAPTURE_TOKEN`, `CAPTURE_PORT`.

## Git

- User: prodnull / prodnull@users.noreply.github.com
- Conventional commits: `type(scope): description`
