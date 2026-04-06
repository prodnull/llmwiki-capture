# Linux deployment (systemd)

Run llmwiki-capture as a user service that starts automatically on boot.

## Setup

1. Install the service:

```bash
cd /path/to/llmwiki-capture
python3 -m venv .venv && source .venv/bin/activate
pip install .
```

2. Create the systemd unit at `~/.config/systemd/user/llmwiki-capture.service`:

```ini
[Unit]
Description=llmwiki-capture
After=network.target

[Service]
ExecStart=/path/to/llmwiki-capture/.venv/bin/llmwiki-capture
WorkingDirectory=/path/to/llmwiki-capture
Restart=always
RestartSec=5
Environment=CAPTURE_TOKEN=your-secret-token
Environment=WIKI_PATH=/home/you/wiki

[Install]
WantedBy=default.target
```

Replace paths and token with your actual values.

3. Enable and start:

```bash
systemctl --user daemon-reload
systemctl --user enable --now llmwiki-capture
```

## Managing the service

```bash
# Status
systemctl --user status llmwiki-capture

# Logs
journalctl --user -u llmwiki-capture -f

# Restart
systemctl --user restart llmwiki-capture

# Stop
systemctl --user stop llmwiki-capture
```

## Raspberry Pi notes

- Works on Pi 3B+ and newer with 64-bit OS
- Use the same systemd setup above
- For Pi Zero / 32-bit, Python 3.11+ may need to be compiled from source or installed via `deadsnakes` PPA
- Consider using [Docker deployment](deploy-docker.md) on Pi for simpler dependency management

## Lingering (run without login)

By default, user services only run while you're logged in. To keep it running after logout:

```bash
sudo loginctl enable-linger $USER
```
