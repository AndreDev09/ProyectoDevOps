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

---------------------------------------------------------

Pasos para Github:

# 1. Actualizar al codigo reciente
git fetch
git pull

# 2. Crear una nueva rama
git checkout -b ""

# 3. Guardar cambios hechos
git add . / git add (carpeta especifica)

# 4. Ver el status de los cambios
git status

# 5. Hacer commit de los cambios
git commit -m ""

# 6. Realizar el push al repositorio de github
git push