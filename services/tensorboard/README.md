# TensorBoard

Centralized TensorBoard instance on macmini, reading training logs from GPU machines via SSHFS.

- **URL:** http://localhost:6006
- **Log sources:** 5090 (`192.168.10.33`)

## macOS Prerequisites

### 1. macFUSE

Install macFUSE, then approve the kernel extension:

```bash
brew install --cask macfuse
```

After install, macOS will block the kernel extension. To approve it:

1. Shut down and boot into **Recovery Mode** (hold Touch ID on power-on)
2. Go to **Utilities → Startup Security Utility → Security Policy**
3. Select **Reduced Security** and enable **Allow user management of kernel extensions**
4. Reboot normally
5. Go to **System Settings → Privacy & Security**, scroll down and click **Allow** next to "Benjamin Fleischer" (macFUSE)
6. Reboot again

### 2. SSHFS

```bash
brew install sshfs
```

## SSHFS Auto-Mount (LaunchAgent)

Create the mount point:

```bash
mkdir -p ~/mnt/5090
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
        <string>follow_symlinks,reconnect,ServerAliveInterval=15,ServerAliveCountMax=3,IdentityFile=/Users/zx/.ssh/id_ed25519</string>
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

Load it:

```bash
launchctl load ~/Library/LaunchAgents/com.homelab.sshfs.5090.plist
```

Verify:

```bash
mount | grep 5090
```

## Docker Compose

The service is included in `machines/macmini/docker-compose.yml`.

Start:

```bash
cd machines/macmini && docker compose up -d tensorboard
```

To add another GPU machine, add a new `logdir_spec` entry and a new SSHFS mount to `services/tensorboard/compose.yml`:

```yaml
command: >
  --logdir_spec 5090:/data/5090,4090:/data/4090
  --host 0.0.0.0
  --port 6006
volumes:
  - /Users/zx/mnt/5090:/data/5090:ro
  - /Users/zx/mnt/4090:/data/4090:ro
```
