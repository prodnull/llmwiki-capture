"""llmwiki-capture: minimal HTTP inbox for llm-wiki."""

from __future__ import annotations

import logging
import secrets
import time
import uuid
from collections import defaultdict
from datetime import UTC, datetime

import uvicorn
from fastapi import FastAPI, Header, HTTPException, Request
from pydantic import BaseModel, model_validator

from capture.config import Config

logger = logging.getLogger("llmwiki-capture")

config = Config()
config.ensure_inbox()

app = FastAPI(title="llmwiki-capture", docs_url=None, redoc_url=None)

# --- Rate limiting (in-memory, resets on restart) ---

_rate_buckets: dict[str, list[float]] = defaultdict(list)


def _check_rate_limit(client_id: str) -> None:
    now = time.monotonic()
    window = 60.0
    bucket = _rate_buckets[client_id]
    _rate_buckets[client_id] = [t for t in bucket if now - t < window]
    if len(_rate_buckets[client_id]) >= config.rate_limit:
        raise HTTPException(429, "Rate limited. Try again later.")
    _rate_buckets[client_id].append(now)


# --- Models ---


class InboxRequest(BaseModel):
    url: str | None = None
    text: str | None = None
    title: str | None = None
    device: str | None = None

    @model_validator(mode="after")
    def require_url_or_text(self) -> InboxRequest:
        if not self.url and not self.text:
            raise ValueError("Either 'url' or 'text' is required.")
        return self


class InboxResponse(BaseModel):
    id: str
    file: str


class HealthResponse(BaseModel):
    status: str
    inbox_path: str
    inbox_count: int


# --- Helpers ---


def _sanitize_frontmatter(value: str) -> str:
    """Remove characters that could break YAML frontmatter."""
    cleaned = value.replace('"', "'").replace("\n", " ").replace("\r", "")
    return cleaned[:200].strip()


def _check_duplicate_url(url: str) -> bool:
    """Scan recent inbox files for a matching URL."""
    try:
        md_files = sorted(config.inbox_path.glob("*.md"), reverse=True)[:100]
    except OSError:
        return False
    for f in md_files:
        try:
            head = f.read_text(encoding="utf-8")[:500]
            if f'source: "{url}"' in head:
                return True
        except OSError:
            continue
    return False


def _write_inbox_file(req: InboxRequest) -> tuple[str, str]:
    """Write inbox file(s). Returns (file_id, relative_path).

    URL-only captures write a .url file (which llm-wiki explicitly handles
    by extracting and fetching the URL) plus a .md companion with metadata.
    Text captures write a .md file only.
    """
    now = datetime.now(UTC)
    file_id = f"{now.strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:8]}"

    title = _sanitize_frontmatter(req.title or req.url or "untitled")
    source = _sanitize_frontmatter(req.url or "manual")
    device = _sanitize_frontmatter(req.device or "unknown")
    captured = now.isoformat()

    # For URL-only captures, write a .url file so llm-wiki's inbox
    # processor recognizes it as a URL to fetch (not a note to store).
    if req.url and not req.text:
        url_filename = f"{file_id}.url"
        url_filepath = config.inbox_path / url_filename
        url_filepath.write_text(
            f"[InternetShortcut]\nURL={req.url}\n", encoding="utf-8"
        )

    # Always write a .md companion with full metadata.
    md_filename = f"{file_id}.md"
    md_filepath = config.inbox_path / md_filename

    lines = [
        "---",
        f'title: "{title}"',
        f'source: "{source}"',
        "type: inbox",
        f"captured: {captured}",
        f'device: "{device}"',
        "---",
    ]
    if req.text:
        lines.append("")
        lines.append(req.text)

    md_filepath.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return file_id, f"inbox/{md_filename}"


# --- Auth ---


def _verify_token(authorization: str | None) -> None:
    if not authorization:
        raise HTTPException(401, "Missing Authorization header.")
    parts = authorization.split(" ", 1)
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(401, "Invalid Authorization header format.")
    if not secrets.compare_digest(parts[1], config.token):
        raise HTTPException(401, "Invalid token.")


# --- Routes ---


@app.post("/inbox", response_model=InboxResponse, status_code=201)
async def post_inbox(
    body: InboxRequest,
    request: Request,
    authorization: str | None = Header(None),
) -> InboxResponse:
    _verify_token(authorization)
    _check_rate_limit(request.client.host if request.client else "unknown")

    if body.url and _check_duplicate_url(body.url):
        raise HTTPException(409, f"URL already in inbox: {body.url}")

    file_id, rel_path = _write_inbox_file(body)
    logger.info("Captured %s -> %s", file_id, rel_path)
    return InboxResponse(id=file_id, file=rel_path)


@app.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    try:
        count = len(list(config.inbox_path.glob("*.md")))
    except OSError:
        count = 0
    return HealthResponse(
        status="ok",
        inbox_path=str(config.inbox_path),
        inbox_count=count,
    )


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
    logger.info("Inbox path: %s", config.inbox_path)
    logger.info("Listening on %s:%d", config.host, config.port)
    uvicorn.run(
        app,
        host=config.host,
        port=config.port,
        log_level="info",
        h11_max_incomplete_event_size=1_048_576,  # 1MB max request size
    )


if __name__ == "__main__":
    main()
