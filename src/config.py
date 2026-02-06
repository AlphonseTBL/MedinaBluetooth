"""
Archivo de configuración de la aplicación.
Modifica estos valores para personalizar el comportamiento de la aplicación.
"""

import json
import os
from pathlib import Path


class Config:
    """
    Gestiona la configuración de la aplicación.
    
    Los valores de configuración se pueden establecer mediante:
    1. Archivo config.json (tiene prioridad)
    2. Valores por defecto definidos en este archivo
    """
    
    # Valores por defecto de la aplicación
    DEFAULTS = {
        # Configuración de la interfaz
        'appearance_mode': 'dark',  # 'dark', 'light', o 'system'
        'color_theme': 'blue',      # 'blue', 'green', 'dark-blue'
        'window_title': 'Monitor Bluetooth',
        'window_width': 900,
        'window_height': 600,
        
        # Configuración de Bluetooth
        'auto_reconnect': True,
        'reconnect_interval': 5,  # segundos
        'scan_timeout': 10,        # segundos
        
        # Configuración de datos
        'data_buffer_size': 100,   # Número de lecturas a mantener en memoria
        'update_interval': 100,    # milisegundos entre actualizaciones de UI
        'save_data': False,        # Guardar datos en archivo
        'data_file': 'bluetooth_data.csv',
        
        # Configuración del dispositivo
        # IMPORTANTE: Modifica estos valores según tu dispositivo
        'device_name_filter': None,  # None para mostrar todos, o nombre específico
        'device_address': None,       # None para selección manual, o dirección MAC
        'data_format': 'text',        # 'text', 'json', 'binary', 'custom'
        'data_separator': '\n',       # Separador de mensajes
        'encoding': 'utf-8',          # Codificación de caracteres
    }
    
    def __init__(self, config_file='config.json'):
        """
        Inicializa la configuración.
        
        Args:
            config_file: Ruta al archivo de configuración JSON
        """
        self.config_file = Path(config_file)
        self.settings = self.DEFAULTS.copy()
        self._load_config()
    
    def _load_config(self):
        """Carga la configuración desde el archivo JSON si existe."""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    user_config = json.load(f)
                    self.settings.update(user_config)
                    print(f"Configuración cargada desde {self.config_file}")
            except Exception as e:
                print(f"Error al cargar configuración: {e}")
                print("Usando configuración por defecto")
    
    def save_config(self):
        """Guarda la configuración actual en el archivo JSON."""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=4, ensure_ascii=False)
            print(f"Configuración guardada en {self.config_file}")
            return True
        except Exception as e:
            print(f"Error al guardar configuración: {e}")
            return False
    
    def get(self, key, default=None):
        """
        Obtiene un valor de configuración.
        
        Args:
            key: Clave de configuración
            default: Valor por defecto si la clave no existe
            
        Returns:
            Valor de configuración
        """
        return self.settings.get(key, default)
    
    def set(self, key, value):
        """
        Establece un valor de configuración.
        
        Args:
            key: Clave de configuración
            value: Nuevo valor
        """
        self.settings[key] = value
    
    def create_default_config_file(self):
        """
        Crea un archivo de configuración con valores por defecto.
        Útil para la primera ejecución.
        """
        if not self.config_file.exists():
            self.save_config()
            print(f"Archivo de configuración creado: {self.config_file}")


# Ejemplo de uso para crear archivo de configuración inicial
if __name__ == "__main__":
    config = Config()
    config.create_default_config_file()
    print("\nConfiguración actual:")
    for key, value in config.settings.items():
        print(f"  {key}: {value}")
