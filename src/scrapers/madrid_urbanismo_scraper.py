"""
Detector de actuaciones urbanísticas de Madrid
relacionadas con vivienda protegida.

Fuente:
Portal de Datos Abiertos del Ayuntamiento de Madrid.
"""

import hashlib
import os
import re
import tempfile
import zipfile
from io import BytesIO

import requests
import shapefile


DATASET_URL = (
    "https://datos.madrid.es/egob/catalogo/"
    "300487-11311034-planeamiento-informacion-publica.zip"
)

SOURCE_PAGE = (
    "https://datos.madrid.es/dataset/"
    "300487-0-planeamiento-informacion-publica"
)


PROTECTED_HOUSING_TERMS = (
    "vppl",
    "vppb",
    "vpp",
    "vivienda protegida",
    "viviendas protegidas",
    "vivienda de protección pública",
    "viviendas de protección pública",
    "vivienda de proteccion publica",
    "viviendas de proteccion publica",
    "vivienda pública",
    "vivienda publica",
)


DEVELOPMENT_TERMS = (
    "vivienda",
    "viviendas",
    "residencial",
    "parcela",
    "parcelas",
    "promoción",
    "promocion",
    "edificación",
    "edificacion",
    "construcción",
    "construccion",
    "obra nueva",
)


CONCRETE_PROJECT_TERMS = (
    "parcela",
    "parcelas",
    "ámbito",
    "ambito",
    "sector",
    "unidad de ejecución",
    "unidad de ejecucion",
    "calle",
    "avenida",
    "paseo",
    "plaza",
    "distrito",
    "barrio",
    "solar",
    "manzana",
    "promoción denominada",
    "promocion denominada",
)


EXCLUDED_TERMS = (
    "modificación de normativa",
    "modificacion de normativa",
    "aplicación de la ley",
    "aplicacion de la ley",
    "aplicación en el municipio de madrid de la ley",
    "aplicacion en el municipio de madrid de la ley",
    "medidas urbanísticas",
    "medidas urbanisticas",
    "ley 3/2024",
    "plan especial para la aplicación",
    "plan especial para la aplicacion",
)


EXCLUDED_EXPEDIENTES = (
    "135/2026/00100",
)


GENERIC_TITLES = (
    "promoción de vivienda protegida",
    "promocion de vivienda protegida",
    "vivienda protegida",
    "viviendas protegidas",
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


def _detect_protection_type(text):
    """
    Detecta si la actuación corresponde
    a VPPL, VPPB o VPP genérica.
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
        or "vivienda de protección pública"
        in normalized
        or "viviendas de protección pública"
        in normalized
        or "vivienda de proteccion publica"
        in normalized
        or "viviendas de proteccion publica"
        in normalized
        or "vivienda pública"
        in normalized
        or "vivienda publica"
        in normalized
    ):
        return "VPP"

    return None


def _is_generic_title(title):
    """
    Detecta denominaciones demasiado genéricas
    que no identifican una promoción concreta.
    """

    normalized_title = (
        _normalize(title).casefold()
    )

    return (
        normalized_title
        in GENERIC_TITLES
    )


def _is_relevant(text):
    """
    Filtra actuaciones relacionadas
    con vivienda protegida.
    """

    normalized_text = (
        _normalize(text).casefold()
    )

    if any(
        term in normalized_text
        for term in EXCLUDED_TERMS
    ):
        return False

    has_protected_term = any(
        term in normalized_text
        for term in PROTECTED_HOUSING_TERMS
    )

    has_development_term = any(
        term in normalized_text
        for term in DEVELOPMENT_TERMS
    )

    return (
        has_protected_term
        and has_development_term
    )


def _has_concrete_project_reference(text):
    """
    Comprueba si el expediente contiene
    referencias que indiquen una actuación concreta.
    """

    normalized_text = (
        _normalize(text).casefold()
    )

    return any(
        term in normalized_text
        for term in CONCRETE_PROJECT_TERMS
    )


def _create_stable_id(reference):
    """
    Genera un ID estable para evitar
    alertas duplicadas.
    """

    normalized = (
        _normalize(reference)
        .casefold()
    )

    digest = hashlib.sha256(
        normalized.encode("utf-8")
    ).hexdigest()[:16]

    return (
        f"urbanismo-madrid-{digest}"
    )


def _find_value(
    record,
    possible_terms,
):
    """
    Busca un campo útil sin depender
    del nombre exacto del dataset.
    """

    for key, value in record.items():

        normalized_key = (
            _normalize(key)
            .casefold()
        )

        if any(
            term in normalized_key
            for term in possible_terms
        ):
            cleaned_value = (
                _normalize(value)
            )

            if cleaned_value:
                return cleaned_value

    return ""


def _record_to_text(record):
    """
    Une todos los campos del expediente.
    """

    values = []

    for value in record.values():

        cleaned = _normalize(value)

        if cleaned:
            values.append(cleaned)

    return " ".join(values)


def parse_shapefile(shp_path):
    """
    Convierte los registros del SHP
    al formato utilizado por el radar.
    """

    promotions = []
    seen_ids = set()

    reader = None

    try:
        reader = shapefile.Reader(
            shp_path
        )

        for shape_record in (
            reader.iterShapeRecords()
        ):

            record = (
                shape_record.record.as_dict()
            )

            full_text = (
                _record_to_text(
                    record
                )
            )

            if not _is_relevant(
                full_text
            ):
                continue

            expediente = _find_value(
                record,
                (
                    "exped",
                    "codigo",
                    "código",
                ),
            )

            if expediente in (
                EXCLUDED_EXPEDIENTES
            ):
                continue

            title = _find_value(
                record,
                (
                    "denom",
                    "titulo",
                    "título",
                    "nombre",
                    "asunto",
                    "descripcion",
                    "descripción",
                ),
            )

            if not title:
                title = (
                    "Actuación de vivienda "
                    "protegida Madrid"
                )

            if (
                _is_generic_title(
                    title
                )
                and not (
                    _has_concrete_project_reference(
                        full_text
                    )
                )
            ):
                continue

            protection_type = (
                _detect_protection_type(
                    full_text
                )
            )

            if protection_type is None:
                protection_type = "VPP"

            reference = (
                expediente
                or title
                or full_text
            )

            promotion_id = (
                _create_stable_id(
                    reference
                )
            )

            if (
                promotion_id
                in seen_ids
            ):
                continue

            if expediente:
                display_title = (
                    f"{title} "
                    f"[{expediente}]"
                )
            else:
                display_title = title

            promotions.append(
                {
                    "id": promotion_id,
                    "title": display_title,
                    "city": "Madrid",
                    "bedrooms": None,
                    "penthouse": False,
                    "price": None,
                    "protection_type": (
                        protection_type
                    ),
                    "source": (
                        "Urbanismo Madrid"
                    ),
                    "developer": (
                        "Ayuntamiento de Madrid"
                    ),
                    "url": SOURCE_PAGE,
                }
            )

            seen_ids.add(
                promotion_id
            )

    finally:
        if reader is not None:
            reader.close()

    return promotions


def search_promotions():
    """
    Descarga el dataset oficial y busca
    actuaciones de vivienda protegida.
    """

    print(
        "Buscando vivienda protegida "
        "en Datos Abiertos Madrid..."
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
            DATASET_URL,
            headers=headers,
            timeout=30,
        )

        response.raise_for_status()

    except requests.RequestException as error:
        print(
            "No se pudo descargar "
            "Datos Abiertos Madrid: "
            f"{error}"
        )
        return []

    try:
        zip_data = BytesIO(
            response.content
        )

        promotions = []

        with tempfile.TemporaryDirectory() as temp_dir:

            with zipfile.ZipFile(
                zip_data
            ) as zip_file:

                zip_file.extractall(
                    temp_dir
                )

            shp_files = []

            for root, _, files in os.walk(
                temp_dir
            ):

                for filename in files:

                    if (
                        filename
                        .lower()
                        .endswith(".shp")
                    ):
                        shp_files.append(
                            os.path.join(
                                root,
                                filename,
                            )
                        )

            if not shp_files:
                print(
                    "El dataset no contiene "
                    "ningún archivo SHP."
                )
                return []

            for shp_path in shp_files:

                try:
                    found = (
                        parse_shapefile(
                            shp_path
                        )
                    )

                    promotions.extend(
                        found
                    )

                except Exception as error:
                    print(
                        "No se pudo leer "
                        f"{os.path.basename(shp_path)}: "
                        f"{error}"
                    )

    except zipfile.BadZipFile:
        print(
            "El archivo descargado "
            "no es un ZIP válido."
        )
        return []

    unique_promotions = {}

    for promotion in promotions:

        unique_promotions[
            promotion["id"]
        ] = promotion

    promotions = list(
        unique_promotions.values()
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
        "Actuaciones de vivienda protegida "
        "encontradas en Urbanismo Madrid: "
        f"{len(promotions)}"
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
            f"Enlace: "
            f"{promotion['url']}"
        )