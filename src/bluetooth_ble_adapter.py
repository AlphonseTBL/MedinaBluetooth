"""
Adaptador para integrar RenphoBLEManager con la aplicación principal.

Este módulo actúa como "puente" entre:
- El gestor BLE (asíncrono, asyncio)
- La aplicación principal (síncrona, threading)

PROBLEMA A RESOLVER:
════════════════════════════════════════════════════════════════
La app principal usa threading (síncrono)
BLE (bleak) usa asyncio (asíncrono)

Son dos modelos de concurrencia DIFERENTES e INCOMPATIBLES.

SOLUCIÓN:
Crear un thread que ejecute un loop de asyncio internamente.
════════════════════════════════════════════════════════════════
"""

import threading
import asyncio
import logging
from typing import Optional, Callable, List, Dict
import time

logger = logging.getLogger(__name__)

try:
    from src.renpho_ble_manager import RenphoBLEManager, BLEAK_AVAILABLE
except ImportError:
    # Si falla el import relativo, intentar absoluto
    try:
        from renpho_ble_manager import RenphoBLEManager, BLEAK_AVAILABLE
    except ImportError:
        BLEAK_AVAILABLE = False
        logger.error("No se pudo importar RenphoBLEManager")


class BluetoothBLEAdapter:
    """
    Adaptador que hace que RenphoBLEManager se comporte como BluetoothManager.
    
    ARQUITECTURA:
    ═══════════════════════════════════════════════════════════
    
    App Principal (threading)
         ↓
    BluetoothBLEAdapter
         ↓
    [Thread separado ejecutando asyncio loop]
         ↓
    RenphoBLEManager (asyncio)
         ↓
    Báscula Renpho BLE
    
    ═══════════════════════════════════════════════════════════
    
    MÉTODOS COMPATIBLES CON BluetoothManager:
    - scan_devices(duration)
    - connect(address, port)
    - disconnect()
    - set_data_callback(callback)
    - set_connection_callback(callback)
    - is_connected()
    """
    
    def __init__(self):
        """Inicializa el adaptador BLE."""
        if not BLEAK_AVAILABLE:
            raise ImportError(
                "bleak no disponible. Instalar con: pip install bleak"
            )
        
        # Manager BLE
        self.ble_manager = RenphoBLEManager()
        
        # Thread y loop asyncio
        self.loop: Optional[asyncio.AbstractEventLoop] = None
        self.thread: Optional[threading.Thread] = None
        self.running = False
        
        # Callbacks
        self.data_callback: Optional[Callable] = None
        self.connection_callback: Optional[Callable] = None
        
        # Iniciar thread con loop asyncio
        self._start_async_loop()
        
        logger.info("BluetoothBLEAdapter inicializado")
    
    def _start_async_loop(self):
        """
        Inicia un thread que ejecuta un loop de asyncio.
        
        ¿POR QUÉ NECESITAMOS ESTO?
        ══════════════════════════════════════════════════════════
        asyncio requiere un "event loop" corriendo continuamente.
        La aplicación principal usa threading, no asyncio.
        
        Solución: Crear un thread dedicado que solo ejecute
        el loop de asyncio.
        
        FUNCIONAMIENTO:
        1. Thread inicia
        2. Crea nuevo loop asyncio
        3. Loop corre indefinidamente
        4. Enviamos tareas al loop desde otros threads
        """
        def run_async_loop():
            """Función que se ejecuta en el thread separado."""
            # Crear nuevo loop para este thread
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
            
            logger.info("Loop asyncio iniciado en thread separado")
            
            # Correr loop indefinidamente
            self.running = True
            try:
                self.loop.run_forever()
            finally:
                self.loop.close()
                logger.info("Loop asyncio cerrado")
        
        # Crear e iniciar thread
        self.thread = threading.Thread(target=run_async_loop, daemon=True)
        self.thread.start()
        
        # Esperar a que el loop esté listo
        while self.loop is None:
            time.sleep(0.01)
        
        logger.info("Thread asyncio listo")
    
    def _run_coroutine(self, coro):
        """
        Ejecuta una coroutina en el loop asyncio desde otro thread.
        
        ¿CÓMO FUNCIONA?
        ══════════════════════════════════════════════════════════
        asyncio.run_coroutine_threadsafe() permite ejecutar
        una coroutina desde un thread diferente al del loop.
        
        Es como "enviar una tarea" al loop y esperar el resultado.
        
        Args:
            coro: Coroutina a ejecutar (función async)
            
        Returns:
            Resultado de la coroutina
        """
        if not self.loop:
            raise RuntimeError("Loop asyncio no disponible")
        
        # Enviar coroutina al loop y obtener Future
        future = asyncio.run_coroutine_threadsafe(coro, self.loop)
        
        # Esperar resultado (blocking)
        return future.result()
    
    # ═══════════════════════════════════════════════════════════
    # MÉTODOS COMPATIBLES CON BluetoothManager
    # ═══════════════════════════════════════════════════════════
    
    def scan_devices(self, duration=8) -> List[Dict]:
        """
        Escanea dispositivos BLE (compatible con BluetoothManager).
        
        Esta versión es SÍNCRONA aunque internamente usa asyncio.
        
        Args:
            duration: Duración del escaneo en segundos
            
        Returns:
            Lista de dispositivos en formato compatible:
            [
                {
                    'name': 'RENPHO',
                    'address': 'XX:XX:XX:XX:XX:XX'
                }
            ]
        """
        logger.info(f"Escaneando dispositivos BLE ({duration}s)...")
        
        try:
            # Ejecutar escaneo asyncio de forma síncrona
            devices = self._run_coroutine(
                self.ble_manager.escanear_dispositivos(duration)
            )
            
            # Formatear para compatibilidad
            formatted_devices = []
            for dev in devices:
                formatted_devices.append({
                    'name': dev['name'],
                    'address': dev['address']
                })
            
            logger.info(f"Escaneo completo: {len(formatted_devices)} dispositivo(s)")
            return formatted_devices
            
        except Exception as e:
            logger.error(f"Error en escaneo BLE: {e}")
            return []
    
    def connect(self, device_address, port=None) -> Dict:
        """
        Conecta a dispositivo BLE (compatible con BluetoothManager).
        
        NOTA: El parámetro 'port' se ignora en BLE
        (BLE no usa puertos como Bluetooth Classic)
        
        Args:
            device_address: Dirección MAC del dispositivo
            port: Ignorado (compatibilidad con BluetoothManager)
            
        Returns:
            Dict con resultado:
            {
                'success': bool,
                'message': str,
                'port': None
            }
        """
        logger.info(f"Conectando a {device_address} vía BLE...")
        
        try:
            # Configurar callbacks ANTES de conectar
            self.ble_manager.set_data_callback(self._on_ble_data)
            self.ble_manager.set_connection_callback(self._on_ble_connection)
            
            # Conectar
            success = self._run_coroutine(
                self.ble_manager.conectar(device_address)
            )
            
            if not success:
                return {
                    'success': False,
                    'message': 'No se pudo establecer conexión BLE',
                    'port': None
                }
            
            # Descubrir servicios (debugging)
            logger.info("Descubriendo servicios GATT...")
            self._run_coroutine(self.ble_manager.descubrir_servicios())
            
            # Suscribirse a notificaciones
            logger.info("Suscribiendo a notificaciones...")
            subscribed = self._run_coroutine(
                self.ble_manager.suscribir_peso()
            )
            
            if not subscribed:
                return {
                    'success': False,
                    'message': (
                        'Conectado pero no se pudo suscribir a notificaciones.\n'
                        'Renpho puede usar protocolo propietario.\n'
                        'Verifica logs para más información.'
                    ),
                    'port': None
                }
            
            return {
                'success': True,
                'message': 'Conectado y suscrito a notificaciones BLE',
                'port': None
            }
            
        except Exception as e:
            logger.error(f"Error conectando BLE: {e}")
            return {
                'success': False,
                'message': f'Error BLE: {str(e)}',
                'port': None
            }
    
    def disconnect(self):
        """Desconecta del dispositivo BLE."""
        logger.info("Desconectando BLE...")
        
        try:
            self._run_coroutine(self.ble_manager.desconectar())
            logger.info("Desconectado exitosamente")
        except Exception as e:
            logger.error(f"Error desconectando: {e}")
    
    def is_connected(self) -> bool:
        """Verifica si hay conexión activa."""
        return self.ble_manager.connected
    
    def set_data_callback(self, callback: Callable):
        """
        Establece callback para datos recibidos.
        
        Args:
            callback: Función que recibe bytes
        """
        self.data_callback = callback
    
    def set_connection_callback(self, callback: Callable):
        """
        Establece callback para cambios de conexión.
        
        Args:
            callback: Función que recibe (connected: bool, info: dict)
        """
        self.connection_callback = callback
    
    # ═══════════════════════════════════════════════════════════
    # CALLBACKS INTERNOS (BLE → App)
    # ═══════════════════════════════════════════════════════════
    
    def _on_ble_data(self, data: bytes):
        """
        Callback interno: BLE Manager → Aplicación Principal.
        
        Cuando RenphoBLEManager recibe datos, llama a este método.
        Este método a su vez llama al callback de la aplicación.
        
        Args:
            data: Datos formateados como bytes
        """
        if self.data_callback:
            self.data_callback(data)
    
    def _on_ble_connection(self, connected: bool, info: dict):
        """
        Callback interno: cambio de conexión.
        
        Args:
            connected: Estado de conexión
            info: Información del dispositivo
        """
        if self.connection_callback:
            self.connection_callback(connected, info)
    
    # ═══════════════════════════════════════════════════════════
    # LIMPIEZA
    # ═══════════════════════════════════════════════════════════
    
    def cleanup(self):
        """Limpia recursos al cerrar."""
        logger.info("Limpiando recursos BLE...")
        
        # Desconectar si está conectado
        if self.is_connected():
            self.disconnect()
        
        # Detener loop asyncio
        if self.loop and self.loop.is_running():
            self.loop.call_soon_threadsafe(self.loop.stop)
        
        # Esperar a que el thread termine
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=2)
        
        logger.info("Limpieza BLE completa")
    
    def __del__(self):
        """Destructor: asegurar limpieza."""
        self.cleanup()


# ═══════════════════════════════════════════════════════════════
# TESTING
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    # Configurar logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("\n" + "=" * 60)
    print("PRUEBA DE BluetoothBLEAdapter")
    print("=" * 60)
    
    try:
        # Crear adaptador
        adapter = BluetoothBLEAdapter()
        
        # Callback de datos
        def on_data(data):
            print(f"\n✓ DATOS: {data.decode('utf-8', errors='ignore')}")
        
        adapter.set_data_callback(on_data)
        
        # Escanear
        print("\n🔍 Escaneando...")
        devices = adapter.scan_devices(10)
        
        if not devices:
            print("❌ No se encontraron dispositivos")
        else:
            print(f"\n✓ Encontrados {len(devices)} dispositivos:")
            for i, dev in enumerate(devices, 1):
                print(f"   {i}. {dev['name']} - {dev['address']}")
            
            # Conectar al primero
            print(f"\n📡 Conectando a {devices[0]['name']}...")
            result = adapter.connect(devices[0]['address'])
            
            if result['success']:
                print("✓ Conectado")
                print("\n⚖️  PISA LA BÁSCULA")
                print("   Esperando 30 segundos...\n")
                
                time.sleep(30)
                
                adapter.disconnect()
            else:
                print(f"❌ Error: {result['message']}")
        
    except KeyboardInterrupt:
        print("\n\nInterrumpido por usuario")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if 'adapter' in locals():
            adapter.cleanup()
    
    print("\n" + "=" * 60)
    print("Prueba finalizada")
    print("=" * 60 + "\n")
