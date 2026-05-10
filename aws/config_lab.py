# aws/config_lab.py
# ─────────────────────────────────────────────────────────────────────────────
# Laboratorio AWS Config — Puntos 2.4, 2.5, 2.6
#   2.4 Auditar acciones mediante AWS Config (sin CloudTrail)
#   2.5 Supervisar cambios en recursos
#   2.6 Almacenar logs en bucket S3 dedicado
#
# NOTA: LocalStack emula AWS Config de forma básica.
#       Algunos waiters y reglas administradas pueden no estar disponibles.
#       El script maneja estos casos con try/except.
# ─────────────────────────────────────────────────────────────────────────────
import os, sys, json, time
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from aws.aws_config import get_client
from botocore.exceptions import ClientError

cfg    = get_client("config")
s3     = get_client("s3")
iam    = get_client("iam")

BUCKET_LOGS   = "flask-app-config-logs"
RECORDER_NAME = "flask-config-recorder"
CHANNEL_NAME  = "flask-delivery-channel"
ROLE_ARN      = "arn:aws:iam::000000000000:role/LabRole"   # simulado en LocalStack


def titulo(texto):
    print(f"\n{'─'*60}")
    print(f"  {texto}")
    print(f"{'─'*60}")


# ═════════════════════════════════════════════════════════════════════════════
#  2.6 — Bucket S3 dedicado para logs (se crea primero, Config lo necesita)
# ═════════════════════════════════════════════════════════════════════════════
titulo("2.6 — Bucket S3 dedicado para logs de Config")
try:
    s3.create_bucket(Bucket=BUCKET_LOGS)
    print(f"  ✔  Bucket '{BUCKET_LOGS}' creado.")
except ClientError as e:
    if e.response["Error"]["Code"] in ("BucketAlreadyExists", "BucketAlreadyOwnedByYou"):
        print(f"  ℹ  Bucket '{BUCKET_LOGS}' ya existe.")
    else:
        raise

# Cifrado en el bucket de logs
s3.put_bucket_encryption(
    Bucket=BUCKET_LOGS,
    ServerSideEncryptionConfiguration={
        "Rules": [{"ApplyServerSideEncryptionByDefault": {"SSEAlgorithm": "AES256"}}]
    },
)
print(f"  ✔  Cifrado AES-256 habilitado en '{BUCKET_LOGS}'.")

# Ciclo de vida: retener logs 365 días
s3.put_bucket_lifecycle_configuration(
    Bucket=BUCKET_LOGS,
    LifecycleConfiguration={
        "Rules": [{
            "ID":         "RetenerLogsConfig",
            "Status":     "Enabled",
            "Filter":     {"Prefix": ""},
            "Expiration": {"Days": 365},
        }]
    },
)
print(f"  ✔  Ciclo de vida configurado: logs se eliminarán a los 365 días.")

# Estructura de prefijos documentada
prefijos = [
    ("config-snapshots/",  "Snapshots de configuración de AWS Config"),
    ("config-history/",    "Historial de cambios de AWS Config"),
    ("access-logs/s3/",    "Logs de acceso al bucket principal"),
    ("cloudwatch-logs/",   "Logs exportados desde CloudWatch"),
    ("app-logs/flask/",    "Logs de la aplicación Flask"),
]
print(f"\n  Estructura de prefijos en '{BUCKET_LOGS}':")
for prefijo, desc in prefijos:
    # Crear objeto vacío para registrar el prefijo
    s3.put_object(Bucket=BUCKET_LOGS, Key=prefijo)
    print(f"     • {prefijo:<30} — {desc}")


# ═════════════════════════════════════════════════════════════════════════════
#  2.4 — Configurar AWS Config Recorder
# ═════════════════════════════════════════════════════════════════════════════
titulo("2.4 — Configurar AWS Config Recorder")
try:
    cfg.put_configuration_recorder(
        ConfigurationRecorder={
            "name": RECORDER_NAME,
            "roleARN": ROLE_ARN,
            "recordingGroup": {
                "allSupported": True,
                "includeGlobalResourceTypes": True,
            },
        }
    )
    print(f"  ✔  Config Recorder '{RECORDER_NAME}' configurado.")
except ClientError as e:
    print(f"  ⚠  Config Recorder: {e.response['Error']['Message']}")

# Delivery channel (enviar snapshots a S3)
try:
    cfg.put_delivery_channel(
        DeliveryChannel={
            "name":          CHANNEL_NAME,
            "s3BucketName":  BUCKET_LOGS,
            "s3KeyPrefix":   "config-snapshots",
            "configSnapshotDeliveryProperties": {
                "deliveryFrequency": "Six_Hours",
            },
        }
    )
    print(f"  ✔  Delivery channel configurado → bucket '{BUCKET_LOGS}'.")
except ClientError as e:
    print(f"  ⚠  Delivery channel: {e.response['Error']['Message']}")

# Iniciar grabación
try:
    cfg.start_configuration_recorder(ConfigurationRecorderName=RECORDER_NAME)
    print(f"  ✔  Grabación iniciada.")
except ClientError as e:
    print(f"  ⚠  Start recorder: {e.response['Error']['Message']}")

# Estado del recorder
try:
    estado = cfg.describe_configuration_recorder_status(
        ConfigurationRecorderNames=[RECORDER_NAME]
    )
    for r in estado.get("ConfigurationRecordersStatus", []):
        print(f"  ℹ  Recorder: {r['name']} — Grabando: {r.get('recording', False)}")
except ClientError as e:
    print(f"  ⚠  Estado: {e.response['Error']['Message']}")


# ═════════════════════════════════════════════════════════════════════════════
#  2.5 — Reglas de conformidad (managed rules)
# ═════════════════════════════════════════════════════════════════════════════
titulo("2.5 — Reglas de conformidad AWS Config")

reglas_managed = [
    {
        "nombre":      "s3-bucket-server-side-encryption-enabled",
        "fuente":      "AWS",
        "descripcion": "Verifica que los buckets S3 tengan SSE habilitado",
    },
    {
        "nombre":      "s3-bucket-versioning-enabled",
        "fuente":      "AWS",
        "descripcion": "Verifica que el versionado S3 esté activo",
    },
]

for regla in reglas_managed:
    try:
        cfg.put_config_rule(
            ConfigRule={
                "ConfigRuleName": regla["nombre"],
                "Description":    regla["descripcion"],
                "Source": {
                    "Owner":            regla["fuente"],
                    "SourceIdentifier": regla["nombre"].upper().replace("-", "_"),
                },
                "Scope": {"ComplianceResourceTypes": ["AWS::S3::Bucket"]},
            }
        )
        print(f"  ✔  Regla creada: {regla['nombre']}")
    except ClientError as e:
        # LocalStack puede no soportar todas las managed rules
        print(f"  ⚠  {regla['nombre']}: {e.response['Error']['Message']}")

# Consultar conformidad
time.sleep(2)
try:
    conformidad = cfg.describe_compliance_by_config_rule()
    reglas_resp = conformidad.get("ComplianceByConfigRules", [])
    if reglas_resp:
        print(f"\n  Estado de conformidad:")
        for r in reglas_resp:
            estado = r["Compliance"]["ComplianceType"]
            print(f"     • {r['ConfigRuleName']}: {estado}")
    else:
        print(f"  ℹ  Sin datos de conformidad aún (normal en LocalStack).")
except ClientError as e:
    print(f"  ℹ  Conformidad: {e.response['Error']['Message']}")

# Resumen comparativo Config vs CloudTrail
titulo("2.4 — Comparativa AWS Config vs CloudTrail")
print("""
  ┌─────────────────────────────────┬──────────────────────────────────┐
  │         AWS Config              │         AWS CloudTrail           │
  ├─────────────────────────────────┼──────────────────────────────────┤
  │ Registra estado de recursos     │ Registra llamadas a la API       │
  │ Detecta cambios de config       │ Registra quién hizo qué          │
  │ Auditoría de conformidad        │ Auditoría de seguridad/acceso    │
  │ Disponible en AWS Academy       │ Limitado en AWS Academy          │
  └─────────────────────────────────┴──────────────────────────────────┘
""")

titulo("AWS Config — Laboratorio completado ✔")
