"""
Gestor de conexiones Bluetooth.
Maneja el descubrimiento, conexión y comunicación con dispositivos Bluetooth.
"""

import bluetooth
import threading
import time
import logging
from typing import Callable, Optional, List, Dict

logger = logging.getLogger(__name__)


class BluetoothManager:
    """
    Gestiona todas las operaciones de Bluetooth.
    
    Esta clase encapsula la lógica de conexión y comunicación con dispositivos
    Bluetooth, proporcionando una interfaz simple para el resto de la aplicación.
    
    Características:
    - Escaneo de dispositivos cercanos
    - Conexión/desconexión automática
    - Recepción de datos en tiempo real
    - Reconexión automática en caso de pérdida de conexión
    """
    
    def __init__(self):
        """Inicializa el gestor de Bluetooth."""
        self.socket: Optional[bluetooth.BluetoothSocket] = None
        self.connected = False
        self.device_address = None
        self.device_name = None
        
        # Callbacks para notificar eventos
        self.data_callback: Optional[Callable] = None
        self.connection_callback: Optional[Callable] = None
        
        # Control de hilos
        self.receiving_thread: Optional[threading.Thread] = None
        self.stop_receiving = threading.Event()
        
        logger.info("BluetoothManager inicializado")
    
    def scan_devices(self, duration: int = 8) -> List[Dict[str, str]]:
        """
        Escanea dispositivos Bluetooth cercanos.
        
        Args:
            duration: Tiempo de escaneo en segundos
            
        Returns:
            Lista de diccionarios con 'address' y 'name' de cada dispositivo
        """
        logger.info(f"Escaneando dispositivos durante {duration} segundos...")
        
        try:
            # Descubrir dispositivos cercanos
            nearby_devices = bluetooth.discover_devices(
                duration=duration,
                lookup_names=True,
                flush_cache=True,
                lookup_class=False
            )
            
            # Formatear resultados
            devices = [
                {'address': addr, 'name': name or 'Desconocido'}
                for addr, name in nearby_devices
            ]
            
            logger.info(f"Encontrados {len(devices)} dispositivos")
            return devices
            
        except Exception as e:
            logger.error(f"Error al escanear dispositivos: {e}")
            return []
    
    def connect(self, device_address: str, port: int = 1) -> bool:
        """
        Conecta a un dispositivo Bluetooth.
        
        Args:
            device_address: Dirección MAC del dispositivo
            port: Puerto RFCOMM (por defecto 1 para SPP)
            
        Returns:
            True si la conexión fue exitosa, False en caso contrario
        """
        try:
            logger.info(f"Intentando conectar a {device_address}:{port}")
            
            # Crear socket Bluetooth RFCOMM
            self.socket = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
            
            # Intentar conexión
            self.socket.connect((device_address, port))
            
            # Guardar información del dispositivo
            self.device_address = device_address
            self.connected = True
            
            # Intentar obtener el nombre del dispositivo
            try:
                self.device_name = bluetooth.lookup_name(device_address)
            except:
                self.device_name = "Desconocido"
            
            logger.info(f"Conectado exitosamente a {self.device_name}")
            
            # Iniciar thread de recepción de datos
            self._start_receiving()
            
            # Notificar cambio de conexión
            if self.connection_callback:
                self.connection_callback(True, {
                    'address': self.device_address,
                    'name': self.device_name
                })
            
            return True
            
        except Exception as e:
            logger.error(f"Error al conectar: {e}")
            self.connected = False
            return False
    
    def disconnect(self):
        """Desconecta del dispositivo Bluetooth actual."""
        if not self.connected:
            return
        
        logger.info("Desconectando dispositivo Bluetooth")
        
        # Detener recepción de datos
        self._stop_receiving()
        
        # Cerrar socket
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
            self.socket = None
        
        self.connected = False
        self.device_address = None
        
        # Notificar cambio de conexión
        if self.connection_callback:
            self.connection_callback(False, None)
        
        logger.info("Desconectado")
    
    def send_data(self, data: str) -> bool:
        """
        Envía datos al dispositivo Bluetooth.
        
        Args:
            data: Cadena de texto a enviar
            
        Returns:
            True si el envío fue exitoso, False en caso contrario
        """
        if not self.connected or not self.socket:
            logger.warning("No hay conexión activa para enviar datos")
            return False
        
        try:
            self.socket.send(data)
            logger.debug(f"Datos enviados: {data}")
            return True
        except Exception as e:
            logger.error(f"Error al enviar datos: {e}")
            return False
    
    def _start_receiving(self):
        """Inicia el thread de recepción de datos."""
        self.stop_receiving.clear()
        self.receiving_thread = threading.Thread(
            target=self._receive_loop,
            daemon=True
        )
        self.receiving_thread.start()
        logger.info("Thread de recepción iniciado")
    
    def _stop_receiving(self):
        """Detiene el thread de recepción de datos."""
        self.stop_receiving.set()
        if self.receiving_thread:
            self.receiving_thread.join(timeout=2)
        logger.info("Thread de recepción detenido")
    
    def _receive_loop(self):
        """
        Loop principal de recepción de datos.
        Se ejecuta en un thread separado para no bloquear la UI.
        """
        logger.info("Iniciando recepción de datos")
        
        while not self.stop_receiving.is_set() and self.connected:
            try:
                # Recibir datos del socket (bloqueante)
                data = self.socket.recv(1024)
                
                if data:
                    # Notificar datos recibidos mediante callback
                    if self.data_callback:
                        self.data_callback(data)
                else:
                    # Si recv retorna vacío, la conexión se cerró
                    logger.warning("Conexión cerrada por el dispositivo")
                    self.disconnect()
                    break
                    
            except bluetooth.BluetoothError as e:
                if self.connected:  # Solo registrar si aún deberíamos estar conectados
                    logger.error(f"Error de Bluetooth: {e}")
                    self.disconnect()
                break
            except Exception as e:
                if self.connected:
                    logger.error(f"Error en recepción: {e}")
                    self.disconnect()
                break
        
        logger.info("Loop de recepción finalizado")
    
    def set_data_callback(self, callback: Callable):
        """
        Establece la función callback para datos recibidos.
        
        Args:
            callback: Función que será llamada cuando se reciban datos.
                     Debe aceptar un parámetro (bytes de datos recibidos)
        """
        self.data_callback = callback
    
    def set_connection_callback(self, callback: Callable):
        """
        Establece la función callback para cambios de conexión.
        
        Args:
            callback: Función que será llamada cuando cambie el estado de conexión.
                     Debe aceptar dos parámetros (connected: bool, device_info: dict)
        """
        self.connection_callback = callback
    
    def is_connected(self) -> bool:
        """Retorna True si hay una conexión activa."""
        return self.connected
    
    def get_device_info(self) -> Optional[Dict[str, str]]:
        """Retorna información del dispositivo conectado o None."""
        if self.connected:
            return {
                'address': self.device_address,
                'name': self.device_name
            }
        return None
