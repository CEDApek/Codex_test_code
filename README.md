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
  authenticating, shows the mock wealth / balance information that comes back
  from the API.
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

- `POST /api/login` – validates demo credentials (see below), returns a mock
  token plus the Fabric identity ID, and includes the category list for the
  upload form.
- `GET /api/ledger/balance?username=<name>` – retrieves upload counts, pending
  transactions, and wealth metrics from the mocked ledger.
- `POST /api/ledger/reward` – simulates a mining reward, increasing the wealth
  and upload counters while returning the mined block metadata.
- `GET /api/files` – returns the shared catalogue compiled from the community
  seeders and the currently logged-in user.
- `GET /api/files/categories` – exposes the canonical category list used by the
  upload form and filter controls.
- `GET /api/files/<owner>/<file_id>` – fetches the latest metadata for an
  individual entry so the frontend detail page stays in sync with the ledger.
- `GET /api/files/<owner>/<file_id>/download` – streams the stored asset (or a
  generated placeholder for seeded demo files) so every catalogue entry is
  downloadable.
- `POST /api/files` – accepts either JSON or multipart form data, enforces the
  100&nbsp;MB limit, stores uploaded binaries on disk, and records the file on the
  ledger with size, hash, and category metadata.
- `POST /api/register` – creates additional demo accounts that can log in and
  publish resources.

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

The Vite dev server proxies API calls to the Flask backend on port `5000`. After
logging in the dashboard now provides:

1. **Community files** – a searchable, filterable catalogue that lets you drill
   into a dedicated detail page for each file and download it directly from the
   backend.
2. **Upload a file** – a drag-and-drop form that calculates the size
   automatically, enforces the 0–100&nbsp;MB limit, and captures a category so the
   ledger can classify the resource.

In addition to the file tools, the top of the dashboard shows your current
wealth, pending transaction count, a quick mining button, and an account wealth
board that tracks the seeded demo users (`admin`, `alice`, `bob`) alongside the
logged-in account. Every mining run is recorded in a short activity feed so you
can copy block hashes for lab notes.

### Demo credentials and multi-user testing

Three accounts are bundled so you can try different Hyperledger workflows right
away:

| Username | Password | Role          |
|----------|----------|---------------|
| `admin`  | `admin`  | administrator |
| `alice`  | `alice`  | member        |
| `bob`    | `bob`    | member        |

Every time the Flask app starts it ensures these users exist inside the mocked
ledger so you can log in as any of them without extra setup. To simulate a
resource sharing session:

1. Log in as **Alice** or **Bob** using the credentials above.
2. Publish a file through the upload form (or `POST /api/files` with
   `{"username": "alice", ...}`) to queue a declaration transaction.
3. Switch accounts (e.g., log in as Bob) and trigger `POST /api/download` to
   record a download transaction against Alice's upload.
4. Mine the pending transactions by calling `POST /api/ledger/reward` (UI
   button) or `POST /api/mine` with Alice/Bob as the miner to mint a block and
   update wealth balances.
5. Inspect `/api/ledger/balance?username=alice` and the community file list to
   see the results.

Need more test accounts? Call `POST /api/register` with a new username and
password; the backend stores the credentials and provisions the ledger identity
automatically.

### Demo credentials and multi-user testing

Three accounts are bundled so you can try different Hyperledger workflows right
away:

| Username | Password | Role          |
|----------|----------|---------------|
| `admin`  | `admin`  | administrator |
| `alice`  | `alice`  | member        |
| `bob`    | `bob`    | member        |

Every time the Flask app starts it ensures these users exist inside the mocked
ledger so you can log in as any of them without extra setup. To simulate a
resource sharing session:

1. Log in as **Alice** or **Bob** using the credentials above.
2. Publish a file through the upload form (or `POST /api/files` with
   `{"username": "alice", ...}`) to queue a declaration transaction.
3. Switch accounts (e.g., log in as Bob) and trigger `POST /api/download` to
   record a download transaction against Alice's upload.
4. Mine the pending transactions by calling `POST /api/ledger/reward` (UI
   button) or `POST /api/mine` with Alice/Bob as the miner to mint a block and
   update wealth balances.
5. Inspect `/api/ledger/balance?username=alice` and the community file list to
   see the results.

Need more test accounts? Call `POST /api/register` with a new username and
password; the backend stores the credentials and provisions the ledger identity
automatically.

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
