# vm-setup: Scripts for setting up a new virtual machine

This repo contains scripts for setting up a new Ubuntu virtual machine, with optional installation of Docker and Bun (Javascript/Typescript runtime).

Included packages include (but are not limited to):

- CLI database tools: `pgcli`, `cypher-shell`, etc.
- Redis CLI tool `iredis`
- `mosquitto_clients`: provides `mosquitto_pub` and `mosquitto_sub`
- `just`: for organizing project scripts

Packages available via `apt` are listed in `apt_list`; however, some packages that are installed manually or via `snap` are specified directly in `setup.sh` or another bash script.

## Usage

This repo is intended for use alongside `yinchi/multipass_setup`.

1. Clone the `yinchi/multipass_setup` repo on your host machine.
2. `cd` into the newly created `multipass_setup` directory.
3. Run `./setup.sh` to set up Multipass and other required packages.
4. Run `./new_instance.sh` to create a new VM; use `./new_instance -h` to see command syntax and options.  The script should also set up `git` and the `gh` CLI tool on the new VM.
5. On GitHub, create a **new** repo from the `yinchi/vm-setup` template.
6. Clone your new repo to the VM.  You can use `gh repo clone`.
7. Run `vm-setup/setup.sh` on the VM.

## Use as a template repository

This repo can be used as a template repository, thus ensuring that projects can quickly setup an initial set of development tools.  All scripts and configuration files are located in `vm-setup/` for isolation from new project code.
