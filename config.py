import os

class DynatraceConfig:
    def __init__(self, 
                 environment_id=None, 
                 account_id=None, 
                 client_id=None, 
                 client_secret=None, 
                 output_path=r"C:\Users\TI724\Downloads"):
        """
        Configuración de credenciales y parámetros para Dynatrace API
        
        :param environment_id: ID del entorno de Dynatrace
        :param account_id: ID de la cuenta de Dynatrace
        :param client_id: ID del cliente OAuth2
        :param client_secret: Secreto del cliente OAuth2
        :param output_path: Ruta de salida para informes
        """
        self.environment_id = environment_id or os.getenv('DYNATRACE_ENV_ID')
        self.account_id = account_id or os.getenv('DYNATRACE_ACCOUNT_ID')
        self.client_id = client_id or os.getenv('DYNATRACE_CLIENT_ID')
        self.client_secret = client_secret or os.getenv('DYNATRACE_CLIENT_SECRET')
        self.output_path = output_path

    def validate(self):
        """
        Valida que todos los parámetros necesarios estén configurados
        """
        required_params = [
            'environment_id', 
            'account_id', 
            'client_id', 
            'client_secret'
        ]
        
        missing_params = [
            param for param in required_params 
            if not getattr(self, param)
        ]
        
        if missing_params:
            raise ValueError(f"Parámetros faltantes: {', '.join(missing_params)}")
        
        return True

    def get_base_url(self):
        """
        Obtiene la URL base para las llamadas a la API
        """
        return f"https://{self.environment_id}.live.dynatrace.com"