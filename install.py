#!/usr/bin/env python3
"""Copy the complete package to a stable location and register its skill."""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

SOURCE = Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser(description="Instale o pacote e inicie a conversa descrita em SKILL.md.")
    parser.add_argument("--agent", required=True, choices=["hermes", "openclaw", "codex", "claude", "other"])
    args = parser.parse_args()
    os.umask(0o077)
    if sys.version_info < (3, 10) or os.name != "posix":
        raise ValueError("Use Python 3.10+ em Linux ou macOS. Em outro ambiente, conduza a instalação em uma VPS Linux.")
    data = Path(os.environ.get("WHATSAPP_ENGINEER_HOME", Path.home() / ".local/share/whatsapp-engineer")).expanduser().resolve()
    destination = data / "app"
    homes = {
        "hermes": Path(os.environ.get("HERMES_HOME", Path.home() / ".hermes")) / "skills",
        "openclaw": Path(os.environ.get("OPENCLAW_STATE_DIR", Path.home() / ".openclaw")) / "skills",
        "codex": Path.home() / ".agents/skills",
        "claude": Path.home() / ".claude/skills",
    }
    link = homes[args.agent].expanduser() / "whatsapp-engineer" if args.agent in homes else None
    if link and link.exists() and link.resolve() != destination:
        raise ValueError(f"Já existe uma skill em {link}. Preserve a instalação existente e resolva a troca antes de continuar.")
    data.mkdir(parents=True, exist_ok=True, mode=0o700)
    if SOURCE != destination:
        for record in data.glob("profiles/*/process.json"):
            pid = json.loads(record.read_text()).get("pid", 0)
            if not isinstance(pid, int) or pid <= 0:
                continue
            result = subprocess.run(["ps", "-p", str(pid), "-o", "args="], capture_output=True, text=True, timeout=5)
            if "baileys_worker.mjs" in result.stdout:
                raise ValueError("Encerre a rodada desta instalação antes de atualizar seus arquivos.")
        stage = Path(tempfile.mkdtemp(prefix="install-", dir=data)) / "app"
        try:
            shutil.copytree(SOURCE, stage, ignore=shutil.ignore_patterns(
                ".git", "node_modules", "__pycache__", "*.pyc", ".env", ".env.*", "dist", "*.zip",
            ))
            if destination.exists():
                stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
                destination.rename(data / ("app-before-" + stamp))
            stage.rename(destination)
        finally:
            shutil.rmtree(stage.parent, ignore_errors=True)
    if link:
        link.parent.mkdir(parents=True, exist_ok=True)
        if not link.exists():
            if link.is_symlink():
                link.unlink()
            link.symlink_to(destination, target_is_directory=True)
    print(json.dumps({"ok": True, "agent": args.agent, "skill": str(link) if link else None,
                      "app": str(destination), "data": str(data),
                      "next": "Leia SKILL.md no destino e inicie a instalação guiada na conversa.",
                      "prepare": [sys.executable, str(destination / "scripts/onboard.py"), "prepare"]},
                     ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValueError, OSError, subprocess.SubprocessError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False))
        raise SystemExit(2)
