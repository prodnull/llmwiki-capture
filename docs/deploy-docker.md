# Docker deployment

## Quick start

```bash
export CAPTURE_TOKEN="your-secret-token"
export WIKI_PATH="$HOME/wiki"
export UID=$(id -u)
export GID=$(id -g)

docker compose up -d
```

## What the compose file does

- Builds the image from the Dockerfile
- Mounts your wiki directory into the container at `/wiki`
- Runs as your host user (not root) to avoid file permission issues
- Restarts automatically unless you explicitly stop it

## Configuration

Pass settings via environment variables in `docker-compose.yml` or a `.env` file:

```bash
# .env
CAPTURE_TOKEN=your-secret-token
WIKI_PATH=/home/you/wiki
UID=1000
GID=1000
```

## Targeting a specific topic wiki

```bash
docker compose up -d -e CAPTURE_WIKI_NAME=cybersecurity
```

Or add it to `docker-compose.yml`:

```yaml
environment:
  - CAPTURE_TOKEN=${CAPTURE_TOKEN}
  - WIKI_PATH=/wiki
  - CAPTURE_WIKI_NAME=cybersecurity
```

## Raspberry Pi / ARM

The Dockerfile uses `python:3.13-slim` which supports `linux/arm64` and `linux/arm/v7`. No changes needed for Pi or ARM-based NAS devices.

## Synology / QNAP NAS

1. Copy the project to your NAS
2. SSH in and run `docker compose up -d`
3. Make sure the wiki directory path is correct for the NAS filesystem
4. The service will persist across NAS reboots (restart policy: `unless-stopped`)

## Logs

```bash
docker compose logs -f capture
```

## Updating

```bash
git pull
docker compose build
docker compose up -d
```
