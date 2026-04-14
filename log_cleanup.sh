#!/bin/bash
LOG_DIR="/var/log"
DAYS=7

echo "[$(date)] Iniciando limpieza de logs..."
find $LOG_DIR -name "*.log" -mtime +1 -exec gzip {} \;
find $LOG_DIR -name "*.gz" -mtime +$DAYS -delete
echo "[$(date)] Limpieza completada."