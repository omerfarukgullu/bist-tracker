# -*- coding: utf-8 -*-
"""
Fiyat verisi üzerinden teknik göstergeleri hesaplar.
Not: Bu göstergeler MEVCUT DURUMUN özetidir, gelecek tahmini değildir.
"""

import pandas as pd
from config import RSI_PERIOD, SMA_SHORT, SMA_LONG, MACD_FAST, MACD_SLOW, MACD_SIGNAL


def compute_rsi(close: pd.Series, period: int = RSI_PERIOD) -> pd.Series:
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()

    rs = avg_gain / avg_loss.replace(0, 1e-10)
    rsi = 100 - (100 / (1 + rs))
    return rsi


def compute_macd(close: pd.Series):
    ema_fast = close.ewm(span=MACD_FAST, adjust=False).mean()
    ema_slow = close.ewm(span=MACD_SLOW, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=MACD_SIGNAL, adjust=False).mean()
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram


def analyze(df: pd.DataFrame) -> dict:
    """Tüm göstergeleri hesaplayıp son değerleri ve basit yorumları döndürür."""
    close = df["Close"]

    rsi = compute_rsi(close)
    macd_line, signal_line, hist = compute_macd(close)
    sma_short = close.rolling(SMA_SHORT).mean()
    sma_long = close.rolling(SMA_LONG).mean()

    last_rsi = round(rsi.iloc[-1], 1) if not rsi.empty else None
    last_macd = round(macd_line.iloc[-1], 3)
    last_signal = round(signal_line.iloc[-1], 3)
    last_hist = round(hist.iloc[-1], 3)
    last_sma_short = round(sma_short.iloc[-1], 2) if not sma_short.isna().all() else None
    last_sma_long = round(sma_long.iloc[-1], 2) if not sma_long.isna().all() else None

    # Basit, şeffaf kural tabanlı yorumlar (tahmin değil, durum tespiti)
    if last_rsi is None:
        rsi_note = "Yeterli veri yok"
    elif last_rsi >= 70:
        rsi_note = "Aşırı alım bölgesi"
    elif last_rsi <= 30:
        rsi_note = "Aşırı satım bölgesi"
    else:
        rsi_note = "Nötr bölge"

    macd_note = "MACD sinyal çizgisinin üzerinde (pozitif momentum)" if last_macd > last_signal \
        else "MACD sinyal çizgisinin altında (negatif momentum)"

    if last_sma_short and last_sma_long:
        trend_note = "Kısa vadeli ortalama uzun vadelinin üzerinde (yükseliş eğilimi)" \
            if last_sma_short > last_sma_long else \
            "Kısa vadeli ortalama uzun vadelinin altında (düşüş eğilimi)"
    else:
        trend_note = "Trend için yeterli veri yok"

    return {
        "rsi": last_rsi,
        "rsi_note": rsi_note,
        "macd": last_macd,
        "macd_signal": last_signal,
        "macd_hist": last_hist,
        "macd_note": macd_note,
        "sma_short": last_sma_short,
        "sma_long": last_sma_long,
        "trend_note": trend_note,
    }
