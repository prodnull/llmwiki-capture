# macOS deployment (launchd)

Run llmwiki-capture as a background service that starts automatically on login.

## Setup

1. Install the service:

```bash
cd /path/to/llmwiki-capture
python -m venv .venv && source .venv/bin/activate
pip install .
```

2. Create the launchd plist at `~/Library/LaunchAgents/com.llmwiki.capture.plist`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.llmwiki.capture</string>
    <key>ProgramArguments</key>
    <array>
        <string>/path/to/llmwiki-capture/.venv/bin/llmwiki-capture</string>
    </array>
    <key>WorkingDirectory</key>
    <string>/path/to/llmwiki-capture</string>
    <key>EnvironmentVariables</key>
    <dict>
        <key>CAPTURE_TOKEN</key>
        <string>your-secret-token</string>
        <key>WIKI_PATH</key>
        <string>/Users/you/wiki</string>
    </dict>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/tmp/llmwiki-capture.log</string>
    <key>StandardErrorPath</key>
    <string>/tmp/llmwiki-capture.log</string>
</dict>
</plist>
```

Replace `/path/to/llmwiki-capture` and `/Users/you/wiki` with your actual paths.

3. Load the service:

```bash
launchctl load ~/Library/LaunchAgents/com.llmwiki.capture.plist
```

## Managing the service

```bash
# Check status
launchctl list | grep llmwiki

# Stop
launchctl unload ~/Library/LaunchAgents/com.llmwiki.capture.plist

# Start
launchctl load ~/Library/LaunchAgents/com.llmwiki.capture.plist

# View logs
tail -f /tmp/llmwiki-capture.log
```

## Notes

- The service starts automatically on login and restarts if it crashes (`KeepAlive: true`)
- Logs go to `/tmp/llmwiki-capture.log` — adjust if you want them elsewhere
- If you use `config.yml` instead of env vars, make sure `WorkingDirectory` points to the directory containing it
