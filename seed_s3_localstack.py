#!/usr/bin/env python3
import json
import time

try:
    import boto3
    from botocore.exceptions import BotoCoreError, ClientError, EndpointConnectionError
except ImportError:
    print("boto3 no esta instalado. Ejecuta: python -m pip install boto3")
    raise SystemExit(1)


ENDPOINT_URL = "http://localhost:4566"
REGION_NAME = "us-east-1"
BUCKET_NAME = "devops-demo-bucket"
OBJECTS = {
    "evidencia.txt": "Bucket de prueba para proyecto DevOps",
    "reporte-demo.json": json.dumps(
        {
            "project": "ProyectoDevOps",
            "environment": "localstack",
            "status": "demo-ready",
        },
        indent=2,
    ),
}


def get_s3_client():
    return boto3.client(
        "s3",
        endpoint_url=ENDPOINT_URL,
        aws_access_key_id="test",
        aws_secret_access_key="test",
        region_name=REGION_NAME,
    )


def bucket_exists(s3, bucket_name):
    try:
        s3.head_bucket(Bucket=bucket_name)
        return True
    except ClientError:
        return False


def ensure_bucket(s3, bucket_name):
    if bucket_exists(s3, bucket_name):
        print(f"Bucket encontrado: {bucket_name}")
        return

    s3.create_bucket(Bucket=bucket_name)
    print(f"Bucket creado: {bucket_name}")


def upload_demo_objects(s3, bucket_name):
    uploaded = []
    for object_name, content in OBJECTS.items():
        s3.put_object(Bucket=bucket_name, Key=object_name, Body=content.encode("utf-8"))
        uploaded.append(object_name)
    return uploaded


def wait_for_objects(s3, bucket_name, expected_objects, retries=5, delay=1):
    for _ in range(retries):
        response = s3.list_objects_v2(Bucket=bucket_name)
        current_objects = {
            obj["Key"] for obj in response.get("Contents", [])
        }
        if set(expected_objects).issubset(current_objects):
            return True
        time.sleep(delay)
    return False


def main():
    try:
        s3 = get_s3_client()
        ensure_bucket(s3, BUCKET_NAME)
        uploaded = upload_demo_objects(s3, BUCKET_NAME)
        if not wait_for_objects(s3, BUCKET_NAME, uploaded):
            print("No se pudieron confirmar todos los objetos en el bucket.")
            return 1
    except (BotoCoreError, ClientError, EndpointConnectionError) as error:
        print(f"No se pudo conectar a LocalStack S3 en {ENDPOINT_URL}: {error}")
        return 1
    except Exception as error:
        print(f"Ocurrio un error inesperado: {error}")
        return 1

    print("Objetos cargados:")
    for object_name in uploaded:
        print(f"- {object_name}")

    print("Seed completado correctamente.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
