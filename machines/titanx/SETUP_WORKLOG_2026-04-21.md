# TitanX Setup Work Log — 2026-04-21

## Goal

Bring up a permanent GitHub Actions path for `homelab-experiments`:

`GitHub push/workflow_dispatch -> TitanX self-hosted runner -> 5090 homelab-runner`

This setup is for dispatch only. Actual experiment execution still happens on
the 5090 side.

## Repos and roles

- `homelab-experiments`
  - source of truth for `spec.yaml` and `model.md`
  - contains `.github/workflows/run-experiment.yml`
- `auto-research`
  - hosts the 5090-side `homelab-runner` FastAPI service
  - receives `POST /runs` and writes run records to disk
- `homelab-agent`
  - infrastructure notes and machine/service layout
- `homelab-init`
  - TitanX runner setup docs and wake workflows

## What was already present

TitanX already had repository-scoped runners for:

- `homelab-init`
- `research-notes`

Those runners could not pick up jobs from `homelab-experiments`, because
self-hosted runners are repository-scoped in this setup.

## Permanent TitanX setup chosen

Repository:

- `carlzhangxuan/homelab-experiments`

Runner details:

- directory: `/home/zx/actions-runner-homelab-exp`
- runner name: `titanx-homelab-exp`
- custom label: `titan-x`

Official service:

- `actions.runner.carlzhangxuan-homelab-experiments.titanx-homelab-exp.service`

## Setup sequence used

1. Confirmed workflow requirement in `homelab-experiments`:
   - `runs-on: [self-hosted, titan-x]`
2. Confirmed 5090 `homelab-runner` health endpoint was up
3. Retrieved a repository runner registration token for
   `homelab-experiments`
4. Created a dedicated TitanX runner directory:
   - `/home/zx/actions-runner-homelab-exp`
5. Reused the existing runner tarball from `/home/zx/actions-runner`
6. Registered the new runner against `homelab-experiments`
7. Resolved duplicate-name registration by replacing the previous GitHub-side
   runner record
8. Installed and started the official systemd service with `svc.sh`

## Commands that mattered

Registration:

```bash
cd /home/zx/actions-runner-homelab-exp

./config.sh \
  --url https://github.com/carlzhangxuan/homelab-experiments \
  --token <registration-token> \
  --labels titan-x \
  --name titanx-homelab-exp \
  --unattended \
  --replace
```

Service install:

```bash
cd /home/zx/actions-runner-homelab-exp
sudo ./svc.sh install
sudo ./svc.sh start
sudo ./svc.sh status
```

Systemd verification:

```bash
sudo systemctl list-units 'actions.runner.*' --all
```

## Final TitanX state

Verified services on TitanX:

- `actions.runner.carlzhangxuan-homelab-experiments.titanx-homelab-exp.service`
- `actions.runner.carlzhangxuan-homelab-init.titanx.service`
- `actions.runner.carlzhangxuan-research-notes.LittleTitanX.service`

The new `homelab-experiments` runner was verified as:

- loaded
- enabled
- active
- running

## End-to-end validation that succeeded

Commit used for validation:

- `8ea14bcf7a26ee03e6fbb97a7af2a6ce455e7471`

Workflow:

- `run-experiment`

Observed result:

- GitHub Actions run completed successfully
- TitanX performed `GET /health` against the 5090 service
- TitanX then sent `POST /runs`
- 5090 accepted the dispatch and flushed the run record to disk

Example accepted run on the 5090 side:

- `run_id`: `a20445a8bfb8`
- `git_sha`: `8ea14bcf7a26ee03e6fbb97a7af2a6ce455e7471`
- `experiment_path`: `Diffusion/ddpm-cifar10-v1`
- `mode`: `sanity`
- `model_card_bytes`: `2396`

The payload included:

- full `spec.yaml`
- `model.md` content size
- the expected experiment path and commit SHA

## Important clarification

The successful validation used the existing experiment directory
`Diffusion/ddpm-cifar10-v1`, but that was only to prove the dispatch path.

The next target is not the old `cifar10-test` classifier job in this repo.
Tonight's intended direction is a real DDPM flow, with TitanX only acting as
the GitHub Actions dispatch hop.

## Current code / infra boundary

What is production-ish now:

- TitanX repository runner install for `homelab-experiments`
- GitHub Actions -> TitanX -> 5090 dispatch path
- 5090 `homelab-runner` health and request logging

What is still not implemented yet:

- generating Dockerfiles from `spec.yaml` + `model.md`
- building the training image
- running DDPM training on the 5090
- writing results back to `homelab-experiments`

## Files worth checking next

- `homelab-experiments/.github/workflows/run-experiment.yml`
- `auto-research/agent/homelab-runner/app/main.py`
- `auto-research/docker-compose.yml`
- `homelab_init/homelab-init/docs/titanx-github-runners.md`

## Operator notes

- Keep `homelab-init` and `homelab-experiments` as separate TitanX runner
  installs
- Do not repoint `/home/zx/actions-runner` at another repository
- For `homelab-experiments`, the required custom label is `titan-x`
- The old `jobs/cifar10-test` content in `homelab-agent` is only a historical
  smoke test and should not be confused with the DDPM path
