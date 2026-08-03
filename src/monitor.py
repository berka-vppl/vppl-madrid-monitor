"""
Radar de vivienda protegida en Madrid.
"""

from config import (
    TARGET_CITY,
    PREFERRED_BEDROOMS,
    PENTHOUSE_PRIORITY,
    CHECK_INTERVAL_HOURS,
)

from database_manager import (
    create_database,
    promotion_exists,
    save_promotion,
    total_promotions,
)

from ranking import calculate_score, get_priority
from scraper_manager import get_all_promotions
from telegram_notifier import create_promotion_message, send_telegram_message
from alert_logger import log_promotion_alert


def main():
    print("=" * 45)
    print("        RADAR VIVIENDA MADRID")
    print("             Versión 0.1")
    print("=" * 45)
    print()

    print("Configuración cargada correctamente")
    print(f"Ciudad: {TARGET_CITY}")
    print(f"Dormitorios preferidos: {PREFERRED_BEDROOMS}")
    print(f"Prioridad áticos: {PENTHOUSE_PRIORITY}")
    print(f"Comprobación cada {CHECK_INTERVAL_HOURS} horas")
    print()

    create_database()

    promotions = get_all_promotions()

    # Calculamos la puntuación de todas las promociones.
    for promotion in promotions:
        promotion["score"] = calculate_score(promotion)
        promotion["priority"] = get_priority(promotion["score"])

    # Ordenamos de mayor a menor puntuación.
    promotions.sort(key=lambda promotion: promotion["score"], reverse=True)

    print(f"Promociones encontradas: {len(promotions)}")

    for promotion in promotions:
        score = promotion["score"]
        priority = promotion["priority"]

        if not promotion_exists(promotion["id"]):
            save_promotion(promotion)
            log_promotion_alert(promotion)

            message = create_promotion_message(promotion)
            send_telegram_message(message)

            print(
                f"Nueva promoción: {promotion['title']} "
                f"| {priority} | {score} puntos"
            )
        else:
            print(
                f"Ya existe: {promotion['title']} "
                f"| {priority} | {score} puntos"
            )

    print(f"Total en la base de datos: {total_promotions()}")
    print("Sistema iniciado correctamente.")


if __name__ == "__main__":
    main()
