"""
rollback_lambda.py
==================
Función Lambda para rollback automático ante fallos en el pipeline CI/CD.
Se activa cuando CodePipeline reporta un fallo.

Eventos que activan esta Lambda:
  - CodePipeline: estado FAILED en cualquier stage
  - CloudWatch Alarm: métricas de error superan el umbral
  - SNS: notificación de fallo manual

Acciones de rollback:
  1. Detecta la última versión estable (S3 artifacts)
  2. Re-despliega el stack CloudFormation anterior
  3. Notifica el rollback por SNS / CloudWatch Logs
  4. Etiqueta el deployment fallido

Compatible con LocalStack y AWS real.
"""

import json
import os
import logging
import boto3
from datetime import datetime
from botocore.exceptions import ClientError

# ── Configuración ─────────────────────────────────────────────────────────────
logger = logging.getLogger()
logger.setLevel(logging.INFO)

LOCALSTACK_ENDPOINT  = os.environ.get("LOCALSTACK_ENDPOINT", "http://localstack:4566")
AWS_REGION           = os.environ.get("AWS_DEFAULT_REGION", "us-east-1")
STACK_NAME           = os.environ.get("STACK_NAME", "devops-project-stack")
ARTIFACTS_BUCKET     = os.environ.get("ARTIFACTS_BUCKET", "devops-project-artifacts")
PIPELINE_NAME        = os.environ.get("PIPELINE_NAME", "devops-project-pipeline")
SNS_TOPIC_ARN        = os.environ.get("SNS_TOPIC_ARN", "")
IS_LOCALSTACK        = os.environ.get("ENVIRONMENT", "localstack") == "localstack"


def get_client(service: str):
    """Crea cliente boto3 apuntando a LocalStack o AWS real."""
    kwargs = {
        "region_name": AWS_REGION,
        "aws_access_key_id":     os.environ.get("AWS_ACCESS_KEY_ID",     "test"),
        "aws_secret_access_key": os.environ.get("AWS_SECRET_ACCESS_KEY", "test"),
    }
    if IS_LOCALSTACK:
        kwargs["endpoint_url"] = LOCALSTACK_ENDPOINT
    return boto3.client(service, **kwargs)


def get_previous_template(s3_client) -> str | None:
    """
    Busca la última plantilla CloudFormation estable en S3.
    Retorna el contenido de la plantilla o None si no se encuentra.
    """
    try:
        resp = s3_client.list_objects_v2(
            Bucket=ARTIFACTS_BUCKET,
            Prefix="builds/",
        )
        objects = sorted(
            resp.get("Contents", []),
            key=lambda o: o["LastModified"],
            reverse=True,
        )

        # Buscar el build más reciente con plantilla CFN
        for obj in objects:
            if obj["Key"].endswith("infrastructure.yaml"):
                template_resp = s3_client.get_object(
                    Bucket=ARTIFACTS_BUCKET,
                    Key=obj["Key"]
                )
                content = template_resp["Body"].read().decode("utf-8")
                logger.info(f"Plantilla de rollback encontrada: {obj['Key']}")
                return content

        logger.warning("No se encontró plantilla previa en S3.")
        return None

    except ClientError as e:
        logger.error(f"Error buscando plantilla en S3: {e}")
        return None


def perform_cloudformation_rollback(cfn_client, template_body: str | None) -> dict:
    """
    Ejecuta el rollback del stack CloudFormation.
    Si hay template_body, re-despliega con esa versión.
    Si no, usa la opción de rollback nativa de CloudFormation.
    """
    result = {"action": None, "status": None, "error": None}

    try:
        if template_body:
            logger.info(f"Desplegando plantilla previa en stack: {STACK_NAME}")
            resp = cfn_client.update_stack(
                StackName=STACK_NAME,
                TemplateBody=template_body,
                Capabilities=["CAPABILITY_IAM", "CAPABILITY_NAMED_IAM"],
                Parameters=[
                    {"ParameterKey": "Environment",   "ParameterValue": "localstack"},
                    {"ParameterKey": "BucketPrefix",  "ParameterValue": "devops-project"},
                ],
            )
            result["action"] = "update_stack"
            result["status"] = "initiated"
            result["stack_id"] = resp.get("StackId")
            logger.info(f"Re-deploy iniciado: {resp.get('StackId')}")

        else:
            # Usar rollback nativo de CloudFormation
            logger.info("Usando rollback nativo de CloudFormation...")
            cfn_client.rollback_stack(StackName=STACK_NAME)
            result["action"] = "native_rollback"
            result["status"] = "initiated"

    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        if error_code == "ValidationError":
            logger.warning(f"Stack no necesita rollback o ya está estable: {e}")
            result["action"] = "no_action"
            result["status"] = "already_stable"
        else:
            logger.error(f"Error en rollback de CloudFormation: {e}")
            result["error"]  = str(e)
            result["status"] = "failed"

    return result


def stop_failed_pipeline(codepipeline_client, pipeline_name: str, execution_id: str):
    """Detiene la ejecución fallida del pipeline."""
    try:
        codepipeline_client.stop_pipeline_execution(
            pipelineName=pipeline_name,
            pipelineExecutionId=execution_id,
            abandon=True,
            reason="Rollback automático activado por Lambda",
        )
        logger.info(f"Pipeline execution {execution_id} detenida.")
    except ClientError as e:
        logger.warning(f"No se pudo detener el pipeline: {e}")


def send_notification(sns_client, message: dict):
    """Envía notificación SNS sobre el rollback."""
    if not SNS_TOPIC_ARN:
        logger.info("SNS no configurado. Saltando notificación.")
        return

    try:
        sns_client.publish(
            TopicArn=SNS_TOPIC_ARN,
            Subject=f"[ROLLBACK] {STACK_NAME} — {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}",
            Message=json.dumps(message, indent=2, default=str),
            MessageAttributes={
                "event_type": {
                    "DataType": "String",
                    "StringValue": "rollback",
                }
            }
        )
        logger.info("Notificación SNS enviada.")
    except ClientError as e:
        logger.warning(f"No se pudo enviar notificación SNS: {e}")


def tag_failed_deployment(ec2_client, failure_info: dict):
    """Etiqueta los recursos del deployment fallido para auditoría."""
    try:
        # Buscar instancias del stack
        resp = ec2_client.describe_instances(
            Filters=[
                {"Name": "tag:Project",     "Values": ["devops-project"]},
                {"Name": "instance-state-name", "Values": ["running", "stopped"]},
            ]
        )
        instance_ids = [
            i["InstanceId"]
            for r in resp["Reservations"]
            for i in r["Instances"]
        ]

        if instance_ids:
            ec2_client.create_tags(
                Resources=instance_ids,
                Tags=[
                    {"Key": "LastRollback",   "Value": datetime.utcnow().isoformat()},
                    {"Key": "RollbackReason", "Value": failure_info.get("reason", "pipeline_failure")},
                ]
            )
            logger.info(f"Etiquetas de rollback aplicadas a {len(instance_ids)} instancias.")

    except ClientError as e:
        logger.warning(f"No se pudieron etiquetar instancias: {e}")


# ── Handler principal ─────────────────────────────────────────────────────────
def lambda_handler(event: dict, context) -> dict:
    """
    Handler principal de la Lambda.

    Evento esperado desde CodePipeline:
    {
      "source": "aws.codepipeline",
      "detail": {
        "pipeline": "devops-project-pipeline",
        "execution-id": "abc-123",
        "state": "FAILED",
        "stage": "Deploy",
        "action": "Deploy-CFN"
      }
    }
    """
    logger.info("=== Lambda Rollback Activada ===")
    logger.info(f"Evento: {json.dumps(event, default=str)}")

    # ── Parsear el evento ──
    detail        = event.get("detail", event)  # soporta evento directo o de EventBridge
    pipeline_name = detail.get("pipeline", PIPELINE_NAME)
    execution_id  = detail.get("execution-id", "unknown")
    failed_stage  = detail.get("stage", "unknown")
    failed_action = detail.get("action", "unknown")
    failure_reason = detail.get("additionalInformation", "Pipeline failure")

    logger.info(f"Pipeline: {pipeline_name} | Execution: {execution_id}")
    logger.info(f"Stage fallido: {failed_stage} → Acción: {failed_action}")

    # ── Inicializar clientes ──
    s3_client           = get_client("s3")
    cfn_client          = get_client("cloudformation")
    codepipeline_client = get_client("codepipeline")
    ec2_client          = get_client("ec2")
    sns_client          = get_client("sns")

    rollback_result = {
        "timestamp":       datetime.utcnow().isoformat(),
        "stack_name":      STACK_NAME,
        "pipeline":        pipeline_name,
        "execution_id":    execution_id,
        "failed_stage":    failed_stage,
        "failure_reason":  failure_reason,
        "environment":     "localstack" if IS_LOCALSTACK else "aws",
    }

    # ── Paso 1: Detener pipeline ──
    logger.info("Paso 1: Deteniendo pipeline fallido...")
    stop_failed_pipeline(codepipeline_client, pipeline_name, execution_id)

    # ── Paso 2: Obtener plantilla previa ──
    logger.info("Paso 2: Buscando última versión estable...")
    previous_template = get_previous_template(s3_client)

    # ── Paso 3: Ejecutar rollback ──
    logger.info("Paso 3: Ejecutando rollback de CloudFormation...")
    cfn_result = perform_cloudformation_rollback(cfn_client, previous_template)
    rollback_result["cloudformation"] = cfn_result

    # ── Paso 4: Etiquetar recursos ──
    logger.info("Paso 4: Etiquetando recursos del deployment fallido...")
    tag_failed_deployment(ec2_client, {"reason": failure_reason})

    # ── Paso 5: Notificar ──
    logger.info("Paso 5: Enviando notificación...")
    rollback_result["status"] = (
        "rollback_completed" if cfn_result.get("status") in ("initiated", "already_stable")
        else "rollback_failed"
    )
    send_notification(sns_client, rollback_result)

    logger.info(f"=== Rollback finalizado: {rollback_result['status']} ===")

    return {
        "statusCode": 200 if "completed" in rollback_result["status"] else 500,
        "body": json.dumps(rollback_result, default=str),
    }


# ── Ejecutar localmente para pruebas ─────────────────────────────────────────
if __name__ == "__main__":
    # Evento de prueba simulando fallo de CodePipeline
    test_event = {
        "source": "aws.codepipeline",
        "detail": {
            "pipeline":              "devops-project-pipeline",
            "execution-id":          "test-exec-001",
            "state":                 "FAILED",
            "stage":                 "Deploy",
            "action":                "Deploy-CloudFormation",
            "additionalInformation": "Template validation failed",
        }
    }

    class FakeContext:
        function_name = "rollback-lambda"
        memory_limit_in_mb = 128
        invoked_function_arn = "arn:aws:lambda:us-east-1:000000000000:function:rollback"

    result = lambda_handler(test_event, FakeContext())
    print(json.dumps(json.loads(result["body"]), indent=2))
