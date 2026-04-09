#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if [[ ! -f ".env" ]]; then
  echo "ERROR: infra/.env not found. Create it from infra/.env.example first."
  exit 1
fi

GHOST_URL=""
TAILSCALE_AUTHKEY=""

require_root() {
  if [[ "${EUID}" -ne 0 ]]; then
    echo "ERROR: run as root (sudo ./infra/deploy.sh)"
    exit 1
  fi
}

detect_pkg_manager() {
  if command -v apt-get >/dev/null 2>&1; then
    echo "apt"
    return
  fi
  if command -v dnf >/dev/null 2>&1; then
    echo "dnf"
    return
  fi
  echo "unsupported"
}

load_env_values() {
  while IFS= read -r line || [[ -n "$line" ]]; do
    line="${line%"${line##*[![:space:]]}"}"
    [[ -z "$line" ]] && continue
    [[ "${line:0:1}" == "#" ]] && continue
    if [[ "$line" == GHOST_URL=* ]]; then
      GHOST_URL="${line#GHOST_URL=}"
      continue
    fi
    if [[ "$line" == TAILSCALE_AUTHKEY=* ]]; then
      TAILSCALE_AUTHKEY="${line#TAILSCALE_AUTHKEY=}"
      continue
    fi
  done < ".env"
}

validate_env_values() {
  if [[ -z "${GHOST_URL}" ]]; then
    echo "ERROR: GHOST_URL is required in infra/.env"
    exit 1
  fi
  if [[ -z "${TAILSCALE_AUTHKEY}" ]]; then
    echo "ERROR: TAILSCALE_AUTHKEY is required in infra/.env"
    exit 1
  fi
}

install_base_packages() {
  local pm="$1"
  if [[ "$pm" == "apt" ]]; then
    apt-get update
    apt-get install -y ca-certificates curl gnupg lsb-release ufw
  elif [[ "$pm" == "dnf" ]]; then
    dnf install -y ca-certificates curl gnupg2 ufw
  fi
}

install_docker_apt() {
  if command -v docker >/dev/null 2>&1; then
    return
  fi
  local distro_id
  distro_id="$(. /etc/os-release && echo "${ID:-}")"
  if [[ "$distro_id" != "ubuntu" && "$distro_id" != "debian" ]]; then
    echo "ERROR: apt-based install supports Ubuntu/Debian only."
    exit 1
  fi
  install -m 0755 -d /etc/apt/keyrings
  if [[ ! -f /etc/apt/keyrings/docker.asc ]]; then
    curl -fsSL "https://download.docker.com/linux/${distro_id}/gpg" -o /etc/apt/keyrings/docker.asc
    chmod a+r /etc/apt/keyrings/docker.asc
  fi
  local codename
  codename="$(. /etc/os-release && echo "${VERSION_CODENAME:-}")"
  if [[ -z "$codename" ]]; then
    echo "ERROR: failed to detect distro codename for Docker repo."
    exit 1
  fi
  cat > /etc/apt/sources.list.d/docker.list <<EOF
deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/${distro_id} ${codename} stable
EOF
  apt-get update
  apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
}

install_docker_dnf() {
  if command -v docker >/dev/null 2>&1; then
    return
  fi
  dnf -y install dnf-plugins-core
  dnf config-manager --add-repo https://download.docker.com/linux/fedora/docker-ce.repo || true
  dnf install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
}

ensure_docker_compose_plugin() {
  if docker compose version >/dev/null 2>&1; then
    return
  fi
  local pm="$1"
  if [[ "$pm" == "apt" ]]; then
    apt-get install -y docker-compose-plugin
  elif [[ "$pm" == "dnf" ]]; then
    dnf install -y docker-compose-plugin
  fi
}

install_tailscale_apt() {
  if command -v tailscale >/dev/null 2>&1; then
    return
  fi
  curl -fsSL https://tailscale.com/install.sh | sh
}

install_tailscale_dnf() {
  if command -v tailscale >/dev/null 2>&1; then
    return
  fi
  curl -fsSL https://tailscale.com/install.sh | sh
}

start_services() {
  systemctl enable --now docker
  systemctl enable --now tailscaled
}

configure_tailscale() {
  if tailscale ip -4 >/dev/null 2>&1; then
    return
  fi
  tailscale up --authkey="${TAILSCALE_AUTHKEY}" --ssh
}

configure_firewall() {
  ufw --force disable >/dev/null 2>&1 || true
  ufw default deny incoming
  ufw default allow outgoing
  ufw allow 80/tcp
  ufw allow 443/tcp
  ufw delete allow 22/tcp >/dev/null 2>&1 || true
  ufw delete allow OpenSSH >/dev/null 2>&1 || true
  ufw deny 22/tcp
  ufw --force enable
}

deploy_ghost() {
  docker compose --env-file .env -f docker-compose.yml up -d
}

main() {
  require_root

  local pm
  pm="$(detect_pkg_manager)"
  if [[ "$pm" == "unsupported" ]]; then
    echo "ERROR: unsupported package manager. Expected apt-get or dnf."
    exit 1
  fi

  load_env_values
  validate_env_values

  install_base_packages "$pm"

  if [[ "$pm" == "apt" ]]; then
    install_docker_apt
    install_tailscale_apt
  else
    install_docker_dnf
    install_tailscale_dnf
  fi

  ensure_docker_compose_plugin "$pm"
  start_services
  configure_tailscale
  configure_firewall
  deploy_ghost

  local tail_ip
  tail_ip="$(tailscale ip -4 2>/dev/null | head -n 1 || true)"
  echo "Done."
  echo "Ghost should be available at: ${GHOST_URL}"
  if [[ -n "${tail_ip}" ]]; then
    echo "Tailnet IPv4: ${tail_ip}"
  fi
  echo "SSH is blocked publicly (22/tcp) and available via Tailscale tunnel."
}

main "$@"
