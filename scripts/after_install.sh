#!/bin/bash
cd /var/www/html
echo "Deteniendo contenedores anteriores si existen..."
docker-compose down || true
echo "after_install completado."
