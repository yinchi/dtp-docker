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

### ENV and secrets ###

# Generate the .env file from .env.template
gen-env:
    #!/usr/bin/env bash
    ./scripts/gen_env.py && sort -o .env .env

# Generate a user for Traefik BasicAuth
htpasswd $user:
    #!/usr/bin/env bash
    htpasswd -B infra/traefik/htpasswd $user
    # Traefik won't re-read the htpasswd file unless we restart the service
    just docker-restart traefik

#############################################################

### DOCKER ###

# Launch the Docker stack
docker-up:
    #!/usr/bin/env bash
    tailscale serve reset
    docker compose --env-file .env up -d
    just tailscale-up

# Restart a single Docker service
docker-restart $service:
    #!/usr/bin/env bash
    docker compose --env-file .env down "$service"
    tailscale serve reset
    docker compose --env-file .env up "$service" -d
    just tailscale-up

# Show Docker Compose status
docker-ps:
    #!/usr/bin/env bash
    docker compose --env-file .env ps

# Show the public ports in the current Docker instance (actual instance, not config)
docker-ports:
    #!/usr/bin/env bash
    docker compose ps --format json | yq -p=json '{.Name: (.Ports | split(", ") | filter(test("0.0.0.0") ))} | . as $item ireduce ({}; . * $item)'

# Show the volumes in the Docker Compose configuration
docker-config-vols:
    #!/usr/bin/env bash
    docker compose --env-file .env config | yq '.volumes'

# Show the networks in the Docker Compose configuration
docker-config-nets:
    #!/usr/bin/env bash
    docker compose --env-file .env config | yq '.networks'

# Show service healthchecks in the Docker Compose configuration
docker-config-healthchecks:
    #!/usr/bin/env bash
    docker compose config | yq '.services[] | {key: .healthcheck.test // [] | join(" ")}'

# Show location of config files for Docker Compose
docker-config-ls:
    #!/usr/bin/env bash
    # Any file named [foo.][bar.]compose[.baz].yaml will be included (.yml also accepted)
    find . -regextype posix-extended -regex '.*/(.*\.)*compose(\..*)*\.(ya?ml)$'

#############################################################

### TAILSCALE ###

# Start up all Tailscale endpoints
tailscale-up:
    #!/usr/bin/env bash
    # Traefik (443 -> 80)
    tailscale serve --bg --https=443 80
    # Traefik Dashboard (5000)
    # PhpPgAdmin (5001)
    echo -n 5000 5001 | xargs -d' ' -I{} tailscale serve --bg --https="{}" "{}"
    # Mosquitto MQTT Broker (1883), TCP
    tailscale serve --bg --tcp=1883 tcp://localhost:1883

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

init-db:
    #!/usr/bin/env bash
    ./datastore/timescaledb/create_dtp.sh

# pgcli command-line interface for PostgreSQL
pgcli:
    #!/usr/bin/env bash
    # The `datastore/timescaledb/create_dtp.sh` script can also be used to update the `dtp` user
    # password (the script will print an error for an existing user/database, but continue)
    source .env
    pgcli "postgres://${PG_USER}:${PG_USER_PASSWORD}@localhost/${PG_DB}"
