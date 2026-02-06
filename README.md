# Monitor Bluetooth con CustomTkinter

Una aplicación Python moderna y extensible para recibir y visualizar datos de dispositivos Bluetooth en tiempo real. La interfaz está construida con CustomTkinter para proporcionar una experiencia visual atractiva y profesional.

![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)

## 📋 Descripción

Esta aplicación permite conectarse a dispositivos Bluetooth (como sensores Arduino, ESP32, microcontroladores, etc.) y visualizar los datos que envían en una interfaz gráfica intuitiva. El código está diseñado para ser fácilmente personalizable según las necesidades específicas de tu dispositivo.

### Características principales

- **Escaneo automático** de dispositivos Bluetooth cercanos
- **Interfaz gráfica moderna** con CustomTkinter
- **Procesamiento flexible** de diferentes formatos de datos (texto, JSON, binario, personalizado)
- **Visualización en tiempo real** de los datos recibidos
- **Exportación a CSV** del historial de datos
- **Arquitectura modular** para fácil personalización y mantenimiento
- **Sistema de logging** completo para debugging
- **Configuración centralizada** mediante archivo JSON

## 🚀 Instalación

### Requisitos previos

- Python 3.8 o superior
- Sistema operativo compatible con Bluetooth (Windows, Linux, macOS)
- Permisos de administrador pueden ser necesarios para acceso Bluetooth

### Instalación paso a paso

1. **Clonar el repositorio**
```bash
git clone https://github.com/tu-usuario/bluetooth-monitor.git
cd bluetooth-monitor
```

2. **Crear un entorno virtual (recomendado)**
```bash
python -m venv venv

# En Windows:
venv\Scripts\activate

# En Linux/macOS:
source venv/bin/activate
```

3. **Instalar dependencias**
```bash
pip install -r requirements.txt
```

### Instalación en Linux

En Linux, pueden ser necesarios algunos paquetes adicionales del sistema:

```bash
# Ubuntu/Debian
sudo apt-get install bluetooth libbluetooth-dev

# Fedora
sudo dnf install bluez bluez-libs bluez-libs-devel
```

### Instalación en Windows

En Windows, asegúrate de tener Bluetooth habilitado y los drivers instalados correctamente. Puede ser necesario instalar Build Tools para Visual Studio para compilar PyBluez.

## 📖 Uso

### Inicio rápido

1. **Ejecutar la aplicación**
```bash
python main.py
```

2. **Conectar un dispositivo**
   - Haz clic en "Escanear Dispositivos"
   - Selecciona tu dispositivo de la lista
   - Haz clic en "Conectar"
   - Los datos comenzarán a aparecer en tiempo real

3. **Exportar datos**
   - Haz clic en "Exportar CSV" para guardar los datos recibidos

### Configuración

La aplicación utiliza un archivo `config.json` para personalizar su comportamiento. En la primera ejecución, se creará automáticamente con valores por defecto.

**Archivo `config.json` de ejemplo:**
```json
{
    "appearance_mode": "dark",
    "color_theme": "blue",
    "window_title": "Monitor Bluetooth",
    "window_width": 900,
    "window_height": 600,
    "auto_reconnect": true,
    "reconnect_interval": 5,
    "data_buffer_size": 100,
    "data_format": "text",
    "encoding": "utf-8"
}
```

## 🔧 Personalización

La aplicación está diseñada para ser fácilmente adaptable a diferentes dispositivos y formatos de datos.

### Adaptando al formato de datos de tu dispositivo

El archivo más importante para personalizar es `src/data_handler.py`. Este archivo contiene la lógica para interpretar los datos que envía tu dispositivo.

#### Ejemplo 1: Sensor de temperatura y humedad (formato texto)

Si tu Arduino envía datos como: `temperatura:25.5,humedad:60.2`

Modifica el método `_process_text()` en `data_handler.py`:

```python
def _process_text(self, raw_data: bytes) -> Dict[str, Any]:
    text = raw_data.decode('utf-8').strip()
    data = {}
    
    # Parsear formato clave:valor separado por comas
    pairs = text.split(',')
    for pair in pairs:
        if ':' in pair:
            key, value = pair.split(':', 1)
            try:
                data[key.strip()] = float(value.strip())
            except ValueError:
                data[key.strip()] = value.strip()
    
    return data
```

#### Ejemplo 2: Datos en formato JSON

Si tu dispositivo envía: `{"temp": 25.5, "hum": 60.2, "sensor": "DHT22"}`

Usa el formato `json` en la configuración y el método `_process_json()` se encargará automáticamente.

#### Ejemplo 3: Protocolo personalizado

Si tu Arduino envía: `T:25.5;H:60.2;P:1013.2`

Modifica el método `_process_custom()` en `data_handler.py`:

```python
def _process_custom(self, raw_data: bytes) -> Dict[str, Any]:
    text = raw_data.decode('utf-8').strip()
    data = {}
    
    # Mapeo de códigos a nombres legibles
    key_map = {
        'T': 'temperatura',
        'H': 'humedad',
        'P': 'presion'
    }
    
    parts = text.split(';')
    for part in parts:
        if ':' in part:
            key, value = part.split(':', 1)
            readable_key = key_map.get(key.strip(), key.strip())
            data[readable_key] = float(value.strip())
    
    return data
```

Luego, en `config.json`, establece: `"data_format": "custom"`

### Modificando la interfaz

Para personalizar la apariencia de la interfaz, edita el archivo `src/ui/main_window.py`. Algunos cambios comunes:

**Cambiar el tema de colores:**
```python
# En config.json
"appearance_mode": "light"  # o "dark", "system"
"color_theme": "green"      # o "blue", "dark-blue"
```

**Ajustar el tamaño de la ventana:**
```python
# En config.json
"window_width": 1200,
"window_height": 800
```

## 📁 Estructura del Proyecto

```
bluetooth-monitor/
├── main.py                    # Punto de entrada de la aplicación
├── config.json               # Archivo de configuración (se crea automáticamente)
├── requirements.txt          # Dependencias de Python
├── README.md                # Este archivo
├── LICENSE                  # Licencia del proyecto
│
├── src/                     # Código fuente principal
│   ├── __init__.py
│   ├── bluetooth_manager.py # Gestión de conexiones Bluetooth
│   ├── data_handler.py      # Procesamiento de datos recibidos
│   ├── config.py           # Gestión de configuración
│   │
│   └── ui/                 # Interfaz gráfica
│       ├── __init__.py
│       └── main_window.py  # Ventana principal
│
└── docs/                   # Documentación adicional (opcional)
    ├── user_guide.md      # Guía de usuario
    └── api_reference.md   # Referencia de la API
```

## 🔍 Debugging y Solución de Problemas

### Activar logging detallado

La aplicación genera automáticamente un archivo `bluetooth_app.log`. Para ver más detalles:

En `main.py`, cambia el nivel de logging:
```python
logging.basicConfig(
    level=logging.DEBUG,  # Cambiar de INFO a DEBUG
    ...
)
```

### Problemas comunes

**No se encuentran dispositivos:**
- Verifica que el Bluetooth esté activado
- Asegúrate de que el dispositivo esté en modo emparejamiento
- En Linux, puede ser necesario ejecutar como root: `sudo python main.py`

**Error al conectar:**
- Verifica que el puerto RFCOMM sea correcto (por defecto es 1)
- Algunos dispositivos usan puertos diferentes
- Intenta emparejar el dispositivo manualmente primero

**Datos no se muestran correctamente:**
- Revisa el formato de datos en `config.json`
- Verifica la codificación de caracteres (`encoding`)
- Usa el archivo de log para ver los datos crudos recibidos

**Problemas de permisos en Linux:**
```bash
# Agregar usuario al grupo bluetooth
sudo usermod -a -G bluetooth $USER

# Reiniciar sesión para aplicar cambios
```

## 🤝 Contribuciones

Las contribuciones son bienvenidas. Por favor:

1. Haz un Fork del proyecto
2. Crea una rama para tu función (`git checkout -b feature/nueva-funcion`)
3. Commit tus cambios (`git commit -m 'Agregar nueva función'`)
4. Push a la rama (`git push origin feature/nueva-funcion`)
5. Abre un Pull Request

## 📝 Código de ejemplo para Arduino

Aquí hay un ejemplo simple de código Arduino que envía datos compatibles con esta aplicación:

```cpp
void setup() {
  Serial.begin(9600);  // Para Bluetooth HC-05/HC-06
}

void loop() {
  // Formato texto simple
  Serial.print("temperatura:");
  Serial.print(25.5);
  Serial.print(",humedad:");
  Serial.println(60.2);
  
  delay(1000);
}
```

O en formato JSON:

```cpp
void loop() {
  Serial.print("{\"temp\":");
  Serial.print(25.5);
  Serial.print(",\"hum\":");
  Serial.print(60.2);
  Serial.println("}");
  
  delay(1000);
}
```

## 📄 Licencia

Este proyecto está bajo la Licencia MIT. Ver el archivo `LICENSE` para más detalles.

## 👥 Autor

Tu Nombre - [@tu-usuario](https://github.com/tu-usuario)

## 🙏 Agradecimientos

- [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter) por la excelente biblioteca de UI
- [PyBluez](https://github.com/pybluez/pybluez) por la comunicación Bluetooth
- La comunidad de Python por su apoyo continuo

## 📞 Soporte

Si encuentras algún problema o tienes preguntas:
- Abre un [Issue](https://github.com/tu-usuario/bluetooth-monitor/issues)
- Consulta la [Documentación](https://github.com/tu-usuario/bluetooth-monitor/wiki)
- Contacta al autor

---

**¿Te gustó este proyecto? Dale una ⭐ en GitHub!**
