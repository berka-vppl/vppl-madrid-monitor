"""
Scraper de Víveme Real Estate Management.

Fuente inicial:
- Vivir en Ahijones

Objetivo:
- Detectar vivienda protegida en Madrid capital.
- Mantener la promoción mientras siga en fase activa.
- Clasificar como VPPL / VPPB si la web lo indica.
- Usar VPP genérica si solo se indica vivienda protegida.
"""

import hashlib
import re
import unicodedata

import requests
from bs4 import BeautifulSoup


PROMOTIONS = (
    {
        "name": "Vivir en Ahijones",
        "url": "https://www.vivirenahijones.es/",
    },
)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/151.0 Safari/537.36"
    )
}

TIMEOUT = 20


ACTIVE_TERMS = (
    "captacion de demanda",
    "captacion de interesados",
    "fase de captacion",
    "proximo proyecto",
    "proxima promocion",
    "preinscripcion",
)


EXCLUDED_TERMS = (
    "promocion finalizada",
    "promocion completada",
    "100% comercializada",
    "agotado",
)


def _normalize(text):
    if text is None:
        return ""

    text = str(text).lower()

    text = "".join(
        char
        for char in unicodedata.normalize("NFKD", text)
        if not unicodedata.combining(char)
    )

    return " ".join(text.split())


def _get(url):
    response = requests.get(
        url,
        headers=HEADERS,
        timeout=TIMEOUT,
    )

    response.raise_for_status()

    return response


def _detect_protection_type(text):
    normalized = _normalize(text)

    if "vppl" in normalized:
        return "VPPL"

    if "precio limitado" in normalized:
        return "VPPL"

    if "vppb" in normalized:
        return "VPPB"

    if "precio basico" in normalized:
        return "VPPB"

    generic_terms = (
        "vivienda protegida",
        "viviendas protegidas",
        "vivienda de proteccion",
        "viviendas de proteccion",
        "proteccion publica",
        "vpp",
    )

    if any(
        term in normalized
        for term in generic_terms
    ):
        return "VPP"

    return None


def _extract_bedrooms(text):
    normalized = _normalize(text)

    values = []

    patterns = (
        r"(\d+)\s*(?:y|-|a)\s*(\d+)\s*dormitorios",
        r"(\d+)\s*dormitorios",
    )

    for pattern in patterns:
        matches = re.findall(
            pattern,
            normalized,
        )

        for match in matches:
            if isinstance(match, tuple):
                for value in match:
                    if value:
                        values.append(
                            int(value)
                        )
            else:
                values.append(
                    int(match)
                )

    values = [
        value
        for value in values
        if 1 <= value <= 9
    ]

    if not values:
        return None

    return max(values)


def _extract_price(text):
    normalized = _normalize(text)

    matches = re.findall(
        r"([\d]{2,3}(?:\.\d{3})+)\s*€",
        normalized,
    )

    prices = []

    for value in matches:
        clean_value = value.replace(
            ".",
            "",
        )

        try:
            price = int(clean_value)

        except ValueError:
            continue

        if (
            50_000
            <= price
            <= 2_000_000
        ):
            prices.append(price)

    if not prices:
        return None

    return min(prices)


def _detect_penthouse(text):
    normalized = _normalize(text)

    return (
        "atico" in normalized
        or "aticos" in normalized
    )


def _is_active(text):
    normalized = _normalize(text)

    if any(
        term in normalized
        for term in EXCLUDED_TERMS
    ):
        return False

    return any(
        term in normalized
        for term in ACTIVE_TERMS
    )


def _make_id(url):
    digest = hashlib.sha1(
        url.encode("utf-8")
    ).hexdigest()[:16]

    return f"viveme-{digest}"


def _parse_promotion(config):
    url = config["url"]
    fallback_name = config["name"]

    response = _get(url)

    soup = BeautifulSoup(
        response.text,
        "html.parser",
    )

    text = soup.get_text(
        " ",
        strip=True,
    )

    normalized = _normalize(text)

    if not _is_active(text):
        return (
            None,
            "promoción no activa o sin fase detectable",
        )

    protection_type = (
        _detect_protection_type(text)
    )

    if protection_type is None:
        return (
            None,
            "no se identifica vivienda protegida",
        )

    if (
        "los ahijones" not in normalized
        and "madrid" not in normalized
        and "vicalvaro" not in normalized
    ):
        return (
            None,
            "fuera de Madrid capital",
        )

    title = fallback_name

    bedrooms = _extract_bedrooms(
        text
    )

    price = _extract_price(
        text
    )

    penthouse = _detect_penthouse(
        text
    )

    promotion = {
        "id": _make_id(url),
        "title": title,
        "city": "Madrid",
        "bedrooms": bedrooms,
        "penthouse": penthouse,
        "price": price,
        "protection_type": protection_type,
        "source": "Víveme",
        "developer": "Víveme Real Estate Management",
        "url": url,
    }

    return promotion, None


def search_promotions():
    print(
        "Buscando vivienda protegida "
        "en Víveme..."
    )

    promotions = []

    for config in PROMOTIONS:
        try:
            promotion, reason = (
                _parse_promotion(
                    config
                )
            )

            if promotion:
                promotions.append(
                    promotion
                )

                print(
                    "  ✓ "
                    f"{promotion['title']} "
                    f"({promotion['protection_type']})"
                )

            else:
                print(
                    "  - "
                    f"{config['name']}: "
                    f"{reason}"
                )

        except Exception as exc:
            print(
                "  - Error leyendo "
                f"{config['name']}: "
                f"{exc}"
            )

    vppl_count = sum(
        1
        for promotion in promotions
        if promotion["protection_type"]
        == "VPPL"
    )

    vppb_count = sum(
        1
        for promotion in promotions
        if promotion["protection_type"]
        == "VPPB"
    )

    vpp_count = sum(
        1
        for promotion in promotions
        if promotion["protection_type"]
        == "VPP"
    )

    print()

    print(
        "Promociones protegidas encontradas "
        f"en Víveme: {len(promotions)}"
    )

    print(
        f"  VPPL: {vppl_count}"
    )

    print(
        f"  VPPB: {vppb_count}"
    )

    print(
        f"  VPP sin clasificar: {vpp_count}"
    )

    return promotions


if __name__ == "__main__":
    results = search_promotions()

    print()

    for promotion in results:
        print(promotion)