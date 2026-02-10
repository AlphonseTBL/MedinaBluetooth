"""
Módulo para gestionar la comunicación Bluetooth
"""

import bluetooth
import logging
import threading
import time

logger = logging.getLogger(__name__)


class BluetoothManager:
    """
    Gestiona el escaneo, conexión y comunicación con dispositivos Bluetooth.
    
    Esta clase maneja todo lo relacionado con Bluetooth usando PyBluez.
    """
    
    def __init__(self):
        """Inicializa el gestor de Bluetooth."""
        self.socket = None
        self.connected = False
        self.current_device = None
        self.receive_thread = None
        self.running = False
        
        # Callbacks
        self.data_callback = None
        self.connection_callback = None
        self.scan_callback = None
        
        logger.info("BluetoothManager inicializado")
    
    def scan_devices(self, duration=8):
        """
        Escanea dispositivos Bluetooth cercanos.
        
        Args:
            duration: Duración del escaneo en segundos
            
        Returns:
            list: Lista de tuplas (nombre, dirección) de dispositivos encontrados
        """
        logger.info(f"Iniciando escaneo de dispositivos (duración: {duration}s)")
        
        try:
            # Escanear dispositivos cercanos
            nearby_devices = bluetooth.discover_devices(
                duration=duration,
                lookup_names=True,
                flush_cache=True,
                lookup_class=False
            )
            
            logger.info(f"Escaneo completado. Dispositivos encontrados: {len(nearby_devices)}")
            
            # Formatear resultados
            devices = []
            for addr, name in nearby_devices:
                devices.append({
                    'name': name if name else "Dispositivo desconocido",
                    'address': addr
                })
                logger.debug(f"Dispositivo encontrado: {name} - {addr}")
            
            return devices
            
        except Exception as e:
            logger.error(f"Error durante el escaneo: {e}")
            return []
    
    def get_device_services(self, device_address):
        """
        Obtiene los servicios disponibles de un dispositivo.
        
        Args:
            device_address: Dirección MAC del dispositivo
            
        Returns:
            list: Lista de servicios disponibles
        """
        try:
            services = bluetooth.find_service(address=device_address)
            logger.info(f"Servicios encontrados para {device_address}: {len(services)}")
            return services
        except Exception as e:
            logger.error(f"Error obteniendo servicios: {e}")
            return []
    
    def diagnosticar_dispositivo(self, device_address, device_name="Dispositivo"):
        """
        Diagnostica un dispositivo y retorna información detallada.
        
        Args:
            device_address: Dirección MAC del dispositivo
            device_name: Nombre del dispositivo (opcional)
            
        Returns:
            dict: Información de diagnóstico con los siguientes campos:
                - compatible: bool - Si es compatible con RFCOMM
                - servicios: list - Lista de servicios encontrados
                - puerto_sugerido: int o None - Puerto RFCOMM si está disponible
                - mensaje: str - Mensaje descriptivo del resultado
                - detalles: str - Detalles técnicos del diagnóstico
        """
        logger.info(f"Iniciando diagnóstico de {device_name} ({device_address})")
        
        resultado = {
            'compatible': False,
            'servicios': [],
            'puerto_sugerido': None,
            'mensaje': '',
            'detalles': ''
        }
        
        # PASO 1: Buscar servicios
        try:
            servicios = bluetooth.find_service(address=device_address)
            
            if not servicios:
                resultado['mensaje'] = "❌ NO COMPATIBLE"
                resultado['detalles'] = (
                    f"No se encontraron servicios en {device_name}.\n\n"
                    f"Posibles causas:\n"
                    f"• El dispositivo no está emparejado\n"
                    f"• El dispositivo está fuera de alcance\n"
                    f"• El dispositivo no ofrece servicios públicos\n\n"
                    f"Intenta emparejar el dispositivo desde la configuración "
                    f"de Bluetooth de tu sistema operativo."
                )
                logger.warning(f"No se encontraron servicios para {device_address}")
                return resultado
            
            # PASO 2: Analizar servicios
            servicios_formateados = []
            puertos_rfcomm = []
            
            for servicio in servicios:
                info_servicio = {
                    'nombre': servicio.get('name', 'Sin nombre'),
                    'protocolo': servicio.get('protocol', 'Desconocido'),
                    'puerto': servicio.get('port', None),
                    'host': servicio.get('host', ''),
                }
                servicios_formateados.append(info_servicio)
                
                # Verificar si tiene puerto RFCOMM
                if info_servicio['puerto'] is not None:
                    puertos_rfcomm.append(info_servicio['puerto'])
                    logger.info(f"Puerto RFCOMM encontrado: {info_servicio['puerto']} "
                              f"({info_servicio['nombre']})")
            
            resultado['servicios'] = servicios_formateados
            
            # PASO 3: Determinar compatibilidad
            if puertos_rfcomm:
                # COMPATIBLE
                resultado['compatible'] = True
                resultado['puerto_sugerido'] = puertos_rfcomm[0]
                resultado['mensaje'] = "✅ COMPATIBLE"
                resultado['detalles'] = (
                    f"¡Buenas noticias! {device_name} es compatible.\n\n"
                    f"Servicios RFCOMM encontrados: {len(puertos_rfcomm)}\n"
                )
                
                for i, servicio in enumerate(servicios_formateados, 1):
                    if servicio['puerto']:
                        resultado['detalles'] += (
                            f"\n{i}. {servicio['nombre']}\n"
                            f"   Puerto: {servicio['puerto']}\n"
                            f"   Protocolo: {servicio['protocolo']}\n"
                        )
                
                resultado['detalles'] += (
                    f"\n💡 Recomendación:\n"
                    f"Conectar usando puerto {resultado['puerto_sugerido']}"
                )
                
                logger.info(f"Dispositivo COMPATIBLE - Puerto sugerido: {resultado['puerto_sugerido']}")
                
            else:
                # NO COMPATIBLE
                resultado['compatible'] = False
                resultado['mensaje'] = "❌ NO COMPATIBLE"
                resultado['detalles'] = (
                    f"{device_name} NO es compatible con esta aplicación.\n\n"
                    f"Este dispositivo no tiene servicios RFCOMM (Serial Port Profile).\n\n"
                    f"Servicios encontrados:\n"
                )
                
                for i, servicio in enumerate(servicios_formateados, 1):
                    resultado['detalles'] += (
                        f"{i}. {servicio['nombre']} ({servicio['protocolo']})\n"
                    )
                
                resultado['detalles'] += (
                    f"\n💡 Este tipo de dispositivo es para:\n"
                )
                
                # Identificar tipo de dispositivo por servicios
                nombres_servicios = ' '.join([s['nombre'].lower() for s in servicios_formateados])
                
                if 'audio' in nombres_servicios or 'a2dp' in nombres_servicios:
                    resultado['detalles'] += "• Streaming de audio (música, llamadas)\n"
                if 'hid' in nombres_servicios:
                    resultado['detalles'] += "• Control de entrada (teclado, ratón)\n"
                if 'hands' in nombres_servicios or 'headset' in nombres_servicios:
                    resultado['detalles'] += "• Llamadas telefónicas\n"
                
                resultado['detalles'] += (
                    f"\n✅ Dispositivos compatibles con esta app:\n"
                    f"• Arduino + HC-05/HC-06\n"
                    f"• ESP32 con Bluetooth Serial\n"
                    f"• Módulos Bluetooth SPP\n"
                    f"• Dispositivos OBD-II\n"
                )
                
                logger.warning(f"Dispositivo NO COMPATIBLE - No hay servicios RFCOMM")
            
            return resultado
            
        except Exception as e:
            resultado['mensaje'] = "❌ ERROR"
            resultado['detalles'] = (
                f"Error al diagnosticar {device_name}:\n\n"
                f"{str(e)}\n\n"
                f"Verifica que:\n"
                f"• El Bluetooth esté habilitado\n"
                f"• El dispositivo esté cerca\n"
                f"• Tengas permisos de Bluetooth"
            )
            logger.error(f"Error en diagnóstico: {e}")
            return resultado
    
    def connect(self, device_address, port=1):
        """
        Conecta a un dispositivo Bluetooth específico.
        
        Args:
            device_address: Dirección MAC del dispositivo
            port: Puerto RFCOMM (por defecto 1)
            
        Returns:
            bool: True si la conexión fue exitosa, False en caso contrario
        """
        try:
            logger.info(f"Intentando conectar a {device_address} en puerto {port}")
            
            # Crear socket RFCOMM
            self.socket = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
            
            # Intentar conectar
            self.socket.connect((device_address, port))
            
            self.connected = True
            self.current_device = {
                'address': device_address,
                'port': port
            }
            
            # Iniciar hilo de recepción de datos
            self._start_receive_thread()
            
            logger.info(f"Conectado exitosamente a {device_address}")
            
            # Notificar cambio de conexión
            if self.connection_callback:
                self.connection_callback(True, self.current_device)
            
            return True
            
        except bluetooth.BluetoothError as e:
            logger.error(f"Error de Bluetooth al conectar: {e}")
            self.connected = False
            return False
        except Exception as e:
            logger.error(f"Error inesperado al conectar: {e}")
            self.connected = False
            return False
    
    def disconnect(self):
        """Desconecta del dispositivo actual."""
        if self.connected and self.socket:
            try:
                logger.info("Desconectando dispositivo Bluetooth")
                
                # Detener hilo de recepción
                self.running = False
                if self.receive_thread and self.receive_thread.is_alive():
                    self.receive_thread.join(timeout=2)
                
                # Cerrar socket
                self.socket.close()
                self.socket = None
                self.connected = False
                
                logger.info("Desconectado exitosamente")
                
                # Notificar cambio de conexión
                if self.connection_callback:
                    self.connection_callback(False, None)
                
            except Exception as e:
                logger.error(f"Error al desconectar: {e}")
    
    def send_data(self, data):
        """
        Envía datos al dispositivo conectado.
        
        Args:
            data: Datos a enviar (string o bytes)
            
        Returns:
            bool: True si el envío fue exitoso
        """
        if not self.connected or not self.socket:
            logger.warning("Intento de envío sin conexión activa")
            return False
        
        try:
            if isinstance(data, str):
                data = data.encode('utf-8')
            
            self.socket.send(data)
            logger.debug(f"Datos enviados: {data}")
            return True
            
        except Exception as e:
            logger.error(f"Error al enviar datos: {e}")
            return False
    
    def _start_receive_thread(self):
        """Inicia el hilo para recibir datos continuamente."""
        self.running = True
        self.receive_thread = threading.Thread(target=self._receive_loop, daemon=True)
        self.receive_thread.start()
        logger.info("Hilo de recepción iniciado")
    
    def _receive_loop(self):
        """
        Loop que recibe datos continuamente del dispositivo.
        
        Este método se ejecuta en un hilo separado.
        """
        logger.info("Loop de recepción iniciado")
        
        while self.running and self.connected:
            try:
                # Recibir datos (máximo 1024 bytes)
                data = self.socket.recv(1024)
                
                if data:
                    logger.debug(f"Datos recibidos: {data}")
                    
                    # Llamar al callback con los datos recibidos
                    if self.data_callback:
                        self.data_callback(data)
                else:
                    # Si no hay datos, puede que la conexión se haya cerrado
                    logger.warning("No se recibieron datos, posible desconexión")
                    time.sleep(0.1)
                    
            except bluetooth.BluetoothError as e:
                if self.running:  # Solo loguear si no estamos cerrando intencionalmente
                    logger.error(f"Error de Bluetooth en recepción: {e}")
                    self.disconnect()
                break
            except Exception as e:
                if self.running:
                    logger.error(f"Error en loop de recepción: {e}")
                break
        
        logger.info("Loop de recepción finalizado")
    
    def set_data_callback(self, callback):
        """
        Establece el callback para cuando se reciban datos.
        
        Args:
            callback: Función a llamar cuando lleguen datos
        """
        self.data_callback = callback
    
    def set_connection_callback(self, callback):
        """
        Establece el callback para cambios de conexión.
        
        Args:
            callback: Función a llamar cuando cambie el estado de conexión
        """
        self.connection_callback = callback
    
    def set_scan_callback(self, callback):
        """
        Establece el callback para el escaneo de dispositivos.
        
        Args:
            callback: Función a llamar durante el escaneo
        """
        self.scan_callback = callback
    
    def is_connected(self):
        """
        Verifica si hay una conexión activa.
        
        Returns:
            bool: True si está conectado
        """
        return self.connected
