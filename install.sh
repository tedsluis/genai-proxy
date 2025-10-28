#!/usr/bin/env bash
set -euo pipefail

echo "genai-proxy installer"

if ! command -v sudo >/dev/null 2>&1; then
  echo "This script requires sudo privileges. Please install sudo or run as root." >&2
  exit 1
fi

if ! command -v podman >/dev/null 2>&1; then
  echo "podman not found. Please install Podman and try again." >&2
  exit 1
fi

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
REPO_DIR="$SCRIPT_DIR"

SERVICE_SRC="$REPO_DIR/genai-proxy.service"
MODELS_SRC="$REPO_DIR/models.yaml"
CONTAINERFILE="$REPO_DIR/Containerfile"

SERVICE_DEST="/etc/systemd/system/genai-proxy.service"
MODELS_DEST_DIR="/opt/genai-proxy"
MODELS_DEST="$MODELS_DEST_DIR/models.yaml"

# Validate sources
[[ -f "$SERVICE_SRC" ]] || { echo "Missing $SERVICE_SRC" >&2; exit 1; }
[[ -f "$MODELS_SRC" ]] || { echo "Missing $MODELS_SRC" >&2; exit 1; }
[[ -f "$CONTAINERFILE" ]] || { echo "Missing $CONTAINERFILE" >&2; exit 1; }

echo "==> Preparing directories"
sudo mkdir -p "$MODELS_DEST_DIR"

echo "==> Installing systemd service"
if [[ -f "$SERVICE_DEST" ]]; then
  echo "Service already exists at $SERVICE_DEST; not copying again."
else
  sudo install -m 0644 "$SERVICE_SRC" "$SERVICE_DEST"
  echo "Installed service to $SERVICE_DEST"
fi

echo "==> Installing models.yaml"
sudo install -m 0644 "$MODELS_SRC" "$MODELS_DEST"

echo "==> Building container image (root storage)"
sudo podman build -t genai-proxy:latest -f "$CONTAINERFILE" "$REPO_DIR"

echo "==> Reloading systemd, enabling and starting genai-proxy"
sudo systemctl daemon-reload
sudo systemctl enable genai-proxy
sudo systemctl restart genai-proxy || sudo systemctl start genai-proxy

echo "==> Done"
sudo systemctl --no-pager --full status genai-proxy || true
