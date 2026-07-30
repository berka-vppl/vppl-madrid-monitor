"""
Radar Vivienda Madrid
Versión 0.1
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

from scraper_manager import get_all_promotions

 for promotion in promotions:
        score = calculate_score(promotion)
        priority = get_priority(score)

        promotion["score"] = score
        promotion["priority"] = priority

        if not promotion_exists(promotion["id"]):
            save_promotion(promotion)
            print(
                f"Nueva promoción: {promotion['title']} "
                f"| {priority} | {score} puntos"
            )
        else:
            print(
                f"Ya existe: {promotion['title']} "
                f"| {priority} | {score} puntos"
            )

    print("Sistema iniciado correctamente.")


def main():
    print("=" * 45)
    print("        RADAR VIVIENDA MADRID")
    print("            Versión 0.1")
    print("=" * 45)
    print()

    print("Configuración cargada correctamente")
    print(f"Ciudad: {TARGET_CITY}")
    print(f"Dormitorios preferidos: {PREFERRED_BEDROOMS}")
    print(f"Prioridad áticos: {PENTHOUSE_PRIORITY}")
    print(f"Comprobación cada {CHECK_INTERVAL_HOURS} horas")
    print()

    create_database()

    promotions = []

    promotions = get_all_promotions()

    print(f"Promociones encontradas: {len(promotions)}")

    


if __name__ == "__main__":
    main()