from prometheus_client import Gauge, CollectorRegistry, generate_latest, CONTENT_TYPE_LATEST
from store import store
from config import settings

_reg = CollectorRegistry()

_g = {
    "online":      Gauge("homelab_host_online",          "1 if host reachable", ["host"], registry=_reg),
    "cpu_temp":    Gauge("homelab_cpu_temp_celsius",     "CPU package temp",    ["host"], registry=_reg),
    "cpu_pct":     Gauge("homelab_cpu_usage_percent",    "CPU usage %",         ["host"], registry=_reg),
    "mem_pct":     Gauge("homelab_memory_usage_percent", "Memory usage %",      ["host"], registry=_reg),
    "mem_used":    Gauge("homelab_memory_used_mb",       "Memory used MB",      ["host"], registry=_reg),
    "gpu_temp":    Gauge("homelab_gpu_temp_celsius",     "GPU temp",            ["host", "index", "name"], registry=_reg),
    "gpu_power":   Gauge("homelab_gpu_power_watts",      "GPU power draw",      ["host", "index", "name"], registry=_reg),
    "gpu_util":    Gauge("homelab_gpu_util_percent",     "GPU utilization %",   ["host", "index", "name"], registry=_reg),
    "gpu_mem_pct": Gauge("homelab_gpu_memory_percent",   "GPU memory usage %",  ["host", "index", "name"], registry=_reg),
    "ssd_temp":    Gauge("homelab_ssd_temp_celsius",     "SSD composite temp",  ["host", "index"], registry=_reg),
    "dimm_temp":   Gauge("homelab_dimm_temp_celsius",    "DDR5 DIMM temp",      ["host", "index"], registry=_reg),
}

# Track registered multi-label combos per host so we can remove them when a host goes offline.
_gpu_labels:  dict[str, list[dict]] = {}
_ssd_counts:  dict[str, int] = {}
_dimm_counts: dict[str, int] = {}

_NAN = float("nan")


def _clear_offline(host: str) -> None:
    for g in ("cpu_temp", "cpu_pct", "mem_pct", "mem_used"):
        _g[g].labels(host=host).set(_NAN)
    for lbl in _gpu_labels.pop(host, []):
        for g in ("gpu_temp", "gpu_power", "gpu_util", "gpu_mem_pct"):
            try:
                _g[g].remove(lbl["host"], lbl["index"], lbl["name"])
            except Exception:
                pass
    for i in range(_ssd_counts.pop(host, 0)):
        try:
            _g["ssd_temp"].remove(host, str(i))
        except Exception:
            pass
    for i in range(_dimm_counts.pop(host, 0)):
        try:
            _g["dimm_temp"].remove(host, str(i))
        except Exception:
            pass


def build_metrics() -> str:
    for host in settings.hosts:
        snap = store.latest(host)
        if not snap:
            continue
        online = snap.get("online", True)
        _g["online"].labels(host=host).set(1 if online else 0)
        if not online:
            _clear_offline(host)
            continue
        if snap.get("cpu_package_c") is not None:
            _g["cpu_temp"].labels(host=host).set(snap["cpu_package_c"])
        if snap.get("cpu_pct") is not None:
            _g["cpu_pct"].labels(host=host).set(snap["cpu_pct"])
        mem = snap.get("memory", {})
        if mem.get("pct") is not None:
            _g["mem_pct"].labels(host=host).set(mem["pct"])
            _g["mem_used"].labels(host=host).set(mem.get("used_mb", 0))
        gpu_lbls = []
        for gpu in snap.get("gpus", []):
            lbl = dict(host=host, index=str(gpu["index"]), name=gpu["name"])
            gpu_lbls.append(lbl)
            _g["gpu_temp"].labels(**lbl).set(gpu["temp_c"])
            _g["gpu_power"].labels(**lbl).set(gpu["power_w"])
            _g["gpu_util"].labels(**lbl).set(gpu["util_pct"])
            _g["gpu_mem_pct"].labels(**lbl).set(gpu["mem_pct"])
        _gpu_labels[host] = gpu_lbls
        ssds = snap.get("ssd_c", [])
        for i, t in enumerate(ssds):
            _g["ssd_temp"].labels(host=host, index=str(i)).set(t)
        _ssd_counts[host] = len(ssds)
        dimms = snap.get("memory_dimm_c", [])
        for i, t in enumerate(dimms):
            _g["dimm_temp"].labels(host=host, index=str(i)).set(t)
        _dimm_counts[host] = len(dimms)

    return generate_latest(_reg).decode()
