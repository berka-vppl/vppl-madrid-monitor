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

from scrapers.idealista_scraper import search_promotions


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

    promotions = search_promotions()

    print(f"Promociones encontradas: {len(promotions)}")

    for promotion in promotions:
        if not promotion_exists(promotion["id"]):
            save_promotion(promotion)
            print(f"Nueva promoción: {promotion['title']}")
        else:
            print(f"Ya existe: {promotion['title']}")

    print(f"Total en la base de datos: {total_promotions()}")

    print("Sistema iniciado correctamente.")


if __name__ == "__main__":
    main()