# -*- coding: utf-8 -*-
"""
AR-GE Yoğunluğu ve "Verimlilik Katsayısı" — çeyreklik/yıllık finansal tablo
verisine dayalı, GÜNLÜK JOB'DAN AYRI çalışan bir modül.

ŞEFFAFLIK NOTU (önemli):
- "Verimlilik Katsayısı" (Ortalama Getiri % / Ortalama AR-GE Yoğunluğu %)
  burada basit, açıklayıcı bir ORANDIR — akademik olarak doğrulanmış,
  kanıtlanmış bir yatırım sinyali değildir. Tek başına "bu hisse iyi/kötü"
  anlamına gelmez; sadece geçmiş AR-GE harcamasının geçmiş getiriyle basit
  bir kıyasıdır.
- AR-GE gideri ve satış geliri verisi isyatirimhisse (İş Yatırım) API'si
  üzerinden çekilir; bu API zaman zaman zaman aşımına uğrayabiliyor — bu
  yüzden bu modül günlük main() akışına DAHİL DEĞİLDİR, elle veya periyodik
  (çeyreklik) olarak ayrıca çalıştırılmalıdır.
- Al/Sat tavsiyesi değildir.

Çalıştırma:
    python arge_sinyali.py
"""

import json
import time
from datetime import datetime

import yfinance as yf
import isyatirimhisse as isy

import auth
from config import DEFAULT_TICKERS, RD_CACHE_FILE, RD_ANALYSIS_YEARS

RD_ITEM_CODE = "3DC"      # Araştırma ve Geliştirme Giderleri (-)
REVENUE_ITEM_CODE = "3C"  # Satış Gelirleri

# "Yüksek AR-GE" eşiği: gelirin bu oranından fazlası AR-GE'ye gidiyorsa
# "yüksek" sayılır. Keyfi ama makul bir eşik — kesin bir sektör standardı
# değildir.
HIGH_RD_THRESHOLD = 0.05

# AR-GE yoğunluğu bu eşiğin altındaysa (gelirin ~%0.1'inden azı) "Verimlilik
# Katsayısı" (getiri / yoğunluk) neredeyse sıfıra bölme haline gelip anlamsız
# derecede büyük/uçuk bir sayı üretir (ör. TUPRS gibi AR-GE yapmayan bir
# şirkette 1000+ çıkabilir). Bu durumda oranı hiç göstermiyoruz.
NEGLIGIBLE_RD_THRESHOLD = 0.001


def _fetch_financials_with_retry(ticker: str, start_year: int, end_year: int, attempts: int = 3):
    last_error = None
    for _ in range(attempts):
        try:
            df = isy.fetch_financials(ticker, start_year=start_year, end_year=end_year)
            if not df.empty:
                return df
        except Exception as e:
            last_error = e
        time.sleep(2)
    raise ValueError(f"finansal tablo verisi alınamadı: {last_error}")


def _annual_columns(df) -> list:
    return [c for c in df.columns if isinstance(c, str) and c.endswith("/12")]


def fetch_rd_intensity_by_year(ticker: str, years: int = RD_ANALYSIS_YEARS) -> dict:
    """Yıl -> AR-GE yoğunluğu (AR-GE gideri / satış geliri, 0-1 aralığında) sözlüğü döndürür."""
    current_year = datetime.now().year
    df = _fetch_financials_with_retry(ticker, current_year - years, current_year)

    annual_cols = _annual_columns(df)
    if not annual_cols:
        raise ValueError("yıllık (Aralık dönemi) finansal veri bulunamadı.")

    rd_row = df[df["FINANCIAL_ITEM_CODE"] == RD_ITEM_CODE]
    rev_row = df[df["FINANCIAL_ITEM_CODE"] == REVENUE_ITEM_CODE]

    if rd_row.empty or rev_row.empty:
        raise ValueError("AR-GE gideri veya satış geliri kalemi bulunamadı.")

    intensity_by_year = {}
    for col in annual_cols:
        year = col.split("/")[0]
        try:
            rd = abs(float(rd_row.iloc[0][col]))
            revenue = float(rev_row.iloc[0][col])
        except (TypeError, ValueError):
            continue
        if revenue > 0:
            intensity_by_year[year] = rd / revenue

    if not intensity_by_year:
        raise ValueError("kullanılabilir AR-GE yoğunluğu hesaplanamadı.")

    return dict(sorted(intensity_by_year.items()))


def fetch_annual_returns(ticker: str, years: list) -> dict:
    """Verilen yıllar için yıl-sonu kapanışa göre basit yıllık getiri (%) döndürür."""
    symbol = f"{ticker}.IS"
    start_year = min(int(y) for y in years) - 1
    df = yf.Ticker(symbol).history(start=f"{start_year}-01-01", interval="1d")

    if df.empty:
        raise ValueError("fiyat verisi bulunamadı.")

    df = df.dropna()
    year_end_close = df.groupby(df.index.year)["Close"].last()

    returns = {}
    for y in years:
        y_int = int(y)
        if y_int in year_end_close.index and (y_int - 1) in year_end_close.index:
            prev = year_end_close.loc[y_int - 1]
            curr = year_end_close.loc[y_int]
            if prev > 0:
                returns[y] = (curr / prev - 1) * 100
    return returns


def classify_group(avg_return_pct: float, avg_intensity: float) -> str:
    if avg_intensity < NEGLIGIBLE_RD_THRESHOLD:
        return "AR-GE Yoğunluğu İhmal Edilebilir Düzeyde"

    high_return = avg_return_pct > 0
    high_rd = avg_intensity > HIGH_RD_THRESHOLD

    if high_return and not high_rd:
        return "Yüksek Getiri / Düşük AR-GE"
    if high_return and high_rd:
        return "Yüksek Getiri / Yüksek AR-GE"
    if not high_return and high_rd:
        return "Düşük Getiri / Yüksek AR-GE"
    return "Düşük Getiri / Düşük AR-GE"


def detect_trend(intensity_by_year: dict) -> str:
    years = sorted(intensity_by_year.keys())
    if len(years) < 2:
        return "Yetersiz veri"
    diff = intensity_by_year[years[-1]] - intensity_by_year[years[0]]
    if abs(diff) < 0.005:
        return "Stabil"
    return "Artıyor" if diff > 0 else "Azalıyor"


def build_rd_signal(ticker: str, years: int = RD_ANALYSIS_YEARS) -> dict:
    intensity_by_year = fetch_rd_intensity_by_year(ticker, years)
    returns_by_year = fetch_annual_returns(ticker, list(intensity_by_year.keys()))

    common_years = [y for y in intensity_by_year if y in returns_by_year]
    if not common_years:
        raise ValueError("AR-GE verisi ile getiri verisinin ortak yılı yok.")

    avg_intensity = sum(intensity_by_year[y] for y in common_years) / len(common_years)
    avg_return = sum(returns_by_year[y] for y in common_years) / len(common_years)

    # Yoğunluk neredeyse sıfırsa (AR-GE yapmayan/az yapan şirket) oran sıfıra
    # bölme haline gelip anlamsız derecede büyük çıkar — bu durumda
    # hesaplamıyoruz (bkz. NEGLIGIBLE_RD_THRESHOLD).
    efficiency_ratio = None
    if avg_intensity >= NEGLIGIBLE_RD_THRESHOLD:
        efficiency_ratio = round(avg_return / (avg_intensity * 100), 2)

    return {
        "available": True,
        "intensity_by_year": {y: round(v, 4) for y, v in intensity_by_year.items()},
        "returns_by_year_pct": {y: round(v, 2) for y, v in returns_by_year.items()},
        "avg_intensity": round(avg_intensity, 4),
        "avg_return_pct": round(avg_return, 2),
        "efficiency_ratio": efficiency_ratio,
        "trend": detect_trend(intensity_by_year),
        "group": classify_group(avg_return, avg_intensity),
        "years_used": common_years,
    }


def _tickers_to_analyze() -> list:
    """
    Hisse listesi artık kullanıcı bazlı (bkz. auth.py) — tüm kullanıcıların
    birleşik listesini kullanır. Henüz hiç kullanıcı kayıtlı değilse (ör.
    users.db yeni oluşturulmuş) DEFAULT_TICKERS'a döner, böylece bu script
    tek başına da anlamlı çalışır.
    """
    auth.init_db()
    tickers = auth.get_all_tracked_tickers()
    if not tickers:
        print("Kayıtlı kullanıcı/hisse yok — DEFAULT_TICKERS kullanılıyor.")
        return list(DEFAULT_TICKERS)
    return tickers


def refresh_rd_cache(years: int = RD_ANALYSIS_YEARS) -> None:
    results = {}
    for ticker in _tickers_to_analyze():
        print(f"[{ticker}] AR-GE verisi çekiliyor...")
        try:
            results[ticker] = build_rd_signal(ticker, years)
            print(f"[{ticker}] OK — Grup: {results[ticker]['group']}")
        except Exception as e:
            print(f"[{ticker}] AR-GE verisi alınamadı: {e}")
            results[ticker] = {"available": False, "reason": str(e)}

    payload = {
        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "tickers": results,
    }
    with open(RD_CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    print(f"\nAR-GE cache güncellendi: {RD_CACHE_FILE}")


if __name__ == "__main__":
    refresh_rd_cache()
