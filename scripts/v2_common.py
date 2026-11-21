"""Shared paths and private configuration for the V2 installation layer."""
from __future__ import annotations

import fcntl
import json
import os
import tempfile
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = Path(os.environ.get("WHATSAPP_ENGINEER_HOME", Path.home() / ".local/share/whatsapp-engineer")).expanduser().resolve()
CONFIG = DATA / "installation.json"
PROFILES = DATA / "profiles.json"
WORKER = ROOT / "workspace/baileys_worker.mjs"


def now():
    return datetime.now(timezone.utc).isoformat()


def read_json(path, default=None):
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    descriptor, temporary = tempfile.mkstemp(dir=path.parent, prefix=".writing-")
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            json.dump(value, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


@contextmanager
def lock(name):
    DATA.mkdir(parents=True, exist_ok=True, mode=0o700)
    with (DATA / (name + ".lock")).open("a") as stream:
        try:
            fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise ValueError("Outra operação está usando estes telefones. Aguarde a conclusão.") from None
        yield


def config():
    value = read_json(CONFIG)
    if value is None:
        raise ValueError("Cadastro pendente. Siga SKILL.md para iniciar a configuração.")
    return value


def select_profiles(slugs=None):
    profiles = [p for p in config()["profiles"] if p.get("enabled", True)]
    if slugs:
        selected = set(slugs)
        missing = selected - {p["slug"] for p in profiles}
        if missing:
            raise ValueError("Telefones não encontrados: " + ", ".join(sorted(missing)))
        profiles = [p for p in profiles if p["slug"] in selected]
    if not profiles:
        raise ValueError("Cadastre pelo menos um telefone.")
    return profiles


def paths(profile):
    directory = DATA / "profiles" / profile["slug"]
    store = directory / "whatsapp-bridge/store"
    return {
        "directory": directory,
        "auth": directory / "auth",
        "db": store / "messages.db",
        "media": store / "media",
        "status": directory / "status.json",
        "qr": directory / "qr.png",
        "process": directory / "process.json",
        "log": directory / "worker.log",
        "token": directory / "admin-token",
    }
