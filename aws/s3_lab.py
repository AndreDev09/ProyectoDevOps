# aws/s3_lab.py
# ─────────────────────────────────────────────────────────────────────────────
# Laboratorio S3 — Puntos 1.1 a 1.5
#   1.1 Crear bucket y configurar permisos (LabRole simulado)
#   1.2 Habilitar versionado
#   1.3 Subir archivos del proyecto automáticamente
#   1.4 Habilitar cifrado SSE-S3
#   1.5 Configurar reglas de ciclo de vida
# ─────────────────────────────────────────────────────────────────────────────
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from aws.aws_config import get_client
from botocore.exceptions import ClientError

s3          = get_client("s3")
BUCKET      = "flask-app-artifacts"
LOGS_BUCKET = "flask-app-config-logs"
PROJECT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "app")

# ── Utilidad ──────────────────────────────────────────────────────────────────
def titulo(texto):
    print(f"\n{'─'*60}")
    print(f"  {texto}")
    print(f"{'─'*60}")


def crear_bucket(nombre):
    try:
        s3.create_bucket(Bucket=nombre)
        print(f"  ✔  Bucket '{nombre}' creado.")
    except ClientError as e:
        if e.response["Error"]["Code"] in ("BucketAlreadyExists", "BucketAlreadyOwnedByYou"):
            print(f"  ℹ  Bucket '{nombre}' ya existe.")
        else:
            raise


# ═════════════════════════════════════════════════════════════════════════════
#  1.1 — Crear buckets
# ═════════════════════════════════════════════════════════════════════════════
titulo("1.1 — Crear buckets S3")
crear_bucket(BUCKET)
crear_bucket(LOGS_BUCKET)

# Simular política LabRole: bloquear acceso público
for b in [BUCKET, LOGS_BUCKET]:
    s3.put_public_access_block(
        Bucket=b,
        PublicAccessBlockConfiguration={
            "BlockPublicAcls": True,
            "IgnorePublicAcls": True,
            "BlockPublicPolicy": True,
            "RestrictPublicBuckets": True,
        },
    )
    print(f"  ✔  Acceso público bloqueado en '{b}'.")


# ═════════════════════════════════════════════════════════════════════════════
#  1.2 — Habilitar versionado
# ═════════════════════════════════════════════════════════════════════════════
titulo("1.2 — Habilitar versionado en S3")
s3.put_bucket_versioning(
    Bucket=BUCKET,
    VersioningConfiguration={"Status": "Enabled"},
)
resp = s3.get_bucket_versioning(Bucket=BUCKET)
print(f"  ✔  Versionado: {resp.get('Status', 'Desactivado')}")


# ═════════════════════════════════════════════════════════════════════════════
#  1.3 — Subir archivos del proyecto
# ═════════════════════════════════════════════════════════════════════════════
titulo("1.3 — Subir archivos del proyecto a S3")
archivos = ["app.py", "requirements.txt", "Dockerfile"]

for archivo in archivos:
    ruta = os.path.join(PROJECT_DIR, archivo)
    if os.path.exists(ruta):
        s3.upload_file(ruta, BUCKET, f"proyecto/{archivo}")
        print(f"  ✔  Subido: proyecto/{archivo}")
    else:
        print(f"  ✗  No encontrado: {ruta}")

# Verificar objetos subidos
print("\n  Objetos en el bucket:")
resp = s3.list_objects_v2(Bucket=BUCKET, Prefix="proyecto/")
for obj in resp.get("Contents", []):
    print(f"     • {obj['Key']}  ({obj['Size']} bytes)")

# Demostrar versionado: subir app.py una segunda vez
s3.upload_file(os.path.join(PROJECT_DIR, "app.py"), BUCKET, "proyecto/app.py")
print("\n  Versiones de proyecto/app.py:")
versiones = s3.list_object_versions(Bucket=BUCKET, Prefix="proyecto/app.py")
for v in versiones.get("Versions", []):
    print(f"     • VersionId={v['VersionId']}  Latest={v['IsLatest']}  Fecha={v['LastModified']}")


# ═════════════════════════════════════════════════════════════════════════════
#  1.4 — Cifrado SSE-S3
# ═════════════════════════════════════════════════════════════════════════════
titulo("1.4 — Habilitar cifrado SSE-S3 (AES-256)")
s3.put_bucket_encryption(
    Bucket=BUCKET,
    ServerSideEncryptionConfiguration={
        "Rules": [{
            "ApplyServerSideEncryptionByDefault": {"SSEAlgorithm": "AES256"},
            "BucketKeyEnabled": True,
        }]
    },
)
config_enc = s3.get_bucket_encryption(Bucket=BUCKET)
algoritmo = config_enc["ServerSideEncryptionConfiguration"]["Rules"][0]["ApplyServerSideEncryptionByDefault"]["SSEAlgorithm"]
print(f"  ✔  Cifrado configurado: {algoritmo}")


# ═════════════════════════════════════════════════════════════════════════════
#  1.5 — Reglas de ciclo de vida
# ═════════════════════════════════════════════════════════════════════════════
titulo("1.5 — Reglas de ciclo de vida")
s3.put_bucket_lifecycle_configuration(
    Bucket=BUCKET,
    LifecycleConfiguration={
        "Rules": [
            {
                "ID": "EliminarLogsViejos",
                "Status": "Enabled",
                "Filter": {"Prefix": "logs/"},
                "Expiration": {"Days": 30},
            },
            {
                "ID": "ArchivarArtifactos",
                "Status": "Enabled",
                "Filter": {"Prefix": "proyecto/"},
                "Transitions": [{"Days": 90, "StorageClass": "STANDARD_IA"}],
                "Expiration": {"Days": 365},
            },
        ]
    },
)
reglas = s3.get_bucket_lifecycle_configuration(Bucket=BUCKET)
for r in reglas["Rules"]:
    print(f"  ✔  Regla '{r['ID']}' — Estado: {r['Status']}")

titulo("S3 — Laboratorio completado ✔")
