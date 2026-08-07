"""
Tests del sistema de ranking.
"""

from src.ranking import calculate_score, get_priority


def test_four_bedroom_vppl_in_madrid():
    promotion = {
        "title": "Promoción VPPL Madrid",
        "city": "Madrid",
        "bedrooms": 4,
        "penthouse": False,
        "price": None,
        "protection_type": "VPPL",
    }

    score = calculate_score(promotion)

    assert score == 90
    assert get_priority(score) == "PRIORIDAD MEDIA"


def test_four_bedroom_vppb_in_madrid():
    promotion = {
        "title": "Promoción VPPB Madrid",
        "city": "Madrid",
        "bedrooms": 4,
        "penthouse": False,
        "price": None,
        "protection_type": "VPPB",
    }

    score = calculate_score(promotion)

    assert score == 80
    assert get_priority(score) == "PRIORIDAD MEDIA"


def test_penthouse_has_maximum_priority():
    promotion = {
        "title": "Ático VPPL Madrid",
        "city": "Madrid",
        "bedrooms": 4,
        "penthouse": True,
        "price": None,
        "protection_type": "VPPL",
    }

    score = calculate_score(promotion)

    assert score == 190
    assert get_priority(score) == "PRIORIDAD MÁXIMA"


def test_vppb_three_bedrooms():
    promotion = {
        "title": "Residencial Sextans",
        "city": "Madrid",
        "bedrooms": 3,
        "penthouse": False,
        "price": None,
        "protection_type": "VPPB",
    }

    score = calculate_score(promotion)

    assert score == 40
    assert get_priority(score) == "PRIORIDAD NORMAL"


def test_vppl_with_price():
    promotion = {
        "title": "Los Ahijones Plaza",
        "city": "Madrid",
        "bedrooms": 3,
        "penthouse": False,
        "price": 323708,
        "protection_type": "VPPL",
    }

    score = calculate_score(promotion)

    assert score == 60
    assert get_priority(score) == "PRIORIDAD MEDIA"