# 📝 GUÍA: QUÉ CAMBIÓ Y CÓMO IMPLEMENTARLO

## 🎯 RESUMEN DE CAMBIOS

Tu proyecto ahora tiene **soporte DUAL**: puede trabajar con **Bluetooth Classic** (Arduino/HC-05) Y con **BLE** (Renpho ES-26BB-B).

---

## 📦 ARCHIVOS NUEVOS AGREGADOS

### **1. src/__init__.py** (NUEVO)
**¿Qué es?** Archivo que marca la carpeta `src/` como un paquete Python  
**¿Por qué?** Permite importar módulos correctamente  
**¿Qué hace?** Define versión y metadatos del proyecto

### **2. src/renpho_ble_manager.py** (NUEVO) ⭐
**¿Qué es?** Gestor completo para dispositivos BLE  
**¿Qué hace?**
- Escanea dispositivos BLE (Renpho, etc.)
- Conecta vía Bluetooth Low Energy
- Descubre servicios GATT
- Suscribe a notificaciones
- Decodifica datos de peso

**Tamaño:** ~570 líneas  
**Contiene:** Explicaciones detalladas de cada función

### **3. src/bluetooth_ble_adapter.py** (NUEVO) ⭐
**¿Qué es?** Adaptador que hace compatible BLE con tu app  
**¿Qué hace?**
- Crea un "puente" entre threading (app) y asyncio (BLE)
- Hace que BLE se vea como Bluetooth Classic para la app
- Maneja la complejidad de asyncio automáticamente

**Tamaño:** ~300 líneas  
**Contiene:** Explicaciones de threading y asyncio

---

## 🔄 ARCHIVOS MODIFICADOS

### **main.py** (ACTUALIZADO) ⭐⭐⭐

**¿Qué cambió?**

#### **ANTES:**
```python
# Solo soportaba Bluetooth Classic
self.bluetooth_manager = BluetoothManager()
```

#### **AHORA:**
```python
# Lee configuración
usar_ble = self.config.get('usar_ble', False)

# Decide qué gestor usar
if usar_ble and BLEAK_AVAILABLE:
    # Modo BLE para Renpho
    self.bluetooth_manager = BluetoothBLEAdapter()
else:
    # Modo Classic para Arduino
    self.bluetooth_manager = BluetoothManager()
```

**¿Qué significa esto?**
- Si `usar_ble = true` en config.json → Usa BLE (Renpho)
- Si `usar_ble = false` en config.json → Usa Classic (Arduino)
- ¡Puedes cambiar entre modos solo editando config.json!

**Cambios específicos:**

1. **Líneas 13-16:** Importa soporte BLE
```python
try:
    from src.bluetooth_ble_adapter import BluetoothBLEAdapter, BLEAK_AVAILABLE
except ImportError:
    BLEAK_AVAILABLE = False
```

2. **Líneas 50-69:** Lógica de selección de modo
```python
usar_ble = self.config.get('usar_ble', False)

if usar_ble:
    if BLEAK_AVAILABLE:
        logger.info("🔵 Modo: BLE")
        self.bluetooth_manager = BluetoothBLEAdapter()
    else:
        logger.warning("bleak no instalado, usando Classic")
        self.bluetooth_manager = BluetoothManager()
else:
    logger.info("📡 Modo: Classic")
    self.bluetooth_manager = BluetoothManager()
```

3. **Líneas 130-135:** Limpieza mejorada
```python
def cleanup(self):
    self.bluetooth_manager.disconnect()
    
    # Si es BLE, limpieza adicional
    if hasattr(self.bluetooth_manager, 'cleanup'):
        self.bluetooth_manager.cleanup()
```

---

### **config.json** (ACTUALIZADO)

**¿Qué cambió?**

#### **ANTES:**
```json
{
    "appearance_mode": "dark",
    "color_theme": "blue",
    "scan_duration": 8
}
```

#### **AHORA:**
```json
{
    "appearance_mode": "dark",
    "color_theme": "blue",
    "scan_duration": 8,
    "usar_ble": false,
    "_comentario_usar_ble": "true = Renpho (BLE), false = Arduino (Classic)"
}
```

**Nueva opción: `"usar_ble"`**
- `false` = Modo Bluetooth Classic (Arduino, HC-05)
- `true` = Modo BLE (Renpho ES-26BB-B)

**¿Cómo cambiarlo?**

Para usar **Renpho**:
```json
"usar_ble": true
```

Para usar **Arduino**:
```json
"usar_ble": false
```

---

### **requirements.txt** (ACTUALIZADO)

**¿Qué cambió?**

#### **ANTES:**
```
customtkinter>=5.2.0
pybluez>=0.23
```

#### **AHORA:**
```
customtkinter>=5.2.0
pybluez>=0.23
bleak>=0.21.0
```

**Nueva dependencia: `bleak`**
- Librería para Bluetooth Low Energy
- Solo necesaria si vas a usar Renpho
- Si solo usas Arduino, no es obligatoria (pero no hace daño)

---

## 📂 ESTRUCTURA FINAL DEL PROYECTO

```
MedinaBluetooth/
│
├── main.py                          ← MODIFICADO (soporte dual)
├── requirements.txt                 ← MODIFICADO (agregado bleak)
├── config.json                      ← MODIFICADO (agregado usar_ble)
├── bluetooth_app.log                (se genera automáticamente)
│
└── src/
    ├── __init__.py                  ← NUEVO
    ├── config.py                    (sin cambios)
    ├── bluetooth_manager.py         (sin cambios - Classic)
    ├── bluetooth_ble_adapter.py     ← NUEVO (adaptador BLE)
    ├── renpho_ble_manager.py        ← NUEVO (gestor BLE)
    ├── data_handler.py              (sin cambios)
    │
    └── ui/
        ├── __init__.py              (sin cambios)
        └── main_window.py           (sin cambios)
```

---

## 🚀 CÓMO IMPLEMENTAR EN TU PROYECTO

### **PASO 1: Hacer Backup**

```bash
# En tu carpeta del proyecto
git add .
git commit -m "Backup antes de actualizar a v2.0"
```

### **PASO 2: Copiar Archivos Nuevos**

Descarga del proyecto actualizado y copia:

**Archivos NUEVOS a agregar:**
```
src/__init__.py                  → Copiar a tu src/
src/renpho_ble_manager.py        → Copiar a tu src/
src/bluetooth_ble_adapter.py     → Copiar a tu src/
```

**Archivos a REEMPLAZAR:**
```
main.py                          → Reemplazar tu main.py actual
config.json                      → Reemplazar tu config.json actual
requirements.txt                 → Reemplazar tu requirements.txt actual
```

**Archivos SIN CAMBIOS (no tocar):**
```
src/bluetooth_manager.py         (mantener como está)
src/config.py                    (mantener como está)
src/data_handler.py              (mantener como está)
src/ui/main_window.py            (mantener como está)
src/ui/__init__.py               (mantener como está)
```

### **PASO 3: Instalar Dependencia BLE**

```bash
pip install bleak
```

### **PASO 4: Verificar Instalación**

```bash
python -c "import bleak; print('✓ bleak instalado')"
```

### **PASO 5: Configurar Modo**

**Para usar Renpho:**
```json
// En config.json
"usar_ble": true
```

**Para usar Arduino:**
```json
// En config.json
"usar_ble": false
```

### **PASO 6: Ejecutar**

```bash
python main.py
```

**Salida esperada:**

**Modo Classic (Arduino):**
```
============================================================
  MEDINABLUETOOTH v2.0
  Soporte: Bluetooth Classic + BLE
============================================================

📡 Modo: Bluetooth Classic (SPP/RFCOMM)
   Compatible con: Arduino, HC-05, HC-06, básculas SPP
✓ Aplicación inicializada en modo Classic
```

**Modo BLE (Renpho):**
```
============================================================
  MEDINABLUETOOTH v2.0
  Soporte: Bluetooth Classic + BLE
============================================================

🔵 Modo: Bluetooth Low Energy (BLE)
   Compatible con: Renpho ES-26BB-B, básculas BLE
✓ Aplicación inicializada en modo BLE
```

---

## 🔧 CÓMO CAMBIAR ENTRE MODOS

### **Cambiar de Arduino a Renpho:**

1. Editar `config.json`:
```json
"usar_ble": true
```

2. Reiniciar aplicación
3. Listo - ahora escanea BLE

### **Cambiar de Renpho a Arduino:**

1. Editar `config.json`:
```json
"usar_ble": false
```

2. Reiniciar aplicación
3. Listo - ahora escanea Classic

---

## 📊 COMPARACIÓN: ANTES vs AHORA

| Característica | ANTES (v1.0) | AHORA (v2.0) |
|----------------|--------------|--------------|
| **Bluetooth Classic** | ✅ Sí | ✅ Sí |
| **Bluetooth BLE** | ❌ No | ✅ Sí |
| **Arduino/HC-05** | ✅ Soportado | ✅ Soportado |
| **Renpho ES-26BB-B** | ❌ No compatible | ✅ Compatible |
| **Cambio de modo** | ❌ No posible | ✅ En config.json |
| **Archivos totales** | 9 archivos | 12 archivos |

---

## ⚠️ ADVERTENCIAS IMPORTANTES

### **1. BLE es Experimental**

```
╔═══════════════════════════════════════════════════════╗
║  Renpho puede NO funcionar completamente              ║
║  Usa protocolo propietario sin documentación          ║
║  Ten Arduino listo como plan B                        ║
╚═══════════════════════════════════════════════════════╝
```

### **2. No Mezclar Modos**

- Decide UN modo antes de escanear
- No cambies modo con dispositivo conectado
- Reinicia app después de cambiar config.json

### **3. Dependencias**

- `bleak` solo funciona en Windows 10+, Linux con BlueZ, macOS 10.15+
- Si tienes problemas instalando `bleak`, usa modo Classic

---

## 🐛 SOLUCIÓN DE PROBLEMAS

### **Problema: "ModuleNotFoundError: No module named 'bleak'"**

**Solución:**
```bash
pip install bleak
```

### **Problema: "bleak not available, using Classic"**

**Causa:** bleak no está instalado o falló import  
**Solución:** Revisar instalación de bleak

### **Problema: No detecta Renpho en modo BLE**

**Solución:**
1. Verificar que `"usar_ble": true` en config.json
2. Pisar báscula para activar Bluetooth
3. Aumentar `scan_duration` a 15 segundos

---

## ✅ CHECKLIST FINAL

Antes de ejecutar:

- [ ] Archivos NUEVOS copiados a `src/`
- [ ] `main.py` reemplazado con versión nueva
- [ ] `config.json` actualizado con `usar_ble`
- [ ] `requirements.txt` actualizado
- [ ] `bleak` instalado (`pip install bleak`)
- [ ] Modo configurado en `config.json`
- [ ] Backup del proyecto anterior hecho

---

## 🎓 EXPLICACIÓN TÉCNICA

### **¿Cómo funciona el soporte dual?**

```python
# En main.py, línea ~50
usar_ble = self.config.get('usar_ble', False)

if usar_ble and BLEAK_AVAILABLE:
    # Crear gestor BLE
    self.bluetooth_manager = BluetoothBLEAdapter()
else:
    # Crear gestor Classic
    self.bluetooth_manager = BluetoothManager()
```

**Ambos gestores tienen los mismos métodos:**
- `scan_devices(duration)`
- `connect(address, port)`
- `disconnect()`
- `set_data_callback(callback)`

**Por eso la UI no necesita cambios** - para ella, ambos son iguales.

### **¿Qué hace el adaptador?**

```
App (threading) → BluetoothBLEAdapter → [Thread asyncio] → RenphoBLE → Báscula
                                              ↑
                            Resuelve incompatibilidad
                            threading vs asyncio
```

---

## 📞 PRÓXIMOS PASOS

1. ✅ Copiar archivos al proyecto
2. ✅ Instalar `bleak`
3. ✅ Configurar modo en `config.json`
4. ✅ Ejecutar y probar
5. ✅ Si Renpho no funciona → Cambiar a Arduino

---

**¡Tu proyecto ahora es dual-mode!** 🎉

Puedes trabajar con **Arduino** (Classic) o **Renpho** (BLE) cambiando solo una línea en `config.json`.
