"""Bounded synchronization with the Iago cadence, using the existing worker."""
from __future__ import annotations

import signal
import time
import uuid

from v2_common import DATA, config, lock, now, save_json, select_profiles
from v2_workers import start_one, status_one, stop_one


def run_cycle(slugs=None):
    settings = config()["sync"]
    profiles = select_profiles(slugs)
    with lock("operation"):
        run_id = now().replace(":", "-") + "-" + uuid.uuid4().hex[:8]
        result = {"id": run_id, "started_at": now(), "phase": "running", "samples": []}
        deadline = time.monotonic() + settings["max_minutes"] * 60
        old_handlers = {}

        def interrupted(signum, frame):
            raise InterruptedError("Rodada interrompida. Os dados recebidos foram preservados.")

        try:
            for signum in [signal.SIGINT, signal.SIGTERM]:
                old_handlers[signum] = signal.signal(signum, interrupted)
            starts = [start_one(profile) for profile in profiles]
            result["starts"] = starts
            save_json(DATA / "last-cycle.json", result)
            previous = None
            for sample_number in range(settings["max_samples"]):
                if previous is not None:
                    remaining = deadline - time.monotonic()
                    if remaining <= 0:
                        result["stop_reason"] = "operational_limit"
                        break
                    time.sleep(min(settings["check_seconds"], remaining))
                current = [status_one(profile) for profile in profiles]
                result["samples"].append({"at": now(), "profiles": current})
                result["before_stop"] = current
                save_json(DATA / "last-cycle.json", result)
                wrong_number = [p for p in current if p["number_matches"] is False]
                if wrong_number:
                    result["stop_reason"] = "number_mismatch"
                    break
                if previous is not None:
                    old = {p["slug"]: p for p in previous}
                    stable = all(
                        p["healthy_observed"] and old[p["slug"]]["healthy_observed"]
                        and 0 <= p["db"]["messages"] - old[p["slug"]]["db"]["messages"] <= settings["max_delta"]
                        for p in current
                    )
                    if stable:
                        result["stop_reason"] = "low_flow_observed"
                        break
                if time.monotonic() >= deadline:
                    result["stop_reason"] = "operational_limit"
                    break
                if all(not p["running"] or p["state"] == "qr" for p in current):
                    result["stop_reason"] = "connection_required"
                    break
                previous = current
            else:
                result["stop_reason"] = "sample_limit"
            result["phase"] = "finished"
        except Exception as exc:
            result["phase"] = "error"
            result["error"] = str(exc)
            result["stop_reason"] = "error"
        finally:
            result["stopped"] = []
            for profile in profiles:
                try:
                    result["stopped"].append(stop_one(profile))
                except Exception as exc:
                    result["stopped"].append({"slug": profile["slug"], "stopped": False, "error": str(exc)})
            result["finished_at"] = now()
            result["ok"] = bool(
                result.get("stop_reason") == "low_flow_observed"
                and all(p["stopped"] for p in result["stopped"])
            )
            result["history_coverage"] = "provider_available_history_not_full_phone_guarantee"
            save_json(DATA / "cycles" / (run_id + ".json"), result)
            save_json(DATA / "last-cycle.json", result)
            for signum, handler in old_handlers.items():
                signal.signal(signum, handler)
        return result
