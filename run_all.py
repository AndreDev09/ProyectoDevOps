# run_all.py
# ─────────────────────────────────────────────────────────────────────────────
# Ejecuta todos los laboratorios en orden.
# Asegúrate de que LocalStack esté corriendo antes de ejecutar:
#   docker-compose up -d
# ─────────────────────────────────────────────────────────────────────────────
import subprocess, sys, time

SCRIPTS = [
    ("aws/s3_lab.py",         "PARTE 1 — S3 (puntos 1.1 a 1.5)"),
    ("aws/dynamodb_lab.py",   "PARTE 1 — DynamoDB (puntos 1.6 a 1.8)"),
    ("aws/cloudwatch_lab.py", "PARTE 2 — CloudWatch (puntos 2.1, 2.2, 2.3, 2.7)"),
    ("aws/config_lab.py",     "PARTE 2 — AWS Config (puntos 2.4, 2.5, 2.6)"),
]

print("=" * 60)
print("  LABORATORIO AWS — EJECUCIÓN COMPLETA")
print("=" * 60)

for script, descripcion in SCRIPTS:
    print(f"\n\n{'═'*60}")
    print(f"  ▶  {descripcion}")
    print(f"{'═'*60}\n")
    time.sleep(1)
    resultado = subprocess.run([sys.executable, script], capture_output=False)
    if resultado.returncode != 0:
        print(f"\n  ✗  Error en {script}. Revisa el output de arriba.")
        sys.exit(1)

print(f"\n\n{'═'*60}")
print("  ✔  Todos los laboratorios completados exitosamente.")
print(f"{'═'*60}\n")
