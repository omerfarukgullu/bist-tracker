# -*- coding: utf-8 -*-
"""
Takip edilecek BIST hisseleri ve genel ayarlar.
Yeni hisse eklemek/çıkarmak için sadece TICKERS listesini düzenle.
"""

import os

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# BIST hisse kodları (yfinance için sonuna otomatik .IS eklenir)
TICKERS = ["TRALT", "SARAE", "ASELS", "TUPRS", "EMPAE"]

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

# Web app'e HTTP Basic Auth koruması eklemek için (ikisi de set edilmezse
# koruma devre dışı kalır — lokal geliştirme için pratik).
APP_USERNAME = os.getenv("APP_USERNAME", "")
APP_PASSWORD = os.getenv("APP_PASSWORD", "")

# Cache dosyası - günlük veriler burada saklanır, bot soru cevaplarken buradan okur
CACHE_FILE = "cache.json"
