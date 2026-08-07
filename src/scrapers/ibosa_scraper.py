"""
Scraper de promociones de Grupo Ibosa.

Busca promociones de vivienda protegida
VPPL y VPPB publicadas en la página
de promociones en curso de Ibosa.
"""

import hashlib
import re
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup


IBOSA_URL = (
    "https://www.grupoibosa.com/"
    "nuestras-promociones/promociones-encurso.html"
)


PROTECTED_TERMS = (
    "vppl",
    "vppb",
    "vpp",
    "vivienda protegida",
    "viviendas protegidas",
    "precio limitado",
    "precio básico",
    "precio basico",
    "protección pública",
    "proteccion publica",
)


def extract_bedrooms(text):
    """
    Extrae el número máximo de dormitorios mencionado.

    Ejemplo:
    '2, 3 y 4 dormitorios' devuelve 4.
    """

    numbers = re.findall(
        r"\b([1-9])\b(?=[^.\n]{0,30}dormitorios)",
        text.casefold(),
    )

    if not numbers:
        return None

    return max(
        int(number)
        for number in numbers
    )


def detect_protection_type(text):
    """
    Detecta si una promoción es VPPL, VPPB
    o VPP genérica.
    """

    normalized = (
        str(text or "")
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


def is_protected_promotion(text):
    """
    Comprueba si el texto contiene
    indicios de vivienda protegida.
    """

    normalized = (
        str(text or "")
        .casefold()
    )

    return any(
        term in normalized
        for term in PROTECTED_TERMS
    )


def search_promotions():
    """
    Busca promociones protegidas
    activas en Grupo Ibosa.
    """

    print(
        "Buscando promociones protegidas "
        "en Ibosa..."
    )

    headers = {
        "User-Agent": (
            "Mozilla/5.0 "
            "(Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 "
            "Chrome/120 Safari/537.36"
        )
    }

    try:
        response = requests.get(
            IBOSA_URL,
            headers=headers,
            timeout=20,
        )

        response.raise_for_status()

    except requests.RequestException as error:
        print(
            f"No se pudo consultar Ibosa: {error}"
        )
        return []

    soup = BeautifulSoup(
        response.text,
        "html.parser",
    )

    promotions = []
    processed_urls = set()

    ignored_titles = {
        "más información",
        "mas información",
        "mas informacion",
        "ver más",
        "ver mas",
        "saber más",
        "saber mas",
        "información",
        "informacion",
        "contactar",
        "guía de vivienda protegida",
        "guia de vivienda protegida",
        "guía vivienda protegida",
        "guia vivienda protegida",
        "guía",
        "guia",
        "vivienda protegida",
    }

    for link in soup.find_all(
        "a",
        href=True,
    ):

        title = link.get_text(
            " ",
            strip=True,
        )

        url = urljoin(
            IBOSA_URL,
            link["href"],
        )

        parent = link.find_parent(
            [
                "article",
                "div",
                "li",
                "section",
            ]
        )

        if parent:
            full_text = parent.get_text(
                " ",
                strip=True,
            )
        else:
            full_text = title

        normalized_text = (
            full_text.casefold()
        )

        if not is_protected_promotion(
            full_text
        ):
            continue

        if (
            not title
            or title.casefold().strip()
            in ignored_titles
            or url in processed_urls
        ):
            continue

        protection_type = (
            detect_protection_type(
                full_text
            )
        )

        bedrooms = extract_bedrooms(
            full_text
        )

        penthouse = any(
            term in normalized_text
            for term in (
                "ático",
                "atico",
                "áticos",
                "aticos",
            )
        )

        promotion = {
            "id": (
                "ibosa-"
                + hashlib.sha256(
                    url.encode("utf-8")
                ).hexdigest()[:16]
            ),
            "title": title,
            "city": "Madrid",
            "bedrooms": bedrooms,
            "penthouse": penthouse,
            "price": None,
            "protection_type": protection_type,
            "source": "Ibosa",
            "developer": "Grupo Ibosa",
            "url": url,
        }

        promotions.append(
            promotion
        )

        processed_urls.add(
            url
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
        "Promociones protegidas encontradas "
        f"en Ibosa: {len(promotions)}"
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

    results = search_promotions()

    for promotion in results:

        print("-" * 50)

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
            f"Enlace: "
            f"{promotion['url']}"
        )