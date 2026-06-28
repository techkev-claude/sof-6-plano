#!/usr/bin/env bash
set -e

echo "=== Plano Installer ==="

if ! command -v docker &>/dev/null; then
  echo "Docker ist nicht installiert. Bitte installiere Docker zuerst."
  echo "Siehe: https://docs.docker.com/engine/install/"
  exit 1
fi

if ! docker compose version &>/dev/null; then
  echo "Docker Compose (v2) ist nicht verfügbar."
  exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(dirname "$SCRIPT_DIR")"

cd "$REPO_DIR"

if [ ! -f ".env" ]; then
  cp .env.example .env
  echo "==> .env aus .env.example erstellt. Bitte anpassen!"
  echo "    Öffne .env und ändere mindestens:"
  echo "    - SECRET_KEY (min. 32 Zeichen)"
  echo "    - DATA_PATH (Pfad für die Datenbank)"
  echo "    - UPLOADS_PATH (Pfad für Uploads)"
  echo ""
  read -rp "Nach Anpassung Enter drücken um fortzufahren..." _
fi

source .env
mkdir -p "${DATA_PATH:-./data}" "${UPLOADS_PATH:-./uploads}"

echo "==> Starte Docker Compose..."
docker compose up -d --build

echo ""
echo "=== Installation abgeschlossen ==="
echo "Plano läuft auf Port ${PORT:-8084}"
echo "Öffne http://$(hostname -I | awk '{print $1}'):${PORT:-8084} im Browser"
echo "Der Setup-Wizard startet automatisch beim ersten Aufruf."
