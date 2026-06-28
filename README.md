# Plano – Urlaubsplaner

Selfhosted, produktionsreifer Urlaubsplaner mit KI-Assistenz, Karten, Budget-Tracking, Packlisten, Ticket-Verwaltung und Reise-Journal.

## Schnellstart (Portainer)

1. `git clone <repo> && cd plano`
2. `cp .env.example .env && nano .env` (PORT + Pfade anpassen)
3. Portainer → Stacks → Add Stack → Repository URL eingeben
4. Env-Variablen aus `.env` übertragen → Deploy
5. `http://<server>:<PORT>` → Setup-Wizard startet automatisch

## Schnellstart (Docker Compose direkt)

```bash
git clone <repo> && cd plano
cp .env.example .env && nano .env
docker compose up -d
```

## Linux Online-Installer

```bash
git clone <repo> && cd plano && bash scripts/install.sh
```

## Konfiguration

Alle API-Keys und SMTP-Config: **Admin-UI → Konfiguration** nach dem Setup-Wizard.

### Wichtige Env-Variablen (.env)

| Variable | Beschreibung |
|---|---|
| `PORT` | Host-Port (Standard: 8084) |
| `SECRET_KEY` | Flask Session-Secret (min. 32 Zeichen) |
| `DATA_PATH` | Host-Pfad für SQLite-DB |
| `UPLOADS_PATH` | Host-Pfad für Ticket/Foto-Uploads |
| `DB_PATH` | Container-interner DB-Pfad |

## Features

- **Visueller Zeitstrahl-Planer** mit Drag & Drop, Snap-Raster, Undo
- **KI-Assistent** (Anthropic Claude / OpenAI) – Vorschläge, Tagesplanung, Import
- **Karten** (Leaflet + OpenStreetMap), Offline-Kacheln-Caching
- **Budget-Tracking** mit Währungsumrechnung und Cost-Split
- **Ticket-Vault** mit Fernet-Verschlüsselung und KI-OCR
- **Packlisten** mit Templates und KI-Generierung
- **Versionierung** mit Diff-Patches und Wiederherstellung
- **PWA** – installierbar, Service Worker, Background-Sync
- **Notifications** – Web-Push und E-Mail via APScheduler
- **Dark Mode** – vollständig

## Entwicklung

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
flask run --debug
```

Tests:
```bash
pytest tests/ -v
```

Wien Beispiel-Trip erstellen:
```bash
python scripts/seed_wien_example.py
```

## Architektur

- **Backend**: Python 3.12, Flask 3, SQLAlchemy 2 + SQLite, Flask-Migrate
- **Frontend**: Jinja2 + HTMX + Alpine.js + Tailwind CSS (CDN)
- **KI**: Anthropic SDK (Claude) / OpenAI SDK, SSE-Streaming
- **Karten**: Leaflet.js + OpenStreetMap
- **Deployment**: Docker (multi-stage, non-root) + docker-compose
