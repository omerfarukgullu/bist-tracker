# -*- coding: utf-8 -*-
"""
Telegram Bot API üzerinden mesaj gönderme yardımcı fonksiyonları.
"""

import requests

TELEGRAM_MAX_LEN = 4000  # Telegram limiti 4096, güvenlik payı bırakıyoruz


def send_message(token: str, chat_id: str, text: str) -> bool:
    """
    Verilen metni Telegram'a gönderir. Metin uzunsa otomatik parçalara böler.
    Başarılıysa True, hata varsa False döner (hata detayını ekrana basar).
    """
    url = f"https://api.telegram.org/bot{token}/sendMessage"

    chunks = [text[i:i + TELEGRAM_MAX_LEN] for i in range(0, len(text), TELEGRAM_MAX_LEN)] or [text]

    for chunk in chunks:
        try:
            resp = requests.post(url, data={
                "chat_id": chat_id,
                "text": chunk,
                # parse_mode kasıtlı olarak KULLANILMIYOR: haber başlıklarında
                # geçen *, _, [, ] gibi karakterler Markdown/HTML parse
                # hatasına yol açıyordu. Düz metin her zaman güvenli gönderilir.
                "disable_web_page_preview": True,
            }, timeout=15)
            if not resp.ok:
                print(f"Telegram gönderim hatası: {resp.status_code} {resp.text}")
                return False
        except requests.RequestException as e:
            print(f"Telegram bağlantı hatası: {e}")
            return False

    return True
