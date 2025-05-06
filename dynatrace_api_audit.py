import requests
import json
import os
import time
import urllib.parse
import getpass
import sys
from datetime import datetime

# Configuraciones generales
account_id = "xxxxxxxxx"
environment_id = "xxxxxx"
output_dir = r"xxxxxxxxxxx"
output_path = os.path.join(output_dir, "dynatrace_api_results.txt")
log_path = os.path.join(output_dir, "dynatrace_api_log.txt")

# Configuraciones para SSO Token
client_id = "xxxxxx"
client_secret = "xxxxxxx"
api_token = "xxxxxxx"

# Inicializar contador de puntos de control
checkpoint_counter = 0

# Función para registrar punto de control
def log_checkpoint(message):
    global checkpoint_counter
    checkpoint_counter += 1
    checkpoint_msg = f"CHECKPOINT #{checkpoint_counter}: {message} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    
    print(checkpoint_msg)
    
    # Registrar en archivo de log
    with open(log_path, 'a', encoding='utf-8') as f:
        f.write(checkpoint_msg + "\n")
    
    # También añadir al archivo de resultados
    with open(output_path, 'a', encoding='utf-8') as f:
        f.write(f"# {checkpoint_msg}\n\n")

# Crear archivo de resultados
def create_result_file():
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(f"Dynatrace API Results - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("="*100 + "\n\n")
        
        # Crear o limpiar archivo de log
        with open(log_path, 'w', encoding='utf-8') as f:
            f.write(f"Dynatrace API Execution Log - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("="*100 + "\n\n")
        
        log_checkpoint("Archivos de resultados y log creados correctamente")
        return True
    except Exception as e:
        print(f"ERROR al crear archivos: {str(e)}")
        return False

# Añadir resultados al archivo
def append_to_file(title, data):
    try:
        with open(output_path, 'a', encoding='utf-8') as f:
            f.write(f"{title}\n")
            f.write("-"*100 + "\n")
            if isinstance(data, dict) or isinstance(data, list):
                f.write(json.dumps(data, indent=2) + "\n\n")
            else:
                f.write(str(data) + "\n\n")
        return True
    except Exception as e:
        print(f"ERROR al escribir en archivo: {str(e)}")
        return False

# Obtener token de Dynatrace SSO
def get_bearer_token():
    log_checkpoint("Solicitando Bearer Token desde Dynatrace SSO")
    
    # Define scopes, organized by category (reduced for testing)
    scopes_array = [
        # Account-related scopes
        "account-idm-read", "account-uac-read",
        # IAM scopes
        "iam:users:read", "iam:groups:read"
        # Add more scopes here after successful testing
    ]

    # Combine scopes into a single space-separated string
    scopes = " ".join(scopes_array)

    # API endpoint for token request
    token_url = "https://sso.dynatrace.com/sso/oauth2/token"

    # Prepare the request body with URL-encoded parameters
    body = {
        "grant_type": "client_credentials",
        "client_id": urllib.parse.quote(client_id),
        "client_secret": urllib.parse.quote(client_secret),
        "scope": urllib.parse.quote(scopes),
        "resource": urllib.parse.quote(f"urn:dtaccount:{account_id}")
    }

    # Convert body to URL-encoded string
    request_body = "&".join(f"{key}={value}" for key, value in body.items())
    print(f"Request Body: {request_body}")  # Debugging

    # Make the POST request to get the token
    try:
        response = requests.post(
            token_url,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data=request_body
        )
        response.raise_for_status()  # Raise exception for bad status codes
        bearer_token = response.json().get("access_token")
        append_to_file("Bearer Token obtenido", f"Token: {bearer_token[:30]}...truncado")
        log_checkpoint("Bearer Token obtenido correctamente")
        return bearer_token
    except requests.exceptions.RequestException as e:
        error_details = str(e)
        if hasattr(e, "response") and e.response:
            error_details += f" (HTTP Status: {e.response.status_code})"
            try:
                error_details += f" - Response: {e.response.text}"
            except:
                error_details += " - Unable to read response body"
        append_to_file("Error al obtener Bearer Token", error_details)
        log_checkpoint(f"Error al obtener Bearer Token: {error_details}")
        return None

# Función mejorada para manejar consultas paginadas
def paginated_api_request(url, headers, endpoint_name, base_url=None, params=None):
    """
    Realiza consultas paginadas a la API de Dynatrace, procesando automáticamente el nextPageKey
    
    Args:
        url (str): URL inicial para la consulta
        headers (dict): Headers para la consulta
        endpoint_name (str): Nombre del endpoint para el registro
        base_url (str, optional): URL base para construir URLs con nextPageKey
        params (dict, optional): Parámetros adicionales para la consulta inicial
    
    Returns:
        tuple: (éxito, fallo, datos combinados)
    """
    successful_requests = 0
    failed_requests = 0
    combined_data = None
    page_count = 1
    total_items = 0
    
    # Si hay parámetros, agregarlos a la URL inicial
    if params:
        param_str = "&".join([f"{k}={urllib.parse.quote(str(v))}" for k, v in params.items()])
        if "?" in url:
            url = f"{url}&{param_str}"
        else:
            url = f"{url}?{param_str}"
    
    # Consulta inicial
    print(f"Consultando {endpoint_name} (página {page_count})...")
    try:
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            append_to_file(f"Resultado de {endpoint_name} (página {page_count})", data)
            successful_requests += 1
            
            # Inicializar datos combinados
            combined_data = data.copy() if isinstance(data, dict) else data
            
            # Contar elementos si existe una lista de resultados
            if isinstance(data, dict):
                for key, value in data.items():
                    if isinstance(value, list) and key not in ["links", "metadata"]:
                        total_items += len(value)
                        print(f"  - Encontrados {len(value)} elementos en la clave '{key}'")
            
            # Verificar si hay más páginas
            next_page_key = data.get("nextPageKey")
            
            # Procesar páginas adicionales si existen
            while next_page_key:
                # Pausa para no sobrecargar la API
                time.sleep(1)
                
                page_count += 1
                print(f"Consultando {endpoint_name} (página {page_count})...")
                
                # Construir URL para la siguiente página
                if "?" in url and not base_url:
                    # Si la URL original ya tiene parámetros, usar esa como base
                    base_endpoint = url.split("?")[0]
                    next_url = f"{base_endpoint}?nextPageKey={urllib.parse.quote(next_page_key)}"
                elif base_url:
                    # Si se proporcionó un base_url específico, usarlo
                    next_url = f"{base_url}?nextPageKey={urllib.parse.quote(next_page_key)}"
                else:
                    # Caso simple: agregar nextPageKey a la URL original
                    next_url = f"{url}?nextPageKey={urllib.parse.quote(next_page_key)}"
                
                try:
                    next_response = requests.get(next_url, headers=headers)
                    
                    if next_response.status_code == 200:
                        next_data = next_response.json()
                        append_to_file(f"Resultado de {endpoint_name} (página {page_count})", next_data)
                        successful_requests += 1
                        
                        # Combinar datos si es posible
                        if isinstance(combined_data, dict) and isinstance(next_data, dict):
                            # Combinar listas de elementos
                            for key, value in next_data.items():
                                if key in combined_data and isinstance(value, list) and isinstance(combined_data[key], list) and key not in ["links", "metadata"]:
                                    # Extender la lista con los nuevos elementos
                                    combined_data[key].extend(value)
                                    total_items += len(value)
                                    print(f"  - Agregados {len(value)} elementos más en la clave '{key}' (total: {len(combined_data[key])})")
                                elif key != "nextPageKey":  # No copiar nextPageKey
                                    # Para otros tipos, simplemente actualizar
                                    combined_data[key] = value
                        
                        # Actualizar la clave de siguiente página
                        next_page_key = next_data.get("nextPageKey")
                    else:
                        error_msg = f"Código de estado: {next_response.status_code}, Mensaje: {next_response.text}"
                        append_to_file(f"Error en {endpoint_name} (página {page_count})", error_msg)
                        failed_requests += 1
                        break
                except Exception as e:
                    error_msg = f"Error en consulta de página {page_count}: {str(e)}"
                    print(error_msg)
                    append_to_file(f"Excepción en {endpoint_name} (página {page_count})", error_msg)
                    failed_requests += 1
                    break
            
            # Si hubo más de una página, guardar los datos combinados
            if page_count > 1:
                append_to_file(f"Resultado combinado de {endpoint_name} ({page_count} páginas, {total_items} elementos)", combined_data)
                log_checkpoint(f"Consulta paginada a {endpoint_name} completada: {page_count} páginas procesadas, {total_items} elementos encontrados")
            
        else:
            error_msg = f"Código de estado: {response.status_code}, Mensaje: {response.text}"
            append_to_file(f"Error en {endpoint_name}", error_msg)
            failed_requests += 1
            
    except Exception as e:
        error_msg = f"Error general en consulta: {str(e)}"
        print(error_msg)
        append_to_file(f"Excepción en {endpoint_name}", error_msg)
        failed_requests += 1
    
    return successful_requests, failed_requests, combined_data

# Función especializada para consultar entidades para un tipo específico
def fetch_entities_for_type(base_url, headers, entity_type):
    """
    Consulta todas las entidades para un tipo específico, manejando la paginación
    
    Args:
        base_url (str): URL base para las consultas
        headers (dict): Headers para la consulta
        entity_type (str): Tipo de entidad a consultar
    
    Returns:
        tuple: (éxito, fallo, entidades)
    """
    print(f"Consultando entities para el tipo {entity_type}...")
    
    # Construir la URL con el tipo codificado correctamente y el tamaño de página
    encoded_selector = urllib.parse.quote(f'type("{entity_type}")')
    entities_url = f"{base_url}/api/v2/entities"
    
    # Usar un tamaño de página grande para reducir el número de consultas necesarias
    # pero no demasiado grande para evitar problemas de rendimiento
    params = {
        "pageSize": "500",  # Aumentar el tamaño de página 
        "entitySelector": encoded_selector,
        "fields": "+properties,+tags,+managementZones"  # Obtener datos adicionales si es necesario
    }
    
    success, failed, entities_data = paginated_api_request(
        entities_url,
        headers,
        f"/api/v2/entities para tipo {entity_type}",
        base_url=entities_url,
        params=params
    )
    
    # Registrar estadísticas
    if entities_data and "entities" in entities_data:
        entity_count = len(entities_data["entities"])
        log_checkpoint(f"Encontradas {entity_count} entidades para el tipo {entity_type}")
    
    return success, failed, entities_data

# Consultar API de Dynatrace Environment
def fetch_environment_api():
    base_url = f"https://{environment_id}.live.dynatrace.com"
    headers = {
        "Authorization": f"Api-Token {api_token}",
        "Accept": "application/json; charset=utf-8"
    }
    
    log_checkpoint("Iniciando consultas a Dynatrace Environment API")
    
    # Lista de endpoints que podrían tener paginación
    paginated_endpoints = [
        "/api/v2/apiTokens",
        "/api/v2/activeGates",
        "/api/v2/activeGateTokens",
        "/api/v2/auditlogs",
        "/api/v2/credentials",
        "/api/v2/tags",
        "/api/config/v1/dashboards",
        "/api/config/v1/applications/mobile",
        "/api/v1/synthetic/monitors",
        "/api/config/v1/applications/web",
        "/api/v2/slo"
    ]
    
    successful_requests = 0
    failed_requests = 0
    
    # Procesar endpoints potencialmente paginados
    for endpoint in paginated_endpoints:
        endpoint_url = f"{base_url}{endpoint}"
        # Usar un tamaño de página grande para cada consulta
        params = {"pageSize": "500"}
        success, failed, _ = paginated_api_request(endpoint_url, headers, endpoint, base_url=endpoint_url, params=params)
        successful_requests += success
        failed_requests += failed
        # Pausa para no sobrecargar la API
        time.sleep(1)
    
    # Caso especial para entity types y entities
    try:
        # Primero obtener todos los tipos de entidades
        entity_types_url = f"{base_url}/api/v2/entityTypes"
        print("Consultando entity types...")
        
        # Usar un tamaño de página grande para entity types
        params = {"pageSize": "500"}
        
        success, failed, entity_types_data = paginated_api_request(
            entity_types_url, 
            headers, 
            "/api/v2/entityTypes",
            base_url=entity_types_url,
            params=params
        )
        successful_requests += success
        failed_requests += failed
        
        # Consultar entidades para cada tipo usando nuestra función especializada
        if entity_types_data and "types" in entity_types_data and entity_types_data["types"]:
            total_types = len(entity_types_data["types"])
            log_checkpoint(f"Consultando entidades para {total_types} tipos encontrados")
            
            for i, type_info in enumerate(entity_types_data["types"], 1):
                entity_type = type_info["type"]  # Extraer el valor "type" de cada tipo
                print(f"Procesando tipo {i}/{total_types}: {entity_type}")
                
                # Usar nuestra función especializada para consultar entidades
                entity_success, entity_failed, _ = fetch_entities_for_type(base_url, headers, entity_type)
                
                successful_requests += entity_success
                failed_requests += entity_failed
                
                # Pausa para no sobrecargar la API
                time.sleep(1)
        else:
            log_checkpoint("No se encontraron tipos de entidades para consultar")
    except Exception as e:
        error_msg = f"Error en procesamiento de entity types: {str(e)}"
        print(error_msg)
        append_to_file("Excepción en procesamiento de entity types", error_msg)
        failed_requests += 1
    
    log_checkpoint(f"Consultas a Environment API completadas: {successful_requests} exitosas, {failed_requests} fallidas")
    return successful_requests, failed_requests

# Consultar API de Dynatrace Account Management
def fetch_account_management_api(bearer_token):
    if not bearer_token:
        log_checkpoint("No se puede consultar Account Management API: Bearer Token no disponible")
        return 0, 1
    
    base_url = "https://api.dynatrace.com"
    headers = {
        "Authorization": f"Bearer {bearer_token}",
        "Accept": "application/json"
    }
    
    log_checkpoint("Iniciando consultas a Dynatrace Account Management API")
    
    # Lista de endpoints
    endpoints = [
        f"/iam/v1/accounts/{account_id}/groups",
        f"/iam/v1/accounts/{account_id}/users",
        f"/sub/v2/accounts/{account_id}/subscriptions"
    ]
    
    successful_requests = 0
    failed_requests = 0
    
    # Procesar endpoints potencialmente paginados
    for endpoint in endpoints:
        endpoint_url = f"{base_url}{endpoint}"
        # Usar un tamaño de página grande para cada consulta
        params = {"pageSize": "500"}
        success, failed, _ = paginated_api_request(endpoint_url, headers, endpoint, base_url=endpoint_url, params=params)
        successful_requests += success
        failed_requests += failed
        # Pausa para no sobrecargar la API
        time.sleep(1)
    
    log_checkpoint(f"Consultas a Account Management API completadas: {successful_requests} exitosas, {failed_requests} fallidas")
    return successful_requests, failed_requests

def main():
    start_time = datetime.now()
    print(f"Iniciando consulta unificada de APIs de Dynatrace. Los resultados se guardarán en {output_path}")
    print(f"El log de ejecución se guardará en {log_path}")
    
    # Verificar si el directorio de salida existe
    if not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
        print(f"Directorio creado: {output_dir}")
    
    # Crear archivo de resultados
    if not create_result_file():
        print("Error al crear archivos de resultados. Abortando.")
        sys.exit(1)
    
    try:
        # Parte 1: Obtener Bearer Token
        bearer_token = get_bearer_token()
        
        # Parte 2: Consultas a Environment API
        print("Consultando Environment API...")
        env_success, env_failed = fetch_environment_api()
        
        # Parte 3: Consultas a Account Management API
        print("Consultando Account Management API...")
        acct_success, acct_failed = fetch_account_management_api(bearer_token)
        
        # Resumen final
        end_time = datetime.now()
        execution_time = (end_time - start_time).total_seconds()
        
        summary = f"""
RESUMEN DE EJECUCIÓN
===================
Fecha y hora: {end_time.strftime('%Y-%m-%d %H:%M:%S')}
Tiempo total de ejecución: {execution_time:.2f} segundos

RESULTADOS:
- Obtención de Bearer Token: {'Exitosa' if bearer_token else 'Fallida'}
- Environment API: {env_success} consultas exitosas, {env_failed} fallidas
- Account Management API: {acct_success} consultas exitosas, {acct_failed} fallidas
- Total: {env_success + acct_success} consultas exitosas, {env_failed + acct_failed} fallidas

Archivos generados:
- Resultados: {output_path}
- Log: {log_path}
        """
        
        print(summary)
        append_to_file("RESUMEN FINAL", summary)
        
        log_checkpoint("Proceso completado exitosamente")
        print(f"Proceso completado. Revisa los resultados en {output_path}")
        return 0
    except Exception as e:
        error_msg = f"Error general en la ejecución: {str(e)}"
        print(error_msg)
        append_to_file("ERROR FATAL", error_msg)
        log_checkpoint(f"Proceso terminado con errores: {str(e)}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
