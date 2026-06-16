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

# ----------------------------------------
# Añadido respecto del ejemplo original v1
# ----------------------------------------

# Mostrar caducidad del secreto en caso de que tenga fecha de caducidad
if secret.properties.expires_on:
    print(f"El secreto caduca el: {secret.properties.expires_on}")

# Mostrar propiedades del secreto
print("\nPropiedades del secreto:")
for propiedad in secret.properties.__dict__:
    print(f"{propiedad}: {getattr(secret.properties, propiedad)}")

# Mostrar atributos internos del secreto
print("\nAtributos internos del secreto:")
# Recorrer el diccionario de atributos internos y mostrar key y value
attrs = dict(getattr(secret.properties, "_attributes", None))
for key, value in attrs.items():
    print(f"{key}: {value}")

# Mostrar fechas de creación, actualización y caducidad del secreto, y si está habilitado o no
print(f"\nCreación: {secret.properties.created_on}")
print(f"Actualización: {secret.properties.updated_on}")
print(f"Caducidad: {secret.properties.expires_on}")
print(f"Habilitado: {secret.properties.enabled}")
