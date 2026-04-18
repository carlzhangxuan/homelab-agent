from fastapi import APIRouter
from fastapi.responses import HTMLResponse
from config import settings
from store import store

router = APIRouter()

_PAGE = """<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>Homelab</title>
  <style>
    :root {
      --bg: #111;
      --fg: #eee;
      --muted: #666;
      --accent: #7df;
      --ok: #4f4;
      --warn: #fc4;
      --err: #f44;
      --warm: #f84;
      --line: #222;
      --line-bright: #333;
      --panel: #1a1a1a;
    }
    body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", monospace;
           background: var(--bg); color: var(--fg); padding: 2rem; margin: 0; }
    h1 { color: var(--accent); margin: 0 0 0.5rem 0; font-weight: 600; }
    .bar { display: flex; justify-content: space-between; align-items: center;
           margin-bottom: 1.5rem; color: var(--muted); font-size: 0.85rem; }
    table { border-collapse: collapse; width: 100%; font-variant-numeric: tabular-nums; }
    th { text-align: left; color: var(--accent); padding: 0.5rem 1rem;
         border-bottom: 1px solid var(--line-bright); font-weight: 500; font-size: 0.85rem;
         text-transform: uppercase; letter-spacing: 0.05em; }
    td { padding: 0.6rem 1rem; border-bottom: 1px solid var(--line); }
    td.host { font-weight: 600; }
    td.host .ip { color: var(--muted); font-weight: normal; margin-left: 0.6rem; font-size: 0.85rem; }
    td.status .online    { color: var(--ok); }
    td.status .offline   { color: var(--err); }
    td.status .working   { color: var(--warn); }
    td.status .unknown   { color: var(--muted); }
    td.status .spinner { display: inline-block; width: 0.6rem; margin-left: 0.3rem; }
    td.na { color: var(--muted); }
    td.actions { white-space: nowrap; text-align: right; }

    button {
      background: transparent;
      color: var(--fg);
      border: 1px solid var(--line-bright);
      padding: 0.35rem 0.9rem;
      border-radius: 999px;
      cursor: pointer;
      margin: 0 3px;
      font-family: inherit;
      font-size: 0.8rem;
      font-weight: 500;
      transition: background 0.15s, color 0.15s, border-color 0.15s, transform 0.08s;
    }
    button:hover:not(:disabled) { transform: translateY(-1px); }
    button:active:not(:disabled) { transform: translateY(0); }
    button:disabled { opacity: 0.4; cursor: not-allowed; }
    button.wake     { border-color: #2a5a2a; color: var(--ok); }
    button.wake:hover:not(:disabled)     { background: #1a3a1a; border-color: var(--ok); }
    button.shutdown { border-color: #5a3a1a; color: var(--warm); }
    button.shutdown:hover:not(:disabled) { background: #3a2512; border-color: var(--warm); }

    #toast {
      position: fixed; bottom: 2rem; right: 2rem;
      min-width: 14rem; max-width: 28rem;
      padding: 0.7rem 1.1rem;
      border-radius: 6px;
      font-family: inherit; font-size: 0.85rem;
      opacity: 0;
      transform: translateY(8px);
      transition: opacity 0.2s, transform 0.2s;
      pointer-events: none;
      box-shadow: 0 4px 14px rgba(0,0,0,0.4);
    }
    #toast.show { opacity: 1; transform: translateY(0); }
    #toast.info { background: #1a2a3a; border: 1px solid var(--accent); color: var(--accent); }
    #toast.ok   { background: #1a3a1a; border: 1px solid var(--ok);     color: var(--ok); }
    #toast.warn { background: #3a2f1a; border: 1px solid var(--warn);   color: var(--warn); }
    #toast.err  { background: #3a1a1a; border: 1px solid var(--err);    color: var(--err); }

    @keyframes pulse { 0%,100% { opacity: 1; } 50% { opacity: 0.3; } }
    .pulse { animation: pulse 1s ease-in-out infinite; }

    .footer { margin-top: 1.5rem; color: var(--muted); font-size: 0.85rem;
              display: flex; flex-direction: column; align-items: flex-start; gap: 0.6rem; }
    .footer button.link,
    .footer a.link,
    .footer .pathchip {
      color: var(--accent); background: transparent;
      border: 1px solid var(--line-bright); border-radius: 999px;
      padding: 0.35rem 0.9rem; font-family: inherit; font-size: 0.85rem;
      transition: background 0.15s, border-color 0.15s;
    }
    .footer button.link,
    .footer a.link { cursor: pointer; text-decoration: none; }
    .footer button.link:hover,
    .footer a.link:hover { background: #1a2a3a; border-color: var(--accent); }
    .footer .pathchip { color: var(--accent); }
  </style>
</head>
<body>
  <h1>Homelab</h1>
  <div class="bar">
    <span>auto-refresh every <span id="refresh-s">5</span>s · <span id="last-refresh">just now</span></span>
    <span id="activity"></span>
  </div>
  <div id="toast"></div>
  <table>
    <tr>
      <th>Host</th><th>Status</th><th>CPU%</th><th>CPU°C</th>
      <th>Mem%</th><th>GPU°C</th><th>GPU W</th><th>SSD°C</th><th>Actions</th>
    </tr>
    {rows}
  </table>
  <div class="footer">
    <a class="link" href="http://localhost:3001/d/homelab-overview/homelab-overview?orgId=1&amp;from=now-5m&amp;to=now&amp;timezone=browser&amp;refresh=5s" target="_blank">Grafana · homelab-overview</a>
    <button class="link" onclick="copyPath('file:///Volumes/titanX')">file:///Volumes/titanX</button>
    <a class="link" href="http://localhost:6006/?darkMode=true#timeseries" target="_blank">tensorboard-5090</a>
  </div>
  <script>
    const REFRESH_MS = 5000;
    const SHUTDOWN_TIMEOUT_MS = 120000;
    const POLL_MS = 5000;

    let _busy = 0;
    let _toastTimer = null;
    let _lastRefresh = Date.now();

    function toast(msg, type, persist) {
      const el = document.getElementById('toast');
      el.textContent = msg;
      el.className = 'show ' + (type || 'info');
      if (_toastTimer) clearTimeout(_toastTimer);
      if (!persist) {
        _toastTimer = setTimeout(() => { el.className = ''; }, 4000);
      }
    }

    function setActivity() {
      const el = document.getElementById('activity');
      el.textContent = _busy > 0 ? (_busy + ' action' + (_busy === 1 ? '' : 's') + ' in progress') : '';
      el.className = _busy > 0 ? 'pulse' : '';
    }

    function startBusy(host, label) {
      _busy++;
      setActivity();
      const row = document.getElementById('row-' + host);
      if (row) {
        const statusCell = row.querySelector('td.status');
        statusCell.innerHTML = '<span class="working pulse">' + label + '</span>';
        row.querySelectorAll('button').forEach(b => b.disabled = true);
      }
    }

    function endBusy() {
      _busy = Math.max(0, _busy - 1);
      setActivity();
      if (_busy === 0) location.reload();
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
      try { return await resp.json(); } catch (_) { return {}; }
    }

    async function copyPath(path) {
      try {
        await navigator.clipboard.writeText(path);
        toast('Copied — paste into address bar', 'ok');
      } catch (e) {
        toast('Copy failed: ' + e.message, 'err');
      }
    }

    async function getHostOnline(host) {
      try {
        const resp = await fetch('/homelab/metrics/' + host, {cache: 'no-store'});
        if (!resp.ok) return null;
        const data = await resp.json();
        return data.online === true;
      } catch (_) { return null; }
    }

    async function wake(host) {
      startBusy(host, 'waking...');
      toast('Waking ' + host + '...', 'info', true);
      try {
        const result = await postOrThrow('/homelab/wake/' + host,
                                         {wait_timeout_s: 90, poll_interval_s: 5});
        if (result && result.already_online) {
          toast(host + ' was already online', 'ok');
        } else if (result && result.online) {
          const s = result.elapsed_s !== undefined ? (' in ~' + result.elapsed_s + 's') : '';
          toast(host + ' is online' + s, 'ok');
        } else if (result && result.detail) {
          toast(result.detail, 'warn');
        } else {
          toast('Wake sent: ' + host, 'ok');
        }
      } catch (e) {
        toast('Wake failed: ' + e.message, 'err');
      } finally {
        endBusy();
      }
    }

    async function shutdown(host) {
      const sudoPassword = prompt('Shutdown ' + host +
        '\\nEnter sudo password (leave blank for passwordless sudo):', '');
      if (sudoPassword === null) return;
      startBusy(host, 'shutting down...');
      toast('Sending shutdown to ' + host + '...', 'info', true);
      const startedAt = Date.now();
      try {
        await postOrThrow('/homelab/shutdown/' + host, {sudo_password: sudoPassword});
        toast('Shutdown sent to ' + host + ', waiting for offline...', 'info', true);
        while (Date.now() - startedAt < SHUTDOWN_TIMEOUT_MS) {
          await new Promise(r => setTimeout(r, POLL_MS));
          const online = await getHostOnline(host);
          if (online === false) {
            const s = Math.round((Date.now() - startedAt) / 1000);
            toast(host + ' is offline (~' + s + 's)', 'ok');
            return;
          }
        }
        toast(host + ' still online after ' +
              Math.round(SHUTDOWN_TIMEOUT_MS / 1000) + 's', 'warn');
      } catch (e) {
        toast('Shutdown failed: ' + e.message, 'err');
      } finally {
        endBusy();
      }
    }

    function updateRefreshLabel() {
      const el = document.getElementById('last-refresh');
      const s = Math.round((Date.now() - _lastRefresh) / 1000);
      el.textContent = s <= 0 ? 'just now' : s + 's ago';
    }
    setInterval(updateRefreshLabel, 1000);
    setInterval(() => { if (_busy === 0) location.reload(); }, REFRESH_MS);
  </script>
</body>
</html>"""


def _row(host: str, cfg: dict) -> str:
    snap = store.latest(host)
    can_wake = "mac" in cfg
    ip = cfg.get("ip", "")

    if not snap:
        status_html = '<span class="unknown">-</span>'
        cells = ['<td class="na">-</td>'] * 6
    elif not snap.get("online", True):
        status_html = '<span class="offline">offline</span>'
        cells = ['<td class="na">-</td>'] * 6
    else:
        status_html = '<span class="online">online</span>'
        cpu_pct = snap.get("cpu_pct")
        cpu_c   = snap.get("cpu_package_c")
        mem_pct = snap.get("memory", {}).get("pct")
        gpus    = snap.get("gpus", [])
        gpu_c   = gpus[0]["temp_c"] if gpus else None
        gpu_w   = gpus[0]["power_w"] if gpus else None
        ssds    = snap.get("ssd_c", [])
        ssd_c   = f"{min(ssds):.0f}" if ssds else None

        def cell(v): return f'<td>{v}</td>' if v is not None else '<td class="na">-</td>'
        cells = [
            cell(f"{cpu_pct:.1f}" if cpu_pct is not None else None),
            cell(f"{cpu_c:.0f}" if cpu_c else None),
            cell(f"{mem_pct:.1f}" if mem_pct else None),
            cell(f"{gpu_c}" if gpu_c is not None else None),
            cell(f"{gpu_w}" if gpu_w is not None else None),
            cell(ssd_c),
        ]

    actions = ""
    if can_wake:
        actions += f'<button class="wake" onclick="wake(\'{host}\')">Wake</button>'
        actions += f'<button class="shutdown" onclick="shutdown(\'{host}\')">Shutdown</button>'

    ip_html = f'<span class="ip">{ip}</span>' if ip else ""
    return (
        f'<tr id="row-{host}">'
        f'<td class="host">{host}{ip_html}</td>'
        f'<td class="status">{status_html}</td>'
        f'{"".join(cells)}'
        f'<td class="actions">{actions}</td>'
        f'</tr>'
    )


@router.get("/ui", response_class=HTMLResponse)
def ui():
    rows = "\n".join(_row(host, cfg) for host, cfg in settings.hosts.items())
    return HTMLResponse(_PAGE.replace("{rows}", rows))
