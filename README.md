# Nexus Demo Stack

This repository contains a minimal demonstration stack that combines a Vue.js
front-end, a Flask API, and a mocked Hyperledger Fabric integration. It is
based on the Nexus torrent platform concept where users earn wealth by keeping
their client online and sharing resources.

## Project structure

```
backend/            # Flask application with ledger endpoints
frontend/           # Vue 3 + Vite single-page app
hyperledger/        # Mock Fabric client used by the backend
```

## What was set up for you

The initial commit created three cooperating pieces:

- **Flask API (`backend/`)** – exposes a handful of REST endpoints to log in
  and retrieve simulated ledger information.
- **Vue 3 single-page app (`frontend/`)** – renders a login form and, after
  authenticating, presents a dashboard with the logged-in user's identity, a
  community file catalogue, and an upload workflow.
- **Mock Hyperledger client (`hyperledger/`)** – represents the Fabric network
  while you are prototyping. It tracks users, upload / download balances, and
  wealth in memory so the demo behaves like the “mining while seeding” concept
  you described.

The sections below walk through running each part locally and describe the data
flow so you can understand how everything interacts.

## Getting started

### 1. Back-end

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export FLASK_APP=app.py
flask run
```

The API exposes:

- `POST /api/login` – validates the demo `admin` / `admin` credentials and
  returns a mock token plus the Fabric identity ID.
- `GET /api/ledger/balance?username=admin` – retrieves upload, download, and
  wealth metrics from the mocked ledger.
- `POST /api/ledger/reward` – simulates a mining reward, increasing the wealth
  and upload counters.
- `GET /api/files` – returns a list of torrents currently shared by the
  community (seeded in memory for demo purposes).
- `POST /api/files` – accepts a JSON payload describing a file and records it in
  the in-memory catalogue using the authenticated username as uploader.

Under the hood the Flask routes use `hyperledger/ledger.py`. The mock ledger
class keeps an in-memory dictionary keyed by username. When you call the reward
endpoint, that structure is updated immediately so subsequent balance requests
reflect the change.

### 2. Front-end

In a second terminal:

```bash
cd frontend
npm install
npm run dev
```

The Vite dev server proxies API calls to the Flask backend on port `5000`. When
the login form is submitted, the Vue component POSTs to `/api/login` and then
fetches `/api/files` to populate the community catalogue view. The dashboard
shows the logged-in user, their ledger identity, and lets you switch between:

1. **Community files** – displays seeded demo torrents and anything you publish
   during the session.
2. **Upload a file** – captures a file name, size, and description and POSTs
   them to `/api/files`, immediately updating the list view with the new entry.

### 3. Hyperledger integration roadmap

The `hyperledger/ledger.py` module currently hosts an in-memory mock so the
project works out of the box. When you are ready to connect to a Fabric
network:

1. Replace `InMemoryLedger` with a Fabric SDK client (e.g.,
   `fabric-sdk-py`).
2. Use Fabric CA to enrol users and return the certificate in
   `ensure_identity`.
3. Implement chaincode that stores upload/download/wealth metrics and call it
   from `get_balance` / `reward_for_uptime`.
4. Consider emitting Fabric events whenever wealth is accrued so the frontend
   can show live updates.

If you are new to Hyperledger Fabric, the [official docs](https://hyperledger-
fabric.readthedocs.io/) provide step-by-step guides for standing up a test
network. Once you have a Fabric client object in place of the mock ledger you
can reuse the Flask route structure—only the storage implementation changes.

## Next steps

- Expand the achievement system based on upload-to-download ratios.
- Persist real session tokens and protect routes.
- Design Vue views for browsing torrents and tracking wealth milestones.
- Replace the mock ledger with an actual Hyperledger Fabric deployment.
