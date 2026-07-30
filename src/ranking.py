"""
Sistema de puntuación de promociones.

Da más prioridad a las promociones que mejor encajan
con los criterios de búsqueda.
"""


def calculate_score(promotion):
    score = 0

    city = str(promotion.get("city") or "").lower()
    bedrooms = promotion.get("bedrooms")
    penthouse = promotion.get("penthouse", False)
    price = promotion.get("price")
    title = str(promotion.get("title") or "").lower()

    # Madrid capital
    if "madrid" in city:
        score += 30

    # Cuatro dormitorios
    if bedrooms == 4:
        score += 40
    elif bedrooms and bedrooms > 4:
        score += 30

    # Ático
    if penthouse or "ático" in title or "atico" in title:
        score += 100

    # Precio disponible
    if price is not None:
        score += 10

    return score


def get_priority(score):
    if score >= 150:
        return "PRIORIDAD MÁXIMA"
    if score >= 100:
        return "PRIORIDAD ALTA"
    if score >= 60:
        return "PRIORIDAD MEDIA"

    return "PRIORIDAD NORMAL"