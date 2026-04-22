# cifar10-test

This job is an old smoke test for validating basic GPU training, TensorBoard
logs, and checkpoint paths.

It is not the current target experiment flow.

Current direction:

- experiment source of truth lives in `homelab-experiments`
- TitanX handles GitHub Actions dispatch
- 5090 receives runs through `auto-research/agent/homelab-runner`
- the next real target is a DDPM workflow, not this CIFAR-10 classifier demo

Keep this directory only as a simple reference for containerized training and
log/checkpoint volume wiring.
