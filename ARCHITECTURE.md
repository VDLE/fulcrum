# Fulcrum Architecture

This document is the formal reference for the codebase. It targets two
audiences: developers onboarding to the project, and AI coding assistants
that need a structured understanding of the system to make accurate changes.
Sections are intentionally compact and indexed so they can be searched and
quoted without context loss.

Conventions:

- **Source paths** use repo-relative form (e.g. `server_backend/app/routes/sessions.py`).
- **Routes** are listed as `METHOD /path` with a one-line purpose.
- **DB tables** use the schema names from `sql_database/create_tables.sql`.
- **Volumes / images** match `docker-compose.yml`.

---

## 1. System overview

Fulcrum is split across two deployment surfaces:

1. **Web app** (server-hosted, Dockerized): a SPA + Flask backend + MySQL +
   Redis + a background worker. Researchers access it through a browser.
2. **Local tracking agent** (participant-hosted, native Python): a PyQt6
   desktop app the participant downloads from the web app and runs on their
   own machine. The agent captures input + screen telemetry and exposes a
   tiny HTTP server on `127.0.0.1:5001` that the participant's browser
   talks to directly.

There is no direct network link between the agent and the backend. All
agent->backend traffic is intermediated by the browser: the browser pulls
the session ZIP from `127.0.0.1:5001`, then POSTs it to the backend through
nginx.

```
+----------------+        +-------------------------+        +---------------+
|  Web frontend  | <----> |   nginx (port 80)       | <----> |  Flask        |
|  (researcher's |        |   - SPA static          |        |  backend      |
|   browser)     |        |   - /api -> backend     |        |  (gunicorn)   |
+--------+-------+        +-------------------------+        +---+---+-------+
         |                                                       |   |
         |   loopback HTTP                                       |   |
         |   (browser <-> local agent on same machine)           |   |
         v                                                       v   v
+-----------------------------+                              +-----+ +--------+
|  Local tracking agent       |                              | RQ  | | MySQL  |
|  PyQt6 + embedded Flask     |                              | wkr | | 8.0    |
|  127.0.0.1:5001             |                              +-----+ +--------+
+-----------------------------+                                 |
                                                                v
                                                            +--------+
                                                            | Redis  |
                                                            | 7      |
                                                            +--------+
```

---

## 2. Repository layout

```
.
|-- docker-compose.yml                     orchestrates the 5 services
|-- .env.example                           template for required env vars
|-- ARCHITECTURE.md                        this file
|-- README.md                              public-facing overview
|-- LICENSE                                MIT (see LICENSE file)
|
|-- frontend/                              Vue 3 SPA, served via nginx in prod
|   |-- Dockerfile                         multi-stage: node build + nginx serve
|   |-- nginx.conf                         /api proxy + static SPA fallback
|   |-- vite.config.js                     env-driven dev proxy
|   `-- src/
|       |-- api/                           axios wrappers for backend routes
|       |-- components/                    reusable widgets (incl. TrackingPhase)
|       |-- views/                         top-level routed pages
|       |-- router/                        vue-router config
|       |-- stores/                        Pinia stores
|       |-- layouts/                       layout components
|       `-- main.js / App.vue              entrypoint
|
|-- server_backend/                        Flask backend + RQ worker
|   |-- Dockerfile                         python:3.11-slim + libmysqlclient
|   |-- requirements.txt                   pinned runtime deps
|   |-- wsgi.py                            gunicorn entrypoint -> app:create_app()
|   |-- app.py                             dev entrypoint (python app.py)
|   |-- worker.py                          RQ worker entrypoint (analytics queue)
|   |-- app/
|   |   |-- __init__.py                    create_app(); MySQL, SQLAlchemy, Mail,
|   |   |                                  Flask-Security init; blueprint wiring
|   |   |-- routes/                        Flask blueprints (one per concern)
|   |   `-- utility/                       shared helpers + analytics processors
|   |-- security/                          Flask-Security User / Role models
|   `-- tests/                             pytest suite
|
|-- local_backend/                         PyQt6 tracking agent
|   |-- README.md                          install + per-platform notes
|   |-- requirements.txt                   minimal runtime deps for the agent
|   |-- driver.py                          Qt UI + embedded Flask
|   |-- tracking/
|   |   |-- tracking.py                    per-trial orchestrator (conduct_trial)
|   |   `-- utility/
|   |       |-- capabilities.py            platform detection + measurement gating
|   |       |-- file_management.py         filesystem paths + per-trial CSV writes
|   |       |-- measure.py                 pynput listeners for mouse + keyboard
|   |       |-- screenrecording.py         continuous-capture .mp4 writer
|   |       |-- screencap.py               single-frame screenshot helper
|   |       `-- heatmap.py                 mouse-movement heat-map overlay
|   `-- tests/                             pytest suite
|
|-- sql_database/
|   |-- create_tables.sql                  full schema; runs on first DB init
|   |-- seed_reference_data.sql            lookup-table inserts (idempotent)
|   `-- drop_tables.sql                    teardown helper
|
`-- .github/workflows/
    `-- apply_python_formatter.yml         CI: run black on PRs
```

---

## 3. Services (docker-compose.yml)

| Service | Image / Build | Ports (host:container) | Volumes | Depends on |
|---|---|---|---|---|
| `db` | `mysql:8.0` | not exposed externally | `mysql_data`; mounts `create_tables.sql` and `seed_reference_data.sql` into `/docker-entrypoint-initdb.d` | - |
| `redis` | `redis:7-alpine` | not exposed | `redis_data` | - |
| `backend` | `./server_backend` (gunicorn) | `5004:5004` | `results_data:/app/data/participants_results`, bind mount `./local_backend:/app/local_backend:ro` | `db` healthy, `redis` started |
| `worker` | `./server_backend` (python worker.py) | none | `results_data:/app/data/participants_results` | `db` healthy, `redis` started |
| `frontend` | `./frontend` (nginx) | `80:80` | none | `backend` |

Named volumes: `mysql_data`, `redis_data`, `results_data`.

Init-script behavior: MySQL only runs the SQL files in
`/docker-entrypoint-initdb.d/` when the data directory is empty (first
boot). To re-seed after schema changes you must `docker compose down -v` to
drop `mysql_data`.

---

## 4. Backend (Flask)

### 4.1 Entry points

| File | Role |
|---|---|
| `server_backend/wsgi.py` | Gunicorn import target (`wsgi:app`). Re-exports `create_app()`. |
| `server_backend/app.py` | Dev entrypoint. `python app.py` runs the Werkzeug dev server, honoring `FLASK_PORT` and `FLASK_DEBUG`. |
| `server_backend/worker.py` | RQ worker. Connects to Redis via env vars (`REDIS_HOST`, `REDIS_PORT`, `REDIS_DB`) and listens on the `analytics` queue. |

`create_app()` lives in `server_backend/app/__init__.py`. It:

1. Loads `.env` via `python-dotenv` (search path includes the container's
   working dir, so the `.env` mounted by compose is picked up).
2. Initializes `Flask-MySQLdb` (`mysql` global), `Flask-SQLAlchemy` (`db`
   global, used by Flask-Security only), `Flask-Mailman`, `Flask-WTF`
   CSRF, and `Flask-Security-Too`.
3. Registers all blueprints under `app/routes/`.
4. Configures CORS, session cookies, mail timeouts, and the URL prefix
   `/api/accounts` for Flask-Security.

### 4.2 Blueprints

All blueprints are wired in `server_backend/app/__init__.py`. Each is under
`server_backend/app/routes/`.

| File | URL prefix | Purpose |
|---|---|---|
| `general.py` | `/api` | Health check (`/api/ping`), DB connectivity probe. |
| `user_handling.py` | `/api` | Profile updates, password / email changes (uses Flask-Security). |
| `studies.py` | `/api` | CRUD on studies, tasks, factors, consent + survey forms. |
| `sessions.py` | `/api` | Participant-session creation, demographics, the large `/api/save_participant_session` ZIP upload + DB indexing. |
| `trials.py` | `/api` | Trial-level reads + updates (start/end timestamps, per-trial JSON). |
| `analytics.py` | `/api` | Per-study and per-trial analytics, plus the RQ-backed async-processing endpoints. |
| `analytics_surveys.py` | `/api` | Survey-form-specific aggregations. |
| `downloads.py` | `/api` | `POST /api/download_tracking_tool` zips `local_backend/` on demand. |
| `testing_reset_db.py` | `/api` | Test-fixture endpoints (rarely used outside CI). |

Flask-Security exposes its own routes under `/api/accounts/*`
(`SECURITY_URL_PREFIX="/api/accounts"`): register, login, logout, confirm,
reset-password, change-password.

### 4.3 Database access

Two access patterns coexist:

- **Raw MySQLdb cursors** (the majority of routes). Acquired via
  `app.utility.db_connection.get_db_connection()`, which returns the
  Flask-MySQLdb connection. Used for everything domain-specific.
- **Flask-SQLAlchemy ORM** (Flask-Security only). Models in
  `server_backend/security/models.py`. The `User` and `Role` models are
  backed by the same MySQL database under `users` / `role_type` /
  `users_roles` tables.

Long term consolidation onto one of these is a known refactor, not
currently in scope.

### 4.4 Background analytics (RQ)

The `worker` service listens on the `analytics` queue. Large aggregations
(mouse-movement processing for thousands of points, heatmap recomputation,
etc.) are dispatched there from `analytics.py` to keep request workers
responsive. Module of record: `server_backend/app/utility/analytics/data_processor.py`.

### 4.5 Configuration via env

All configuration is supplied via env vars; defaults are documented in
`.env.example`. Important keys:

| Variable | Default | Effect |
|---|---|---|
| `MYSQL_HOST` / `MYSQL_USER` / `MYSQL_PASSWORD` / `MYSQL_DB` | from compose | DB connection |
| `REDIS_HOST` / `REDIS_PORT` / `REDIS_DB` | from compose | RQ queue + cache |
| `SECRET_KEY` | none (required) | Flask session signing |
| `SECRET_PASSWORD_SALT` | none (required) | Flask-Security password hash salt |
| `MAIL_SERVER` / `MAIL_PORT` / `MAIL_USE_TLS` / `MAIL_USE_SSL` / `MAIL_USERNAME` / `MAIL_PASSWORD` / `MAIL_DEFAULT_SENDER` / `MAIL_TIMEOUT` | port=465, SSL=on, timeout=10s | SMTP relay used by Flask-Security email confirmation, password reset, etc. |
| `RESULTS_BASE_DIR_PATH` | `/app/data/participants_results` | Where extracted session results land. Backed by the `results_data` volume. |
| `TRACKING_TOOL_DIR_PATH` | `/app/data/tracking_tool_downloads` | Reserved for prebuilt agent ZIPs; current implementation zips on demand from `/app/local_backend` instead. |
| `EXPECTED_FRONTEND_DOMAIN_URL` | `http://localhost` | CORS allowlist + Flask-Security confirmation redirect base URL. |
| `FLASK_PORT` / `FLASK_DEBUG` | 5004 / false | Dev-server only (gunicorn ignores). |

---

## 5. Frontend (Vue 3)

### 5.1 Build pipeline

- `frontend/Dockerfile` runs `npm ci && npm run build` in a node:20-alpine
  builder stage, then copies `/app/dist/` into an `nginx:alpine` runtime
  stage.
- `frontend/nginx.conf` serves the SPA from `/` and proxies `/api/` to
  `http://backend:5004/api/` (via Docker's internal DNS). It also bumps
  `client_max_body_size` to 2 GB so session-result uploads pass through.
- `frontend/vite.config.js` reads `frontend/src/config.json` if present
  (gitignored, used in local dev) and falls back to `VITE_BACKEND_URL` /
  `VITE_BACKEND_PORT` env vars otherwise. In production the build embeds
  no backend URL because nginx handles routing.

### 5.2 Notable components and pages

| File | Role |
|---|---|
| `frontend/src/App.vue`, `frontend/src/main.js` | Entrypoint. |
| `frontend/src/router/index.js` | Vue Router config. |
| `frontend/src/views/UserRegister.vue` | Sign-up; surfaces Flask-Security `field_errors`. |
| `frontend/src/components/TrackingPhase.vue` | Owns the entire session loop: pings the local agent, posts study config to `/run_study`, polls `/session_results_status` after the trial ends, then POSTs the ZIP to the backend. |
| `frontend/src/components/TrackingSetup.vue` | Drives the "Download Tracking Tool" handoff. |
| `frontend/src/api/analyticsApi.js` | Axios wrapper for analytics endpoints; defaults to relative `/api` and respects `VITE_DIRECT_API_URL`. |

---

## 6. Local tracking agent

### 6.1 Process model

`local_backend/driver.py` is the only entry point. Layout when running:

- Main thread: PyQt6 event loop. Runs `GlobalToolbar` (the floating
  toolbar widget) and modal dialogs.
- Daemon thread (`start_flask`): runs Flask on `127.0.0.1:5001`. All HTTP
  routes are defined on `FlaskWrapper` in `driver.py`.
- Per-trial threads spawned during a trial:
  - `record_measurements` (mouse + keyboard listeners via pynput)
  - `record_screen` (continuous mss capture, encoded with OpenCV;
    post-process via ffmpeg through `imageio-ffmpeg`)
  - `generate_heatmap` (after the trial; PIL screenshot + OpenCV overlay)

### 6.2 HTTP surface (loopback only)

The agent's Flask server binds `127.0.0.1` deliberately. All endpoints
accept simple CORS from any of `http://localhost`, `http://localhost:5173`,
`http://127.0.0.1`, `http://127.0.0.1:5173`, overridable via
`FULCRUM_FRONTEND_ORIGINS` (comma-separated list).

| Route | Method | Purpose |
|---|---|---|
| `/check_local_tracking_running` | GET | Liveness probe; the browser polls this every few seconds. |
| `/run_study` | POST | Receives the session JSON. Validates the requested measurement list against `capabilities.validate_measurements()`; returns 400 with a clear message if unsupported. |
| `/session_results_status` | GET | State machine: `idle` -> `packaging` -> `ready` (or `error`). The browser polls this after the participant ends the trial. |
| `/get_session_zip_results` | GET | Streams the packaged ZIP. |
| `/get_session_json_results` | GET | Returns the per-session JSON manifest. |
| `/cleanup_session_results` | POST | Best-effort: deletes the local ZIP after the browser confirms a successful upload. |
| `/shutdown_local_tracking` | POST | Triggered by the browser at session end. Requires the literal auth key `shutdownOK`. |

### 6.3 Storage location

Defaults via `platformdirs.user_data_dir("Fulcrum")`:

| OS | Path |
|---|---|
| Windows | `C:\Users\<user>\AppData\Local\Fulcrum\sessions\` |
| macOS | `~/Library/Application Support/Fulcrum/sessions/` |
| Linux | `~/.local/share/Fulcrum/sessions/` |

Override with `FULCRUM_STORAGE_DIR=<path>`.

### 6.4 Capability gating

`local_backend/tracking/utility/capabilities.py` is the single source of
truth for what measurements the agent will accept on the current host.

```python
detect_platform()        -> "windows" | "macos" | "linux-x11" | "linux-wayland" | "unknown"
supported_measurements() -> set[str]  empty on linux-wayland
validate_measurements(requested) -> (ok: bool, errors: list[str])
```

Wayland: `_SUPPORTED[PLATFORM_LINUX_WAYLAND] = set()` deliberately. The
`/run_study` route refuses every session on Wayland with a single, clear
error message.

### 6.5 Sensor reliability invariants

Every sensor thread sets its completion event in a `finally:` block so
that a thread crash (e.g. mss capture failure on a misconfigured display)
never deadlocks the trial wrap-up. Specifically:

| Sensor | Completion event | Guarantee |
|---|---|---|
| `record_measurements` | `data_storage_complete_event` | `finally:` writes CSVs and sets the event. |
| `record_screen` | `adjustments_finished` | `try/except` sets the event on capture failure; `finally:` clears `recording_active`. The adjuster thread sets `adjustments_finished` on the happy path. |
| `generate_heatmap` | `heatmap_generation_complete` | `try/finally` always sets the event, and always removes the intermediate `screenshot.png` so backend ingestion does not see an unrecognized file. |

`driver.GlobalToolbar.wait_trial_save()` spins on these events, so they
are the contract that prevents the "Saving results..." modal from hanging.

---

## 7. Data model

The schema is in `sql_database/create_tables.sql` (27 tables). Reference /
lookup tables are populated by `sql_database/seed_reference_data.sql` on
first DB init.

### 7.1 Core entities

```
user --< study_user_role >-- study
                              |
study --< task                |
study --< factor              |
study --< participant_session --< trial --< session_data_instance
                                                          |
                                                          v
                                                  files on disk
                                                  (RESULTS_BASE_DIR_PATH)
```

- `user`: researcher accounts. Owned by Flask-Security; rows live here
  but are surfaced through SQLAlchemy models in `server_backend/security/`.
- `study`: a research study. Has `study_design_type_id` (Within /
  Between), `expected_participants`, etc.
- `study_user_role`: many-to-many user <-> study with roles Owner / Editor
  / Viewer (`study_user_role_type`).
- `task`, `factor`: study design components. A study has many of each.
- `task_measurement`: which measurements (mouse movement, screen
  recording, etc.) are enabled for which tasks. References
  `measurement_option`.
- `participant_session`: one participant doing one run of a study.
- `trial`: one task-factor pair within a session, with start/end
  timestamps.
- `session_data_instance`: one telemetry file (CSV, MP4, PNG) for one
  trial. The `results_path` column points to the on-disk file under
  `RESULTS_BASE_DIR_PATH`.

### 7.2 Lookup tables (seeded once)

`role_type`, `study_design_type`, `study_user_access_type`,
`study_user_role_type`, `measurement_option`, `gender_type`,
`ethnicity_type`, `highest_education_type`. These are populated by
`seed_reference_data.sql`; the file uses `INSERT IGNORE` so re-running it
is safe.

### 7.3 Consent and surveys

- `consent_form`: one PDF per study, stored on disk via
  `RESULTS_BASE_DIR_PATH/study_consent_forms/<study_id>/`.
- `consent_ack`: a participant's signed acknowledgement.
- `survey_form`: one optional pre- and one optional post-trial JSON
  survey form per study.
- `survey_results`: per-participant submissions.

### 7.4 On-disk results layout

Under `RESULTS_BASE_DIR_PATH` (default: a Docker volume mounted at
`/app/data/participants_results` in the backend container):

```
<study_id>_study_id/
  <participant_session_id>_participant_session_id/
    <trial_id>_trial_id/
      <session_data_instance_id>.csv   (Mouse Movement, etc.)
      <session_data_instance_id>.mp4   (Screen Recording)
      <session_data_instance_id>.png   (Heat Map)
```

The renaming from human-readable filenames (e.g. `Mouse Movement.csv`) to
`<id>.<ext>` happens in `process_trial_file` in
`server_backend/app/utility/sessions.py`. The DB row holds the path; the
filesystem holds the bytes.

---

## 8. End-to-end session flow

A complete participant session:

1. **Researcher creates a study** via `studies.py` blueprint. Rows land
   in `study`, `task`, `factor`, `task_measurement`, optional
   `consent_form` and `survey_form` files on disk.
2. **Researcher initiates a participant session.** `sessions.py`
   creates a `participant_session` row and returns a URL.
3. **Participant clicks the URL, lands in `TrackingPhase.vue`.** Vue
   starts polling `http://127.0.0.1:5001/check_local_tracking_running`
   every 5s.
4. **Participant downloads + runs the agent.** First request:
   `POST /api/download_tracking_tool`, served by `downloads.py` which
   zips `/app/local_backend` on the fly. Participant extracts and runs
   `python driver.py`.
5. **Agent boots, browser sees pings succeed.** The participant clicks
   "Continue" on the Qt "Ready to Go!" dialog.
6. **Browser POSTs `/run_study` to the agent.** Agent's
   `FlaskWrapper.run_study()` calls
   `capabilities.validate_measurements(...)`. On success, signals the
   Qt thread to start the trial.
7. **Per-trial capture.** Three threads run in parallel:
   `record_measurements`, `record_screen`, plus per-trial heatmap
   processing at the end.
8. **Participant clicks End in the toolbar.** `wait_trial_save()`
   blocks on the three completion events. Once all are set,
   `package_session_results()` zips the on-disk session dir into
   `<storage_dir>/session_results_<session_id>.zip`.
9. **Browser polls `/session_results_status` until state == "ready"**,
   then `GET /get_session_zip_results` and `GET /get_session_json_results`.
10. **Browser POSTs the ZIP to the backend** at
    `/api/save_participant_session`. Backend extracts to a tempdir, walks
    each trial folder, and for every recognized file calls
    `process_trial_file()` which inserts a `session_data_instance` row
    and `shutil.move`s the file under `RESULTS_BASE_DIR_PATH`. Unknown
    filenames are skipped with a log line instead of rolling back the
    transaction.
11. **Browser fires `/cleanup_session_results`** so the agent removes
    its local copy of the ZIP.
12. **Browser fires `/shutdown_local_tracking`**; agent exits.

Failure paths worth knowing:

- Agent's Flask thread crashes silently: `start_flask` catches and prints
  the traceback to stderr.
- Trial wrap-up deadlock: prevented by the `finally:` invariants in
  Section 6.5.
- ZIP not yet packaged when browser polls: `/session_results_status`
  returns `packaging`; browser keeps polling until `ready` or its 60-second
  timeout.
- Backend can't `os.rename` across filesystems: `shutil.move` is used in
  `process_trial_file` to handle the `EXDEV` case between `/tmp` and the
  named volume.
- Unrecognized file in the ZIP: the per-file try/except in
  `save_participant_session` skips it rather than rolling back.

---

## 9. Known issues

Tracked in the public README. Quick summary for developers:

- Multi-monitor: hardcoded `sct.monitors[1]` in
  `local_backend/tracking/utility/screenrecording.py` and the implicit
  primary-monitor grab in `screencap.take_screenshot()`. Both need to
  become per-study configurable.
- Wayland: explicitly rejected. PipeWire portal integration is the
  eventual path forward but is non-trivial.
- Email confirmation: Flask-Security commits the user row before the
  SMTP send. A failed send leaves an orphan account row.
- Python 3.13 / 3.14 wheels: some pinned packages (numpy, pandas,
  Pillow) lack prebuilt wheels for the very latest Python. Pin
  participants to 3.12.
- Distribution: agent ships as Python source. PyInstaller bundling is a
  follow-up.

---

## 10. Testing

| Suite | Location | Runner |
|---|---|---|
| Backend unit + integration | `server_backend/tests/` | `pytest` from `server_backend/` |
| Agent unit | `local_backend/tests/` | `pytest` from `local_backend/` |
| Frontend e2e | `frontend/cypress/` | `npx cypress open` from `frontend/` |

CI runs `black` formatting via `.github/workflows/apply_python_formatter.yml`.
No e2e or unit tests run in CI today; that is a planned addition.

---

## 11. Deployment notes

- **Single-host dev / demo**: `docker compose up --build` on any machine
  with Docker. Frontend at `http://localhost/`.
- **Server-hosted production**: same compose file plus a reverse proxy
  (or replace `frontend` with an externally-facing nginx that terminates
  TLS). `EXPECTED_FRONTEND_DOMAIN_URL` must match the public URL.
- **Outbound SMTP**: prefer port 465 if the host's network blocks 587
  (Docker bridge networks sometimes do; .env.example explains).
- **Persistence**: named volumes `mysql_data`, `redis_data`,
  `results_data` retain across container recreations. `docker compose
  down -v` drops them.

---

## 12. Glossary

| Term | Meaning |
|---|---|
| Study | A research experiment definition; has tasks, factors, design type. |
| Task | A unit of activity the participant performs during the study. |
| Factor | An independent variable applied to one or more tasks. |
| Trial | One task-factor pair inside one participant session. |
| Participant session | One participant's run of one study, made up of multiple trials. |
| Measurement | A single telemetry channel: Mouse Movement, Mouse Clicks, etc. Lives in `measurement_option`. |
| Session data instance | One captured file (CSV / MP4 / PNG) for one measurement on one trial. |
| Agent | The local PyQt6 tracking tool installed on the participant's machine. |
| RQ | Redis Queue, used for background analytics jobs. |
