# -*- coding: utf-8 -*-
"""
Her günün hesaplanan verilerini (gösterge, haber, backtest) diske kaydeder.
bot_listener.py bu dosyayı okuyarak sorulara cevap verir.

Yazma işlemi ATOMİKTİR: önce geçici bir dosyaya yazılır, sonra os.replace ile
yerine taşınır. Böylece yazma sırasında süreç ölürse (Render'ın servisi
uyutması, Ctrl+C) cache.json yarım/bozuk kalmaz. Okuma tarafı da bozuk JSON'a
karşı toleranslıdır — aksi halde tek bozuk dosya tüm web panelini 500'e
düşürüyordu.
"""

import json
import os
import sys
import tempfile
import threading
from datetime import datetime

from config import CACHE_FILE

# Web app'te arka plan zamanlayıcısı ile istek thread'leri aynı dosyaya
# yazabiliyor; yazmaları seri hale getirir.
_write_lock = threading.Lock()


def save_cache(data: dict) -> None:
    payload = {
        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "tickers": data,
    }

    target_dir = os.path.dirname(os.path.abspath(CACHE_FILE)) or "."

    with _write_lock:
        fd, tmp_path = tempfile.mkstemp(dir=target_dir, prefix=".cache-", suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(payload, f, ensure_ascii=False, indent=2)
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp_path, CACHE_FILE)
        except BaseException:
            # Geçici dosyayı asla ortada bırakma.
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
            raise


def load_cache() -> dict:
    if not os.path.exists(CACHE_FILE):
        return {}
    try:
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        # Bozuk/okunamayan cache tüm uygulamayı çökertmesin — boş dönüp
        # bir sonraki tam analizin dosyayı yeniden yazmasına izin ver.
        print(f"UYARI: {CACHE_FILE} okunamadı ({e}) — boş cache kullanılıyor.", file=sys.stderr)
        return {}

    if not isinstance(data, dict):
        print(f"UYARI: {CACHE_FILE} beklenen formatta değil — boş cache kullanılıyor.", file=sys.stderr)
        return {}
    return data
