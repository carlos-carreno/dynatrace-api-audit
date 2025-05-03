# Dynatrace API Audit Tool

## Descripción
Esta herramienta permite realizar una auditoría completa de las APIs de Dynatrace, generando un informe detallado de los endpoints accesibles y su estado.

## Características
- Auditoría de múltiples endpoints de Dynatrace
- Generación de informe en formato JSON
- Configuración flexible mediante variables de entorno
- Manejo de errores y registro de APIs fallidas

## Requisitos Previos
- Python 3.8+
- Bibliotecas: `requests`
- Credenciales de Dynatrace (Client ID, Client Secret, Environment ID, Account ID)

## Instalación
1. Clonar el repositorio
```bash
git clone https://github.com/carlos-carreno/dynatrace-api-audit.git
cd dynatrace-api-audit
```

2. Instalar dependencias
```bash
pip install requests
```

## Configuración
Configurar las siguientes variables de entorno:
- `DYNATRACE_ENV_ID`: ID de tu entorno de Dynatrace
- `DYNATRACE_ACCOUNT_ID`: ID de tu cuenta de Dynatrace
- `DYNATRACE_CLIENT_ID`: ID de cliente OAuth2
- `DYNATRACE_CLIENT_SECRET`: Secreto de cliente OAuth2

### Ejemplo de configuración (Linux/macOS)
```bash
export DYNATRACE_ENV_ID=your_env_id
export DYNATRACE_ACCOUNT_ID=your_account_id
export DYNATRACE_CLIENT_ID=your_client_id
export DYNATRACE_CLIENT_SECRET=your_client_secret
```

### Ejemplo de configuración (Windows PowerShell)
```powershell
$env:DYNATRACE_ENV_ID = "your_env_id"
$env:DYNATRACE_ACCOUNT_ID = "your_account_id"
$env:DYNATRACE_CLIENT_ID = "your_client_id"
$env:DYNATRACE_CLIENT_SECRET = "your_client_secret"
```

## Uso
```bash
python dynatrace_api_audit.py
```

## Estructura del Informe
El informe generado contendrá:
- Lista de APIs exitosas
- Lista de APIs fallidas
- Detalles de cada endpoint auditado

## Recursos de Soporte
- [Documentación de Dynatrace API](https://docs.dynatrace.com/docs/discover-dynatrace/references/dynatrace-api)
- [Guía de Autenticación de Dynatrace](https://docs.dynatrace.com/docs/manage-authentication-and-access)

## Contribuciones
Las contribuciones son bienvenidas. Por favor, abre un issue o realiza un pull request.

## Licencia
[Especificar la licencia]