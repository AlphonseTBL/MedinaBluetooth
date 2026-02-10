"""
Ventana principal de la aplicación
"""

import customtkinter as ctk
from tkinter import messagebox, filedialog
import logging
import threading

logger = logging.getLogger(__name__)


class MainWindow:
    """
    Ventana principal de la aplicación Bluetooth.
    
    Maneja toda la interfaz gráfica y la interacción con el usuario.
    """
    
    def __init__(self, bluetooth_manager, data_handler, config):
        """
        Inicializa la ventana principal.
        
        Args:
            bluetooth_manager: Instancia del gestor de Bluetooth
            data_handler: Instancia del manejador de datos
            config: Configuración de la aplicación
        """
        self.bt_manager = bluetooth_manager
        self.data_handler = data_handler
        self.config = config
        
        # Lista de dispositivos encontrados
        self.devices_list = []
        self.selected_device = None
        
        # Crear ventana principal
        self.root = ctk.CTk()
        self.root.title("Aplicación Bluetooth - Selector de Dispositivos")
        self.root.geometry(self.config.get('window_size', '900x700'))
        
        # Configurar cierre de ventana
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Crear interfaz
        self._create_widgets()
        
        logger.info("Ventana principal creada")
    
    def _create_widgets(self):
        """Crea todos los widgets de la interfaz."""
        
        # ========== FRAME SUPERIOR: CONEXIÓN Y ESCANEO ==========
        connection_frame = ctk.CTkFrame(self.root)
        connection_frame.pack(fill="x", padx=10, pady=10)
        
        # Título
        title_label = ctk.CTkLabel(
            connection_frame,
            text="🔵 Gestor de Dispositivos Bluetooth",
            font=("Arial", 20, "bold")
        )
        title_label.pack(pady=10)
        
        # Botón de escaneo
        self.scan_button = ctk.CTkButton(
            connection_frame,
            text="🔍 Escanear Dispositivos",
            command=self.start_scan,
            width=200,
            height=40,
            font=("Arial", 14, "bold")
        )
        self.scan_button.pack(pady=5)
        
        # Label de estado de escaneo
        self.scan_status_label = ctk.CTkLabel(
            connection_frame,
            text="Presiona 'Escanear' para buscar dispositivos",
            font=("Arial", 12)
        )
        self.scan_status_label.pack(pady=5)
        
        # ========== FRAME CENTRAL: LISTA DE DISPOSITIVOS ==========
        devices_frame = ctk.CTkFrame(self.root)
        devices_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        devices_label = ctk.CTkLabel(
            devices_frame,
            text="Dispositivos Encontrados:",
            font=("Arial", 16, "bold")
        )
        devices_label.pack(pady=10)
        
        # Frame con scrollbar para la lista de dispositivos
        list_frame = ctk.CTkFrame(devices_frame)
        list_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # ScrollableFrame para dispositivos
        self.devices_scrollable = ctk.CTkScrollableFrame(list_frame)
        self.devices_scrollable.pack(fill="both", expand=True)
        
        # Mensaje cuando no hay dispositivos
        self.no_devices_label = ctk.CTkLabel(
            self.devices_scrollable,
            text="No hay dispositivos escaneados.\nPresiona 'Escanear Dispositivos' para comenzar.",
            font=("Arial", 12),
            text_color="gray"
        )
        self.no_devices_label.pack(pady=50)
        
        # ========== FRAME DE CONEXIÓN ==========
        connect_frame = ctk.CTkFrame(self.root)
        connect_frame.pack(fill="x", padx=10, pady=10)
        
        # Label de dispositivo seleccionado
        self.selected_label = ctk.CTkLabel(
            connect_frame,
            text="Ningún dispositivo seleccionado",
            font=("Arial", 12),
            text_color="orange"
        )
        self.selected_label.pack(pady=5)
        
        # Botones de conexión
        button_frame = ctk.CTkFrame(connect_frame)
        button_frame.pack(pady=5)
        
        # Botón de diagnóstico
        self.diagnostic_button = ctk.CTkButton(
            button_frame,
            text="🔍 Diagnosticar",
            command=self.diagnosticar_dispositivo_seleccionado,
            width=150,
            state="disabled",
            fg_color="purple",
            hover_color="darkviolet"
        )
        self.diagnostic_button.pack(side="left", padx=5)
        
        self.connect_button = ctk.CTkButton(
            button_frame,
            text="📡 Conectar",
            command=self.connect_to_device,
            width=150,
            state="disabled"
        )
        self.connect_button.pack(side="left", padx=5)
        
        self.disconnect_button = ctk.CTkButton(
            button_frame,
            text="❌ Desconectar",
            command=self.disconnect_from_device,
            width=150,
            state="disabled",
            fg_color="red",
            hover_color="darkred"
        )
        self.disconnect_button.pack(side="left", padx=5)
        
        # Estado de conexión
        self.connection_status_label = ctk.CTkLabel(
            connect_frame,
            text="● Desconectado",
            font=("Arial", 14, "bold"),
            text_color="red"
        )
        self.connection_status_label.pack(pady=5)
        
        # ========== FRAME INFERIOR: DATOS RECIBIDOS ==========
        data_frame = ctk.CTkFrame(self.root)
        data_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        data_label = ctk.CTkLabel(
            data_frame,
            text="Datos Recibidos:",
            font=("Arial", 14, "bold")
        )
        data_label.pack(pady=5)
        
        # TextBox para mostrar datos
        self.data_textbox = ctk.CTkTextbox(
            data_frame,
            height=150,
            font=("Courier", 11)
        )
        self.data_textbox.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Botón para limpiar datos
        clear_button = ctk.CTkButton(
            data_frame,
            text="🗑️ Limpiar Datos",
            command=self.clear_data_display,
            width=150
        )
        clear_button.pack(pady=5)
    
    def start_scan(self):
        """
        Inicia el escaneo de dispositivos Bluetooth.
        
        Este método se ejecuta en un hilo separado para no bloquear la UI.
        """
        # Deshabilitar botón durante escaneo
        self.scan_button.configure(state="disabled", text="⏳ Escaneando...")
        self.scan_status_label.configure(
            text="Escaneando dispositivos Bluetooth... (esto puede tardar unos segundos)",
            text_color="orange"
        )
        
        # Limpiar lista anterior
        self.clear_device_list()
        
        # Ejecutar escaneo en hilo separado
        scan_thread = threading.Thread(target=self._perform_scan, daemon=True)
        scan_thread.start()
    
    def _perform_scan(self):
        """
        Realiza el escaneo de dispositivos en un hilo separado.
        
        Este método NO debe interactuar directamente con la UI.
        """
        try:
            # Obtener duración del escaneo desde config
            duration = self.config.get('scan_duration', 8)
            
            # Realizar escaneo
            devices = self.bt_manager.scan_devices(duration=duration)
            
            # Actualizar UI en el hilo principal
            self.root.after(0, self._update_devices_list, devices)
            
        except Exception as e:
            logger.error(f"Error durante escaneo: {e}")
            self.root.after(0, self._scan_error, str(e))
    
    def _update_devices_list(self, devices):
        """
        Actualiza la lista de dispositivos en la UI.
        
        Args:
            devices: Lista de dispositivos encontrados
        """
        self.devices_list = devices
        
        # Limpiar widgets anteriores
        self.clear_device_list()
        
        if not devices:
            # Mostrar mensaje si no hay dispositivos
            self.no_devices_label.pack(pady=50)
            self.scan_status_label.configure(
                text=f"No se encontraron dispositivos. Intenta escanear nuevamente.",
                text_color="red"
            )
        else:
            # Ocultar mensaje de "no dispositivos"
            self.no_devices_label.pack_forget()
            
            # Crear un widget por cada dispositivo
            for idx, device in enumerate(devices):
                self._create_device_widget(device, idx)
            
            self.scan_status_label.configure(
                text=f"✓ Se encontraron {len(devices)} dispositivo(s)",
                text_color="green"
            )
        
        # Rehabilitar botón de escaneo
        self.scan_button.configure(state="normal", text="🔍 Escanear Dispositivos")
    
    def _create_device_widget(self, device, index):
        """
        Crea un widget para mostrar un dispositivo.
        
        Args:
            device: Diccionario con información del dispositivo
            index: Índice del dispositivo en la lista
        """
        # Frame para cada dispositivo
        device_frame = ctk.CTkFrame(
            self.devices_scrollable,
            corner_radius=10
        )
        device_frame.pack(fill="x", padx=10, pady=5)
        
        # Frame de información
        info_frame = ctk.CTkFrame(device_frame, fg_color="transparent")
        info_frame.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        
        # Nombre del dispositivo
        name_label = ctk.CTkLabel(
            info_frame,
            text=f"📱 {device['name']}",
            font=("Arial", 14, "bold"),
            anchor="w"
        )
        name_label.pack(anchor="w")
        
        # Dirección MAC
        address_label = ctk.CTkLabel(
            info_frame,
            text=f"MAC: {device['address']}",
            font=("Courier", 11),
            text_color="gray",
            anchor="w"
        )
        address_label.pack(anchor="w")
        
        # Botón de selección
        select_button = ctk.CTkButton(
            device_frame,
            text="Seleccionar",
            command=lambda d=device: self.select_device(d),
            width=120
        )
        select_button.pack(side="right", padx=10)
    
    def select_device(self, device):
        """
        Selecciona un dispositivo de la lista.
        
        Args:
            device: Diccionario con información del dispositivo
        """
        self.selected_device = device
        
        # Actualizar label de selección
        self.selected_label.configure(
            text=f"✓ Dispositivo seleccionado: {device['name']} ({device['address']})",
            text_color="green"
        )
        
        # Habilitar botones de diagnóstico y conexión
        self.diagnostic_button.configure(state="normal")
        self.connect_button.configure(state="normal")
        
        logger.info(f"Dispositivo seleccionado: {device['name']} - {device['address']}")
    
    def diagnosticar_dispositivo_seleccionado(self):
        """
        Diagnostica el dispositivo seleccionado y muestra los resultados.
        
        Este método ejecuta un diagnóstico completo del dispositivo para
        verificar su compatibilidad con la aplicación.
        """
        if not self.selected_device:
            messagebox.showwarning(
                "Sin dispositivo",
                "Por favor selecciona un dispositivo primero"
            )
            return
        
        # Deshabilitar botón durante diagnóstico
        self.diagnostic_button.configure(state="disabled", text="⏳ Diagnosticando...")
        
        # Ejecutar diagnóstico en hilo separado
        diagnostic_thread = threading.Thread(
            target=self._perform_diagnostic,
            daemon=True
        )
        diagnostic_thread.start()
    
    def _perform_diagnostic(self):
        """
        Realiza el diagnóstico en un hilo separado.
        
        Este método NO debe interactuar directamente con la UI.
        """
        try:
            # Realizar diagnóstico
            resultado = self.bt_manager.diagnosticar_dispositivo(
                self.selected_device['address'],
                self.selected_device['name']
            )
            
            # Actualizar UI en el hilo principal
            self.root.after(0, self._mostrar_resultado_diagnostico, resultado)
            
        except Exception as e:
            logger.error(f"Error durante diagnóstico: {e}")
            self.root.after(0, self._diagnostic_error, str(e))
    
    def _mostrar_resultado_diagnostico(self, resultado):
        """
        Muestra el resultado del diagnóstico en una ventana.
        
        Args:
            resultado: Diccionario con información del diagnóstico
        """
        # Rehabilitar botón
        self.diagnostic_button.configure(state="normal", text="🔍 Diagnosticar")
        
        # Crear ventana de diagnóstico
        ventana_diagnostico = ctk.CTkToplevel(self.root)
        ventana_diagnostico.title(f"Diagnóstico - {self.selected_device['name']}")
        ventana_diagnostico.geometry("600x500")
        
        # Centrar ventana
        ventana_diagnostico.transient(self.root)
        ventana_diagnostico.grab_set()
        
        # Frame principal
        main_frame = ctk.CTkFrame(ventana_diagnostico)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Título
        titulo_color = "green" if resultado['compatible'] else "red"
        titulo_label = ctk.CTkLabel(
            main_frame,
            text=resultado['mensaje'],
            font=("Arial", 24, "bold"),
            text_color=titulo_color
        )
        titulo_label.pack(pady=10)
        
        # Información del dispositivo
        info_frame = ctk.CTkFrame(main_frame)
        info_frame.pack(fill="x", pady=10)
        
        device_info = ctk.CTkLabel(
            info_frame,
            text=f"📱 {self.selected_device['name']}\n"
                 f"📍 MAC: {self.selected_device['address']}",
            font=("Arial", 12),
            justify="left"
        )
        device_info.pack(pady=10)
        
        # Detalles del diagnóstico
        details_label = ctk.CTkLabel(
            main_frame,
            text="Detalles del Diagnóstico:",
            font=("Arial", 14, "bold")
        )
        details_label.pack(pady=(10, 5))
        
        # TextBox con detalles
        details_textbox = ctk.CTkTextbox(
            main_frame,
            height=250,
            font=("Courier", 11)
        )
        details_textbox.pack(fill="both", expand=True, pady=5)
        details_textbox.insert("1.0", resultado['detalles'])
        details_textbox.configure(state="disabled")  # Solo lectura
        
        # Botón de cerrar
        close_button = ctk.CTkButton(
            main_frame,
            text="Cerrar",
            command=ventana_diagnostico.destroy,
            width=150
        )
        close_button.pack(pady=10)
        
        # Si es compatible, ofrecer conectar directamente
        if resultado['compatible'] and resultado['puerto_sugerido']:
            connect_button = ctk.CTkButton(
                main_frame,
                text=f"📡 Conectar a Puerto {resultado['puerto_sugerido']}",
                command=lambda: self._conectar_con_puerto(
                    resultado['puerto_sugerido'],
                    ventana_diagnostico
                ),
                width=250,
                fg_color="green",
                hover_color="darkgreen"
            )
            connect_button.pack(pady=5)
    
    def _conectar_con_puerto(self, puerto, ventana):
        """
        Conecta usando un puerto específico sugerido por el diagnóstico.
        
        Args:
            puerto: Puerto RFCOMM a usar
            ventana: Ventana de diagnóstico a cerrar
        """
        # Guardar puerto sugerido
        if not hasattr(self, '_puerto_sugerido'):
            self._puerto_sugerido = puerto
        
        # Cerrar ventana de diagnóstico
        ventana.destroy()
        
        # Conectar
        self.connect_to_device()
    
    def _diagnostic_error(self, error_msg):
        """
        Maneja errores durante el diagnóstico.
        
        Args:
            error_msg: Mensaje de error
        """
        self.diagnostic_button.configure(state="normal", text="🔍 Diagnosticar")
        
        messagebox.showerror(
            "Error de diagnóstico",
            f"Error al diagnosticar el dispositivo:\n\n{error_msg}"
        )
    
    def connect_to_device(self):
        """Conecta al dispositivo seleccionado."""
        if not self.selected_device:
            messagebox.showwarning(
                "Sin dispositivo",
                "Por favor selecciona un dispositivo primero"
            )
            return
        
        # Deshabilitar botones
        self.connect_button.configure(state="disabled")
        self.scan_button.configure(state="disabled")
        
        # Actualizar estado
        self.connection_status_label.configure(
            text="● Conectando...",
            text_color="orange"
        )
        
        # Conectar en hilo separado
        connect_thread = threading.Thread(
            target=self._perform_connection,
            daemon=True
        )
        connect_thread.start()
    
    def _perform_connection(self):
        """Realiza la conexión en un hilo separado."""
        try:
            # Intentar conexión
            success = self.bt_manager.connect(self.selected_device['address'])
            
            # Actualizar UI según resultado
            self.root.after(0, self._connection_result, success)
            
        except Exception as e:
            logger.error(f"Error en conexión: {e}")
            self.root.after(0, self._connection_result, False)
    
    def _connection_result(self, success):
        """
        Maneja el resultado de la conexión.
        
        Args:
            success: True si la conexión fue exitosa
        """
        if success:
            self.connection_status_label.configure(
                text="● Conectado",
                text_color="green"
            )
            self.disconnect_button.configure(state="normal")
            self.connect_button.configure(state="disabled")
            
            messagebox.showinfo(
                "Conexión exitosa",
                f"Conectado a {self.selected_device['name']}"
            )
        else:
            self.connection_status_label.configure(
                text="● Error de conexión",
                text_color="red"
            )
            self.connect_button.configure(state="normal")
            self.scan_button.configure(state="normal")
            
            messagebox.showerror(
                "Error de conexión",
                f"No se pudo conectar a {self.selected_device['name']}\n\n"
                "Verifica que:\n"
                "• El dispositivo está encendido\n"
                "• El Bluetooth está habilitado\n"
                "• El dispositivo acepta conexiones"
            )
    
    def disconnect_from_device(self):
        """Desconecta del dispositivo actual."""
        self.bt_manager.disconnect()
        
        # Actualizar UI
        self.connection_status_label.configure(
            text="● Desconectado",
            text_color="red"
        )
        self.disconnect_button.configure(state="disabled")
        self.connect_button.configure(state="normal")
        self.scan_button.configure(state="normal")
    
    def clear_device_list(self):
        """Limpia la lista de dispositivos mostrados."""
        # Destruir todos los widgets hijos del frame scrollable
        for widget in self.devices_scrollable.winfo_children():
            widget.destroy()
    
    def _scan_error(self, error_msg):
        """
        Maneja errores durante el escaneo.
        
        Args:
            error_msg: Mensaje de error
        """
        self.scan_button.configure(state="normal", text="🔍 Escanear Dispositivos")
        self.scan_status_label.configure(
            text=f"Error durante escaneo: {error_msg}",
            text_color="red"
        )
        
        messagebox.showerror("Error de escaneo", f"Error durante el escaneo:\n{error_msg}")
    
    def update_data_display(self, processed_data):
        """
        Actualiza la visualización de datos recibidos.
        
        Args:
            processed_data: Datos procesados del manejador de datos
        """
        # Formatear datos para mostrar
        timestamp = processed_data['timestamp'].strftime("%H:%M:%S")
        text = processed_data['text']
        hex_data = processed_data['hex']
        
        # Agregar al textbox
        display_text = f"[{timestamp}] {text}\n"
        if hex_data:
            display_text += f"  HEX: {hex_data}\n"
        
        self.data_textbox.insert("end", display_text)
        
        # Auto-scroll al final
        self.data_textbox.see("end")
    
    def clear_data_display(self):
        """Limpia la visualización de datos."""
        self.data_textbox.delete("1.0", "end")
        self.data_handler.clear_history()
    
    def update_connection_status(self, connected, device_info):
        """
        Actualiza el estado de la conexión.
        
        Args:
            connected: True si está conectado
            device_info: Información del dispositivo
        """
        if connected:
            self.connection_status_label.configure(
                text="● Conectado",
                text_color="green"
            )
        else:
            self.connection_status_label.configure(
                text="● Desconectado",
                text_color="red"
            )
    
    def show_error(self, message):
        """
        Muestra un mensaje de error.
        
        Args:
            message: Mensaje a mostrar
        """
        messagebox.showerror("Error", message)
    
    def on_closing(self):
        """Maneja el cierre de la ventana."""
        if self.bt_manager.is_connected():
            if messagebox.askokcancel("Cerrar", "¿Desconectar y cerrar la aplicación?"):
                self.bt_manager.disconnect()
                self.root.destroy()
        else:
            self.root.destroy()
    
    def run(self):
        """Inicia el loop principal de la aplicación."""
        self.root.mainloop()
