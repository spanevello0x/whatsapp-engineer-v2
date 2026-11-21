#!/usr/bin/env python3
"""Agent-facing setup commands. The user-facing wizard is defined in SKILL.md."""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import socket
import subprocess
import sys
import time
import unicodedata
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from v2_common import CONFIG, DATA, PROFILES, ROOT, config, lock, now, paths, read_json, save_json, select_profiles
from v2_workers import owned_process, start_one, status_one, stop_one


def emit(value):
    print(json.dumps(value, ensure_ascii=False, indent=2))


def slugify(value):
    normalized = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", normalized.lower()).strip("-") or "equipe"


def phone_number(value):
    value = str(value).strip()
    if not re.fullmatch(r"\+?[0-9 ()-]+", value):
        raise ValueError("Informe o número do telefone com DDD.")
    digits = re.sub(r"\D", "", value)
    if not value.startswith("+") and len(digits) in [10, 11]:
        digits = "55" + digits
    if not 10 <= len(digits) <= 15:
        raise ValueError("Confira o número com DDD e, para outro país, inclua + e o código do país.")
    return "+" + digits


def available_port(used):
    for port in range(18900, 19900):
        if port in used:
            continue
        with socket.socket() as check:
            try:
                check.bind(("127.0.0.1", port))
            except OSError:
                continue
        return port
    raise ValueError("Não encontrei uma porta local disponível.")


def configure(answers):
    if not isinstance(answers, dict) or not answers.get("phones"):
        raise ValueError("Informe número, pessoa e setor de pelo menos um telefone.")
    with lock("operation"):
        current = read_json(CONFIG, {})
        by_number = {p["number"]: p for p in current.get("profiles", [])}
        seen = set()
        used_ports = {p["admin_port"] for p in by_number.values()}
        for item in answers["phones"]:
            number = phone_number(item.get("number", ""))
            person = str(item.get("person", "")).strip()
            department = str(item.get("department", "")).strip()
            if not person or not department:
                raise ValueError("Cada telefone precisa do nome de quem usa e do setor.")
            if item.get("consent") is not True:
                raise ValueError("Registre a autorização do responsável antes de conectar o telefone.")
            if number in seen:
                raise ValueError("Um número foi informado mais de uma vez.")
            seen.add(number)
            existing = by_number.get(number, {})
            port = existing.get("admin_port") or available_port(used_ports)
            used_ports.add(port)
            by_number[number] = {
                **existing, "slug": existing.get("slug", "phone-" + number[1:]),
                "number": number, "person": person, "department": department,
                "name": person + " — " + department, "project": department,
                "project_slug": slugify(department), "project_folder": slugify(department),
                "consent": True, "consent_recorded_at": existing.get("consent_recorded_at", now()),
                "enabled": True, "admin_port": port,
            }
        sync = {
            "timezone": "America/Sao_Paulo", "start_hour": 6, "end_hour": 22,
            "every_hours": 2, "weekdays_only": False, "check_seconds": 120,
            "max_delta": 19, "max_minutes": 45, "max_samples": 24,
            **current.get("sync", {}), **answers.get("sync", {}),
        }
        for key in ["start_hour", "end_hour", "every_hours", "check_seconds", "max_delta", "max_minutes", "max_samples"]:
            if type(sync[key]) is not int:
                raise ValueError("Parâmetro de horário inválido: " + key)
        if not 0 <= sync["start_hour"] <= sync["end_hour"] <= 23 or sync["every_hours"] not in [1, 2, 4, 6, 12]:
            raise ValueError("Escolha horários entre 00h e 23h no mesmo dia, com intervalo de 1, 2, 4, 6 ou 12 horas.")
        if not 30 <= sync["check_seconds"] <= 600 or not 1 <= sync["max_minutes"] <= 45:
            raise ValueError("A verificação deve ocorrer a cada 30–600 segundos e a rodada deve durar até 45 minutos.")
        if not 2 <= sync["max_samples"] <= 100 or sync["max_delta"] < 0 or type(sync["weekdays_only"]) is not bool:
            raise ValueError("Critério de parada inválido.")
        if not re.fullmatch(r"[A-Za-z_]+/[A-Za-z_]+(?:/[A-Za-z_]+)?|UTC", sync["timezone"]):
            raise ValueError("Fuso inválido.")
        ZoneInfo(sync["timezone"])
        result = {**current, "version": 2, "updated_at": now(), "profiles": list(by_number.values()), "sync": sync,
                  "purpose": str(answers.get("purpose", current.get("purpose", "Acompanhar atendimentos e pendências")))}
        save_json(CONFIG, result)
        profiles = []
        for profile in result["profiles"]:
            profiles.append({**profile, "profile_dir": str(paths(profile)["directory"]), "port": 0,
                             "description": profile["person"] + " — " + profile["department"]})
        save_json(PROFILES, {"version": 1, "profiles_dir": str(DATA / "profiles"), "profiles": profiles})
    return {"ok": True, "config": str(CONFIG), "phones": len(result["profiles"]), "sync": sync}


def doctor():
    node = shutil.which("node")
    sqlite_ok = False
    if node:
        result = subprocess.run([node, "--experimental-sqlite", "--input-type=module", "-e", "import { DatabaseSync } from 'node:sqlite';"],
                                capture_output=True, text=True, timeout=15)
        sqlite_ok = result.returncode == 0
    return {"python": sys.version.split()[0], "node": node, "node_sqlite": sqlite_ok,
            "npm": shutil.which("npm"), "platform": sys.platform, "root": str(ROOT), "data": str(DATA),
            "configured": CONFIG.exists(), "dependencies_present": (ROOT / "node_modules/@whiskeysockets/baileys").exists(),
            "requirements": "Python 3.10+ e Node.js com node:sqlite (22.13+). Linux/systemd ou macOS/launchd para os horários."}


def prepare():
    checks = doctor()
    if not checks["node_sqlite"] or not checks["npm"]:
        raise ValueError("Instale Node.js 22.13+ com npm e execute prepare novamente.")
    with lock("operation"):
        if CONFIG.exists() and any(owned_process(p) for p in config()["profiles"]):
            raise ValueError("Conclua ou pause a conexão dos telefones antes de instalar dependências.")
        subprocess.run([checks["npm"], "ci", "--omit=dev"], cwd=ROOT, check=True, timeout=900,
                       stdout=sys.stderr, stderr=sys.stderr)
        current = read_json(CONFIG, {"version": 2, "profiles": []})
        current["node"] = checks["node"]
        save_json(CONFIG, current)
    return {"ok": True, "node": checks["node"], "root": str(ROOT)}


def next_sync():
    settings = config()["sync"]
    local = datetime.now(ZoneInfo(settings["timezone"]))
    for day in range(8):
        candidate_day = local + timedelta(days=day)
        if settings["weekdays_only"] and candidate_day.weekday() >= 5:
            continue
        for hour in range(settings["start_hour"], settings["end_hour"] + 1, settings["every_hours"]):
            candidate = candidate_day.replace(hour=hour, minute=0, second=0, microsecond=0)
            if candidate > local:
                return candidate.isoformat()


def status(slugs=None):
    from v2_schedule import status as schedule_status
    current = config()
    if "sync" not in current or not current.get("profiles"):
        return {"ok": False, "step": "phone_details_required", "data": str(DATA)}
    return {"profiles": [status_one(p) for p in select_profiles(slugs)],
            "last_cycle": read_json(DATA / "last-cycle.json", {}),
            "schedule": schedule_status(), "next_planned_sync": next_sync(), "timezone": current["sync"]["timezone"]}


def pair(slug, ready):
    if not ready:
        raise ValueError("Aguarde a pessoa confirmar que o celular está pronto para escanear o código QR.")
    profile = select_profiles([slug])[0]
    with lock("operation"):
        result = start_one(profile, pairing=True)
        deadline = time.monotonic() + 20
        while time.monotonic() < deadline:
            result = status_one(profile)
            if result["number_matches"] is False:
                stop_one(profile)
                raise ValueError("O número conectado difere do cadastro. Confira com a pessoa antes de continuar.")
            if result["healthy_observed"] or result["qr"]["fresh"] or not result["running"]:
                return result
            if result["state"] == "close":
                return result
            time.sleep(1)
        return result


def repair_auth(slug, confirmed):
    if not confirmed:
        raise ValueError("Confirme que este telefone precisa de uma nova conexão e que a pessoa está pronta.")
    profile = select_profiles([slug])[0]
    with lock("operation"):
        stopped = stop_one(profile)
        if not stopped["stopped"]:
            raise ValueError("O processo do telefone ainda está encerrando.")
        auth = paths(profile)["auth"]
        if auth.exists():
            backup = DATA / "auth-backups" / profile["slug"] / now().replace(":", "-")
            backup.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
            auth.rename(backup)
        return {"ok": True, "slug": slug, "next": "pair --profile " + slug + " --ready", "history_preserved": True}


def sync_background(slugs):
    record = read_json(DATA / "background-cycle.json", {})
    pid = record.get("pid", 0)
    if pid:
        check = subprocess.run(["ps", "-p", str(pid), "-o", "lstart=", "-o", "args="], capture_output=True, text=True, timeout=5)
        if check.stdout.strip() == record.get("signature"):
            return {"ok": True, "already_running": True, "pid": pid, "progress": str(DATA / "last-cycle.json")}
    args = [sys.executable, str(ROOT / "scripts/onboard.py"), "sync"]
    for slug in slugs or []:
        args.extend(["--profile", slug])
    with (DATA / "cycle.out.log").open("ab") as output:
        process = subprocess.Popen(args, cwd=ROOT, stdout=output, stderr=output, start_new_session=True, umask=0o077)
    signature = subprocess.run(["ps", "-p", str(process.pid), "-o", "lstart=", "-o", "args="], capture_output=True, text=True, timeout=5).stdout.strip()
    save_json(DATA / "background-cycle.json", {"pid": process.pid, "signature": signature, "at": now()})
    return {"ok": True, "pid": process.pid, "progress": str(DATA / "last-cycle.json")}


def main():
    os.umask(0o077)
    parser = argparse.ArgumentParser(description="Instalação assistida do WhatsApp Engineer V2. O agente conduz a conversa usando SKILL.md.")
    parser.add_argument("action", choices=["doctor", "prepare", "configure", "status", "pair", "stop", "repair-auth", "sync", "schedule", "mcp", "search"])
    parser.add_argument("--answers", help="JSON privado, ou - para ler da entrada padrão")
    parser.add_argument("--profile", action="append")
    parser.add_argument("--ready", action="store_true")
    parser.add_argument("--confirmed", action="store_true")
    parser.add_argument("--background", action="store_true")
    parser.add_argument("--install", action="store_true")
    args, remaining = parser.parse_known_args()
    if remaining and args.action != "search":
        parser.error("Argumentos desconhecidos: " + " ".join(remaining))
    try:
        if args.action == "doctor":
            result = doctor()
        elif args.action == "prepare":
            result = prepare()
        elif args.action == "configure":
            if not args.answers:
                raise ValueError("Forneça --answers com o JSON das respostas da conversa.")
            if args.answers == "-":
                answers = json.load(sys.stdin)
            else:
                from pathlib import Path
                answers = read_json(Path(args.answers).expanduser())
            result = configure(answers)
        elif args.action == "status":
            result = status(args.profile)
        elif args.action in ["pair", "repair-auth"]:
            if len(args.profile or []) != 1:
                raise ValueError("Escolha um telefone por vez com --profile.")
            result = pair(args.profile[0], args.ready) if args.action == "pair" else repair_auth(args.profile[0], args.confirmed)
        elif args.action == "stop":
            with lock("operation"):
                result = {"profiles": [stop_one(p) for p in select_profiles(args.profile)]}
        elif args.action == "sync":
            if args.background:
                with lock("background-start"):
                    result = sync_background(args.profile)
            else:
                from v2_cycle import run_cycle
                result = run_cycle(args.profile)
        elif args.action == "schedule":
            from v2_schedule import definition, install
            result = install() if args.install else definition()
        elif args.action == "mcp":
            result = {"command": sys.executable, "args": [str(ROOT / "embedded_mcp/whatsapp_profiles/stdio_server.py")],
                      "env": {"WHATSAPP_MCP_PROFILES_CONFIG": str(PROFILES)}}
        else:
            select_profiles(args.profile)
            command = [sys.executable, str(ROOT / "scripts/search_history.py"), "--profiles-config", str(PROFILES)]
            if args.profile:
                if len(args.profile) != 1:
                    raise ValueError("Busque um telefone por vez ou omita --profile para todos.")
                command.extend(["--profile", args.profile[0]])
            return subprocess.call(command + remaining)
        emit(result)
        return 0
    except (ValueError, OSError, subprocess.SubprocessError) as exc:
        emit({"ok": False, "error": str(exc)})
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
