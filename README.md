# AvanceDevOps

Pasos cualquier persona que clone tu repo solo necesita hacer:

En bash:

# 1. Clonar el repo
git clone https://github.com/AndreDev09/ProyectoDevOps.git

# 2. Levantar LocalStack
docker-compose up -d

# 3. Entrar al contenedor
docker exec -it localstack_main bash

# 4. Correr los scripts
./setup.sh
./install_deps.sh
./log_cleanup.sh