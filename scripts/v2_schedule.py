"""Install the bounded cycle in a user systemd timer or a macOS LaunchAgent."""
from __future__ import annotations

import os
import platform
import plistlib
import subprocess
import sys
from pathlib import Path

from v2_common import DATA, ROOT, config, now, save_json

NAME = "whatsapp-engineer-v2"
MAC_NAME = "com.whatsapp-engineer.v2"


def scheduler_env():
    environment = dict(os.environ)
    runtime = Path("/run/user") / str(os.getuid())
    if runtime.exists():
        environment.setdefault("XDG_RUNTIME_DIR", str(runtime))
        environment.setdefault("DBUS_SESSION_BUS_ADDRESS", "unix:path=" + str(runtime / "bus"))
    return environment


def command(args, check=True):
    result = subprocess.run(args, env=scheduler_env(), capture_output=True, text=True, timeout=30)
    if check and result.returncode:
        raise ValueError((result.stderr or result.stdout).strip())
    return result


def systemd_quote(value):
    return '"' + str(value).replace("\\", "\\\\").replace('"', '\\"').replace("%", "%%") + '"'


def definition():
    settings = config()["sync"]
    hours = list(range(settings["start_hour"], settings["end_hour"] + 1, settings["every_hours"]))
    program = [sys.executable, str(ROOT / "scripts/onboard.py"), "sync"]
    environment = {"WHATSAPP_ENGINEER_HOME": str(DATA), "PATH": os.environ.get("PATH", "/usr/bin:/bin")}
    if platform.system() == "Linux":
        directory = Path.home() / ".config/systemd/user"
        days = "Mon..Fri " if settings["weekdays_only"] else ""
        calendar = days + "*-*-* " + ",".join(f"{hour:02d}" for hour in hours) + ":00:00 " + settings["timezone"]
        service = "\n".join([
            "[Unit]", "Description=WhatsApp Engineer V2 bounded synchronization", "",
            "[Service]", "Type=oneshot", "UMask=0077",
            "WorkingDirectory=" + systemd_quote(ROOT),
            *["Environment=" + systemd_quote(key + "=" + value) for key, value in environment.items()],
            "ExecStart=" + " ".join(systemd_quote(item) for item in program),
            "TimeoutStartSec=50min", "KillMode=control-group", "",
        ])
        timer = "\n".join([
            "[Unit]", "Description=WhatsApp Engineer V2 scheduled synchronization", "",
            "[Timer]", "OnCalendar=" + calendar, "Persistent=false", "AccuracySec=1min",
            "Unit=" + NAME + ".service", "", "[Install]", "WantedBy=timers.target", "",
        ])
        return {"kind": "systemd", "files": {
            str(directory / (NAME + ".service")): service,
            str(directory / (NAME + ".timer")): timer,
        }, "calendar": calendar}
    if platform.system() == "Darwin":
        # launchd calendar entries use the machine timezone. Refuse a silent offset.
        from datetime import datetime
        from zoneinfo import ZoneInfo
        reference = datetime.now().astimezone()
        if reference.utcoffset() != datetime.now(ZoneInfo(settings["timezone"])).utcoffset():
            raise ValueError("O fuso do Mac difere do horário escolhido. Use um servidor com esse fuso ou ajuste a escolha.")
        entries = []
        for hour in hours:
            if settings["weekdays_only"]:
                entries.extend({"Hour": hour, "Minute": 0, "Weekday": day} for day in range(1, 6))
            else:
                entries.append({"Hour": hour, "Minute": 0})
        payload = {
            "Label": MAC_NAME, "ProgramArguments": program,
            "EnvironmentVariables": environment, "StartCalendarInterval": entries,
            "StandardOutPath": str(DATA / "schedule.out.log"),
            "StandardErrorPath": str(DATA / "schedule.error.log"), "Umask": 0o077,
        }
        path = Path.home() / "Library/LaunchAgents" / (MAC_NAME + ".plist")
        return {"kind": "launchd", "files": {str(path): plistlib.dumps(payload).decode()}, "hours": hours}
    raise ValueError("Instale a sincronização em uma VPS Linux ou em um Mac ligado nos horários escolhidos.")


def status():
    if platform.system() == "Linux":
        result = command(["systemctl", "--user", "show", NAME + ".timer", "--property=LoadState,ActiveState,NextElapseUSecRealtime"], check=False)
        details = dict(line.split("=", 1) for line in result.stdout.splitlines() if "=" in line)
        linger = command(["loginctl", "show-user", str(os.getuid()), "--property=Linger", "--value"], check=False)
        return {"kind": "systemd", "active": details.get("ActiveState") == "active", "details": details,
                "survives_logout": linger.stdout.strip() == "yes", "error": result.stderr.strip()}
    if platform.system() == "Darwin":
        result = command(["launchctl", "print", f"gui/{os.getuid()}/{MAC_NAME}"], check=False)
        return {"kind": "launchd", "active": result.returncode == 0, "requires_logged_in_user": True,
                "error": result.stderr.strip()}
    return {"active": False, "error": "Agendamento requer Linux/systemd ou macOS/launchd."}


def install():
    plan = definition()
    DATA.mkdir(parents=True, exist_ok=True, mode=0o700)
    for name, content in plan["files"].items():
        path = Path(name)
        if path.exists() and path.read_text() != content:
            # Preserve this package's previous definition before replacing it.
            save_json(DATA / "schedule-previous.json", {"path": name, "content": path.read_text(), "at": now()})
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
        path.chmod(0o600)
    if plan["kind"] == "systemd":
        command(["systemctl", "--user", "daemon-reload"])
        command(["systemctl", "--user", "enable", "--now", NAME + ".timer"])
        command(["systemctl", "--user", "restart", NAME + ".timer"])
    else:
        path = next(iter(plan["files"]))
        command(["launchctl", "bootout", f"gui/{os.getuid()}/{MAC_NAME}"], check=False)
        command(["launchctl", "bootstrap", f"gui/{os.getuid()}", path])
    result = status()
    save_json(DATA / "schedule.json", {"at": now(), "plan": plan, "status": result})
    return result
