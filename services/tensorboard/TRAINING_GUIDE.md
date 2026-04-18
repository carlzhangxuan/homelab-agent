# Training Guide (4090 + 5090)

本文件统一约定两台训练机的 TensorBoard 日志输出路径，避免实验日志混乱。

机器与环境路径配置文件：`services/tensorboard/storage_paths.yaml`

## 1) 日志根目录约定

- `5090` 日志根目录：`/mnt/ssd4t/logs`
- `4090` 日志根目录：`/home/zx/lab-small/tensorboard`

每个实验都创建独立子目录：

- `5090` 示例：`/mnt/ssd4t/logs/cifar10-test`
- `4090` 示例：`/home/zx/lab-small/tensorboard/cifar10-test`

## 2) 与 macmini 的映射关系

- `5090:/mnt/ssd4t/logs` -> `mac:/Users/zx/mnt/5090`
- `4090:/home/zx/lab-small/tensorboard` -> `mac:/Users/zx/mnt/4090`

当前 TensorBoard 容器会读取：

- `5090:/data/5090`
- `4090:/data/4090`

对应 UI 里会显示为 `5090/<run_name>` 和 `4090/<run_name>`。

## 3) 训练脚本应如何设置 log_dir

建议统一按 `实验名` 输出，避免互相覆盖。

`5090`:

```python
log_dir = "/mnt/ssd4t/logs/<exp_name>"
```

`4090`:

```python
log_dir = "/home/zx/lab-small/tensorboard/<exp_name>"
```

如果要按环境隔离，建议使用：

- `sandbox`:
  - `5090`: `/mnt/ssd4t/logs/sandbox/<exp_name>`
  - `4090`: `/home/zx/lab-small/tensorboard/sandbox/<exp_name>`
- `prod`:
  - `5090`: `/mnt/ssd4t/logs/prod/<exp_name>`
  - `4090`: `/home/zx/lab-small/tensorboard/prod/<exp_name>`

## 4) 4090 目录初始化（如需）

如果 4090 上目录还没准备好，执行：

```bash
mkdir -p /home/zx/lab-small/{tensorboard,checkpoints,artifacts,datasets,scripts,tmp}
```

如果你想把“轻量实验”和“正式实验”分离，也可以再加：

```bash
mkdir -p /home/zx/lab-small/tensorboard/{sandbox,prod}
```
