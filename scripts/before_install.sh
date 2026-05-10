#!/bin/bash
echo "Instalando Docker si no existe..."
if ! command -v docker &> /dev/null; then
    apt-get update -y
    apt-get install -y docker.io
    systemctl start docker
fi

echo "Instalando Docker Compose si no existe..."
if ! command -v docker-compose &> /dev/null; then
    curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
fi

echo "before_install completado."
