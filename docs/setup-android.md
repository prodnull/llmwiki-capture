# Android Setup (HTTP Shortcuts)

Capture URLs from Android's share sheet using the [HTTP Shortcuts](https://play.google.com/store/apps/details?id=ch.rmy.android.http_shortcuts) app.

## Prerequisites

- llmwiki-capture running on your Mac/server
- Your capture service URL (e.g., `http://your-mac:7199`)
- Your bearer token (printed on first run)
- Both devices on the same Tailscale network (or using Cloudflare Tunnel)

## Install the app

Install **HTTP Shortcuts** from the Play Store. It's free, open source, and has no ads.

## Create the shortcut

1. Open HTTP Shortcuts
2. Tap **+** → **Regular Shortcut**
3. Configure:

### Basic settings

- **Name**: Wiki Inbox
- **Method**: POST
- **URL**: `http://YOUR-MAC:7199/inbox`

### Headers

Add two headers:

| Header | Value |
|--------|-------|
| `Authorization` | `Bearer YOUR_TOKEN_HERE` |
| `Content-Type` | `application/json` |

### Request body

- Select **Custom Body** (JSON)
- Body:
  ```json
  {"url": "{url}", "device": "android"}
  ```
  
  `{url}` is a built-in variable that HTTP Shortcuts populates from the share intent.

### Trigger

- Under **Trigger** settings, enable **Share action**
- Select content types: **Text** and **URLs**

### Response handling

- Under **Response**, set to **Show simple toast message** on success
- Message: `Sent to Wiki`

4. Tap **Save**

## Fallback for offline capture

HTTP Shortcuts doesn't have built-in fallback logic, but you can:

1. **Use "Delay execution"**: HTTP Shortcuts supports queuing requests and retrying later. Under advanced settings, enable **Retry on failure**.

2. **Manual fallback**: If the request fails, the app shows an error. Copy the URL to Google Keep or a text file, process later.

## Testing

1. Open Chrome or any app, find an article
2. Tap **Share**
3. Select **HTTP Shortcuts** → **Wiki Inbox**
4. You should see the "Sent to Wiki" toast
5. Verify: `ls ~/wiki/inbox/` on your server should show the new file

## Alternative: Tasker

If you already use Tasker, you can create a share intent profile:

1. **Profile**: Event → System → Intent Received (action: `android.intent.action.SEND`)
2. **Task**:
   - Variable Set: `%url` to `%CLIP` (or extract from intent data)
   - HTTP Request: POST to `http://YOUR-MAC:7199/inbox`
     - Headers: `Authorization: Bearer YOUR_TOKEN`
     - Body: `{"url": "%url", "device": "android"}`
   - Flash: "Sent to Wiki"

## Troubleshooting

| Problem | Fix |
|---------|-----|
| Connection refused | Check Tailscale is connected on your phone |
| 401 Unauthorized | Verify the bearer token matches |
| 409 Conflict | URL already captured (not an error) |
| App doesn't appear in share menu | Ensure "Share action" trigger is enabled in the shortcut settings |
| `{url}` not replaced | Make sure you're sharing a URL, not plain text. For text, use `{text}` instead |
