"""
Módulo BLE para Báscula Renpho ES-26BB-B
Autor: Sistema MedinaBluetooth
Versión: 1.0.0 EXPERIMENTAL

ADVERTENCIA IMPORTANTE:
════════════════════════════════════════════════════════════════
Este módulo es EXPERIMENTAL. Renpho ES-26BB-B usa un protocolo
propietario que puede estar encriptado o requerir autenticación.

NO hay garantía de que funcione completamente sin acceso a la
documentación oficial del protocolo de Renpho.
════════════════════════════════════════════════════════════════

Especificaciones Renpho ES-26BB-B:
- Frecuencia: 2402-2480 MHz (Bluetooth estándar)
- Potencia RF: 0.82 dBm
- Versión: Bluetooth 4.0+ (BLE/Low Energy)
"""

import asyncio
import logging
import struct
from datetime import datetime
from typing import Optional, Callable, Dict, List
import threading

logger = logging.getLogger(__name__)

# Verificar disponibilidad de bleak
try:
    from bleak import BleakScanner, BleakClient
    from bleak.backends.characteristic import BleakGATTCharacteristic
    BLEAK_AVAILABLE = True
    logger.info("bleak disponible - BLE soportado")
except ImportError:
    BLEAK_AVAILABLE = False
    logger.error("bleak NO disponible - instalar con: pip install bleak")


# ═══════════════════════════════════════════════════════════════
# UUIDs COMUNES PARA BÁSCULAS BLE
# ═══════════════════════════════════════════════════════════════

# UUIDs estándar de Bluetooth SIG para básculas
UUID_WEIGHT_MEASUREMENT = "00002a9d-0000-1000-8000-00805f9b34fb"
UUID_BODY_COMPOSITION = "00002a9c-0000-1000-8000-00805f9b34fb"
UUID_WEIGHT_SCALE_FEATURE = "00002a9e-0000-1000-8000-00805f9b34fb"

# UUIDs de servicios estándar
UUID_DEVICE_INFORMATION = "0000180a-0000-1000-8000-00805f9b34fb"
UUID_BATTERY_SERVICE = "0000180f-0000-1000-8000-00805f9b34fb"
UUID_GENERIC_ACCESS = "00001800-0000-1000-8000-00805f9b34fb"

# Cliente Characteristic Configuration Descriptor (para habilitar notificaciones)
UUID_CCCD = "00002902-0000-1000-8000-00805f9b34fb"


class RenphoBLEManager:
    """
    Gestor de comunicación BLE para báscula Renpho ES-26BB-B.
    
    Esta clase maneja todo el ciclo de vida de la conexión BLE:
    1. Escaneo de dispositivos
    2. Conexión al dispositivo
    3. Descubrimiento de servicios
    4. Suscripción a notificaciones
    5. Decodificación de datos
    6. Callbacks a la aplicación principal
    
    FUNCIONAMIENTO:
    ══════════════════════════════════════════════════════════════
    
    BLE usa un modelo de "Servicios" y "Características":
    
    Dispositivo BLE (Báscula)
    └── Servicio 1 (ej: Battery Service)
        ├── Característica 1.1 (Battery Level)
        └── Característica 1.2 (...)
    └── Servicio 2 (ej: Weight Service)
        ├── Característica 2.1 (Weight Measurement)
        └── Característica 2.2 (Body Composition)
    
    Para recibir datos:
    1. Encontrar la característica correcta
    2. Suscribirse a sus "notificaciones"
    3. Cuando la báscula envíe datos, se ejecuta un callback
    ══════════════════════════════════════════════════════════════
    """
    
    def __init__(self):
        """Inicializa el gestor BLE."""
        if not BLEAK_AVAILABLE:
            raise ImportError(
                "bleak no está instalado. Instalar con: pip install bleak"
            )
        
        # Cliente BLE
        self.client: Optional[BleakClient] = None
        self.device_address: Optional[str] = None
        self.device_name: Optional[str] = None
        
        # Estado de conexión
        self.connected = False
        self.running = False
        
        # Datos recibidos
        self.ultimo_peso: Optional[float] = None
        self.ultima_lectura: Optional[datetime] = None
        
        # Callbacks (funciones a llamar cuando ocurran eventos)
        self.data_callback: Optional[Callable] = None
        self.connection_callback: Optional[Callable] = None
        
        # Loop de eventos asyncio
        self.loop: Optional[asyncio.AbstractEventLoop] = None
        self.thread: Optional[threading.Thread] = None
        
        logger.info("RenphoBLEManager inicializado")
    
    # ═══════════════════════════════════════════════════════════
    # ESCANEO DE DISPOSITIVOS
    # ═══════════════════════════════════════════════════════════
    
    async def escanear_dispositivos(self, duracion: int = 10) -> List[Dict]:
        """
        Escanea dispositivos BLE cercanos buscando básculas Renpho.
        
        ¿CÓMO FUNCIONA EL ESCANEO BLE?
        ══════════════════════════════════════════════════════════
        1. El adaptador Bluetooth escanea señales BLE (advertisements)
        2. Cada dispositivo BLE transmite periódicamente:
           - Su nombre
           - Su dirección MAC
           - UUIDs de servicios que ofrece
           - Potencia de señal (RSSI)
        3. Filtramos solo dispositivos que parecen ser Renpho
        
        Args:
            duracion: Segundos a escanear (default: 10)
            
        Returns:
            Lista de diccionarios con info de dispositivos:
            [
                {
                    'name': 'RENPHO ES-26BB',
                    'address': 'XX:XX:XX:XX:XX:XX',
                    'rssi': -65
                }
            ]
        """
        logger.info(f"Escaneando dispositivos BLE ({duracion}s)...")
        
        try:
            # BleakScanner.discover() es ASÍNCRONO
            # Escanea durante X segundos y retorna lista de dispositivos
            devices = await BleakScanner.discover(timeout=duracion)
            
            # Filtrar solo dispositivos Renpho
            renpho_devices = []
            
            for device in devices:
                # device.name puede ser None si no transmite nombre
                nombre = device.name if device.name else "Desconocido"
                
                # Buscar palabras clave que identifiquen Renpho
                keywords = ['renpho', 'es-26', 'es26bb', 'scale']
                
                if any(kw in nombre.lower() for kw in keywords):
                    device_info = {
                        'name': nombre,
                        'address': device.address,
                        'rssi': device.rssi  # Potencia de señal (más cerca = más alto)
                    }
                    renpho_devices.append(device_info)
                    logger.info(f"Renpho encontrado: {nombre} ({device.address})")
            
            logger.info(f"Escaneo completo. {len(renpho_devices)} Renpho encontrado(s)")
            return renpho_devices
            
        except Exception as e:
            logger.error(f"Error durante escaneo BLE: {e}")
            return []
    
    # ═══════════════════════════════════════════════════════════
    # CONEXIÓN AL DISPOSITIVO
    # ═══════════════════════════════════════════════════════════
    
    async def conectar(self, device_address: str) -> bool:
        """
        Conecta a la báscula Renpho usando BLE.
        
        ¿CÓMO FUNCIONA LA CONEXIÓN BLE?
        ══════════════════════════════════════════════════════════
        1. BleakClient crea una conexión con la dirección MAC
        2. Se establece un enlace GATT (Generic Attribute Profile)
        3. El dispositivo comparte sus "servicios" disponibles
        4. Cada servicio contiene "características" que podemos leer/escribir
        
        DIFERENCIA CON BLUETOOTH CLASSIC:
        - Classic: Abre un "puerto" como si fuera serial
        - BLE: Accede a "características" organizadas en "servicios"
        
        Args:
            device_address: Dirección MAC (ej: "A4:C1:38:12:34:56")
            
        Returns:
            True si conectó exitosamente, False si falló
        """
        logger.info(f"Conectando a {device_address}...")
        
        try:
            # Crear cliente BLE
            # BleakClient maneja toda la comunicación de bajo nivel
            self.client = BleakClient(device_address)
            
            # Conectar (esto puede tardar varios segundos)
            # timeout: esperar máximo 15 segundos
            await self.client.connect(timeout=15.0)
            
            # Verificar conexión
            if self.client.is_connected:
                self.connected = True
                self.device_address = device_address
                
                logger.info(f"✓ Conectado a {device_address}")
                
                # Notificar a la aplicación principal
                if self.connection_callback:
                    self.connection_callback(True, {'address': device_address})
                
                return True
            else:
                logger.error("Conexión falló")
                return False
                
        except Exception as e:
            logger.error(f"Error al conectar: {e}")
            self.connected = False
            return False
    
    # ═══════════════════════════════════════════════════════════
    # DESCUBRIMIENTO DE SERVICIOS
    # ═══════════════════════════════════════════════════════════
    
    async def descubrir_servicios(self) -> Dict:
        """
        Descubre todos los servicios y características del dispositivo.
        
        ¿POR QUÉ ES IMPORTANTE?
        ══════════════════════════════════════════════════════════
        Renpho puede usar UUIDs propietarios (no estándar).
        Necesitamos ver TODOS los servicios para encontrar
        cuál contiene los datos de peso.
        
        ESTRUCTURA GATT:
        Servicio (UUID)
        └── Característica (UUID)
            ├── Propiedades: [READ, WRITE, NOTIFY]
            └── Descriptores
        
        Returns:
            Diccionario con todos los servicios y características
        """
        if not self.client or not self.client.is_connected:
            logger.error("No hay conexión activa")
            return {}
        
        logger.info("Descubriendo servicios GATT...")
        
        try:
            # Obtener todos los servicios
            # Esto es automático, BleakClient ya los descubre al conectar
            services = self.client.services
            
            servicios_info = {}
            
            for service in services:
                service_uuid = str(service.uuid)
                logger.info(f"\n📋 Servicio: {service_uuid}")
                logger.info(f"   Descripción: {service.description}")
                
                caracteristicas_info = []
                
                # Cada servicio tiene características
                for char in service.characteristics:
                    char_uuid = str(char.uuid)
                    props = char.properties  # ['read', 'write', 'notify', etc.]
                    
                    logger.info(f"\n   📝 Característica: {char_uuid}")
                    logger.info(f"      Propiedades: {props}")
                    
                    char_info = {
                        'uuid': char_uuid,
                        'properties': props,
                        'descriptors': []
                    }
                    
                    # Intentar leer si es posible
                    if "read" in props:
                        try:
                            # read_gatt_char() lee el valor actual
                            value = await self.client.read_gatt_char(char_uuid)
                            char_info['value'] = value.hex()
                            logger.info(f"      Valor: {value.hex()}")
                        except Exception as e:
                            logger.debug(f"      No se pudo leer: {e}")
                    
                    caracteristicas_info.append(char_info)
                
                servicios_info[service_uuid] = {
                    'descripcion': service.description,
                    'caracteristicas': caracteristicas_info
                }
            
            return servicios_info
            
        except Exception as e:
            logger.error(f"Error descubriendo servicios: {e}")
            return {}
    
    # ═══════════════════════════════════════════════════════════
    # SUSCRIPCIÓN A NOTIFICACIONES (RECIBIR DATOS)
    # ═══════════════════════════════════════════════════════════
    
    async def suscribir_peso(self) -> bool:
        """
        Se suscribe a notificaciones de peso de la báscula.
        
        ¿CÓMO FUNCIONAN LAS NOTIFICACIONES BLE?
        ══════════════════════════════════════════════════════════
        En BLE, los datos NO se envían continuamente como en serial.
        En su lugar:
        
        1. Cliente se "suscribe" a una característica
        2. Cuando el dispositivo tiene datos nuevos, envía una "notificación"
        3. Se ejecuta un callback con los datos
        
        Es como suscribirse a un canal de YouTube:
        - No descargas videos continuamente
        - Recibes notificación cuando hay nuevo contenido
        
        PROCESO:
        1. Encontrar característica de peso (por UUID)
        2. Llamar a start_notify() con un handler
        3. Cuando lleguen datos, se ejecuta el handler
        
        Returns:
            True si se suscribió exitosamente
        """
        if not self.client or not self.client.is_connected:
            logger.error("No hay conexión activa")
            return False
        
        logger.info("Suscribiéndose a notificaciones de peso...")
        
        # Lista de UUIDs a probar (del más probable al menos probable)
        uuids_a_probar = [
            UUID_WEIGHT_MEASUREMENT,      # UUID estándar de peso
            UUID_BODY_COMPOSITION,         # UUID de composición corporal
            # Renpho puede usar UUIDs propietarios no listados aquí
        ]
        
        # Intentar cada UUID
        for uuid in uuids_a_probar:
            try:
                logger.info(f"Probando UUID: {uuid}")
                
                # start_notify() inicia las notificaciones
                # Parámetros:
                #   uuid: característica a suscribir
                #   callback: función a llamar cuando lleguen datos
                await self.client.start_notify(uuid, self._notification_handler)
                
                logger.info(f"✓ Suscrito a {uuid}")
                return True
                
            except Exception as e:
                logger.debug(f"UUID {uuid} no disponible: {e}")
        
        logger.warning("No se pudo suscribir a ningún UUID conocido")
        logger.info("Renpho puede usar UUIDs propietarios")
        
        # Intentar suscribirse a TODAS las características con NOTIFY
        return await self._suscribir_todas_notificaciones()
    
    async def _suscribir_todas_notificaciones(self) -> bool:
        """
        Intenta suscribirse a TODAS las características que soporten notificaciones.
        
        ¿POR QUÉ ESTO?
        ══════════════════════════════════════════════════════════
        Si Renpho usa UUIDs propietarios (no estándar), no sabremos
        cuál es el correcto. Entonces nos suscribimos a TODO y vemos
        qué datos llegan.
        
        ESTRATEGIA:
        1. Recorrer todos los servicios
        2. Recorrer todas las características
        3. Si tiene propiedad 'notify', suscribirse
        4. Ver qué datos llegan
        """
        logger.info("Intentando suscripción a todas las notificaciones...")
        
        try:
            services = self.client.services
            suscripciones_exitosas = 0
            
            for service in services:
                for char in service.characteristics:
                    # Verificar si soporta notificaciones
                    if "notify" in char.properties:
                        try:
                            await self.client.start_notify(
                                char.uuid,
                                self._notification_handler
                            )
                            logger.info(f"✓ Suscrito a {char.uuid}")
                            suscripciones_exitosas += 1
                        except Exception as e:
                            logger.debug(f"No se pudo suscribir a {char.uuid}: {e}")
            
            if suscripciones_exitosas > 0:
                logger.info(f"Suscrito a {suscripciones_exitosas} características")
                return True
            else:
                logger.error("No se pudo suscribir a ninguna característica")
                return False
                
        except Exception as e:
            logger.error(f"Error en suscripción masiva: {e}")
            return False
    
    # ═══════════════════════════════════════════════════════════
    # HANDLER DE NOTIFICACIONES (CUANDO LLEGAN DATOS)
    # ═══════════════════════════════════════════════════════════
    
    def _notification_handler(
        self,
        sender: BleakGATTCharacteristic,
        data: bytearray
    ):
        """
        Handler ejecutado cuando llega una notificación del dispositivo.
        
        ¿QUÉ RECIBIMOS?
        ══════════════════════════════════════════════════════════
        sender: La característica que envió la notificación
        data: Bytes crudos enviados por la báscula
        
        PROBLEMA:
        Los datos vienen en formato binario y NO sabemos el formato
        exacto que usa Renpho. Tenemos que:
        
        1. Ver los bytes en hexadecimal
        2. Intentar decodificar como diferentes formatos
        3. Buscar patrones que parezcan peso
        
        FORMATOS COMUNES PARA PESO EN BLE:
        - IEEE 11073 (estándar médico)
        - Peso en kg * 200 (entero de 16 bits)
        - Peso en kg * 100 (entero de 16 bits)
        - Flotante de 32 bits
        
        Args:
            sender: Característica BLE que envió datos
            data: Datos crudos (bytes)
        """
        logger.info(f"\n📨 Notificación recibida de {sender.uuid}")
        logger.info(f"   Datos HEX: {data.hex()}")
        logger.info(f"   Datos DEC: {list(data)}")
        logger.info(f"   Longitud: {len(data)} bytes")
        
        # Intentar diferentes decodificaciones
        peso_detectado = self._decodificar_peso(data)
        
        if peso_detectado:
            self.ultimo_peso = peso_detectado
            self.ultima_lectura = datetime.now()
            
            logger.info(f"   ⚖️  PESO DETECTADO: {peso_detectado:.1f} kg")
            
            # Llamar callback de la aplicación principal
            if self.data_callback:
                # Formatear datos para que sean compatibles
                # con la aplicación principal
                datos_formateados = self._formatear_para_app(peso_detectado)
                self.data_callback(datos_formateados)
        else:
            logger.warning("   No se pudo decodificar como peso")
    
    # ═══════════════════════════════════════════════════════════
    # DECODIFICACIÓN DE DATOS
    # ═══════════════════════════════════════════════════════════
    
    def _decodificar_peso(self, data: bytearray) -> Optional[float]:
        """
        Intenta decodificar los bytes crudos como peso en kilogramos.
        
        ¿CÓMO FUNCIONA?
        ══════════════════════════════════════════════════════════
        Probamos múltiples formatos comunes:
        
        1. IEEE 11073 (estándar médico)
           - Formato complejo con flags
           - Usado por básculas médicas certificadas
        
        2. Entero de 16 bits (peso * 200)
           - Ejemplo: 15060 = 75.3 kg
           - Común en básculas chinas
        
        3. Entero de 16 bits (peso * 100)
           - Ejemplo: 7530 = 75.3 kg
        
        4. Flotante de 32 bits
           - Peso directamente como float
        
        Args:
            data: Bytes crudos de la notificación
            
        Returns:
            Peso en kg o None si no se pudo decodificar
        """
        if len(data) < 2:
            return None
        
        # INTENTO 1: Formato IEEE 11073 (estándar para básculas médicas)
        try:
            # Primer byte = flags
            flags = data[0]
            
            # Segundo y tercer byte = peso
            if len(data) >= 3:
                # Little-endian: byte menos significativo primero
                peso_raw = struct.unpack('<H', data[1:3])[0]
                
                # Típicamente multiplicado por 200
                peso_kg = peso_raw / 200.0
                
                # Validar que sea un peso razonable (5-300 kg)
                if 5.0 <= peso_kg <= 300.0:
                    logger.debug(f"Decodificado (IEEE 11073): {peso_kg:.1f} kg")
                    return peso_kg
        except Exception as e:
            logger.debug(f"Formato IEEE 11073 falló: {e}")
        
        # INTENTO 2: Entero de 16 bits (peso * 200)
        try:
            peso_raw = struct.unpack('<H', data[0:2])[0]
            peso_kg = peso_raw / 200.0
            
            if 5.0 <= peso_kg <= 300.0:
                logger.debug(f"Decodificado (int16/200): {peso_kg:.1f} kg")
                return peso_kg
        except Exception as e:
            logger.debug(f"Formato int16/200 falló: {e}")
        
        # INTENTO 3: Entero de 16 bits (peso * 100)
        try:
            peso_raw = struct.unpack('<H', data[0:2])[0]
            peso_kg = peso_raw / 100.0
            
            if 5.0 <= peso_kg <= 300.0:
                logger.debug(f"Decodificado (int16/100): {peso_kg:.1f} kg")
                return peso_kg
        except Exception as e:
            logger.debug(f"Formato int16/100 falló: {e}")
        
        # INTENTO 4: Flotante de 32 bits
        try:
            if len(data) >= 4:
                peso_kg = struct.unpack('<f', data[0:4])[0]
                
                if 5.0 <= peso_kg <= 300.0:
                    logger.debug(f"Decodificado (float32): {peso_kg:.1f} kg")
                    return peso_kg
        except Exception as e:
            logger.debug(f"Formato float32 falló: {e}")
        
        # Si nada funcionó, retornar None
        logger.warning("No se pudo decodificar peso con formatos conocidos")
        return None
    
    def _formatear_para_app(self, peso: float) -> bytes:
        """
        Formatea los datos de peso para que sean compatibles
        con la aplicación principal (que espera bytes).
        
        La app principal (DataHandler) espera recibir bytes
        que pueda decodificar como texto. Convertimos el peso
        a un formato similar al que enviaría una báscula SPP.
        
        Args:
            peso: Peso en kilogramos
            
        Returns:
            Bytes formateados como "PESO: XX.X kg\n"
        """
        timestamp = self.ultima_lectura.strftime("%H:%M:%S")
        mensaje = f"[{timestamp}] PESO: {peso:.1f} kg\n"
        return mensaje.encode('utf-8')
    
    # ═══════════════════════════════════════════════════════════
    # DESCONEXIÓN
    # ═══════════════════════════════════════════════════════════
    
    async def desconectar(self):
        """
        Desconecta del dispositivo BLE.
        
        IMPORTANTE:
        Siempre desconectar correctamente para liberar recursos
        y evitar que el dispositivo quede "ocupado".
        """
        if self.client and self.client.is_connected:
            try:
                logger.info("Desconectando...")
                await self.client.disconnect()
                self.connected = False
                
                logger.info("✓ Desconectado")
                
                if self.connection_callback:
                    self.connection_callback(False, None)
                    
            except Exception as e:
                logger.error(f"Error al desconectar: {e}")
    
    # ═══════════════════════════════════════════════════════════
    # CALLBACKS
    # ═══════════════════════════════════════════════════════════
    
    def set_data_callback(self, callback: Callable):
        """
        Establece función a llamar cuando se reciban datos.
        
        Args:
            callback: Función que recibe datos (bytes)
        """
        self.data_callback = callback
    
    def set_connection_callback(self, callback: Callable):
        """
        Establece función a llamar cuando cambie estado de conexión.
        
        Args:
            callback: Función que recibe (conectado: bool, info: dict)
        """
        self.connection_callback = callback
    
    # ═══════════════════════════════════════════════════════════
    # MÉTODOS PARA INTEGRACIÓN CON APLICACIÓN PRINCIPAL
    # ═══════════════════════════════════════════════════════════
    
    def scan_devices_sync(self, duration: int = 10) -> List[Dict]:
        """
        Versión síncrona de escaneo para compatibilidad con app principal.
        
        La aplicación principal usa threading, no asyncio.
        Este método crea un loop temporal para ejecutar el escaneo async.
        """
        return asyncio.run(self.escanear_dispositivos(duration))
    
    def connect_sync(self, address: str) -> bool:
        """Versión síncrona de conexión."""
        return asyncio.run(self.conectar(address))
    
    def subscribe_sync(self) -> bool:
        """Versión síncrona de suscripción."""
        return asyncio.run(self.suscribir_peso())
    
    def disconnect_sync(self):
        """Versión síncrona de desconexión."""
        asyncio.run(self.desconectar())


# ═══════════════════════════════════════════════════════════════
# EJEMPLO DE USO
# ═══════════════════════════════════════════════════════════════

async def ejemplo_completo():
    """
    Ejemplo completo de cómo usar RenphoBLEManager.
    
    FLUJO:
    1. Crear manager
    2. Escanear dispositivos
    3. Conectar al primero encontrado
    4. Descubrir servicios (debugging)
    5. Suscribirse a notificaciones
    6. Esperar 30 segundos (mientras pisas la báscula)
    7. Desconectar
    """
    print("=" * 60)
    print("RENPHO ES-26BB-B - CONEXIÓN BLE")
    print("=" * 60)
    
    # Crear manager
    manager = RenphoBLEManager()
    
    # Callback para datos
    def on_data(data):
        print(f"\n✓ DATOS RECIBIDOS: {data.decode('utf-8', errors='ignore')}")
    
    manager.set_data_callback(on_data)
    
    # PASO 1: Escanear
    print("\n🔍 Escaneando...")
    devices = await manager.escanear_dispositivos(10)
    
    if not devices:
        print("❌ No se encontró báscula Renpho")
        return
    
    print(f"\n✓ Encontrado: {devices[0]['name']}")
    
    # PASO 2: Conectar
    print(f"\n📡 Conectando a {devices[0]['address']}...")
    conectado = await manager.conectar(devices[0]['address'])
    
    if not conectado:
        print("❌ No se pudo conectar")
        return
    
    print("✓ Conectado")
    
    # PASO 3: Descubrir servicios (opcional, para debugging)
    print("\n📋 Descubriendo servicios...")
    await manager.descubrir_servicios()
    
    # PASO 4: Suscribirse
    print("\n📊 Suscribiendo a notificaciones...")
    suscrito = await manager.suscribir_peso()
    
    if suscrito:
        print("✓ Suscrito")
        print("\n⚖️  PISA LA BÁSCULA AHORA")
        print("   Esperando 30 segundos...\n")
        
        # Esperar datos
        await asyncio.sleep(30)
    else:
        print("❌ No se pudo suscribir")
    
    # PASO 5: Desconectar
    print("\n🔌 Desconectando...")
    await manager.desconectar()
    
    print("\n✓ Ejemplo finalizado")


if __name__ == "__main__":
    # Ejecutar ejemplo
    asyncio.run(ejemplo_completo())
