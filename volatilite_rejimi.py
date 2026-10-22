# -*- coding: utf-8 -*-
"""
EGARCH(1,1) tabanlı koşullu volatilite ve rejim sınıflandırması.

ÖNEMLİ SINIRLAMA: Bu, gelecekteki volatiliteyi TAHMİN ETMEZ. Sadece geçmiş
fiyat hareketlerinden, güncel koşullu volatilitenin kendi tarihsel
dağılımına göre nerede durduğunu (düşük/normal/yüksek) şeffaf biçimde
özetler. GARCH modelleri parametre belirsizliği taşır — özellikle kısa veri
pencerelerinde katsayılar istatistiksel olarak anlamlı çıkmayabilir; bu
modül böyle durumlarda da sonucu üretir ama kesinlik iddia etmez.

Kaldıraç etkisi (negatif şokların volatiliteye pozitif şoklardan farklı
etki etmesi) EGARCH'ın asimetri katsayısı (gamma) ile ölçülür; ayrıca son
30 günün düşüş/yükseliş günlerindeki ortalama koşullu volatilite oranı
sezgisel bir karşılaştırma olarak eklenir.
"""

import numpy as np
import pandas as pd
import yfinance as yf
from arch import arch_model

from config import VOLATILITY_HISTORY_DAYS

MIN_OBSERVATIONS = 60


def fetch_long_history(ticker: str, days: int = VOLATILITY_HISTORY_DAYS) -> pd.DataFrame:
    """
    GARCH modeli için ana price_data.fetch_history'den (HISTORY_DAYS) daha
    uzun, bağımsız bir fiyat penceresi çeker — daha güvenilir parametre
    tahmini için.
    """
    symbol = f"{ticker}.IS"
    df = yf.Ticker(symbol).history(period=f"{days}d", interval="1d")

    if df.empty:
        raise ValueError(f"{ticker} için volatilite hesaplaması amacıyla veri bulunamadı.")

    return df.dropna()


def compute_volatility_regime(df: pd.DataFrame) -> dict:
    close = df["Close"]
    returns = 100 * close.pct_change().dropna()

    if len(returns) < MIN_OBSERVATIONS:
        return {
            "available": False,
            "reason": f"Volatilite modeli için yeterli veri yok (en az {MIN_OBSERVATIONS} gün gerekli, {len(returns)} var).",
        }

    try:
        model = arch_model(returns, vol="EGARCH", p=1, o=1, q=1, dist="normal")
        result = model.fit(disp="off", show_warning=False)
    except Exception as e:
        return {"available": False, "reason": f"Model uyumlanamadı: {e}"}

    cond_vol = result.conditional_volatility
    current_vol = float(cond_vol.iloc[-1])

    p33, p67 = np.percentile(cond_vol, [33, 67])
    if current_vol < p33:
        regime = "Düşük"
    elif current_vol > p67:
        regime = "Yüksek"
    else:
        regime = "Normal"

    gamma = result.params.get("gamma[1]")
    gamma_pvalue = result.pvalues.get("gamma[1]")

    # Sezgisel kaldıraç oranı: son 30 günün düşüş/yükseliş günlerindeki
    # ortalama koşullu volatilite kıyası (EGARCH gamma katsayısına ek,
    # daha kolay okunabilir bir özet).
    recent_returns = returns.tail(30)
    recent_vol = cond_vol.tail(30)
    down_days_vol = recent_vol[recent_returns < 0]
    up_days_vol = recent_vol[recent_returns > 0]
    leverage_ratio = None
    if len(down_days_vol) > 0 and len(up_days_vol) > 0 and up_days_vol.mean() > 0:
        leverage_ratio = round(float(down_days_vol.mean() / up_days_vol.mean()), 2)

    return {
        "available": True,
        "current_volatility_pct": round(current_vol, 2),
        "regime": regime,
        "percentile_low": round(float(p33), 2),
        "percentile_high": round(float(p67), 2),
        "gamma": round(float(gamma), 4) if gamma is not None else None,
        "gamma_pvalue": round(float(gamma_pvalue), 4) if gamma_pvalue is not None else None,
        "leverage_ratio_30d": leverage_ratio,
        "observations": len(returns),
    }
