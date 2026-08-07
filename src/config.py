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

DATABASE_DIR.mkdir(exist_ok=True)
LOG_DIR.mkdir(exist_ok=True)


# Base de datos

DATABASE_FILE = DATABASE_DIR / "promotions.db"


# Configuración

CHECK_INTERVAL_HOURS = 6


# Ciudad objetivo

TARGET_CITY = "Madrid"


# Tipos de vivienda protegida incluidos en el radar

TARGET_PROTECTION_TYPES = (
    "VPPL",
    "VPPB",
)


# Preferencias principales

PREFERRED_BEDROOMS = 4

PENTHOUSE_PRIORITY = True


# Preferencia por tipo de protección

PREFERRED_PROTECTION_TYPE = "VPPL"


# Puntuaciones adicionales por tipo de protección

VPPL_BONUS = 20
VPPB_BONUS = 10


# Las credenciales se leen de las variables:
#
# TELEGRAM_BOT_TOKEN
# TELEGRAM_CHAT_ID
#
# Nunca deben guardarse en el repositorio.