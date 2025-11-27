# JUSTFILE
# Use `just <command>` to launch any of the below scripts
# Use `source scripts/just_completion.sh` to enable autocompletion

# Default: launch interactive menu
default:
    @just --choose

# List available commands
list:
    #!/usr/bin/env bash
    just --list --color=always | less -F -R

#############################################################

### DOCKER ###

# Launch the docker stack
docker-up:
    #!/usr/bin/env bash
    docker compose --env-file .env up -d

# Show Docker Compose status
docker-ps:
    #!/usr/bin/env bash
    docker compose --env-file .env ps

# Show the volumes in the Docker Compose configuration
docker-config-vols:
    #!/usr/bin/env bash
    docker compose --env-file .env config | yq '.volumes'

# Show the networks in the Docker Compose configuration
docker-config-nets:
    #!/usr/bin/env bash
    docker compose --env-file .env config | yq '.networks'

# Show the public ports in the Docker Compose
docker-ports:
    #!/usr/bin/env bash
    docker compose ps --format json | yq -p=json '{.Name: (.Ports | split(", ") | filter(test("0.0.0.0") ))} | . as $item ireduce ({}; . * $item)'

#############################################################

### TAILSCALE ###

# Serve a port from the current machine
tailscale-serve $port='':
    #!/usr/bin/env bash
    PORT=${port:-$(gum input --prompt="Port: ")}
    if [ -z "$PORT" ]; then
        echo 'Cancelled.'
        exit 1
    fi
    tailscale serve --bg --https="$PORT" "$PORT"

# Stop serving on a given port
tailscale-unserve $port='':
    #!/usr/bin/env bash
    PORT=${port:-$(gum input --prompt="Port: ")}
    if [ -z "$PORT" ]; then
        echo 'Cancelled.'
        exit 1
    fi
    tailscale serve --https="$PORT" off

# Show the current status of `tailscale serve`
tailscale-serve-status:
    #!/usr/bin/env bash
    tailscale serve status

#############################################################

### POSTGRESQL/TIMESCALEDB ###

# pgcli command-line interface for PostgreSQL
pgcli:
    #!/usr/bin/env bash
    # The `datastore/timescaledb/create_dtp.sh` script can also be used to update the `dtp` user
    # password (the script will print an error for an existing user/database, but continue)
    source env/timescaledb.env
    pgcli "postgres://${USER_NAME}:${USER_PASSWORD}@localhost/${USER_DB}"
