import json
import os
from fastapi import APIRouter, HTTPException
import wakeonlan
import paramiko
from config import settings

router = APIRouter()

_METRICS_SCRIPT = """
import os, json, glob, subprocess

def hwmon_sensors():
    result = {'cpu_package_c': None, 'cpu_cores_c': [], 'ssd_c': [], 'ambient_c': None}
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
        elif name == 'nvme':
            c = temps.get('Composite')
            if c is not None:
                result['ssd_c'].append(c)
        elif name == 'dell_smm':
            result['ambient_c'] = temps.get('Ambient')
    return result

def gpu_metrics():
    try:
        out = subprocess.check_output(
            ['nvidia-smi',
             '--query-gpu=index,name,temperature.gpu,utilization.gpu,memory.used,memory.total',
             '--format=csv,noheader,nounits'], text=True)
        gpus = []
        for line in out.strip().splitlines():
            idx, name, temp, util, mem_used, mem_total = [x.strip() for x in line.split(',')]
            gpus.append({'index': int(idx), 'name': name, 'temp_c': int(temp),
                         'util_pct': int(util), 'mem_used_mb': int(mem_used),
                         'mem_total_mb': int(mem_total)})
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
    return {'total_mb': total, 'used_mb': total - available, 'available_mb': available}

print(json.dumps({**hwmon_sensors(), 'gpus': gpu_metrics(), 'memory': memory_metrics()}))
"""


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
    _ssh_exec(cfg["ip"], cfg["user"], cfg["ssh_key"], "sudo shutdown -h now")
    return {"action": "shutdown", "host": host}


@router.get("/metrics/{host}")
def metrics(host: str):
    cfg = _get_host(host)
    stdout = _ssh_exec_stdin(cfg["ip"], cfg["user"], cfg["ssh_key"],
                             "python3 -", _METRICS_SCRIPT)
    data = json.loads(stdout.strip())
    return {"host": host, **data}


def _get_host(name: str) -> dict:
    cfg = settings.hosts.get(name)
    if not cfg:
        raise HTTPException(status_code=404, detail=f"host '{name}' not configured")
    return cfg


def _ssh_exec(ip: str, user: str, key_path: str, cmd: str) -> str:
    key_path = os.path.expanduser(key_path)
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(ip, username=user, key_filename=key_path, timeout=10)
    _, stdout, _ = client.exec_command(cmd)
    out = stdout.read().decode()
    client.close()
    return out


def _ssh_exec_stdin(ip: str, user: str, key_path: str, cmd: str, stdin_data: str) -> str:
    key_path = os.path.expanduser(key_path)
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(ip, username=user, key_filename=key_path, timeout=30)
    stdin, stdout, _ = client.exec_command(cmd)
    stdin.write(stdin_data)
    stdin.channel.shutdown_write()
    out = stdout.read().decode()
    client.close()
    return out
