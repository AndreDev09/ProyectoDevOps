#!/bin/bash
echo "=== Instalando paquetes esenciales ==="
apt-get update -y
apt-get install -y git vim python3 python3-pip docker.io
echo "=== Verificando instalaciones ==="
git --version
vim --version | head -1
python3 --version
echo "=== Instalación completa ==="