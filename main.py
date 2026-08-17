# -*- coding: utf-8 -*-
"""
Ana çalıştırma dosyası. Her gün otomatik çalıştırıldığında:
1. Her hisse için fiyat verisini çeker
2. Teknik göstergeleri hesaplar
3. Haberleri tarayıp duyarlılık skoru çıkarır
4. Basit backtest istatistiği üretir
5. Hepsini tek bir Markdown raporunda birleştirir

Kullanım:
    python main.py
"""

import sys
import traceback
from datetime import datetime

from config import TICKERS, OUTPUT_DIR, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
from price_data import fetch_history, latest_snapshot
from indicators import analyze
from news_sentiment import fetch_news, summarize_sentiment
from backtest import rsi_oversold_stats
from report_generator import build_ticker_section, build_report
from data_cache import save_cache
from telegram_sender import send_message


def process_ticker(ticker: str):
    print(f"[{ticker}] Fiyat verisi çekiliyor...")
    df = fetch_history(ticker)
    snapshot = latest_snapshot(df)

    print(f"[{ticker}] Göstergeler hesaplanıyor...")
    ind = analyze(df)

    print(f"[{ticker}] Haberler taranıyor...")
    news_items = fetch_news(ticker)
    sentiment = summarize_sentiment(news_items)

    print(f"[{ticker}] Geçmiş istatistik hesaplanıyor...")
    bt = rsi_oversold_stats(df)

    section = build_ticker_section(ticker, snapshot, ind, news_items, sentiment, bt)
    raw = {
        "snapshot": snapshot,
        "indicators": ind,
        "news": news_items,
        "sentiment": sentiment,
        "backtest": bt,
    }
    return section, raw


def main():
    print(f"=== BIST Takip Botu — {datetime.now().strftime('%Y-%m-%d %H:%M')} ===\n")

    sections = []
    cache_data = {}

    for ticker in TICKERS:
        try:
            section, raw = process_ticker(ticker)
            sections.append(section)
            cache_data[ticker] = raw
        except Exception as e:
            print(f"[{ticker}] HATA: {e}", file=sys.stderr)
            traceback.print_exc()
            sections.append(
                f"## {ticker}\n\n⚠️ Bu hisse için veri alınamadı: {e}\n\n---\n"
            )

    filename = build_report(sections, OUTPUT_DIR)
    print(f"\nRapor oluşturuldu: {filename}")

    # Bot Q&A özelliğinin son verileri okuyabilmesi için cache'i kaydet
    save_cache(cache_data)
    print("Cache güncellendi (bot_listener.py bu veriyi kullanacak).")

    # Telegram'a gönder (token/chat_id ayarlanmışsa)
    if TELEGRAM_BOT_TOKEN and "BURAYA" not in TELEGRAM_BOT_TOKEN:
        with open(filename, "r", encoding="utf-8") as f:
            report_text = f.read()
        ok = send_message(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, report_text)
        print("Telegram'a gönderildi." if ok else "Telegram gönderimi başarısız oldu.")
    else:
        print("Telegram ayarları yapılmamış (config.py'de TOKEN/CHAT_ID gir) — mesaj gönderilmedi.")


if __name__ == "__main__":
    main()
