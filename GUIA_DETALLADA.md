# 📘 GUÍA PASO A PASO - Explicación Detallada del Código

## 🎯 Objetivo del Proyecto

Crear una aplicación que permita:
1. **Escanear** dispositivos Bluetooth cercanos
2. **Seleccionar** visualmente qué dispositivo usar
3. **Conectar** al dispositivo elegido
4. **Recibir y mostrar** datos en tiempo real

---

## 📚 Conceptos Fundamentales

### 1. ¿Qué es Bluetooth RFCOMM?

**RFCOMM** = Radio Frequency Communication

```
┌─────────────┐         RFCOMM         ┌─────────────┐
│             │◄─────────────────────►│             │
│  Computadora│    (Como un cable    │  Dispositivo│
│             │     serial virtual)   │  Bluetooth  │
└─────────────┘                        └─────────────┘
```

Es como crear un "cable virtual" entre dos dispositivos Bluetooth.

### 2. ¿Qué es un Socket?

Un **socket** es un punto de conexión para enviar/recibir datos:

```python
# Crear un socket Bluetooth
socket = bluetooth.BluetoothSocket(bluetooth.RFCOMM)

# Es como crear un "teléfono" para comunicarse
# Ahora puedes "llamar" (conectar) a otro dispositivo
socket.connect((address, port))

# Y "hablar" (enviar datos)
socket.send("Hola")

# Y "escuchar" (recibir datos)
data = socket.recv(1024)
```

### 3. ¿Por qué Threading?

**Sin threading:**
```python
# La UI se congela mientras escanea
button.configure(state="disabled")
devices = scan_bluetooth()  # ⏸️ UI CONGELADA 8 segundos
show_devices(devices)
```

**Con threading:**
```python
# La UI sigue funcionando
button.configure(state="disabled")
Thread(target=scan_and_update).start()  # ✅ UI responde

def scan_and_update():
    devices = scan_bluetooth()  # En segundo plano
    root.after(0, show_devices, devices)  # Actualizar UI de forma segura
```

---

## 🔍 Análisis Línea por Línea - Componente Principal

### **BluetoothManager - scan_devices()**

```python
def scan_devices(self, duration=8):
    """Escanea dispositivos Bluetooth cercanos."""
    
    logger.info(f"Iniciando escaneo (duración: {duration}s)")
    
    try:
        # PASO 1: Llamar a PyBluez para escanear
        nearby_devices = bluetooth.discover_devices(
            duration=duration,        # Cuánto tiempo escanear
            lookup_names=True,        # Obtener nombres de dispositivos
            flush_cache=True,         # No usar caché antiguo
            lookup_class=False        # No necesitamos clase de dispositivo
        )
        
        # nearby_devices es una lista de tuplas:
        # [('00:11:22:33:44:55', 'Mi Headset'),
        #  ('AA:BB:CC:DD:EE:FF', 'Arduino BT')]
        
        logger.info(f"Encontrados: {len(nearby_devices)}")
        
        # PASO 2: Formatear en diccionarios más legibles
        devices = []
        for addr, name in nearby_devices:
            devices.append({
                'name': name if name else "Dispositivo desconocido",
                'address': addr
            })
        
        return devices
        
    except Exception as e:
        logger.error(f"Error durante escaneo: {e}")
        return []
```

**¿Qué está pasando aquí?**

1. `bluetooth.discover_devices()` activa el adaptador Bluetooth
2. Escanea señales Bluetooth durante 8 segundos
3. Por cada señal encontrada, obtiene:
   - **Dirección MAC** (identificador único): `00:11:22:33:44:55`
   - **Nombre del dispositivo** (si está disponible): `"Mi Headset"`
4. Retorna lista de dispositivos encontrados

---

### **BluetoothManager - connect()**

```python
def connect(self, device_address, port=1):
    """Conecta a un dispositivo Bluetooth."""
    
    try:
        logger.info(f"Conectando a {device_address}:{port}")
        
        # PASO 1: Crear socket Bluetooth tipo RFCOMM
        self.socket = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
        # RFCOMM = protocolo para comunicación serial
        
        # PASO 2: Conectar al dispositivo
        self.socket.connect((device_address, port))
        # device_address = "00:11:22:33:44:55"
        # port = 1 (puerto RFCOMM, similar a puerto TCP)
        
        # PASO 3: Marcar como conectado
        self.connected = True
        self.current_device = {
            'address': device_address,
            'port': port
        }
        
        # PASO 4: Iniciar hilo para recibir datos
        self._start_receive_thread()
        
        logger.info(f"Conectado a {device_address}")
        
        # PASO 5: Notificar a la UI
        if self.connection_callback:
            self.connection_callback(True, self.current_device)
        
        return True
        
    except bluetooth.BluetoothError as e:
        logger.error(f"Error Bluetooth: {e}")
        return False
```

**¿Qué está pasando?**

1. **Crear socket**: Es como tomar un "teléfono Bluetooth"
2. **Conectar**: Es como "marcar el número" (dirección MAC)
3. **Guardar estado**: Recordar que estamos conectados
4. **Iniciar recepción**: Empezar a escuchar datos entrantes
5. **Notificar UI**: Informar a la interfaz que todo está listo

---

### **BluetoothManager - _receive_loop()**

```python
def _receive_loop(self):
    """Loop que recibe datos continuamente."""
    
    logger.info("Loop de recepción iniciado")
    
    # Mientras estemos conectados...
    while self.running and self.connected:
        try:
            # PASO 1: Esperar datos (BLOQUEANTE)
            data = self.socket.recv(1024)
            # recv(1024) = recibir hasta 1024 bytes
            # Esta línea BLOQUEA hasta que lleguen datos
            
            if data:
                # PASO 2: Si llegaron datos, procesarlos
                logger.debug(f"Datos recibidos: {data}")
                
                # PASO 3: Llamar al callback
                if self.data_callback:
                    self.data_callback(data)
                    # Esto llama a _on_data_received en main.py
            else:
                # Si no hay datos, posible desconexión
                logger.warning("Sin datos, posible desconexión")
                time.sleep(0.1)
                
        except bluetooth.BluetoothError as e:
            if self.running:
                logger.error(f"Error en recepción: {e}")
                self.disconnect()
            break
    
    logger.info("Loop finalizado")
```

**¿Por qué en un hilo separado?**

```python
# ❌ PROBLEMA si estuviera en el hilo principal:
data = socket.recv(1024)  # ⏸️ Se CONGELA aquí esperando datos
# La UI no responde, usuario no puede hacer clic en nada

# ✅ SOLUCIÓN con threading:
Thread(target=_receive_loop).start()
# El loop se ejecuta en segundo plano
# La UI sigue funcionando normalmente
```

---

### **MainWindow - start_scan()**

```python
def start_scan(self):
    """Inicia el escaneo de dispositivos."""
    
    # PASO 1: Deshabilitar botón (evitar múltiples escaneos)
    self.scan_button.configure(
        state="disabled",
        text="⏳ Escaneando..."
    )
    
    # PASO 2: Actualizar estado en UI
    self.scan_status_label.configure(
        text="Escaneando... (esto puede tardar unos segundos)",
        text_color="orange"
    )
    
    # PASO 3: Limpiar lista anterior
    self.clear_device_list()
    
    # PASO 4: Crear hilo para escanear
    scan_thread = threading.Thread(
        target=self._perform_scan,
        daemon=True  # Se cierra automáticamente al cerrar app
    )
    scan_thread.start()
```

**¿Por qué crear un hilo aquí?**

Sin hilo, la UI se congelaría durante 8 segundos. El usuario no podría mover la ventana, hacer clic en nada, etc.

---

### **MainWindow - _perform_scan()**

```python
def _perform_scan(self):
    """Realiza el escaneo (EN HILO SEPARADO)."""
    
    try:
        # PASO 1: Obtener duración desde config
        duration = self.config.get('scan_duration', 8)
        
        # PASO 2: Escanear dispositivos (tarda ~8 segundos)
        devices = self.bt_manager.scan_devices(duration=duration)
        
        # PASO 3: Actualizar UI de forma SEGURA
        # ⚠️ IMPORTANTE: NO modificar UI directamente desde este hilo
        # Usar root.after() para hacerlo en el hilo principal
        self.root.after(0, self._update_devices_list, devices)
        
    except Exception as e:
        logger.error(f"Error durante escaneo: {e}")
        self.root.after(0, self._scan_error, str(e))
```

**¿Por qué `root.after()`?**

```python
# ❌ PELIGRO - Modificar UI desde otro hilo
def _perform_scan():
    devices = scan()
    self.label.configure(text="Listo")  # ¡CRASH!

# ✅ CORRECTO - Usar root.after()
def _perform_scan():
    devices = scan()
    self.root.after(0, self._safe_update, devices)

def _safe_update(devices):
    self.label.configure(text="Listo")  # Seguro ✓
```

`root.after(0, función, args)` dice:
- "Ejecuta esta función en el hilo principal"
- "Lo antes posible (0 milisegundos)"
- "Con estos argumentos"

---

### **MainWindow - _update_devices_list()**

```python
def _update_devices_list(self, devices):
    """Actualiza la lista de dispositivos en UI."""
    
    self.devices_list = devices
    
    # PASO 1: Limpiar widgets anteriores
    self.clear_device_list()
    
    if not devices:
        # CASO 1: No se encontraron dispositivos
        self.no_devices_label.pack(pady=50)
        self.scan_status_label.configure(
            text="No se encontraron dispositivos",
            text_color="red"
        )
    else:
        # CASO 2: Dispositivos encontrados
        self.no_devices_label.pack_forget()
        
        # PASO 2: Crear widget por cada dispositivo
        for idx, device in enumerate(devices):
            self._create_device_widget(device, idx)
        
        # PASO 3: Actualizar contador
        self.scan_status_label.configure(
            text=f"✓ Se encontraron {len(devices)} dispositivo(s)",
            text_color="green"
        )
    
    # PASO 4: Rehabilitar botón
    self.scan_button.configure(
        state="normal",
        text="🔍 Escanear Dispositivos"
    )
```

---

### **MainWindow - _create_device_widget()**

```python
def _create_device_widget(self, device, index):
    """Crea un widget visual para un dispositivo."""
    
    # PASO 1: Frame contenedor
    device_frame = ctk.CTkFrame(
        self.devices_scrollable,
        corner_radius=10
    )
    device_frame.pack(fill="x", padx=10, pady=5)
    
    # PASO 2: Frame de información
    info_frame = ctk.CTkFrame(device_frame, fg_color="transparent")
    info_frame.pack(side="left", fill="both", expand=True, padx=10, pady=10)
    
    # PASO 3: Label con nombre
    name_label = ctk.CTkLabel(
        info_frame,
        text=f"📱 {device['name']}",
        font=("Arial", 14, "bold"),
        anchor="w"
    )
    name_label.pack(anchor="w")
    
    # PASO 4: Label con dirección MAC
    address_label = ctk.CTkLabel(
        info_frame,
        text=f"MAC: {device['address']}",
        font=("Courier", 11),
        text_color="gray",
        anchor="w"
    )
    address_label.pack(anchor="w")
    
    # PASO 5: Botón de selección
    select_button = ctk.CTkButton(
        device_frame,
        text="Seleccionar",
        command=lambda d=device: self.select_device(d),
        width=120
    )
    select_button.pack(side="right", padx=10)
```

**Visual resultante:**

```
┌────────────────────────────────────────┐
│ 📱 Mi Headset                          │
│ MAC: 00:11:22:33:44:55                 │
│                        [Seleccionar]   │
└────────────────────────────────────────┘
```

**Nota importante sobre lambda:**

```python
# ❌ INCORRECTO
command=self.select_device(device)
# Esto EJECUTA la función inmediatamente

# ✅ CORRECTO
command=lambda d=device: self.select_device(d)
# Esto GUARDA la función para ejecutar después
```

---

## 🔄 Flujo Completo Detallado

### Escenario: Usuario conecta a un Arduino Bluetooth

```
PASO 1: Usuario abre la aplicación
    ↓
main.py crea BluetoothApp
    ↓
BluetoothApp.__init__():
    - Carga config.json
    - Crea BluetoothManager
    - Crea DataHandler
    - Crea MainWindow (UI)
    - Conecta callbacks
    ↓
Se muestra ventana principal

PASO 2: Usuario hace clic en "Escanear"
    ↓
start_scan() se ejecuta:
    - Deshabilita botón
    - Limpia lista anterior
    - Crea Thread → _perform_scan()
    ↓
_perform_scan() (en thread separado):
    - Llama bluetooth_manager.scan_devices(8)
    - PyBluez escanea durante 8 segundos
    - Encuentra: [Arduino BT, Headset BT, Teclado BT]
    - Usa root.after() → _update_devices_list(dispositivos)
    ↓
_update_devices_list() (en thread principal):
    - Por cada dispositivo:
        * Crea frame visual
        * Muestra nombre y MAC
        * Crea botón "Seleccionar"
    - Habilita botón de escaneo

PASO 3: Usuario hace clic en "Seleccionar" del Arduino
    ↓
select_device(arduino_device):
    - Guarda en self.selected_device
    - Actualiza label: "✓ Arduino BT seleccionado"
    - Habilita botón "Conectar"

PASO 4: Usuario hace clic en "Conectar"
    ↓
connect_to_device():
    - Deshabilita botones
    - Cambia estado a "Conectando..."
    - Crea Thread → _perform_connection()
    ↓
_perform_connection() (en thread separado):
    - Llama bluetooth_manager.connect("AA:BB:CC:DD:EE:FF")
    - BluetoothManager.connect():
        * Crea socket Bluetooth
        * socket.connect((address, 1))
        * Inicia Thread → _receive_loop()
    - Usa root.after() → _connection_result(True)
    ↓
_connection_result(True):
    - Actualiza estado: "● Conectado" (verde)
    - Habilita botón "Desconectar"
    - Muestra mensaje de éxito

PASO 5: Arduino envía datos "Temp:25.3"
    ↓
_receive_loop() (en thread de recepción):
    - data = socket.recv(1024)  # Bloquea hasta recibir
    - Recibe: b'Temp:25.3'
    - Llama data_callback(b'Temp:25.3')
    ↓
_on_data_received(b'Temp:25.3'):
    - Llama data_handler.process(b'Temp:25.3')
    - Retorna:
        {
            'timestamp': 2024-02-06 12:30:45,
            'text': 'Temp:25.3',
            'hex': '54 65 6D 70 3A 32 35 2E 33'
        }
    - Llama ui.update_data_display(datos)
    ↓
update_data_display():
    - Formatea: "[12:30:45] Temp:25.3"
    - Inserta en textbox
    - Auto-scroll al final

PASO 6: Usuario cierra aplicación
    ↓
on_closing():
    - Pregunta si desconectar
    - bluetooth_manager.disconnect():
        * self.running = False
        * Espera que thread termine
        * Cierra socket
    - root.destroy()
```

---

## 💡 Conceptos Clave para Entender

### 1. **Callbacks (Funciones de Retorno)**

```python
# Configurar callback
bluetooth_manager.set_data_callback(self._on_data_received)

# Cuando llegan datos, BluetoothManager llama:
self.data_callback(data)

# Que ejecuta:
self._on_data_received(data)
```

**¿Por qué usar callbacks?**
- Desacoplar componentes
- BluetoothManager no necesita saber cómo mostrar datos
- MainWindow no necesita saber cómo recibir datos

### 2. **Threading Safety**

```python
# ⚠️ Regla de oro con Tkinter:
# SOLO el hilo principal puede modificar la UI

# ❌ NUNCA hacer esto desde otro hilo:
def worker_thread():
    label.configure(text="Hola")  # ¡CRASH!

# ✅ SIEMPRE usar root.after():
def worker_thread():
    root.after(0, lambda: label.configure(text="Hola"))
```

### 3. **Sockets Bloqueantes**

```python
# socket.recv() es BLOQUEANTE
data = socket.recv(1024)  # ⏸️ Se queda aquí hasta recibir datos

# Por eso debe estar en su propio thread
def receive_loop():
    while running:
        data = socket.recv(1024)  # Bloquea solo este thread
        process(data)
```

---

## 🎓 Ejercicios para Practicar

### Ejercicio 1: Agregar Filtro de Dispositivos
Modifica `_update_devices_list()` para filtrar solo dispositivos con "Arduino" en el nombre.

### Ejercicio 2: Cambiar Puerto RFCOMM
Agrega un campo de entrada para que el usuario pueda especificar el puerto (1-30).

### Ejercicio 3: Exportar Historial
Implementa un botón para guardar todos los datos recibidos en un archivo .txt.

### Ejercicio 4: Enviar Comandos
Agrega un campo de texto y botón para enviar comandos al dispositivo conectado.

---

## 📊 Diagrama de Arquitectura Completo

```
┌───────────────────────────────────────────────────────────┐
│                        main.py                            │
│                    (BluetoothApp)                         │
│                                                           │
│  ┌──────────────────────────────────────────────────┐   │
│  │ __init__():                                       │   │
│  │   - Carga Config                                  │   │
│  │   - Crea BluetoothManager                        │   │
│  │   - Crea DataHandler                             │   │
│  │   - Crea MainWindow                              │   │
│  │   - Conecta callbacks                            │   │
│  └──────────────────────────────────────────────────┘   │
│                                                           │
│  ┌──────────────────────────────────────────────────┐   │
│  │ Callbacks:                                        │   │
│  │   _on_data_received(raw_data)                    │   │
│  │   _on_connection_change(status)                  │   │
│  └──────────────────────────────────────────────────┘   │
└───────────────────────────────────────────────────────────┘
                         │
          ┌──────────────┼──────────────┬──────────────┐
          ▼              ▼              ▼              ▼
    ┌──────────┐  ┌──────────────┐  ┌────────────┐  ┌─────────┐
    │  Config  │  │  Bluetooth   │  │    Data    │  │   UI    │
    │          │  │   Manager    │  │  Handler   │  │ Window  │
    └──────────┘  └──────────────┘  └────────────┘  └─────────┘
                        │                                  │
                        ▼                                  ▼
                  ┌──────────┐                      ┌──────────┐
                  │ PyBluez  │                      │CustomTk  │
                  │  Socket  │                      │ Widgets  │
                  └──────────┘                      └──────────┘
                        │
                        ▼
                ┌──────────────┐
                │ Dispositivo  │
                │  Bluetooth   │
                └──────────────┘
```

---

**¡Felicidades! Ahora entiendes a fondo cómo funciona cada parte del código.** 🎉
