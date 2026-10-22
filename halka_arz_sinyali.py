# -*- coding: utf-8 -*-
"""
Yeni halka arz olmuş hisseleri tespit edip, KENDİ fiyat geçmişine dayalı
tavan/taban seri istatistiği üretir.

ÖNEMLİ SINIRLAMA: Bu modül "kaç tavan daha yapar" ya da "ne zaman bozar"
tarzında bir GELECEK TAHMİNİ üretmez — böyle bir tahmin hiçbir istatistiksel
yöntemle dürüstçe verilemez. Sadece şeffaf, geçmişe dönük bir özet sunar:
mevcut tavan/taban serisi kaç gün sürüyor, bu hissede daha önce benzer bir
seri kırıldıysa (varsa) ardından ortalama ne olmuş. Yeni halka arzların çoğu
kısa bir geçmişe sahip olduğundan "kırılma sonrası" istatistiği çoğu zaman
üretilemez — bu durumda modül bir sayı UYDURMAZ, yetersiz veri olduğunu
açıkça belirtir.

Yeni halka arz tespiti iki katmanlıdır:
1. Birincil: Borsa İstanbul'un BIST Halka Arz Endeksi (XHARZ) güncel üye
   listesi (halka arzdan sonraki 2 yıl boyunca üye kalınır) — resmi ve
   güvenilir.
2. Fallback (CSV çekilemezse): hissenin toplam işlem günü sayısı
   RECENT_IPO_TRADING_DAYS'in altındaysa "yeni" sayılır.
"""

import anthropic
import pandas as pd
import requests
import yfinance as yf

from config import (
    TAVAN_TABAN_BAND_PCT, RECENT_IPO_TRADING_DAYS, MIN_STREAK_FOR_BREAK_STATS,
    ANTHROPIC_API_KEY,
)

IPO_INDEX_CSV_URL = "https://www.borsaistanbul.com/datum/hisse_endeks_ds.csv"
IPO_INDEX_CODE = "XHARZ"

IPO_AI_SYSTEM_PROMPT = (
    "Sen bir BIST hisse takip aracının parçasısın. Sana yeni halka arz olmuş "
    "bir hissenin tavan/taban seri istatistikleri, son günlerin kapanış/işlem "
    "hacmi verisi ve haber duyarlılığı veriliyor. Görevin bunları BİRLİKTE "
    "değerlendirip, mevcut tavan/taban eğiliminin devam etmesinin mi yoksa "
    "kırılmasının (bozmasının) mı daha olası göründüğünü tartışan kısa "
    "(3-5 cümle) bir Türkçe yorum üretmek.\n\n"
    "DİL VE ÜSLUP:\n"
    "- Okuyucunun borsa hakkında hiçbir bilgisi olmadığını varsay, sade ve "
    "günlük konuşma diline yakın cümleler kur.\n"
    "- Kısa cümleler kur.\n\n"
    "KESİN KURALLAR:\n"
    "- 'X tavan daha yapacak' ya da 'Y günde bozar' gibi KESİN bir sayı/iddia "
    "asla verme — 'olabilir', 'görünüyor', 'ihtimal dahilinde' gibi açıkça "
    "belirsizlik içeren, tedbirli ifadeler kullan.\n"
    "- Al/sat tavsiyesi verme.\n"
    "- Sadece sana verilen veriyi (seri istatistiği, hacim, haber) yorumla; "
    "hisse hakkında kendi bilginden ek iddialarda bulunma.\n"
    "- Cevabının EN SONUNA, ayrı bir satırda, aynen şu cümleyi ekle: "
    "'⚠️ Bu bir AI tahminidir, kesinlik taşımaz ve yatırım tavsiyesi değildir.'"
)


def fetch_ipo_index_tickers() -> set:
    """
    BIST Halka Arz Endeksi'nin (XHARZ) güncel üyelerini döner. Ağ hatasında
    None döner (çağıran taraf işlem-günü sayısına dayalı fallback'e düşer).
    """
    try:
        resp = requests.get(
            IPO_INDEX_CSV_URL,
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=15,
        )
        resp.raise_for_status()
    except requests.RequestException:
        return None

    tickers = set()
    lines = resp.text.splitlines()
    for line in lines[2:]:  # ilk iki satır başlık (TR + EN)
        parts = line.split(";")
        if len(parts) < 3:
            continue
        code, _name, index_code = parts[0], parts[1], parts[2]
        if index_code.strip() == IPO_INDEX_CODE:
            tickers.add(code.strip().removesuffix(".E"))

    if not tickers:
        # CSV indi ama tek bir XHARZ satırı bile ayrıştırılamadı — neredeyse
        # kesinlikle format/ayraç değişmiş demektir. Boş küme döndürmek
        # "hiçbir hisse yeni halka arz değil" gibi görünüp analizi sessizce
        # kapatıyordu; None dönüp işlem-günü fallback'ine düşmesi daha doğru.
        print("UYARI: XHARZ üye listesi ayrıştırılamadı — işlem günü sayısına dayalı fallback kullanılacak.")
        return None
    return tickers


def fetch_full_history(ticker: str) -> pd.DataFrame:
    """
    Hissenin borsaya girdiğinden bu yana fiyat geçmişini çeker. period="max"
    kullanılmıyor — çok taze halka arzlarda (ör. ilk işlem gününde)
    yfinance/Yahoo "max" periyodunu geçersiz sayıp hata verebiliyor. "2y"
    her zaman çalışıyor ve zaten bu modülün kapsamı için yeterli: "yeni
    halka arz" tanımı (XHARZ üyeliği ya da RECENT_IPO_TRADING_DAYS eşiği)
    en fazla ~2 yıllık bir pencereyle sınırlı.
    """
    symbol = f"{ticker}.IS"
    df = yf.Ticker(symbol).history(period="2y", interval="1d")

    if df.empty:
        raise ValueError(f"{ticker} için halka arz analizi amacıyla veri bulunamadı.")

    return df.dropna()


def _label_days(df: pd.DataFrame) -> pd.Series:
    """Her günü 'tavan' / 'taban' / None olarak etiketler."""
    returns = df["Close"].pct_change() * 100
    band = TAVAN_TABAN_BAND_PCT

    def label(r):
        if pd.isna(r):
            return None
        if r >= band:
            return "tavan"
        if r <= -band:
            return "taban"
        return None

    return returns.apply(label)


def _current_streak(labels: pd.Series):
    """En son günden geriye doğru kesintisiz aynı-tip seriyi sayar."""
    if len(labels) == 0:
        return None, 0

    last_label = labels.iloc[-1]
    if pd.isna(last_label):
        return None, 0

    streak = 0
    for label in reversed(labels.tolist()):
        if label == last_label:
            streak += 1
        else:
            break
    return last_label, streak


def _longest_streaks(labels: pd.Series) -> dict:
    """Tüm geçmişteki en uzun tavan ve taban serilerini bulur."""
    longest = {"tavan": 0, "taban": 0}
    current_type = None
    current_len = 0

    for label in labels.tolist():
        if not pd.isna(label) and label == current_type:
            current_len += 1
        elif not pd.isna(label):
            current_type = label
            current_len = 1
        else:
            current_type = None
            current_len = 0
        if current_type in longest:
            longest[current_type] = max(longest[current_type], current_len)

    return longest


def _break_stats(df: pd.DataFrame, labels: pd.Series) -> dict:
    """
    Geçmişte MIN_STREAK_FOR_BREAK_STATS gün ve üzeri süren her tavan
    serisinin bittiği günden sonraki 5 işlem gününde ortalama getiri.
    """
    close = df["Close"]
    label_list = labels.tolist()
    n = len(label_list)

    streak_start = None
    returns_after_break = []

    for i in range(n):
        if label_list[i] == "tavan":
            if streak_start is None:
                streak_start = i
        else:
            if streak_start is not None:
                streak_len = i - streak_start
                if streak_len >= MIN_STREAK_FOR_BREAK_STATS:
                    break_idx = i
                    if break_idx + 5 < n:
                        price_at_break = float(close.iloc[break_idx])
                        price_after_5d = float(close.iloc[break_idx + 5])
                        returns_after_break.append(
                            (price_after_5d - price_at_break) / price_at_break * 100
                        )
                streak_start = None

    if not returns_after_break:
        return {
            "available": False,
            "reason": "Bu hissede daha önce kırılan bir tavan serisi yok — geçmiş kırılma istatistiği üretilemiyor.",
        }

    wins = sum(1 for r in returns_after_break if r > 0)
    return {
        "available": True,
        "sample_size": len(returns_after_break),
        "avg_return_5d_pct": round(sum(returns_after_break) / len(returns_after_break), 2),
        "win_rate": round(wins / len(returns_after_break) * 100, 1),
    }


def compute_ipo_signal(ticker: str, df: pd.DataFrame, ipo_index_tickers=None) -> dict:
    trading_days_since_listing = len(df)
    listing_date = df.index[0].strftime("%Y-%m-%d")

    in_bist_ipo_index = None
    if ipo_index_tickers is not None:
        in_bist_ipo_index = ticker in ipo_index_tickers
        is_recent_ipo = in_bist_ipo_index
    else:
        is_recent_ipo = trading_days_since_listing < RECENT_IPO_TRADING_DAYS

    if not is_recent_ipo:
        return {"available": False, "reason": "Yeni halka arz olarak sınıflandırılmadı."}

    labels = _label_days(df)
    current_streak_type, current_streak_length = _current_streak(labels)
    longest = _longest_streaks(labels)

    return {
        "available": True,
        "listing_date": listing_date,
        "trading_days_since_listing": trading_days_since_listing,
        "in_bist_ipo_index": in_bist_ipo_index,
        "current_streak_type": current_streak_type,
        "current_streak_length": current_streak_length,
        "total_tavan_days": int((labels == "tavan").sum()),
        "total_taban_days": int((labels == "taban").sum()),
        "longest_tavan_streak": longest["tavan"],
        "longest_taban_streak": longest["taban"],
        "break_stats": _break_stats(df, labels),
    }


def _format_volume_context(df: pd.DataFrame) -> str:
    recent = df.tail(10)
    lines = []
    for date, row in recent.iterrows():
        volume = int(row["Volume"]) if pd.notna(row["Volume"]) else 0
        lines.append(f"{date.strftime('%Y-%m-%d')}: kapanış {row['Close']:.2f} TL, hacim {volume:,}")
    return "\n".join(lines)


def _format_news_context(news_items: list, sentiment: dict) -> str:
    if not news_items:
        return "Haber bulunamadı."
    lines = [f"Genel duyarlılık: {sentiment.get('label', 'bilinmiyor')} ({sentiment.get('count', 0)} haber tarandı)"]
    for item in news_items[:5]:
        lines.append(f"- {item['title']}")
    return "\n".join(lines)


def build_ai_assessment(ticker: str, ipo_signal: dict, df: pd.DataFrame,
                         news_items: list = None, sentiment: dict = None):
    """
    Seri istatistiği + hacim + haber duyarlılığını birlikte AI'a verip kısa,
    açıkça "AI tahmini" olarak etiketlenmiş, tedbirli bir yorum üretir.
    ANTHROPIC_API_KEY ayarlı değilse ya da hisse yeni IPO değilse None döner.
    """
    if not ANTHROPIC_API_KEY or not ipo_signal.get("available"):
        return None

    streak_desc = (
        f"{ipo_signal['current_streak_length']} gündür üst üste {ipo_signal['current_streak_type']}"
        if ipo_signal.get("current_streak_type")
        else "şu anda aktif bir tavan/taban serisi yok"
    )
    bs = ipo_signal.get("break_stats") or {}
    break_desc = (
        f"geçmişte kırılan {bs['sample_size']} tavan serisinden sonraki 5 işlem gününde "
        f"ortalama getiri %{bs['avg_return_5d_pct']:+.2f} (pozitif kapanma oranı %{bs['win_rate']})"
        if bs.get("available")
        else "bu hissede daha önce kırılan bir tavan serisi yok"
    )

    user_content = (
        f"Hisse: {ticker} (borsaya giriş: {ipo_signal['listing_date']}, "
        f"{ipo_signal['trading_days_since_listing']} işlem günü geçti)\n\n"
        f"Mevcut seri durumu: {streak_desc}\n"
        f"Bugüne kadar: {ipo_signal['total_tavan_days']} tavan günü, "
        f"{ipo_signal['total_taban_days']} taban günü\n"
        f"En uzun tavan serisi: {ipo_signal['longest_tavan_streak']} gün\n"
        f"Kırılma istatistiği: {break_desc}\n\n"
        f"Son işlem günleri (kapanış / hacim):\n{_format_volume_context(df)}\n\n"
        f"Haberler:\n{_format_news_context(news_items or [], sentiment or {})}\n"
    )

    try:
        client = anthropic.Anthropic()
        response = client.messages.create(
            model="claude-opus-5",
            max_tokens=16000,  # bkz. ai_summary.py: thinking bu sınırdan düşer
            output_config={"effort": "low"},
            system=IPO_AI_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_content}],
        )
        if response.stop_reason == "refusal":
            print(f"[{ticker}] Halka arz AI değerlendirmesi reddedildi (refusal).")
            return None
        if response.stop_reason == "max_tokens":
            print(f"[{ticker}] Halka arz AI değerlendirmesi token sınırında kesildi — yarım metin gösterilmiyor.")
            return None
        return next((b.text for b in response.content if b.type == "text"), None)
    except Exception as e:
        print(f"[{ticker}] Halka arz AI değerlendirmesi üretilemedi: {e}")
        return None
