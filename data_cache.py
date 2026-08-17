# -*- coding: utf-8 -*-
"""
Her günün hesaplanan verilerini (gösterge, haber, backtest) diske kaydeder.
bot_listener.py bu dosyayı okuyarak sorulara cevap verir.
"""

import json
import os
from datetime import datetime
from config import CACHE_FILE


def save_cache(data: dict) -> None:
    payload = {
        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "tickers": data,
    }
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)


def load_cache() -> dict:
    if not os.path.exists(CACHE_FILE):
        return {}
    with open(CACHE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)
