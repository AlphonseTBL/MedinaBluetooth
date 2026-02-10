"""
Módulo de configuración de la aplicación
"""

import json
import os
from pathlib import Path


class Config:
    """Gestiona la configuración de la aplicación."""
    
    def __init__(self, config_file='config.json'):
        """
        Inicializa la configuración.
        
        Args:
            config_file: Ruta al archivo de configuración
        """
        self.config_file = config_file
        self.config = self._load_config()
    
    def _load_config(self):
        """
        Carga la configuración desde el archivo.
        
        Returns:
            dict: Configuración cargada o configuración por defecto
        """
        default_config = {
            'appearance_mode': 'dark',
            'color_theme': 'blue',
            'window_size': '800x600',
            'scan_duration': 8,  # Duración del escaneo en segundos
            'last_device': None  # Último dispositivo conectado
        }
        
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    loaded_config = json.load(f)
                    default_config.update(loaded_config)
            except Exception as e:
                print(f"Error cargando configuración: {e}")
        
        return default_config
    
    def get(self, key, default=None):
        """
        Obtiene un valor de configuración.
        
        Args:
            key: Clave de configuración
            default: Valor por defecto si no existe
            
        Returns:
            Valor de configuración
        """
        return self.config.get(key, default)
    
    def set(self, key, value):
        """
        Establece un valor de configuración.
        
        Args:
            key: Clave de configuración
            value: Valor a establecer
        """
        self.config[key] = value
        self._save_config()
    
    def _save_config(self):
        """Guarda la configuración en el archivo."""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=4)
        except Exception as e:
            print(f"Error guardando configuración: {e}")
