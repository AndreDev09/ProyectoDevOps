import json
import random

def lambda_handler(event, context):
    mensajes = [
        "Bienvenido al sistema financiero",
        "Operacion realizada con exito",
        "Saldo actualizado",
        "Transferencia procesada",
        "Servicio disponible"
    ]

    respuesta = random.choice(mensajes)

    return {
        "statusCode": 200,
        "body": json.dumps({
            "mensaje": respuesta
        })
    }