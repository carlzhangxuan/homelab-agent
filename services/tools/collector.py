import asyncio
import json
import logging
import time

from config import settings
from store import store, WINDOW
from ssh import ssh_run

logger = logging.getLogger(__name__)

INTERVAL = 5  # seconds between collections; WINDOW * INTERVAL = history duration

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
        raw = ssh_run(cfg["ip"], cfg["user"], cfg["ssh_key"], "python3 -", METRICS_SCRIPT)
        data = json.loads(raw.strip())
        data["ts"] = time.time()
        store.push(host, data)
    except Exception as e:
        logger.warning("collect %s failed: %s", host, e)
