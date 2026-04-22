# TitanX

TitanX is the GitHub Actions bridge node in the current homelab training flow.
It does not run the 5090 training workload itself. Its main job is to host
repository-scoped self-hosted runners that can reach other LAN machines.

Current runner roles:

- `homelab-init` -> wake workflows, label `titanx`
- `homelab-experiments` -> experiment dispatch workflow, label `titan-x`

For the detailed April 21, 2026 setup and validation log, see
[`SETUP_WORKLOG_2026-04-21.md`](SETUP_WORKLOG_2026-04-21.md).

Current steady-state on TitanX:

- official systemd runner for `homelab-experiments`
- service:
  `actions.runner.carlzhangxuan-homelab-experiments.titanx-homelab-exp.service`
- runner directory:
  `/home/zx/actions-runner-homelab-exp`

The 5090-side `homelab-runner` service is separate and lives in the
`auto-research` repository under Docker Compose.
