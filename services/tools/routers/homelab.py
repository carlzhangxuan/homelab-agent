import ipaddress
import json
import os
import shlex
import time
from fastapi import APIRouter, Body, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import wakeonlan
from config import settings
from store import store
from ssh import ssh_run
from collector import METRICS_SCRIPT

router = APIRouter()


class ShutdownRequest(BaseModel):
    sudo_password: str = ""


class WakeRequest(BaseModel):
    wait_timeout_s: int = Field(default=90, ge=10, le=180)
    poll_interval_s: int = Field(default=5, ge=2, le=10)


@router.post("/wake/{host}")
def wake(host: str, req: WakeRequest = Body(default_factory=WakeRequest)):
    cfg = _get_host(host)
    if "mac" not in cfg:
        raise HTTPException(status_code=400, detail=f"host '{host}' does not support wake-on-lan")

    if _is_host_online(host, cfg):
        return {"action": "wake", "host": host, "already_online": True, "online": True}

    # Use directed broadcast (192.168.x.255) so magic packets route correctly from inside
    # Docker bridge network; global 255.255.255.255 is swallowed by the Docker bridge.
    broadcast = _directed_broadcast(cfg.get("ip", ""), cfg.get("broadcast"))
    for _ in range(3):
        wakeonlan.send_magic_packet(cfg["mac"], ip_address=broadcast)
        time.sleep(0.4)

    start = time.monotonic()
    while time.monotonic() - start < req.wait_timeout_s:
        if _is_host_online(host, cfg):
            elapsed = int(time.monotonic() - start)
            return {"action": "wake", "host": host, "online": True, "elapsed_s": elapsed}
        time.sleep(req.poll_interval_s)

    return JSONResponse(
        status_code=202,
        content={
            "action": "wake",
            "host": host,
            "online": False,
            "detail": f"{host} is still booting after {req.wait_timeout_s}s",
        },
    )


@router.post("/shutdown/{host}")
def shutdown(host: str, req: ShutdownRequest | None = None):
    cfg = _get_host(host)
    if "mac" not in cfg:
        raise HTTPException(status_code=400, detail=f"host '{host}' does not support shutdown")

    # Run power-off deferred in background so SSH can exit cleanly before the machine drops.
    power_cmd = "nohup sh -c 'sleep 1; systemctl poweroff 2>/dev/null || shutdown -h now' >/dev/null 2>&1 &"
    if req and req.sudo_password:
        cmd = f"sudo -S -p '' sh -c {shlex.quote(power_cmd)}"
        stdin_data = req.sudo_password + "\n"
    else:
        cmd = f"sudo -n sh -c {shlex.quote(power_cmd)}"
        stdin_data = ""

    try:
        ssh_run(cfg["ip"], cfg["user"], cfg["ssh_key"], cmd, stdin_data=stdin_data)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"shutdown failed for '{host}': {e}") from e
    return {"action": "shutdown", "host": host}


@router.get("/metrics/{host}")
def metrics(host: str):
    snap = store.latest(host)
    if snap:
        return {"host": host, **snap}
    cfg = _get_host(host)
    raw = ssh_run(cfg["ip"], cfg["user"], cfg["ssh_key"], "python3 -", METRICS_SCRIPT)
    return {"host": host, **json.loads(raw.strip())}


@router.get("/metrics/{host}/history")
def metrics_history(host: str):
    _get_host(host)
    return {
        "host": host,
        "interval_s": 5,
        "window_s": 300,
        "history": store.history(host),
    }


def _get_host(name: str) -> dict:
    cfg = settings.hosts.get(name)
    if not cfg:
        raise HTTPException(status_code=404, detail=f"host '{name}' not configured")
    return cfg


def _directed_broadcast(ip: str, override: str | None = None) -> str:
    if override:
        return override
    try:
        return str(ipaddress.ip_network(f"{ip}/24", strict=False).broadcast_address)
    except Exception:
        return "255.255.255.255"


def _is_host_online(host: str, cfg: dict) -> bool:
    snap = store.latest(host)
    if snap and snap.get("online"):
        return True
    if cfg.get("local"):
        return True
    if "ip" not in cfg:
        return False
    try:
        ssh_run(cfg["ip"], cfg["user"], cfg["ssh_key"], "true", timeout=4)
        return True
    except Exception:
        return False
