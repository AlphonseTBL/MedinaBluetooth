"""
Lector de peso en tiempo real para báscula Renpho ES-26BB-B
============================================================
Protocolo documentado en:
  - https://github.com/oliexdev/openScale/issues/900
  - https://github.com/oliexdev/openScale/pull/901

Dependencias:
    pip install bleak

Uso:
    # Modo escaneo (para encontrar la MAC de tu báscula):
    python renpho_es26bb_weight.py --scan

    # Modo lectura continua (reemplaza con tu MAC):
    python renpho_es26bb_weight.py --mac AA:BB:CC:DD:EE:FF

    # Modo descubrimiento (lista todos los servicios/características):
    python renpho_es26bb_weight.py --mac AA:BB:CC:DD:EE:FF --discover
"""

import asyncio
import argparse
import struct
from bleak import BleakScanner, BleakClient

# ─── UUIDs del protocolo Renpho ES-26BB-B ────────────────────────────────────
# Documentados mediante ingeniería inversa del tráfico BLE (HCI snoop log).
# Referencia: openScale PR #901 (github.com/oliexdev/openScale/pull/901)

DEVICE_NAME          = "ES-26BB-B"

# ─── UUIDs originales (modelo ES-26BB-B estándar) ─────────────────────────────
SERVICE_UUID_CLASSIC        = "0000ffe0-0000-1000-8000-00805f9b34fb"
CHARACTERISTIC_UUID_CLASSIC = "0000ffe1-0000-1000-8000-00805f9b34fb"

# ─── UUIDs del servicio propietario TI (detectado en tu báscula) ──────────────
# Encontrados via --discover: el servicio "Unknown" con características notify+write
# es el canal de datos de peso en modelos Renpho con chipset Texas Instruments.
SERVICE_UUID_TI = "f000ffc0-0451-4000-b000-000000000000"
CHARACTERISTIC_NOTIFY = "f000ffc1-0451-4000-b000-000000000000"
CHARACTERISTIC_WRITE = "f000ffc2-0451-4000-b000-000000000000"

# UUID activo (cambia automáticamente al conectar según lo que encuentre)
SERVICE_UUID        = SERVICE_UUID_TI
CHARACTERISTIC_UUID = CHARACTERISTIC_NOTIFY

# ─── Protocolo de paquetes ────────────────────────────────────────────────────
# Estructura del paquete recibido (bytes):
#   [0]     → Cabecera / tipo de mensaje
#   [1]     → Flags (bit 1: peso estabilizado, bit 2: medición con impedancia)
#   [2]     → Unidades (0x00=kg, 0x01=lb, 0x02=jin)
#   [3][4]  → Peso bruto (big-endian, dividir entre 100 para obtener kg)
#   [5]..   → Datos de impedancia y otros (ignorados aquí)
#   [N-1]   → Checksum (XOR de todos los bytes anteriores)

HEADER_MEASUREMENT = 0x10  # Cabecera de paquete de medición en tiempo real
FLAG_WEIGHT_STABLE  = 0x02  # El peso está estabilizado (lectura final)

INIT_COMMANDS = [
    # Handshake de 7 bytes: Crítico para modelos Renpho 2024/2025
    ("Handshake Sincro", bytearray([0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x01])),
    ("Renpho TI estándar", bytearray([0xFE, 0xFF, 0x30, 0x31])),
    ("Renpho TI v2",       bytearray([0xFF, 0xFF, 0x00, 0x00])),
    ("Solicitar peso",     bytearray([0x10, 0x00, 0x00, 0x00, 0x10])),
]

def parse_weight(data: bytearray, debug: bool = False) -> tuple:
    """Parsea el paquete de bytes de la báscula."""
    if len(data) < 5:
        return None, False, ""

    header = data[0]
    # Ampliamos los headers válidos (incluimos 0x01 y 0x02 que son comunes en TI)
    VALID_HEADERS = {0x10, 0x12, 0x1C, 0x01, 0x02}
    
    if header not in VALID_HEADERS:
        if debug: print(f" 🔍 Header ignorado: {header:#04x}")
        return None, False, ""

    # Validar Checksum (XOR)
    checksum = 0
    for b in data[:-1]:
        checksum ^= b
    if checksum != data[-1]:
        if debug: print(f" ⚠️ Checksum inválido en paquete: {data.hex()}")
        return None, False, ""

    flags = data[1]
    unit_byte = data[2]
    # Peso en bytes [3] y [4] (Big Endian)
    raw_weight = struct.unpack(">H", data[3:5])[0]
    
    weight_kg = raw_weight / 100.0
    stabilized = bool(flags & 0x02) # El bit 2 suele indicar peso fijo
    
    units = {0x00: "kg", 0x01: "lb", 0x02: "jin"}
    unit_str = units.get(unit_byte, "kg")

    return weight_kg, stabilized, unit_str

async def read_weight(mac: str, debug: bool = False):
    """Conexión forzada para modelos rebeldes."""
    
    def notification_handler(sender, data: bytearray):
        # Si llega CUALQUIER cosa, la imprimimos para saber que hay vida
        print(f" 📨 [DATOS RECIBIDOS]: {data.hex()}")
        weight, stable, unit = parse_weight(data, debug)
        if weight is not None:
            status = "✅ [FIJO]" if stable else "⏳ [MIDIENDO]"
            print(f" ⚖️  Peso: {weight:.2f} {unit} {status}")

    print(f"🔗 Conectando a {mac}...")
    try:
        # 1. Conexión con un tiempo de espera mayor
        async with BleakClient(mac, timeout=20.0) as client:
            print(f"✅ Conectado. Enviando ráfaga de activación...")

            # 2. ENVIAR COMANDOS ANTES DE SUSCRIBIR (Estrategia Renpho TI)
            # Probamos el comando de 7 bytes y el estándar
            comandos_fuerza = [
                bytearray([0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x01]),
                bytearray([0xFE, 0xFF, 0x30, 0x31]),
                bytearray([0xFD])
            ]
            
            for cmd in comandos_fuerza:
                await client.write_gatt_char(CHARACTERISTIC_WRITE, cmd, response=False)
                await asyncio.sleep(0.2)

            # 3. SUSCRIBIRSE JUSTO DESPUÉS
            await client.start_notify(CHARACTERISTIC_NOTIFY, notification_handler)
            print(f"📡 Escuchando... (Sube a la báscula AHORA)")

            # 4. MANTENER VIVA LA CONEXIÓN
            # Enviamos un "ping" cada 2 segundos para que no se duerma
            while client.is_connected:
                await client.write_gatt_char(CHARACTERISTIC_WRITE, bytearray([0xFD]), response=False)
                await asyncio.sleep(2.0)

    except Exception as e:
        print(f"❌ Error: {e}")
# ─── MODO ESCANEO ─────────────────────────────────────────────────────────────

async def scan_for_scale(timeout: float = 10.0):
    """Busca la báscula ES-26BB-B y muestra su dirección MAC."""
    print(f"🔍 Buscando dispositivo BLE '{DEVICE_NAME}' por {timeout}s...\n")
    print("   (Sube a la báscula para que empiece a emitir señal BLE)\n")

    found = []

    def detection_callback(device, advertisement_data):
        name = device.name or advertisement_data.local_name or ""
        if DEVICE_NAME in name and device.address not in [d.address for d in found]:
            found.append(device)
            print(f"   ✅ Encontrado: {device.name}")
            print(f"      MAC: {device.address}")
            print(f"      RSSI: {advertisement_data.rssi} dBm\n")

    scanner = BleakScanner(detection_callback=detection_callback)
    await scanner.start()
    await asyncio.sleep(timeout)
    await scanner.stop()

    if not found:
        print("❌ No se encontró ningún dispositivo 'ES-26BB-B'.")
        print("   Asegúrate de:")
        print("   1. Subir a la báscula para activarla")
        print("   2. Que el Bluetooth de tu computador esté encendido")
        print("   3. Que ninguna otra app esté conectada a la báscula")
    else:
        print(f"✅ Total encontrados: {len(found)}")
        print(f"   Usa la MAC para conectar: --mac {found[0].address}")


# ─── MODO DESCUBRIMIENTO ──────────────────────────────────────────────────────

async def discover_services(mac: str):
    """Lista todos los servicios y características del dispositivo."""
    print(f"🔬 Descubriendo servicios de {mac}...\n")

    async with BleakClient(mac, timeout=15.0) as client:
        print(f"✅ Conectado\n")
        for service in client.services:
            print(f"  📦 Servicio: {service.uuid}")
            print(f"             {service.description}")
            for char in service.characteristics:
                props = ", ".join(char.properties)
                print(f"     🔑 Char: {char.uuid}  [{props}]")
                print(f"            {char.description}")
                # Leer valor si es readable
                if "read" in char.properties:
                    try:
                        value = await client.read_gatt_char(char.uuid)
                        print(f"            Valor: {value.hex()} ({list(value)})")
                    except Exception:
                        pass
            print()


# ─── COMANDOS DE ACTIVACIÓN CONOCIDOS ────────────────────────────────────────
# Distintos firmwares Renpho/TI usan distintos handshakes de inicio.
# La báscula solo responde al comando correcto; los demás son ignorados.
INIT_COMMANDS = [
    # Nombre descriptivo          bytes del comando
    ("Renpho TI estándar",        bytearray([0xFE, 0xFF, 0x30, 0x31])),
    ("Renpho TI v2",              bytearray([0xFF, 0xFF, 0x00, 0x00])),
    ("Renpho TI solicitar peso",  bytearray([0x10, 0x00, 0x00, 0x00, 0x10])),
    ("Renpho TI ping",            bytearray([0x02, 0x26, 0x20, 0x00, 0x04])),
    ("Renpho timestamp",          bytearray([0x02, 0x21, 0x10, 0x00, 0x33])),
    ("Byte único 0x01",           bytearray([0x01])),
    ("Byte único 0xFD",           bytearray([0xFD])),
]


# ─── MODO PRUEBA DE COMANDOS (--probe) ────────────────────────────────────────

async def probe_commands(mac: str):
    """
    Estrategia correcta para básculas con timeout de inactividad:
    1. Conectar PRIMERO mientras la báscula está encendida (con peso encima)
    2. Suscribirse inmediatamente
    3. Disparar todos los comandos en ráfaga rápida (<0.5s total)
    4. Esperar paquetes

    La clave es que el usuario debe subir a la báscula ANTES de ejecutar
    este comando, y quedarse quieto durante toda la prueba (~20 segundos).
    """
    print("=" * 62)
    print("🔬  MODO PROBE — Detección de protocolo Renpho")
    print("=" * 62)
    print()
    print("  ⚠️  INSTRUCCIONES IMPORTANTES:")
    print("  1. Sube a la báscula y quédate parado sobre ella")
    print("  2. Mueve el peso ligeramente cada 3-4 segundos para")
    print("     evitar que se apague (cambia el peso de un pie al otro)")
    print("  3. Pulsa ENTER cuando estés listo")
    print()
    input("  ▶ Pulsa ENTER para comenzar...")
    print()

    all_packets   = []
    connect_ok    = False

    def capture(sender, data: bytearray):
        p = bytearray(data)
        all_packets.append(p)
        print(f"  🟢 PAQUETE RECIBIDO: {p.hex()}  {list(p)}")

    print("🔗 Conectando...")
    try:
        async with BleakClient(mac, timeout=20.0) as client:
            connect_ok = True
            print(f"✅ Conectado\n")

            # ── Activar notificaciones ────────────────────────────────────────
            await _write_cccd_manually(client, CHARACTERISTIC_NOTIFY)
            await client.start_notify(CHARACTERISTIC_NOTIFY, capture)
            print(f"📡 Notify activo en {CHARACTERISTIC_NOTIFY}")

            # ── Fase 0: ¿llegan datos sin enviar nada? ────────────────────────
            print(f"\n[Fase 0] Esperando datos espontáneos (3s)...")
            print(f"         (sigue moviéndote sobre la báscula)")
            await asyncio.sleep(3.0)
            phase0_count = len(all_packets)
            if phase0_count:
                print(f"  ✅ ¡La báscula transmite sola! {phase0_count} paquetes recibidos.")
                print(f"  No necesitas comando de activación.")
                await client.stop_notify(CHARACTERISTIC_NOTIFY)
                _print_probe_summary(all_packets, mac, None)
                return

            print(f"  — Sin datos espontáneos. Probando comandos en ráfaga...")

            # ── Fase 1: enviar TODOS los comandos en ráfaga rápida ───────────
            # La báscula puede apagarse pronto; enviamos todo a máxima velocidad
            print(f"\n[Fase 1] Disparando {len(INIT_COMMANDS)} comandos en ráfaga...")
            winning_cmd = None
            for name, cmd in INIT_COMMANDS:
                try:
                    await client.write_gatt_char(CHARACTERISTIC_WRITE, cmd, response=False)
                    print(f"  📤 {name}: {cmd.hex()}")
                    await asyncio.sleep(0.1)
                    if len(all_packets) > 0:
                        winning_cmd = (name, cmd)
                        print(f"  ✅ Paquetes recibidos tras '{name}'!")
                        break
                except Exception as e:
                    print(f"  ✗ {name}: {e}")
                    break  # báscula desconectada

            # ── Fase 2: esperar más paquetes ──────────────────────────────────
            print(f"\n[Fase 2] Esperando paquetes adicionales (10s)...")
            print(f"         (sigue moviéndote sobre la báscula)")
            for t in range(10):
                await asyncio.sleep(1.0)
                count = len(all_packets)
                if count > 0:
                    print(f"  ⚖  {count} paquetes hasta ahora...")

            try:
                await client.stop_notify(CHARACTERISTIC_NOTIFY)
            except Exception:
                pass

    except Exception as e:
        print(f"❌ Error de conexión: {e}")
        if not connect_ok:
            print("   Asegúrate de estar sobre la báscula al ejecutar el comando.")
        return

    _print_probe_summary(all_packets, mac, winning_cmd)


def _print_probe_summary(packets: list, mac: str, winning_cmd):
    print(f"\n{'═' * 62}")
    if packets:
        print(f"✅ Total paquetes capturados: {len(packets)}")
        print(f"\n   Bytes crudos (cópialos y compártelos):")
        for i, p in enumerate(packets, 1):
            print(f"   [{i:02d}] {p.hex()}  →  {list(p)}")
        if winning_cmd:
            print(f"\n   Comando que despertó la báscula: '{winning_cmd[0]}'  {winning_cmd[1].hex()}")
    else:
        print(f"❌ No se capturó ningún paquete.")
        print()
        print(f"   Posibles causas:")
        print(f"   A) La báscula se apagó antes de conectar — necesitas moverte")
        print(f"      activamente mientras corres el script")
        print(f"   B) El protocolo de handshake es diferente a los conocidos")
        print()
        print(f"   Próximo paso recomendado:")
        print(f"   Instala 'nRF Connect' en tu celular Android, conéctate a la")
        print(f"   báscula desde la app de Renpho, y luego usa nRF Connect para")
        print(f"   ver el log BLE (Log → Export). Comparte ese archivo.")
    print(f"{'═' * 62}")



async def _write_cccd_manually(client: BleakClient, char_uuid: str):
    """
    Escribe 0x0100 en el descriptor CCCD (2902) de la característica.
    En Windows con chips TI, bleak a veces no activa las notificaciones
    automáticamente — esto lo fuerza manualmente.
    """
    try:
        for service in client.services:
            for char in service.characteristics:
                if char.uuid == char_uuid:
                    for descriptor in char.descriptors:
                        if descriptor.uuid.startswith("00002902"):
                            await client.write_gatt_descriptor(
                                descriptor.handle,
                                bytearray([0x01, 0x00])  # Enable notifications
                            )
                            return  # éxito silencioso
    except Exception:
        pass  # si falla, start_notify lo intentará por su cuenta



# ─── MODO LECTURA CONTINUA ────────────────────────────────────────────────────

async def read_weight(mac: str, debug: bool = False):
    """Conecta a la báscula y lee el peso en tiempo real."""

    last_weight = None
    reading_count = 0

    def notification_handler(sender, data: bytearray):
        nonlocal last_weight, reading_count
        reading_count += 1

        if debug:
            print(f"  📨 Raw [{sender}]: {data.hex()}  {list(data)}")

        weight_kg, stabilized, unit_str = parse_weight(data, debug=debug)

        if weight_kg is None:
            if debug:
                print(f"  📦 Paquete [{data.hex()}] — tipo no reconocido como peso")
            return

        last_weight = weight_kg
        status = "✅ ESTABILIZADO" if stabilized else "⏳ midiendo..."
        print(f"  ⚖  {weight_kg:.2f} kg  ({unit_str} bruto)  {status}")

    print(f"🔗 Conectando a {mac}...")
    print(f"   (Sube a la báscula para activar la medición)\n")

    async with BleakClient(mac, timeout=15.0) as client:
        print(f"✅ Conectado\n")

        # ── Auto-detección del servicio disponible ────────────────────────────
        available_services = [s.uuid for s in client.services]

        if SERVICE_UUID_TI in available_services:
            active_notify = CHARACTERISTIC_NOTIFY
            active_write  = CHARACTERISTIC_WRITE
            print(f"📡 Usando servicio TI propietario (f000ffc0...)")
        elif SERVICE_UUID_CLASSIC in available_services:
            active_notify = CHARACTERISTIC_UUID_CLASSIC
            active_write  = None
            print(f"📡 Usando servicio clásico FFE0...")
        else:
            print(f"⚠️  No se encontró ningún servicio conocido.")
            for s in client.services:
                print(f"     {s.uuid}  ({s.description})")
            print(f"\n   Ejecuta --discover o --probe para diagnosticar.")
            return

        # ── Suscribirse ANTES de enviar comandos ──────────────────────────────
        # En Windows + chipset TI, forzar CCCD manualmente garantiza notificaciones
        await _write_cccd_manually(client, active_notify)
        await client.start_notify(active_notify, notification_handler)
        print(f"📡 Suscrito a notificaciones en {active_notify}")

        # ── Enviar todos los comandos de inicio conocidos ─────────────────────
        # No sabemos cuál es el correcto para este firmware, así que los
        # enviamos todos con una pequeña pausa entre ellos. El incorrecto
        # es ignorado; el correcto despierta la báscula.
        if active_write:
            print(f"📤 Enviando comandos de activación...")
            for name, cmd in INIT_COMMANDS:
                try:
                    await client.write_gatt_char(active_write, cmd, response=False)
                    if debug:
                        print(f"   → {name}: {cmd.hex()}")
                    await asyncio.sleep(0.15)
                except Exception as e:
                    if debug:
                        print(f"   ✗ {name}: {e}")
                    break  # si falla, la báscula se desconectó — salir del loop

        print(f"   Peso en tiempo real (Ctrl+C para salir):\n")

        try:
            while True:
                await asyncio.sleep(1.0)
        except KeyboardInterrupt:
            print(f"\n\n🛑 Detenido. Total de paquetes recibidos: {reading_count}")
            if last_weight:
                print(f"   Último peso registrado: {last_weight:.2f} kg")

        await client.stop_notify(active_notify)


# ─── PUNTO DE ENTRADA ─────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Lector BLE para báscula Renpho ES-26BB-B",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  Buscar la báscula y obtener su MAC:
    python renpho_es26bb_weight.py --scan

  Leer peso en tiempo real:
    python renpho_es26bb_weight.py --mac AA:BB:CC:DD:EE:FF

  Ver todos los servicios BLE del dispositivo:
    python renpho_es26bb_weight.py --mac AA:BB:CC:DD:EE:FF --discover

  Probar comandos de activación (si no llegan datos):
    python renpho_es26bb_weight.py --mac AA:BB:CC:DD:EE:FF --probe

  Diagnóstico con bytes crudos:
    python renpho_es26bb_weight.py --mac AA:BB:CC:DD:EE:FF --debug
        """
    )
    parser.add_argument("--scan",    action="store_true", help="Escanear y mostrar dispositivos cercanos")
    parser.add_argument("--mac",     type=str,            help="Dirección MAC de la báscula")
    parser.add_argument("--discover",action="store_true", help="Listar todos los servicios/características")
    parser.add_argument("--probe",   action="store_true", help="Probar todos los comandos de activación (diagnóstico)")
    parser.add_argument("--timeout", type=float, default=10.0, help="Tiempo de escaneo en segundos (default: 10)")
    parser.add_argument("--debug",   action="store_true", help="Mostrar paquetes BLE crudos (útil para diagnóstico)")
    args = parser.parse_args()

    if args.scan:
        asyncio.run(scan_for_scale(args.timeout))
    elif args.mac and args.discover:
        asyncio.run(discover_services(args.mac))
    elif args.mac and args.probe:
        asyncio.run(probe_commands(args.mac))
    elif args.mac:
        asyncio.run(read_weight(args.mac, debug=args.debug))
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
