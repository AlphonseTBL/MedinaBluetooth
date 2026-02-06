# Guía de Usuario - Monitor Bluetooth

Esta guía te ayudará a comenzar a usar la aplicación de monitoreo Bluetooth paso a paso.

## Primeros Pasos

### 1. Preparación del Dispositivo

Antes de usar la aplicación, asegúrate de que tu dispositivo Bluetooth esté:

- Encendido y funcionando
- En modo visible/emparejable
- Transmitiendo datos (si es un sensor o dispositivo de lectura)
- Dentro del rango de alcance (generalmente 10 metros)

### 2. Iniciar la Aplicación

Abre una terminal o línea de comandos en la carpeta del proyecto y ejecuta:

```bash
python main.py
```

La ventana principal se abrirá mostrando dos paneles principales:
- Panel izquierdo: Control de conexión Bluetooth
- Panel derecho: Visualización de datos

### 3. Escanear Dispositivos

Haz clic en el botón "Escanear Dispositivos" en el panel izquierdo. La aplicación buscará todos los dispositivos Bluetooth cercanos durante aproximadamente 8 segundos (este tiempo se puede configurar en `config.json`).

Durante el escaneo verás el mensaje "Escaneando..." en el botón. Una vez completado, aparecerá una lista de dispositivos encontrados mostrando:
- Nombre del dispositivo
- Dirección MAC del dispositivo

### 4. Conectar a un Dispositivo

Una vez que aparezcan los dispositivos en la lista:

1. Revisa la lista de dispositivos encontrados
2. Identifica tu dispositivo por su nombre
3. Haz clic en el botón "Conectar"

Nota: La versión actual se conecta automáticamente al primer dispositivo de la lista. Una futura actualización permitirá seleccionar manualmente el dispositivo deseado.

Si la conexión es exitosa:
- El estado en la parte inferior cambiará a "Conectado"
- Verás la información del dispositivo en verde
- Los botones cambiarán para mostrar "Desconectar" activo
- Los datos comenzarán a aparecer en el panel derecho

### 5. Visualizar Datos en Tiempo Real

Una vez conectado, los datos aparecerán automáticamente en el panel de la derecha. Cada línea muestra:
- Marca de tiempo (hora:minuto:segundo)
- Datos recibidos formateados según tu configuración

Por ejemplo:
```
[14:23:15] temperatura: 25.5 | humedad: 60.2
[14:23:16] temperatura: 25.6 | humedad: 60.1
[14:23:17] temperatura: 25.5 | humedad: 60.3
```

La visualización se actualiza automáticamente y hace scroll al último dato recibido.

### 6. Gestionar los Datos

La aplicación ofrece dos opciones para gestionar los datos:

**Limpiar datos:**
- Haz clic en el botón "Limpiar" en la parte superior del panel de datos
- Confirma la acción en el diálogo que aparece
- Esto borrará la visualización y el historial en memoria

**Exportar datos:**
- Haz clic en el botón "Exportar CSV"
- Los datos se guardarán automáticamente en un archivo CSV con el formato:
  `bluetooth_data_AAAAMMDD_HHMMSS.csv`
- El archivo incluirá:
  - Marca de tiempo de cada lectura
  - Número de mensaje
  - Todos los campos de datos recibidos
- Recibirás una notificación con la ubicación del archivo

### 7. Desconectar

Para finalizar la conexión:
- Haz clic en el botón "Desconectar"
- La aplicación cerrará la conexión de forma segura
- El estado volverá a "Desconectado"
- Podrás reconectar o escanear nuevamente si lo deseas

### 8. Cerrar la Aplicación

Para cerrar la aplicación:
- Haz clic en la X de la ventana
- Si hay una conexión activa, se te preguntará si deseas cerrar de todas formas
- Confirma para cerrar completamente

## Personalización

### Cambiar el Tema Visual

Puedes cambiar entre modo oscuro y claro editando el archivo `config.json`:

```json
{
    "appearance_mode": "dark"
}
```

Opciones disponibles:
- `"dark"` - Modo oscuro (por defecto)
- `"light"` - Modo claro
- `"system"` - Sigue la configuración del sistema

### Cambiar el Esquema de Colores

También en `config.json`:

```json
{
    "color_theme": "blue"
}
```

Opciones: `"blue"`, `"green"`, `"dark-blue"`

### Ajustar el Formato de Datos

Si los datos no se muestran correctamente, verifica el formato en `config.json`:

```json
{
    "data_format": "text",
    "data_separator": "\n",
    "encoding": "utf-8"
}
```

Formatos soportados:
- `"text"` - Texto plano (por defecto)
- `"json"` - Datos en formato JSON
- `"binary"` - Datos binarios
- `"custom"` - Formato personalizado (requiere modificar el código)

## Solución de Problemas Comunes

### No aparecen dispositivos en el escaneo

**Posibles causas:**
- El Bluetooth de tu computadora está desactivado
- El dispositivo no está encendido o no es visible
- El dispositivo está fuera de rango
- Problemas de permisos (especialmente en Linux)

**Soluciones:**
- Verifica que el Bluetooth de tu computadora esté activado
- Asegúrate de que el dispositivo esté encendido y en modo visible
- Acerca el dispositivo a tu computadora
- En Linux, intenta ejecutar con permisos de administrador: `sudo python main.py`

### No se puede conectar al dispositivo

**Posibles causas:**
- El dispositivo ya está conectado a otro equipo
- Puerto RFCOMM incorrecto
- Dispositivo requiere emparejamiento previo

**Soluciones:**
- Desconecta el dispositivo de otros equipos
- Verifica que el puerto RFCOMM sea el correcto (generalmente 1)
- Empareja el dispositivo manualmente desde la configuración de Bluetooth de tu sistema operativo antes de usar la aplicación

### Los datos se ven incorrectos o ilegibles

**Posibles causas:**
- Formato de datos incorrecto en la configuración
- Codificación de caracteres incorrecta
- El dispositivo envía datos en un formato no estándar

**Soluciones:**
- Verifica el parámetro `data_format` en `config.json`
- Prueba con diferentes valores de `encoding` (utf-8, ascii, latin-1)
- Revisa el archivo `bluetooth_app.log` para ver los datos crudos recibidos
- Puede ser necesario personalizar el procesamiento en `data_handler.py`

### La aplicación se cierra inesperadamente

**Soluciones:**
- Revisa el archivo `bluetooth_app.log` para identificar el error
- Verifica que todas las dependencias estén instaladas correctamente
- Asegúrate de tener permisos suficientes para acceder al Bluetooth

## Consejos y Trucos

1. **Mantén el historial pequeño:** Si vas a recibir muchos datos durante mucho tiempo, considera ajustar `data_buffer_size` en la configuración o exporta y limpia periódicamente para evitar problemas de memoria.

2. **Automatiza la conexión:** Si siempre te conectas al mismo dispositivo, puedes establecer su dirección MAC en `config.json` bajo `device_address` para conexión automática en futuras versiones.

3. **Debugging efectivo:** Cuando tengas problemas, activa el modo DEBUG en `main.py` para obtener información detallada en los logs.

4. **Exporta regularmente:** Si estás recolectando datos importantes, haz exportaciones periódicas para no perder información en caso de un cierre inesperado.

5. **Personaliza la interfaz:** No dudes en modificar `main_window.py` para agregar visualizaciones específicas para tus datos, como gráficos o indicadores personalizados.

## Próximos Pasos

Una vez que te familiarices con el uso básico, considera:

- Personalizar el procesamiento de datos en `data_handler.py` para tu dispositivo específico
- Agregar visualizaciones adicionales a la interfaz
- Implementar gráficos en tiempo real de tus mediciones
- Configurar alertas basadas en umbrales de valores
- Integrar con bases de datos para almacenamiento a largo plazo

¡Disfruta monitoreando tus dispositivos Bluetooth!
