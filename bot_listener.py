# -*- coding: utf-8 -*-
"""
Telegram'dan gelen mesajları dinleyip, kural tabanlı olarak cache.json
içindeki en son veriyle cevap veren sürekli çalışan bot.

Bu script main.py'dan AYRIDIR ve arka planda SÜREKLİ açık kalması gerekir
(cron/Task Scheduler ile değil — kurulum talimatları README.md'de).

Kullanım:
    python bot_listener.py
"""

import time
import requests

from config import TELEGRAM_BOT_TOKEN
import auth
from data_cache import load_cache

API_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"


def help_text() -> str:
    return (
        "Merhaba! Şu formatlarda soru sorabilirsin:\n\n"
        "• `ASELS rsi` — RSI değeri ve yorumu\n"
        "• `ASELS macd` — MACD durumu\n"
        "• `ASELS trend` — kısa/uzun vadeli trend\n"
        "• `ASELS haber` — son haberler ve duyarlılık\n"
        "• `ASELS tahmin` — önümüzdeki ay için istatistiksel aralık + AI yorumu\n"
        "• `ASELS volatilite` — EGARCH volatilite rejimi (düşük/normal/yüksek)\n"
        "• `ASELS arge` — AR-GE yoğunluğu ve verimlilik katsayısı (çeyreklik veri)\n"
        "• `ASELS grafik` — Fiyat/RSI/MACD grafiklerinin AI ile görsel okuması\n"
        "• `ASELS tavan` — yeni halka arz ise tavan/taban seri analizi (sadece yakın zamanda halka arz olmuş hisselerde)\n"
        "• `ASELS özet` — tüm bilgilerin özeti\n"
        "• `yardım` — bu mesajı tekrar gösterir\n\n"
        f"Takip edilen hisseler: {', '.join(auth.get_all_tracked_tickers())}"
    )


def find_ticker(text: str):
    text_upper = text.upper()
    for t in auth.get_all_tracked_tickers():
        if t in text_upper:
            return t
    return None


def answer_question(text: str) -> str:
    text_lower = text.lower().strip()

    if text_lower in ("yardım", "/start", "/help", "help"):
        return help_text()

    ticker = find_ticker(text)
    if not ticker:
        return (
            "Hangi hisseyi sorduğunu anlayamadım. "
            f"Takip edilen hisseler: {', '.join(auth.get_all_tracked_tickers())}\n\n"
            "Örnek: `ASELS rsi` — 'yardım' yazarak tüm komutları görebilirsin."
        )

    return _answer_for_ticker(ticker, text_lower)


def answer_for_ticker(ticker: str, text: str) -> str:
    """
    Web paneldeki hisse-bazlı chat kutusu için: hisse zaten sayfadan belli
    olduğundan (find_ticker'a gerek yok) kullanıcı sadece 'rsi', 'trend' vb.
    yazabilir. answer_question ile aynı komut kümesini kullanır.
    """
    ticker = ticker.upper()
    if ticker not in auth.get_all_tracked_tickers():
        return f"{ticker} takip edilmiyor."
    return _answer_for_ticker(ticker, text.lower().strip())


def _answer_for_ticker(ticker: str, text_lower: str) -> str:
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

    if "tahmin" in text_lower or "forecast" in text_lower:
        forecast = data.get("forecast") or {}
        if not forecast.get("available"):
            return (
                f"📐 {ticker} için istatistiksel aralık hesaplanamamış "
                f"({forecast.get('reason', 'yetersiz veri')})."
            )
        lines = [
            f"📐 {ticker} İstatistiksel Aralık ({forecast['horizon_days']} işlem günü sonrası)",
            f"%10-%90 aralık: {forecast['p10']} TL – {forecast['p90']} TL "
            f"(medyan {forecast['median']} TL, %{forecast['median_change_pct']:+.2f})",
            "Not: Bu bir tahmin/garanti değil — geçmiş volatiliteye dayalı "
            "istatistiksel bir aralık.",
        ]
        ai_comment = data.get("ai_comment")
        if ai_comment:
            lines.append("")
            lines.append(ai_comment)
        lines.append(f"(Veri güncelleme: {updated_at})")
        return "\n".join(lines)

    if "volatilite" in text_lower or "rejim" in text_lower:
        vol = data.get("volatility") or {}
        if not vol.get("available"):
            return (
                f"📉 {ticker} için volatilite rejimi hesaplanamamış "
                f"({vol.get('reason', 'yetersiz veri')})."
            )
        lines = [
            f"📉 {ticker} Volatilite Rejimi: {vol['regime']} "
            f"(güncel koşullu volatilite: %{vol['current_volatility_pct']})",
        ]
        if vol.get("leverage_ratio_30d") is not None:
            lines.append(
                f"Kaldıraç etkisi (son 30 gün): düşüş günleri, yükseliş "
                f"günlerine göre {vol['leverage_ratio_30d']}× daha volatil."
            )
        lines.append("Not: Bu bir tahmin değil, EGARCH ile geçmiş fiyat hareketinden hesaplanan güncel durumdur.")
        lines.append(f"(Veri güncelleme: {updated_at})")
        return "\n".join(lines)

    if "arge" in text_lower or "ar-ge" in text_lower or "ar ge" in text_lower:
        rd = data.get("rd_signal") or {}
        if not rd.get("available"):
            return (
                f"🔬 {ticker} için AR-GE sinyali henüz hesaplanmamış "
                f"({rd.get('reason', 'python arge_sinyali.py çalıştırılmalı')})."
            )
        lines = [
            f"🔬 {ticker} AR-GE Yoğunluğu (ort. {len(rd['years_used'])} yıl): "
            f"%{rd['avg_intensity'] * 100:.1f} ({rd['trend'].lower()})",
        ]
        if rd.get("efficiency_ratio") is not None:
            lines.append(f"Verimlilik Katsayısı (bilgilendirici oran): {rd['efficiency_ratio']}")
        lines.append(f"Grup: {rd['group']}")
        lines.append("Not: Bu doğrulanmış bir yatırım sinyali değil, basit bir özet orandır.")
        return "\n".join(lines)

    if "tavan" in text_lower or "taban" in text_lower or "halka arz" in text_lower or "ipo" in text_lower:
        ipo = data.get("ipo_signal") or {}
        if not ipo.get("available"):
            return f"🆕 {ticker} yeni halka arz olarak sınıflandırılmadı ya da bu analiz için veri yok."
        lines = [f"🆕 {ticker} Yeni Halka Arz — Tavan/Taban Seri Analizi"]
        if ipo.get("current_streak_type"):
            lines.append(f"Mevcut seri: {ipo['current_streak_length']} gündür üst üste {ipo['current_streak_type']}.")
        else:
            lines.append("Şu anda aktif bir tavan/taban serisi yok.")
        lines.append(
            f"Bugüne kadar: {ipo['total_tavan_days']} tavan, {ipo['total_taban_days']} taban günü "
            f"(borsaya giriş: {ipo['listing_date']})."
        )
        lines.append(f"En uzun seri: tavan {ipo['longest_tavan_streak']} gün, taban {ipo['longest_taban_streak']} gün.")
        bs = ipo.get("break_stats") or {}
        if bs.get("available"):
            lines.append(
                f"Geçmiş kırılan {bs['sample_size']} tavan serisinden sonra 5 günlük ort. getiri: "
                f"%{bs['avg_return_5d_pct']:+.2f} (pozitif oran: %{bs['win_rate']})."
            )
        else:
            lines.append(bs.get("reason", "Kırılma sonrası istatistiği için yeterli geçmiş yok."))
        if ipo.get("ai_assessment"):
            lines.append("")
            lines.append(f"AI Değerlendirmesi (spekülatif): {ipo['ai_assessment']}")
        else:
            lines.append("Not: Bu bir gelecek tahmini değildir — 'kaç tavan daha yapar' sorusuna kesin cevap üretilemez.")
        return "\n".join(lines)

    if "grafik" in text_lower or "chart" in text_lower:
        readings = data.get("chart_readings") or {}
        if not any(readings.values()):
            return (
                f"🖼️ {ticker} için grafik okuması henüz yok "
                "(ANTHROPIC_API_KEY ayarlı değil ya da üretim başarısız oldu)."
            )
        labels = {"price": "Fiyat/SMA", "rsi": "RSI", "macd": "MACD"}
        lines = [f"🖼️ {ticker} Grafik Okumaları (AI, görsel)"]
        for key, label in labels.items():
            if readings.get(key):
                lines.append(f"\n{label}: {readings[key]}")
        lines.append(f"\n(Veri güncelleme: {updated_at})")
        return "\n".join(lines)

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
        f"Bu soruyu anlayamadım. {ticker} için 'rsi', 'macd', 'trend', 'haber', "
        "'tahmin', 'volatilite', 'arge', 'grafik' veya 'tavan' yazabilirsin. Tüm "
        "komutlar için 'yardım' yaz."
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
