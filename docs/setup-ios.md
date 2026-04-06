# iOS Shortcut Setup

Create a share sheet shortcut that sends URLs to your llmwiki-capture service, with a fallback to Apple Notes if the service is unreachable.

## Prerequisites

- llmwiki-capture running on your Mac/server
- Your capture service URL (e.g., `http://your-mac:7199`)
- Your bearer token (printed on first run)
- Both devices on the same Tailscale network (or using Cloudflare Tunnel)

## Create the shortcut

1. Open the **Shortcuts** app on your iPhone
2. Tap **+** to create a new shortcut
3. Tap the name at the top, rename to **Wiki Inbox**
4. Tap the **ⓘ** (info) button → enable **Show in Share Sheet**
5. Under "Receives", select **URLs**, **Text**, and **Safari web pages**

## Add the actions

Build this flow in order:

### Step 1: Receive the shared input

- **Receive** input from Share Sheet
- **Set Variable** — name it `SharedURL`, set to **Shortcut Input**

### Step 2: Try sending to capture service

- **Get Contents of URL**
  - URL: `http://YOUR-MAC:7199/inbox`
  - Method: **POST**
  - Headers:
    - `Authorization`: `Bearer YOUR_TOKEN_HERE`
    - `Content-Type`: `application/json`
  - Request Body (JSON):
    - `url`: `SharedURL` (variable)
    - `device`: `ios`

### Step 3: Add fallback for when service is down

- Wrap Step 2 in an **If** block:
  - After "Get Contents of URL", add **If** → **has any value**
    - (This path = success, do nothing)
  - **Otherwise** (the request failed):
    - **Add to Note** — choose or create a note called "Wiki Inbox"
      - Content: `SharedURL` (variable)
    - **Show Notification**: "Saved to Wiki Inbox note (service offline)"

### Step 4: Success feedback

- After the If block, on the success path:
  - **Show Notification**: "Sent to Wiki" (set to auto-dismiss)

## Simplified version (no fallback)

If you don't want the fallback and accept losing URLs when the service is down:

1. **Receive** Shortcut Input
2. **Get Contents of URL** (POST to `/inbox` with JSON body as above)
3. **Show Notification**: "Sent to Wiki"

That's it — three actions.

## Testing

1. Open Safari, navigate to any article
2. Tap the **Share** button
3. Tap **Wiki Inbox** in the share sheet
4. You should see the "Sent to Wiki" notification
5. Verify: `ls ~/wiki/inbox/` on your Mac should show the new file

## Processing the Apple Notes fallback

If URLs accumulated in the "Wiki Inbox" note while the service was down:

1. Open the note, copy the URLs
2. In Claude Code: paste them and ask to ingest, or manually:
   ```
   /wiki:ingest https://first-url
   /wiki:ingest https://second-url
   ```

Or write a quick script to POST each line from the note to the capture service once it's back up.

## Troubleshooting

| Problem | Fix |
|---------|-----|
| "Could not connect to the server" | Check Tailscale is connected on both devices |
| 401 Unauthorized | Verify the bearer token matches your config |
| 409 Conflict | URL was already captured (not an error) |
| Shortcut doesn't appear in share sheet | Check "Show in Share Sheet" is enabled in shortcut settings |
