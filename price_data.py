# -*- coding: utf-8 -*-
"""
BIST hisseleri için geçmiş fiyat verisini yfinance üzerinden çeker.
"""

import yfinance as yf
import pandas as pd
from config import HISTORY_DAYS


def fetch_history(ticker: str) -> pd.DataFrame:
    """
    Verilen BIST kodu için son HISTORY_DAYS günlük OHLCV verisini döndürür.
    BIST hisseleri yfinance'ta '.IS' uzantısıyla bulunur (örn. ASELS.IS).
    """
    symbol = f"{ticker}.IS"
    df = yf.Ticker(symbol).history(period=f"{HISTORY_DAYS}d", interval="1d")

    if df.empty:
        raise ValueError(
            f"{ticker} için veri bulunamadı. Kodun doğru olduğundan "
            f"ve yfinance'ta '{symbol}' olarak listelendiğinden emin ol."
        )

    df = df.dropna()
    return df


# "Anlık" sekmesindeki periyot seçenekleri: her biri için yfinance'a
# sorulacak (period, interval) ve son çekilen pencerenin tek işlem gününe
# kırpılıp kırpılmayacağı (trim_to_last_day — sadece "1d" için gerekli,
# hafta sonu/tatilde bile en son işlem gününü göstermek için).
INTRADAY_RANGES = {
    "1d": {"period": "5d", "interval": "5m", "trim_to_last_day": True, "label": "Günlük"},
    "1w": {"period": "5d", "interval": "15m", "trim_to_last_day": False, "label": "Haftalık"},
    "1mo": {"period": "1mo", "interval": "60m", "trim_to_last_day": False, "label": "Aylık"},
    "6mo": {"period": "6mo", "interval": "1d", "trim_to_last_day": False, "label": "6 Aylık"},
    "1y": {"period": "1y", "interval": "1d", "trim_to_last_day": False, "label": "Yıllık"},
}


def fetch_intraday(ticker: str, range_key: str = "1d") -> pd.DataFrame:
    """
    "Anlık" sekmesi için seçilen periyoda (INTRADAY_RANGES) göre fiyat
    verisi döndürür. "1d" için hafta sonu/tatilde bile son işlem gününü
    göstermek üzere birkaç günlük pencere çekip en son tarihe kırpılır.
    """
    cfg = INTRADAY_RANGES.get(range_key, INTRADAY_RANGES["1d"])
    symbol = f"{ticker}.IS"
    df = yf.Ticker(symbol).history(period=cfg["period"], interval=cfg["interval"])

    if df.empty:
        raise ValueError(
            f"{ticker} için veri bulunamadı. Yahoo Finance bu hisse için "
            f"bu periyotta veri sağlamıyor olabilir."
        )

    df = df.dropna()
    if cfg["trim_to_last_day"]:
        last_date = df.index[-1].date()
        df = df[df.index.date == last_date]
    return df


def latest_snapshot(df: pd.DataFrame) -> dict:
    """Son işlem gününe ait özet bilgiyi çıkarır."""
    last = df.iloc[-1]
    prev = df.iloc[-2] if len(df) > 1 else last

    change = last["Close"] - prev["Close"]
    change_pct = (change / prev["Close"] * 100) if prev["Close"] else 0.0

    return {
        "last_close": round(last["Close"], 2),
        "change": round(change, 2),
        "change_pct": round(change_pct, 2),
        "volume": int(last["Volume"]),
        "date": df.index[-1].strftime("%Y-%m-%d"),
    }
