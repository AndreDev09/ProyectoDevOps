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

# 5. Instalar boto3 para consultar S3
pip install boto3

# 6. Crear bucket y objetos de prueba en LocalStack
python3 seed_s3_localstack.py

# 7. Ejecutar automatizacion en Python
python3 automation_tasks.py

El archivo `automation_tasks.py` automatiza tareas operativas del proyecto sin AWS:

- Verifica dependencias clave como `git`, `docker`, `python3` y `vim`.
- Consulta el estado de servicios locales como `LocalStack` y la app web.
- Utiliza `boto3` para conectarse a S3 en LocalStack.
- Lista buckets y objetos almacenados.
- Genera un reporte JSON automatico en `reports/resource_report.json`.
- Permite ejecutar scripts Bash existentes desde un solo punto.
- Incluye limpieza automatizada de logs.

El archivo `seed_s3_localstack.py` prepara datos de prueba en S3 usando `boto3`:

- Se conecta a `LocalStack` por `http://localhost:4566`.
- Crea el bucket `devops-demo-bucket` si no existe.
- Sube los objetos `evidencia.txt` y `reporte-demo.json`.
- Permite que `automation_tasks.py` liste buckets y objetos como evidencia.

Ejemplos de uso:

```bash
# Crear bucket y objetos de prueba
python3 seed_s3_localstack.py

# Ejecutar el verificador
python3 automation_tasks.py
```

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
