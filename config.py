# -*- coding: utf-8 -*-
"""
Takip edilecek BIST hisseleri ve genel ayarlar.

Hisse takip listesi artık kullanıcı bazlı (bkz. auth.py, users.db) —
DEFAULT_TICKERS sadece yeni kayıt olan kullanıcıların başlangıç listesi
olarak kullanılır. TICKERS_FILE (tickers.json), göç öncesi tek global
listenin kalıntısıdır; ilk kayıt olan kullanıcıya bir kereliğine seed
olarak devredilir (bkz. auth._seed_tickers_for_new_user), başka bir yerde
kullanılmaz.
"""

import os
import secrets

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

DEFAULT_TICKERS = ["TRALT", "SARAE", "ASELS", "TUPRS", "EMPAE"]
TICKERS_FILE = "tickers.json"

# Teknik gösterge ayarları
RSI_PERIOD = 14
SMA_SHORT = 20
SMA_LONG = 50
MACD_FAST = 12
MACD_SLOW = 26
MACD_SIGNAL = 9

# Geçmiş veri kaç günlük çekilsin (gösterge hesaplamak için yeterli pencere)
HISTORY_DAYS = 180

# Her hisse için kaç haber taransın
NEWS_LIMIT_PER_TICKER = 8

# Rapor dosyalarının kaydedileceği klasör
OUTPUT_DIR = "raporlar"

# Web app çalışırken fiyat/gösterge/istatistik verisinin arka planda kaç
# dakikada bir hafifçe yenileneceği (haber/AI/Telegram dahil değil —
# bkz. main.refresh_price_data).
PRICE_REFRESH_MINUTES = 5

# --- Telegram Bot Ayarları ---
# BotFather'dan aldığın token'ı ortam değişkeni (env var) olarak set et,
# koda YAZMA. Lokalde .env dosyası kullanabilirsin (bkz. .env.example),
# Render'da dashboard'dan environment variable olarak girilir.
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")

# Botun mesaj göndereceği/dinleyeceği sohbetin chat_id'si
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

# Telegram'ın setWebhook'a verilen secret_token'ı; webhook isteklerinin
# gerçekten Telegram'dan geldiğini doğrulamak için kullanılır (opsiyonel).
TELEGRAM_WEBHOOK_SECRET = os.getenv("TELEGRAM_WEBHOOK_SECRET", "")

# /api/refresh endpoint'ini tetiklemek için gereken bearer token
# (GitHub Actions cron bu token'ı kullanır).
REFRESH_TOKEN = os.getenv("REFRESH_TOKEN", "")

# --- Kullanıcı hesapları (auth.py) ---
DB_FILE = "users.db"

# Flask oturum çerezlerini imzalamak için. .env'de SECRET_KEY set edilmezse,
# ilk çalıştırmada yerel bir dosyada (secret_key.txt) rastgele üretilip
# saklanır — böylece .env kurmadan da restart'lar arasında oturumlar düşmez.
SECRET_KEY = os.getenv("SECRET_KEY", "")
if not SECRET_KEY:
    _key_file = "secret_key.txt"
    if os.path.exists(_key_file):
        with open(_key_file, "r", encoding="utf-8") as f:
            SECRET_KEY = f.read().strip()
    if not SECRET_KEY:
        SECRET_KEY = secrets.token_hex(32)
        with open(_key_file, "w", encoding="utf-8") as f:
            f.write(SECRET_KEY)

# --- İstatistiksel Aylık Aralık (forecast.py) ---
# Kaç işlem günü ileriye simülasyon yapılsın (21 ≈ 1 takvim ayı) ve
# Monte Carlo simülasyon sayısı.
FORECAST_HORIZON_DAYS = 21
FORECAST_SIMULATIONS = 2000

# --- AI Yorumu (ai_summary.py) ---
# Claude API key. Boşsa AI yorumu tamamen devre dışı kalır — sadece
# istatistiksel aralık (yukarıdaki) üretilir, hiçbir hata oluşmaz.
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

# --- Volatilite Rejimi (volatilite_rejimi.py, EGARCH) ---
# GARCH modeli için ana HISTORY_DAYS'ten daha uzun bir fiyat penceresi
# gerekir (daha güvenilir parametre tahmini için).
VOLATILITY_HISTORY_DAYS = 500

# --- Yeni Halka Arz Tespiti + Tavan/Taban Seri Analizi (halka_arz_sinyali.py) ---
# Günlük getirinin tavan/taban sayılması için eşik (%). BIST'in standart
# ±%10 günlük fiyat bandının bir yaklaşıklığıdır (yfinance'ta resmi
# taban/tavan eşiği verisi yok).
TAVAN_TABAN_BAND_PCT = 9.5

# Bir hissenin "yeni halka arz" sayılması için üst sınır (işlem günü) —
# BIST'in BIST Halka Arz Endeksi (XHARZ) şirketleri 2 yıl üye tutmasıyla
# tutarlı bir yaklaşık değer; sadece XHARZ CSV'si çekilemediğinde fallback
# olarak kullanılır.
RECENT_IPO_TRADING_DAYS = 500

# Bir tavan serisinin "kırılma sonrası ne olur" istatistiğine dahil
# edilmesi için gereken minimum seri uzunluğu (gün).
MIN_STREAK_FOR_BREAK_STATS = 3

# --- AR-GE Sinyali (arge_sinyali.py) ---
# Günlük job'dan AYRI, çeyreklik/yıllık finansal tablo yayınlandığında elle
# çalıştırılması beklenen modül: `python arge_sinyali.py`. Sonuçlar bu ayrı
# cache dosyasına yazılır; günlük main() sadece buradan OKUR, yeniden
# hesaplamaz (isyatirimhisse API'si zaman zaman zaman aşımına uğrayabiliyor,
# günlük akışı buna bağımlı kılmamak için).
RD_CACHE_FILE = "rd_cache.json"
RD_ANALYSIS_YEARS = 3

# Cache dosyası - günlük veriler burada saklanır, bot soru cevaplarken buradan okur
CACHE_FILE = "cache.json"
