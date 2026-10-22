# -*- coding: utf-8 -*-
"""
Web panel için Türkçe/İngilizce dil desteği.

Kapsam: statik arayüz metinleri (t()) ve backend'in ürettiği sabit/az
sayıda değer alan Türkçe not metinleri (tn() — RSI/MACD/trend notları,
volatilite rejimi, AR-GE grubu/trendi, haber duyarlılığı etiketi).

KAPSAM DIŞI (bilinçli tercih): AI Yorumu, Grafik Okuması ve Telegram bot
mesajları günde bir kez üretiliyor ve önbelleğe yazılıyor — her görüntüleyen
için anlık iki dilde üretmek AI maliyetini ikiye katlardı, bu yüzden bu
içerikler her zaman üretildikleri dilde (Türkçe) kalır. Aynı şekilde
raporlar/*.md dosyaları da üretildikleri anda Türkçe yazılır, geriye dönük
çevrilmez. Web paneldeki chat kutusunun CEVAPLARI da bu kapsam dışı grupta —
bot_listener.answer_for_ticker() Telegram bot'uyla aynı kural tabanlı,
Türkçe-sabit mantığı kullanır (bkz. app.py /hisse/<ticker>/chat); sadece
chat kutusunun kendi arayüz metinleri (başlık, placeholder, hızlı soru
butonları) t() ile çevrilir.
"""

DEFAULT_LANG = "tr"
SUPPORTED_LANGS = ("tr", "en")

UI = {
    "tr": {
        "brand_text": "BIST Tracker",
        "nav_panel": "Panel",
        "nav_reports": "Raporlar",
        "nav_login": "Giriş Yap",
        "nav_register": "Kayıt Ol",
        "nav_logout": "Çıkış Yap",
        "theme_toggle": "Temayı değiştir",
        "lang_toggle": "Dili değiştir",

        "login_title": "Giriş Yap",
        "register_title": "Kayıt Ol",
        "field_username": "Kullanıcı Adı",
        "field_email": "E-posta",
        "field_password": "Şifre",
        "field_password_confirm": "Şifre (tekrar)",
        "login_btn": "Giriş Yap",
        "register_btn": "Kayıt Ol",
        "login_no_account": "Hesabın yok mu?",
        "register_have_account": "Zaten hesabın var mı?",
        "error_username_taken": "Bu kullanıcı adı zaten alınmış.",
        "error_invalid_credentials": "Kullanıcı adı veya şifre hatalı.",
        "error_passwords_mismatch": "Şifreler eşleşmiyor.",
        "error_password_too_short": "Şifre en az 6 karakter olmalı.",
        "error_username_invalid": "Kullanıcı adı 3-30 karakter olmalı, sadece harf/rakam/alt çizgi içerebilir.",
        "error_email_invalid": "Geçerli bir e-posta adresi gir.",

        "panel_title": "Panel",
        "last_updated": "Son güncelleme",
        "no_data_yet": "Henüz veri yok. İlk analiz çalıştığında burada görünecek.",
        "ticker_add_placeholder": "Hisse kodu ekle (ör. THYAO)",
        "ticker_add_btn": "+ Ekle",
        "ticker_add_hint": "BIST kodu doğrulanıp hemen ilk analiz çalıştırılır — birkaç saniye sürebilir.",
        "ticker_remove_confirm": "{ticker} takipten çıkarılsın mı?",
        "ticker_remove_title": "Takipten çıkar",
        "no_data": "Veri yok",

        "back_to_panel": "Panel",
        "no_ticker_data": "Bu hisse için henüz veri yok.",
        "volume": "İşlem Hacmi",
        "close_suffix": "kapanışı",
        "trend": "Trend",
        "uptrend": "Yükseliş ▲",
        "downtrend": "Düşüş ▼",
        "not_enough_data": "Yeterli veri yok",
        "volatility": "Volatilite",
        "daily_egarch": "günlük (EGARCH)",
        "could_not_calculate": "Hesaplanamadı.",

        "charts_title": "Grafikler",
        "chart_refresh_title": "Grafiği yenile",
        "tab_price": "Fiyat / SMA",
        "tab_rsi": "RSI",
        "tab_macd": "MACD",
        "tab_intraday": "Anlık",
        "range_daily": "Günlük",
        "range_weekly": "Haftalık",
        "range_monthly": "Aylık",
        "range_6m": "6 Aylık",
        "range_1y": "Yıllık",

        "chart_label_close": "Kapanış",
        "chart_label_overbought": "Aşırı alım (70)",
        "chart_label_oversold": "Aşırı satım (30)",
        "chart_label_histogram": "Histogram",
        "chart_label_signal": "Sinyal",
        "chart_label_price": "Fiyat",
        "chart_error_data": "Grafik verisi yüklenemedi.",
        "chart_error_generic": "Veri yüklenemedi.",
        "intraday_status_1d": "Son işlem günü: {date} — 5 dakikalık mumlar. 60 saniyede bir otomatik yenilenir (son yenileme: {time}).",
        "intraday_status_1w": "Son 5 işlem günü — 15 dakikalık mumlar.",
        "intraday_status_1mo": "Son 1 ay — 60 dakikalık mumlar.",
        "intraday_status_6mo": "Son 6 ay — günlük kapanışlar.",
        "intraday_status_1y": "Son 1 yıl — günlük kapanışlar.",

        "chart_reading_title": "Grafik Okuması (AI)",
        "chart_reading_missing": "Bu grafik için AI okuması yok (ANTHROPIC_API_KEY ayarlı değil ya da üretim başarısız oldu).",
        "chart_reading_intraday": "Anlık grafik için AI okuması üretilmiyor — bu okumalar günlük analizle (Fiyat/RSI/MACD) birlikte bir kez üretiliyor, sürekli değişen anlık grafiğe uymuyor.",
        "chart_reading_disclaimer": "Her sekme yukarıdaki ilgili grafiğin görsel olarak AI ile okunmuş halidir; sabit bir metin değildir. Yatırım tavsiyesi değildir.",

        "forecast_title": "Önümüzdeki Ay İçin İstatistiksel Aralık",
        "forecast_median": "medyan",
        "forecast_range_suffix": "işlem günü sonrası için %10-%90 persentil aralığı —",
        "forecast_disclaimer": "Bu bir tahmin/garanti değildir — geçmiş volatiliteye dayalı istatistiksel bir aralıktır. Gerçek fiyat bu aralığın dışında da kalabilir; trend veya haber gibi hiçbir sinyali hesaba katmaz.",

        "backtest_title": "Geçmiş İstatistik (RSI Aşırı Satım Sonrası, 5 gün)",
        "backtest_occurred": "Geçmişte {n} kez bu koşul oluşmuş.",
        "backtest_avg_return": "5 gün sonra ortalama getiri",
        "backtest_win_rate": "Pozitif kapanan durum oranı",
        "backtest_small_sample": "Küçük örneklem boyutları istatistiksel olarak güvenilir olmayabilir.",
        "backtest_none": "Son dönemde bu koşul (RSI ≤ 30) hiç oluşmamış.",

        "volatility_detail_title": "Volatilite Rejimi Detayı (EGARCH)",
        "leverage_effect": "Kaldıraç etkisi (son 30 gün): düşüş günlerinde ortalama koşullu volatilite, yükseliş günlerine göre {ratio}× (EGARCH asimetri katsayısı: {gamma}).",
        "volatility_disclaimer": "Bu bir volatilite tahmini değildir — geçmiş fiyat hareketlerinden hesaplanan güncel durumun özetidir. Yatırım tavsiyesi değildir.",
        "high_volatility_title": "Yüksek Volatilite Rejimi.",
        "high_volatility_note": "Fiyat hareketleri tarihsel olarak geniş bantta seyrediyor. Bu bir tavsiye değildir; pozisyon büyüklüğü ve stop-loss disiplinine dikkat etmek isteyebilirsin.",

        "ipo_title": "Yeni Halka Arz — Tavan/Taban Seri Analizi",
        "ipo_subtitle": "(yeni halka arz)",
        "ipo_current_streak": "Mevcut seri",
        "ipo_streak_days": "{n} gündür üst üste {type}",
        "ipo_no_streak": "Şu anda aktif bir tavan/taban serisi yok.",
        "ipo_summary": "Bugüne kadar {tavan} tavan günü, {taban} taban günü (borsaya giriş: {date}, {days} işlem günü geçti).",
        "ipo_longest": "En uzun tavan serisi {tavan} gün, en uzun taban serisi {taban} gün.",
        "ipo_break_stats": "Geçmişte kırılan {n} tavan serisinden sonraki 5 işlem gününde ortalama getiri: %{avg:+.2f} (pozitif kapanma oranı: %{win}).",
        "ipo_break_stats_none": "Bu hissede daha önce kırılan bir tavan serisi yok — geçmiş kırılma istatistiği üretilemiyor.",
        "ipo_ai_label": "AI Değerlendirmesi (spekülatif)",
        "ipo_disclaimer": "Bu bir GELECEK TAHMİNİ değildir — 'kaç tavan daha yapar' ya da 'ne zaman bozar' sorusuna kesin bir cevap üretilemez. Sadece hissenin kendi geçmişine dayalı şeffaf bir seri özetidir. Tavan/taban günleri, BIST'in standart günlük fiyat bandına (~%10) yakın getiri eşiğiyle yaklaşık olarak belirlenir. Yatırım tavsiyesi değildir.",

        "rd_title": "AR-GE Sinyali",
        "rd_subtitle": "(çeyreklik/yıllık)",
        "rd_intensity": "AR-GE Yoğunluğu",
        "rd_avg_years": "ortalama, son {n} yıl — {years}, trend: {trend}",
        "rd_efficiency": "Verimlilik Katsayısı (bilgilendirici oran)",
        "rd_group": "Grup (bilgilendirici sınıflandırma)",
        "rd_disclaimer": "Bu sınıflandırma ve oran doğrulanmış bir yatırım sinyali değildir — geçmiş AR-GE gideri/satış oranını geçmiş getiriyle karşılaştıran basit, şeffaf bir özet istatistiktir. Yatırım tavsiyesi değildir.",
        "rd_not_calculated": "Henüz hesaplanmamış (python arge_sinyali.py çalıştırılmalı).",

        "news_title": "Haber Duyarlılığı",
        "news_count_suffix": "haber",
        "news_score": "skor",

        "ai_comment_title": "AI Yorumu (Veri Sentezi)",
        "ai_comment_disclaimer": "Bu paragraf yukarıdaki veriler temel alınarak yapay zeka ile üretilmiştir; yeni bir analiz değil, mevcut verinin özetidir. Yatırım tavsiyesi değildir.",

        "chat_title": "Hisseye Soru Sor",
        "chat_subtitle": "Kayıtlı veriden anında cevap — kural tabanlı, yapay zeka değil.",
        "chat_placeholder": "Örn. rsi, trend, tahmin, özet...",
        "chat_send": "Gönder",
        "chat_empty_question": "Önce bir soru yaz.",
        "chat_error": "Cevap alınamadı, tekrar dener misin?",
        "chat_q_rsi": "RSI",
        "chat_q_macd": "MACD",
        "chat_q_trend": "Trend",
        "chat_q_forecast": "Tahmin",
        "chat_q_volatility": "Volatilite",
        "chat_q_rd": "AR-GE",
        "chat_q_news": "Haber",
        "chat_q_summary": "Özet",
        "chat_q_ipo": "Tavan/Taban",

        "reports_title": "Geçmiş Raporlar",
        "no_reports": "Henüz rapor yok.",
    },
    "en": {
        "brand_text": "BIST Tracker",
        "nav_panel": "Dashboard",
        "nav_reports": "Reports",
        "nav_login": "Log In",
        "nav_register": "Sign Up",
        "nav_logout": "Log Out",
        "theme_toggle": "Toggle theme",
        "lang_toggle": "Switch language",

        "login_title": "Log In",
        "register_title": "Sign Up",
        "field_username": "Username",
        "field_email": "Email",
        "field_password": "Password",
        "field_password_confirm": "Confirm Password",
        "login_btn": "Log In",
        "register_btn": "Sign Up",
        "login_no_account": "Don't have an account?",
        "register_have_account": "Already have an account?",
        "error_username_taken": "This username is already taken.",
        "error_invalid_credentials": "Incorrect username or password.",
        "error_passwords_mismatch": "Passwords don't match.",
        "error_password_too_short": "Password must be at least 6 characters.",
        "error_username_invalid": "Username must be 3-30 characters, letters/numbers/underscore only.",
        "error_email_invalid": "Enter a valid email address.",

        "panel_title": "Dashboard",
        "last_updated": "Last updated",
        "no_data_yet": "No data yet. This will appear once the first analysis runs.",
        "ticker_add_placeholder": "Add ticker code (e.g. THYAO)",
        "ticker_add_btn": "+ Add",
        "ticker_add_hint": "The BIST code is validated and the first analysis runs immediately — this may take a few seconds.",
        "ticker_remove_confirm": "Remove {ticker} from tracking?",
        "ticker_remove_title": "Remove from tracking",
        "no_data": "No data",

        "back_to_panel": "Dashboard",
        "no_ticker_data": "No data yet for this ticker.",
        "volume": "Trading Volume",
        "close_suffix": "close",
        "trend": "Trend",
        "uptrend": "Uptrend ▲",
        "downtrend": "Downtrend ▼",
        "not_enough_data": "Not enough data",
        "volatility": "Volatility",
        "daily_egarch": "daily (EGARCH)",
        "could_not_calculate": "Could not be calculated.",

        "charts_title": "Charts",
        "chart_refresh_title": "Refresh chart",
        "tab_price": "Price / SMA",
        "tab_rsi": "RSI",
        "tab_macd": "MACD",
        "tab_intraday": "Live",
        "range_daily": "Daily",
        "range_weekly": "Weekly",
        "range_monthly": "Monthly",
        "range_6m": "6 Months",
        "range_1y": "1 Year",

        "chart_label_close": "Close",
        "chart_label_overbought": "Overbought (70)",
        "chart_label_oversold": "Oversold (30)",
        "chart_label_histogram": "Histogram",
        "chart_label_signal": "Signal",
        "chart_label_price": "Price",
        "chart_error_data": "Failed to load chart data.",
        "chart_error_generic": "Failed to load data.",
        "intraday_status_1d": "Last trading day: {date} — 5-minute candles. Refreshes automatically every 60 seconds (last refresh: {time}).",
        "intraday_status_1w": "Last 5 trading days — 15-minute candles.",
        "intraday_status_1mo": "Last 1 month — 60-minute candles.",
        "intraday_status_6mo": "Last 6 months — daily closes.",
        "intraday_status_1y": "Last 1 year — daily closes.",

        "chart_reading_title": "Chart Reading (AI)",
        "chart_reading_missing": "No AI reading for this chart (ANTHROPIC_API_KEY not set, or generation failed).",
        "chart_reading_intraday": "No AI reading is generated for the live chart — these readings are produced once a day together with the Price/RSI/MACD analysis, which doesn't fit the constantly changing live chart.",
        "chart_reading_disclaimer": "Each tab shows that specific chart read visually by AI — it isn't fixed text. Not investment advice.",

        "forecast_title": "Statistical Range for the Next Month",
        "forecast_median": "median",
        "forecast_range_suffix": "trading days ahead, 10%-90% percentile range —",
        "forecast_disclaimer": "This is not a prediction or guarantee — it's a statistical range based on past volatility. The real price may fall outside this range; it does not factor in any signal such as trend or news.",

        "backtest_title": "Historical Statistics (5 Days After RSI Oversold)",
        "backtest_occurred": "This condition has occurred {n} times in the past.",
        "backtest_avg_return": "Average return after 5 days",
        "backtest_win_rate": "Share of cases closing positive",
        "backtest_small_sample": "Small sample sizes may not be statistically reliable.",
        "backtest_none": "This condition (RSI ≤ 30) hasn't occurred recently.",

        "volatility_detail_title": "Volatility Regime Detail (EGARCH)",
        "leverage_effect": "Leverage effect (last 30 days): average conditional volatility on down days is {ratio}× that of up days (EGARCH asymmetry coefficient: {gamma}).",
        "volatility_disclaimer": "This is not a volatility forecast — it's a summary of the current state calculated from past price movements. Not investment advice.",
        "high_volatility_title": "High Volatility Regime.",
        "high_volatility_note": "Price movements have historically ranged widely. This is not advice; you may want to pay attention to position sizing and stop-loss discipline.",

        "ipo_title": "New IPO — Limit-Up/Limit-Down Streak Analysis",
        "ipo_subtitle": "(recent IPO)",
        "ipo_current_streak": "Current streak",
        "ipo_streak_days": "{n} days in a row of {type}",
        "ipo_no_streak": "No active limit-up/limit-down streak right now.",
        "ipo_summary": "So far: {tavan} limit-up days, {taban} limit-down days (listed: {date}, {days} trading days so far).",
        "ipo_longest": "Longest limit-up streak: {tavan} days, longest limit-down streak: {taban} days.",
        "ipo_break_stats": "After the {n} previously broken limit-up streaks in this stock's history, the average return over the next 5 trading days was {avg:+.2f}% (positive-close rate: {win}%).",
        "ipo_break_stats_none": "No limit-up streak has broken before in this stock's history — no historical break statistic can be produced.",
        "ipo_ai_label": "AI Assessment (speculative)",
        "ipo_disclaimer": "This is NOT a future prediction — no method can honestly answer 'how many more limit-ups' or 'when will it break'. It's only a transparent summary based on the stock's own history. Limit-up/limit-down days are approximated using a return threshold close to BIST's standard daily price band (~10%). Not investment advice.",

        "rd_title": "R&D Signal",
        "rd_subtitle": "(quarterly/annual)",
        "rd_intensity": "R&D Intensity",
        "rd_avg_years": "average, last {n} years — {years}, trend: {trend}",
        "rd_efficiency": "Efficiency Ratio (informational)",
        "rd_group": "Group (informational classification)",
        "rd_disclaimer": "This classification and ratio is not a validated investment signal — it's a simple, transparent summary statistic comparing past R&D expense/sales ratio with past returns. Not investment advice.",
        "rd_not_calculated": "Not calculated yet (run python arge_sinyali.py).",

        "news_title": "News Sentiment",
        "news_count_suffix": "news items",
        "news_score": "score",

        "ai_comment_title": "AI Commentary (Data Synthesis)",
        "ai_comment_disclaimer": "This paragraph was generated by AI based on the data above; it's not a new analysis, just a summary of existing data. Not investment advice.",

        "chat_title": "Ask About This Stock",
        "chat_subtitle": "Instant answers from the stored data — rule-based, not AI.",
        "chat_placeholder": "e.g. rsi, trend, forecast, summary...",
        "chat_send": "Send",
        "chat_empty_question": "Type a question first.",
        "chat_error": "Couldn't get an answer, try again?",
        "chat_q_rsi": "RSI",
        "chat_q_macd": "MACD",
        "chat_q_trend": "Trend",
        "chat_q_forecast": "Forecast",
        "chat_q_volatility": "Volatility",
        "chat_q_rd": "R&D",
        "chat_q_news": "News",
        "chat_q_summary": "Summary",
        "chat_q_ipo": "Limit-up/down",

        "reports_title": "Past Reports",
        "no_reports": "No reports yet.",
    },
}

# Backend'in ürettiği sabit/az sayıda değer alan Türkçe not metinlerinin
# tam eşleşme çevirisi (RSI/MACD/trend notları, volatilite rejimi, AR-GE
# grubu/trendi, haber duyarlılığı etiketi, vb.)
NOTE_EXACT = {
    # indicators.py — rsi_note / macd_note / trend_note
    "Yeterli veri yok": "Not enough data",
    "Aşırı alım bölgesi": "Overbought zone",
    "Aşırı satım bölgesi": "Oversold zone",
    "Nötr bölge": "Neutral zone",
    "MACD sinyal çizgisinin üzerinde (pozitif momentum)": "MACD above signal line (positive momentum)",
    "MACD sinyal çizgisinin altında (negatif momentum)": "MACD below signal line (negative momentum)",
    "Kısa vadeli ortalama uzun vadelinin üzerinde (yükseliş eğilimi)": "Short-term average above long-term (uptrend)",
    "Kısa vadeli ortalama uzun vadelinin altında (düşüş eğilimi)": "Short-term average below long-term (downtrend)",
    "Trend için yeterli veri yok": "Not enough data for trend",

    # forecast.py
    "Monte Carlo (geometrik rastgele yürüyüş, geçmiş günlük log-getiri ortalama/std'sine dayalı)":
        "Monte Carlo (geometric random walk, based on the mean/std of past daily log returns)",
    "Volatilite hesaplanamadı.": "Could not calculate volatility.",

    # volatilite_rejimi.py — regime
    "Düşük": "Low",
    "Normal": "Normal",
    "Yüksek": "High",

    # halka_arz_sinyali.py — streak type
    "tavan": "limit-up",
    "taban": "limit-down",

    # arge_sinyali.py — trend / group
    "Artıyor": "Increasing",
    "Azalıyor": "Decreasing",
    "Stabil": "Stable",
    "Yetersiz veri": "Insufficient data",
    "Yüksek Getiri / Düşük AR-GE": "High Return / Low R&D",
    "Yüksek Getiri / Yüksek AR-GE": "High Return / High R&D",
    "Düşük Getiri / Yüksek AR-GE": "Low Return / High R&D",
    "Düşük Getiri / Düşük AR-GE": "Low Return / Low R&D",
    "AR-GE Yoğunluğu İhmal Edilebilir Düzeyde": "R&D Intensity Negligible",

    # news_sentiment.py — label
    "Genel olarak olumlu": "Generally positive",
    "Genel olarak olumsuz": "Generally negative",
    "Nötr / karışık": "Neutral / mixed",
    "Haber bulunamadı": "No news found",
}

# Dinamik (içine sayı/istisna metni gömülü) not metinleri için parça parça
# çeviri — tam eşleşme bulunamazsa bu değişiklikler sırayla uygulanır.
NOTE_PARTIALS = [
    ("Volatilite modeli için yeterli veri yok (en az", "Not enough data for the volatility model (at least"),
    ("gün gerekli,", "days required,"),
    ("var).", "available)."),
    ("Model uyumlanamadı:", "Model could not be fit:"),
    ("Yeterli geçmiş veri yok (en az", "Not enough historical data (at least"),
    ("gün gerekli).", "days required)."),
    ("için veri bulunamadı.", ": data not found."),
    ("için anlık veri bulunamadı.", ": no live data found."),
]


def t(key: str, lang: str = DEFAULT_LANG, **kwargs) -> str:
    """Statik arayüz metni çevirisi. Anahtar bulunamazsa anahtarın kendisini döner."""
    lang = lang if lang in SUPPORTED_LANGS else DEFAULT_LANG
    text = UI.get(lang, {}).get(key) or UI[DEFAULT_LANG].get(key) or key
    if kwargs:
        try:
            return text.format(**kwargs)
        except (KeyError, IndexError):
            return text
    return text


def tn(text: str, lang: str = DEFAULT_LANG) -> str:
    """
    Backend'in ürettiği Türkçe not metnini (rsi_note, regime, group, vb.)
    hedef dile çevirir. Türkçe modda veya boş/eşleşmeyen metinlerde metni
    olduğu gibi döner — asla hata vermez.
    """
    if lang != "en" or not text:
        return text
    if text in NOTE_EXACT:
        return NOTE_EXACT[text]
    translated = text
    for tr_part, en_part in NOTE_PARTIALS:
        translated = translated.replace(tr_part, en_part)
    return translated
