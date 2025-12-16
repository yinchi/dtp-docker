#!/usr/bin/env bash
# Set up a new virtual machine instance with some basic dev packages

set -euo pipefail

# cd to directory of this script
cd "$(dirname "$0")"

############################################################

# Ensure ~/.local/bin exists and is on PATH
mkdir -p "$HOME/.local/bin"

echo '🔨  Configuring ~/.bashrc to include ~/.local/bin in PATH...'
if ! echo "$PATH" | tr ':' '\n' | grep -qx "$HOME/.local/bin"; then
    # Update .bashrc
    cat <<'EOF' >>"$HOME/.bashrc"

# Add ~/.local/bin to PATH if not already in PATH
if ! echo "$PATH" | tr ':' '\n' | grep -qx "$HOME/.local/bin"; then
    export PATH="$HOME/.local/bin:$PATH"
fi
EOF
    # Update $PATH for current session
    export PATH="$HOME/.local/bin:$PATH"
    echo '✅  Added ~/.local/bin to PATH in .bashrc.  Log out and back in and restart this ' \
        'script to continue.'
    exit 1
else
    echo '✅  ~/.local/bin is already in PATH.'
fi
echo ''

############################################################

echo '🔨  Configuring pureline...'

# Check for pureline script
if ! command -v pureline &>/dev/null; then
    echo '    Installing pureline...'
    if [ ! -d "$HOME/pureline" ]; then
        gh repo clone chris-marsh/pureline "$HOME/pureline"
    fi
    cp "$HOME/pureline/pureline" "$HOME/.local/bin/pureline"
    cp "pureline.conf" "$HOME/.pureline.conf"
else
    echo '✅  pureline is already installed.'
fi

# Check .bashrc setup
if ! grep -F -q 'source ~/pureline/pureline' "$HOME/.bashrc"; then
    cat <<'EOF' >>"$HOME/.bashrc"

# Set up pureline
if [ "$TERM" != "linux" ]; then
    source ~/pureline/pureline ~/.pureline.conf
fi
EOF
    echo '✅  pureline added to .bashrc.  To see the updated shell prompts, start a new bash session.'
else
    echo '✅  pureline setup already exists in .bashrc.'
fi
echo '    To ensure proper rendering, ensure that you are using a Nerd Font' \
    '(https://www.nerdfonts.com/)'
echo ''

############################################################

echo '🔨  Configuring uv...'

if ! command -v uv &>/dev/null; then
    curl -LsSf https://astral.sh/uv/install.sh | sh
    echo '✅  uv installed.'
else
    echo '✅  uv already installed.  You can upgrade uv using `uv self update`.'
    uv --version
fi
echo ''

#############################################################

echo '🔨  Updating package lists...'
sudo apt-get update -qq
echo '🔨  Upgrading packages...'
sudo apt-get upgrade -yqq
echo '🔨  Installing necessary packages for software source management...'
sudo apt-get install -yqq ca-certificates curl gnupg lsb-release

echo '🔨  Configuring software sources...'
sudo mkdir -p /etc/apt/keyrings

# Provides `gum` for easier, prettier shell prompts
if [ ! -f /etc/apt/keyrings/charm.gpg ]; then
    curl -fsSL https://repo.charm.sh/apt/gpg.key | sudo gpg --dearmor \
        -o /etc/apt/keyrings/charm.gpg
fi
echo "deb [signed-by=/etc/apt/keyrings/charm.gpg] https://repo.charm.sh/apt/ * *" |
    sudo tee /etc/apt/sources.list.d/charm.list >/dev/null

# Docker
if [ ! -f /etc/apt/keyrings/docker.gpg ]; then
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg |
        sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
fi
echo "deb [signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu/ noble stable" |
    sudo tee /etc/apt/sources.list.d/docker.list >/dev/null

# Provides cypher-shell for interacting with Neo4j databases
if [ ! -f /etc/apt/keyrings/neotechnology.gpg ]; then
    curl -fsSL https://debian.neo4j.com/neotechnology.gpg.key |
        sudo gpg --dearmor -o /etc/apt/keyrings/neotechnology.gpg
fi
echo 'deb [signed-by=/etc/apt/keyrings/neotechnology.gpg] https://debian.neo4j.com stable latest' |
    sudo tee /etc/apt/sources.list.d/neo4j.list >/dev/null

# Provides nodejs
if [ ! -f /etc/apt/keyrings/nodesource.gpg ]; then
    curl -fsSL https://deb.nodesource.com/gpgkey/nodesource-repo.gpg.key |
        sudo gpg --dearmor -o /etc/apt/keyrings/nodesource.gpg
fi
echo 'deb [signed-by=/etc/apt/keyrings/nodesource.gpg] https://deb.nodesource.com/node_24.x nodistro main' |
    sudo tee /etc/apt/sources.list.d/nodesource.list >/dev/null

echo '🔨  Updating package lists (again)...'
sudo apt-get update -qq
echo '🔨  Upgrading packages (again)...'
sudo apt-get upgrade -yqq

##############################################################

echo '🔨  Installing/Refreshing snaps...'
sudo snap install yq # YAML processor
sudo snap install fx # JSON viewer/processor
sudo snap refresh

echo '🔨  Installing/Refreshing apt packages...'
sed 's/#.*//;/^[[:space:]]*$/d' apt_list | xargs sudo apt-get install -yqq
echo '✅  Apt packages installed.'
echo ''

##############################################################

# Optional installations
echo '🔨  Checking for Docker...'
if ! command -v docker &>/dev/null; then
    if (gum confirm "Docker not found.  Do you want to install Docker and related tools?"); then
        echo '🔨  Running Docker setup...'
        bash setup_docker.sh
    else
        echo '⚠️  Skipping Docker setup as per user request.'
    fi
else
    echo '✅  Docker is already installed.'
    docker --version
fi
echo ''

echo '🔨  Checking for bun...'
if ! command -v bun &>/dev/null; then
    if (gum confirm "Do you want to install Bun (a fast JavaScript/TypeScript runtime)?"); then
        echo '🔨  Installing Bun...'
        # Install script installs to ~/.bun and adds to PATH
        curl -fsSL https://bun.sh/install | bash
        # Make `bun` available in current session as well
        export BUN_INSTALL="$HOME/.bun"
        export PATH="$BUN_INSTALL/bin:$PATH"
        echo '✅  Bun installed.'
        bun --version
    else
        echo '⚠️  Skipping Bun installation as per user request.'
    fi
else
    echo '✅  Bun is already installed.  You can upgrade Bun using `bun upgrade`.'
    bun --version
fi
echo ''

echo '🎉  Setup complete.'
echo '    Please restart your terminal session to ensure all changes take effect.'
echo ''
