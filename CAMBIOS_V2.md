# 📝 GUÍA DE CAMBIOS - Integración BLE a MedinaBluetooth

## 🎯 ¿QUÉ SE AGREGÓ AL PROYECTO?

Tu proyecto ahora soporta **AMBOS** tipos de Bluetooth:
- ✅ Bluetooth Classic (SPP/RFCOMM) - Para Arduino, HC-05
- ✅ Bluetooth Low Energy (BLE) - Para Renpho ES-26BB-B

---

## 📦 ARCHIVOS NUEVOS AGREGADOS

### **1. src/__init__.py** (NUEVO)

**¿Qué es?** Marca la carpeta `src` como paquete Python

**Contenido:**
```python
"""Paquete principal de la aplicación Bluetooth MedinaBluetooth"""
__version__ = '1.0.0'
__author__ = 'Equipo MedinaBluetooth'
```

**¿Por qué es necesario?**
- Python requiere este archivo para importar módulos de la carpeta
- Sin él, `from src.bluetooth_manager import...` fallaría

---

### **2. src/renpho_ble_manager.py** (NUEVO - 570 líneas)

**¿Qué hace?** Gestor completo para Bluetooth Low Energy

**Funciones principales:**
- `escanear_dispositivos()` - Busca dispositivos BLE
- `conectar()` - Conecta a báscula Renpho
- `descubrir_servicios()` - Ve qué servicios ofrece el dispositivo
- `suscribir_peso()` - Se suscribe a notificaciones de peso
- `_decodificar_peso()` - Convierte bytes a kilogramos

**Ejemplo de uso:**
```python
manager = RenphoBLEManager()
devices = await manager.escanear_dispositivos(10)
await manager.conectar(devices[0]['address'])
await manager.suscribir_peso()
# Cuando pisas báscula → envía notificación → llama callback
```

---

### **3. src/bluetooth_ble_adapter.py** (NUEVO - 300 líneas)

**¿Qué hace?** Adaptador que hace que BLE funcione con tu app actual

**Problema que resuelve:**
```
Tu app usa threading (síncrono)
BLE usa asyncio (asíncrono)
→ INCOMPATIBLES

Adaptador = Puente entre ambos
```

**Cómo funciona:**
1. Crea thread separado que ejecuta loop asyncio
2. Recibe llamadas síncronas de tu app
3. Las convierte a asíncronas para BLE
4. Retorna resultados síncronamente

---

## 📄 ARCHIVOS MODIFICADOS

### **1. main.py** (ACTUALIZADO)

#### **Cambios principales:**

**ANTES:**
```python
# Solo Bluetooth Classic
self.bluetooth_manager = BluetoothManager()
```

**AHORA:**
```python
# Intenta importar BLE
try:
    from src.bluetooth_ble_adapter import BluetoothBLEAdapter, BLEAK_AVAILABLE
    BLE_SUPPORT = True
except ImportError:
    BLE_SUPPORT = False

# Determina qué usar
usar_ble = self.config.get('usar_ble', False)

if usar_ble and BLE_SUPPORT:
    self.bluetooth_manager = BluetoothBLEAdapter()  # BLE
else:
    self.bluetooth_manager = BluetoothManager()      # Classic
```

**¿Qué hace esto?**
1. Lee configuración de `config.json`
2. Si `"usar_ble": true` → usa BLE
3. Si `"usar_ble": false` → usa Classic
4. Si bleak no está instalado → usa Classic (fallback)

#### **Nuevo método cleanup():**

```python
def cleanup(self):
    self.bluetooth_manager.disconnect()
    
    # Si es BLE, limpieza adicional
    if hasattr(self.bluetooth_manager, 'cleanup'):
        self.bluetooth_manager.cleanup()
```

**¿Por qué?** BLE necesita cerrar loop asyncio correctamente

---

### **2. requirements.txt** (ACTUALIZADO)

**ANTES:**
```
customtkinter>=5.2.0
pybluez>=0.23
```

**AHORA:**
```
customtkinter>=5.2.0
pybluez>=0.23
bleak>=0.21.0          ← NUEVO
```

**bleak** = Librería para Bluetooth Low Energy

---

### **3. config.json** (NECESITA ACTUALIZACIÓN)

**ANTES:**
```json
{
    "appearance_mode": "dark",
    "color_theme": "blue",
    "window_size": "900x700",
    "scan_duration": 8,
    "last_device": null
}
```

**AHORA (agregar esta línea):**
```json
{
    "appearance_mode": "dark",
    "color_theme": "blue",
    "window_size": "900x700",
    "scan_duration": 8,
    "usar_ble": false,     ← AGREGAR ESTA LÍNEA
    "last_device": null
}
```

**Valores posibles:**
- `"usar_ble": true` → Usa BLE (Renpho)
- `"usar_ble": false` → Usa Classic (Arduino/HC-05)

---

## 📁 ESTRUCTURA FINAL DEL PROYECTO

```
MedinaBluetooth/
│
├── main.py                          ✏️ ACTUALIZADO
├── requirements.txt                 ✏️ ACTUALIZADO
├── config.json                      ⚠️ ACTUALIZAR MANUALMENTE
├── bluetooth_app.log
├── README.md
├── GUIA_DETALLADA.md
│
└── src/
    ├── __init__.py                  ⭐ NUEVO
    ├── config.py
    ├── bluetooth_manager.py         (sin cambios)
    ├── data_handler.py              (sin cambios)
    ├── renpho_ble_manager.py        ⭐ NUEVO
    ├── bluetooth_ble_adapter.py     ⭐ NUEVO
    │
    └── ui/
        ├── __init__.py
        └── main_window.py           (sin cambios)
```

---

## 🔧 CÓMO IMPLEMENTAR LOS CAMBIOS

### **PASO 1: Instalar bleak**

```bash
pip install bleak
```

**Si da error en Windows:**
- Necesitas Visual C++ Build Tools
- Descarga: https://visualstudio.microsoft.com/visual-cpp-build-tools/

---

### **PASO 2: Agregar archivos nuevos**

Copia estos archivos a tu proyecto:

1. **`src/__init__.py`**
   - Ubicación: `MedinaBluetooth/src/__init__.py`

2. **`src/renpho_ble_manager.py`**
   - Ubicación: `MedinaBluetooth/src/renpho_ble_manager.py`

3. **`src/bluetooth_ble_adapter.py`**
   - Ubicación: `MedinaBluetooth/src/bluetooth_ble_adapter.py`

---

### **PASO 3: Reemplazar archivos existentes**

1. **Reemplazar `main.py`** con la versión actualizada

2. **Reemplazar `requirements.txt`** con la versión actualizada

---

### **PASO 4: Actualizar config.json**

Abre `config.json` y agrega la línea `"usar_ble"`:

```json
{
    "appearance_mode": "dark",
    "color_theme": "blue",
    "window_size": "900x700",
    "scan_duration": 8,
    "usar_ble": false,
    "last_device": null
}
```

---

## 🎮 CÓMO USAR LA APLICACIÓN AHORA

### **Modo 1: Bluetooth Classic (Arduino/HC-05)**

1. En `config.json`:
   ```json
   "usar_ble": false
   ```

2. Ejecutar:
   ```bash
   python main.py
   ```

3. Usar normalmente (como antes)

---

### **Modo 2: Bluetooth Low Energy (Renpho)**

1. En `config.json`:
   ```json
   "usar_ble": true
   ```

2. Ejecutar:
   ```bash
   python main.py
   ```

3. Flujo:
   - Presionar "Escanear Dispositivos"
   - Pisar báscula Renpho (activarla)
   - Seleccionar báscula de la lista
   - Presionar "Conectar"
   - Pisar báscula nuevamente
   - Ver peso en "Datos Recibidos"

---

## 📊 COMPARACIÓN: QUÉ CAMBIÓ

| Aspecto | ANTES (v1.0) | AHORA (v2.0) |
|---------|--------------|--------------|
| **Bluetooth soportado** | Solo Classic | Classic + BLE |
| **Dispositivos** | Arduino, HC-05 | + Renpho, básculas BLE |
| **Archivos** | 7 archivos | 10 archivos |
| **Dependencias** | pybluez, customtkinter | + bleak |
| **Configuración** | Sin opción BLE | `"usar_ble"` en config |
| **Complejidad** | Simple | Media |

---

## ⚙️ EXPLICACIÓN TÉCNICA DE LOS CAMBIOS

### **¿Por qué se necesitan 2 archivos nuevos?**

#### **renpho_ble_manager.py:**

**Función:** Implementa BLE desde cero

**Razón:** 
- PyBluez NO soporta BLE
- Necesitamos librería diferente (bleak)
- Protocolo completamente distinto

**Analogía:**
```
PyBluez (Classic) = Hablar por teléfono
bleak (BLE)       = Enviar WhatsApp

Mismo propósito (comunicación)
Pero método completamente diferente
```

#### **bluetooth_ble_adapter.py:**

**Función:** Hace que BLE se vea igual que Classic para tu app

**Razón:**
- Tu app usa threading (síncrono)
- BLE usa asyncio (asíncrono)
- Necesitas "traductor"

**Analogía:**
```
Tu app habla "Español" (threading)
BLE habla "Chino" (asyncio)

Adaptador = Intérprete que traduce
```

---

### **¿Por qué main.py decide cuál usar?**

**Antes:**
```python
# Siempre usaba Classic
manager = BluetoothManager()
```

**Ahora:**
```python
# Decide según configuración
if config dice "usar BLE":
    manager = BluetoothBLEAdapter()
else:
    manager = BluetoothManager()
```

**Ventaja:** Cambias de Classic a BLE solo editando config.json

**Sin tocar código**

---

## 🐛 SOLUCIÓN DE PROBLEMAS

### **Error: "bleak module not found"**

**Causa:** bleak no instalado

**Solución:**
```bash
pip install bleak
```

---

### **Error: "No module named 'src'"**

**Causa:** Falta `src/__init__.py`

**Solución:**
- Crear archivo vacío `src/__init__.py`
- O copiar el que te proporcioné

---

### **App usa Classic aunque config dice BLE**

**Causa:** bleak no instalado o error al importar

**Verificar:**
```python
python -c "import bleak; print('BLE OK')"
```

**Si falla:** Reinstalar bleak

---

### **Renpho no aparece al escanear**

**Causa:** Báscula no está transmitiendo

**Solución:**
1. Pisar báscula (activarla)
2. Escanear mientras está encendida
3. Aumentar duración de escaneo en config

---

## ✅ CHECKLIST DE IMPLEMENTACIÓN

- [ ] `bleak` instalado (`pip install bleak`)
- [ ] Archivo `src/__init__.py` creado
- [ ] Archivo `src/renpho_ble_manager.py` agregado
- [ ] Archivo `src/bluetooth_ble_adapter.py` agregado
- [ ] Archivo `main.py` reemplazado
- [ ] Archivo `requirements.txt` reemplazado
- [ ] `config.json` actualizado con `"usar_ble"`
- [ ] Probado con `"usar_ble": false` (Classic)
- [ ] Probado con `"usar_ble": true` (BLE)

---

## 🎯 RESUMEN EJECUTIVO

### **¿Qué cambió?**
3 archivos nuevos + 2 actualizados = Soporte BLE completo

### **¿Qué sigue funcionando igual?**
Todo lo de antes (Arduino, HC-05, Classic)

### **¿Qué ganaste?**
Ahora puedes conectar Renpho ES-26BB-B

### **¿Qué perdiste?**
Nada. Classic sigue funcionando 100%

### **¿Es más complejo?**
Sí, pero switcheas con 1 línea en config.json

---

**¿Listo para implementar? ¡Te ayudo en cualquier paso!** 🚀
