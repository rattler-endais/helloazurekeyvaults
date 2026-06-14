# Hello Azure KeyVaults

# ¿Que tenemos por aqui?
Del mismo modo que cuando empezamos a aprender un lenguaje de programación se suele comenzar con un ejemplo sencillo para mostrar un mensaje simple en pantalla (Hello World u Hola Mundo), este repositorio pretende ser un "Hola Mundo" para la implementación y uso de almacenes de secretos en Azure como medio seguro para almacenar datos sensibles (como contraseñas, tokens, certificados) y cómo acceder a esta información de forma segura desde nuestro código (aplicaciones, scripts, autotizaciones...). De ese modo sirve como base para su implementación en otros proyectos.

- Creación de almacén de secretos en Azure y protección del mismo
- Creación y actualización de secretos dentro del almacén
- Acceso a secretos desde un script python
- Acceso a secretos desde Ansible 

# Requisitos
Para comenzar, es imprescindible contar con acceso a Azure con permisos administrativos para poder crear el almacén de secretos (KeyVault). Si no dispones de una cuenta en Azure, puedes conseguir una gratuita con una cuenta de Microosft asociada a tu dirección de correo personal [en esta página de Microsoft](https://azure.microsoft.com/es-es/pricing/purchase-options/azure-account/)

Una vez creado el almacén, necesitaremos tener instalado [python](https://www.python.org/downloads/) si queremos probar el acceso mediante el ejemplo proporcionado en este lenguaje, o de [ansible](https://docs.ansible.com/), para probar el funcionamiento del ejemplo proporcionado para esta herramienta.


# 1) Qué piezas intervienen
Piensa en 4 piezas:

**El vault**

Es donde guardas el secreto. Key Vault puede almacenar secretos, claves y certificados.

**La identidad de la aplicación**

Tu servidor on‑prem no “entra” al vault como máquina; entra una identidad (normalmente un service principal). Microsoft documenta dos opciones para ese service principal: con password/secret o con certificado; y recomienda certificado por ser más seguro.

**Los permisos**

En Key Vault el acceso se separa entre plano de control (crear/administrar el vault) y plano de datos (leer/escribir secretos). Con RBAC puedes dar, por ejemplo, solo Key Vault Secrets User para leer o Key Vault Secrets Officer para gestionar secretos.

**La red**

Tu servidor on‑prem necesita llegar a:

Microsoft Entra ID para autenticarse,
el endpoint del vault https://<vault>.vault.azure.net,
y, si va a crear/configurar recursos, también a management.azure.com.
Todo eso va por HTTPS 443; ocasionalmente puede haber tráfico HTTP 80 para comprobaciones de revocación de certificados (CRL).

# 2) Qué patrón te recomiendo para un servidor on‑prem
**Opción A — La más práctica y universal**

Servidor on‑prem + service principal con certificado + Key Vault RBAC + firewall/IP allowlist
Es la mejor para empezar porque:

funciona con Linux/Windows on‑prem,
no depende de que el servidor esté en Azure,
evita meter passwords fijos de Azure en el servidor,
y es fácil de automatizar desde Python, PowerShell o shell.

**Opción B — La más cerrada de red**

Lo mismo que arriba, pero con Private Endpoint y acceso privado desde on‑prem a Azure
Es la opción más robusta a nivel de red:

el vault se expone por IP privada en una VNet,
puedes deshabilitar el acceso público,
y desde on‑prem llegas al vault por tu conectividad híbrida y con DNS adecuado.
Microsoft indica además que, si conectas desde on‑prem a un Key Vault con Private Endpoint, debes tener bien configurados los DNS forwarders/resolución para vault.azure.net y vaultcore.azure.net.

**Recomendación:**

Empieza por la Opción A si quieres algo operativo ya; evoluciona a Opción B si el vault va a guardar credenciales muy sensibles o si tu política de seguridad exige que no exista punto de acceso público.


# 3) Ejemplo práctico completo

Vamos a montar este escenario:

- Admin de Azure crea el vault y el secreto.
- Aplicación en servidor on‑prem solo necesita leer el secreto.
- La autenticación del servidor on‑prem se hace con service principal + certificado.
- El servidor on‑prem usará Python con azure-identity y azure-keyvault-secrets

## Paso 1. Crear el Key Vault
Microsoft documenta que puedes crear el vault con Azure CLI y recomienda habilitar [**RBAC** y **purge protection**](https://learn.microsoft.com/en-us/azure/key-vault/secrets/quick-create-cli).

Accede al [Portal de Azure](https://portal.azure.com) e inicia sesión con tu cuenta.

Abre una consola de Cloud Shell (icono cuadrado arriba a la derecha con forma de terminal)

Lo habitual es que se abra una terminal de tipo Power Shell, si es asi, cambia a una terminal tipo Bash para continuar.

TIP: Si desde la terminal clonas este repositorio te evitas copiar y pegar el código que te indico a continuación y tan sólo tendrás que editar el script proporcionado con los valores de acuerdo a tu entorno/preferencias.

Clonar repositorio: `git clone https://github.com/rattler-endais/helloazurekeyvaults.git`



```shell
# Variables de ejemplo
RG="rg-kv-onprem-demo"
LOC="westeurope"
KV="kv-onprem-demo-001"

# Crear grupo de recursos
az group create --name "$RG" --location "$LOC"

# Crear Key Vault con RBAC y purge protection
az keyvault create \
  --name "$KV" \
  --resource-group "$RG" \
  --enable-rbac-authorization true \
  --enable-purge-protection true
```
¿Qué has hecho aquí?

- has creado el contenedor lógico (resource group),
- has creado el vault,
- y has activado dos cosas importantes:

    - RBAC para permisos modernos,
    - purge protection para evitar borrado permanente prematuro

[ ] Marcar como completado

## Paso 2. Crear el secreto


[ ] Marcar como completado

