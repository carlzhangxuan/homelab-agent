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
    #modal-overlay {
      display: none; position: fixed; inset: 0;
      background: rgba(0,0,0,0.7); z-index: 100;
      align-items: center; justify-content: center;
    }
    #modal-overlay.show { display: flex; }
    #modal {
      background: #1e1e1e; border: 1px solid #444; border-radius: 6px;
      padding: 1.5rem 2rem; min-width: 320px;
    }
    #modal h2 { margin: 0 0 1rem; color: #f84; font-size: 1rem; }
    #modal input {
      width: 100%; box-sizing: border-box;
      background: #111; color: #eee; border: 1px solid #555;
      padding: 0.4rem 0.6rem; border-radius: 3px; font-family: monospace;
      margin-bottom: 1rem;
    }
    #modal .actions { display: flex; gap: 0.5rem; justify-content: flex-end; }
  </style>
</head>
<body>
  <h1>Homelab</h1>
  <table>
    <tr>
      <th>Host</th><th>Status</th><th>CPU%</th><th>CPU°C</th>
      <th>Mem%</th><th>GPU°C</th><th>GPU W</th><th>SSD°C</th><th>Actions</th>
    </tr>
    {rows}
  </table>

  <div id="modal-overlay">
    <div id="modal">
      <h2 id="modal-title">Shutdown</h2>
      <input type="password" id="modal-pw" placeholder="sudo password (blank if passwordless)" />
      <div class="actions">
        <button onclick="modalCancel()">Cancel</button>
        <button class="shutdown" onclick="modalConfirm()">Confirm</button>
      </div>
    </div>
  </div>

  <script>
    let _modalResolve = null;

    function showModal(host) {
      document.getElementById('modal-title').textContent = 'Shutdown ' + host;
      const pw = document.getElementById('modal-pw');
      pw.value = '';
      document.getElementById('modal-overlay').classList.add('show');
      pw.focus();
      return new Promise(resolve => { _modalResolve = resolve; });
    }
    function modalCancel() {
      document.getElementById('modal-overlay').classList.remove('show');
      if (_modalResolve) _modalResolve(null);
    }
    function modalConfirm() {
      const pw = document.getElementById('modal-pw').value;
      document.getElementById('modal-overlay').classList.remove('show');
      if (_modalResolve) _modalResolve(pw);
    }
    document.getElementById('modal-pw').addEventListener('keydown', e => {
      if (e.key === 'Enter') modalConfirm();
      if (e.key === 'Escape') modalCancel();
    });

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
          alert(host + ' is online' + elapsed);
        } else if (result && result.detail) {
          alert(result.detail);
        } else {
          alert('Wake sent: ' + host);
        }
      } catch (e) {
        alert('Wake failed: ' + e.message);
      }
    }
    async function shutdown(host) {
      const pw = await showModal(host);
      if (pw === null) return;
      try {
        await postOrThrow('/homelab/shutdown/' + host, {sudo_password: pw});
        alert('Shutdown sent: ' + host);
      } catch (e) {
        alert('Shutdown failed: ' + e.message);
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
