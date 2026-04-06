# Networking

Your phone needs to reach the capture service. This page covers both recommended options.

## Tailscale (recommended)

[Tailscale](https://tailscale.com/) creates a private network (tailnet) between your devices using WireGuard. Free for personal use (up to 100 devices).

### Setup

1. Install Tailscale on your Mac/server and phone
2. Sign in on both devices with the same account
3. The capture service is reachable at `http://<machine-name>:7199`

Find your machine's Tailscale name:

```bash
tailscale status
```

### iOS considerations

- Tailscale runs as a VPN profile on iOS
- Enable "Always On VPN" in Tailscale settings for reliability
- Some corporate/hotel networks block VPN — the capture shortcut will fail on those networks (the Apple Notes fallback handles this)

### Android considerations

- Same VPN profile approach as iOS
- Enable "Always-on VPN" in Android Settings > Network > VPN > Tailscale

## Cloudflare Tunnel (alternative)

[Cloudflare Tunnel](https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/) exposes a local service via a public HTTPS URL. No VPN needed on the phone — it's a regular HTTPS request.

### Requirements

- A domain managed by Cloudflare (free plan works)
- `cloudflared` CLI installed on your server

### Setup

```bash
# Install
brew install cloudflared   # macOS
# or: apt install cloudflared  # Debian/Ubuntu

# Create tunnel
cloudflared tunnel login
cloudflared tunnel create wiki-inbox

# Route DNS
cloudflared tunnel route dns wiki-inbox inbox.yourdomain.com

# Run (foreground)
cloudflared tunnel run --url http://localhost:7199 wiki-inbox
```

For persistent operation, run `cloudflared` as a service:

```bash
cloudflared service install
```

### Security with Cloudflare Tunnel

Cloudflare Tunnel exposes your endpoint to the internet. Add a Cloudflare Access policy to restrict access:

1. Go to Cloudflare Zero Trust dashboard
2. Create an Access Application for `inbox.yourdomain.com`
3. Add a policy: allow only your email address
4. On your phone, you'll authenticate once via browser, then the shortcut works

This gives you the bearer token (application-level auth) + Cloudflare Access (network-level auth).

## Comparison

| | Tailscale | Cloudflare Tunnel |
|---|-----------|-------------------|
| Cost | Free | Free (requires domain) |
| Phone app needed | Yes (Tailscale) | No |
| Works on hostile networks | No (VPN may be blocked) | Yes (regular HTTPS) |
| Setup complexity | Low | Medium |
| Auth layers | Tailscale ACL + bearer token | Cloudflare Access + bearer token |
| Always reachable | If VPN is connected | Yes |
