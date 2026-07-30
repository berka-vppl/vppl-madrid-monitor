import os

import requests


def send_telegram_message(message):
    """
    Envía un mensaje al chat de Telegram configurado.
    """

    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")

    if not bot_token or not chat_id:
        print(
            "Aviso: Telegram no está configurado. "
            "Faltan TELEGRAM_BOT_TOKEN o TELEGRAM_CHAT_ID."
        )
        return False

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

    data = {
    "chat_id": chat_id,
    "text": message,
    "parse_mode": "Markdown",
    "disable_web_page_preview": False,
}

    try:
        response = requests.post(url, data=data, timeout=15)
        response.raise_for_status()

        print("Alerta enviada correctamente a Telegram.")
        return True

    except requests.RequestException as error:
        print(f"No se pudo enviar la alerta de Telegram: {error}")
        return False


def create_promotion_message(promotion):
    """
    Construye un mensaje bonito para Telegram.
    """

    title = promotion.get("title", "Promoción sin nombre")
    source = promotion.get("source", "Desconocido")
    city = promotion.get("city", "Madrid")
    bedrooms = promotion.get("bedrooms", "No indicado")
    penthouse = promotion.get("penthouse", False)
    url = promotion.get("url", "")
    score = promotion.get("score", promotion.get("points", 0))
    priority = promotion.get("priority", "NORMAL")

    penthouse_icon = "🏠 Sí" if penthouse else "—"

    message = (
        "🚨 *NUEVA PROMOCIÓN VPPL*\n\n"
        f"🏢 *{title}*\n\n"
        f"📍 Ciudad: {city}\n"
        f"🏗 Promotora: {source}\n"
        f"🛏 Dormitorios: {bedrooms}\n"
        f"🏠 Ático: {penthouse_icon}\n"
        f"⭐ Prioridad: {priority}\n"
        f"📊 Puntuación: {score}\n"
    )

    if url:
        message += f"\n🔗 {url}"

    return message