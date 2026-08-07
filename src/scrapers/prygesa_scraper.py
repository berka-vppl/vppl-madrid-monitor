"""
Detector de promociones de vivienda protegida
publicadas por PRYGESA en Madrid capital.
"""

import hashlib
import re
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup


PRYGESA_URL = (
    "https://www.prygesa.es/obra-nueva/madrid"
)


PROTECTED_TERMS = (
    "vppl",
    "vppb",
    "vpp",
    "vivienda protegida",
    "viviendas protegidas",
    "protección pública",
    "proteccion publica",
)


MADRID_CAPITAL_TERMS = (
    "vicálvaro",
    "vicalvaro",
    "vallecas",
    "los ahijones",
    "los berrocales",
    "el cañaveral",
    "canaveral",
    "los cerros",
    "valdecarros",
)


EXCLUDED_LOCATIONS = (
    "torrejón de ardoz",
    "torrejon de ardoz",
    "parla",
    "valdemoro",
    "alcalá de henares",
    "alcala de henares",
    "tres cantos",
    "las rozas",
    "coslada",
    "san fernando de henares",
    "rivas-vaciamadrid",
)


EXCLUDED_STATUS_TERMS = (
    "100% comercializada",
    "comercializada al 100%",
    "comercializado al 100%",
    "solo viviendas pmr",
    "sólo viviendas pmr",
    "solo disponibles viviendas adaptadas pmr",
    "sólo disponibles viviendas adaptadas pmr",
)


def _normalize(value):
    """
    Convierte cualquier valor a texto limpio.
    """

    if value is None:
        return ""

    return re.sub(
        r"\s+",
        " ",
        str(value),
    ).strip()


def _create_stable_id(url, title):
    """
    Crea un identificador estable
    para evitar duplicados.
    """

    reference = (
        url
        or title
    )

    normalized = (
        _normalize(reference)
        .casefold()
    )

    digest = hashlib.sha256(
        normalized.encode("utf-8")
    ).hexdigest()[:16]

    return f"prygesa-{digest}"


def _detect_protection_type(text):
    """
    Detecta si la promoción es VPPL,
    VPPB o VPP genérica.
    """

    normalized = (
        _normalize(text)
        .casefold()
    )

    if re.search(
        r"\bvppl\b",
        normalized,
    ):
        return "VPPL"

    if (
        "precio limitado"
        in normalized
    ):
        return "VPPL"

    if re.search(
        r"\bvppb\b",
        normalized,
    ):
        return "VPPB"

    if (
        "precio básico"
        in normalized
        or "precio basico"
        in normalized
    ):
        return "VPPB"

    if re.search(
        r"\bvpp\b",
        normalized,
    ):
        return "VPP"

    if (
        "vivienda protegida"
        in normalized
        or "viviendas protegidas"
        in normalized
        or "protección pública"
        in normalized
        or "proteccion publica"
        in normalized
    ):
        return "VPP"

    return None


def _is_protected(text):
    """
    Comprueba si la promoción es
    de vivienda protegida.
    """

    normalized = (
        _normalize(text)
        .casefold()
    )

    return any(
        term in normalized
        for term in PROTECTED_TERMS
    )


def _is_madrid_capital(text, url):
    """
    Limita los resultados a Madrid capital.
    """

    normalized_text = (
        _normalize(text)
        .casefold()
    )

    normalized_url = (
        _normalize(url)
        .casefold()
    )

    combined = (
        f"{normalized_text} "
        f"{normalized_url}"
    )

    if any(
        location in combined
        for location in EXCLUDED_LOCATIONS
    ):
        return False

    return any(
        location in combined
        for location in MADRID_CAPITAL_TERMS
    )


def _is_available(text):
    """
    Descarta promociones que ya no representan
    una oportunidad útil para el radar.
    """

    normalized = (
        _normalize(text)
        .casefold()
    )

    return not any(
        term in normalized
        for term in EXCLUDED_STATUS_TERMS
    )


def _extract_bedrooms(text):
    """
    Intenta identificar el máximo número
    de dormitorios anunciado.
    """

    normalized = (
        _normalize(text)
        .casefold()
    )

    matches = re.findall(
        r"\b([1-5])\s+dormitorios?\b",
        normalized,
    )

    if not matches:
        return None

    values = [
        int(value)
        for value in matches
    ]

    return max(values)


def _detect_penthouse(text):
    """
    Detecta si la promoción menciona áticos.
    """

    normalized = (
        _normalize(text)
        .casefold()
    )

    return any(
        term in normalized
        for term in (
            "ático",
            "atico",
            "áticos",
            "aticos",
        )
    )


def _extract_price(text):
    """
    Intenta extraer el precio publicado
    como importe DESDE.
    """

    normalized = _normalize(text)

    match = re.search(
        r"(?:desde\s*)"
        r"([0-9]{2,3}(?:[.\s][0-9]{3})+)",
        normalized,
        flags=re.IGNORECASE,
    )

    if not match:
        return None

    price_text = re.sub(
        r"[.\s]",
        "",
        match.group(1),
    )

    try:
        return int(price_text)

    except ValueError:
        return None


def _find_candidate_links(soup):
    """
    Busca enlaces de promociones
    dentro de la página de Madrid.
    """

    candidates = []

    for link in soup.find_all(
        "a",
        href=True,
    ):

        href = _normalize(
            link.get("href")
        )

        if "/obra-nueva/madrid/" not in href:
            continue

        url = urljoin(
            PRYGESA_URL,
            href,
        )

        container = link

        for _ in range(5):

            parent = container.parent

            if parent is None:
                break

            parent_text = _normalize(
                parent.get_text(
                    " ",
                    strip=True,
                )
            )

            if len(parent_text) >= 80:
                container = parent
                break

            container = parent

        text = _normalize(
            container.get_text(
                " ",
                strip=True,
            )
        )

        title = _normalize(
            link.get_text(
                " ",
                strip=True,
            )
        )

        if not title:
            continue

        candidates.append(
            {
                "title": title,
                "text": text,
                "url": url,
            }
        )

    return candidates


def parse_promotions(html):
    """
    Convierte las promociones publicadas
    por PRYGESA al formato del radar.
    """

    soup = BeautifulSoup(
        html,
        "html.parser",
    )

    promotions = []
    seen_urls = set()

    candidates = _find_candidate_links(
        soup
    )

    for candidate in candidates:

        title = candidate["title"]
        text = candidate["text"]
        url = candidate["url"]

        combined_text = (
            f"{title} {text}"
        )

        if url in seen_urls:
            continue

        if not _is_protected(
            combined_text
        ):
            continue

        if not _is_madrid_capital(
            combined_text,
            url,
        ):
            continue

        if not _is_available(
            combined_text
        ):
            continue

        protection_type = (
            _detect_protection_type(
                combined_text
            )
        )

        promotion_id = (
            _create_stable_id(
                url,
                title,
            )
        )

        bedrooms = _extract_bedrooms(
            combined_text
        )

        penthouse = _detect_penthouse(
            combined_text
        )

        price = _extract_price(
            combined_text
        )

        promotions.append(
            {
                "id": promotion_id,
                "title": title,
                "city": "Madrid",
                "bedrooms": bedrooms,
                "penthouse": penthouse,
                "price": price,
                "protection_type": protection_type,
                "source": "PRYGESA",
                "developer": "PRYGESA",
                "url": url,
            }
        )

        seen_urls.add(
            url
        )

    return promotions


def search_promotions():
    """
    Consulta las promociones de PRYGESA
    y devuelve únicamente vivienda protegida
    útil situada en Madrid capital.
    """

    print(
        "Buscando promociones protegidas "
        "en PRYGESA..."
    )

    headers = {
        "User-Agent": (
            "Mozilla/5.0 "
            "(Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 "
            "(KHTML, like Gecko) "
            "Chrome/120 Safari/537.36"
        )
    }

    try:

        response = requests.get(
            PRYGESA_URL,
            headers=headers,
            timeout=30,
        )

        response.raise_for_status()

    except requests.RequestException as error:

        print(
            "No se pudo consultar "
            f"PRYGESA: {error}"
        )

        return []

    promotions = parse_promotions(
        response.text
    )

    vppl_count = sum(
        1
        for promotion in promotions
        if promotion.get(
            "protection_type"
        ) == "VPPL"
    )

    vppb_count = sum(
        1
        for promotion in promotions
        if promotion.get(
            "protection_type"
        ) == "VPPB"
    )

    generic_vpp_count = sum(
        1
        for promotion in promotions
        if promotion.get(
            "protection_type"
        ) == "VPP"
    )

    print(
        "Promociones protegidas activas "
        "encontradas en PRYGESA "
        f"(Madrid capital): {len(promotions)}"
    )

    print(
        f"  VPPL: {vppl_count}"
    )

    print(
        f"  VPPB: {vppb_count}"
    )

    print(
        f"  VPP sin clasificar: "
        f"{generic_vpp_count}"
    )

    return promotions


if __name__ == "__main__":

    promotions = search_promotions()

    for promotion in promotions:

        print("-" * 60)

        print(
            f"Promoción: "
            f"{promotion['title']}"
        )

        print(
            f"Tipo: "
            f"{promotion['protection_type']}"
        )

        print(
            f"Dormitorios: "
            f"{promotion['bedrooms']}"
        )

        print(
            f"Ático mencionado: "
            f"{promotion['penthouse']}"
        )

        print(
            f"Precio: "
            f"{promotion['price']}"
        )

        print(
            f"Enlace: "
            f"{promotion['url']}"
        )