"""
Scraper base

Versión 0.2
"""

def search_promotions():

    print("Buscando promociones...")

    promotions = [

        {
            "id": "promo001",
            "title": "Residencial Las Rosas",
            "city": "Madrid",
            "bedrooms": 4,
            "penthouse": True,
            "price": 420000
        },

        {
            "id": "promo002",
            "title": "Residencial Valdebebas",
            "city": "Madrid",
            "bedrooms": 3,
            "penthouse": False,
            "price": 365000
        }

    ]

    return promotions