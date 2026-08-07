"""
Sistema de puntuación de promociones.

Da más prioridad a las promociones que mejor encajan
con los criterios de búsqueda.
"""

import re

from .config import (
    PREFERRED_BEDROOMS,
    PENTHOUSE_PRIORITY,
    VPPL_BONUS,
    VPPB_BONUS,
)


def _detect_protection_type(promotion):
    """
    Intenta identificar si la promoción es
    VPPL, VPPB o VPP genérica.
    """

    explicit_type = promotion.get(
        "protection_type"
    )

    if explicit_type:
        return str(
            explicit_type
        ).upper()

    title = str(
        promotion.get("title")
        or ""
    )

    description = str(
        promotion.get("description")
        or ""
    )

    text = (
        f"{title} {description}"
    ).casefold()

    if re.search(
        r"\bvppl\b",
        text,
    ):
        return "VPPL"

    if re.search(
        r"\bvppb\b",
        text,
    ):
        return "VPPB"

    if (
        "precio limitado"
        in text
    ):
        return "VPPL"

    if (
        "precio básico"
        in text
        or "precio basico"
        in text
    ):
        return "VPPB"

    if re.search(
        r"\bvpp\b",
        text,
    ):
        return "VPP"

    if (
        "vivienda protegida"
        in text
        or "protección pública"
        in text
        or "proteccion publica"
        in text
    ):
        return "VPP"

    return None


def calculate_score(promotion):
    """
    Calcula la puntuación de una promoción.
    """

    score = 0

    city = str(
        promotion.get("city")
        or ""
    ).casefold()

    bedrooms = promotion.get(
        "bedrooms"
    )

    penthouse = promotion.get(
        "penthouse",
        False,
    )

    price = promotion.get(
        "price"
    )

    title = str(
        promotion.get("title")
        or ""
    ).casefold()

    protection_type = (
        _detect_protection_type(
            promotion
        )
    )

    # Madrid capital
    if "madrid" in city:
        score += 30

    # Tipo de vivienda protegida
    if protection_type == "VPPL":
        score += VPPL_BONUS

    elif protection_type == "VPPB":
        score += VPPB_BONUS

    # Dormitorios preferidos
    if bedrooms == PREFERRED_BEDROOMS:
        score += 40

    elif (
        bedrooms
        and bedrooms > PREFERRED_BEDROOMS
    ):
        score += 30

    # Ático: máxima prioridad
    if PENTHOUSE_PRIORITY:
        if (
            penthouse
            or "ático" in title
            or "atico" in title
        ):
            score += 100

    # Precio disponible
    if price is not None:
        score += 10

    return score


def get_priority(score):
    """
    Convierte la puntuación en una
    categoría de prioridad.
    """

    if score >= 150:
        return "PRIORIDAD MÁXIMA"

    if score >= 100:
        return "PRIORIDAD ALTA"

    if score >= 60:
        return "PRIORIDAD MEDIA"

    return "PRIORIDAD NORMAL"