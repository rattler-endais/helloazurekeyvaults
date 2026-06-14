import os
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

VAULT_NAME = "kv-onprem-demo-001"
SECRET_NAME = "db-password-prod"

vault_url = f"https://{VAULT_NAME}.vault.azure.net"

# DefaultAzureCredential usará las variables de entorno:
# AZURE_CLIENT_ID, AZURE_TENANT_ID, AZURE_CLIENT_CERTIFICATE_PATH
credential = DefaultAzureCredential()

client = SecretClient(vault_url=vault_url, credential=credential)

secret = client.get_secret(SECRET_NAME)

print(f"Secreto leído correctamente. Nombre: {secret.name}")
print(f"Valor recuperado (solo para prueba): {secret.value}")
