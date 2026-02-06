# 🚀 Inicio Rápido - Monitor Bluetooth

## ¿Qué es este proyecto?

Esta es una aplicación completa de Python para recibir y visualizar datos de dispositivos Bluetooth en tiempo real. Está diseñada para ser fácilmente personalizable para trabajar con cualquier dispositivo que envíe datos por Bluetooth (Arduino, ESP32, sensores, etc.).

## 📦 Contenido del Proyecto

```
bluetooth-monitor/
│
├── 📄 main.py                    ← EMPIEZA AQUÍ: Ejecuta la aplicación
├── ⚙️ config.json               ← Configuración (se crea automáticamente)
├── 📋 requirements.txt          ← Dependencias de Python
│
├── 📚 README.md                 ← Documentación completa
├── 🔧 setup.py                  ← Script de instalación
├── 📜 LICENSE                   ← Licencia MIT
│
├── 🐍 src/                      ← Código fuente
│   ├── bluetooth_manager.py    ← Gestión de Bluetooth
│   ├── data_handler.py         ← Procesamiento de datos (PERSONALIZA AQUÍ)
│   ├── config.py              ← Gestión de configuración
│   │
│   └── ui/                    ← Interfaz gráfica
│       └── main_window.py     ← Ventana principal
│
└── 📖 docs/                    ← Documentación adicional
    ├── user_guide.md          ← Guía paso a paso
    ├── api_reference.md       ← Referencia técnica
    └── architecture.md        ← Explicación de la arquitectura
```

## ⚡ Instalación en 3 Pasos

### Paso 1: Verificar Python
```bash
python --version
# Necesitas Python 3.8 o superior
```

### Paso 2: Instalar Dependencias
```bash
# Opción A: Instalación automática
python setup.py

# Opción B: Instalación manual
pip install -r requirements.txt
```

### Paso 3: Ejecutar
```bash
python main.py
```

## 🎯 Uso Básico

### Conectar un Dispositivo

1. **Escanear**: Haz clic en "Escanear Dispositivos"
2. **Seleccionar**: Revisa la lista de dispositivos encontrados
3. **Conectar**: Haz clic en "Conectar"
4. **Visualizar**: Los datos aparecerán automáticamente en tiempo real

### Exportar Datos

Haz clic en "Exportar CSV" para guardar todos los datos recibidos en un archivo.

## 🔧 Personalización Rápida

### Cambiar el Formato de Datos

Edita el archivo `config.json`:

```json
{
    "data_format": "text"
}
```

Opciones disponibles:
- `"text"` - Texto simple (ejemplo: `temperatura:25.5,humedad:60`)
- `"json"` - JSON (ejemplo: `{"temp": 25.5, "hum": 60}`)
- `"binary"` - Datos binarios
- `"custom"` - Tu formato personalizado

### Adaptar al Formato de Tu Dispositivo

Si tu dispositivo envía datos en un formato específico, edita el archivo `src/data_handler.py`.

**Ejemplo: Tu Arduino envía** `T:25.5;H:60.2;P:1013`

```python
# En src/data_handler.py, método _process_custom():

def _process_custom(self, raw_data: bytes) -> Dict[str, Any]:
    text = raw_data.decode('utf-8').strip()
    data = {}
    
    # Mapeo de códigos a nombres
    key_map = {
        'T': 'temperatura',
        'H': 'humedad',
        'P': 'presion'
    }
    
    # Separar por punto y coma
    parts = text.split(';')
    for part in parts:
        if ':' in part:
            key, value = part.split(':', 1)
            readable_key = key_map.get(key.strip(), key.strip())
            data[readable_key] = float(value.strip())
    
    return data
```

Luego en `config.json` establece: `"data_format": "custom"`

### Cambiar la Apariencia

En `config.json`:

```json
{
    "appearance_mode": "dark",    // "dark", "light", o "system"
    "color_theme": "blue",        // "blue", "green", o "dark-blue"
    "window_width": 900,
    "window_height": 600
}
```

## 📱 Código de Ejemplo para Arduino

Para probar la aplicación con Arduino, usa este código simple:

```cpp
// Para módulos Bluetooth HC-05/HC-06
void setup() {
  Serial.begin(9600);  // Velocidad del Bluetooth
}

void loop() {
  // Enviar datos en formato texto
  Serial.print("temperatura:");
  Serial.print(25.5);
  Serial.print(",humedad:");
  Serial.println(60.2);
  
  delay(1000);  // Enviar cada segundo
}
```

## 🐛 Solución de Problemas Comunes

### No se encuentran dispositivos
- ✅ Verifica que Bluetooth esté activo en tu computadora
- ✅ Asegúrate de que tu dispositivo esté encendido y visible
- ✅ En Linux, puede necesitar permisos: `sudo python main.py`

### No se pueden instalar las dependencias
- ✅ Windows: Puede necesitar Build Tools para Visual Studio
- ✅ Linux: Instala primero `bluetooth libbluetooth-dev`
  ```bash
  sudo apt-get install bluetooth libbluetooth-dev
  ```

### Los datos no se muestran correctamente
- ✅ Verifica el formato en `config.json`
- ✅ Revisa el archivo `bluetooth_app.log` para ver los datos crudos
- ✅ Ajusta el método de procesamiento en `data_handler.py`

## 📚 Siguientes Pasos

Una vez que tengas la aplicación funcionando:

1. **Lee la documentación completa** en `README.md`
2. **Consulta la guía de usuario** en `docs/user_guide.md` para uso detallado
3. **Revisa la referencia de API** en `docs/api_reference.md` si quieres extender el código
4. **Explora la arquitectura** en `docs/architecture.md` para entender cómo funciona internamente

## 💡 Archivos Clave para Personalizar

| Archivo | Cuándo Modificarlo |
|---------|-------------------|
| `config.json` | Para cambiar configuración básica (tema, tamaño, formato) |
| `src/data_handler.py` | Para adaptar al formato de datos de tu dispositivo |
| `src/ui/main_window.py` | Para cambiar la interfaz o agregar visualizaciones |
| `src/bluetooth_manager.py` | Para modificar la lógica de conexión Bluetooth |

## 🎓 Conceptos Importantes

### Formato de Datos
La aplicación puede procesar diferentes formatos de datos. El más común es texto plano con pares clave:valor. Si tu dispositivo envía datos de otra forma, personaliza el método correspondiente en `data_handler.py`.

### Threading
La aplicación usa un thread separado para recibir datos, lo que mantiene la interfaz responsiva. No necesitas preocuparte por esto a menos que estés haciendo modificaciones avanzadas.

### Callbacks
Los componentes se comunican mediante callbacks (funciones que se llaman cuando ocurre un evento). Esto mantiene el código desacoplado y fácil de modificar.

## 🤝 Contribuir

Si encuentras un bug o tienes una mejora, ¡las contribuciones son bienvenidas! Abre un issue o envía un pull request en GitHub.

## 📞 Ayuda

Si tienes problemas:
1. Revisa esta guía y la documentación completa
2. Consulta el archivo `bluetooth_app.log` para ver errores
3. Abre un issue en el repositorio de GitHub
4. Revisa los ejemplos en la documentación

## ✨ Características Destacadas

- 🔍 **Escaneo automático** de dispositivos Bluetooth
- 📊 **Visualización en tiempo real** de datos
- 💾 **Exportación a CSV** para análisis posterior
- ⚙️ **Configuración flexible** mediante JSON
- 🎨 **Interfaz moderna** con CustomTkinter
- 📝 **Logging completo** para debugging
- 🔧 **Fácil personalización** para diferentes dispositivos

## 🎉 ¡Listo para Empezar!

Ahora que conoces lo básico, ejecuta:

```bash
python main.py
```

Y comienza a monitorear tus dispositivos Bluetooth. ¡Diviértete!

---

**¿Necesitas más ayuda?** Consulta `README.md` para la documentación completa.
