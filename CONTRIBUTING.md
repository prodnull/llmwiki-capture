# Contributing

Contributions are welcome. This is a small project — keep it simple.

## Development setup

```bash
git clone https://github.com/prodnull/llmwiki-capture.git
cd llmwiki-capture
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
```

## Before submitting

```bash
ruff check capture/ tests/   # lint
ruff format capture/ tests/  # format
pytest tests/ -v             # test
```

All three must pass.

## Guidelines

- Keep the service minimal. It writes files to a directory. That's it.
- No database. No ORM. No frontend framework. No additional dependencies without a strong reason.
- Tests for every endpoint behavior. Arrange-Act-Assert pattern.
- Security-relevant changes need corresponding tests (auth bypass, input sanitization, etc.).

## Scope

In scope:
- Bug fixes
- New deployment targets (docs or config)
- Input handling improvements (new share sheet edge cases)
- Security hardening

Out of scope:
- Web UI (that's a separate project)
- Wiki compilation or processing (that's llm-wiki's job)
- User management / multi-tenancy
