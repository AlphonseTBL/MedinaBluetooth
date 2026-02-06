#!/usr/bin/env python3
"""
Script de instalación y verificación para la aplicación Monitor Bluetooth.
Ejecuta este script para verificar que todas las dependencias estén instaladas correctamente.
"""

import sys
import subprocess
import platform

def print_header(text):
    """Imprime un encabezado formateado."""
    print("\n" + "=" * 60)
    print(f"  {text}")
    print("=" * 60 + "\n")

def check_python_version():
    """Verifica que la versión de Python sea compatible."""
    print_header("Verificando versión de Python")
    
    version = sys.version_info
    print(f"Versión de Python: {version.major}.{version.minor}.{version.micro}")
    
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ ERROR: Se requiere Python 3.8 o superior")
        return False
    else:
        print("✓ Versión de Python compatible")
        return True

def check_dependencies():
    """Verifica que las dependencias estén instaladas."""
    print_header("Verificando dependencias")
    
    dependencies = [
        ('customtkinter', 'CustomTkinter'),
        ('bluetooth', 'PyBluez')
    ]
    
    all_installed = True
    
    for module_name, package_name in dependencies:
        try:
            __import__(module_name)
            print(f"✓ {package_name} está instalado")
        except ImportError:
            print(f"❌ {package_name} NO está instalado")
            all_installed = False
    
    return all_installed

def install_dependencies():
    """Intenta instalar las dependencias faltantes."""
    print_header("Instalando dependencias")
    
    print("Ejecutando: pip install -r requirements.txt")
    
    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
        ])
        print("\n✓ Dependencias instaladas exitosamente")
        return True
    except subprocess.CalledProcessError:
        print("\n❌ Error al instalar dependencias")
        print("Intenta instalar manualmente con: pip install -r requirements.txt")
        return False

def check_bluetooth():
    """Verifica el soporte de Bluetooth del sistema."""
    print_header("Verificando soporte de Bluetooth")
    
    system = platform.system()
    print(f"Sistema operativo: {system}")
    
    if system == "Linux":
        print("\nEn Linux, asegúrate de tener instalado:")
        print("  - bluetooth")
        print("  - libbluetooth-dev")
        print("\nComandos de instalación:")
        print("  Ubuntu/Debian: sudo apt-get install bluetooth libbluetooth-dev")
        print("  Fedora: sudo dnf install bluez bluez-libs bluez-libs-devel")
        
    elif system == "Windows":
        print("\nEn Windows, asegúrate de:")
        print("  - Tener Bluetooth habilitado en la configuración del sistema")
        print("  - Tener los drivers de Bluetooth instalados")
        print("  - Puede ser necesario instalar Build Tools para Visual Studio")
        
    elif system == "Darwin":  # macOS
        print("\nEn macOS, el soporte de Bluetooth debería estar disponible")
        print("Si tienes problemas, actualiza Xcode Command Line Tools")
    
    return True

def create_config():
    """Crea el archivo de configuración si no existe."""
    print_header("Configuración inicial")
    
    import os
    
    if os.path.exists("config.json"):
        print("✓ El archivo config.json ya existe")
        return True
    
    print("Creando archivo de configuración por defecto...")
    
    try:
        from src.config import Config
        config = Config()
        config.create_default_config_file()
        print("✓ Archivo config.json creado exitosamente")
        return True
    except Exception as e:
        print(f"❌ Error al crear configuración: {e}")
        return False

def main():
    """Función principal del script de instalación."""
    print_header("Instalación de Monitor Bluetooth")
    print("Este script verificará y configurará tu entorno\n")
    
    # Verificar Python
    if not check_python_version():
        print("\nPor favor, instala Python 3.8 o superior y vuelve a ejecutar este script.")
        sys.exit(1)
    
    # Verificar dependencias
    dependencies_ok = check_dependencies()
    
    if not dependencies_ok:
        response = input("\n¿Deseas instalar las dependencias ahora? (s/n): ")
        if response.lower() in ['s', 'si', 'sí', 'y', 'yes']:
            if not install_dependencies():
                print("\nNo se pudieron instalar todas las dependencias.")
                print("Por favor, revisa los errores e intenta instalar manualmente.")
                sys.exit(1)
        else:
            print("\nDebes instalar las dependencias antes de ejecutar la aplicación.")
            print("Ejecuta: pip install -r requirements.txt")
            sys.exit(1)
    
    # Verificar Bluetooth
    check_bluetooth()
    
    # Crear configuración
    create_config()
    
    # Resumen final
    print_header("Instalación completada")
    print("Todo está listo para usar la aplicación!")
    print("\nPara ejecutar la aplicación:")
    print("  python main.py")
    print("\nPara más información, consulta README.md")
    print("Para guía de usuario, consulta docs/user_guide.md")
    print()

if __name__ == "__main__":
    main()
