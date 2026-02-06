"""
Aplicación Bluetooth con CustomTkinter
Autor: Tu Nombre
Versión: 1.0.0
Descripción: Aplicación para recibir y visualizar datos de dispositivos Bluetooth
"""

import customtkinter as ctk
from src.bluetooth_manager import BluetoothManager
from src.data_handler import DataHandler
from src.ui.main_window import MainWindow
from src.config import Config
import logging

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
    
    Esta clase actúa como el controlador principal que une el gestor de Bluetooth,
    el procesador de datos y la interfaz gráfica.
    """
    
    def __init__(self):
        """Inicializa la aplicación y todos sus componentes."""
        logger.info("Iniciando aplicación Bluetooth")
        
        # Cargar configuración
        self.config = Config()
        
        # Configurar el tema de CustomTkinter
        ctk.set_appearance_mode(self.config.get('appearance_mode', 'dark'))
        ctk.set_default_color_theme(self.config.get('color_theme', 'blue'))
        
        # Inicializar componentes
        self.bluetooth_manager = BluetoothManager()
        self.data_handler = DataHandler()
        self.ui = MainWindow(
            bluetooth_manager=self.bluetooth_manager,
            data_handler=self.data_handler,
            config=self.config
        )
        
        # Conectar callbacks
        self._setup_callbacks()
        
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
        logger.info("Cerrando aplicación")
        self.bluetooth_manager.disconnect()


def main():
    """Punto de entrada principal de la aplicación."""
    try:
        app = BluetoothApp()
        app.run()
    except KeyboardInterrupt:
        logger.info("Aplicación interrumpida por el usuario")
    except Exception as e:
        logger.critical(f"Error crítico: {e}", exc_info=True)
    finally:
        if 'app' in locals():
            app.cleanup()


if __name__ == "__main__":
    main()
