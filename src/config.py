"""
Radar Vivienda Madrid
Configuración general del proyecto
"""

from pathlib import Path

# Carpeta raíz del proyecto
ROOT_DIR = Path(__file__).resolve().parent.parent

# Directorios principales
CONFIG_DIR = ROOT_DIR / "config"
DATABASE_DIR = ROOT_DIR / "database"
LOG_DIR = ROOT_DIR / "logs"

# Crear carpetas si no existen
LOG_DIR.mkdir(exist_ok=True)

# Base de datos
DATABASE_FILE = DATABASE_DIR / "promotions.db"

# Configuración
CHECK_INTERVAL_HOURS = 6

# Prioridades del usuario
TARGET_CITY = "Madrid"

PREFERRED_BEDROOMS = 4

PENTHOUSE_PRIORITY = True
