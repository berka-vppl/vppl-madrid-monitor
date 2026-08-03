"""
Detector de nuevas promociones residenciales
publicadas por EMVS Madrid.
"""

import hashlib
import re
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup


EMVS_URL = "https://www4.emvs.es/licitacion/UltimosExpte.do"

HOUSING_TERMS = (
    "vivienda",
    "viviendas",
    "promoción",
    "promocion",
    "residencial",
)

PROJECT_TERMS = (
    "construcción",
    "construccion",
    "obra",
    "obras",
    "ejecución",
    "ejecucion",
    "proyecto",
    "promoción",
    "promocion",
)

EXCLUDED_TERMS = (
    "seguro",
    "facility management",
    "mantenimiento",
    "mediación",
    "mediacion",
    "intermediación",
    "intermediacion",
    "adquisición de viviendas",
    "adquisicion de viviendas",
    "reforma de la vivienda",
)


def _is_housing_project(description):
    """
    Decide si una licitación corresponde
    a una promoción residencial.
    """

    text = description.casefold()

    has_housing_term = any(
        term in text
        for term in HOUSING_TERMS
    )

    has_project_term = any(
        term in text
        for term in PROJECT_TERMS
    )

    has_excluded_term = any(
        term in text
        for term in EXCLUDED_TERMS
    )

    return (
        has_housing_term
        and has_project_term
        and not has_excluded_term
    )


def _find_record_text(link):
    """
    Localiza el bloque completo de información
    correspondiente a un expediente.
    """

    preferred_container = link.find_parent(
        ["article", "tr", "li"]
    )

    if preferred_container is not None:
        text = preferred_container.get_text(
            " ",
            strip=True,
        )

        if "descripción:" in text.casefold():
            return text

    node = link

    for _ in range(10):
        node = node.parent

        if node is None:
            break

        text = node.get_text(
            " ",
            strip=True,
        )

        if "descripción:" in text.casefold():
            return text

    return ""


def _extract_description(record_text):
    """
    Extrae únicamente la descripción
    del expediente.
    """

    match = re.search(
        (
            r"Descripción:\s*(.+?)"
            r"(?=\s+Asunto:|"
            r"\s+Importe Con Impuestos:|"
            r"\s+Organismo:|$)"
        ),
        record_text,
        flags=re.IGNORECASE | re.DOTALL,
    )

    if not match:
        return ""

    return match.group(1).strip()


def _create_stable_id(expediente, description):
    """
    Crea un identificador estable utilizando
    el número de expediente de EMVS.
    """

    reference = expediente or description

    normalized_reference = re.sub(
        r"\s+",
        " ",
        reference,
    ).strip().casefold()

    identifier = hashlib.sha256(
        normalized_reference.encode("utf-8")
    ).hexdigest()[:16]

    return f"emvs-{identifier}"


def _extract_title(description, expediente):
    """
    Obtiene el nombre de la promoción.
    """

    name_match = re.search(
        (
            r"(?:denominada|promoción de|"
            r"promocion de)\s+[\"“]?"
            r"([^\"”.,]+)"
        ),
        description,
        flags=re.IGNORECASE,
    )

    if name_match:
        return name_match.group(1).strip()

    return f"Promoción EMVS {expediente}"


def parse_promotions(html):
    """
    Convierte el listado oficial de EMVS
    al formato utilizado por el radar.
    """

    soup = BeautifulSoup(html, "html.parser")
    promotions = []
    seen_ids = set()

    for link in soup.find_all("a", href=True):
        href = link.get("href", "")

        if "fichaExpte.do" not in href:
            continue

        record_text = _find_record_text(link)
        description = _extract_description(
            record_text
        )

        if not description:
            continue

        if not _is_housing_project(description):
            continue

        expediente = link.get_text(
            " ",
            strip=True,
        )

        promotion_id = _create_stable_id(
            expediente,
            description,
        )

        if promotion_id in seen_ids:
            continue

        url = urljoin(EMVS_URL, href)

        title = _extract_title(
            description,
            expediente,
        )

        promotions.append(
            {
                "id": promotion_id,
                "title": title,
                "city": "Madrid",
                "bedrooms": None,
                "penthouse": False,
                "price": None,
                "source": "EMVS Madrid",
                "developer": "EMVS Madrid",
                "url": url,
            }
        )

        seen_ids.add(promotion_id)

    return promotions


def search_promotions():
    """
    Descarga y analiza las últimas
    licitaciones publicadas por EMVS.
    """

    print(
        "Buscando nuevas promociones "
        "en EMVS Madrid..."
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
            EMVS_URL,
            headers=headers,
            timeout=25,
        )
        response.raise_for_status()

    except requests.RequestException:
        print(
            "No se pudo consultar EMVS Madrid."
        )
        return []

    promotions = parse_promotions(
        response.text
    )

    print(
        "Promociones residenciales encontradas "
        f"en EMVS: {len(promotions)}"
    )

    return promotions


if __name__ == "__main__":
    for promotion in search_promotions():
        print(promotion)