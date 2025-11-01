"""Flask backend for Nexus-style BT resource sharing application."""

import hashlib
import os
import re
import sys
import time
import traceback
from typing import Any, Dict, List

from flask import Flask, jsonify, request
from flask_cors import CORS

# Ensure project root (Nexus/) is in sys.path so "hyperledger" can be imported
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

# Import the hyperledger ResourceSharingSystem according to your interface doc
# This must exist at hyperledger/ledger.py
try:
    from hyperledger.ledger import ResourceSharingSystem
except Exception as e:  # pragma: no cover - import guard for developer ergonomics
    # If import fails, raise a helpful error so developer can fix hyperledger package
    raise ImportError(
        "Failed to import ResourceSharingSystem from hyperledger.ledger. "
        "Please ensure hyperledger/ledger.py exports ResourceSharingSystem."
    ) from e

app = Flask(__name__)
CORS(app)

# Single global ResourceSharingSystem instance
system: ResourceSharingSystem = ResourceSharingSystem()

# Demo credential store used by the Vue frontend.
USERS: Dict[str, Dict[str, str]] = {
    "admin": {"password": "admin", "role": "administrator"},
    # Demo seed accounts so you can test uploads/downloads without registering first.
    "alice": {"password": "alice", "role": "member"},
    "bob": {"password": "bob", "role": "member"},
}


def bootstrap_demo_accounts() -> None:
    """Ensure the built-in demo accounts exist in the ledger layer."""
    for username in USERS:
        ensure_ledger_user(username)


def ensure_ledger_user(username: str):
    """Return an existing ledger user or register a new one on demand."""
    user = system.get_user(username)
    if user is None:
        user = system.register_user(username)
    return user


def format_size(size_gb: float) -> str:
    """Convert a size in gigabytes into a human friendly string."""
    if size_gb >= 1:
        return f"{size_gb:.2f} GB"
    size_mb = size_gb * 1024
    if size_mb >= 1:
        return f"{size_mb:.1f} MB"
    size_kb = size_mb * 1024
    return f"{size_kb:.0f} KB"


def parse_size_to_gb(size_text: str) -> float:
    """Parse size strings such as '42.7 MB' into gigabytes."""
    if not size_text:
        raise ValueError("size is required")

    match = re.match(r"\s*([0-9]*\.?[0-9]+)\s*([a-zA-Z]*)\s*", size_text)
    if not match:
        raise ValueError("invalid size format")

    value = float(match.group(1))
    unit = match.group(2).lower() or "mb"
    multipliers = {
        "kb": 1 / (1024 * 1024),
        "mb": 1 / 1024,
        "gb": 1,
        "tb": 1024,
    }

    if unit not in multipliers:
        raise ValueError(f"unsupported size unit '{unit}'")

    return value * multipliers[unit]


def serialize_shared_file(file_obj, owner_username: str) -> Dict[str, Any]:
    """Convert SharedFile objects into dictionaries for the frontend."""
    return {
        "id": f"{owner_username or 'catalogue'}-{file_obj.id}",
        "name": getattr(file_obj, "name", "Unnamed"),
        "description": getattr(file_obj, "description", ""),
        "size": format_size(getattr(file_obj, "size_gb", 0.0)),
        "uploader": owner_username or getattr(file_obj, "uploader", "community"),
        "seeds": getattr(file_obj, "seeds", 0),
        "peers": getattr(file_obj, "peers", 0),
    }


def list_catalogue() -> List[Dict[str, Any]]:
    """Aggregate shared files from the global catalogue and all users."""
    results: List[Dict[str, Any]] = []

    # Include globally seeded demo files.
    for file_obj in system.global_resource_manager.get_active_files():
        results.append(serialize_shared_file(file_obj, owner_username="community"))

    # Include every registered user's active files.
    for username, user in system.users.items():
        for file_obj in user.resource_manager.get_active_files():
            results.append(serialize_shared_file(file_obj, owner_username=username))

    return results


def error_response(msg: str, code: int = 400):
    return jsonify({"success": False, "error": msg, "message": msg}), code


bootstrap_demo_accounts()


@app.route("/api/login", methods=["POST"])
def api_login():
    try:
        data: Dict[str, Any] = request.get_json(force=True)
    except Exception:
        return error_response("invalid JSON payload", 400)

    username = data.get("username", "").strip()
    password = data.get("password", "")

    if not username or not password:
        return error_response("username and password are required", 400)

    user_record = USERS.get(username)
    if not user_record or user_record.get("password") != password:
        return error_response("Invalid username or password.", 401)

    ledger_user = ensure_ledger_user(username)

    return jsonify({
        "token": f"demo-token-{username}",
        "username": username,
        "role": user_record.get("role", "user"),
        "ledgerIdentity": getattr(ledger_user, "address", None),
    })


@app.route("/api/ledger/balance", methods=["GET"])
def api_ledger_balance():
    username = request.args.get("username", "").strip()
    if not username:
        return error_response("missing field: username", 400)

    ledger_user = ensure_ledger_user(username)
    balance = system.get_user_balance(username)

    uploads = len(ledger_user.resource_manager.get_files_by_owner(ledger_user.address))

    return jsonify({
        "username": username,
        "ledgerIdentity": getattr(ledger_user, "address", None),
        "wealth": balance,
        "uploads": uploads,
        "downloads": 0,
        "pendingTransactions": len(system.blockchain.pending_transactions),
    })


@app.route("/api/ledger/reward", methods=["POST"])
def api_ledger_reward():
    try:
        data: Dict[str, Any] = request.get_json(force=True)
    except Exception:
        return error_response("invalid JSON payload", 400)

    username = data.get("username", "").strip()
    if not username:
        return error_response("missing field: username", 400)

    ensure_ledger_user(username)
    block = system.mine_block(username)
    if block is None:
        return error_response("no pending transactions to mine", 400)

    block_payload = block.to_dict() if hasattr(block, "to_dict") else {
        "index": getattr(block, "index", None),
        "timestamp": getattr(block, "timestamp", None),
        "hash": getattr(block, "hash", None),
    }

    return jsonify({
        "success": True,
        "block": block_payload,
        "wealth": system.get_user_balance(username),
    })


@app.route("/api/files", methods=["GET"])
def api_list_files():
    catalogue = list_catalogue()
    return jsonify(catalogue)


@app.route("/api/files", methods=["POST"])
def api_publish_file():
    try:
        data: Dict[str, Any] = request.get_json(force=True)
    except Exception:
        return error_response("invalid JSON payload", 400)

    username = data.get("username", "").strip()
    name = data.get("name", "").strip()
    size_text = data.get("size", "").strip()
    description = (data.get("description") or "").strip()

    if not username or not name or not size_text:
        return error_response("username, name, and size are required", 400)

    ledger_user = ensure_ledger_user(username)

    try:
        size_gb = parse_size_to_gb(size_text)
    except ValueError as exc:
        return error_response(str(exc), 400)

    file_hash = hashlib.sha256(f"{username}:{name}:{time.time()}".encode()).hexdigest()[:16]
    file_payload = {
        "name": name,
        "size_gb": size_gb,
        "uploader": username,
        "seeds": 1,
        "peers": 0,
        "description": description,
        "category": "community",
        "file_hash": file_hash,
    }

    success = system.declare_user_resources(username, file_payload)
    if not success:
        return error_response("unable to publish file to ledger", 500)

    created_file = None
    for file_obj in ledger_user.resource_manager.get_files_by_owner(ledger_user.address):
        if getattr(file_obj, "file_hash", "") == file_hash:
            created_file = file_obj
            break

    if created_file is None:
        created = {
            "id": f"{username}-{int(time.time())}",
            "name": name,
            "description": description,
            "size": size_text,
            "uploader": username,
            "seeds": 1,
            "peers": 0,
        }
    else:
        created = serialize_shared_file(created_file, owner_username=username)

    return jsonify(created), 201


@app.route("/api/register", methods=["POST"])
def api_register():
    """
    POST /api/register
    body: { "username": "alice" }
    """
    try:
        data: Dict[str, Any] = request.get_json(force=True)
        username = (data.get("username") or "").strip()
        password = (data.get("password") or "").strip()
        role = (data.get("role") or "user").strip() or "user"

        if not username or not password:
            return error_response("username and password are required", 400)

        if system.get_user(username):
            return error_response(f"username '{username}' already exists", 409)

        if username in USERS:
            return error_response(f"username '{username}' already exists", 409)

        user = system.register_user(username)
        USERS[username] = {"password": password, "role": role}

        return jsonify({
            "success": True,
            "username": username,
            "address": getattr(user, "address", None),
            "role": role,
        })
    except Exception as e:  # pragma: no cover - defensive logging for dev server
        traceback.print_exc()
        return error_response(str(e), 500)


@app.route("/api/declare", methods=["POST"])
def api_declare():
    """
    POST /api/declare
    body: {
      "username": "alice",
      "file": { ... }   # see file_data example in interface doc
    }
    """
    try:
        data: Dict[str, Any] = request.get_json(force=True)
        username = data.get("username")
        file_data = data.get("file")
        if not username or not file_data:
            return error_response("missing username or file data", 400)

        user = system.get_user(username)
        if not user:
            return error_response("user not found", 404)

        success = system.declare_user_resources(username, file_data)
        if success:
            return jsonify({"success": True, "message": "resource declared (added to pending txs)"})
        else:
            return error_response("declare failed (see hyperledger logs)", 500)
    except Exception as e:  # pragma: no cover - defensive logging for dev server
        traceback.print_exc()
        return error_response(str(e), 500)


@app.route("/api/download", methods=["POST"])
def api_download():
    """
    POST /api/download
    body: {
      "downloader": "bob",
      "owner": "alice",
      "file_id": 2
    }
    """
    try:
        data: Dict[str, Any] = request.get_json(force=True)
        downloader = data.get("downloader")
        owner = data.get("owner")
        file_id = data.get("file_id")
        if not downloader or not owner or file_id is None:
            return error_response("missing downloader/owner/file_id", 400)

        # System-level convenience method per your doc
        ok = system.download_resource(downloader, owner, int(file_id))
        if ok:
            return jsonify({"success": True, "message": "download transaction added to pending pool"})
        else:
            return error_response("download failed (insufficient balance, missing file, or other)", 400)
    except Exception as e:  # pragma: no cover - defensive logging for dev server
        traceback.print_exc()
        return error_response(str(e), 500)


@app.route("/api/mine", methods=["POST"])
def api_mine():
    """
    POST /api/mine
    body: { "miner": "alice" }
    """
    try:
        data: Dict[str, Any] = request.get_json(force=True)
        miner = data.get("miner")
        if not miner:
            return error_response("missing field: miner", 400)

        # mine_block returns a Block per your doc
        block = system.mine_block(miner)
        if block is None:
            return error_response("no pending transactions to mine", 400)

        # Block is expected to have to_dict method (or attributes)
        block_dict = block.to_dict() if hasattr(block, "to_dict") else {
            "index": getattr(block, "index", None)
        }
        return jsonify({"success": True, "block": block_dict})
    except Exception as e:  # pragma: no cover - defensive logging for dev server
        traceback.print_exc()
        return error_response(str(e), 500)


@app.route("/api/balance/<username>", methods=["GET"])
def api_balance(username: str):
    try:
        user = system.get_user(username)
        if not user:
            return error_response("user not found", 404)
        balance = system.get_user_balance(username)
        return jsonify({"success": True, "username": username, "balance": balance})
    except Exception as e:  # pragma: no cover - defensive logging for dev server
        traceback.print_exc()
        return error_response(str(e), 500)


@app.route("/api/blockchain", methods=["GET"])
def api_blockchain_info():
    try:
        info = system.get_blockchain_info()
        return jsonify({"success": True, "blockchain_info": info})
    except Exception as e:  # pragma: no cover - defensive logging for dev server
        traceback.print_exc()
        return error_response(str(e), 500)


@app.route("/api/resources", methods=["GET"])
def api_search_resources():
    """
    GET /api/resources?keyword=...&category=...&min_size=...&max_size=...&min_seeds=...
    """
    try:
        q = request.args
        kwargs: Dict[str, Any] = {}
        if "keyword" in q and q.get("keyword"):
            kwargs["keyword"] = q.get("keyword")
        if "category" in q and q.get("category"):
            kwargs["category"] = q.get("category")
        if "min_size" in q and q.get("min_size"):
            kwargs["min_size"] = float(q.get("min_size"))
        if "max_size" in q and q.get("max_size"):
            kwargs["max_size"] = float(q.get("max_size"))
        if "min_seeds" in q and q.get("min_seeds"):
            kwargs["min_seeds"] = int(q.get("min_seeds"))

        results = system.search_resources(**kwargs)
        # Each result expected to have to_dict()
        return jsonify({"success": True, "results": [r.to_dict() for r in results]})
    except Exception as e:  # pragma: no cover - defensive logging for dev server
        traceback.print_exc()
        return error_response(str(e), 500)


@app.route("/api/resources/all", methods=["GET"])
def api_get_all_resources():
    try:
        results = system.get_all_resources()
        return jsonify({"success": True, "results": [r.to_dict() for r in results]})
    except Exception as e:  # pragma: no cover - defensive logging for dev server
        traceback.print_exc()
        return error_response(str(e), 500)


@app.route("/api/user/<username>/files", methods=["GET"])
def api_get_user_files(username: str):
    try:
        user = system.get_user(username)
        if not user:
            return error_response("user not found", 404)
        files = user.get_my_files()
        return jsonify({"success": True, "files": [f.to_dict() for f in files]})
    except Exception as e:  # pragma: no cover - defensive logging for dev server
        traceback.print_exc()
        return error_response(str(e), 500)


@app.route("/api/user/<username>/file/<int:file_id>", methods=["DELETE"])
def api_delete_user_file(username: str, file_id: int):
    try:
        user = system.get_user(username)
        if not user:
            return error_response("user not found", 404)
        ok = user.remove_my_file(file_id)
        if ok:
            return jsonify({"success": True, "message": "file removed"})
        else:
            return error_response("remove failed (not found or not owner)", 400)
    except Exception as e:  # pragma: no cover - defensive logging for dev server
        traceback.print_exc()
        return error_response(str(e), 500)


@app.route("/api/user/<username>/file/<int:file_id>", methods=["PUT"])
def api_update_user_file(username: str, file_id: int):
    """
    PUT /api/user/<username>/file/<file_id>
    body: { "update": { ... } }
    """
    try:
        payload: Dict[str, Any] = request.get_json(force=True)
        update_data = payload.get("update")
        if not update_data:
            return error_response("missing update data", 400)
        user = system.get_user(username)
        if not user:
            return error_response("user not found", 404)
        updated = user.update_my_file(file_id, update_data)
        if updated:
            return jsonify({"success": True, "file": updated.to_dict()})
        else:
            return error_response("update failed (not found or not owner)", 400)
    except Exception as e:  # pragma: no cover - defensive logging for dev server
        traceback.print_exc()
        return error_response(str(e), 500)


# --- Report & Admin review (only use public interfaces) ---
@app.route("/api/report", methods=["POST"])
def api_report():
    """
    POST /api/report
    body: { "reporter": "bob", "owner": "alice", "file_id": 3, "reason": "..." }

    Implementation: use ResourceManager.update_file to set is_active=False (if available).
    We do NOT perform chain rollbacks here.
    """
    try:
        data: Dict[str, Any] = request.get_json(force=True)
        reporter = data.get("reporter")
        owner = data.get("owner")
        file_id = data.get("file_id")
        reason = data.get("reason", "")

        if not reporter or not owner or file_id is None:
            return error_response("missing reporter/owner/file_id", 400)

        owner_user = system.get_user(owner)
        if not owner_user:
            return error_response("owner user not found", 404)

        # get_file then update to set is_active False via update_file if available
        rm = owner_user.resource_manager
        target = rm.get_file(int(file_id))
        if not target:
            return error_response("file not found", 404)

        # Use update_file to change is_active if allowed by hyperledger implementation
        update_payload = {"is_active": False}
        updated = rm.update_file(int(file_id), update_payload, owner_user.address)
        if updated:
            return jsonify({
                "success": True,
                "message": f"file {file_id} marked inactive (reported). Admin review required.",
                "file": updated.to_dict(),
                "report": {"reporter": reporter, "reason": reason}
            })
        else:
            # If update_file rejects (e.g., not permitted), fallback to error
            return error_response("failed to mark file inactive via ResourceManager.update_file", 500)
    except Exception as e:  # pragma: no cover - defensive logging for dev server
        traceback.print_exc()
        return error_response(str(e), 500)


@app.route("/api/admin/review", methods=["POST"])
def api_admin_review():
    """
    POST /api/admin/review
    body: {
      "admin": "admin1",
      "owner": "alice",
      "file_id": 3,
      "action": "approve" | "remove" | "rollback",
      "reason": "...",
    }

    approve -> set is_active True
    remove  -> set is_active False
    rollback -> NOT IMPLEMENTED here (requires hyperledger-level balance/rollback APIs)
    """
    try:
        data: Dict[str, Any] = request.get_json(force=True)
        admin = data.get("admin")
        owner = data.get("owner")
        file_id = data.get("file_id")
        action = data.get("action")

        if not admin or not owner or file_id is None or not action:
            return error_response("missing fields", 400)

        owner_user = system.get_user(owner)
        if not owner_user:
            return error_response("owner not found", 404)

        rm = owner_user.resource_manager
        target = rm.get_file(int(file_id))
        if not target:
            return error_response("file not found", 404)

        if action == "approve":
            updated = rm.update_file(int(file_id), {"is_active": True}, owner_user.address)
            if updated:
                return jsonify({"success": True, "message": "resource approved", "file": updated.to_dict()})
            else:
                return error_response("approve failed", 500)
        elif action == "remove":
            updated = rm.update_file(int(file_id), {"is_active": False}, owner_user.address)
            if updated:
                return jsonify({"success": True, "message": "resource removed (inactive)", "file": updated.to_dict()})
            else:
                return error_response("remove failed", 500)
        elif action == "rollback":
            # We do not implement chain/balance rollbacks in app layer.
            # This requires hyperledger resource to expose a safe API to deduct credits or emit rollback tx.
            return error_response(
                "rollback not implemented in app layer; please implement on hyperledger and expose an API",
                501,
            )
        else:
            return error_response("unknown action", 400)
    except Exception as e:  # pragma: no cover - defensive logging for dev server
        traceback.print_exc()
        return error_response(str(e), 500)


if __name__ == "__main__":
    # Run as module recommended: python -m backend.app  (from project root)
    app.run(host="0.0.0.0", port=5000, debug=True)
