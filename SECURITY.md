# Security

## Threat model

llmwiki-capture is designed for personal use behind a private network (Tailscale). The service accepts URLs and text from trusted devices and writes them to the local filesystem.

**In scope:** preventing accidental misuse, defending against malformed input, and avoiding common web vulnerabilities even though the service is not internet-facing by default.

**Out of scope:** multi-user access control, compliance frameworks, protection against a compromised Tailscale network. If your tailnet is compromised, the capture service is the least of your problems.

## Controls

### Authentication

- Bearer token required on all write endpoints (`POST /inbox`)
- Token compared using `secrets.compare_digest()` (constant-time) to prevent timing side-channels
- Token auto-generated on first run if not configured; stored in `config.yml` or environment variable
- Health endpoint (`GET /health`) is unauthenticated by design — it exposes no sensitive data

### Input validation

- **Filenames:** Generated from timestamp + UUID. No user-supplied input is used in file paths, preventing path traversal.
- **Frontmatter:** All user-supplied strings (title, URL, device) are sanitized before writing to YAML frontmatter. Double quotes replaced with single quotes, newlines stripped, length capped at 200 characters.
- **Body validation:** Pydantic enforces schema. Empty bodies and missing required fields return 422.
- **Duplicates:** URLs are checked against recent inbox files. Duplicates return 409 instead of writing again.

### Rate limiting

- In-memory sliding window: 60 requests per minute per client IP (configurable via `CAPTURE_RATE_LIMIT`)
- Resets on service restart
- Returns 429 when exceeded

### Request size

- HTTP request body capped at 1MB via uvicorn's `h11_max_incomplete_event_size`

### Network

- Default listen: `0.0.0.0:7199` — intended to be reachable from Tailscale peers
- **Not designed to be exposed to the public internet without additional protection** (e.g., Cloudflare Access, reverse proxy with auth)
- If using Cloudflare Tunnel, add Cloudflare Access policies to restrict who can reach the endpoint

## Reporting vulnerabilities

If you find a security issue, please open a GitHub issue or contact the maintainer directly. This is a personal-use project — responsible disclosure is appreciated but formal processes are not in place.
