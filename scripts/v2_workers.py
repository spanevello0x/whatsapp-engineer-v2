"""Manage one unmodified Baileys worker per phone, following the Iago layout."""
from __future__ import annotations

import json
import os
import signal
import socket
import sqlite3
import subprocess
import time

from v2_common import DATA, ROOT, WORKER, now, paths, read_json, save_json


def owned_process(profile):
    record = read_json(paths(profile)["process"], {})
    pid = record.get("pid", 0)
    if not isinstance(pid, int) or pid <= 0:
        return None
    result = subprocess.run(
        ["ps", "-p", str(pid), "-o", "lstart=", "-o", "args="],
        text=True, capture_output=True, timeout=5,
    )
    signature = result.stdout.strip()
    if result.returncode or not signature or signature != record.get("signature"):
        return None
    if str(WORKER) not in signature:
        return None
    return record


def db_counts(path):
    if not path.exists():
        return {"exists": False, "messages": 0, "chats": 0}
    try:
        with sqlite3.connect(path.as_uri() + "?mode=ro", uri=True, timeout=2) as db:
            first, last = db.execute("select min(timestamp), max(timestamp) from messages").fetchone()
            return {
                "exists": True,
                "messages": db.execute("select count(*) from messages").fetchone()[0],
                "chats": db.execute("select count(*) from chats").fetchone()[0],
                "first": first, "last": last,
            }
    except sqlite3.Error as exc:
        return {"exists": True, "error": str(exc)}


def connection_events(profile, record):
    """Read only structured connection events from this process generation."""
    connection = "unknown"
    identity = None
    last_history = None
    log = paths(profile)["log"]
    if not record or not log.exists():
        return connection, identity, last_history
    with log.open("rb") as stream:
        stream.seek(record.get("log_offset", 0))
        for raw in stream:
            if not raw.startswith(b"{"):
                continue
            try:
                event = json.loads(raw)
            except (ValueError, UnicodeDecodeError):
                continue
            if event.get("event") == "open":
                connection = "open"
                identity = (event.get("user") or {}).get("id")
            elif event.get("event") == "close":
                connection = "close"
            elif event.get("event") == "history":
                last_history = {key: event.get(key) for key in ["messages", "stored", "isLatest"]}
    return connection, identity, last_history


def status_one(profile):
    resources = paths(profile)
    record = owned_process(profile)
    try:
        state = read_json(resources["status"], {})
    except (ValueError, OSError):
        state = {}
    connection, identity, history = connection_events(profile, record)
    number = identity.split(":")[0].split("@")[0] if identity else None
    matches = number == profile["number"].lstrip("+") if number else None
    db = db_counts(resources["db"])
    healthy = bool(record and connection == "open" and matches is True and db.get("exists") and not db.get("error"))
    qr_fresh = bool(
        record and state.get("state") == "qr" and resources["qr"].exists()
        and time.time() - resources["qr"].stat().st_mtime < 45
    )
    return {
        "slug": profile["slug"], "number": profile["number"],
        "person": profile["person"], "department": profile["department"],
        "running": bool(record), "connection": connection,
        "number_matches": matches, "state": state.get("state", "unknown"),
        "healthy_observed": healthy, "history_batch": history,
        "status_updated_at": state.get("updated_at"),
        "observed_at": now(), "db": db,
        "qr": {"fresh": qr_fresh, "path": str(resources["qr"]) if qr_fresh else None},
    }


def stop_one(profile):
    record = owned_process(profile)
    if record:
        os.kill(record["pid"], signal.SIGTERM)
        deadline = time.monotonic() + 8
        while owned_process(profile) and time.monotonic() < deadline:
            time.sleep(0.25)
        if owned_process(profile):
            os.kill(record["pid"], signal.SIGKILL)
        deadline = time.monotonic() + 3
        while owned_process(profile) and time.monotonic() < deadline:
            time.sleep(0.25)
    stopped = owned_process(profile) is None
    if stopped:
        paths(profile)["qr"].unlink(missing_ok=True)
    return {"slug": profile["slug"], "stopped": stopped}


def start_one(profile, pairing=False):
    resources = paths(profile)
    if owned_process(profile):
        return status_one(profile)
    if not pairing and not (resources["auth"] / "creds.json").exists():
        return {"slug": profile["slug"], "error": "Este telefone precisa ser conectado por código QR."}
    node = config_node()
    if not (ROOT / "node_modules/@whiskeysockets/baileys").exists():
        raise ValueError("Dependências pendentes. Execute prepare antes de conectar.")
    with socket.socket() as check:
        try:
            check.bind(("127.0.0.1", profile["admin_port"]))
        except OSError:
            raise ValueError("A porta deste telefone está ocupada. Verifique a instância existente.") from None
    for name in ["directory", "auth", "media"]:
        resources[name].mkdir(parents=True, exist_ok=True, mode=0o700)
    resources["status"].unlink(missing_ok=True)
    resources["qr"].unlink(missing_ok=True)
    environment = dict(os.environ)
    environment.update({
        "WHATSAPP_ENGINEER_STATE_DIR": str(resources["directory"]),
        "WHATSAPP_ENGINEER_AUTH_DIR": str(resources["auth"]),
        "WHATSAPP_ENGINEER_DB_PATH": str(resources["db"]),
        "WHATSAPP_ENGINEER_MEDIA_DIR": str(resources["media"]),
        "WHATSAPP_ENGINEER_QR_PATH": str(resources["qr"]),
        "WHATSAPP_ENGINEER_STATUS_PATH": str(resources["status"]),
        "WHATSAPP_ENGINEER_ADMIN_TOKEN_PATH": str(resources["token"]),
        "WHATSAPP_ENGINEER_ADMIN_HOST": "127.0.0.1",
        "WHATSAPP_ENGINEER_ADMIN_PORT": str(profile["admin_port"]),
        "WHATSAPP_ENGINEER_ADMIN_ALLOW_WRITES": "0",
        "WHATSAPP_ENGINEER_SYNC_FULL_HISTORY": "1",
        "WHATSAPP_ENGINEER_BAILEYS_LOG_LEVEL": "silent",
    })
    log_offset = resources["log"].stat().st_size if resources["log"].exists() else 0
    with resources["log"].open("ab") as log:
        process = subprocess.Popen(
            [node, "--experimental-sqlite", str(WORKER)], cwd=ROOT, env=environment,
            stdout=log, stderr=log, start_new_session=True, umask=0o077,
        )
    signature = subprocess.run(
        ["ps", "-p", str(process.pid), "-o", "lstart=", "-o", "args="],
        capture_output=True, text=True, timeout=5,
    ).stdout.strip()
    save_json(resources["process"], {
        "pid": process.pid, "signature": signature, "started_at": now(),
        "log_offset": log_offset,
    })
    return status_one(profile)


def config_node():
    from v2_common import config
    node = config().get("node")
    if not node:
        raise ValueError("Preparação pendente. Execute prepare.")
    return node
