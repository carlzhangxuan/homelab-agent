# Training Guide (4090 + 5090)

This document defines the TensorBoard log directory conventions for the two
training machines so experiment logs stay organized and easy to browse.

Machine and path mapping config:
`services/tensorboard/storage_paths.yaml`

## 1) Log root conventions

- `5090` log root: `/mnt/ssd4t/logs`
- `4090` log root: `/home/zx/lab-small/tensorboard`

Each experiment should use its own subdirectory:

- `5090` example: `/mnt/ssd4t/logs/ddpm-sandbox-001`
- `4090` example: `/home/zx/lab-small/tensorboard/ddpm-sandbox-001`

## 2) Mapping to macmini

- `5090:/mnt/ssd4t/logs` -> `mac:/Users/zx/mnt/5090`
- `4090:/home/zx/lab-small/tensorboard` -> `mac:/Users/zx/mnt/4090`

The current TensorBoard container reads:

- `5090:/data/5090`
- `4090:/data/4090`

In the UI, runs appear as `5090/<run_name>` and `4090/<run_name>`.

## 3) How training scripts should set `log_dir`

Use the experiment name consistently to avoid collisions. Prefer DDPM-style
names instead of continuing to reuse early smoke-test names like
`cifar10-test`.

`5090`:

```python
log_dir = "/mnt/ssd4t/logs/<exp_name>"
```

`4090`:

```python
log_dir = "/home/zx/lab-small/tensorboard/<exp_name>"
```

If you want environment separation, use:

- `sandbox`:
  - `5090`: `/mnt/ssd4t/logs/sandbox/<exp_name>`
  - `4090`: `/home/zx/lab-small/tensorboard/sandbox/<exp_name>`
- `prod`:
  - `5090`: `/mnt/ssd4t/logs/prod/<exp_name>`
  - `4090`: `/home/zx/lab-small/tensorboard/prod/<exp_name>`

## 4) 4090 directory initialization

If the 4090-side directory layout is not ready yet, run:

```bash
mkdir -p /home/zx/lab-small/{tensorboard,checkpoints,artifacts,datasets,scripts,tmp}
```

If you want to separate lightweight and more formal runs, you can also add:

```bash
mkdir -p /home/zx/lab-small/tensorboard/{sandbox,prod}
```
