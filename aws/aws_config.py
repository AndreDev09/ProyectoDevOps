# aws/aws_config.py
# ─────────────────────────────────────────────────────────────────────────────
# Cliente boto3 apuntando a LocalStack en localhost:4566
# Usa estas funciones en todos los scripts del laboratorio.
# ─────────────────────────────────────────────────────────────────────────────
import boto3

ENDPOINT   = "http://localhost:4566"
REGION     = "us-east-1"
ACCESS_KEY = "test"          # LocalStack acepta cualquier valor
SECRET_KEY = "test"


def get_client(service: str):
    return boto3.client(
        service,
        endpoint_url=ENDPOINT,
        region_name=REGION,
        aws_access_key_id=ACCESS_KEY,
        aws_secret_access_key=SECRET_KEY,
    )


def get_resource(service: str):
    return boto3.resource(
        service,
        endpoint_url=ENDPOINT,
        region_name=REGION,
        aws_access_key_id=ACCESS_KEY,
        aws_secret_access_key=SECRET_KEY,
    )
