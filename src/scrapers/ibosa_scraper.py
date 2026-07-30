"""
Scraper de promociones de Grupo Ibosa.

Busca promociones VPPL publicadas en la página
de promociones en curso de Ibosa.
"""

import re
import hashlib
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup


IBOSA_URL = (
    "https://www.grupoibosa.com/"
    "nuestras-promociones/promociones-encurso.html"
)


def extract_bedrooms(text):
    """
    Extrae el número máximo de dormitorios mencionado.

    Ejemplo:
    '2, 3 y 4 dormitorios' devuelve 4.
    """
    numbers = re.findall(
        r"\b([1-9])\b(?=[^.\n]{0,30}dormitorios)",
        text.lower(),
    )

    if not numbers:
        return None

    return max(int(number) for number in numbers)


def search_promotions():
    print("Buscando promociones en Ibosa...")

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 Chrome/120 Safari/537.36"
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
        print(f"No se pudo consultar Ibosa: {error}")
        return []

    soup = BeautifulSoup(response.text, "html.parser")

    promotions = []
    processed_urls = set()

    for link in soup.find_all("a", href=True):
        title = link.get_text(" ", strip=True)
        url = urljoin(IBOSA_URL, link["href"])

        parent = link.find_parent(
            ["article", "div", "li", "section"]
        )

        if parent:
            full_text = parent.get_text(" ", strip=True)
        else:
            full_text = title

        normalized_text = full_text.lower()

        is_protected = any(
            term in normalized_text
            for term in [
                "vppl",
                "vivienda protegida",
                "precio limitado",
            ]
        )

        if not is_protected:
            continue

        ignored_titles = {
            "más información",
            "ver más",
            "saber más",
            "información",
            "contactar",
            "guía de vivienda protegida",
            "guía vivienda protegida",
            "guía",
            "vivienda protegida",
        }

        if (
            not title
            or title.lower().strip() in ignored_titles
            or url in processed_urls
        ):
            continue

        bedrooms = extract_bedrooms(full_text)

        promotion = {
            "id": f"ibosa-{hashlib.sha256(url.encode('utf-8')).hexdigest()[:16]}",
            "title": title,
            "city": "Madrid",
            "bedrooms": bedrooms,
            "penthouse": "ático" in normalized_text,
            "price": None,
            "source": "Ibosa",
            "url": url,
        }

        promotions.append(promotion)
        processed_urls.add(url)

    print(
        f"Promociones VPPL encontradas en Ibosa: "
        f"{len(promotions)}"
    )

    return promotions


if __name__ == "__main__":
    results = search_promotions()

    for promotion in results:
        print("-" * 50)
        print(f"Promoción: {promotion['title']}")
        print(f"Dormitorios: {promotion['bedrooms']}")
        print(f"Ático mencionado: {promotion['penthouse']}")
        print(f"Enlace: {promotion['url']}")