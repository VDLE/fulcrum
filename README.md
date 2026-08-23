# Fulcrum

A web platform for running Human-Computer Interaction (HCI) studies end to end:
design a study, run participant sessions, capture mouse / keyboard / screen
telemetry, and review the results in one place. Originally built as a
university senior-project codebase and now in a containerized, minimum viable
state for broader use.

This repository ships two pieces:

- **Web app** (this repo's top level). A Dockerized stack with a Vue 3
  frontend, a Flask backend, MySQL, Redis + RQ for background analytics, and
  nginx as the entry point. Researchers use it from a browser.
- **Local tracking agent** (`local_backend/`). A PyQt6 desktop tool that the
  participant downloads from the web app and runs on their own machine to
  capture mouse, keyboard, screen, and heatmap data during a trial. See
  [local_backend/README.md](local_backend/README.md) for its install and
  per-platform notes.

A full developer reference for layout, runtime flow, data model, and the
contract between the two pieces lives in [ARCHITECTURE.md](ARCHITECTURE.md).

## Quick start (web app)

Requirements: Docker Engine + the `docker compose` plugin, or Docker Desktop
on Windows / macOS (with WSL2 enabled on Windows).

```bash
git clone https://github.com/VDLE/fulcrum/
cd fulcrum
cp .env.example .env
# Edit .env and fill in MYSQL_PASSWORD, SECRET_KEY, SECRET_PASSWORD_SALT,
# and SMTP credentials.
docker compose up --build
```

When the stack is healthy:

- Frontend: <http://localhost/>
- Backend health check: <http://localhost/api/ping>

To wipe the database and reseed from scratch:

```bash
docker compose down -v
docker compose up --build
```

## What it does

1. Researcher signs up through the web frontend. Account confirmation is
   sent via SMTP. `.env.example` documents working Gmail App-Password,
   Outlook, and SendGrid setups.
2. Researcher creates a study: name, description, design type (within
   or between subjects), tasks, factors, consent form (PDF), and optional
   pre/post-trial survey forms (JSON).
3. Participant joins a session. The web app generates the session URL
   and prompts them to download and run the local tracking agent.
4. Tracking agent runs locally. It exposes a small Flask server on
   `127.0.0.1:5001` that the browser talks to directly. During each trial it
   captures whichever measurements the study requested:
   - Mouse movement
   - Mouse clicks
   - Mouse scrolls
   - Keyboard inputs
   - Full-screen recording (MP4, optional)
   - Heat map (PNG composited over a screenshot)
5. Session ends, results upload. The agent zips the per-trial data, the
   browser POSTs it to the backend, and the backend extracts and indexes
   the files into MySQL plus the named `results_data` Docker volume.
6. Researcher reviews analytics in the web app: per-trial summaries,
   download of raw CSV / MP4 / PNG, heatmaps, and aggregate visualizations.
   Heavy aggregations run on the RQ worker.

## Limitations

### Local tracking agent: platform support

| Platform | Mouse + Keyboard | Heat Map | Screen Recording |
|---|---|---|---|
| Windows 10 / 11 | yes | yes | yes |
| macOS 12+ | yes (untested) | yes (untested) | yes (untested) |
| Linux + X11 / Xorg | yes | yes | yes |
| Linux + Wayland | **not supported** | **not supported** | **not supported** |

### Distribution model for the agent

The agent ships as Python source, not a precompiled binary. Participants
must have Python 3.10 to 3.12 installed (3.12 recommended; newer versions currently
lack prebuilt wheels for some pinned dependencies). 

## Known issues

- Multi-monitor setups unsupported: Screen recording
  and the heatmap screenshot grab monitor index 1 from
  [`mss`](https://pypi.org/project/mss/). On multi-display systems the
  researcher's primary monitor may be index 2 or higher, so the wrong
  display gets captured. Should become a per-study setting. Tracked as
  future work.
- Email-confirmation rollback when SMTP fails. Flask-Security inserts
  the user row before the confirmation email is sent. If SMTP fails after
  that, re-using the same email on a retry hits a uniqueness collision.
  Workaround: use a fresh email, or `docker compose down -v` to drop the
  database.

## Repository layout

```
.
|-- docker-compose.yml         orchestrates db + redis + backend + worker + frontend
|-- .env.example               template for required env vars
|-- frontend/                  Vue 3 + Vuetify SPA; nginx serves the build
|-- server_backend/            Flask backend + RQ analytics worker
|-- local_backend/             PyQt6 tracking agent (downloaded by participants)
|-- sql_database/              MySQL schema + reference-data seed scripts
`-- .github/workflows/         CI: Python black formatter on PRs
```

See [ARCHITECTURE.md](ARCHITECTURE.md) for the full breakdown.

## Configuration

All configuration lives in `.env` at the repo root. Key fields:

| Variable | Purpose |
|---|---|
| `MYSQL_PASSWORD` | Root password for the bundled MySQL container |
| `SECRET_KEY` | Flask session signing key (use 64 random chars) |
| `SECRET_PASSWORD_SALT` | Flask-Security password salt |
| `MAIL_SERVER` / `MAIL_PORT` / `MAIL_USERNAME` / `MAIL_PASSWORD` | SMTP relay for outbound mail |
| `EXPECTED_FRONTEND_DOMAIN_URL` | Public URL of the deployed frontend; used for CORS and confirmation redirects |

`.env.example` lists the full set with inline comments and provider-specific
SMTP examples.

## License

See [LICENSE](LICENSE).

