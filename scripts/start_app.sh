#!/bin/bash
cd /var/www/html
echo "Levantando la aplicación con Docker Compose..."
docker-compose up -d --build
echo "Aplicación iniciada en el puerto 5000."
