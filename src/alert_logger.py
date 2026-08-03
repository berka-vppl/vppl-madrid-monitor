"""
Registro local de nuevas promociones detectadas.
"""

from datetime import datetime
from pathlib import Path


LOG_DIRECTORY = Path(__file__).resolve().parent.parent / "logs"
ALERT_LOG_PATH = LOG_DIRECTORY / "alerts.log"


def log_promotion_alert(promotion):
    """
    Guarda en un archivo de texto una promoción nueva detectada.
    """

    LOG_DIRECTORY.mkdir(exist_ok=True)

    detected_at = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

    title = promotion.get("title", "Promoción sin nombre")
    source = promotion.get("source", "Fuente no indicada")
    city = promotion.get("city", "Madrid")
    bedrooms = promotion.get("bedrooms", "No indicados")
    penthouse = "Sí" if promotion.get("penthouse", False) else "No"
    score = promotion.get("score", 0)
    priority = promotion.get("priority", "PRIORIDAD NORMAL")
    url = promotion.get("url", "Sin enlace")

    entry = (
        f"{'=' * 60}\n"
        f"FECHA DE DETECCIÓN: {detected_at}\n\n"
        f"NUEVA PROMOCIÓN\n\n"
        f"Nombre: {title}\n"
        f"Ciudad: {city}\n"
        f"Fuente: {source}\n"
        f"Dormitorios: {bedrooms}\n"
        f"Áticos: {penthouse}\n"
        f"Prioridad: {priority}\n"
        f"Puntuación: {score} puntos\n"
        f"Enlace: {url}\n"
        f"{'=' * 60}\n\n"
    )

    with ALERT_LOG_PATH.open("a", encoding="utf-8") as log_file:
        log_file.write(entry)

    print(f"Alerta guardada en: {ALERT_LOG_PATH}")
