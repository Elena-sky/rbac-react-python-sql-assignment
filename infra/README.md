# Ghost on Hetzner via Tailscale Tunnel

This folder contains a minimal infra-only setup for the assignment:
- one command deploy
- Ghost reachable publicly on HTTP
- SSH not exposed publicly, only through Tailscale

## Files

- `deploy.sh` - installs dependencies, configures tunnel/firewall, starts Ghost
- `docker-compose.yml` - Ghost service definition (SQLite storage under Ghost content volume)
- `.env.example` - required environment variable placeholders

## Quick start

1. Copy env template and set values:

```bash
cp infra/.env.example infra/.env
```

2. Edit `infra/.env`:
- `GHOST_URL` - public URL (domain or IP)
- `TAILSCALE_AUTHKEY` - Tailscale auth key

3. Run deploy as root:

```bash
sudo ./infra/deploy.sh
```

The script is safe to re-run for normal redeploys.

Supported target:
- Ubuntu or Debian based Hetzner VPS

## Database mode

This setup uses SQLite explicitly:
- `database__client=sqlite3`
- `database__connection__filename=/var/lib/ghost/content/data/ghost.db`

Reason: a minimal single-node deployment without external MySQL dependency.

## SSH access (Tailscale only)

Access model in this setup:
- SSH path is Tailscale tunnel only
- Public `22/tcp` is blocked by UFW
- `tailscale up --ssh` is enabled by deploy script

After deploy, use Tailscale to connect:

```bash
tailscale ssh root@<tailscale-hostname-or-ip>
```

or regular SSH over tailnet IP:

```bash
ssh root@100.x.y.z
```

## Ports policy

- Open publicly:
  - `80/tcp` (HTTP)
  - `443/tcp` (reserved for future TLS reverse proxy)
- Blocked publicly:
  - `22/tcp` (SSH)

## Architecture overview

- Visitor traffic: Internet -> VPS:80 -> Ghost container:2368
- Admin traffic: Engineer machine -> Tailscale mesh tunnel -> VPS SSH
- Security boundary: no public SSH ingress; operational access only through tailnet tunnel

Ghost remains publicly accessible over HTTP in this minimal setup, while SSH is limited to the tunnel path.
