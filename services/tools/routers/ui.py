from fastapi import APIRouter
from fastapi.responses import HTMLResponse
from config import settings
from store import store

router = APIRouter()

_PAGE = """<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <meta http-equiv="refresh" content="5">
  <title>Homelab</title>
  <style>
    body { font-family: monospace; background: #111; color: #eee; padding: 2rem; }
    h1 { color: #7df; margin-bottom: 1.5rem; }
    table { border-collapse: collapse; width: 100%; }
    th { text-align: left; color: #7df; padding: 0.5rem 1rem; border-bottom: 1px solid #333; }
    td { padding: 0.5rem 1rem; border-bottom: 1px solid #222; }
    .online  { color: #4f4; }
    .offline { color: #f44; }
    .na      { color: #666; }
    button { background: #333; color: #eee; border: 1px solid #555; padding: 0.3rem 0.8rem;
             border-radius: 3px; cursor: pointer; margin: 0 2px; }
    button:hover { background: #444; }
    button.wake { border-color: #4f4; }
    button.shutdown { border-color: #f84; }
    #toast { position: fixed; bottom: 2rem; right: 2rem; padding: 0.6rem 1.2rem;
             border-radius: 4px; font-family: monospace; font-size: 0.9rem;
             opacity: 0; transition: opacity 0.3s; pointer-events: none; }
    #toast.show { opacity: 1; }
    #toast.ok  { background: #1a3a1a; border: 1px solid #4f4; color: #4f4; }
    #toast.err { background: #3a1a1a; border: 1px solid #f44; color: #f44; }
  </style>
</head>
<body>
  <h1>Homelab</h1>
  <div id="toast"></div>
  <table>
    <tr>
      <th>Host</th><th>Status</th><th>CPU%</th><th>CPU°C</th>
      <th>Mem%</th><th>GPU°C</th><th>GPU W</th><th>SSD°C</th><th>Actions</th>
    </tr>
    {rows}
  </table>
  <script>
    let _toastTimer = null;
    function toast(msg, type) {
      const el = document.getElementById('toast');
      el.textContent = msg;
      el.className = 'show ' + type;
      if (_toastTimer) clearTimeout(_toastTimer);
      _toastTimer = setTimeout(() => { el.className = ''; }, 3000);
    }

    async function postOrThrow(url, body) {
      const options = {method: 'POST'};
      if (body !== undefined) {
        options.headers = {'Content-Type': 'application/json'};
        options.body = JSON.stringify(body);
      }
      const resp = await fetch(url, options);
      if (!resp.ok) {
        let msg = resp.status + ' ' + resp.statusText;
        try {
          const data = await resp.json();
          if (data && data.detail) msg = data.detail;
        } catch (_) {}
        throw new Error(msg);
      }
      try {
        return await resp.json();
      } catch (_) {
        return {};
      }
    }
    async function wake(host) {
      try {
        const result = await postOrThrow('/homelab/wake/' + host, {wait_timeout_s: 90, poll_interval_s: 5});
        if (result && result.online) {
          const elapsed = (result.elapsed_s !== undefined) ? (' in ~' + result.elapsed_s + 's') : '';
          toast(host + ' is online' + elapsed, 'ok');
        } else if (result && result.detail) {
          toast(result.detail, 'ok');
        } else {
          toast('Wake sent: ' + host, 'ok');
        }
      } catch (e) {
        toast('Wake failed: ' + e.message, 'err');
      }
    }
    async function shutdown(host) {
      try {
        const sudoPassword = prompt('Shutdown ' + host + '\\nInput sudo password (leave blank if passwordless sudo):', '');
        if (sudoPassword === null) return;
        await postOrThrow('/homelab/shutdown/' + host, {sudo_password: sudoPassword});
        toast('Shutdown sent: ' + host, 'ok');
      } catch (e) {
        toast('Shutdown failed: ' + e.message, 'err');
      }
    }
  </script>
</body>
</html>"""


def _row(host: str, cfg: dict) -> str:
    snap = store.latest(host)
    can_wake = "mac" in cfg

    if not snap:
        status = '<span class="na">-</span>'
        cells = ['<td class="na">-</td>'] * 7
    elif not snap.get("online", True):
        status = '<span class="offline">offline</span>'
        cells = ['<td class="na">-</td>'] * 7
    else:
        status = '<span class="online">online</span>'
        cpu_pct = snap.get("cpu_pct")
        cpu_c   = snap.get("cpu_package_c")
        mem_pct = snap.get("memory", {}).get("pct")
        gpus    = snap.get("gpus", [])
        gpu_c   = gpus[0]["temp_c"] if gpus else None
        gpu_w   = gpus[0]["power_w"] if gpus else None
        ssds    = snap.get("ssd_c", [])
        ssd_c   = f"{min(ssds):.0f}" if ssds else None

        def cell(v): return f'<td>{v}</td>' if v is not None else '<td class="na">-</td>'
        cells = [cell(f"{cpu_pct:.1f}"), cell(f"{cpu_c:.0f}" if cpu_c else None),
                 cell(f"{mem_pct:.1f}" if mem_pct else None),
                 cell(f"{gpu_c}" if gpu_c is not None else None),
                 cell(f"{gpu_w}" if gpu_w is not None else None),
                 cell(ssd_c)]
        cells.append("<td></td>")  # placeholder for actions column

    actions = ""
    if can_wake:
        actions += f'<button class="wake" onclick="wake(\'{host}\')">Wake</button>'
        actions += f'<button class="shutdown" onclick="shutdown(\'{host}\')">Shutdown</button>'

    return f"<tr><td><b>{host}</b></td><td>{status}</td>{''.join(cells[:-1])}<td>{actions}</td></tr>"


@router.get("/ui", response_class=HTMLResponse)
def ui():
    rows = "\n".join(_row(host, cfg) for host, cfg in settings.hosts.items())
    return HTMLResponse(_PAGE.replace("{rows}", rows))
