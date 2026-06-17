import os
from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient


def load_config():
    # Cargar variables desde .env
    load_dotenv()

    config = {
        "vault_name": os.getenv("KEYVAULT_NAME"),
        "secret_name": os.getenv("SECRET_NAME"),
        "secret_names" : os.getenv("SECRETS").split(","),
        "client_id": os.getenv("AZURE_CLIENT_ID"),
        "tenant_id": os.getenv("AZURE_TENANT_ID"),
        "cert_path": os.getenv("AZURE_CLIENT_CERTIFICATE_PATH"),
    }

    # Validación básica (muy recomendable en prod)
    missing = [k for k, v in config.items() if not v]
    if missing:
        raise ValueError(f"Faltan variables de entorno: {missing}")

    return config


def get_secret(config,secret_name):
    vault_url = f"https://{config['vault_name']}.vault.azure.net"

    credential = DefaultAzureCredential()

    client = SecretClient(
        vault_url=vault_url,
        credential=credential
    )

    secret = client.get_secret(secret_name)

    return secret


def main():
    try:
        config = load_config()

        # Recuperación de un secreto
        secret = get_secret(config, config["secret_name"])
        print("✅ Secreto obtenido correctamente")
        print(f"Nombre: {secret.name}")
        print(f"Valor: {secret.value}")  # solo para testing

        # Recuperación de varios secretos definidos en una lista
        secret_names = config['secret_names']
        for name in secret_names:
            secret = get_secret(config,name)
            print("✅ Secreto obtenido correctamente")
            print(f"Nombre: {secret.name}")
            print(f"Valor: {secret.value}")  # solo para testing
    except Exception as e:
        print("❌ Error:", str(e))


if __name__ == "__main__":
    main()

