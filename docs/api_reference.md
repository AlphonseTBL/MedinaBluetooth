# Referencia de API - Monitor Bluetooth

Esta documentación proporciona detalles técnicos sobre las clases y métodos principales de la aplicación para desarrolladores que deseen extender o modificar el código.

## Módulo: bluetooth_manager.py

### Clase: BluetoothManager

Gestiona todas las operaciones relacionadas con la comunicación Bluetooth.

#### Constructor

```python
BluetoothManager()
```

Inicializa el gestor de Bluetooth sin parámetros. Prepara las estructuras internas para manejar conexiones.

#### Métodos Públicos

##### scan_devices()

```python
scan_devices(duration: int = 8) -> List[Dict[str, str]]
```

Escanea dispositivos Bluetooth cercanos durante un tiempo especificado.

**Parámetros:**
- `duration` (int): Tiempo de escaneo en segundos. Por defecto 8 segundos.

**Retorna:**
- Lista de diccionarios, cada uno con las claves:
  - `'address'` (str): Dirección MAC del dispositivo
  - `'name'` (str): Nombre del dispositivo o 'Desconocido'

**Ejemplo:**
```python
bt = BluetoothManager()
devices = bt.scan_devices(duration=10)
for device in devices:
    print(f"{device['name']}: {device['address']}")
```

##### connect()

```python
connect(device_address: str, port: int = 1) -> bool
```

Establece una conexión con un dispositivo Bluetooth específico.

**Parámetros:**
- `device_address` (str): Dirección MAC del dispositivo (formato: "XX:XX:XX:XX:XX:XX")
- `port` (int): Puerto RFCOMM para la conexión. Por defecto 1 (protocolo SPP estándar)

**Retorna:**
- `True` si la conexión fue exitosa
- `False` si falló la conexión

**Efectos secundarios:**
- Inicia un thread de recepción de datos
- Llama al callback de conexión si está configurado
- Establece `self.connected = True`

**Ejemplo:**
```python
success = bt.connect("00:11:22:33:44:55", port=1)
if success:
    print("Conexión establecida")
```

##### disconnect()

```python
disconnect() -> None
```

Cierra la conexión actual con el dispositivo Bluetooth de forma segura.

**Efectos secundarios:**
- Detiene el thread de recepción
- Cierra el socket Bluetooth
- Llama al callback de conexión indicando desconexión
- Establece `self.connected = False`

##### send_data()

```python
send_data(data: str) -> bool
```

Envía datos de texto al dispositivo Bluetooth conectado.

**Parámetros:**
- `data` (str): Cadena de texto a enviar

**Retorna:**
- `True` si el envío fue exitoso
- `False` si falló o no hay conexión activa

**Nota:** Este método codifica automáticamente el string a bytes antes de enviar.

##### set_data_callback()

```python
set_data_callback(callback: Callable) -> None
```

Configura una función que será llamada cada vez que se reciban datos.

**Parámetros:**
- `callback` (Callable): Función que acepta un parámetro de tipo `bytes`

**Ejemplo:**
```python
def on_data_received(raw_data):
    print(f"Datos recibidos: {raw_data}")

bt.set_data_callback(on_data_received)
```

##### set_connection_callback()

```python
set_connection_callback(callback: Callable) -> None
```

Configura una función que será llamada cuando cambie el estado de conexión.

**Parámetros:**
- `callback` (Callable): Función que acepta dos parámetros:
  - `connected` (bool): Estado de la conexión
  - `device_info` (dict o None): Información del dispositivo si está conectado

**Ejemplo:**
```python
def on_connection_change(connected, device_info):
    if connected:
        print(f"Conectado a {device_info['name']}")
    else:
        print("Desconectado")

bt.set_connection_callback(on_connection_change)
```

##### is_connected()

```python
is_connected() -> bool
```

Verifica si hay una conexión activa.

**Retorna:**
- `True` si hay una conexión establecida
- `False` en caso contrario

##### get_device_info()

```python
get_device_info() -> Optional[Dict[str, str]]
```

Obtiene información del dispositivo actualmente conectado.

**Retorna:**
- Diccionario con claves `'address'` y `'name'` si hay conexión
- `None` si no hay dispositivo conectado

---

## Módulo: data_handler.py

### Clase: DataHandler

Procesa y estructura los datos crudos recibidos del dispositivo Bluetooth.

#### Constructor

```python
DataHandler(buffer_size: int = 100)
```

**Parámetros:**
- `buffer_size` (int): Número máximo de lecturas a mantener en el historial. Por defecto 100.

#### Métodos Públicos

##### process()

```python
process(raw_data: bytes, format_type: str = 'text') -> Dict[str, Any]
```

Procesa los datos crudos y retorna un diccionario estructurado.

**Parámetros:**
- `raw_data` (bytes): Datos recibidos del dispositivo
- `format_type` (str): Tipo de formato. Opciones: 'text', 'json', 'binary', 'custom'

**Retorna:**
- Diccionario con las claves:
  - `'timestamp'` (datetime): Momento de recepción
  - `'message_number'` (int): Número secuencial del mensaje
  - `'data'` (dict): Datos procesados y estructurados
  - `'raw_bytes'` (bytes): Datos originales para debugging

**Ejemplo:**
```python
handler = DataHandler()
result = handler.process(b"temperatura:25.5,humedad:60.2", format_type='text')
print(result['data'])  # {'temperatura': 25.5, 'humedad': 60.2}
```

##### get_history()

```python
get_history(n: int = None) -> List[Dict[str, Any]]
```

Recupera el historial de datos procesados.

**Parámetros:**
- `n` (int, opcional): Número de elementos a retornar. None retorna todos.

**Retorna:**
- Lista de diccionarios con datos procesados

##### get_last_value()

```python
get_last_value() -> Any
```

Obtiene el último valor procesado sin metadatos.

**Retorna:**
- Diccionario con los últimos datos procesados
- None si no hay datos aún

##### clear_history()

```python
clear_history() -> None
```

Limpia el historial de datos almacenados y reinicia el contador de mensajes.

##### export_to_csv()

```python
export_to_csv(filename: str = 'bluetooth_data.csv') -> bool
```

Exporta todo el historial de datos a un archivo CSV.

**Parámetros:**
- `filename` (str): Nombre del archivo de salida

**Retorna:**
- `True` si la exportación fue exitosa
- `False` si hubo un error

**Formato del CSV:**
- Primera fila: encabezados (timestamp, message_number, campos de datos)
- Filas subsiguientes: valores correspondientes

#### Métodos Privados (Personalizables)

##### _process_text()

```python
_process_text(raw_data: bytes) -> Dict[str, Any]
```

Procesa datos en formato de texto plano. Este es el método principal para personalizar si tus datos son texto simple.

**Formato esperado por defecto:**
```
clave1:valor1,clave2:valor2,clave3:valor3
```

**Modifica este método** para adaptarlo a tu formato específico de texto.

##### _process_json()

```python
_process_json(raw_data: bytes) -> Dict[str, Any]
```

Procesa datos en formato JSON. Usa este método si tu dispositivo envía JSON válido.

##### _process_binary()

```python
_process_binary(raw_data: bytes) -> Dict[str, Any]
```

Procesa datos en formato binario. **Personaliza este método** según el protocolo binario de tu dispositivo.

##### _process_custom()

```python
_process_custom(raw_data: bytes) -> Dict[str, Any]
```

Implementa lógica personalizada para formatos únicos. Este es el lugar ideal para protocolos propietarios o formatos especiales.

---

## Módulo: config.py

### Clase: Config

Gestiona la configuración de la aplicación mediante archivo JSON.

#### Constructor

```python
Config(config_file='config.json')
```

**Parámetros:**
- `config_file` (str): Ruta al archivo de configuración. Por defecto 'config.json'

#### Métodos Públicos

##### get()

```python
get(key: str, default=None) -> Any
```

Obtiene un valor de configuración.

**Parámetros:**
- `key` (str): Nombre del parámetro de configuración
- `default` (Any): Valor por defecto si la clave no existe

**Retorna:**
- Valor de configuración o el valor por defecto

##### set()

```python
set(key: str, value: Any) -> None
```

Establece un valor de configuración (solo en memoria).

**Parámetros:**
- `key` (str): Nombre del parámetro
- `value` (Any): Nuevo valor

**Nota:** Para persistir los cambios, debes llamar a `save_config()`

##### save_config()

```python
save_config() -> bool
```

Guarda la configuración actual en el archivo JSON.

**Retorna:**
- `True` si se guardó exitosamente
- `False` si hubo un error

##### create_default_config_file()

```python
create_default_config_file() -> None
```

Crea un archivo de configuración con valores por defecto si no existe.

---

## Módulo: ui/main_window.py

### Clase: MainWindow

Ventana principal de la interfaz gráfica construida con CustomTkinter.

#### Constructor

```python
MainWindow(bluetooth_manager, data_handler, config)
```

**Parámetros:**
- `bluetooth_manager` (BluetoothManager): Instancia del gestor Bluetooth
- `data_handler` (DataHandler): Instancia del procesador de datos
- `config` (Config): Configuración de la aplicación

#### Métodos Públicos

##### update_data_display()

```python
update_data_display(processed_data: Dict[str, Any]) -> None
```

Actualiza la visualización con nuevos datos recibidos.

**Parámetros:**
- `processed_data` (dict): Datos procesados retornados por DataHandler.process()

Este método es típicamente llamado automáticamente por los callbacks.

##### update_connection_status()

```python
update_connection_status(connected: bool, device_info: Dict = None) -> None
```

Actualiza la UI para reflejar el estado de la conexión.

**Parámetros:**
- `connected` (bool): True si está conectado
- `device_info` (dict, opcional): Información del dispositivo conectado

##### show_error()

```python
show_error(message: str) -> None
```

Muestra un cuadro de diálogo de error al usuario.

**Parámetros:**
- `message` (str): Mensaje de error a mostrar

##### run()

```python
run() -> None
```

Inicia el loop principal de la interfaz gráfica. Este método es bloqueante y debe ser llamado al final de la inicialización.

---

## Flujo de Trabajo Típico

Este es el flujo de trabajo normal de la aplicación desde el punto de vista del código:

1. **Inicialización** (main.py)
   ```python
   app = BluetoothApp()
   ```
   - Se crea Config, BluetoothManager, DataHandler y MainWindow
   - Se configuran los callbacks entre componentes

2. **Usuario escanea dispositivos**
   ```python
   devices = bluetooth_manager.scan_devices()
   ```

3. **Usuario se conecta**
   ```python
   bluetooth_manager.connect(device_address)
   ```
   - Se inicia thread de recepción
   - Se llama al callback de conexión

4. **Recepción de datos** (en thread separado)
   ```python
   # En _receive_loop():
   raw_data = socket.recv(1024)
   data_callback(raw_data)  # Notifica a la app
   ```

5. **Procesamiento de datos** (callback en main.py)
   ```python
   def _on_data_received(raw_data):
       processed = data_handler.process(raw_data)
       ui.update_data_display(processed)
   ```

6. **Actualización de UI**
   ```python
   # En MainWindow:
   data_display.insert("end", formatted_text)
   ```

7. **Desconexión**
   ```python
   bluetooth_manager.disconnect()
   ```
   - Detiene el thread de recepción
   - Cierra el socket
   - Llama al callback de desconexión

---

## Extendiendo la Aplicación

### Agregar un nuevo formato de datos

Para agregar soporte para un nuevo formato:

1. Agrega el formato a la lista en Config.DEFAULTS
2. Crea un método `_process_tu_formato()` en DataHandler
3. Modifica el método `process()` para incluir tu formato en el if/elif

Ejemplo:
```python
# En data_handler.py
def _process_xml(self, raw_data: bytes) -> Dict[str, Any]:
    import xml.etree.ElementTree as ET
    tree = ET.fromstring(raw_data.decode('utf-8'))
    # Tu lógica de parseo XML
    return data_dict

# En process():
elif format_type == 'xml':
    processed = self._process_xml(raw_data)
```

### Agregar visualizaciones personalizadas

Para agregar gráficos o visualizaciones:

1. Importa la biblioteca necesaria (matplotlib, plotly, etc.)
2. Crea un nuevo frame en MainWindow
3. Actualiza la visualización en `update_data_display()`

Ejemplo con matplotlib:
```python
# En main_window.py
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

def _create_graph_panel(self):
    self.fig, self.ax = plt.subplots()
    self.canvas = FigureCanvasTkAgg(self.fig, self.graph_frame)
    self.canvas.get_tk_widget().pack()

def update_data_display(self, processed_data):
    # Actualizar texto como antes...
    # Luego actualizar gráfico:
    self.update_graph(processed_data)

def update_graph(self, data):
    # Lógica para graficar
    self.ax.plot(x_data, y_data)
    self.canvas.draw()
```

---

## Notas de Implementación

### Threading

La aplicación usa threading para mantener la UI responsiva durante la recepción de datos. El thread de recepción corre en modo daemon para que se cierre automáticamente cuando la aplicación termina.

### Manejo de Errores

Todos los métodos principales incluyen manejo de excepciones y logging. Los errores se registran en `bluetooth_app.log` y, cuando es apropiado, se muestran al usuario mediante cuadros de diálogo.

### Codificación

Por defecto, la aplicación asume UTF-8 para la decodificación de datos de texto. Esto se puede cambiar en el archivo de configuración.

### Compatibilidad

La aplicación ha sido diseñada para ser compatible con Python 3.8+. Las dependencias principales son CustomTkinter y PyBluez.

---

Esta referencia proporciona una base sólida para desarrolladores que deseen extender o modificar la aplicación. Para preguntas específicas o contribuciones, consulta el README principal del proyecto.
