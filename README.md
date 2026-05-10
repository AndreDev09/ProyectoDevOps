# AWS Labs — Flask + Docker + LocalStack

## Requisitos previos
- Docker Desktop corriendo
- Python 3.9+
- VS Code con extensión Python
- Cuenta gratuita en [localstack.cloud](https://localstack.cloud) (para el Auth Token)

---

## 1. Configurar el token de LocalStack

En la parte de `docker-compose.yml` reemplaza `PEGA_TU_TOKEN_AQUI` con un Auth Token personal:
```yaml
- LOCALSTACK_AUTH_TOKEN=ls-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
```

---

## 2. Instalar dependencias Python

Desde la terminal de VS Code, en la raíz del proyecto:
```bash
pip install boto3
```

---

## 3. Levantar los contenedores

```bash
docker-compose up -d
```

Espera ~20 segundos a que LocalStack esté healthy. Puedes verificarlo con:
```bash
docker-compose ps
```
Debe mostrar `healthy` en la columna de estado de LocalStack.

---

## 4. Ejecutar los laboratorios

### Opción A — Todos de una vez
```bash
py run_all.py
```

### Opción B — Uno por uno (recomendado para ir documentando)
```bash
python aws/s3_lab.py          # Puntos 1.1 – 1.5
python aws/dynamodb_lab.py    # Puntos 1.6 – 1.8
python aws/cloudwatch_lab.py  # Puntos 2.1, 2.2, 2.3, 2.7
python aws/config_lab.py      # Puntos 2.4, 2.5, 2.6
```

---

## 5. Estructura del proyecto

```
proyecto/
├── app/
│   ├── app.py              ← Flask con logging habilitado
│   ├── requirements.txt    ← Flask + boto3
│   └── Dockerfile
├── aws/
│   ├── aws_config.py       ← Cliente boto3 → LocalStack (importar en todos)
│   ├── s3_lab.py           ← Laboratorio S3
│   ├── dynamodb_lab.py     ← Laboratorio DynamoDB
│   ├── cloudwatch_lab.py   ← Laboratorio CloudWatch + Logs
│   └── config_lab.py       ← Laboratorio AWS Config
├── scripts/
│   ├── before_install.sh
│   ├── after_install.sh
│   └── start_app.sh
├── docker-compose.yml      ← LocalStack + Flask
├── appspec.yml
├── buildspec.yml
├── run_all.py              ← Ejecuta todo el laboratorio
└── .gitignore
```

---

## Notas importantes

- **No compartas tu Auth Token** en repositorios públicos. Agrégalo como variable de entorno local o en un archivo `.env` (ya está en `.gitignore`).
- LocalStack emula AWS Config de forma básica; algunas managed rules pueden no estar disponibles. Los scripts manejan esto con `try/except`.
- Los logs de Flask se guardan en `app/logs/flask.log` (ignorado por git).
