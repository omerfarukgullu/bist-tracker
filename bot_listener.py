# -*- coding: utf-8 -*-
"""
Telegram'dan gelen mesajları dinleyip, kural tabanlı olarak cache.json
içindeki en son veriyle cevap veren sürekli çalışan bot.

Bu script main.py'dan AYRIDIR ve arka planda SÜREKLİ açık kalması gerekir
(cron/Task Scheduler ile değil — kurulum talimatları README.md'de).

Kullanım:
    python bot_listener.py
"""

import re
import time
import requests

from config import TICKERS, TELEGRAM_BOT_TOKEN
from data_cache import load_cache

API_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"

HELP_TEXT = (
    "Merhaba! Şu formatlarda soru sorabilirsin:\n\n"
    "• `ASELS rsi` — RSI değeri ve yorumu\n"
    "• `ASELS macd` — MACD durumu\n"
    "• `ASELS trend` — kısa/uzun vadeli trend\n"
    "• `ASELS haber` — son haberler ve duyarlılık\n"
    "• `ASELS özet` — tüm bilgilerin özeti\n"
    "• `yardım` — bu mesajı tekrar gösterir\n\n"
    f"Takip edilen hisseler: {', '.join(TICKERS)}"
)


def find_ticker(text: str):
    text_upper = text.upper()
    for t in TICKERS:
        if t in text_upper:
            return t
    return None


def answer_question(text: str) -> str:
    text_lower = text.lower().strip()

    if text_lower in ("yardım", "/start", "/help", "help"):
        return HELP_TEXT

    ticker = find_ticker(text)
    if not ticker:
        return (
            "Hangi hisseyi sorduğunu anlayamadım. "
            f"Takip edilen hisseler: {', '.join(TICKERS)}\n\n"
            "Örnek: `ASELS rsi` — 'yardım' yazarak tüm komutları görebilirsin."
        )

    cache = load_cache()
    tickers_data = cache.get("tickers", {})
    if ticker not in tickers_data:
        return f"{ticker} için henüz veri yok. Önce main.py çalıştırılmış olmalı."

    data = tickers_data[ticker]
    ind = data["indicators"]
    snapshot = data["snapshot"]
    sentiment = data["sentiment"]
    news = data["news"]
    updated_at = cache.get("updated_at", "bilinmiyor")

    if "rsi" in text_lower:
        return (
            f"📊 {ticker} RSI: {ind['rsi']} — {ind['rsi_note']}\n"
            f"(Veri güncelleme: {updated_at})"
        )

    if "macd" in text_lower:
        return (
            f"📊 {ticker} MACD: {ind['macd']} / Sinyal: {ind['macd_signal']}\n"
            f"{ind['macd_note']}\n(Veri güncelleme: {updated_at})"
        )

    if "trend" in text_lower or "ortalama" in text_lower:
        return (
            f"📈 {ticker} Trend: SMA20={ind['sma_short']}, SMA50={ind['sma_long']}\n"
            f"{ind['trend_note']}\n(Veri güncelleme: {updated_at})"
        )

    if "haber" in text_lower or "duyarlılık" in text_lower or "duyarlilik" in text_lower:
        lines = [f"📰 {ticker} Haber Duyarlılığı: {sentiment['label']} (skor: {sentiment['average_score']})"]
        for item in news[:3]:
            lines.append(f"- {item['title']}")
        lines.append(f"(Veri güncelleme: {updated_at})")
        return "\n".join(lines)

    if "özet" in text_lower or "ozet" in text_lower or "durum" in text_lower:
        return (
            f"📋 {ticker} Özet ({updated_at})\n\n"
            f"Son Kapanış: {snapshot['last_close']} TL ({snapshot['change_pct']:+.2f}%)\n"
            f"RSI: {ind['rsi']} — {ind['rsi_note']}\n"
            f"MACD: {ind['macd_note']}\n"
            f"Trend: {ind['trend_note']}\n"
            f"Haber Duyarlılığı: {sentiment['label']}"
        )

    return (
        f"Bu soruyu anlayamadım. {ticker} için 'rsi', 'macd', 'trend', 'haber' "
        "veya 'özet' yazabilirsin. Tüm komutlar için 'yardım' yaz."
    )


def send_reply(chat_id: str, text: str):
    requests.post(f"{API_URL}/sendMessage", data={"chat_id": chat_id, "text": text}, timeout=15)


def run():
    print("Bot dinlemeye başladı. Durdurmak için Ctrl+C.")
    offset = None

    while True:
        try:
            params = {"timeout": 30}
            if offset:
                params["offset"] = offset

            resp = requests.get(f"{API_URL}/getUpdates", params=params, timeout=35)
            updates = resp.json().get("result", [])

            for update in updates:
                offset = update["update_id"] + 1
                message = update.get("message", {})
                text = message.get("text", "")
                chat_id = message.get("chat", {}).get("id")

                if text and chat_id:
                    print(f"Gelen mesaj: {text}")
                    reply = answer_question(text)
                    send_reply(chat_id, reply)

        except requests.RequestException as e:
            print(f"Bağlantı hatası, 5 saniye sonra tekrar denenecek: {e}")
            time.sleep(5)
        except KeyboardInterrupt:
            print("\nBot durduruldu.")
            break


if __name__ == "__main__":
    run()
