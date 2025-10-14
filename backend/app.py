"""Flask backend for Nexus-style demo application.

This backend exposes a login endpoint that validates demo credentials and
provides stub endpoints that would eventually connect to Hyperledger
Fabric. For now they simply call into the ``hyperledger`` helpers that mock
ledger behaviour so the Vue frontend has a coherent API to talk to.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from itertools import count
from typing import Dict, List, Optional
from dataclasses import dataclass
from typing import Dict, Optional

from flask import Flask, jsonify, request
from flask_cors import CORS

from hyperledger.ledger import LedgerClient, InMemoryLedger


@dataclass
class User:
    username: str
    password: str
    role: str


@dataclass
class SharedFile:
    """Representation of a file that has been shared through the exchange."""

    id: int
    name: str
    size: str
    uploader: str
    seeds: int
    peers: int
    description: str = ""


app = Flask(__name__)
CORS(app)

# In a real project credentials would be stored in a database and hashed.
USERS: Dict[str, User] = {
    "admin": User(username="admin", password="admin", role="administrator"),
}

ledger: LedgerClient = InMemoryLedger()


FILES: List[SharedFile] = [
    SharedFile(
        id=1,
        name="The Art of Seeding.pdf",
        size="12.4 MB",
        uploader="seedMaster",
        seeds=42,
        peers=5,
        description="Illustrated guide to earning wealth rewards efficiently.",
    ),
    SharedFile(
        id=2,
        name="Nexus OST.mp3",
        size="6.3 MB",
        uploader="djHyper",
        seeds=18,
        peers=12,
        description="Synthwave soundtrack to keep your node online.",
    ),
    SharedFile(
        id=3,
        name="ClientSetup.zip",
        size="48.1 MB",
        uploader="builderBee",
        seeds=33,
        peers=4,
        description="Automation scripts to bootstrap a new seeding rig.",
    ),
]

FILE_ID_COUNTER = count(start=len(FILES) + 1)


@app.post("/api/login")
def login() -> tuple[str, int] | tuple[Dict[str, str], int]:
    """Validate user credentials.

    The demo only accepts the hard-coded admin/admin credentials. When the
    login succeeds we return a simple token and the ledger identity that was
    registered for the user.
    """
    payload = request.get_json(silent=True) or {}
    username = payload.get("username", "")
    password = payload.get("password", "")

    user: Optional[User] = USERS.get(username)
    if not user or user.password != password:
        return jsonify({"message": "Invalid username or password."}), 401

    identity = ledger.ensure_identity(username)
    return jsonify({
        "token": f"demo-token-for-{username}",
        "username": username,
        "role": user.role,
        "ledgerIdentity": identity,
    })


@app.get("/api/ledger/balance")
def ledger_balance() -> tuple[Dict[str, int], int]:
    """Return the user's current upload/download balance from the ledger."""
    username = request.args.get("username")
    if not username:
        return jsonify({"message": "username query parameter is required"}), 400

    balance = ledger.get_balance(username)
    if balance is None:
        return jsonify({"message": "User not found on ledger"}), 404

    return jsonify(balance), 200


@app.post("/api/ledger/reward")
def ledger_reward() -> tuple[Dict[str, int], int]:
    """Simulate mining rewards by increasing the wealth metric."""
    payload = request.get_json(silent=True) or {}
    username = payload.get("username")
    if not username:
        return jsonify({"message": "username is required"}), 400

    updated = ledger.reward_for_uptime(username)
    if updated is None:
        return jsonify({"message": "User not found on ledger"}), 404

    return jsonify(updated), 200


@app.get("/api/files")
def list_files() -> tuple[List[Dict[str, object]], int]:
    """Return the catalogue of files shared by the community."""

    return jsonify([asdict(entry) for entry in FILES]), 200


@app.post("/api/files")
def upload_file() -> tuple[Dict[str, str], int]:
    """Record a newly shared file in the in-memory catalogue."""

    payload = request.get_json(silent=True) or {}
    name = (payload.get("name") or "").strip()
    size = (payload.get("size") or "").strip()
    username = payload.get("username")
    description = (payload.get("description") or "").strip()

    if not username:
        return jsonify({"message": "username is required"}), 400

    if username not in USERS:
        return jsonify({"message": "Unknown user"}), 404

    if not name:
        return jsonify({"message": "File name is required"}), 400

    if not size:
        return jsonify({"message": "File size is required"}), 400

    entry = SharedFile(
        id=next(FILE_ID_COUNTER),
        name=name,
        size=size,
        uploader=username,
        seeds=1,
        peers=0,
        description=description,
    )
    FILES.append(entry)

    return jsonify(asdict(entry)), 201


if __name__ == "__main__":
    app.run(debug=True)
