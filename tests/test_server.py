"""Tests for llmwiki-capture server."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def _setup_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Configure a temporary wiki inbox for each test."""
    inbox = tmp_path / "wiki" / "inbox"
    inbox.mkdir(parents=True)
    monkeypatch.setenv("WIKI_PATH", str(tmp_path / "wiki"))
    monkeypatch.setenv("CAPTURE_TOKEN", "test-token-abc123")
    monkeypatch.setenv("CAPTURE_PORT", "3999")

    # Force re-import to pick up new env vars
    import capture.config
    import capture.server

    new_config = capture.config.Config()
    new_config.ensure_inbox()
    capture.server.config = new_config
    capture.server._rate_buckets.clear()


@pytest.fixture
def client() -> TestClient:
    from capture.server import app

    return TestClient(app)


AUTH = {"Authorization": "Bearer test-token-abc123"}


class TestPostInbox:
    def test_capture_url(self, client: TestClient, tmp_path: Path) -> None:
        resp = client.post(
            "/inbox",
            json={"url": "https://example.com/article"},
            headers=AUTH,
        )
        assert resp.status_code == 201
        data = resp.json()
        assert "id" in data
        assert data["file"].startswith("inbox/")
        assert data["file"].endswith(".md")

        inbox = tmp_path / "wiki" / "inbox"

        # Verify .md file was written
        md_files = list(inbox.glob("*.md"))
        assert len(md_files) == 1
        content = md_files[0].read_text()
        assert 'source: "https://example.com/article"' in content
        assert "type: inbox" in content

        # Verify .url file was also written (for llm-wiki compatibility)
        url_files = list(inbox.glob("*.url"))
        assert len(url_files) == 1
        url_content = url_files[0].read_text()
        assert "[InternetShortcut]" in url_content
        assert "URL=https://example.com/article" in url_content

    def test_capture_text(self, client: TestClient, tmp_path: Path) -> None:
        resp = client.post(
            "/inbox",
            json={"text": "A note about something", "title": "My note"},
            headers=AUTH,
        )
        assert resp.status_code == 201

        inbox = tmp_path / "wiki" / "inbox"
        md_files = list(inbox.glob("*.md"))
        content = md_files[0].read_text()
        assert 'title: "My note"' in content
        assert "A note about something" in content

        # Text captures should NOT create .url files
        url_files = list(inbox.glob("*.url"))
        assert len(url_files) == 0

    def test_capture_with_device(self, client: TestClient, tmp_path: Path) -> None:
        resp = client.post(
            "/inbox",
            json={"url": "https://example.com", "device": "ios"},
            headers=AUTH,
        )
        assert resp.status_code == 201
        inbox = tmp_path / "wiki" / "inbox"
        content = list(inbox.glob("*.md"))[0].read_text()
        assert 'device: "ios"' in content

    def test_empty_body_rejected(self, client: TestClient) -> None:
        resp = client.post("/inbox", json={}, headers=AUTH)
        assert resp.status_code == 422

    def test_no_url_or_text_rejected(self, client: TestClient) -> None:
        resp = client.post("/inbox", json={"title": "just a title"}, headers=AUTH)
        assert resp.status_code == 422


class TestAuth:
    def test_missing_auth(self, client: TestClient) -> None:
        resp = client.post("/inbox", json={"url": "https://example.com"})
        assert resp.status_code == 401

    def test_wrong_token(self, client: TestClient) -> None:
        resp = client.post(
            "/inbox",
            json={"url": "https://example.com"},
            headers={"Authorization": "Bearer wrong-token"},
        )
        assert resp.status_code == 401

    def test_malformed_auth(self, client: TestClient) -> None:
        resp = client.post(
            "/inbox",
            json={"url": "https://example.com"},
            headers={"Authorization": "NotBearer token"},
        )
        assert resp.status_code == 401


class TestDuplicateDetection:
    def test_duplicate_url_rejected(self, client: TestClient) -> None:
        url = "https://example.com/dupe-test"
        resp1 = client.post("/inbox", json={"url": url}, headers=AUTH)
        assert resp1.status_code == 201

        resp2 = client.post("/inbox", json={"url": url}, headers=AUTH)
        assert resp2.status_code == 409

    def test_different_urls_accepted(self, client: TestClient) -> None:
        resp1 = client.post(
            "/inbox", json={"url": "https://example.com/a"}, headers=AUTH
        )
        resp2 = client.post(
            "/inbox", json={"url": "https://example.com/b"}, headers=AUTH
        )
        assert resp1.status_code == 201
        assert resp2.status_code == 201


class TestHealth:
    def test_health_ok(self, client: TestClient) -> None:
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert isinstance(data["inbox_count"], int)

    def test_health_counts_files(self, client: TestClient) -> None:
        # Add some files first
        client.post("/inbox", json={"url": "https://example.com/1"}, headers=AUTH)
        client.post("/inbox", json={"url": "https://example.com/2"}, headers=AUTH)
        resp = client.get("/health")
        assert resp.json()["inbox_count"] == 2


class TestSanitization:
    def test_title_with_quotes(self, client: TestClient, tmp_path: Path) -> None:
        resp = client.post(
            "/inbox",
            json={"url": "https://example.com", "title": 'He said "hello"'},
            headers=AUTH,
        )
        assert resp.status_code == 201
        inbox = tmp_path / "wiki" / "inbox"
        content = list(inbox.glob("*.md"))[0].read_text()
        # Double quotes replaced with single
        assert "He said 'hello'" in content

    def test_title_with_newlines(self, client: TestClient, tmp_path: Path) -> None:
        resp = client.post(
            "/inbox",
            json={"url": "https://example.com", "title": "line1\nline2\rline3"},
            headers=AUTH,
        )
        assert resp.status_code == 201
        inbox = tmp_path / "wiki" / "inbox"
        content = list(inbox.glob("*.md"))[0].read_text()
        assert "\nline2" not in content  # newlines stripped from frontmatter

    def test_path_traversal_in_title(self, client: TestClient, tmp_path: Path) -> None:
        resp = client.post(
            "/inbox",
            json={
                "url": "https://example.com",
                "title": "../../etc/passwd",
            },
            headers=AUTH,
        )
        assert resp.status_code == 201
        # File should be in inbox, not traversed
        inbox = tmp_path / "wiki" / "inbox"
        files = list(inbox.glob("*.md"))
        assert len(files) == 1
        assert files[0].parent == inbox


class TestRateLimit:
    def test_rate_limit_enforced(
        self, client: TestClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        import capture.server

        capture.server.config.rate_limit = 3

        for i in range(3):
            resp = client.post(
                "/inbox",
                json={"url": f"https://example.com/{i}"},
                headers=AUTH,
            )
            assert resp.status_code == 201

        resp = client.post(
            "/inbox",
            json={"url": "https://example.com/overflow"},
            headers=AUTH,
        )
        assert resp.status_code == 429
