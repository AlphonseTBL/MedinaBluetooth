# Arquitectura del Proyecto - Monitor Bluetooth

## Visión General

Este documento describe la arquitectura de la aplicación Monitor Bluetooth, explicando cómo se organizan y comunican los diferentes componentes.

## Arquitectura en Capas

La aplicación sigue una arquitectura en capas que separa las responsabilidades en tres niveles principales:

```
┌─────────────────────────────────────────────────┐
│         Capa de Presentación (UI)               │
│              CustomTkinter                       │
│          (main_window.py)                        │
└──────────────────┬──────────────────────────────┘
                   │
                   │ Callbacks y eventos
                   │
┌──────────────────▼──────────────────────────────┐
│         Capa de Lógica de Negocio               │
│                                                  │
│  ┌──────────────┐      ┌──────────────┐        │
│  │ Bluetooth    │      │ Data         │        │
│  │ Manager      │─────▶│ Handler      │        │
│  └──────────────┘      └──────────────┘        │
│                                                  │
└──────────────────┬──────────────────────────────┘
                   │
                   │ Comunicación física
                   │
┌──────────────────▼──────────────────────────────┐
│         Capa de Comunicación                     │
│              PyBluez / Bluetooth                 │
│          (bluetooth_manager.py)                  │
└──────────────────────────────────────────────────┘
```

## Componentes Principales

### 1. main.py - Controlador Principal

El archivo `main.py` actúa como el orquestador central de la aplicación. Es responsable de:

- Inicializar todos los componentes del sistema
- Coordinar la comunicación entre componentes mediante callbacks
- Manejar el ciclo de vida de la aplicación
- Gestionar la configuración global y el logging

**Flujo de inicialización:**
```
BluetoothApp.__init__()
    ├─ Cargar Config
    ├─ Inicializar BluetoothManager
    ├─ Inicializar DataHandler
    ├─ Crear MainWindow
    └─ Configurar callbacks entre componentes
```

### 2. BluetoothManager - Gestor de Comunicaciones

Este componente encapsula toda la lógica relacionada con Bluetooth. Su diseño sigue el patrón Observer para notificar eventos a otros componentes.

**Responsabilidades:**
- Escaneo de dispositivos disponibles
- Establecimiento y cierre de conexiones
- Recepción continua de datos en un thread separado
- Notificación de eventos mediante callbacks

**Diseño de threading:**
```
Main Thread                     Background Thread
    │                                 │
    │ connect()                       │
    ├─────────────────────────────────▶
    │                                 │
    │                           _receive_loop()
    │                                 │
    │                           while connected:
    │                                 │
    │                           data = socket.recv()
    │                                 │
    │◀────────── callback ────────────┤
    │                                 │
```

El uso de un thread separado asegura que la interfaz gráfica permanezca responsiva mientras se reciben datos continuamente del dispositivo Bluetooth.

### 3. DataHandler - Procesador de Datos

El DataHandler transforma los datos crudos recibidos del Bluetooth en estructuras de datos utilizables. Este componente implementa el patrón Strategy, permitiendo diferentes algoritmos de procesamiento según el tipo de datos.

**Estrategias de procesamiento:**
- `_process_text()` - Para datos de texto plano con formato clave:valor
- `_process_json()` - Para datos en formato JSON
- `_process_binary()` - Para protocolos binarios personalizados
- `_process_custom()` - Para formatos únicos o propietarios

**Pipeline de procesamiento:**
```
Datos crudos (bytes)
    │
    ▼
Decodificación
    │
    ▼
Selección de estrategia
    │
    ├─ text   ──▶ _process_text()
    ├─ json   ──▶ _process_json()
    ├─ binary ──▶ _process_binary()
    └─ custom ──▶ _process_custom()
    │
    ▼
Datos estructurados (dict)
    │
    ▼
Agregar metadatos (timestamp, número de mensaje)
    │
    ▼
Guardar en historial
    │
    ▼
Retornar resultado
```

### 4. MainWindow - Interfaz Gráfica

La interfaz está construida con CustomTkinter y organizada en paneles independientes. Sigue el patrón Model-View-Presenter (MVP), donde actúa como la Vista.

**Estructura de la UI:**
```
┌────────────────────────────────────────────────────────┐
│  Ventana Principal (CTk)                               │
│                                                         │
│  ┌──────────────────┐  ┌─────────────────────────────┐│
│  │ Connection Panel │  │  Data Panel                 ││
│  │                  │  │                             ││
│  │ - Scan Button    │  │  - Data Display (TextBox)  ││
│  │ - Device List    │  │  - Clear/Export Buttons    ││
│  │ - Connect Button │  │                             ││
│  └──────────────────┘  └─────────────────────────────┘│
│                                                         │
│  ┌──────────────────────────────────────────────────┐ │
│  │  Status Bar                                       │ │
│  │  - Connection Status    - Message Counter        │ │
│  └──────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────┘
```

### 5. Config - Gestor de Configuración

El módulo Config proporciona acceso centralizado a la configuración de la aplicación, permitiendo que todos los componentes accedan a sus parámetros de manera consistente.

**Jerarquía de configuración:**
```
1. Valores por defecto (Config.DEFAULTS)
         │
         ▼
2. Archivo config.json (si existe)
         │
         ▼
3. Modificaciones en tiempo de ejecución
```

## Patrones de Diseño Utilizados

### 1. Observer (Patrón Observador)

El BluetoothManager implementa este patrón para notificar eventos:

```python
# BluetoothManager es el "Subject"
class BluetoothManager:
    def set_data_callback(self, callback):
        self.data_callback = callback
    
    def _receive_loop(self):
        data = socket.recv()
        self.data_callback(data)  # Notificar a observadores

# BluetoothApp es el "Observer"
class BluetoothApp:
    def __init__(self):
        self.bt_manager.set_data_callback(self._on_data_received)
    
    def _on_data_received(self, data):
        # Reaccionar al evento
```

### 2. Strategy (Patrón Estrategia)

DataHandler utiliza diferentes estrategias de procesamiento:

```python
def process(self, raw_data, format_type):
    # Selección dinámica de estrategia
    if format_type == 'text':
        return self._process_text(raw_data)
    elif format_type == 'json':
        return self._process_json(raw_data)
    # ... otras estrategias
```

### 3. Facade (Patrón Fachada)

BluetoothApp actúa como fachada, simplificando la interacción entre componentes complejos:

```python
class BluetoothApp:
    def __init__(self):
        # Coordina múltiples subsistemas
        self.bt_manager = BluetoothManager()
        self.data_handler = DataHandler()
        self.ui = MainWindow()
        self._setup_callbacks()  # Conecta todo
```

## Flujo de Datos Completo

Veamos el flujo completo desde que se reciben datos hasta que se muestran en la UI:

```
1. Dispositivo Bluetooth
    │ (envía datos)
    ▼
2. BluetoothManager._receive_loop()
    │ (recibe bytes en thread)
    │ data = socket.recv(1024)
    ▼
3. Callback: data_callback(data)
    │
    ▼
4. BluetoothApp._on_data_received(data)
    │ processed = data_handler.process(data)
    ▼
5. DataHandler.process(raw_data)
    │ - Decodifica bytes
    │ - Aplica estrategia de procesamiento
    │ - Agrega metadatos
    │ - Guarda en historial
    │ return processed_data
    ▼
6. BluetoothApp._on_data_received (continúa)
    │ ui.update_data_display(processed)
    ▼
7. MainWindow.update_data_display(processed_data)
    │ - Formatea para visualización
    │ - Inserta en TextBox
    │ - Actualiza contador
    └─ (Usuario ve los datos)
```

## Extensibilidad

La arquitectura está diseñada para ser extensible en varios puntos clave:

### Punto de Extensión 1: Formatos de Datos

Para agregar un nuevo formato de datos:
1. Crear método `_process_nuevo_formato()` en DataHandler
2. Agregar caso en el método `process()`
3. Actualizar configuración con el nuevo tipo

### Punto de Extensión 2: Visualizaciones

Para agregar nuevas visualizaciones:
1. Crear nuevo panel en MainWindow
2. Actualizar `update_data_display()` para poblar el nuevo panel
3. Mantener separación entre lógica de datos y presentación

### Punto de Extensión 3: Fuentes de Datos

Para soportar otras fuentes además de Bluetooth:
1. Crear nuevo manager similar a BluetoothManager
2. Implementar los mismos métodos de interfaz (connect, disconnect, callbacks)
3. Usar en BluetoothApp de manera intercambiable

## Threading y Concurrencia

La aplicación utiliza threading de manera cuidadosa:

**Main Thread:**
- Maneja la UI (CustomTkinter requiere que la UI esté en el main thread)
- Procesa callbacks de datos
- Actualiza visualizaciones

**Background Thread (daemon):**
- Recibe datos del socket Bluetooth
- Se ejecuta en modo daemon para terminación automática
- Comunica con el main thread solo mediante callbacks

**Sincronización:**
- Los callbacks proporcionan la sincronización necesaria
- No se requieren locks explícitos debido al diseño event-driven
- La UI se actualiza solo desde el main thread

## Manejo de Errores

Cada capa maneja errores de manera apropiada:

```
UI Layer
  │ - Muestra mensajes al usuario
  │ - Mensajes amigables
  ▼
Logic Layer
  │ - Registra errores en log
  │ - Intenta recuperación cuando es posible
  ▼
Communication Layer
  │ - Captura excepciones de Bluetooth
  │ - Propaga información de error hacia arriba
```

## Consideraciones de Rendimiento

1. **Buffer circular** en DataHandler limita el uso de memoria
2. **Threading** mantiene la UI responsiva
3. **Lazy loading** de configuración solo cuando es necesaria
4. **Actualización selectiva** de la UI solo cuando hay nuevos datos

## Conclusión

Esta arquitectura modular y bien organizada permite que la aplicación sea:
- **Mantenible**: Cada componente tiene responsabilidades claras
- **Extensible**: Fácil agregar nuevas funcionalidades
- **Testeable**: Los componentes están desacoplados
- **Comprensible**: La separación en capas facilita el entendimiento

La clave del diseño es la separación de responsabilidades y el uso de callbacks para desacoplar los componentes, permitiendo que cada uno evolucione independientemente.
