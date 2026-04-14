#!/bin/bash
LOGFILE="/var/log/install_deps.log"
PACKAGES=("git" "vim" "docker.io" "python3" "python3-pip" "cron")

echo "[$(date)] Iniciando instalación de dependencias" | tee -a $LOGFILE

for pkg in "${PACKAGES[@]}"; do
    if dpkg -l | grep -q "^ii  $pkg"; then
        echo "[OK] $pkg ya instalado" | tee -a $LOGFILE
    else
        echo "[...] Instalando $pkg" | tee -a $LOGFILE
        apt-get install -y $pkg >> $LOGFILE 2>&1
        echo "[OK] $pkg instalado" | tee -a $LOGFILE
    fi
done

echo "[$(date)] Instalación finalizada" | tee -a $LOGFILE