# 🔵 Aplicación Bluetooth con Selector de Dispositivos

Aplicación de escritorio para escanear, seleccionar y conectarse a dispositivos Bluetooth cercanos.

## 📋 Características

✅ **Escaneo de dispositivos Bluetooth** - Busca automáticamente dispositivos cercanos
✅ **Selector visual de dispositivos** - Interfaz intuitiva para elegir el dispositivo
✅ **Conexión RFCOMM** - Conexión estable a dispositivos Bluetooth
✅ **Recepción de datos en tiempo real** - Visualiza datos recibidos instantáneamente
✅ **Historial de datos** - Mantiene registro de información recibida
✅ **Interfaz moderna** - Diseñada con CustomTkinter

## 🛠️ Requisitos Previos

### Windows
1. Python 3.8 o superior
2. Microsoft Visual C++ 14.0 o superior
3. Adaptador Bluetooth habilitado

### Linux
1. Python 3.8 o superior
2. BlueZ (viene preinstalado en la mayoría de distribuciones)
```bash
sudo apt-get install libbluetooth-dev
```

### macOS
1. Python 3.8 o superior
2. Xcode Command Line Tools
```bash
xcode-select --install
```

## 📦 Instalación

### Paso 1: Clonar o descargar el proyecto
```bash
git clone <url-de-tu-repositorio>
cd bluetooth-app
```

### Paso 2: Crear entorno virtual (recomendado)
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/macOS
python3 -m venv venv
source venv/bin/activate
```

### Paso 3: Instalar dependencias
```bash
pip install -r requirements.txt
```

### Paso 4: Ejecutar la aplicación
```bash
python main.py
```

## 📁 Estructura del Proyecto

```
bluetooth-app/
│
├── main.py                      # Punto de entrada de la aplicación
├── requirements.txt             # Dependencias del proyecto
├── config.json                  # Configuración (se crea automáticamente)
├── bluetooth_app.log           # Archivo de logs
│
└── src/
    ├── __init__.py
    ├── config.py               # Gestión de configuración
    ├── bluetooth_manager.py    # Gestión de Bluetooth
    ├── data_handler.py         # Procesamiento de datos
    │
    └── ui/
        ├── __init__.py
        └── main_window.py      # Interfaz gráfica principal
```

## 🎯 Cómo Usar la Aplicación

### 1. Escanear Dispositivos
- Presiona el botón **"🔍 Escanear Dispositivos"**
- La aplicación buscará dispositivos Bluetooth cercanos (tarda ~8 segundos)
- Los dispositivos encontrados aparecerán en una lista

### 2. Seleccionar un Dispositivo
- Haz clic en el botón **"Seleccionar"** del dispositivo deseado
- El dispositivo seleccionado se mostrará en la parte inferior

### 3. Conectar al Dispositivo
- Presiona el botón **"📡 Conectar"**
- Espera a que la conexión se establezca
- El estado cambiará a "● Conectado" en verde

### 4. Ver Datos Recibidos
- Los datos recibidos aparecerán automáticamente en el área inferior
- Se muestra el timestamp, texto y representación hexadecimal
- Puedes limpiar los datos con el botón **"🗑️ Limpiar Datos"**

### 5. Desconectar
- Presiona el botón **"❌ Desconectar"**
- O simplemente cierra la aplicación

## 🔧 Explicación Técnica del Código

### Arquitectura del Proyecto

La aplicación sigue el patrón **MVC (Modelo-Vista-Controlador)** adaptado:

```
┌─────────────────┐
│   main.py       │ ← Controlador Principal (BluetoothApp)
│  (Controller)   │
└────────┬────────┘
         │
    ┌────┴─────┬──────────────┬─────────────┐
    ▼          ▼              ▼             ▼
┌────────┐ ┌─────────┐ ┌──────────┐ ┌──────────┐
│ Config │ │Bluetooth│ │   Data   │ │    UI    │
│        │ │ Manager │ │ Handler  │ │ (Vista)  │
└────────┘ └─────────┘ └──────────┘ └──────────┘
```

### Componentes Principales

#### 1. **main.py - BluetoothApp (Coordinador Principal)**

**¿Qué hace?**
- Inicializa todos los componentes
- Conecta los diferentes módulos mediante callbacks
- Coordina el flujo de datos entre componentes

**Flujo de trabajo:**
```python
BluetoothApp.__init__()
    ↓
Crear Config, BluetoothManager, DataHandler, MainWindow
    ↓
Configurar callbacks (cuando lleguen datos, llamar a _on_data_received)
    ↓
Iniciar interfaz gráfica
```

**Callbacks importantes:**
- `_on_data_received`: Se ejecuta cuando llegan datos Bluetooth
- `_on_connection_change`: Se ejecuta cuando cambia el estado de conexión

#### 2. **bluetooth_manager.py - Gestión de Bluetooth**

**Métodos clave:**

**a) `scan_devices(duration=8)`**
```python
# ¿Qué hace?
# Escanea dispositivos Bluetooth cercanos durante X segundos

# Proceso paso a paso:
1. Llama a bluetooth.discover_devices() de PyBluez
2. Obtiene nombre y dirección MAC de cada dispositivo
3. Retorna lista de diccionarios: [{'name': '...', 'address': '...'}]

# Ejemplo de resultado:
[
    {'name': 'Mi Headset', 'address': '00:11:22:33:44:55'},
    {'name': 'Arduino BT', 'address': 'AA:BB:CC:DD:EE:FF'}
]
```

**b) `connect(device_address, port=1)`**
```python
# ¿Qué hace?
# Conecta a un dispositivo específico usando su dirección MAC

# Proceso paso a paso:
1. Crea un socket Bluetooth tipo RFCOMM
2. Intenta conectar a la dirección MAC en el puerto especificado
3. Si tiene éxito, inicia un hilo para recibir datos
4. Retorna True/False según el resultado

# RFCOMM = Radio Frequency Communication
# Es como abrir un "canal de comunicación" con el dispositivo
```

**c) `_receive_loop()`**
```python
# ¿Qué hace?
# Loop infinito que recibe datos del dispositivo

# Proceso paso a paso:
1. Se ejecuta en un hilo separado (no bloquea la UI)
2. Constantemente espera datos del socket (hasta 1024 bytes)
3. Cuando llegan datos, llama al callback configurado
4. Si hay error o desconexión, sale del loop

# ¿Por qué en un hilo separado?
# Porque socket.recv() es BLOQUEANTE
# Si se ejecutara en el hilo principal, congelaría la interfaz
```

#### 3. **data_handler.py - Procesamiento de Datos**

**¿Qué hace?**
```python
# Transforma datos crudos en información útil

# Input (raw_data):  b'Hello\n'
# Output (processed):
{
    'timestamp': datetime.now(),
    'raw': b'Hello\n',
    'text': 'Hello\n',
    'length': 6,
    'hex': '48 65 6C 6C 6F 0A'
}
```

**Métodos importantes:**
- `process(raw_data)`: Convierte bytes a texto y hexadecimal
- `get_history()`: Obtiene historial de datos recibidos
- `_to_hex()`: Convierte a representación hexadecimal

#### 4. **main_window.py - Interfaz Gráfica**

**Estructura visual:**
```
┌────────────────────────────────────────┐
│  🔵 Gestor de Dispositivos Bluetooth   │
│  [🔍 Escanear Dispositivos]            │
│  Estado: Listo para escanear           │
├────────────────────────────────────────┤
│  Dispositivos Encontrados:             │
│  ┌──────────────────────────────────┐  │
│  │ 📱 Mi Headset                    │  │
│  │ MAC: 00:11:22:33:44:55           │  │
│  │                    [Seleccionar] │  │
│  ├──────────────────────────────────┤  │
│  │ 📱 Arduino BT                    │  │
│  │ MAC: AA:BB:CC:DD:EE:FF           │  │
│  │                    [Seleccionar] │  │
│  └──────────────────────────────────┘  │
├────────────────────────────────────────┤
│  ✓ Dispositivo: Mi Headset             │
│  [📡 Conectar] [❌ Desconectar]        │
│  ● Conectado                           │
├────────────────────────────────────────┤
│  Datos Recibidos:                      │
│  ┌──────────────────────────────────┐  │
│  │ [12:30:45] Temperatura: 25.3°C   │  │
│  │   HEX: 54 65 6D 70 ...           │  │
│  └──────────────────────────────────┘  │
│  [🗑️ Limpiar Datos]                   │
└────────────────────────────────────────┘
```

**Métodos clave:**

**a) `start_scan()`**
```python
# ¿Qué hace?
# Inicia el proceso de escaneo

# Flujo:
1. Deshabilita botón de escaneo (evitar múltiples escaneos)
2. Limpia lista de dispositivos anterior
3. Crea un THREAD para _perform_scan()
   (Para no congelar la interfaz durante 8 segundos)
```

**b) `_perform_scan()` (en hilo separado)**
```python
# ¿Qué hace?
# Ejecuta el escaneo real

# Flujo:
1. Llama a bluetooth_manager.scan_devices()
2. Espera ~8 segundos (PyBluez escaneando)
3. Cuando termina, usa self.root.after() para actualizar UI
   (IMPORTANTE: Tkinter NO es thread-safe, 
    solo el hilo principal puede modificar la UI)
```

**c) `_update_devices_list(devices)`**
```python
# ¿Qué hace?
# Actualiza la UI con dispositivos encontrados

# Flujo:
1. Limpia widgets anteriores
2. Por cada dispositivo, crea un frame con:
   - Nombre del dispositivo
   - Dirección MAC
   - Botón "Seleccionar"
3. Actualiza contador de dispositivos
```

**d) `select_device(device)`**
```python
# ¿Qué hace?
# Marca un dispositivo como seleccionado

# Flujo:
1. Guarda dispositivo en self.selected_device
2. Actualiza label mostrando cuál está seleccionado
3. Habilita botón de conexión
```

**e) `connect_to_device()`**
```python
# ¿Qué hace?
# Conecta al dispositivo seleccionado

# Flujo:
1. Verifica que haya un dispositivo seleccionado
2. Deshabilita botones (evitar doble clic)
3. Crea THREAD para _perform_connection()
   (Conexión puede tardar, no bloquear UI)
```

**f) `_perform_connection()` (en hilo separado)**
```python
# ¿Qué hace?
# Realiza la conexión Bluetooth

# Flujo:
1. Llama a bluetooth_manager.connect(dirección_MAC)
2. Espera resultado (puede tardar varios segundos)
3. Usa self.root.after() para actualizar UI con resultado
```

### 🔄 Flujo Completo de la Aplicación

#### Escenario: Usuario escanea y conecta a un dispositivo

```
1. USUARIO presiona "Escanear"
   ↓
2. start_scan() crea THREAD → _perform_scan()
   ↓
3. _perform_scan() llama bluetooth_manager.scan_devices()
   ↓
4. PyBluez escanea durante 8 segundos
   ↓
5. Dispositivos encontrados retornan a _perform_scan()
   ↓
6. _perform_scan() usa root.after() → _update_devices_list()
   ↓
7. _update_devices_list() crea widgets en UI
   ↓
8. USUARIO hace clic en "Seleccionar" de un dispositivo
   ↓
9. select_device() guarda dispositivo y habilita "Conectar"
   ↓
10. USUARIO presiona "Conectar"
    ↓
11. connect_to_device() crea THREAD → _perform_connection()
    ↓
12. _perform_connection() llama bluetooth_manager.connect()
    ↓
13. BluetoothManager crea socket y conecta
    ↓
14. Si éxito, inicia THREAD → _receive_loop()
    ↓
15. _receive_loop() constantemente espera datos
    ↓
16. Cuando llegan datos, llama callback → _on_data_received()
    ↓
17. _on_data_received() procesa datos → data_handler.process()
    ↓
18. Datos procesados se envían a UI → update_data_display()
    ↓
19. UI muestra datos en tiempo real
```

### 🧵 Threading: ¿Por qué usamos hilos?

**Problema sin hilos:**
```python
# Sin threading
scan_button.configure(state="disabled")
devices = bluetooth.discover_devices(duration=8)  # ← UI CONGELADA 8 segundos
update_list(devices)
```

**Solución con hilos:**
```python
# Con threading
scan_button.configure(state="disabled")
thread = Thread(target=perform_scan)  # ← UI sigue respondiendo
thread.start()

def perform_scan():
    devices = bluetooth.discover_devices(duration=8)  # En segundo plano
    root.after(0, update_list, devices)  # Actualizar UI de forma segura
```

### ⚠️ Consideraciones Importantes

#### 1. **Thread Safety en Tkinter**
```python
# ❌ INCORRECTO - Modificar UI desde otro hilo
def scan_thread():
    devices = scan()
    label.configure(text="Listo")  # ¡PELIGRO! Puede causar crashes

# ✅ CORRECTO - Usar root.after()
def scan_thread():
    devices = scan()
    root.after(0, lambda: label.configure(text="Listo"))
```

#### 2. **Puerto RFCOMM**
```python
# Puerto 1 es el más común para SPP (Serial Port Profile)
# Algunos dispositivos usan otros puertos (2, 3, etc.)
# Puedes obtener servicios con:
services = bluetooth.find_service(address=device_address)
```

#### 3. **Permisos en Linux**
```bash
# Si obtienes errores de permisos:
sudo usermod -a -G bluetooth $USER
# Luego cerrar sesión y volver a entrar
```

## 🐛 Solución de Problemas Comunes

### Error: "No se encontraron dispositivos"
- Verifica que Bluetooth esté encendido
- Asegúrate de que el dispositivo sea visible/emparejable
- Aumenta la duración del escaneo en config.json

### Error: "No se puede conectar"
- Verifica que el dispositivo acepte conexiones
- Intenta con diferentes puertos (1-30)
- Algunos dispositivos requieren emparejamiento previo

### Error: "bluetooth module not found"
- En Windows: Instala Visual C++ Build Tools
- En Linux: `sudo apt-get install libbluetooth-dev`
- Reinstala: `pip uninstall pybluez && pip install pybluez`

## 📝 Personalización

### Cambiar duración del escaneo
Edita `config.json`:
```json
{
    "scan_duration": 10
}
```

### Cambiar tema
Edita `config.json`:
```json
{
    "appearance_mode": "light",
    "color_theme": "green"
}
```

## 📚 Recursos Adicionales

- [Documentación PyBluez](https://github.com/pybluez/pybluez)
- [Documentación CustomTkinter](https://customtkinter.tomschimansky.com/)
- [Tutorial Bluetooth Python](https://people.csail.mit.edu/albert/bluez-intro/)

## 🤝 Contribuciones

¡Las contribuciones son bienvenidas! Por favor:
1. Fork el proyecto
2. Crea una rama para tu feature
3. Commit tus cambios
4. Push a la rama
5. Abre un Pull Request

## 📄 Licencia

Este proyecto es de código abierto y está disponible bajo la licencia MIT.

---

**Creado con ❤️ para el aprendizaje de desarrollo de software**
