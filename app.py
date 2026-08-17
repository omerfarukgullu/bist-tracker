# -*- coding: utf-8 -*-
"""
BIST Takip Botu — Web App.

Mevcut script'lerin (main.py, bot_listener.py, price_data.py vb.) mantığını
tekrar yazmadan, üzerine ince bir web katmanı ekler:

- Dashboard: cache.json'daki en son veriyi kart olarak gösterir.
- Hisse detay sayfası: günün göstergeleri, backtest, haberler.
- Geçmiş raporlar: raporlar/*.md dosyalarını listeler ve HTML olarak gösterir.
- /api/refresh: main.main()'i tetikleyip veriyi günceller (dış cron çağırır).
- /telegram/webhook: bot_listener.answer_question() ile aynı soru-cevap
  mantığını polling yerine Telegram webhook üzerinden sunar.

Lokal çalıştırma:
    python app.py
Prodüksiyon (Render):
    gunicorn app:app
"""

import os
from functools import wraps

import markdown as markdown_lib
from flask import Flask, abort, render_template, request, Response, jsonify

from config import (
    TICKERS, OUTPUT_DIR, APP_USERNAME, APP_PASSWORD,
    REFRESH_TOKEN, TELEGRAM_WEBHOOK_SECRET, TELEGRAM_BOT_TOKEN,
)
from data_cache import load_cache
import main as main_module
import bot_listener
import telegram_sender

app = Flask(__name__)


# --- HTTP Basic Auth (opsiyonel, APP_USERNAME/APP_PASSWORD set edilmişse) ---

def _auth_required():
    return bool(APP_USERNAME and APP_PASSWORD)


def _check_auth(auth):
    return auth and auth.username == APP_USERNAME and auth.password == APP_PASSWORD


def require_basic_auth(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if _auth_required():
            auth = request.authorization
            if not _check_auth(auth):
                return Response(
                    "Giriş gerekli.", 401,
                    {"WWW-Authenticate": 'Basic realm="BIST Takip"'},
                )
        return view(*args, **kwargs)
    return wrapped


# --- Sayfalar ---

@app.route("/")
@require_basic_auth
def index():
    cache = load_cache()
    tickers_data = cache.get("tickers", {})
    updated_at = cache.get("updated_at")
    return render_template(
        "index.html", tickers=TICKERS, tickers_data=tickers_data, updated_at=updated_at,
    )


@app.route("/hisse/<ticker>")
@require_basic_auth
def ticker_detail(ticker):
    ticker = ticker.upper()
    if ticker not in TICKERS:
        abort(404)

    cache = load_cache()
    tickers_data = cache.get("tickers", {})
    data = tickers_data.get(ticker)
    updated_at = cache.get("updated_at")

    return render_template(
        "ticker.html", ticker=ticker, data=data, updated_at=updated_at,
    )


@app.route("/raporlar")
@require_basic_auth
def raporlar_list():
    if not os.path.isdir(OUTPUT_DIR):
        files = []
    else:
        files = sorted(
            (f for f in os.listdir(OUTPUT_DIR) if f.endswith(".md")),
            reverse=True,
        )
    return render_template("raporlar.html", files=files)


@app.route("/raporlar/<path:filename>")
@require_basic_auth
def rapor_detail(filename):
    if "/" in filename or "\\" in filename or not filename.endswith(".md"):
        abort(404)

    filepath = os.path.join(OUTPUT_DIR, filename)
    if not os.path.isfile(filepath):
        abort(404)

    with open(filepath, "r", encoding="utf-8") as f:
        raw = f.read()

    html = markdown_lib.markdown(raw, extensions=["extra"])
    return render_template("rapor_detail.html", filename=filename, content=html)


# --- API: günlük analizi tetikle (dış cron çağırır) ---

@app.route("/api/refresh", methods=["POST"])
def api_refresh():
    if not REFRESH_TOKEN:
        return jsonify({"error": "REFRESH_TOKEN ayarlanmamış."}), 503

    auth_header = request.headers.get("Authorization", "")
    if auth_header != f"Bearer {REFRESH_TOKEN}":
        abort(401)

    main_module.main()
    return jsonify({"status": "ok"})


# --- Telegram webhook (bot_listener.py'nin polling mantığının aynısı) ---

@app.route("/telegram/webhook", methods=["POST"])
def telegram_webhook():
    if TELEGRAM_WEBHOOK_SECRET:
        header = request.headers.get("X-Telegram-Bot-Api-Secret-Token", "")
        if header != TELEGRAM_WEBHOOK_SECRET:
            abort(401)

    update = request.get_json(silent=True) or {}
    message = update.get("message", {})
    text = message.get("text", "")
    chat_id = message.get("chat", {}).get("id")

    if text and chat_id:
        reply = bot_listener.answer_question(text)
        telegram_sender.send_message(TELEGRAM_BOT_TOKEN, chat_id, reply)

    return jsonify({"ok": True})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)), debug=True)
