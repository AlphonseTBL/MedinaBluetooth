"""
Aplicación Bluetooth con CustomTkinter
Autor: Equipo MedinaBluetooth
Versión: 2.0.0
Descripción: Aplicación para escanear, seleccionar y recibir datos de dispositivos Bluetooth
            Soporta Bluetooth Classic (SPP/RFCOMM) y Bluetooth Low Energy (BLE)
"""

import customtkinter as ctk
from src.bluetooth_manager import BluetoothManager
from src.data_handler import DataHandler
from src.ui.main_window import MainWindow
from src.config import Config
import logging

# Intentar importar soporte BLE
try:
    from src.bluetooth_ble_adapter import BluetoothBLEAdapter, BLEAK_AVAILABLE
    BLE_SUPPORT = True
except ImportError:
    BLEAK_AVAILABLE = False
    BLE_SUPPORT = False

# Configuración del sistema de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bluetooth_app.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


class BluetoothApp:
    """
    Clase principal de la aplicación que coordina todos los componentes.
    
    NUEVO EN VERSIÓN 2.0:
    ═══════════════════════════════════════════════════════════════════
    Ahora soporta AMBOS tipos de Bluetooth:
    
    • Bluetooth Classic (SPP/RFCOMM) - Para Arduino, HC-05, etc.
    • Bluetooth Low Energy (BLE) - Para básculas Renpho, etc.
    
    El tipo se configura en config.json con "usar_ble": true/false
    ═══════════════════════════════════════════════════════════════════
    """
    
    def __init__(self):
        """Inicializa la aplicación y todos sus componentes."""
        logger.info("=" * 60)
        logger.info("Iniciando MedinaBluetooth v2.0")
        logger.info("=" * 60)
        
        # Cargar configuración
        self.config = Config()
        
        # Configurar el tema de CustomTkinter
        ctk.set_appearance_mode(self.config.get('appearance_mode', 'dark'))
        ctk.set_default_color_theme(self.config.get('color_theme', 'blue'))
        
        # Determinar qué gestor Bluetooth usar
        usar_ble = self.config.get('usar_ble', False)
        
        # Inicializar gestor Bluetooth apropiado
        if usar_ble:
            logger.info("Modo: Bluetooth Low Energy (BLE)")
            if not BLE_SUPPORT or not BLEAK_AVAILABLE:
                logger.error("=" * 60)
                logger.error("ERROR: Modo BLE solicitado pero bleak no está instalado")
                logger.error("Instalar con: pip install bleak")
                logger.error("Cambiando a modo Bluetooth Classic...")
                logger.error("=" * 60)
                self.bluetooth_manager = BluetoothManager()
            else:
                try:
                    self.bluetooth_manager = BluetoothBLEAdapter()
                    logger.info("✓ Gestor BLE inicializado correctamente")
                except Exception as e:
                    logger.error(f"Error iniciando BLE: {e}")
                    logger.info("Cambiando a Bluetooth Classic...")
                    self.bluetooth_manager = BluetoothManager()
        else:
            logger.info("Modo: Bluetooth Classic (SPP/RFCOMM)")
            self.bluetooth_manager = BluetoothManager()
        
        # Inicializar resto de componentes (igual que antes)
        self.data_handler = DataHandler()
        self.ui = MainWindow(
            bluetooth_manager=self.bluetooth_manager,
            data_handler=self.data_handler,
            config=self.config
        )
        
        # Conectar callbacks
        self._setup_callbacks()
        
        logger.info("Aplicación inicializada correctamente")
        logger.info("=" * 60)
        
    def _setup_callbacks(self):
        """
        Configura los callbacks entre componentes.
        
        Esto permite que el gestor de Bluetooth notifique a la interfaz
        cuando se reciben nuevos datos.
        """
        self.bluetooth_manager.set_data_callback(self._on_data_received)
        self.bluetooth_manager.set_connection_callback(self._on_connection_change)
        
    def _on_data_received(self, raw_data):
        """
        Callback ejecutado cuando se reciben datos del dispositivo Bluetooth.
        
        Args:
            raw_data: Datos crudos recibidos del dispositivo
        """
        try:
            # Procesar los datos recibidos
            processed_data = self.data_handler.process(raw_data)
            
            # Actualizar la interfaz con los datos procesados
            self.ui.update_data_display(processed_data)
            
            logger.debug(f"Datos procesados: {processed_data}")
            
        except Exception as e:
            logger.error(f"Error al procesar datos: {e}")
            self.ui.show_error(f"Error procesando datos: {str(e)}")
    
    def _on_connection_change(self, connected, device_info=None):
        """
        Callback ejecutado cuando cambia el estado de la conexión.
        
        Args:
            connected: True si está conectado, False si está desconectado
            device_info: Información del dispositivo conectado
        """
        self.ui.update_connection_status(connected, device_info)
        
        if connected:
            logger.info(f"Conectado a dispositivo: {device_info}")
        else:
            logger.info("Desconectado del dispositivo")
    
    def run(self):
        """Inicia el loop principal de la aplicación."""
        logger.info("Iniciando interfaz gráfica")
        self.ui.run()
    
    def cleanup(self):
        """Limpia recursos antes de cerrar la aplicación."""
        logger.info("Cerrando aplicación...")
        
        try:
            # Desconectar Bluetooth
            self.bluetooth_manager.disconnect()
            
            # Si es BLE, limpieza adicional
            if hasattr(self.bluetooth_manager, 'cleanup'):
                logger.info("Limpiando recursos BLE...")
                self.bluetooth_manager.cleanup()
                
        except Exception as e:
            logger.error(f"Error durante limpieza: {e}")
        
        logger.info("Aplicación cerrada")


def main():
    """Punto de entrada principal de la aplicación."""
    try:
        app = BluetoothApp()
        app.run()
    except KeyboardInterrupt:
        logger.info("\nAplicación interrumpida por el usuario")
    except Exception as e:
        logger.critical(f"Error crítico: {e}", exc_info=True)
    finally:
        if 'app' in locals():
            app.cleanup()


if __name__ == "__main__":
    main()
