import json
from fastapi import APIRouter, HTTPException
import wakeonlan
from config import settings
from store import store
from ssh import ssh_run
from collector import METRICS_SCRIPT

router = APIRouter()


@router.post("/wake/{host}")
def wake(host: str):
    cfg = _get_host(host)
    if "mac" not in cfg:
        raise HTTPException(status_code=400, detail=f"host '{host}' does not support wake-on-lan")
    wakeonlan.send_magic_packet(cfg["mac"])
    return {"action": "wake", "host": host}


@router.post("/shutdown/{host}")
def shutdown(host: str):
    cfg = _get_host(host)
    if "mac" not in cfg:
        raise HTTPException(status_code=400, detail=f"host '{host}' does not support shutdown")
    ssh_run(cfg["ip"], cfg["user"], cfg["ssh_key"], "sudo shutdown -h now")
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
