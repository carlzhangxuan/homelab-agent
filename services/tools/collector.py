import asyncio
import json
import logging
import time

from config import settings
from store import store
from routers.homelab import _ssh_exec_stdin, _METRICS_SCRIPT

logger = logging.getLogger(__name__)
INTERVAL = 5


async def collect_loop():
    while True:
        tasks = [
            asyncio.to_thread(_collect_one, name, cfg)
            for name, cfg in settings.hosts.items()
        ]
        await asyncio.gather(*tasks, return_exceptions=True)
        await asyncio.sleep(INTERVAL)


def _collect_one(host: str, cfg: dict):
    try:
        raw = _ssh_exec_stdin(cfg["ip"], cfg["user"], cfg["ssh_key"],
                              "python3 -", _METRICS_SCRIPT)
        data = json.loads(raw.strip())
        data["ts"] = time.time()
        store.push(host, data)
    except Exception as e:
        logger.warning("collect %s failed: %s", host, e)
