import asyncio
import json
import logging
import re
import time

from config import settings
from store import store, WINDOW
from ssh import ssh_run

logger = logging.getLogger(__name__)

INTERVAL = 5  # seconds; WINDOW * INTERVAL = history duration

METRICS_SCRIPT = """
import os, json, glob, subprocess, time

def hwmon_sensors():
    result = {'cpu_package_c': None, 'cpu_cores_c': [], 'ssd_c': [],
              'ambient_c': None, 'memory_dimm_c': []}
    for hwmon in sorted(glob.glob('/sys/class/hwmon/hwmon*')):
        name_f = f'{hwmon}/name'
        name = open(name_f).read().strip() if os.path.exists(name_f) else ''
        temps = {}
        for f in sorted(glob.glob(f'{hwmon}/temp*_input')):
            try:
                label_f = f.replace('_input', '_label')
                label = open(label_f).read().strip() if os.path.exists(label_f) else 'unlabeled'
                val = round(int(open(f).read().strip()) / 1000, 1)
                temps[label] = val
            except Exception:
                pass
        if name == 'coretemp':
            result['cpu_package_c'] = temps.get('Package id 0')
            result['cpu_cores_c'] = [v for k, v in temps.items() if k.startswith('Core')]
        elif name == 'k10temp':
            result['cpu_package_c'] = temps.get('Tctl')
            result['cpu_cores_c'] = [v for k, v in temps.items() if k.startswith('Tccd')]
        elif name == 'nvme':
            c = temps.get('Composite')
            if c is not None:
                result['ssd_c'].append(c)
        elif name == 'dell_smm':
            result['ambient_c'] = temps.get('Ambient')
        elif name == 'spd5118':
            v = next(iter(temps.values()), None)
            if v is not None:
                result['memory_dimm_c'].append(v)
    return result

def cpu_usage():
    def read_stat():
        with open('/proc/stat') as f:
            vals = list(map(int, f.readline().split()[1:8]))
        idle = vals[3] + vals[4]
        return idle, sum(vals)
    idle1, total1 = read_stat()
    time.sleep(0.5)
    idle2, total2 = read_stat()
    delta = total2 - total1
    return round((1 - (idle2 - idle1) / delta) * 100, 1) if delta else 0.0

def gpu_metrics():
    try:
        out = subprocess.check_output(
            ['nvidia-smi',
             '--query-gpu=index,name,temperature.gpu,utilization.gpu,'
             'memory.used,memory.total,power.draw',
             '--format=csv,noheader,nounits'], text=True)
        gpus = []
        for line in out.strip().splitlines():
            idx, name, temp, util, mem_used, mem_total, power = [x.strip() for x in line.split(',')]
            gpus.append({
                'index': int(idx), 'name': name,
                'temp_c': int(temp), 'util_pct': int(util),
                'mem_used_mb': int(mem_used), 'mem_total_mb': int(mem_total),
                'mem_pct': round(int(mem_used) / int(mem_total) * 100, 1),
                'power_w': round(float(power), 1),
            })
        return gpus
    except Exception:
        return []

def memory_metrics():
    m = {}
    with open('/proc/meminfo') as f:
        for line in f:
            parts = line.split(':', 1)
            if len(parts) == 2:
                m[parts[0].strip()] = int(parts[1].split()[0])
    total = m.get('MemTotal', 0) // 1024
    available = m.get('MemAvailable', 0) // 1024
    used = total - available
    return {'total_mb': total, 'used_mb': used, 'available_mb': available,
            'pct': round(used / total * 100, 1) if total else 0.0}

print(json.dumps({
    **hwmon_sensors(),
    'cpu_pct': cpu_usage(),
    'gpus': gpu_metrics(),
    'memory': memory_metrics(),
}))
"""


def _collect_local() -> dict:
    import psutil
    cpu_pct = psutil.cpu_percent(interval=0.5)
    mem = psutil.virtual_memory()
    return {
        'cpu_package_c': None,
        'cpu_cores_c': [],
        'ssd_c': [],
        'ambient_c': None,
        'memory_dimm_c': [],
        'cpu_pct': round(cpu_pct, 1),
        'gpus': [],
        'memory': {
            'total_mb': mem.total // 1024 // 1024,
            'used_mb': mem.used // 1024 // 1024,
            'available_mb': mem.available // 1024 // 1024,
            'pct': round(mem.percent, 1),
        },
    }


def _parse_battery(out: str) -> dict:
    m = re.search(r'(\d+)%;\s*([\w\s]+?);', out)
    if not m:
        return {}
    return {"battery_pct": int(m.group(1)), "battery_state": m.group(2).strip()}


def _mb(token: str) -> int:
    m = re.match(r'(\d+(?:\.\d+)?)([KMGT]?)', token)
    if not m:
        return 0
    val = float(m.group(1))
    mult = {"": 1/1024/1024, "K": 1/1024, "M": 1, "G": 1024, "T": 1024*1024}[m.group(2)]
    return int(val * mult)


def _parse_macos_probe(out: str) -> dict:
    data = {}
    cpu = re.search(r'CPU usage:.*?(\d+(?:\.\d+)?)%\s*idle', out)
    if cpu:
        data["cpu_pct"] = round(100 - float(cpu.group(1)), 1)
    used_m = re.search(r'PhysMem:\s*(\S+)\s*used', out)
    unused_m = re.search(r'(\S+)\s*unused', out)
    if used_m and unused_m:
        used_mb = _mb(used_m.group(1))
        unused_mb = _mb(unused_m.group(1))
        total_mb = used_mb + unused_mb
        data["memory"] = {
            "total_mb": total_mb,
            "used_mb": used_mb,
            "available_mb": unused_mb,
            "pct": round(used_mb / total_mb * 100, 1) if total_mb else 0.0,
        }
    data.update(_parse_battery(out))
    return data


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
        if cfg.get("local"):
            data = _collect_local()
        elif cfg.get("ping_only"):
            if cfg.get("battery"):
                out = ssh_run(cfg["ip"], cfg["user"], cfg["ssh_key"],
                              'top -l 1 -n 0 | grep -E "^(CPU|PhysMem)"; pmset -g batt',
                              timeout=6)
                data = _parse_macos_probe(out)
            else:
                ssh_run(cfg["ip"], cfg["user"], cfg["ssh_key"], "true", timeout=4)
                data = {}
        else:
            raw = ssh_run(cfg["ip"], cfg["user"], cfg["ssh_key"], "python3 -", METRICS_SCRIPT)
            data = json.loads(raw.strip())
        data["ts"] = time.time()
        data["online"] = True
        store.push(host, data)
    except Exception as e:
        logger.warning("collect %s failed: %s", host, e)
        store.push(host, {"online": False, "ts": time.time()})
