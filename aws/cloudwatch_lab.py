# aws/cloudwatch_lab.py
# ─────────────────────────────────────────────────────────────────────────────
# Laboratorio CloudWatch — Puntos 2.1, 2.2, 2.3, 2.7
#   2.1 Métricas de EC2 y S3 (simuladas en LocalStack)
#   2.2 Alarma para alto consumo de CPU
#   2.3 Dashboard personalizado
#   2.7 Envío de logs al log group de CloudWatch
# ─────────────────────────────────────────────────────────────────────────────
import os, sys, json, datetime, time
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from aws.aws_config import get_client

cw   = get_client("cloudwatch")
logs = get_client("logs")

INSTANCIA_ID  = "i-1234567890abcdef0"   # ID simulado para LocalStack
BUCKET        = "flask-app-artifacts"
ALARM_NAME    = "Alta-CPU-FlaskApp"
DASHBOARD     = "FlaskApp-Monitor"
LOG_GROUP_APP = "/ec2/flask-app/application"
LOG_GROUP_SYS = "/ec2/flask-app/syslog"


def titulo(texto):
    print(f"\n{'─'*60}")
    print(f"  {texto}")
    print(f"{'─'*60}")


# ═════════════════════════════════════════════════════════════════════════════
#  2.1 — Publicar métricas simuladas (EC2 y S3)
# ═════════════════════════════════════════════════════════════════════════════
titulo("2.1 — Publicar métricas de EC2 y S3 en CloudWatch")

# Métrica CPU (EC2)
cw.put_metric_data(
    Namespace="AWS/EC2",
    MetricData=[{
        "MetricName": "CPUUtilization",
        "Dimensions": [{"Name": "InstanceId", "Value": INSTANCIA_ID}],
        "Timestamp":  datetime.datetime.utcnow(),
        "Value":      45.5,
        "Unit":       "Percent",
    }],
)
print("  ✔  Métrica CPUUtilization publicada (45.5%)")

# Métrica NetworkIn (EC2)
cw.put_metric_data(
    Namespace="AWS/EC2",
    MetricData=[{
        "MetricName": "NetworkIn",
        "Dimensions": [{"Name": "InstanceId", "Value": INSTANCIA_ID}],
        "Timestamp":  datetime.datetime.utcnow(),
        "Value":      1024000,
        "Unit":       "Bytes",
    }],
)
print("  ✔  Métrica NetworkIn publicada (1 MB)")

# Métrica S3 BucketSizeBytes
cw.put_metric_data(
    Namespace="AWS/S3",
    MetricData=[{
        "MetricName": "BucketSizeBytes",
        "Dimensions": [
            {"Name": "BucketName",   "Value": BUCKET},
            {"Name": "StorageType",  "Value": "StandardStorage"},
        ],
        "Timestamp": datetime.datetime.utcnow(),
        "Value":     512000,
        "Unit":      "Bytes",
    }],
)
print("  ✔  Métrica BucketSizeBytes publicada (512 KB)")

# Consultar métricas publicadas
resp = cw.list_metrics(Namespace="AWS/EC2")
print(f"\n  Métricas disponibles en AWS/EC2:")
for m in resp.get("Metrics", []):
    print(f"     • {m['MetricName']}")


# ═════════════════════════════════════════════════════════════════════════════
#  2.2 — Alarma de CPU
# ═════════════════════════════════════════════════════════════════════════════
titulo("2.2 — Crear alarma: Alta-CPU-FlaskApp (umbral 80%)")
cw.put_metric_alarm(
    AlarmName=ALARM_NAME,
    AlarmDescription="CPU > 80% por mas de 10 minutos consecutivos",
    MetricName="CPUUtilization",
    Namespace="AWS/EC2",
    Statistic="Average",
    Dimensions=[{"Name": "InstanceId", "Value": INSTANCIA_ID}],
    Period=300,
    EvaluationPeriods=2,
    Threshold=80.0,
    ComparisonOperator="GreaterThanThreshold",
    TreatMissingData="notBreaching",
)
print(f"  ✔  Alarma '{ALARM_NAME}' creada.")

# Verificar alarma
alarmas = cw.describe_alarms(AlarmNames=[ALARM_NAME])
for a in alarmas.get("MetricAlarms", []):
    print(f"  ℹ  Nombre:    {a['AlarmName']}")
    print(f"  ℹ  Umbral:    {a['Threshold']}%")
    print(f"  ℹ  Operador:  {a['ComparisonOperator']}")
    print(f"  ℹ  Períodos:  {a['EvaluationPeriods']} x {a['Period']}s")

# Simular disparo de alarma (CPU al 95%)
titulo("2.2b — Simular CPU alta para probar alarma")
cw.put_metric_data(
    Namespace="AWS/EC2",
    MetricData=[{
        "MetricName": "CPUUtilization",
        "Dimensions": [{"Name": "InstanceId", "Value": INSTANCIA_ID}],
        "Timestamp":  datetime.datetime.utcnow(),
        "Value":      95.0,
        "Unit":       "Percent",
    }],
)
print("  ✔  Métrica CPUUtilization publicada (95%) — simula sobrecarga")


# ═════════════════════════════════════════════════════════════════════════════
#  2.3 — Dashboard
# ═════════════════════════════════════════════════════════════════════════════
titulo("2.3 — Crear dashboard: FlaskApp-Monitor")
widgets = [
    {
        "type": "metric", "x": 0, "y": 0, "width": 12, "height": 6,
        "properties": {
            "title":   "CPU EC2 — Flask App",
            "metrics": [["AWS/EC2", "CPUUtilization", "InstanceId", INSTANCIA_ID]],
            "period":  300,
            "stat":    "Average",
            "view":    "timeSeries",
        },
    },
    {
        "type": "metric", "x": 12, "y": 0, "width": 12, "height": 6,
        "properties": {
            "title":   "Red EC2 — NetworkIn / NetworkOut",
            "metrics": [
                ["AWS/EC2", "NetworkIn",  "InstanceId", INSTANCIA_ID],
                ["AWS/EC2", "NetworkOut", "InstanceId", INSTANCIA_ID],
            ],
            "period":  300,
            "stat":    "Sum",
            "view":    "timeSeries",
        },
    },
    {
        "type": "metric", "x": 0, "y": 6, "width": 12, "height": 6,
        "properties": {
            "title":   "Tamaño Bucket S3",
            "metrics": [[
                "AWS/S3", "BucketSizeBytes",
                "BucketName", BUCKET,
                "StorageType", "StandardStorage",
            ]],
            "period":  86400,
            "stat":    "Average",
            "view":    "timeSeries",
        },
    },
    {
        "type": "alarm", "x": 12, "y": 6, "width": 12, "height": 6,
        "properties": {
            "title":  "Estado de Alarmas",
            "alarms": [f"arn:aws:cloudwatch:us-east-1:000000000000:alarm:{ALARM_NAME}"],
        },
    },
]

cw.put_dashboard(
    DashboardName=DASHBOARD,
    DashboardBody=json.dumps({"widgets": widgets}),
)
print(f"  ✔  Dashboard '{DASHBOARD}' creado con {len(widgets)} widgets.")

dashboards = cw.list_dashboards()
for d in dashboards.get("DashboardEntries", []):
    print(f"  ℹ  Dashboard: {d['DashboardName']}")


# ═════════════════════════════════════════════════════════════════════════════
#  2.7 — CloudWatch Logs (simular agente)
# ═════════════════════════════════════════════════════════════════════════════
titulo("2.7 — Enviar logs de Flask a CloudWatch Logs")

for grupo in [LOG_GROUP_APP, LOG_GROUP_SYS]:
    try:
        logs.create_log_group(logGroupName=grupo)
        logs.put_retention_policy(logGroupName=grupo, retentionInDays=30)
        print(f"  ✔  Log group creado: {grupo} (retención: 30 días)")
    except logs.exceptions.ResourceAlreadyExistsException:
        print(f"  ℹ  Log group ya existe: {grupo}")

# Crear log stream
stream_name = INSTANCIA_ID
try:
    logs.create_log_stream(logGroupName=LOG_GROUP_APP, logStreamName=stream_name)
    print(f"  ✔  Log stream creado: {stream_name}")
except logs.exceptions.ResourceAlreadyExistsException:
    print(f"  ℹ  Log stream ya existe: {stream_name}")

# Enviar eventos de log simulando Flask
eventos_flask = [
    "INFO 2025-05-10 GET / — solicitud recibida — status 200",
    "INFO 2025-05-10 GET /health — health check — status 200",
    "WARNING 2025-05-10 GET /missing — ruta no encontrada — status 404",
    "ERROR 2025-05-10 Excepción no controlada en /api/data",
]

ts_base = int(datetime.datetime.utcnow().timestamp() * 1000)
log_events = [
    {"timestamp": ts_base + i * 1000, "message": msg}
    for i, msg in enumerate(eventos_flask)
]

logs.put_log_events(
    logGroupName=LOG_GROUP_APP,
    logStreamName=stream_name,
    logEvents=log_events,
)
print(f"  ✔  {len(log_events)} eventos de log enviados a CloudWatch Logs.")

# Leer los logs enviados
time.sleep(1)
resp_logs = logs.get_log_events(
    logGroupName=LOG_GROUP_APP,
    logStreamName=stream_name,
    startFromHead=True,
)
print(f"\n  Logs registrados en CloudWatch ({LOG_GROUP_APP}):")
for evento in resp_logs.get("events", []):
    print(f"     {evento['message']}")

titulo("CloudWatch — Laboratorio completado ✔")
