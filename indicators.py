# -*- coding: utf-8 -*-
"""
Fiyat verisi üzerinden teknik göstergeleri hesaplar.
Not: Bu göstergeler MEVCUT DURUMUN özetidir, gelecek tahmini değildir.
"""

import pandas as pd
from config import RSI_PERIOD, SMA_SHORT, SMA_LONG, MACD_FAST, MACD_SLOW, MACD_SIGNAL


def _wilder_average(series: pd.Series, period: int) -> pd.Series:
    """
    Wilder yumuşatması: tohum değer ilk `period` gözlemin düz ortalamasıdır,
    sonraki her değer `(önceki * (period-1) + yeni) / period` ile ilerler.

    `ewm(alpha=1/period, adjust=False)` tek başına yeterli DEĞİL: o, serinin
    ilk değerinden tohumlar ve kısa serilerde Wilder'dan 6-11 puan sapar.
    Tohumu period'uncu konuma yazıp öncesini NaN bırakınca `ignore_na=True`
    ile özyineleme doğru noktadan başlar.
    """
    out = series.astype(float).copy()
    out.iloc[:period] = float("nan")
    out.iloc[period] = series.iloc[1:period + 1].mean()
    return out.ewm(alpha=1 / period, adjust=False, ignore_na=True).mean()


def compute_rsi(close: pd.Series, period: int = RSI_PERIOD) -> pd.Series:
    """
    Wilder yumuşatmasıyla standart RSI.

    Önceden `rolling(period).mean()` (düz hareketli ortalama) kullanılıyordu.
    Bu, Wilder'ın 1978'de tanımladığı ve TradingView/Investing dahil yaygın
    platformların uyguladığı RSI DEĞİLDİR: düz ortalama, pencereden çıkan günü
    tamamen atıp yapay sıçramalar üretir; Wilder ise geçmişi 1/period
    ağırlığıyla üstel olarak söndürür. İki yöntem aynı hisse için gözle
    görülür farklı değerler verdiğinden, panelde gösterilen RSI kullanıcının
    başka bir yerde gördüğüyle uyuşmuyordu.
    """
    # Tohum için `period`+1 kapanış gerekir (ilk fark NaN olduğundan).
    if len(close) <= period:
        return pd.Series(float("nan"), index=close.index)

    delta = close.diff()
    avg_gain = _wilder_average(delta.clip(lower=0), period)
    avg_loss = _wilder_average(-delta.clip(upper=0), period)

    rsi = 100 - (100 / (1 + avg_gain / avg_loss))

    # Sınır durumları: avg_loss sıfırsa bölme inf/NaN üretir. Hiç düşüş yoksa
    # RSI 100; ne düşüş ne yükseliş varsa (yatay fiyat) konvansiyon 50'dir.
    # Isınma periyodundaki NaN'lar etkilenmez (NaN karşılaştırmaları False).
    rsi = rsi.mask((avg_loss == 0) & (avg_gain > 0), 100.0)
    rsi = rsi.mask((avg_loss == 0) & (avg_gain == 0), 50.0)
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
