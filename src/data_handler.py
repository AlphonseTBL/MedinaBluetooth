"""
Módulo para procesar y formatear datos recibidos
"""

import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class DataHandler:
    """
    Procesa y formatea los datos recibidos del dispositivo Bluetooth.
    
    Esta clase se encarga de convertir los datos crudos en información
    útil para mostrar en la interfaz.
    """
    
    def __init__(self):
        """Inicializa el manejador de datos."""
        self.data_history = []
        self.max_history = 100  # Máximo de registros a mantener
        logger.info("DataHandler inicializado")
    
    def process(self, raw_data):
        """
        Procesa datos crudos recibidos del dispositivo.
        
        Args:
            raw_data: Datos crudos (bytes o string)
            
        Returns:
            dict: Datos procesados con timestamp y formato
        """
        try:
            # Convertir bytes a string si es necesario
            if isinstance(raw_data, bytes):
                data_str = raw_data.decode('utf-8', errors='ignore')
            else:
                data_str = str(raw_data)
            
            # Crear registro de datos procesados
            processed = {
                'timestamp': datetime.now(),
                'raw': raw_data,
                'text': data_str,
                'length': len(raw_data),
                'hex': self._to_hex(raw_data)
            }
            
            # Agregar a historial
            self.data_history.append(processed)
            
            # Mantener tamaño máximo del historial
            if len(self.data_history) > self.max_history:
                self.data_history.pop(0)
            
            logger.debug(f"Datos procesados: {processed['text'][:50]}...")
            
            return processed
            
        except Exception as e:
            logger.error(f"Error procesando datos: {e}")
            return {
                'timestamp': datetime.now(),
                'raw': raw_data,
                'text': f"Error: {str(e)}",
                'length': 0,
                'hex': ''
            }
    
    def _to_hex(self, data):
        """
        Convierte datos a representación hexadecimal.
        
        Args:
            data: Datos a convertir
            
        Returns:
            str: Representación hexadecimal
        """
        if isinstance(data, bytes):
            return ' '.join([f'{b:02X}' for b in data])
        elif isinstance(data, str):
            return ' '.join([f'{ord(c):02X}' for c in data])
        return ''
    
    def get_history(self, count=None):
        """
        Obtiene el historial de datos.
        
        Args:
            count: Número de registros a obtener (None = todos)
            
        Returns:
            list: Lista de datos procesados
        """
        if count is None:
            return self.data_history
        else:
            return self.data_history[-count:]
    
    def clear_history(self):
        """Limpia el historial de datos."""
        self.data_history.clear()
        logger.info("Historial de datos limpiado")
    
    def export_history(self, filepath):
        """
        Exporta el historial a un archivo.
        
        Args:
            filepath: Ruta del archivo de destino
        """
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                for item in self.data_history:
                    f.write(f"{item['timestamp']}: {item['text']}\n")
            logger.info(f"Historial exportado a {filepath}")
        except Exception as e:
            logger.error(f"Error exportando historial: {e}")
