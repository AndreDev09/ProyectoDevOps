#!/usr/bin/env python3
import json
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen

try:
    import boto3
    from botocore.exceptions import BotoCoreError, ClientError, EndpointConnectionError
except ImportError:
    boto3 = None
    BotoCoreError = ClientError = EndpointConnectionError = Exception


REPORT_DIR = Path("reports")
REPORT_FILE = REPORT_DIR / "resource_report.json"

TOOLS = ["git", "docker", "python"]
SERVICES = {
    "localstack": "http://localhost:4566/_localstack/health",
    "app": "http://localhost:5000/health",
}


def check_tool(tool_name):
    """Verifica si una herramienta esta instalada."""
    return shutil.which(tool_name) is not None


def check_service(name, url):
    """Verifica si un servicio responde."""
    try:
        with urlopen(url, timeout=3) as response:
            return {
                "name": name,
                "status": "up",
                "code": response.status,
            }
    except URLError:
        return {
            "name": name,
            "status": "down",
            "code": None,
        }


def get_docker_containers():
    """ lista simple de contenedores activos."""
    if not check_tool("docker"):
        return []

    try:
        result = subprocess.run(
            ["docker", "ps", "--format", "{{.Names}}"],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        if result.returncode != 0:
            return []
        return [line for line in result.stdout.splitlines() if line.strip()]
    except Exception:
        return []


def list_s3_buckets_and_objects():
    """Lista buckets de S3 y sus objetos usando boto3 sobre LocalStack."""
    if boto3 is None:
        return {
            "enabled": False,
            "message": "boto3 no esta instalado",
            "buckets": [],
        }

    try:
        s3 = boto3.client(
            "s3",
            endpoint_url="http://localhost:4566",
            aws_access_key_id="test",
            aws_secret_access_key="test",
            region_name="us-east-1",
        )

        response = s3.list_buckets()
        buckets = []

        for bucket in response.get("Buckets", []):
            bucket_name = bucket["Name"]
            objects_response = s3.list_objects_v2(Bucket=bucket_name)
            objects = sorted(obj["Key"] for obj in objects_response.get("Contents", []))
            buckets.append({
                "name": bucket_name,
                "objects": objects,
            })

        return {
            "enabled": True,
            "message": "consulta S3 completada",
            "buckets": buckets,
        }
    except (BotoCoreError, ClientError, EndpointConnectionError) as error:
        return {
            "enabled": True,
            "message": f"no se pudo consultar S3: {error}",
            "buckets": [],
        }


def create_report():
    """reporte JSON con estado del entorno."""
    report = {
        "generated_at": datetime.now().isoformat(),
        "tools": {tool: check_tool(tool) for tool in TOOLS},
        "services": {name: check_service(name, url) for name, url in SERVICES.items()},
        "containers": get_docker_containers(),
        "s3": list_s3_buckets_and_objects(),
    }

    REPORT_DIR.mkdir(exist_ok=True)
    REPORT_FILE.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


def print_status(report):
    """resumen rapido en consola."""
    print("Estado del proyecto")
    print("\nHerramientas:")
    for tool, installed in report["tools"].items():
        print(f"- {tool}: {'instalado' if installed else 'no instalado'}")

    print("\nServicios:")
    for name, data in report["services"].items():
        print(f"- {name}: {data['status']}")

    print("\nContenedores activos:")
    if report["containers"]:
        for container in report["containers"]:
            print(f"- {container}")
    else:
        print("- No hay contenedores activos")

    print("\nBuckets S3:")
    if not report["s3"]["enabled"]:
        print(f"- {report['s3']['message']}")
    elif report["s3"]["buckets"]:
        for bucket in report["s3"]["buckets"]:
            print(f"- Bucket: {bucket['name']}")
            if bucket["objects"]:
                for obj in bucket["objects"]:
                    print(f"  - Objeto: {obj}")
            else:
                print("  - Sin objetos")
    else:
        print(f"- {report['s3']['message']}")

    print(f"\nReporte guardado en: {REPORT_FILE}")


if __name__ == "__main__":
    report = create_report()
    print_status(report)
