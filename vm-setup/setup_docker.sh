#!/usr/bin/env bash
# Set up Docker environment with some basic dev packages

set -euo pipefail

cd "$HOME"

if ! apt info docker-ce &>/dev/null; then
    echo '❌  Docker repository not found. Please run setup.sh to set up the Docker repository' \
        'first.'
    exit 1
fi

echo '🔨  Updating apt package lists...'
sudo apt-get update -yqq
echo '🔨  Installing Docker...'
sudo apt-get install -yqq \
    docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
echo '✅  Docker packages installed.'

# Create docker group if not exists
if ! getent group docker &>/dev/null; then
    echo '🔨  Creating docker group...'
    sudo groupadd docker
    echo '✅  docker group created.'
else
    echo '✅  docker group already exists.'
fi

sudo usermod -aG docker "$USER"
echo '✅  Added user to docker group.'
echo ''

echo '🔨  Installing lazydocker...'
curl -fsSL https://raw.githubusercontent.com/jesseduffield/lazydocker/master/scripts/install_update_linux.sh | bash
echo '✅  lazydocker installed.'
lazydocker --version
echo ''

echo '🔨  Installing ctop...'
sudo wget -q https://github.com/bcicen/ctop/releases/download/v0.7.7/ctop-0.7.7-linux-amd64 \
    -O /usr/local/bin/ctop
sudo chmod +x /usr/local/bin/ctop
echo '✅  ctop installed.'
ctop -v
echo ''
