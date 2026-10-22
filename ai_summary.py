# -*- coding: utf-8 -*-
"""
İsteğe bağlı: Hesaplanan gösterge + haber duyarlılığı + istatistiksel
aralık verisini Claude API ile okunabilir bir Türkçe paragrafa çevirir.

ÖNEMLİ: AI burada SADECE var olan veriyi yorumluyor — kendi başına fiyat
üretmiyor, tahmin yapmıyor, al/sat tavsiyesi vermiyor. ANTHROPIC_API_KEY
ortam değişkeni girilmemişse bu özellik tamamen devre dışı kalır; main.py
diğer her şeyi (göstergeler, istatistiksel aralık, Telegram gönderimi)
eskisi gibi üretmeye devam eder.
"""

from typing import Optional

import anthropic
from config import ANTHROPIC_API_KEY

SYSTEM_PROMPT = (
    "Sen bir BIST hisse takip aracının parçasısın. Sana bir hisse için "
    "önceden hesaplanmış teknik göstergeler, haber duyarlılığı ve geçmiş "
    "volatiliteye dayalı istatistiksel bir olasılık aralığı veriliyor. "
    "Görevin bu veriyi 3-5 cümlelik bir Türkçe paragrafta sentezlemek.\n\n"
    "DİL VE ÜSLUP (ÇOK ÖNEMLİ):\n"
    "- Okuyucunun borsa/finans hakkında HİÇBİR bilgisi olmadığını varsay. "
    "Sanki bir arkadaşına anlatıyormuşsun gibi sade, günlük konuşma "
    "diline yakın cümleler kur.\n"
    "- 'RSI', 'MACD', 'SMA', 'volatilite', 'momentum' gibi bir terim "
    "kullanman gerekiyorsa, yanına parantez içinde tek cümlelik çok sade "
    "bir açıklama ekle (ör. 'RSI (hissenin son dönemde ne kadar hızlı "
    "alınıp satıldığını gösteren bir gösterge)').\n"
    "- Kısa cümleler kur, uzun ve iç içe geçmiş cümlelerden kaçın.\n\n"
    "KESİN KURALLAR:\n"
    "- Al/sat tavsiyesi verme, 'yükselecek/düşecek' gibi kesin tahminlerde "
    "bulunma.\n"
    "- İstatistiksel aralığı sunarken bunun bir GARANTİ olmadığını, geçmiş "
    "volatiliteye dayalı bir olasılık tahmini olduğunu netçe belirt.\n"
    "- Sadece sana verilen veriyi yorumla; kendi bilgin ile hisse hakkında "
    "ek iddialarda bulunma.\n"
    "- Yatırım tavsiyesi olmadığını ayrıca hatırlatmana gerek yok, bu zaten "
    "raporun başka bir yerinde belirtiliyor — direkt veri sentezine odaklan."
)


def _is_enabled() -> bool:
    return bool(ANTHROPIC_API_KEY)


def _format_backtest(bt: dict) -> str:
    if bt.get("sample_size", 0) == 0:
        return "örneklem yok (bu koşul son dönemde hiç oluşmamış)"
    return f"{bt['sample_size']} örnek, ortalama getiri %{bt['avg_return_pct']}"


def _format_forecast(forecast: dict) -> str:
    if not forecast or not forecast.get("available"):
        reason = (forecast or {}).get("reason", "yetersiz veri")
        return f"hesaplanamadı ({reason})"
    return (
        f"{forecast['horizon_days']} işlem günü sonrası %10-%90 aralık: "
        f"{forecast['p10']} TL ile {forecast['p90']} TL arası "
        f"(medyan {forecast['median']} TL, %{forecast['median_change_pct']:+.2f} değişim)"
    )


def build_summary(ticker: str, snapshot: dict, ind: dict, sentiment: dict,
                   bt: dict, forecast: dict) -> Optional[str]:
    """AI destekli veri sentezi paragrafı üretir. Ayarlanmamışsa/hata olursa None döner."""
    if not _is_enabled():
        return None

    user_content = (
        f"Hisse: {ticker}\n"
        f"Son kapanış: {snapshot['last_close']} TL "
        f"({snapshot['change_pct']:+.2f}%, {snapshot['date']})\n\n"
        f"Teknik göstergeler:\n"
        f"- RSI: {ind['rsi']} ({ind['rsi_note']})\n"
        f"- MACD: {ind['macd_note']}\n"
        f"- Trend: {ind['trend_note']}\n\n"
        f"Haber duyarlılığı: {sentiment['label']} ({sentiment['count']} haber tarandı)\n\n"
        f"Geçmiş istatistik (RSI aşırı satım sonrası 5 gün): {_format_backtest(bt)}\n\n"
        f"Önümüzdeki ay için istatistiksel aralık (Monte Carlo): {_format_forecast(forecast)}\n"
    )

    try:
        client = anthropic.Anthropic()
        response = client.messages.create(
            model="claude-opus-5",
            # Claude Opus 5'te düşünme (thinking) varsayılan olarak açık ve
            # düşünme token'ları max_tokens'tan düşüyor. 768/1024 gibi dar bir
            # sınır, düşünme bütçeyi yediğinde cevabın yarıda kesilmesine ya
            # da hiç metin dönmemesine yol açıyordu. Sınır sadece bir tavan —
            # yalnızca gerçekten üretilen token ücretlendirilir.
            max_tokens=16000,
            output_config={"effort": "low"},
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_content}],
        )
        if response.stop_reason == "refusal":
            print(f"[{ticker}] AI özet reddedildi (refusal).")
            return None
        if response.stop_reason == "max_tokens":
            print(f"[{ticker}] AI özet token sınırında kesildi — yarım metin gösterilmiyor.")
            return None
        return next((b.text for b in response.content if b.type == "text"), None)
    except Exception as e:
        print(f"[{ticker}] AI özet üretilemedi: {e}")
        return None
