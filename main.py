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

import json
import os
import sys
import traceback
from datetime import datetime

from config import OUTPUT_DIR, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, RD_CACHE_FILE
import auth
from price_data import fetch_history, latest_snapshot
from indicators import analyze
from news_sentiment import fetch_news, summarize_sentiment
from backtest import rsi_oversold_stats
from forecast import simulate_forecast
from ai_summary import build_summary
from grafik_okuma import build_chart_readings
from volatilite_rejimi import fetch_long_history, compute_volatility_regime
from halka_arz_sinyali import (
    fetch_ipo_index_tickers, fetch_full_history, compute_ipo_signal, build_ai_assessment,
)
from report_generator import build_ticker_section, build_report
from data_cache import save_cache, load_cache
from telegram_sender import send_message


def load_rd_cache() -> dict:
    """arge_sinyali.py'nin ayrı olarak ürettiği son AR-GE sinyali cache'ini okur."""
    if not os.path.exists(RD_CACHE_FILE):
        return {}
    with open(RD_CACHE_FILE, "r", encoding="utf-8") as f:
        return json.load(f).get("tickers", {})


def process_ticker(ticker: str, rd_cache: dict = None, ipo_index_tickers=None):
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

    print(f"[{ticker}] İstatistiksel aralık simüle ediliyor...")
    forecast = simulate_forecast(df)

    print(f"[{ticker}] Volatilite rejimi hesaplanıyor (EGARCH)...")
    try:
        long_df = fetch_long_history(ticker)
        volatility = compute_volatility_regime(long_df)
    except Exception as e:
        volatility = {"available": False, "reason": str(e)}

    # AR-GE sinyali günlük hesaplanmaz — arge_sinyali.py'nin ayrı ürettiği
    # son sonuç varsa cache'den okunur.
    rd = (rd_cache or {}).get(ticker)

    print(f"[{ticker}] AI özeti üretiliyor (ANTHROPIC_API_KEY ayarlıysa)...")
    ai_comment = build_summary(ticker, snapshot, ind, sentiment, bt, forecast)

    print(f"[{ticker}] Grafik okumaları üretiliyor (Fiyat/RSI/MACD, ANTHROPIC_API_KEY ayarlıysa)...")
    chart_readings = build_chart_readings(ticker, df)

    print(f"[{ticker}] Yeni halka arz / tavan-taban seri analizi yapılıyor...")
    try:
        ipo_df = fetch_full_history(ticker)
        ipo_signal = compute_ipo_signal(ticker, ipo_df, ipo_index_tickers)
        if ipo_signal.get("available"):
            ipo_signal["ai_assessment"] = build_ai_assessment(
                ticker, ipo_signal, ipo_df, news_items, sentiment
            )
    except Exception as e:
        ipo_signal = {"available": False, "reason": str(e)}

    section = build_ticker_section(
        ticker, snapshot, ind, news_items, sentiment, bt, forecast, ai_comment,
        volatility=volatility, rd=rd, chart_readings=chart_readings, ipo_signal=ipo_signal,
    )
    raw = {
        "snapshot": snapshot,
        "indicators": ind,
        "news": news_items,
        "sentiment": sentiment,
        "backtest": bt,
        "forecast": forecast,
        "ai_comment": ai_comment,
        "volatility": volatility,
        "rd_signal": rd,
        "chart_readings": chart_readings,
        "ipo_signal": ipo_signal,
    }
    return section, raw


def refresh_price_data() -> None:
    """
    Fiyat/gösterge/backtest/istatistiksel aralık verisini ve tavan/taban
    seri istatistiklerini günceller. Haberleri yeniden taramaz, AI yorumu/
    AI halka arz değerlendirmesi üretmez, Telegram'a mesaj göndermez —
    bunlar cache'de olduğu gibi korunur. Tavan/taban SERİ İSTATİSTİKLERİ
    (ai_assessment hariç) burada da güncellenir çünkü fiyata dayalı ve hızlı
    değişebilir — özellikle çok taze halka arzlarda günlük tek güncelleme
    saatlerce eski kalabilir. Web app'in arka planda sık aralıklarla
    (PRICE_REFRESH_MINUTES) hafifçe tazelenmesi içindir; günlük tam analiz
    (main()) ayrı ve bağımsız çalışır.
    """
    cache = load_cache()
    tickers_data = cache.get("tickers", {})
    ipo_index_tickers = fetch_ipo_index_tickers()

    for ticker in auth.get_all_tracked_tickers():
        existing = tickers_data.get(ticker)
        if existing is None:
            # Bu hisse için henüz hiç tam analiz (main()) çalışmamış —
            # haber/duyarlılık/AI yorumu olmadan yarım bir kayıt yazıp web
            # app'i bozmamak için hafif yenilemeyi atla; ilk tam veri
            # günlük analizle gelecek.
            continue

        try:
            df = fetch_history(ticker)
            snapshot = latest_snapshot(df)
            ind = analyze(df)
            bt = rsi_oversold_stats(df)
            forecast = simulate_forecast(df)
        except Exception as e:
            print(f"[{ticker}] Fiyat yenileme hatası: {e}", file=sys.stderr)
            continue

        ipo_signal = existing.get("ipo_signal")
        try:
            ipo_df = fetch_full_history(ticker)
            new_ipo_signal = compute_ipo_signal(ticker, ipo_df, ipo_index_tickers)
            if new_ipo_signal.get("available"):
                # AI değerlendirmesi pahalı/yavaş üretiliyor — burada tekrar
                # üretilmez, mevcut (varsa) değeri korunur.
                new_ipo_signal["ai_assessment"] = (existing.get("ipo_signal") or {}).get("ai_assessment")
            ipo_signal = new_ipo_signal
        except Exception as e:
            print(f"[{ticker}] Halka arz sinyali yenileme hatası: {e}", file=sys.stderr)

        tickers_data[ticker] = {
            **existing,
            "snapshot": snapshot,
            "indicators": ind,
            "backtest": bt,
            "forecast": forecast,
            "ipo_signal": ipo_signal,
        }

    save_cache(tickers_data)


def _telegram_ready() -> bool:
    return bool(TELEGRAM_BOT_TOKEN) and "BURAYA" not in TELEGRAM_BOT_TOKEN


def _send_alert(text: str) -> None:
    """Hata durumunda Telegram'a ayrı, kısa bir uyarı mesajı gönderir."""
    if not _telegram_ready():
        return
    if not send_message(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, text):
        print("Telegram uyarı mesajı gönderilemedi.", file=sys.stderr)


def main():
    print(f"=== BIST Tracker — {datetime.now().strftime('%Y-%m-%d %H:%M')} ===\n")

    sections = []
    # Mevcut cache'in üzerine yazılır, sıfırdan kurulmaz: bir hissenin verisi
    # geçici bir ağ hatası yüzünden çekilemediğinde o hissenin ÖNCEKİ verisi
    # korunur. (Önceden boş dict ile başlanıp save_cache çağrıldığı için
    # başarısız olan her hissenin cache kaydı tamamen siliniyordu.)
    tracked = auth.get_all_tracked_tickers()
    cache_data = dict(load_cache().get("tickers", {}))
    failed = []  # (ticker, hata mesajı) çiftleri
    rd_cache = load_rd_cache()
    ipo_index_tickers = fetch_ipo_index_tickers()

    for ticker in tracked:
        try:
            section, raw = process_ticker(ticker, rd_cache, ipo_index_tickers)
            sections.append(section)
            cache_data[ticker] = raw
        except Exception as e:
            print(f"[{ticker}] HATA: {e}", file=sys.stderr)
            traceback.print_exc()
            failed.append((ticker, str(e)))
            sections.append(
                f"## {ticker}\n\n⚠️ Bu hisse için veri alınamadı: {e}\n\n---\n"
            )

    if failed:
        alert_lines = [f"⚠️ BIST Tracker: {len(failed)} hisse için veri kaynağına ulaşılamadı."]
        alert_lines += [f"- {ticker}: {err}" for ticker, err in failed]
        _send_alert("\n".join(alert_lines))

    try:
        filename = build_report(sections, OUTPUT_DIR)
        print(f"\nRapor oluşturuldu: {filename}")

        # Artık takip edilmeyen hisseler cache'i sonsuza kadar büyütmesin.
        cache_data = {t: d for t, d in cache_data.items() if t in tracked}

        # Bot Q&A özelliğinin son verileri okuyabilmesi için cache'i kaydet
        save_cache(cache_data)
        print("Cache güncellendi (bot_listener.py bu veriyi kullanacak).")
    except Exception as e:
        print(f"HATA: Rapor/cache oluşturulamadı: {e}", file=sys.stderr)
        traceback.print_exc()
        _send_alert(f"🔴 BIST Tracker: Günlük analiz tamamen başarısız oldu — {e}")
        raise

    # Telegram'a gönder (token/chat_id ayarlanmışsa)
    if _telegram_ready():
        with open(filename, "r", encoding="utf-8") as f:
            report_text = f.read()
        ok = send_message(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, report_text)
        print("Telegram'a gönderildi." if ok else "Telegram gönderimi başarısız oldu.")
    else:
        print("Telegram ayarları yapılmamış (config.py'de TOKEN/CHAT_ID gir) — mesaj gönderilmedi.")


if __name__ == "__main__":
    main()
