"""Flask backend for Nexus-style BT resource sharing application."""

import hashlib
import io
import mimetypes
import os
import re
import sys
import time
import traceback
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from flask import Flask, jsonify, request, send_file, url_for
from flask_cors import CORS
from werkzeug.utils import secure_filename

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

UPLOAD_ROOT = os.path.join(ROOT, "backend", "uploads")
MAX_UPLOAD_BYTES = 100 * 1024 * 1024  # 100 MB cap per requirements
os.makedirs(UPLOAD_ROOT, exist_ok=True)

# Demo credential store used by the Vue frontend.
USERS: Dict[str, Dict[str, str]] = {
    "admin": {"password": "admin", "role": "administrator"},
    # Demo seed accounts so you can test uploads/downloads without registering first.
    "alice": {"password": "alice", "role": "member"},
    "bob": {"password": "bob", "role": "member"},
}

FILE_CATEGORIES: List[Dict[str, str]] = [
    {"value": "document", "label": "Document"},
    {"value": "audio", "label": "Audio"},
    {"value": "video", "label": "Video"},
    {"value": "software", "label": "Software"},
    {"value": "dataset", "label": "Dataset"},
    {"value": "image", "label": "Image"},
    {"value": "archive", "label": "Archive"},
    {"value": "other", "label": "Other"},
]

CATEGORY_LABEL_LOOKUP = {entry["value"]: entry["label"] for entry in FILE_CATEGORIES}
DEFAULT_CATEGORY = "other"


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


def bytes_to_gb(size_bytes: int) -> float:
    return size_bytes / (1024 ** 3)


def clamp_upload_size(size_bytes: int) -> None:
    if size_bytes <= 0:
        raise ValueError("uploaded file is empty")
    if size_bytes > MAX_UPLOAD_BYTES:
        raise ValueError("uploaded file exceeds the 100 MB limit")


def normalize_category(raw: str) -> str:
    if not raw:
        return DEFAULT_CATEGORY
    slug = re.sub(r"[^a-z0-9]+", "_", raw.strip().lower()).strip("_")
    if slug in CATEGORY_LABEL_LOOKUP:
        return slug
    if slug.endswith("s") and slug[:-1] in CATEGORY_LABEL_LOOKUP:
        return slug[:-1]
    return DEFAULT_CATEGORY


def category_label(value: str) -> str:
    normalized = normalize_category(value)
    return CATEGORY_LABEL_LOOKUP.get(normalized, normalized.title() or "Other")


def split_name(name: str) -> Tuple[str, str]:
    base, ext = os.path.splitext(name or "")
    cleaned_ext = ext[1:].lower() if ext else ""
    return (base or name or "Unnamed"), cleaned_ext


def serialize_shared_file(file_obj, owner_username: str) -> Dict[str, Any]:
    """Convert SharedFile objects into dictionaries for the frontend."""

    name = getattr(file_obj, "name", "Unnamed")
    base_name, derived_extension = split_name(name)
    extension = getattr(file_obj, "extension", "") or derived_extension
    category_value = normalize_category(getattr(file_obj, "category", DEFAULT_CATEGORY))
    size_gb = float(getattr(file_obj, "size_gb", 0.0) or 0.0)
    size_mb = size_gb * 1024
    uploader = getattr(file_obj, "uploader", owner_username or "community")
    owner = owner_username or uploader or "community"
    file_id = getattr(file_obj, "id", None)
    upload_time = getattr(file_obj, "upload_time", None)
    upload_iso: Optional[str] = None
    if upload_time:
        upload_iso = datetime.utcfromtimestamp(upload_time).isoformat() + "Z"

    download_url = None
    if file_id is not None:
        try:
            download_url = url_for("api_download_file", owner=owner, file_id=file_id, _external=False)
        except RuntimeError:
            download_url = f"/api/files/{owner}/{file_id}/download"

    return {
        "id": f"{owner}-{file_id}" if owner and file_id is not None else str(file_id or name),
        "fileId": file_id,
        "owner": owner,
        "ownerAddress": getattr(file_obj, "owner_address", ""),
        "uploader": uploader,
        "fileHash": getattr(file_obj, "file_hash", ""),
        "name": name,
        "baseName": base_name,
        "extension": extension,
        "category": category_value,
        "categoryLabel": category_label(category_value),
        "description": getattr(file_obj, "description", ""),
        "size": format_size(size_gb),
        "sizeText": format_size(size_gb),
        "sizeGB": size_gb,
        "sizeMB": round(size_mb, 3),
        "seeds": getattr(file_obj, "seeds", 0),
        "peers": getattr(file_obj, "peers", 0),
        "downloadUrl": download_url,
        "canDownload": True,
        "hasStorage": bool(getattr(file_obj, "storage_path", "")),
        "uploadTime": upload_time,
        "uploadTimeIso": upload_iso,
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

    results.sort(key=lambda item: item.get("uploadTime") or 0, reverse=True)
    return results


def error_response(msg: str, code: int = 400):
    return jsonify({"success": False, "error": msg, "message": msg}), code


def locate_file(owner_username: str, file_id: int):
    normalized_owner = (owner_username or "").strip()
    if normalized_owner == "community":
        file_obj = system.global_resource_manager.get_file(int(file_id))
        return file_obj, "community", None

    user = system.get_user(normalized_owner)
    if not user:
        return None, normalized_owner, None

    file_obj = user.resource_manager.get_file(int(file_id))
    return file_obj, normalized_owner, user


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
    wealth = system.get_user_balance(username)

    return jsonify({
        "token": f"demo-token-{username}",
        "username": username,
        "role": user_record.get("role", "user"),
        "ledgerIdentity": getattr(ledger_user, "address", None),
        "wealth": wealth,
        "pendingTransactions": len(system.blockchain.pending_transactions),
        "categories": FILE_CATEGORIES,
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


@app.route("/api/files/categories", methods=["GET"])
def api_file_categories():
    return jsonify(FILE_CATEGORIES)


@app.route("/api/files", methods=["POST"])
def api_publish_file():
    content_type = request.content_type or ""
    is_multipart = "multipart/form-data" in content_type

    if is_multipart:
        form = request.form
        uploaded_file = request.files.get("file")
        username = (form.get("username") or "").strip()
        name = (form.get("name") or "").strip()
        description = (form.get("description") or "").strip()
        category_value = normalize_category(form.get("category"))

        if uploaded_file is None or not uploaded_file.filename:
            return error_response("a file must be provided", 400)

        try:
            uploaded_file.stream.seek(0)
            hasher = hashlib.sha256()
            total_size = 0
            while True:
                chunk = uploaded_file.stream.read(8192)
                if not chunk:
                    break
                total_size += len(chunk)
                hasher.update(chunk)
            clamp_upload_size(total_size)
        except ValueError as exc:
            return error_response(str(exc), 400)
        finally:
            uploaded_file.stream.seek(0)

        size_gb = bytes_to_gb(total_size)
        size_text = format_size(size_gb)
        file_hash = hasher.hexdigest()[:16]

        safe_name = secure_filename(uploaded_file.filename) or "uploaded.bin"
        if not name:
            name = uploaded_file.filename or safe_name

        base_name, extension = split_name(uploaded_file.filename or safe_name)

        if not username or not name:
            return error_response("username and name are required", 400)

        ledger_user = ensure_ledger_user(username)

        user_folder = os.path.join(UPLOAD_ROOT, username)
        os.makedirs(user_folder, exist_ok=True)
        timestamp = int(time.time())
        filename_parts = [str(timestamp), file_hash, safe_name]
        stored_filename = "_".join(filter(None, filename_parts))
        stored_path = os.path.join(user_folder, stored_filename)
        uploaded_file.save(stored_path)

        file_payload = {
            "name": name,
            "size_gb": size_gb,
            "uploader": username,
            "seeds": 1,
            "peers": 0,
            "description": description,
            "category": category_value,
            "extension": extension,
            "file_hash": file_hash,
            "storage_path": stored_path,
        }
    else:
        try:
            data: Dict[str, Any] = request.get_json(force=True)
        except Exception:
            return error_response("invalid JSON payload", 400)

        username = data.get("username", "").strip()
        name = data.get("name", "").strip()
        size_text = data.get("size", "").strip()
        description = (data.get("description") or "").strip()
        category_value = normalize_category(data.get("category"))

        if not username or not name or not size_text:
            return error_response("username, name, and size are required", 400)

        ledger_user = ensure_ledger_user(username)

        try:
            size_gb = parse_size_to_gb(size_text)
        except ValueError as exc:
            return error_response(str(exc), 400)

        size_text = format_size(size_gb)

        base_name, extension = split_name(name)
        file_hash = hashlib.sha256(f"{username}:{name}:{time.time()}".encode()).hexdigest()[:16]
        file_payload = {
            "name": name,
            "size_gb": size_gb,
            "uploader": username,
            "seeds": 1,
            "peers": 0,
            "description": description,
            "category": category_value,
            "extension": extension,
            "file_hash": file_hash,
        }

    success = system.declare_user_resources(username, file_payload)
    if not success:
        return error_response("unable to publish file to ledger", 500)

    ledger_user = ensure_ledger_user(username)
    created_file = None
    for file_obj in ledger_user.resource_manager.get_files_by_owner(ledger_user.address):
        if getattr(file_obj, "file_hash", "") == file_payload["file_hash"]:
            created_file = file_obj
            break

    created: Optional[Dict[str, Any]] = None
    if created_file is not None:
        created = serialize_shared_file(created_file, owner_username=username)
    else:
        for entry in list_catalogue():
            if entry.get("fileHash") == file_payload["file_hash"]:
                created = entry
                break

    if created is None:
        now = time.time()
        created = {
            "id": f"{username}-{int(now)}",
            "fileId": None,
            "owner": username,
            "ownerAddress": getattr(ledger_user, "address", ""),
            "uploader": username,
            "fileHash": file_payload["file_hash"],
            "name": name,
            "baseName": base_name,
            "extension": extension,
            "category": category_value,
            "categoryLabel": category_label(category_value),
            "description": description,
            "size": size_text if not is_multipart else format_size(size_gb),
            "sizeText": size_text if not is_multipart else format_size(size_gb),
            "sizeGB": size_gb,
            "sizeMB": round(size_gb * 1024, 3),
            "seeds": 1,
            "peers": 0,
            "downloadUrl": None,
            "canDownload": True,
            "hasStorage": is_multipart,
            "uploadTime": now,
            "uploadTimeIso": datetime.utcfromtimestamp(now).isoformat() + "Z",
        }

    return jsonify(created), 201


@app.route("/api/files/<owner>/<int:file_id>", methods=["GET"])
def api_file_detail(owner: str, file_id: int):
    file_obj, normalized_owner, _ = locate_file(owner, file_id)
    if not file_obj or not getattr(file_obj, "is_active", True):
        return error_response("file not found", 404)

    payload = serialize_shared_file(file_obj, owner_username=normalized_owner or "community")
    return jsonify(payload)


@app.route("/api/files/<owner>/<int:file_id>/download", methods=["GET"])
def api_download_file(owner: str, file_id: int):
    file_obj, normalized_owner, _ = locate_file(owner, file_id)
    if not file_obj or not getattr(file_obj, "is_active", True):
        return error_response("file not found", 404)

    file_name = getattr(file_obj, "name", f"download-{file_id}") or f"download-{file_id}"
    storage_path = getattr(file_obj, "storage_path", "")
    mime_type, _ = mimetypes.guess_type(file_name)

    if storage_path and os.path.isfile(storage_path):
        absolute_path = os.path.abspath(storage_path)
        if not absolute_path.startswith(ROOT):
            return error_response("file storage path is invalid", 403)
        return send_file(
            absolute_path,
            as_attachment=True,
            download_name=file_name,
            mimetype=mime_type or "application/octet-stream",
        )

    # Fallback: generate an informative payload so catalogue files can be downloaded
    info_lines = [
        "This is a generated copy of a catalogue resource.",
        f"Name: {file_name}",
        f"Category: {category_label(getattr(file_obj, 'category', DEFAULT_CATEGORY))}",
        f"Owner: {normalized_owner or getattr(file_obj, 'uploader', 'community')}",
        "",  # blank line
        getattr(file_obj, "description", ""),
    ]
    fallback_bytes = "\n".join(line for line in info_lines if line).encode("utf-8")
    buffer = io.BytesIO(fallback_bytes)
    buffer.seek(0)

    return send_file(
        buffer,
        as_attachment=True,
        download_name=file_name,
        mimetype=mime_type or "text/plain",
    )


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
