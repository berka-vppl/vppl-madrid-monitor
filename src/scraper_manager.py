"""
Gestor de scrapers.

Centraliza todos los scrapers disponibles.
"""

from concurrent.futures import ThreadPoolExecutor, as_completed

from scrapers.idealista_scraper import search_promotions as search_idealista
from scrapers.ibosa_scraper import search_promotions as search_ibosa


def get_all_promotions():
    promotions = []

    scrapers = [
        ("Idealista", search_idealista),
        ("Ibosa", search_ibosa),
    ]

    with ThreadPoolExecutor(max_workers=len(scrapers)) as executor:

        futures = {
            executor.submit(scraper_function): scraper_name
            for scraper_name, scraper_function in scrapers
        }

        for future in as_completed(futures):

            scraper_name = futures[future]

            try:
                scraper_promotions = future.result()

                print(
                    f"{scraper_name}: "
                    f"{len(scraper_promotions)} promociones encontradas."
                )

                promotions.extend(scraper_promotions)

            except Exception as error:
                print(f"Error en el scraper de {scraper_name}: {error}")

    print()
    print("=" * 45)
    print("RESUMEN DE LA BÚSQUEDA")
    print("=" * 45)
    print(f"Total de promociones encontradas: {len(promotions)}")
    print()

    return promotions