"""Flask backend for Nexus-style demo application.

This backend exposes a login endpoint that validates demo credentials and
provides stub endpoints that would eventually connect to Hyperledger
Fabric. For now they simply call into the ``hyperledger`` helpers that mock
ledger behaviour so the Vue frontend has a coherent API to talk to.
"""
from __future__ import annotations

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


app = Flask(__name__)
CORS(app)

# In a real project credentials would be stored in a database and hashed.
USERS: Dict[str, User] = {
    "admin": User(username="admin", password="admin", role="administrator"),
}

ledger: LedgerClient = InMemoryLedger()


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


if __name__ == "__main__":
    app.run(debug=True)
