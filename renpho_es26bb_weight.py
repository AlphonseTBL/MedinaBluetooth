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
SERVICE_UUID         = "0000ffe0-0000-1000-8000-00805f9b34fb"
CHARACTERISTIC_UUID  = "0000ffe1-0000-1000-8000-00805f9b34fb"

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


def parse_weight(data: bytearray) -> tuple[float | None, bool, str]:
    """
    Parsea un paquete BLE de la báscula.

    Returns:
        (peso_kg, estabilizado, unidad_str)
        Devuelve (None, False, '') si el paquete no es de peso.
    """
    if len(data) < 5:
        return None, False, ""

    header = data[0]
    if header != HEADER_MEASUREMENT:
        return None, False, ""

    # Validar checksum (XOR de todos los bytes menos el último)
    checksum = 0
    for b in data[:-1]:
        checksum ^= b
    if checksum != data[-1]:
        print(f"  ⚠ Checksum inválido: esperado {checksum:#04x}, recibido {data[-1]:#04x}")
        return None, False, ""

    flags      = data[1]
    unit_byte  = data[2]
    raw_weight = struct.unpack(">H", data[3:5])[0]  # big-endian unsigned short

    weight_kg  = raw_weight / 100.0
    stabilized = bool(flags & FLAG_WEIGHT_STABLE)

    units = {0x00: "kg", 0x01: "lb", 0x02: "斤"}
    unit_str = units.get(unit_byte, f"?({unit_byte:#04x})")

    # Convertir a kg si la báscula está en otra unidad
    if unit_byte == 0x01:   # libras → kg
        weight_kg = round(weight_kg * 0.453592, 2)
    elif unit_byte == 0x02: # jin → kg
        weight_kg = round(weight_kg * 0.5, 2)

    return weight_kg, stabilized, unit_str


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


# ─── MODO LECTURA CONTINUA ────────────────────────────────────────────────────

async def read_weight(mac: str):
    """Conecta a la báscula y lee el peso en tiempo real."""

    last_weight = None
    reading_count = 0

    def notification_handler(sender, data: bytearray):
        nonlocal last_weight, reading_count
        reading_count += 1

        weight_kg, stabilized, unit_str = parse_weight(data)

        if weight_kg is None:
            # Paquete de otro tipo (ej. batería, confirmación offline, etc.)
            print(f"  📦 Paquete [{data.hex()}] — tipo no reconocido como peso")
            return

        last_weight = weight_kg
        status = "✅ ESTABILIZADO" if stabilized else "⏳ midiendo..."
        print(f"  ⚖  {weight_kg:.2f} kg  ({unit_str} bruto)  {status}")

    print(f"🔗 Conectando a {mac}...")
    print(f"   (Sube a la báscula para activar la medición)\n")

    async with BleakClient(mac, timeout=15.0) as client:
        print(f"✅ Conectado\n")

        # Verificar que el servicio y la característica existen
        services = [s.uuid for s in client.services]
        if SERVICE_UUID not in services:
            print(f"⚠️  El servicio {SERVICE_UUID} no se encontró.")
            print(f"   Ejecuta --discover para ver los servicios disponibles.")
            return

        # Suscribirse a notificaciones
        await client.start_notify(CHARACTERISTIC_UUID, notification_handler)
        print(f"📡 Suscrito a notificaciones en {CHARACTERISTIC_UUID}")
        print(f"   Peso en tiempo real (Ctrl+C para salir):\n")

        try:
            while True:
                await asyncio.sleep(1.0)
        except KeyboardInterrupt:
            print(f"\n\n🛑 Detenido. Total de paquetes recibidos: {reading_count}")
            if last_weight:
                print(f"   Último peso registrado: {last_weight:.2f} kg")

        await client.stop_notify(CHARACTERISTIC_UUID)


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
        """
    )
    parser.add_argument("--scan",    action="store_true", help="Escanear y mostrar dispositivos cercanos")
    parser.add_argument("--mac",     type=str,            help="Dirección MAC de la báscula")
    parser.add_argument("--discover",action="store_true", help="Listar todos los servicios/características")
    parser.add_argument("--timeout", type=float, default=10.0, help="Tiempo de escaneo en segundos (default: 10)")
    args = parser.parse_args()

    if args.scan:
        asyncio.run(scan_for_scale(args.timeout))
    elif args.mac and args.discover:
        asyncio.run(discover_services(args.mac))
    elif args.mac:
        asyncio.run(read_weight(args.mac))
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
