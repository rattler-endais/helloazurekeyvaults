import os
import time
import random
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
    """
    Carga variables desde .env ubicado junto a la aplicación.
    """
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    load_dotenv(env_path)

    logger.info("Cargando configuración desde .env")

    config = {
        "vault_name": os.getenv("KEYVAULT_NAME"),
        "secret_name": os.getenv("SECRET_NAME"),
        "client_id": os.getenv("AZURE_CLIENT_ID"),
        "tenant_id": os.getenv("AZURE_TENANT_ID"),
        "cert_path": os.getenv("AZURE_CLIENT_CERTIFICATE_PATH"),

        # parámetros opcionales de reintentos
        "max_retries": int(os.getenv("MAX_RETRIES", "4")),
        "backoff_initial": float(os.getenv("BACKOFF_INITIAL", "1.0")),
        "backoff_max": float(os.getenv("BACKOFF_MAX", "10.0")),
        "backoff_jitter": float(os.getenv("BACKOFF_JITTER", "0.5")),
    }

    missing = [
        k for k in [
            "vault_name",
            "secret_name",
            "client_id",
            "tenant_id",
            "cert_path"
        ] if not config[k]
    ]

    if missing:
        logger.error("Variables de entorno faltantes: %s", missing)
        raise ValueError(f"Faltan variables obligatorias en .env: {missing}")

    logger.debug("Configuración cargada correctamente")
    return config

#########################################################
# CLIENTE KEY VAULT
#########################################################

def create_client(vault_name):
    """
    Inicializa SecretClient contra Azure Key Vault.
    """
    vault_url = f"https://{vault_name}.vault.azure.net"
    logger.info("Inicializando cliente para vault: %s", vault_name)

    try:
        credential = DefaultAzureCredential()
        client = SecretClient(vault_url=vault_url, credential=credential)
        logger.info("Cliente Key Vault creado correctamente")
        return client

    except ClientAuthenticationError:
        logger.error("Error de autenticación con Azure al crear el cliente", exc_info=True)
        raise

    except Exception:
        logger.error("Error inesperado creando cliente de Key Vault", exc_info=True)
        raise

#########################################################
# LÓGICA DE RETRY
#########################################################

def is_retryable_exception(exc):
    """
    RECOMENDACIÓN PRÁCTICA:
    Reintentamos:
      - ServiceRequestError -> problemas transitorios de red/DNS/transporte.
      - HttpResponseError con 408, 429 o 5xx -> timeouts, throttling, errores temporales de servicio.
    No reintentamos:
      - ClientAuthenticationError -> credenciales/configuración.
      - ResourceNotFoundError -> secreto inexistente.
      - Otros errores no identificados como transitorios.
    """
    if isinstance(exc, ServiceRequestError):
        return True

    if isinstance(exc, HttpResponseError):
        status_code = getattr(exc, "status_code", None)
        if status_code in (408, 429):
            return True
        if status_code is not None and 500 <= status_code <= 599:
            return True

    return False


def calculate_backoff(attempt, initial, max_backoff, jitter):
    """
    Backoff exponencial con jitter:
      delay = min(initial * 2^(attempt-1), max_backoff) + random(0, jitter)
    """
    base = min(initial * (2 ** (attempt - 1)), max_backoff)
    return base + random.uniform(0, jitter)

#########################################################
# OBTENER SECRETO CON RETRIES
#########################################################

def get_secret_with_retry(client, secret_name, max_retries, backoff_initial, backoff_max, backoff_jitter):
    """
    Recupera el secreto con reintentos para errores transitorios.
    """
    attempt = 0

    while True:
        attempt += 1
        logger.info("Recuperando secreto '%s' (intento %d/%d)", secret_name, attempt, max_retries + 1)

        try:
            secret = client.get_secret(secret_name)
            logger.info("Secreto recuperado correctamente en el intento %d", attempt)
            logger.debug(
                "Metadata secreto: name=%s version=%s",
                secret.name,
                getattr(secret.properties, "version", "N/A")
            )
            return secret

        except ResourceNotFoundError:
            logger.error("El secreto '%s' no existe en el vault", secret_name, exc_info=True)
            raise

        except ClientAuthenticationError:
            logger.error("Error de autenticación accediendo al vault; no se reintenta", exc_info=True)
            raise

        except (ServiceRequestError, HttpResponseError, AzureError) as exc:
            retryable = is_retryable_exception(exc)

            if not retryable:
                logger.error("Error no reintentable accediendo al vault", exc_info=True)
                raise

            if attempt > max_retries:
                logger.error(
                    "Se agotaron los reintentos (%d) para recuperar el secreto '%s'",
                    max_retries,
                    secret_name,
                    exc_info=True
                )
                raise

            delay = calculate_backoff(
                attempt=attempt,
                initial=backoff_initial,
                max_backoff=backoff_max,
                jitter=backoff_jitter
            )

            logger.warning(
                "Error transitorio al recuperar '%s'. Reintento en %.2f segundos...",
                secret_name,
                delay,
                exc_info=True
            )
            time.sleep(delay)

        except Exception:
            logger.error("Error inesperado no controlado al recuperar el secreto", exc_info=True)
            raise

#########################################################
# MAIN
#########################################################

def main():
    logger.info("==== Inicio de aplicación ====")

    try:
        config = load_config()

        client = create_client(config["vault_name"])

        secret = get_secret_with_retry(
            client=client,
            secret_name=config["secret_name"],
            max_retries=config["max_retries"],
            backoff_initial=config["backoff_initial"],
            backoff_max=config["backoff_max"],
            backoff_jitter=config["backoff_jitter"]
        )

        # SOLO PARA PRUEBAS.
        # En producción, evita escribir el valor del secreto en logs.
        logger.warning("Mostrando el valor del secreto solo para pruebas")
        logger.info("Valor del secreto: %s", secret.value)

    except Exception:
        logger.critical("Error fatal en la ejecución", exc_info=True)

    finally:
        logger.info("==== Fin de aplicación ====")


if __name__ == "__main__":
    main()
