"""
Ventana principal de la interfaz gráfica.
Utiliza CustomTkinter para una apariencia moderna y profesional.
"""

import customtkinter as ctk
from tkinter import messagebox
import logging
from typing import Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class MainWindow:
    """
    Ventana principal de la aplicación.
    
    Proporciona una interfaz gráfica intuitiva para:
    - Conectar/desconectar dispositivos Bluetooth
    - Visualizar datos en tiempo real
    - Monitorear el estado de la conexión
    - Exportar datos recolectados
    """
    
    def __init__(self, bluetooth_manager, data_handler, config):
        """
        Inicializa la ventana principal.
        
        Args:
            bluetooth_manager: Instancia del gestor Bluetooth
            data_handler: Instancia del procesador de datos
            config: Configuración de la aplicación
        """
        self.bt_manager = bluetooth_manager
        self.data_handler = data_handler
        self.config = config
        
        # Crear ventana principal
        self.window = ctk.CTk()
        self.window.title(config.get('window_title', 'Monitor Bluetooth'))
        self.window.geometry(
            f"{config.get('window_width', 900)}x{config.get('window_height', 600)}"
        )
        
        # Configurar el cierre de ventana
        self.window.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Variables de UI
        self.devices_list = []
        self.selected_device = None
        
        # Construir la interfaz
        self._build_ui()
        
        logger.info("Ventana principal creada")
    
    def _build_ui(self):
        """Construye todos los elementos de la interfaz."""
        # Configurar grid layout
        self.window.grid_columnconfigure(1, weight=1)
        self.window.grid_rowconfigure(0, weight=1)
        
        # Panel lateral izquierdo (conexión)
        self._create_connection_panel()
        
        # Panel principal derecho (datos)
        self._create_data_panel()
        
        # Barra de estado inferior
        self._create_status_bar()
    
    def _create_connection_panel(self):
        """Crea el panel lateral de conexión."""
        # Frame contenedor
        self.connection_frame = ctk.CTkFrame(self.window, width=300, corner_radius=0)
        self.connection_frame.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)
        self.connection_frame.grid_rowconfigure(4, weight=1)
        
        # Título
        title = ctk.CTkLabel(
            self.connection_frame,
            text="Conexión Bluetooth",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="w")
        
        # Botón de escaneo
        self.scan_button = ctk.CTkButton(
            self.connection_frame,
            text="Escanear Dispositivos",
            command=self.scan_devices
        )
        self.scan_button.grid(row=1, column=0, padx=20, pady=10, sticky="ew")
        
        # Lista de dispositivos
        devices_label = ctk.CTkLabel(
            self.connection_frame,
            text="Dispositivos encontrados:",
            font=ctk.CTkFont(size=12)
        )
        devices_label.grid(row=2, column=0, padx=20, pady=(10, 5), sticky="w")
        
        self.devices_listbox = ctk.CTkTextbox(
            self.connection_frame,
            height=200,
            width=260
        )
        self.devices_listbox.grid(row=3, column=0, padx=20, pady=5, sticky="ew")
        self.devices_listbox.configure(state="disabled")
        
        # Información del dispositivo seleccionado
        self.device_info_label = ctk.CTkLabel(
            self.connection_frame,
            text="Ningún dispositivo seleccionado",
            font=ctk.CTkFont(size=11),
            text_color="gray"
        )
        self.device_info_label.grid(row=4, column=0, padx=20, pady=10, sticky="n")
        
        # Botones de conexión
        button_frame = ctk.CTkFrame(self.connection_frame, fg_color="transparent")
        button_frame.grid(row=5, column=0, padx=20, pady=(0, 20), sticky="ew")
        button_frame.grid_columnconfigure((0, 1), weight=1)
        
        self.connect_button = ctk.CTkButton(
            button_frame,
            text="Conectar",
            command=self.connect_device,
            state="disabled"
        )
        self.connect_button.grid(row=0, column=0, padx=(0, 5), pady=0, sticky="ew")
        
        self.disconnect_button = ctk.CTkButton(
            button_frame,
            text="Desconectar",
            command=self.disconnect_device,
            state="disabled",
            fg_color="gray",
            hover_color="darkgray"
        )
        self.disconnect_button.grid(row=0, column=1, padx=(5, 0), pady=0, sticky="ew")
    
    def _create_data_panel(self):
        """Crea el panel principal de visualización de datos."""
        # Frame contenedor
        self.data_frame = ctk.CTkFrame(self.window)
        self.data_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        self.data_frame.grid_rowconfigure(1, weight=1)
        self.data_frame.grid_columnconfigure(0, weight=1)
        
        # Título y controles
        header_frame = ctk.CTkFrame(self.data_frame, fg_color="transparent")
        header_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        header_frame.grid_columnconfigure(0, weight=1)
        
        title = ctk.CTkLabel(
            header_frame,
            text="Datos Recibidos",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title.grid(row=0, column=0, sticky="w")
        
        # Botones de control
        controls_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        controls_frame.grid(row=0, column=1, sticky="e")
        
        self.clear_button = ctk.CTkButton(
            controls_frame,
            text="Limpiar",
            command=self.clear_data,
            width=100
        )
        self.clear_button.grid(row=0, column=0, padx=5)
        
        self.export_button = ctk.CTkButton(
            controls_frame,
            text="Exportar CSV",
            command=self.export_data,
            width=120
        )
        self.export_button.grid(row=0, column=1, padx=5)
        
        # Área de visualización de datos
        self.data_display = ctk.CTkTextbox(
            self.data_frame,
            font=ctk.CTkFont(family="Courier", size=12)
        )
        self.data_display.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        
        # Mensaje inicial
        self.data_display.insert("1.0", "Esperando conexión...\n\n")
        self.data_display.configure(state="disabled")
    
    def _create_status_bar(self):
        """Crea la barra de estado en la parte inferior."""
        self.status_frame = ctk.CTkFrame(self.window, height=30, corner_radius=0)
        self.status_frame.grid(row=1, column=0, columnspan=2, sticky="ew", padx=0, pady=0)
        
        self.status_label = ctk.CTkLabel(
            self.status_frame,
            text="Estado: Desconectado",
            font=ctk.CTkFont(size=11)
        )
        self.status_label.pack(side="left", padx=10)
        
        self.message_counter = ctk.CTkLabel(
            self.status_frame,
            text="Mensajes: 0",
            font=ctk.CTkFont(size=11)
        )
        self.message_counter.pack(side="right", padx=10)
    
    def scan_devices(self):
        """Inicia el escaneo de dispositivos Bluetooth."""
        logger.info("Iniciando escaneo de dispositivos")
        
        # Deshabilitar botón durante escaneo
        self.scan_button.configure(state="disabled", text="Escaneando...")
        self.window.update()
        
        # Realizar escaneo
        self.devices_list = self.bt_manager.scan_devices(
            duration=self.config.get('scan_timeout', 8)
        )
        
        # Actualizar lista
        self.devices_listbox.configure(state="normal")
        self.devices_listbox.delete("1.0", "end")
        
        if self.devices_list:
            for i, device in enumerate(self.devices_list):
                self.devices_listbox.insert(
                    "end",
                    f"{i+1}. {device['name']}\n   {device['address']}\n\n"
                )
            self.connect_button.configure(state="normal")
        else:
            self.devices_listbox.insert("end", "No se encontraron dispositivos.\n")
        
        self.devices_listbox.configure(state="disabled")
        
        # Rehabilitar botón
        self.scan_button.configure(state="normal", text="Escanear Dispositivos")
        
        logger.info(f"Escaneo completado: {len(self.devices_list)} dispositivos encontrados")
    
    def connect_device(self):
        """Conecta al dispositivo seleccionado."""
        if not self.devices_list:
            messagebox.showwarning("Advertencia", "No hay dispositivos disponibles")
            return
        
        # Por ahora, conectar al primer dispositivo
        # TODO: Implementar selección de dispositivo
        device = self.devices_list[0]
        
        logger.info(f"Intentando conectar a {device['name']}")
        
        # Intentar conexión
        success = self.bt_manager.connect(device['address'])
        
        if success:
            self.selected_device = device
            self.device_info_label.configure(
                text=f"Conectado a:\n{device['name']}\n{device['address']}",
                text_color="green"
            )
            self.connect_button.configure(state="disabled")
            self.disconnect_button.configure(
                state="normal",
                fg_color=["#3B8ED0", "#1F6AA5"],
                hover_color=["#36719F", "#144870"]
            )
        else:
            messagebox.showerror(
                "Error de Conexión",
                f"No se pudo conectar a {device['name']}"
            )
    
    def disconnect_device(self):
        """Desconecta del dispositivo actual."""
        self.bt_manager.disconnect()
        
        self.selected_device = None
        self.device_info_label.configure(
            text="Ningún dispositivo seleccionado",
            text_color="gray"
        )
        self.connect_button.configure(state="normal")
        self.disconnect_button.configure(
            state="disabled",
            fg_color="gray",
            hover_color="darkgray"
        )
    
    def update_data_display(self, processed_data: Dict[str, Any]):
        """
        Actualiza la visualización con nuevos datos.
        
        Args:
            processed_data: Diccionario con los datos procesados
        """
        # Habilitar edición temporal
        self.data_display.configure(state="normal")
        
        # Formatear y mostrar datos
        timestamp = processed_data.get('timestamp', datetime.now())
        data = processed_data.get('data', {})
        
        # Crear línea de datos
        display_text = f"[{timestamp.strftime('%H:%M:%S')}] "
        
        if isinstance(data, dict):
            # Formatear datos como clave: valor
            items = [f"{k}: {v}" for k, v in data.items()]
            display_text += " | ".join(items)
        else:
            display_text += str(data)
        
        display_text += "\n"
        
        # Insertar al final
        self.data_display.insert("end", display_text)
        
        # Auto-scroll al final
        self.data_display.see("end")
        
        # Deshabilitar edición
        self.data_display.configure(state="disabled")
        
        # Actualizar contador
        count = processed_data.get('message_number', 0)
        self.message_counter.configure(text=f"Mensajes: {count}")
    
    def update_connection_status(self, connected: bool, device_info: Dict = None):
        """
        Actualiza el estado de la conexión en la UI.
        
        Args:
            connected: True si está conectado
            device_info: Información del dispositivo
        """
        if connected:
            status_text = f"Estado: Conectado - {device_info.get('name', 'Desconocido')}"
            self.status_label.configure(text=status_text, text_color="green")
        else:
            self.status_label.configure(text="Estado: Desconectado", text_color="red")
    
    def clear_data(self):
        """Limpia el área de visualización de datos."""
        response = messagebox.askyesno(
            "Confirmar",
            "¿Desea limpiar todos los datos mostrados?"
        )
        
        if response:
            self.data_display.configure(state="normal")
            self.data_display.delete("1.0", "end")
            self.data_display.configure(state="disabled")
            
            self.data_handler.clear_history()
            self.message_counter.configure(text="Mensajes: 0")
            
            logger.info("Datos limpiados")
    
    def export_data(self):
        """Exporta los datos a un archivo CSV."""
        filename = f"bluetooth_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        success = self.data_handler.export_to_csv(filename)
        
        if success:
            messagebox.showinfo(
                "Exportación Exitosa",
                f"Datos exportados a:\n{filename}"
            )
        else:
            messagebox.showerror(
                "Error",
                "No se pudieron exportar los datos"
            )
    
    def show_error(self, message: str):
        """Muestra un mensaje de error al usuario."""
        messagebox.showerror("Error", message)
    
    def on_closing(self):
        """Maneja el cierre de la ventana."""
        if self.bt_manager.is_connected():
            response = messagebox.askyesno(
                "Confirmar Salida",
                "Hay una conexión activa. ¿Desea salir de todas formas?"
            )
            if not response:
                return
        
        logger.info("Cerrando aplicación desde UI")
        self.window.destroy()
    
    def run(self):
        """Inicia el loop principal de la interfaz."""
        self.window.mainloop()
