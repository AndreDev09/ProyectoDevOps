# aws/dynamodb_lab.py
# ─────────────────────────────────────────────────────────────────────────────
# Laboratorio DynamoDB — Puntos 1.6 a 1.8
#   1.6 Crear tabla con clave primaria
#   1.7 Insertar, modificar y eliminar registros con boto3
#   1.8 Restricciones de acceso con LabRole (simulado en LocalStack)
# ─────────────────────────────────────────────────────────────────────────────
import os, sys, uuid, datetime
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from aws.aws_config import get_client, get_resource
from botocore.exceptions import ClientError
import time

ddb_client   = get_client("dynamodb")
ddb_resource = get_resource("dynamodb")
TABLA        = "flask-eventos"


def titulo(texto):
    print(f"\n{'─'*60}")
    print(f"  {texto}")
    print(f"{'─'*60}")


# ═════════════════════════════════════════════════════════════════════════════
#  1.6 — Crear tabla
# ═════════════════════════════════════════════════════════════════════════════
titulo("1.6 — Crear tabla DynamoDB")
try:
    ddb_client.create_table(
        TableName=TABLA,
        AttributeDefinitions=[
            {"AttributeName": "event_id",  "AttributeType": "S"},
            {"AttributeName": "timestamp", "AttributeType": "S"},
        ],
        KeySchema=[
            {"AttributeName": "event_id",  "KeyType": "HASH"},
            {"AttributeName": "timestamp", "KeyType": "RANGE"},
        ],
        BillingMode="PAY_PER_REQUEST",
    )
    # Esperar a que la tabla esté activa
    waiter = ddb_client.get_waiter("table_exists")
    waiter.wait(TableName=TABLA)
    print(f"  ✔  Tabla '{TABLA}' creada.")
except ClientError as e:
    if e.response["Error"]["Code"] == "ResourceInUseException":
        print(f"  ℹ  Tabla '{TABLA}' ya existe.")
    else:
        raise

# Describir tabla
desc = ddb_client.describe_table(TableName=TABLA)["Table"]
print(f"  ℹ  Estado: {desc['TableStatus']}")
print(f"  ℹ  Partition Key: event_id (S)")
print(f"  ℹ  Sort Key:      timestamp (S)")


# ═════════════════════════════════════════════════════════════════════════════
#  1.7 — CRUD
# ═════════════════════════════════════════════════════════════════════════════
tabla = ddb_resource.Table(TABLA)

# ── INSERT ───────────────────────────────────────────────────────────────────
titulo("1.7a — Insertar registro (PutItem)")
event_id  = str(uuid.uuid4())
timestamp = datetime.datetime.utcnow().isoformat()

tabla.put_item(Item={
    "event_id":    event_id,
    "timestamp":   timestamp,
    "tipo":        "HTTP_REQUEST",
    "ruta":        "/",
    "status_code": "200",
    "mensaje":     "Solicitud procesada por Flask",
})
print(f"  ✔  Insertado: event_id={event_id}")

# ── READ ─────────────────────────────────────────────────────────────────────
titulo("1.7b — Leer registro (GetItem)")
resp = tabla.get_item(Key={"event_id": event_id, "timestamp": timestamp})
item = resp.get("Item", {})
print(f"  ✔  Registro encontrado:")
for k, v in item.items():
    print(f"     {k}: {v}")

# ── UPDATE ───────────────────────────────────────────────────────────────────
titulo("1.7c — Modificar registro (UpdateItem)")
tabla.update_item(
    Key={"event_id": event_id, "timestamp": timestamp},
    UpdateExpression="SET status_code = :sc, mensaje = :msg",
    ExpressionAttributeValues={
        ":sc":  "404",
        ":msg": "Recurso no encontrado",
    },
)
resp_upd = tabla.get_item(Key={"event_id": event_id, "timestamp": timestamp})
item_upd = resp_upd.get("Item", {})
print(f"  ✔  status_code actualizado: {item_upd.get('status_code')}")
print(f"  ✔  mensaje actualizado:     {item_upd.get('mensaje')}")

# ── DELETE ───────────────────────────────────────────────────────────────────
titulo("1.7d — Eliminar registro (DeleteItem)")
tabla.delete_item(Key={"event_id": event_id, "timestamp": timestamp})
resp_del = tabla.get_item(Key={"event_id": event_id, "timestamp": timestamp})
if "Item" not in resp_del:
    print(f"  ✔  Registro eliminado correctamente (ya no existe).")
else:
    print(f"  ✗  El registro sigue existiendo.")

# ── SCAN para verificar estado final ─────────────────────────────────────────
titulo("Estado final de la tabla (Scan)")
scan = tabla.scan()
print(f"  ℹ  Total de registros en tabla: {scan['Count']}")


# ═════════════════════════════════════════════════════════════════════════════
#  1.8 — Restricciones de acceso (LabRole simulado)
# ═════════════════════════════════════════════════════════════════════════════
titulo("1.8 — Política IAM de mínimo privilegio (referencia)")
politica = {
    "Version": "2012-10-17",
    "Statement": [{
        "Effect": "Allow",
        "Action": [
            "dynamodb:PutItem",
            "dynamodb:GetItem",
            "dynamodb:UpdateItem",
            "dynamodb:DeleteItem",
            "dynamodb:Query",
            "dynamodb:Scan",
        ],
        "Resource": f"arn:aws:dynamodb:us-east-1:*:table/{TABLA}",
    }],
}
import json
print("  Política aplicada a LabRole:")
print(json.dumps(politica, indent=4, ensure_ascii=False))
print("\n  ℹ  En AWS Academy, LabRole ya incluye estos permisos.")
print("  ℹ  En LocalStack no se requiere configuración IAM adicional.")

titulo("DynamoDB — Laboratorio completado ✔")
