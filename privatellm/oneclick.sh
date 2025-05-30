#!/bin/bash

# Filename: run-layer8.sh
# Usage: chmod +x run-layer8.sh && ./run-layer8.sh

set -e

# Function to check and install Docker
install_docker() {
  echo "Docker not found. Installing Docker..."

  sudo apt update
  sudo apt install -y \
    ca-certificates \
    curl \
    gnupg \
    lsb-release

  sudo mkdir -p /etc/apt/keyrings
  curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

  echo \
    "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
    $(lsb_release -cs) stable" | \
    sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

  sudo apt update
  sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

  echo "Docker installed successfully."
}

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
  install_docker
else
  echo "Docker is already installed."
fi

# Pull the image
echo "=== Pulling the Layer8 image ==="
docker pull vickydev810/layer8:latest

# Create Docker volumes
echo "=== Creating Docker volumes ==="
docker volume create ollama
docker volume create open-web2ui

# Run the container
echo "=== Running the Layer8 container ==="
docker run -d -p 3000:8080 --gpus=all -e WEBUI_AUTH=False \
  -v ollama:/root/.ollama \
  -v open-web2ui:/app/backend/data \
  --name open-web2ui \
  --restart always \
  vickydev810/layer8:latest

echo "=== Layer8 is now running at http://localhost:3000 ==="
