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
