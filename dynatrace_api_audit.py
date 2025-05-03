import os
import json
import requests
from datetime import datetime
from config import DynatraceConfig

class DynatraceAPIAudit:
    def __init__(self, config):
        """
        Inicializa la auditoría de APIs de Dynatrace
        
        :param config: Configuración de Dynatrace
        """
        self.config = config
        self.config.validate()
        self.output_path = config.output_path
        self.base_url = config.get_base_url()
        self.token = self._get_bearer_token()
        self.audit_results = {
            'successful_apis': [],
            'failed_apis': []
        }

    def _get_bearer_token(self):
        """
        Obtiene un token bearer para autenticación
        
        :return: Token bearer
        """
        token_url = "https://sso.dynatrace.com/sso/oauth2/token"
        payload = {
            'grant_type': 'client_credentials',
            'client_id': self.config.client_id,
            'client_secret': self.config.client_secret,
            'scope': 'account-uac-read account-idm-read',
            'resource': f'urn:dtaccount:{self.config.account_id}'
        }
        
        response = requests.post(token_url, data=payload)
        response.raise_for_status()
        return response.json()['access_token']

    def _make_api_request(self, endpoint, method='GET', params=None):
        """
        Realiza una solicitud a la API de Dynatrace
        
        :param endpoint: Endpoint de la API
        :param method: Método HTTP
        :param params: Parámetros de la solicitud
        :return: Resultado de la solicitud
        """
        headers = {
            'Authorization': f'Bearer {self.token}',
            'accept': 'application/json'
        }
        
        full_url = f"{self.base_url}{endpoint}"
        
        try:
            if method == 'GET':
                response = requests.get(full_url, headers=headers, params=params)
            else:
                response = requests.request(method, full_url, headers=headers, params=params)
            
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {'error': str(e)}

    def audit_apis(self):
        """
        Realiza la auditoría de múltiples endpoints de Dynatrace
        """
        apis_to_audit = [
            ('/api/v2/apiTokens', 'API Tokens'),
            ('/api/v2/activeGates', 'Active Gates'),
            ('/api/v2/auditlogs', 'Audit Logs'),
            ('/api/v2/credentials', 'Credentials'),
            ('/api/v2/tags', 'Custom Tags'),
            ('/api/v2/events', 'Events'),
            ('/api/v2/metrics', 'Metrics'),
            ('/api/v2/entities', 'Monitored Entities')
        ]
        
        for endpoint, api_name in apis_to_audit:
            result = self._make_api_request(endpoint)
            
            if 'error' in result:
                self.audit_results['failed_apis'].append({
                    'endpoint': endpoint,
                    'name': api_name,
                    'error': result['error']
                })
            else:
                self.audit_results['successful_apis'].append({
                    'endpoint': endpoint,
                    'name': api_name,
                    'items_count': len(result.get('items', []))
                })

    def generate_report(self):
        """
        Genera un informe de los resultados de la auditoría
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_filename = os.path.join(self.output_path, f"dynatrace_api_audit_{timestamp}.json")
        
        # Asegurarse de que el directorio de salida exista
        os.makedirs(self.output_path, exist_ok=True)
        
        with open(report_filename, 'w', encoding='utf-8') as f:
            json.dump(self.audit_results, f, indent=2, ensure_ascii=False)
        
        print(f"Informe generado: {report_filename}")
        
        # Resumen en consola
        print("\n--- Resumen de Auditoría ---")
        print(f"APIs Exitosas: {len(self.audit_results['successful_apis'])}")
        print(f"APIs Fallidas: {len(self.audit_results['failed_apis'])}")
        
        return report_filename

def main():
    try:
        # Configuración desde variables de entorno o parámetros directos
        config = DynatraceConfig(
            environment_id=os.getenv('DYNATRACE_ENV_ID'),
            account_id=os.getenv('DYNATRACE_ACCOUNT_ID'),
            client_id=os.getenv('DYNATRACE_CLIENT_ID'),
            client_secret=os.getenv('DYNATRACE_CLIENT_SECRET')
        )
        
        audit = DynatraceAPIAudit(config)
        audit.audit_apis()
        audit.generate_report()
    
    except Exception as e:
        print(f"Error durante la auditoría: {e}")

if __name__ == "__main__":
    main()