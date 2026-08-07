"""
Scraper de promociones de vivienda protegida de Grupo Asentis.

Busca promociones VPPL / VPPB / VPP en Madrid capital.

Criterios:
- Descubre fichas mediante sitemap.
- Lee el estado real de cada promoción.
- Incluye promociones activas / en precomercialización.
- Excluye promociones completadas, terminadas o entregadas.
- Excluye promociones donde únicamente quedan viviendas PMR.
"""

import hashlib
import re
import unicodedata
from xml.etree import ElementTree

import requests
from bs4 import BeautifulSoup


SITEMAP_URLS = (
    "https://asentis.es/sitemap.xml",
    "https://asentis.es/sitemap_index.xml",
    "https://asentis.es/wp-sitemap.xml",
)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/151.0 Safari/537.36"
    )
}

TIMEOUT = 20


ACTIVE_STATUS = {
    "proxima precomercializacion",
    "precomercializacion",
    "proxima comercializacion",
    "en comercializacion",
}


EXCLUDED_STATUS = {
    "promocion completada",
    "promocion terminada",
    "promocion entregada",
}


MADRID_CAPITAL_TERMS = (
    "los ahijones",
    "ahijones",
    "los cerros",
    "el canaveral",
    "canaveral",
    "valdecarros",
    "los berrocales",
    "berrocales",
    "vicalvaro",
    "villa de vallecas",
    "ensanche de vallecas",
    "zona este de la capital",
    "este de la capital",
)


OUTSIDE_MADRID_TERMS = (
    "torrejon de ardoz",
    "azuqueca",
    "ciempozuelos",
    "villanueva",
    "pozuelo de alarcon",
    "boadilla",
    "majadahonda",
    "las rozas",
)


PMR_ONLY_TERMS = (
    "disponibles unicamente viviendas adaptadas",
    "unicamente viviendas adaptadas",
    "certificacion pmr obligatoria",
    "solo viviendas adaptadas",
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


def _extract_xml_locations(xml_text):
    locations = []

    try:
        root = ElementTree.fromstring(xml_text)

    except ElementTree.ParseError:
        return locations

    for element in root.iter():
        if (
            element.tag.endswith("loc")
            and element.text
        ):
            locations.append(
                element.text.strip()
            )

    return locations


def _discover_sitemaps():
    found = set()

    for sitemap_url in SITEMAP_URLS:
        try:
            response = _get(sitemap_url)

        except Exception:
            continue

        locations = _extract_xml_locations(
            response.text
        )

        if not locations:
            continue

        found.add(sitemap_url)

        for location in locations:
            if "sitemap" in location.lower():
                found.add(location)

    return sorted(found)


def _extract_promotion_links():
    sitemap_urls = _discover_sitemaps()

    if not sitemap_urls:
        raise RuntimeError(
            "No se ha encontrado ningún sitemap accesible en Asentis."
        )

    promotion_links = set()
    processed_sitemaps = set()
    pending_sitemaps = list(sitemap_urls)

    while pending_sitemaps:
        sitemap_url = pending_sitemaps.pop(0)

        if sitemap_url in processed_sitemaps:
            continue

        processed_sitemaps.add(
            sitemap_url
        )

        try:
            response = _get(sitemap_url)

        except Exception:
            continue

        locations = _extract_xml_locations(
            response.text
        )

        for location in locations:
            lower_location = location.lower()

            if "sitemap" in lower_location:
                if (
                    location
                    not in processed_sitemaps
                ):
                    pending_sitemaps.append(
                        location
                    )

                continue

            if "/promocion/" in lower_location:
                promotion_links.add(
                    location.rstrip("/") + "/"
                )

    return sorted(promotion_links)


def _find_real_status(soup):
    """
    Busca únicamente estados EXACTOS en encabezados.

    IMPORTANTE:
    No usamos coincidencias parciales.

    Así:
    "PROMOCIÓN COMPLETADA" -> estado real
    "Promociones completadas" -> NO es estado
    """

    for heading in soup.find_all(
        ["h1", "h2", "h3", "h4"]
    ):
        text = heading.get_text(
            " ",
            strip=True,
        )

        normalized = _normalize(text)

        if normalized in ACTIVE_STATUS:
            return heading, "ACTIVE"

        if normalized in EXCLUDED_STATUS:
            return heading, "EXCLUDED"

    return None, None


def _extract_title(status_heading, url):
    """
    Obtiene el primer encabezado útil inmediatamente posterior
    al encabezado de estado.
    """

    if status_heading is not None:
        for heading in status_heading.find_all_next(
            ["h1", "h2", "h3", "h4"]
        ):
            text = heading.get_text(
                " ",
                strip=True,
            )

            normalized = _normalize(text)

            if not text:
                continue

            if normalized in ACTIVE_STATUS:
                continue

            if normalized in EXCLUDED_STATUS:
                continue

            ignored = (
                "galeria de imagenes",
                "mapa de ubicacion",
                "viviendas disponibles",
                "rellena nuestro formulario",
                "llamanos",
                "contacta con nosotros",
                "facilities",
            )

            if normalized in ignored:
                continue

            return text

    slug = (
        url
        .rstrip("/")
        .split("/")[-1]
    )

    return (
        slug
        .replace("-", " ")
        .title()
    )


def _extract_promotion_text(status_heading):
    """
    Extrae únicamente el contenido de la ficha desde el estado
    hasta CONTACTA CON NOSOTROS.
    """

    if status_heading is None:
        return ""

    parts = []

    for node in status_heading.find_all_next(
        string=True
    ):
        parent = node.parent

        if parent is None:
            continue

        if parent.name in (
            "script",
            "style",
            "noscript",
        ):
            continue

        text = str(node).strip()

        if not text:
            continue

        normalized = _normalize(text)

        if normalized == "contacta con nosotros":
            break

        parts.append(text)

    return " ".join(parts)


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
        "vivienda de proteccion publica",
        "viviendas de proteccion publica",
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
        r"(\d+)\s*dorm\.",
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

    patterns = (
        r"desde\s+([\d\.\,]+)\s*€",
        r"precio\s+desde\s+([\d\.\,]+)\s*€",
        r"([\d]{2,3}(?:\.\d{3})+)\s*€",
    )

    prices = []

    for pattern in patterns:
        matches = re.findall(
            pattern,
            normalized,
        )

        for value in matches:
            clean_value = (
                value
                .replace(".", "")
                .replace(",", "")
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


def _is_madrid_capital(text):
    normalized = _normalize(text)

    if any(
        term in normalized
        for term in OUTSIDE_MADRID_TERMS
    ):
        return False

    if any(
        term in normalized
        for term in MADRID_CAPITAL_TERMS
    ):
        return True

    if "madrid" in normalized:
        return True

    return False


def _is_pmr_only(text):
    normalized = _normalize(text)

    return any(
        term in normalized
        for term in PMR_ONLY_TERMS
    )


def _make_id(url):
    digest = hashlib.sha1(
        url.encode("utf-8")
    ).hexdigest()[:16]

    return f"asentis-{digest}"


def _parse_promotion(url):
    response = _get(url)

    soup = BeautifulSoup(
        response.text,
        "html.parser",
    )

    status_heading, status = (
        _find_real_status(soup)
    )

    if status_heading is None:
        return (
            None,
            "no se identifica estado real",
        )

    title = _extract_title(
        status_heading,
        url,
    )

    if status == "EXCLUDED":
        return (
            None,
            "promoción completada/entregada",
        )

    promotion_text = (
        _extract_promotion_text(
            status_heading
        )
    )

    combined_text = (
        f"{title} {promotion_text}"
    )

    protection_type = (
        _detect_protection_type(
            combined_text
        )
    )

    if protection_type is None:
        return (
            None,
            "no indica VPPL/VPPB/VPP",
        )

    if not _is_madrid_capital(
        combined_text
    ):
        return (
            None,
            "fuera de Madrid capital",
        )

    if _is_pmr_only(
        combined_text
    ):
        return (
            None,
            "solo viviendas adaptadas/PMR",
        )

    bedrooms = _extract_bedrooms(
        combined_text
    )

    price = _extract_price(
        combined_text
    )

    penthouse = _detect_penthouse(
        combined_text
    )

    promotion = {
        "id": _make_id(url),
        "title": title,
        "city": "Madrid",
        "bedrooms": bedrooms,
        "penthouse": penthouse,
        "price": price,
        "protection_type": protection_type,
        "source": "Asentis",
        "developer": "Grupo Asentis",
        "url": url,
    }

    return promotion, None


def search_promotions():
    print(
        "Buscando vivienda protegida "
        "en Grupo Asentis..."
    )

    try:
        links = _extract_promotion_links()

    except Exception as exc:
        print(
            "Error descubriendo promociones "
            f"de Asentis: {exc}"
        )

        return []

    print(
        "Fichas de promoción localizadas "
        f"en Asentis: {len(links)}"
    )

    print()

    promotions = []

    for url in links:
        try:
            promotion, reason = (
                _parse_promotion(url)
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
                slug = (
                    url.rstrip("/")
                    .split("/")[-1]
                )

                print(
                    f"  - {slug}: {reason}"
                )

        except requests.exceptions.HTTPError as exc:
            if (
                exc.response is not None
                and exc.response.status_code == 404
            ):
                print(
                    "  - Ficha antigua ignorada "
                    f"(404): {url}"
                )

            else:
                print(
                    "  - Error leyendo promoción "
                    f"Asentis {url}: {exc}"
                )

        except Exception as exc:
            print(
                "  - Error leyendo promoción "
                f"Asentis {url}: {exc}"
            )

    unique_promotions = {}

    for promotion in promotions:
        unique_promotions[
            promotion["url"]
        ] = promotion

    promotions = list(
        unique_promotions.values()
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
        f"en Asentis: {len(promotions)}"
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