"""
Procesador de datos recibidos del dispositivo Bluetooth.
Esta clase se encarga de interpretar y transformar los datos crudos.
"""

import json
import logging
from typing import Any, Dict, List
from datetime import datetime
from collections import deque

logger = logging.getLogger(__name__)


class DataHandler:
    """
    Procesa y estructura los datos recibidos del dispositivo Bluetooth.
    
    Esta clase es el punto central para personalizar cómo se interpretan
    los datos de tu dispositivo específico. Puedes modificar el método
    'process()' para adaptarlo a tu formato de datos particular.
    
    Características:
    - Decodificación de diferentes formatos (texto, JSON, binario)
    - Validación de datos
    - Almacenamiento de historial
    - Parseo personalizable
    """
    
    def __init__(self, buffer_size: int = 100):
        """
        Inicializa el procesador de datos.
        
        Args:
            buffer_size: Número máximo de lecturas a mantener en memoria
        """
        self.buffer_size = buffer_size
        self.data_history = deque(maxlen=buffer_size)
        self.last_value = None
        self.message_count = 0
        
        logger.info(f"DataHandler inicializado con buffer de {buffer_size}")
    
    def process(self, raw_data: bytes, format_type: str = 'text') -> Dict[str, Any]:
        """
        Procesa los datos crudos recibidos del Bluetooth.
        
        ESTE ES EL MÉTODO PRINCIPAL PARA PERSONALIZAR SEGÚN TU DISPOSITIVO.
        
        Args:
            raw_data: Datos en formato bytes recibidos del dispositivo
            format_type: Tipo de formato esperado ('text', 'json', 'binary', 'custom')
            
        Returns:
            Diccionario con los datos procesados y estructurados
        """
        try:
            self.message_count += 1
            timestamp = datetime.now()
            
            # Seleccionar método de procesamiento según formato
            if format_type == 'text':
                processed = self._process_text(raw_data)
            elif format_type == 'json':
                processed = self._process_json(raw_data)
            elif format_type == 'binary':
                processed = self._process_binary(raw_data)
            elif format_type == 'custom':
                processed = self._process_custom(raw_data)
            else:
                processed = {'raw': raw_data.decode('utf-8', errors='ignore')}
            
            # Agregar metadatos
            result = {
                'timestamp': timestamp,
                'message_number': self.message_count,
                'data': processed,
                'raw_bytes': raw_data
            }
            
            # Guardar en historial
            self.data_history.append(result)
            self.last_value = processed
            
            logger.debug(f"Datos procesados: {processed}")
            return result
            
        except Exception as e:
            logger.error(f"Error al procesar datos: {e}")
            return {
                'timestamp': datetime.now(),
                'message_number': self.message_count,
                'error': str(e),
                'raw_bytes': raw_data
            }
    
    def _process_text(self, raw_data: bytes) -> Dict[str, Any]:
        """
        Procesa datos en formato texto simple.
        
        Ejemplo de formato esperado:
        "temperatura:25.5,humedad:60.2,presion:1013.2"
        
        MODIFICA ESTA FUNCIÓN para adaptar a tu formato específico.
        """
        try:
            # Decodificar bytes a string
            text = raw_data.decode('utf-8').strip()
            
            # Ejemplo: parsear pares clave:valor separados por comas
            data = {}
            
            # Si el texto contiene comas, asumimos formato clave:valor
            if ',' in text and ':' in text:
                pairs = text.split(',')
                for pair in pairs:
                    if ':' in pair:
                        key, value = pair.split(':', 1)
                        # Intentar convertir a número si es posible
                        try:
                            data[key.strip()] = float(value.strip())
                        except ValueError:
                            data[key.strip()] = value.strip()
            else:
                # Si no tiene formato estructurado, guardar como texto
                data['message'] = text
            
            return data
            
        except Exception as e:
            logger.warning(f"Error en procesamiento de texto: {e}")
            return {'raw_text': raw_data.decode('utf-8', errors='ignore')}
    
    def _process_json(self, raw_data: bytes) -> Dict[str, Any]:
        """
        Procesa datos en formato JSON.
        
        Ejemplo de formato esperado:
        {"temperatura": 25.5, "humedad": 60.2, "sensor": "DHT22"}
        """
        try:
            text = raw_data.decode('utf-8').strip()
            data = json.loads(text)
            return data
        except json.JSONDecodeError as e:
            logger.warning(f"Error al decodificar JSON: {e}")
            return {'error': 'JSON inválido', 'raw': text}
        except Exception as e:
            logger.warning(f"Error en procesamiento de JSON: {e}")
            return {'error': str(e)}
    
    def _process_binary(self, raw_data: bytes) -> Dict[str, Any]:
        """
        Procesa datos en formato binario.
        
        Ejemplo: El primer byte es temperatura, segundo es humedad
        
        MODIFICA ESTA FUNCIÓN según el protocolo binario de tu dispositivo.
        """
        try:
            data = {}
            
            # Ejemplo de parseo binario (ajusta según tu protocolo)
            if len(raw_data) >= 2:
                # Primer byte: temperatura (0-255 representa 0-100°C)
                data['temperatura'] = (raw_data[0] / 255.0) * 100
                
                # Segundo byte: humedad (0-255 representa 0-100%)
                data['humedad'] = (raw_data[1] / 255.0) * 100
            
            # Agregar representación hexadecimal para debugging
            data['hex'] = raw_data.hex()
            
            return data
            
        except Exception as e:
            logger.warning(f"Error en procesamiento binario: {e}")
            return {'hex': raw_data.hex()}
    
    def _process_custom(self, raw_data: bytes) -> Dict[str, Any]:
        """
        Procesa datos con un formato personalizado específico.
        
        IMPLEMENTA AQUÍ tu lógica personalizada para tu dispositivo.
        
        Ejemplo para un dispositivo Arduino que envía:
        "T:25.5;H:60.2;P:1013.2\n"
        """
        try:
            text = raw_data.decode('utf-8').strip()
            data = {}
            
            # Ejemplo: parsear formato "CLAVE:VALOR;" 
            parts = text.split(';')
            for part in parts:
                if ':' in part:
                    key, value = part.split(':', 1)
                    try:
                        # Convertir códigos cortos a nombres legibles
                        key_map = {
                            'T': 'temperatura',
                            'H': 'humedad',
                            'P': 'presion',
                            'A': 'altitud',
                            'L': 'luz'
                        }
                        readable_key = key_map.get(key.strip(), key.strip())
                        data[readable_key] = float(value.strip())
                    except ValueError:
                        data[key.strip()] = value.strip()
            
            return data
            
        except Exception as e:
            logger.warning(f"Error en procesamiento personalizado: {e}")
            return {'raw': raw_data.decode('utf-8', errors='ignore')}
    
    def get_history(self, n: int = None) -> List[Dict[str, Any]]:
        """
        Obtiene el historial de datos procesados.
        
        Args:
            n: Número de elementos a retornar (None para todos)
            
        Returns:
            Lista de datos procesados
        """
        if n is None:
            return list(self.data_history)
        else:
            return list(self.data_history)[-n:]
    
    def get_last_value(self) -> Any:
        """Retorna el último valor procesado."""
        return self.last_value
    
    def clear_history(self):
        """Limpia el historial de datos."""
        self.data_history.clear()
        self.message_count = 0
        logger.info("Historial de datos limpiado")
    
    def export_to_csv(self, filename: str = 'bluetooth_data.csv') -> bool:
        """
        Exporta el historial de datos a un archivo CSV.
        
        Args:
            filename: Nombre del archivo de salida
            
        Returns:
            True si la exportación fue exitosa
        """
        try:
            import csv
            
            if not self.data_history:
                logger.warning("No hay datos para exportar")
                return False
            
            with open(filename, 'w', newline='', encoding='utf-8') as f:
                # Obtener todas las claves de datos
                all_keys = set()
                for entry in self.data_history:
                    if 'data' in entry and isinstance(entry['data'], dict):
                        all_keys.update(entry['data'].keys())
                
                # Crear encabezados
                fieldnames = ['timestamp', 'message_number'] + sorted(all_keys)
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                
                # Escribir datos
                for entry in self.data_history:
                    row = {
                        'timestamp': entry.get('timestamp', ''),
                        'message_number': entry.get('message_number', '')
                    }
                    if 'data' in entry and isinstance(entry['data'], dict):
                        row.update(entry['data'])
                    writer.writerow(row)
            
            logger.info(f"Datos exportados a {filename}")
            return True
            
        except Exception as e:
            logger.error(f"Error al exportar datos: {e}")
            return False


# Ejemplo de uso del DataHandler
if __name__ == "__main__":
    # Configurar logging para pruebas
    logging.basicConfig(level=logging.DEBUG)
    
    # Crear instancia
    handler = DataHandler()
    
    # Simular datos recibidos
    test_data = [
        b"temperatura:25.5,humedad:60.2",
        b'{"temp": 26.1, "hum": 58.3}',
        b"T:24.8;H:62.1;P:1013.2\n"
    ]
    
    print("\nProbando procesamiento de datos:\n")
    
    for i, data in enumerate(test_data, 1):
        print(f"Test {i}:")
        print(f"  Raw: {data}")
        
        if i == 1:
            result = handler.process(data, 'text')
        elif i == 2:
            result = handler.process(data, 'json')
        else:
            result = handler.process(data, 'custom')
        
        print(f"  Procesado: {result['data']}")
        print()
