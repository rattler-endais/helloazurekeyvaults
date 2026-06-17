import os
import logging
from dotenv import load_dotenv

from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
from azure.core.exceptions import (
    AzureError,
    ClientAuthenticationError,
    ResourceNotFoundError,
    ServiceRequestError,
    HttpResponseError
)

#########################################################
# CONFIGURACIÓN LOGGING
#########################################################

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

logger = logging.getLogger("kv-client")

#########################################################
# CARGA CONFIG
#########################################################

def load_config():
    logger.info("Cargando configuración desde .env")

    load_dotenv()

    config = {
        "vault_name": os.getenv("KEYVAULT_NAME"),
        "secret_name": os.getenv("SECRET_NAME"),
        "client_id": os.getenv("AZURE_CLIENT_ID"),
        "tenant_id": os.getenv("AZURE_TENANT_ID"),
        "cert_path": os.getenv("AZURE_CLIENT_CERTIFICATE_PATH"),
    }

    missing = [k for k, v in config.items() if not v]
    if missing:
        logger.error(f"Variables de entorno faltantes: {missing}")
        raise ValueError(f"Faltan variables: {missing}")

    logger.debug(f"Configuración cargada correctamente: {config}")

    return config

#########################################################
# CLIENTE KEY VAULT
#########################################################

def create_client(vault_name):
    vault_url = f"https://{vault_name}.vault.azure.net"

    logger.info(f"Inicializando cliente para vault: {vault_name}")

    try:
        credential = DefaultAzureCredential()
        client = SecretClient(vault_url=vault_url, credential=credential)

        logger.info("Cliente Key Vault creado correctamente")
        return client

    except ClientAuthenticationError as e:
        logger.error("Error de autenticación con Azure", exc_info=True)
        raise

    except Exception as e:
        logger.error("Error inesperado creando cliente", exc_info=True)
        raise

#########################################################
# OBTENER SECRETO
#########################################################

def get_secret(client, secret_name):
    logger.info(f"Recuperando secreto: {secret_name}")

    try:
        secret = client.get_secret(secret_name)

        logger.info("Secreto recuperado correctamente")
        logger.debug(f"Metadata secreto: name={secret.name}, version={secret.properties.version}")

        return secret

    except ResourceNotFoundError:
        logger.error(f"El secreto '{secret_name}' no existe en el vault", exc_info=True)
        raise

    except ClientAuthenticationError:
        logger.error("Error de autenticación al acceder al vault", exc_info=True)
        raise

    except ServiceRequestError:
        logger.error("Error de red o conectividad con Azure", exc_info=True)
        raise

    except HttpResponseError as e:
        logger.error(f"Error HTTP del servicio: {e.message}", exc_info=True)
        raise

    except AzureError:
        logger.error("Error genérico del SDK de Azure", exc_info=True)
        raise

    except Exception:
        logger.error("Error inesperado al recuperar el secreto", exc_info=True)
        raise

#########################################################
# MAIN
#########################################################

def main():
    logger.info("==== Inicio de aplicación ====")

    try:
        config = load_config()

        client = create_client(config["vault_name"])

        secret = get_secret(client, config["secret_name"])

        # SOLO PARA TEST - en producción no imprimir secretos
        logger.warning("Mostrando el valor del secreto (solo pruebas)")
        logger.info(f"Valor del secreto: {secret.value}")

    except Exception as e:
        logger.critical("Error fatal en la ejecución", exc_info=True)

    finally:
        logger.info("==== Fin de aplicación ====")


if __name__ == "__main__":
    main()
