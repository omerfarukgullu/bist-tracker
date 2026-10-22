# -*- coding: utf-8 -*-
"""
BIST Tracker — Web App.

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

import hmac
import os
import re
import sys
import threading
from datetime import datetime

import markdown as markdown_lib
import pandas as pd
from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask, abort, redirect, render_template, request, jsonify, url_for
from flask_login import (
    LoginManager, login_user, logout_user, login_required, current_user,
)

from config import (
    OUTPUT_DIR, SMA_SHORT, SMA_LONG, SECRET_KEY,
    REFRESH_TOKEN, TELEGRAM_WEBHOOK_SECRET, TELEGRAM_BOT_TOKEN,
    PRICE_REFRESH_MINUTES,
)
import auth
import halka_arz_sinyali
from data_cache import load_cache, save_cache
from price_data import fetch_history, fetch_intraday, INTRADAY_RANGES
from indicators import compute_rsi, compute_macd
from translations import t, tn, DEFAULT_LANG, SUPPORTED_LANGS
import main as main_module
import bot_listener
import telegram_sender

TICKER_CODE_RE = re.compile(r"^[A-Z0-9]{2,10}$")
LANG_COOKIE = "lang"

app = Flask(__name__)
app.secret_key = SECRET_KEY

auth.init_db()

login_manager = LoginManager(app)
login_manager.login_view = "login"


@login_manager.user_loader
def load_user(user_id):
    return auth.get_user_by_id(int(user_id))


def get_lang() -> str:
    lang = request.cookies.get(LANG_COOKIE, DEFAULT_LANG)
    return lang if lang in SUPPORTED_LANGS else DEFAULT_LANG


@app.context_processor
def inject_i18n():
    lang = get_lang()
    return {
        "lang": lang,
        "t": lambda key, **kwargs: t(key, lang, **kwargs),
        "tn": lambda text: tn(text, lang),
    }


@app.route("/dil/<lang_code>")
def set_lang(lang_code):
    lang_code = lang_code if lang_code in SUPPORTED_LANGS else DEFAULT_LANG
    target = request.referrer or url_for("index")
    resp = redirect(target)
    resp.set_cookie(LANG_COOKIE, lang_code, max_age=60 * 60 * 24 * 365)
    return resp


# --- Kayıt / Giriş / Çıkış ---

USERNAME_RE = re.compile(r"^[A-Za-z0-9_]{3,30}$")


@app.route("/kayit", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("index"))

    if request.method == "GET":
        return render_template("register.html")

    username = request.form.get("username", "").strip()
    email = request.form.get("email", "").strip()
    password = request.form.get("password", "")
    password_confirm = request.form.get("password_confirm", "")

    if not USERNAME_RE.match(username):
        return render_template("register.html", error=t("error_username_invalid", get_lang()), username=username, email=email)
    if "@" not in email or "." not in email:
        return render_template("register.html", error=t("error_email_invalid", get_lang()), username=username, email=email)
    if len(password) < 6:
        return render_template("register.html", error=t("error_password_too_short", get_lang()), username=username, email=email)
    if password != password_confirm:
        return render_template("register.html", error=t("error_passwords_mismatch", get_lang()), username=username, email=email)

    user = auth.create_user(username, email, password)
    if user is None:
        return render_template("register.html", error=t("error_username_taken", get_lang()), username=username, email=email)

    login_user(user)
    return redirect(url_for("index"))


@app.route("/giris", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("index"))

    if request.method == "GET":
        return render_template("login.html")

    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")

    user = auth.verify_password(username, password)
    if user is None:
        return render_template("login.html", error=t("error_invalid_credentials", get_lang()), username=username)

    login_user(user)
    return redirect(url_for("index"))


@app.route("/cikis")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))


# --- Sayfalar ---

@app.route("/")
@login_required
def index():
    cache = load_cache()
    tickers_data = cache.get("tickers", {})
    updated_at = cache.get("updated_at")
    tickers = auth.get_user_tickers(current_user.id)
    return render_template(
        "index.html", tickers=tickers, tickers_data=tickers_data, updated_at=updated_at,
        error=request.args.get("error"), info=request.args.get("info"),
    )


@app.route("/hisse-ekle", methods=["POST"])
@login_required
def add_ticker_route():
    ticker = request.form.get("ticker", "").strip().upper()

    if not ticker:
        return redirect(url_for("index"))

    if not TICKER_CODE_RE.match(ticker):
        return redirect(url_for("index", error=f"'{ticker}' geçerli bir hisse kodu gibi görünmüyor."))

    user_tickers = auth.get_user_tickers(current_user.id)
    if ticker in user_tickers:
        return redirect(url_for("index", info=f"{ticker} zaten takip ediliyor."))

    already_tracked = ticker in auth.get_all_tracked_tickers()

    if not already_tracked:
        try:
            fetch_history(ticker)  # BIST'te böyle bir kod var mı diye doğrula
        except ValueError:
            return redirect(url_for("index", error=f"{ticker} bulunamadı — BIST kodunu kontrol et."))

    auth.add_user_ticker(current_user.id, ticker)

    if not already_tracked:
        # Bu hisseyi henüz hiçbir kullanıcı takip etmiyordu — hemen tam
        # analiz çalıştır (haber + AI + volatilite dahil) ki kullanıcı bir
        # sonraki günlük çalıştırmayı beklemesin.
        try:
            rd_cache = main_module.load_rd_cache()
            ipo_index_tickers = halka_arz_sinyali.fetch_ipo_index_tickers()
            _, raw = main_module.process_ticker(ticker, rd_cache, ipo_index_tickers)
            cache = load_cache()
            tickers_data = cache.get("tickers", {})
            tickers_data[ticker] = raw
            save_cache(tickers_data)
        except Exception as e:
            print(f"[{ticker}] ilk analiz başarısız oldu: {e}")

    return redirect(url_for("ticker_detail", ticker=ticker))


@app.route("/hisse-sil", methods=["POST"])
@login_required
def remove_ticker_route():
    ticker = request.form.get("ticker", "").strip().upper()
    auth.remove_user_ticker(current_user.id, ticker)
    return redirect(url_for("index"))


@app.route("/hisse/<ticker>")
@login_required
def ticker_detail(ticker):
    ticker = ticker.upper()
    if ticker not in auth.get_all_tracked_tickers():
        abort(404)

    cache = load_cache()
    tickers_data = cache.get("tickers", {})
    data = tickers_data.get(ticker)
    updated_at = cache.get("updated_at")

    return render_template(
        "ticker.html", ticker=ticker, data=data, updated_at=updated_at,
    )


def _series_to_list(series: pd.Series) -> list:
    return [None if pd.isna(v) else round(float(v), 3) for v in series]


@app.route("/hisse/<ticker>/chart-data")
@login_required
def ticker_chart_data(ticker):
    ticker = ticker.upper()
    if ticker not in auth.get_all_tracked_tickers():
        abort(404)

    try:
        df = fetch_history(ticker)
    except ValueError as e:
        return jsonify({"error": str(e)}), 502

    close = df["Close"]
    rsi = compute_rsi(close)
    macd_line, signal_line, hist = compute_macd(close)
    sma_short = close.rolling(SMA_SHORT).mean()
    sma_long = close.rolling(SMA_LONG).mean()

    return jsonify({
        "dates": [d.strftime("%Y-%m-%d") for d in df.index],
        "close": _series_to_list(close),
        "sma_short": _series_to_list(sma_short),
        "sma_long": _series_to_list(sma_long),
        "rsi": _series_to_list(rsi),
        "macd": _series_to_list(macd_line),
        "macd_signal": _series_to_list(signal_line),
        "macd_hist": _series_to_list(hist),
    })


def _intraday_label(range_key: str, ts) -> str:
    if range_key == "1d":
        return ts.strftime("%H:%M")
    if range_key in ("1w", "1mo"):
        return ts.strftime("%d.%m %H:%M")
    return ts.strftime("%Y-%m-%d")


@app.route("/hisse/<ticker>/chat", methods=["POST"])
@login_required
def ticker_chat(ticker):
    ticker = ticker.upper()
    if ticker not in auth.get_all_tracked_tickers():
        abort(404)

    body = request.get_json(silent=True) or {}
    question = (body.get("question") or "").strip()
    if not question:
        return jsonify({"error": t("chat_empty_question", get_lang())}), 400

    answer = bot_listener.answer_for_ticker(ticker, question)
    return jsonify({"answer": answer})


@app.route("/hisse/<ticker>/intraday-data")
@login_required
def ticker_intraday_data(ticker):
    ticker = ticker.upper()
    if ticker not in auth.get_all_tracked_tickers():
        abort(404)

    range_key = request.args.get("range", "1d")
    if range_key not in INTRADAY_RANGES:
        range_key = "1d"

    try:
        df = fetch_intraday(ticker, range_key)
    except ValueError as e:
        return jsonify({"error": str(e)}), 502

    return jsonify({
        "range": range_key,
        "session_date": df.index[-1].strftime("%Y-%m-%d"),
        "timestamps": [_intraday_label(range_key, d) for d in df.index],
        "close": _series_to_list(df["Close"]),
    })


@app.route("/raporlar")
@login_required
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
@login_required
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

# Tam günlük analiz (tüm hisseler × fiyat + haber + AI) dakikalar sürer;
# gunicorn'un varsayılan worker timeout'u 30 saniyedir. Senkron çalıştırıldığında
# worker öldürülüyor ve istek HER SEFERİNDE hata dönüyordu. Bu yüzden analiz
# arka plan thread'inde çalıştırılıp istek hemen 202 ile cevaplanır.
_refresh_lock = threading.Lock()
_refresh_state = {
    "running": False,
    "started_at": None,
    "finished_at": None,
    "last_error": None,
}


def _run_full_analysis() -> None:
    try:
        main_module.main()
        _refresh_state["last_error"] = None
    except Exception as e:
        _refresh_state["last_error"] = str(e)
        print(f"Günlük analiz başarısız oldu: {e}", file=sys.stderr)
    finally:
        _refresh_state["running"] = False
        _refresh_state["finished_at"] = datetime.now().strftime("%Y-%m-%d %H:%M")
        _refresh_lock.release()


def _refresh_token_ok() -> bool:
    """Token'ı sabit zamanda karşılaştırır (basit != karşılaştırması uzunluk/
    içerik sızdırabilir)."""
    header = request.headers.get("Authorization", "")
    return hmac.compare_digest(header, f"Bearer {REFRESH_TOKEN}")


@app.route("/api/refresh", methods=["POST"])
def api_refresh():
    if not REFRESH_TOKEN:
        return jsonify({"error": "REFRESH_TOKEN ayarlanmamış."}), 503

    if not _refresh_token_ok():
        abort(401)

    if not _refresh_lock.acquire(blocking=False):
        return jsonify({
            "status": "already_running",
            "started_at": _refresh_state["started_at"],
        }), 409

    _refresh_state["running"] = True
    _refresh_state["started_at"] = datetime.now().strftime("%Y-%m-%d %H:%M")
    _refresh_state["finished_at"] = None
    threading.Thread(target=_run_full_analysis, name="full-analysis", daemon=True).start()

    return jsonify({"status": "started"}), 202


@app.route("/api/refresh/status")
def api_refresh_status():
    """Arka planda çalışan analizin durumu (cron'un sonucu görebilmesi için)."""
    if not REFRESH_TOKEN:
        return jsonify({"error": "REFRESH_TOKEN ayarlanmamış."}), 503
    if not _refresh_token_ok():
        abort(401)
    return jsonify(_refresh_state)


# --- Telegram webhook (bot_listener.py'nin polling mantığının aynısı) ---

@app.route("/telegram/webhook", methods=["POST"])
def telegram_webhook():
    if TELEGRAM_WEBHOOK_SECRET:
        header = request.headers.get("X-Telegram-Bot-Api-Secret-Token", "")
        if not hmac.compare_digest(header, TELEGRAM_WEBHOOK_SECRET):
            abort(401)

    update = request.get_json(silent=True) or {}
    message = update.get("message", {})
    text = message.get("text", "")
    chat_id = message.get("chat", {}).get("id")

    if text and chat_id:
        reply = bot_listener.answer_question(text)
        telegram_sender.send_message(TELEGRAM_BOT_TOKEN, chat_id, reply)

    return jsonify({"ok": True})


# --- Arka planda fiyat/gösterge yenileme (PRICE_REFRESH_MINUTES'te bir) ---

def _run_price_refresh():
    try:
        main_module.refresh_price_data()
    except Exception as e:
        print(f"Fiyat yenileme sırasında hata: {e}")


def start_price_scheduler():
    scheduler = BackgroundScheduler(daemon=True)
    scheduler.add_job(
        _run_price_refresh, "interval",
        minutes=PRICE_REFRESH_MINUTES, id="price_refresh",
        next_run_time=datetime.now(),  # sunucu açılır açılmaz bir kez hemen çalışsın
    )
    scheduler.start()
    print(f"Fiyat yenileme zamanlayıcısı başladı ({PRICE_REFRESH_MINUTES} dakikada bir).")


if __name__ == "__main__":
    # debug=True, Werkzeug'un interaktif debugger'ını açar — bu konsol
    # üzerinden SUNUCUDA KOD ÇALIŞTIRILABİLİR. Önceden sabit olarak açıktı ve
    # host 0.0.0.0 ile tüm ağ arayüzlerine bağlanıyordu. Artık ikisi de
    # ortam değişkeniyle, varsayılanları güvenli tarafta:
    #   FLASK_DEBUG=1  -> debugger'ı aç (sadece lokal geliştirme)
    #   HOST=0.0.0.0   -> ağdaki diğer cihazlardan erişime izin ver
    debug = os.getenv("FLASK_DEBUG", "").lower() in ("1", "true", "yes")
    host = os.getenv("HOST", "127.0.0.1")

    # Debug reloader bu dosyayı iki kez çalıştırır (dosyaları izleyen dış
    # süreç + gerçek sunucu süreci); WERKZEUG_RUN_MAIN sadece ikincisinde
    # "true" olur. Bu kontrol olmadan zamanlayıcı iki kez başlar. Debug
    # kapalıyken tek süreç vardır ve koşul doğrudan sağlanır.
    if not debug or os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        start_price_scheduler()

    app.run(host=host, port=int(os.getenv("PORT", 5000)), debug=debug)
