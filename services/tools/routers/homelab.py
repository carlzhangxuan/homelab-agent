"""Homelab control tools: wake, shutdown, metrics."""
import asyncio
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import wakeonlan
import paramiko
from config import settings

router = APIRouter()


class HostAction(BaseModel):
    host: str


@router.post("/wake/{host}")
def wake(host: str):
    cfg = _get_host(host)
    wakeonlan.send_magic_packet(cfg["mac"])
    return {"action": "wake", "host": host}


@router.post("/shutdown/{host}")
def shutdown(host: str):
    cfg = _get_host(host)
    _ssh_run(cfg["ip"], cfg["user"], cfg["ssh_key"], "sudo shutdown -h now")
    return {"action": "shutdown", "host": host}


@router.get("/metrics/{host}")
def metrics(host: str):
    cfg = _get_host(host)
    stdout = _ssh_run(cfg["ip"], cfg["user"], cfg["ssh_key"],
                      "nvidia-smi --query-gpu=temperature.gpu,utilization.gpu,memory.used,memory.total "
                      "--format=csv,noheader,nounits")
    lines = [l.strip() for l in stdout.splitlines() if l.strip()]
    gpus = []
    for i, line in enumerate(lines):
        temp, util, mem_used, mem_total = line.split(", ")
        gpus.append({"index": i, "temp_c": int(temp), "util_pct": int(util),
                     "mem_used_mb": int(mem_used), "mem_total_mb": int(mem_total)})
    return {"host": host, "gpus": gpus}


def _get_host(name: str) -> dict:
    cfg = settings.hosts.get(name)
    if not cfg:
        raise HTTPException(status_code=404, detail=f"host '{name}' not configured")
    return cfg


def _ssh_run(ip: str, user: str, key_path: str, cmd: str) -> str:
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(ip, username=user, key_filename=key_path, timeout=10)
    _, stdout, stderr = client.exec_command(cmd)
    out = stdout.read().decode()
    client.close()
    return out
