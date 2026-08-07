import os
import re

import requests


def send_telegram_message(message):
    """
    Envía un mensaje al chat de Telegram configurado.
    """

    bot_token = os.getenv(
        "TELEGRAM_BOT_TOKEN"
    )

    chat_id = os.getenv(
        "TELEGRAM_CHAT_ID"
    )

    if not bot_token or not chat_id:
        print(
            "Aviso: Telegram no está configurado. "
            "Faltan TELEGRAM_BOT_TOKEN "
            "o TELEGRAM_CHAT_ID."
        )
        return False

    bot_token = bot_token.strip()
    chat_id = chat_id.strip()

    url = (
        "https://api.telegram.org/"
        f"bot{bot_token}/sendMessage"
    )

    data = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "Markdown",
        "disable_web_page_preview": False,
    }

    try:
        response = requests.post(
            url,
            data=data,
            timeout=15,
        )

        if response.ok:
            print(
                "Alerta enviada correctamente "
                "a Telegram."
            )
            return True

        print(
            "No se pudo enviar la alerta "
            "de Telegram."
        )

        print(
            "Código HTTP: "
            f"{response.status_code}"
        )

        try:
            error_data = response.json()

            description = error_data.get(
                "description"
            )

            if description:
                print(
                    "Telegram responde: "
                    f"{description}"
                )

        except ValueError:
            pass

        if response.status_code == 401:
            print(
                "El token del bot de Telegram "
                "no es válido o ha sido revocado."
            )

        return False

    except requests.RequestException as error:
        print(
            "No se pudo conectar con Telegram."
        )

        print(
            f"Detalle: {error}"
        )

        return False


def _detect_protection_type(promotion):
    """
    Intenta identificar el tipo de vivienda
    protegida a partir de los datos disponibles.
    """

    explicit_type = promotion.get(
        "protection_type"
    )

    if explicit_type:
        return str(
            explicit_type
        ).upper()

    title = promotion.get(
        "title",
        "",
    )

    description = promotion.get(
        "description",
        "",
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

    if re.search(
        r"\bvpp\b",
        text,
    ):
        return "VPP"

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

    if (
        "vivienda protegida"
        in text
        or "protección pública"
        in text
        or "proteccion publica"
        in text
    ):
        return "VPP"

    return "VPP"


def create_promotion_message(promotion):
    """
    Construye el mensaje de una promoción
    para Telegram.
    """

    title = promotion.get(
        "title",
        "Promoción sin nombre",
    )

    source = promotion.get(
        "source",
        "Desconocida",
    )

    developer = promotion.get(
        "developer",
        source,
    )

    city = promotion.get(
        "city",
        "Madrid",
    )

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

    url = promotion.get(
        "url",
        "",
    )

    score = promotion.get(
        "score",
        promotion.get(
            "points",
            0,
        ),
    )

    priority = promotion.get(
        "priority",
        "PRIORIDAD NORMAL",
    )

    protection_type = (
        _detect_protection_type(
            promotion
        )
    )

    if bedrooms is None:
        bedrooms_text = (
            "No indicado"
        )
    else:
        bedrooms_text = str(
            bedrooms
        )

    penthouse_text = (
        "🏠 Sí"
        if penthouse
        else "—"
    )

    if price:
        try:
            price_text = (
                f"{int(price):,}"
                .replace(",", ".")
                + " €"
            )

        except (
            TypeError,
            ValueError,
        ):
            price_text = str(
                price
            )

    else:
        price_text = (
            "No indicado"
        )

    message = (
        "🚨 *NUEVA PROMOCIÓN VPP*\n\n"
        f"🏢 *{title}*\n\n"
        f"🏷 Tipo: {protection_type}\n"
        f"📍 Ciudad: {city}\n"
        f"🏗 Promotora: {developer}\n"
        f"🛏 Dormitorios: {bedrooms_text}\n"
        f"🏠 Ático: {penthouse_text}\n"
        f"💶 Precio: {price_text}\n"
        f"⭐ Prioridad: {priority}\n"
        f"📊 Puntuación: {score}\n"
    )

    if url:
        message += (
            f"\n🔗 {url}"
        )

    return message