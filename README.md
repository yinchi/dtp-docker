# DTP-Docker: Docker Compose stack for a Digital Twin platform (DTP)

&copy; 2025-2026 Yin-Chi Chan & Anandarup Mukherjee, Institute for Manufacturing, University of Cambridge

This project has been tested on a VM running Ubuntu 24.04 LTS.  The code in this project assumes a Debian-based environment (`bash` shell & `apt` package manager).

## Setup

The preferred method is to run the Docker Stack inside a Ubuntu or Debian VM, so that supporting software can be easily installed.  For example, [`yinchi/multipass_setup`](https://github.com/yinchi/multipass_setup) sets up Multipass VMs with Git and gh (the GitHub CLI) preconfigured, using the configured bridge network setup.

After setting up Git and gh, clone this repository and:

1. Run `vm-setup/setup.sh` to install required packages.
2. Source `scripts/aliases.sh` to load Git and bash aliases for this project.  Alternatively, you may copy the bash portion of this script to `~/.bashrc` or `~/.bash_aliases`.
3. Source `scripts/just_completions.sh` to set up completions for [Just](https://just.systems/man/en/).  You can edit your `~/.bashrc` to source this script automatically for each new shell session.
4. Run `scripts/gen_env.py` to generate a `.env` file.  This file is automatically read by Docker Compose unless overriden.
5. Connect to a tailnet; see the "Tailscale" section below.
6. For local development, run `uv sync --all-packages` to set up the Python virtual environment (managed by `uv`).
7. Start up **only** the main database: `docker compose up timescaledb -d`
8. Create the `dtp` user and database using `just init-db`.
9. `docker compose down`
10. Launch the full DTP stack with `just docker-up`.

## Just

A number of `just` recipes are available in the `justfile`.  Running `just` with no arguments will launch an interactive menu (press Escape to exit without running any recipe).  Note, however, that recipes requiring arguments cannot be invoked via the menu.  Alternatively, tab auto-completion can be set up using the steps above.

## Tailscale

We use [Tailscale](https://tailscale.com/kb/1151/what-is-tailscale) to expose services within a virtual private network.  Assuming we have a tailnet, run the following on the new VM:

```bash
curl -fsSL https://tailscale.com/install.sh | sh
sudo tailscale up
```

Follow the prompts to authorize the new VM and add it to the tailnet.

Once the Docker Compose stack is launched and connected to the tailnet using `just docker-up`, the status of the tailscale port-forwards can be reviewed using `just tailscale-serve-status`.

## Pre-commit

To enforce code formatting and linting rules, `pre-commit` is used in this project.  Use `pre-commit install` to install the pre-commit hooks, and `pre-commit run [-a]` to run the hooks (optionally on all files, not just staged files).

Hooks for other stages, such as pre-push, [can also be set up](https://pre-commit.com/#confining-hooks-to-run-at-certain-stages).
