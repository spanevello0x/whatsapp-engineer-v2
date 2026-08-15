#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SKILL_DIR = Path(__file__).resolve().parents[1]
STATE_DIR = Path.home() / ".openclaw" / "state" / "whatsapp-engineer"
BAILEYS_DIR = STATE_DIR / "baileys"
INSTALL_DIR = STATE_DIR / "install"
PHONE_REGISTRY = STATE_DIR / "phone_registry.json"
INSTALL_PLAN = INSTALL_DIR / "install-plan.json"
QR_HANDOFF = INSTALL_DIR / "qr-handoff.png"

PLACEHOLDER_PNG = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+/p9sAAAAASUVORK5CYII="
)


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def write_private_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.chmod(path, 0o600)


def ask(prompt: str, default: str = "") -> str:
    suffix = f" [{default}]" if default else ""
    print(f"\n{prompt}{suffix}")
    value = input("> ").strip()
    return value if value else default


def ask_bool(prompt: str, default: bool = False) -> bool:
    marker = "Y/n" if default else "y/N"
    print(f"\n{prompt} [{marker}]")
    value = input("> ").strip().lower()
    if not value:
        return default
    return value in {"y", "yes", "s", "sim", "1", "true"}


def ask_choice(prompt: str, choices: list[str], default: str) -> str:
    rendered = "/".join(choices)
    while True:
        value = ask(f"{prompt} ({rendered})", default).lower()
        if value in choices:
            return value
        print(f"Escolha uma opcao valida: {rendered}")


def split_csv(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def sanitize_slug(value: str, fallback: str) -> str:
    slug = "".join(ch.lower() if ch.isalnum() else "-" for ch in value.strip())
    slug = "-".join(part for part in slug.split("-") if part)
    return slug or fallback


def warning_block() -> None:
    print("\nWhatsApp Engineer install wizard")
    print("=" * 34)
    print("Antes do QR, leia isto com calma:")
    print("- Esta skill pode baixar 100% das conversas acessiveis pelo WhatsApp Web do telefone pareado.")
    print("- O historico fica no ambiente local em SQLite, fora do Git, mas ainda e dado sensivel.")
    print("- O agente/sistema que consultar esse banco precisa ter guardrails para nao vazar conversas a terceiros.")
    print("- Nao publique resumos em grupos/canais publicos sem filtro humano e permissao explicita.")
    print("- Sincronia 100% continua pode pesar no VPS/container. Use rotina horaria/diaria quando for suficiente.")
    print("- O dono do telefone precisa consentir com o pareamento e entender a finalidade do monitoramento.")


def collect_interactive() -> dict[str, Any]:
    warning_block()
    accepted = ask("Digite ACEITO para confirmar que entendeu o risco de privacidade", "")
    if accepted.strip().upper() != "ACEITO":
        raise SystemExit("[blocked] Instalacao interrompida antes do QR.")

    operator = ask("Nome de quem esta instalando/conduzindo", "")
    agent_system = ask_choice("Onde o agente vai rodar", ["openclaw", "hermes", "codex", "other"], "openclaw")
    gateway_channel = ask_choice("Por qual gateway o QR deve ser entregue", ["telegram", "whatsapp", "manual"], "manual")
    gateway_target = ask("ID/chat/destino do gateway, ou vazio se manual", "")
    qr_delivery = ask_choice("Como entregar o QR", ["media-line", "copy-path", "custom-command"], "media-line")
    custom_command = ""
    if qr_delivery == "custom-command":
        custom_command = ask("Comando custom com {path} e {message}", "")

    phones: list[dict[str, Any]] = []
    count_raw = ask("Quantos telefones serao documentados agora", "1")
    try:
        count = max(1, int(count_raw))
    except ValueError:
        count = 1
    for index in range(count):
        print(f"\nTelefone {index + 1}/{count}")
        owner = ask("De quem e este telefone", "")
        number = ask("Numero E.164, se puder registrar agora", "")
        label = ask("Nome/slug do perfil", sanitize_slug(owner or f"telefone-{index + 1}", f"telefone-{index + 1}"))
        purpose = ask("Finalidade do monitoramento", "suporte/operacao")
        monitor_scope = ask("Escopo de chats/grupos a monitorar", "todos inicialmente, ajustar depois")
        cadence = ask_choice("Cadencia recomendada", ["continuous", "hourly", "daily", "business-hours", "manual"], "hourly")
        consent = ask_bool("O dono do telefone autorizou o pareamento e monitoramento?", False)
        notes = ask("Notas/limites importantes", "")
        phones.append(
            {
                "owner": owner,
                "number": number,
                "label": label,
                "slug": sanitize_slug(label, f"telefone-{index + 1}"),
                "purpose": purpose,
                "monitor_scope": monitor_scope,
                "cadence": cadence,
                "consent_confirmed": consent,
                "notes": notes,
            }
        )

    install_mode = ask_choice("Modo de instalacao agora", ["plan-only", "generate-qr", "monitor-existing"], "plan-only")
    return {
        "operator": operator,
        "agent_system": agent_system,
        "gateway": {
            "channel": gateway_channel,
            "target": gateway_target,
            "qr_delivery": qr_delivery,
            "custom_command": custom_command,
        },
        "phones": phones,
        "install_mode": install_mode,
    }


def demo_answers() -> dict[str, Any]:
    return {
        "operator": "Demo Operator",
        "agent_system": "openclaw",
        "gateway": {
            "channel": "telegram",
            "target": "TELEGRAM_CHAT_OR_USER_ID",
            "qr_delivery": "media-line",
            "custom_command": "",
        },
        "phones": [
            {
                "owner": "Maria - Suporte",
                "number": "+5500000000000",
                "label": "suporte-maria",
                "slug": "suporte-maria",
                "purpose": "Monitorar suporte e pendencias de clientes.",
                "monitor_scope": "Grupos de suporte e conversas diretas de clientes.",
                "cadence": "hourly",
                "consent_confirmed": True,
                "notes": "Nao publicar conversa bruta em canal de equipe.",
            }
        ],
        "install_mode": "plan-only",
    }


def normalize_answers(raw: dict[str, Any]) -> dict[str, Any]:
    phones = raw.get("phones") or []
    normalized = []
    for index, phone in enumerate(phones):
        label = str(phone.get("label") or phone.get("owner") or f"telefone-{index + 1}")
        cadence = str(phone.get("cadence") or "hourly")
        if cadence not in {"continuous", "hourly", "daily", "business-hours", "manual"}:
            cadence = "hourly"
        normalized.append(
            {
                "owner": str(phone.get("owner") or ""),
                "number": str(phone.get("number") or ""),
                "label": label,
                "slug": sanitize_slug(str(phone.get("slug") or label), f"telefone-{index + 1}"),
                "purpose": str(phone.get("purpose") or "operacao"),
                "monitor_scope": str(phone.get("monitor_scope") or "todos inicialmente, ajustar depois"),
                "cadence": cadence,
                "consent_confirmed": bool(phone.get("consent_confirmed", False)),
                "notes": str(phone.get("notes") or ""),
            }
        )
    if not normalized:
        normalized = demo_answers()["phones"]
    gateway = raw.get("gateway") or {}
    return {
        "operator": str(raw.get("operator") or ""),
        "agent_system": str(raw.get("agent_system") or "openclaw"),
        "gateway": {
            "channel": str(gateway.get("channel") or "manual"),
            "target": str(gateway.get("target") or ""),
            "qr_delivery": str(gateway.get("qr_delivery") or "media-line"),
            "custom_command": str(gateway.get("custom_command") or ""),
        },
        "phones": normalized,
        "install_mode": str(raw.get("install_mode") or "plan-only"),
    }


def cron_suggestions(phones: list[dict[str, Any]]) -> list[dict[str, str]]:
    suggestions: list[dict[str, str]] = []
    seen: set[str] = set()
    for phone in phones:
        cadence = phone["cadence"]
        if cadence in seen:
            continue
        seen.add(cadence)
        if cadence == "continuous":
            suggestions.append(
                {
                    "cadence": "continuous",
                    "use_when": "suporte critico, vendas ativas ou operacao que precisa reagir rapido.",
                    "cron": "nao usar cron para cada mensagem; manter worker ativo e criar digest de controle a cada 15-30 min.",
                }
            )
        elif cadence == "hourly":
            suggestions.append(
                {
                    "cadence": "hourly",
                    "use_when": "operacao normal com risco de sobrecarga se sincronizar tudo em tempo real.",
                    "cron": "0 * * * * whatsapp-engineer digest --period last_1h --profile <slug>",
                }
            )
        elif cadence == "daily":
            suggestions.append(
                {
                    "cadence": "daily",
                    "use_when": "resumo executivo, auditoria leve e acompanhamento sem urgencia.",
                    "cron": "0 8 * * * whatsapp-engineer digest --period yesterday --profile <slug>",
                }
            )
        elif cadence == "business-hours":
            suggestions.append(
                {
                    "cadence": "business-hours",
                    "use_when": "avisos de pendencia durante horario comercial.",
                    "cron": "*/30 9-18 * * 1-5 whatsapp-engineer digest --period last_30m --profile <slug>",
                }
            )
        else:
            suggestions.append(
                {
                    "cadence": "manual",
                    "use_when": "ambiente sensivel, baixa demanda ou teste inicial.",
                    "cron": "sem cron; operador roda busca/resumo sob demanda.",
                }
            )
    return suggestions


def build_plan(answers: dict[str, Any], *, simulate: bool) -> dict[str, Any]:
    phones = answers["phones"]
    consent_missing = [phone["slug"] for phone in phones if not phone["consent_confirmed"]]
    return {
        "version": 1,
        "generated_at": now_iso(),
        "simulate": simulate,
        "operator": answers["operator"],
        "agent_system": answers["agent_system"],
        "privacy_notice": {
            "full_history_download": True,
            "message": "O pareamento pode baixar 100% das conversas acessiveis pelo WhatsApp Web para SQLite local.",
            "required_guardrails": [
                "nao publicar conversa bruta em canal publico",
                "mascarar telefones quando possivel",
                "confirmar destino antes do primeiro envio",
                "limitar quais chats/perfis o agente pode consultar",
                "registrar quem e dono de cada telefone e finalidade",
            ],
        },
        "gateway": answers["gateway"],
        "phones": phones,
        "consent_missing": consent_missing,
        "recommended_sync": {
            "default": "hourly",
            "continuous_warning": "sync 100% continua pode consumir CPU, disco e rede; use so quando o tempo real for necessario.",
            "suggestions": cron_suggestions(phones),
        },
        "next_steps": [
            "instalar dependencias com npm install",
            "rodar python3 workspace/run.py install-wizard --generate-qr quando o operador estiver pronto",
            "entregar o QR imediatamente pelo gateway escolhido",
            "monitorar status ate open/history",
            "validar com status-v2 e uma busca limitada antes de liberar digest automatico",
        ],
    }


def save_phone_registry(phones: list[dict[str, Any]], plan_path: Path) -> None:
    existing = load_json(PHONE_REGISTRY, {"version": 1, "phones": []})
    by_slug = {str(item.get("slug")): item for item in existing.get("phones", []) if item.get("slug")}
    for phone in phones:
        record = dict(phone)
        record["updated_at"] = now_iso()
        record["install_plan"] = str(plan_path)
        by_slug[phone["slug"]] = record
    write_private_json(PHONE_REGISTRY, {"version": 1, "updated_at": now_iso(), "phones": list(by_slug.values())})


def create_placeholder_qr(path: Path) -> None:
    import base64

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(base64.b64decode(PLACEHOLDER_PNG))
    os.chmod(path, 0o600)


def copy_qr_to_handoff(source: Path, simulate: bool) -> Path:
    if simulate:
        create_placeholder_qr(QR_HANDOFF)
        return QR_HANDOFF
    if not source.exists():
        raise FileNotFoundError(f"QR ainda nao encontrado: {source}")
    QR_HANDOFF.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, QR_HANDOFF)
    os.chmod(QR_HANDOFF, 0o600)
    return QR_HANDOFF


def print_qr_delivery(plan: dict[str, Any], qr_path: Path) -> None:
    gateway = plan["gateway"]
    message = "Escaneie este QR pelo WhatsApp > Aparelhos conectados > Conectar aparelho."
    print("\nQR pronto para entrega")
    print(f"Arquivo: {qr_path}")
    if gateway["qr_delivery"] == "media-line":
        print("\nEnvie pelo gateway/canal atual usando:")
        print(f"MEDIA:{qr_path}")
        print(message)
    elif gateway["qr_delivery"] == "copy-path":
        print("\nCopie/anexe manualmente este arquivo no gateway escolhido.")
        print(message)
    elif gateway["qr_delivery"] == "custom-command" and gateway.get("custom_command"):
        cmd = gateway["custom_command"].format(path=str(qr_path), message=message)
        print("\nComando sugerido para entrega custom:")
        print(cmd)
    else:
        print("\nAnexe manualmente o PNG no gateway escolhido.")


def start_connect(wait_seconds: int) -> dict[str, Any]:
    cmd = [sys.executable, str(SKILL_DIR / "workspace" / "run.py"), "connect", "--wait-qr-seconds", str(wait_seconds)]
    proc = subprocess.run(cmd, cwd=str(SKILL_DIR), text=True, capture_output=True, check=False)
    payload: dict[str, Any] = {"returncode": proc.returncode, "stdout": proc.stdout[-4000:], "stderr": proc.stderr[-4000:]}
    try:
        payload["json"] = json.loads(proc.stdout)
    except Exception:
        pass
    return payload


def monitor_status(timeout_seconds: int, interval_seconds: int = 5) -> dict[str, Any]:
    status_path = BAILEYS_DIR / "status.json"
    deadline = time.time() + timeout_seconds
    last: dict[str, Any] = {}
    while time.time() < deadline:
        last = load_json(status_path, {})
        state = last.get("state")
        if state:
            print(json.dumps({"event": "status", "state": state, "status": last}, ensure_ascii=False))
        if state in {"open", "history"}:
            return {"ok": True, "status": last}
        if state == "error":
            return {"ok": False, "status": last}
        time.sleep(interval_seconds)
    return {"ok": False, "timeout": True, "status": last}


def main() -> int:
    parser = argparse.ArgumentParser(description="Guided installer for public WhatsApp Engineer deployments.")
    parser.add_argument("--answers", type=Path, help="JSON answers for non-interactive runs.")
    parser.add_argument("--simulate", action="store_true", help="Simulate the full flow without starting WhatsApp.")
    parser.add_argument("--generate-qr", action="store_true", help="Start the connect flow and prepare the QR handoff.")
    parser.add_argument("--monitor", action="store_true", help="Monitor Baileys status after QR delivery.")
    parser.add_argument("--print-plan", action="store_true", help="Print the generated install plan.")
    parser.add_argument("--wait-qr-seconds", type=int, default=20)
    parser.add_argument("--monitor-timeout-seconds", type=int, default=240)
    args = parser.parse_args()

    if args.answers:
        answers = normalize_answers(load_json(args.answers, {}))
    elif args.simulate:
        answers = normalize_answers(demo_answers())
    else:
        answers = normalize_answers(collect_interactive())

    plan = build_plan(answers, simulate=args.simulate)
    write_private_json(INSTALL_PLAN, plan)
    save_phone_registry(plan["phones"], INSTALL_PLAN)

    print(f"\nPlano salvo em: {INSTALL_PLAN}")
    print(f"Registro de telefones salvo em: {PHONE_REGISTRY}")
    if plan["consent_missing"]:
        print(f"[blocked] Consentimento faltando para: {', '.join(plan['consent_missing'])}")
        print("Registre o consentimento antes de gerar QR real.")

    should_generate_qr = args.generate_qr or answers.get("install_mode") == "generate-qr"
    if args.simulate or should_generate_qr:
        if plan["consent_missing"] and not args.simulate:
            return 2
        if args.simulate:
            qr_path = copy_qr_to_handoff(BAILEYS_DIR / "qr.png", simulate=True)
            print_qr_delivery(plan, qr_path)
        else:
            result = start_connect(args.wait_qr_seconds)
            print(json.dumps({"event": "connect-started", "result": result}, ensure_ascii=False, indent=2))
            qr_path = copy_qr_to_handoff(BAILEYS_DIR / "qr.png", simulate=False)
            print_qr_delivery(plan, qr_path)

    if args.monitor and not args.simulate:
        result = monitor_status(args.monitor_timeout_seconds)
        print(json.dumps({"event": "monitor-complete", "result": result}, ensure_ascii=False, indent=2))
    elif args.monitor and args.simulate:
        print(json.dumps({"event": "monitor-complete", "result": {"ok": True, "status": {"state": "simulated-open"}}}, ensure_ascii=False))

    print("\nSugestoes de cron/usabilidade:")
    for suggestion in plan["recommended_sync"]["suggestions"]:
        print(f"- {suggestion['cadence']}: {suggestion['use_when']} | {suggestion['cron']}")

    if args.print_plan:
        print(json.dumps(plan, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
