# TensorBoard

Centralized TensorBoard on macmini, reading training logs from GPU machines via SSHFS.

Training log layout reference: `services/tensorboard/TRAINING_GUIDE.md`
Path config (YAML): `services/tensorboard/storage_paths.yaml`

- URL: `http://localhost:6006/?darkMode=true#timeseries`
- Log sources:
  - `5090` -> `/mnt/ssd4t/logs` (mounted to mac `/Users/zx/mnt/5090`)
  - `4090` -> `/home/zx/lab-small/tensorboard` (mounted to mac `/Users/zx/mnt/4090`)

## 4090 small-experiment layout

On `4090`, this structure is used for lightweight experiments:

```text
/home/zx/lab-small/
  tensorboard/
  checkpoints/
  artifacts/
  datasets/
  scripts/
  tmp/
```

## mac prerequisites

Install macFUSE + SSHFS first:

```bash
brew install --cask macfuse
brew install sshfs
```

## SSHFS auto-mount (LaunchAgent)

Create mount points:

```bash
mkdir -p /Users/zx/mnt/5090 /Users/zx/mnt/4090
```

Create `~/Library/LaunchAgents/com.homelab.sshfs.5090.plist`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.homelab.sshfs.5090</string>
    <key>ProgramArguments</key>
    <array>
        <string>/opt/homebrew/bin/sshfs</string>
        <string>zx@192.168.10.33:/mnt/ssd4t/logs</string>
        <string>/Users/zx/mnt/5090</string>
        <string>-o</string>
        <string>follow_symlinks,reconnect,ServerAliveInterval=15,ServerAliveCountMax=3,IdentityFile=/Users/zx/.ssh/id_rsa</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/tmp/homelab-sshfs-5090.log</string>
    <key>StandardErrorPath</key>
    <string>/tmp/homelab-sshfs-5090.err</string>
</dict>
</plist>
```

Create `~/Library/LaunchAgents/com.homelab.sshfs.4090.plist`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.homelab.sshfs.4090</string>
    <key>ProgramArguments</key>
    <array>
        <string>/opt/homebrew/bin/sshfs</string>
        <string>zx@192.168.10.31:/home/zx/lab-small/tensorboard</string>
        <string>/Users/zx/mnt/4090</string>
        <string>-o</string>
        <string>follow_symlinks,reconnect,ServerAliveInterval=15,ServerAliveCountMax=3,IdentityFile=/Users/zx/.ssh/id_ed25519</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/tmp/homelab-sshfs-4090.log</string>
    <key>StandardErrorPath</key>
    <string>/tmp/homelab-sshfs-4090.err</string>
</dict>
</plist>
```

Load/reload:

```bash
launchctl unload ~/Library/LaunchAgents/com.homelab.sshfs.5090.plist 2>/dev/null || true
launchctl unload ~/Library/LaunchAgents/com.homelab.sshfs.4090.plist 2>/dev/null || true
launchctl load ~/Library/LaunchAgents/com.homelab.sshfs.5090.plist
launchctl load ~/Library/LaunchAgents/com.homelab.sshfs.4090.plist
```

Verify:

```bash
mount | grep '/Users/zx/mnt/'
ls /Users/zx/mnt/5090
ls /Users/zx/mnt/4090
```

## Docker compose

TensorBoard is included by `machines/macmini/docker-compose.yml`.

Start/recreate:

```bash
cd machines/macmini
docker compose up -d --force-recreate tensorboard
```

Current compose wiring:

```yaml
command: >
  --logdir_spec 5090:/data/5090,4090:/data/4090
volumes:
  - /Users/zx/mnt:/data:ro
```
