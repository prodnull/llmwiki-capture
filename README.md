# llmwiki-capture

A lightweight capture service for [llm-wiki](https://github.com/nvk/llm-wiki). Send URLs and notes from your phone's share sheet to your wiki inbox — two taps, any platform.

```
Phone (iOS/Android)              Your machine                llm-wiki
───────────────────              ────────────                ────────
Share sheet                       POST /inbox                 /wiki:ingest --inbox
  → "Wiki Inbox"                    → validate                  → fetch content
    → HTTP POST                       → write inbox file          → compile article
      → done                            → done                      → wiki
```

The capture service is a dumb pipe. It writes files. The wiki plugin does the thinking.

## Requirements

- Python 3.11+
- An [llm-wiki](https://github.com/nvk/llm-wiki) setup (the `~/wiki/` directory structure)
- [Tailscale](https://tailscale.com/) (or another way for your phone to reach the service)

## Quick start

```bash
# Clone and install
git clone https://github.com/prodnull/llmwiki-capture.git
cd llmwiki-capture
python -m venv .venv && source .venv/bin/activate
pip install .

# Configure
cp config.example.yml config.yml
# Edit config.yml — set wiki_path at minimum

# Run
llmwiki-capture
```

On first run, a bearer token is generated and printed. Save it — you need it for the mobile setup.

Then set up your phone: **[iOS](docs/setup-ios.md)** or **[Android](docs/setup-android.md)**.

## Configuration

All settings can be provided via `config.yml`, environment variables, or both (env vars take precedence).

| Setting | Env var | Config key | Default | Description |
|---------|---------|------------|---------|-------------|
| Wiki path | `WIKI_PATH` | `wiki_path` | `~/wiki` | Root of your llm-wiki directory |
| Topic wiki | `CAPTURE_WIKI_NAME` | `wiki_name` | _(none)_ | Target a specific topic wiki's inbox |
| Token | `CAPTURE_TOKEN` | `token` | _(generated)_ | Bearer token for authentication |
| Port | `CAPTURE_PORT` | `port` | `7199` | Listen port |
| Host | `CAPTURE_HOST` | `host` | `0.0.0.0` | Listen address |
| Rate limit | `CAPTURE_RATE_LIMIT` | `rate_limit` | `60` | Max requests per minute per client |

**Example:** To capture into the `cybersecurity` topic wiki:

```yaml
wiki_path: ~/wiki
wiki_name: cybersecurity
```

This writes inbox files to `~/wiki/topics/cybersecurity/inbox/`.

## API

Two endpoints.

### `POST /inbox`

Capture a URL or text note.

```bash
curl -X POST http://your-machine:7199/inbox \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com/article"}'
```

**Request body:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `url` | string | url or text | URL to capture |
| `text` | string | url or text | Text content to capture |
| `title` | string | no | Override the title (defaults to the URL) |
| `device` | string | no | Source device (e.g., `ios`, `android`) |

**Responses:**

| Status | Meaning |
|--------|---------|
| `201` | Captured. Returns `{"id": "...", "file": "inbox/..."}` |
| `401` | Missing or invalid bearer token |
| `409` | URL already in inbox (duplicate) |
| `422` | Validation error (e.g., neither url nor text provided) |
| `429` | Rate limited |

### `GET /health`

```bash
curl http://your-machine:7199/health
# {"status": "ok", "inbox_path": "...", "inbox_count": 5}
```

## Inbox file format

Each captured item becomes a markdown file compatible with llm-wiki's inbox processing:

```yaml
---
title: "Article title or URL"
source: "https://example.com/article"
type: inbox
captured: 2026-04-06T14:30:22+00:00
device: ios
---
```

Text captures include the body below the frontmatter. Filenames are timestamp + UUID (`20260406-143022-a1b2c3d4.md`) — no user input in filenames.

## Deployment

The service runs anywhere Python does.

| Method | Platform | Details |
|--------|----------|---------|
| Direct | Any | `llmwiki-capture` or `python -m capture.server` |
| [Docker](docs/deploy-docker.md) | Any | Best for NAS, Pi, VPS |
| [launchd](docs/deploy-macos.md) | macOS | Auto-start on login |
| [systemd](docs/deploy-linux.md) | Linux | Auto-start on boot |

## Networking

Your phone needs to reach the service. Two options:

**[Tailscale](https://tailscale.com/) (recommended):** Both devices join the same tailnet. The service is reachable at `http://your-machine-name:7199`. Free, no domain required.

**[Cloudflare Tunnel](https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/) (alternative):** Exposes the service as a public HTTPS URL behind Cloudflare Access. No VPN on the phone. Requires a domain on Cloudflare. See [networking docs](docs/networking.md).

## What if the service is down?

The mobile shortcut's HTTP request fails. The recommended setup includes a fallback: if the POST fails, the URL is saved to a local note (Apple Notes on iOS, Google Keep on Android). Process the backlog when the service is back up.

For always-on availability, deploy to a Raspberry Pi, NAS, or VPS using Docker.

## Security

This is designed for personal use behind a private network. The security model assumes Tailscale (or equivalent) as the network boundary.

- Bearer token authentication with constant-time comparison
- No user input in filenames (path traversal prevention)
- YAML frontmatter sanitization (injection prevention)
- Rate limiting per client IP (default 60/min)
- Request body size capped at 1MB

For details, see [SECURITY.md](SECURITY.md).

## Development

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

pytest tests/ -v          # run tests
ruff check capture/ tests/  # lint
ruff format capture/ tests/ # format
```

## License

[MIT](LICENSE)
