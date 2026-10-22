# -*- coding: utf-8 -*-
"""
Önümüzdeki ay için İSTATİSTİKSEL bir olasılık aralığı üretir — geçmiş
günlük getirilerin volatilitesine dayalı Monte Carlo simülasyonu.

ÖNEMLİ: Bu bir fiyat TAHMİNİ değildir. Gelecekte fiyatın nerede olacağını
bilmiyoruz; sadece "geçmişte bu hisse ne kadar oynak davrandı, aynı
davranış devam ederse istatistiksel olarak nasıl bir aralık beklenir"
sorusuna şeffaf bir cevap veriyoruz. Trend/momentum/haber gibi hiçbir
sinyali kullanmaz, saf rastgele yürüyüş (geometric random walk)
varsayımıyla çalışır — bu yüzden geniş bir aralık üretir ve bu kasıtlıdır.
"""

import numpy as np
import pandas as pd
from config import FORECAST_HORIZON_DAYS, FORECAST_SIMULATIONS


def simulate_forecast(df: pd.DataFrame, horizon_days: int = FORECAST_HORIZON_DAYS,
                       num_simulations: int = FORECAST_SIMULATIONS) -> dict:
    """
    Geçmiş günlük log-getirilerin ortalama/std'sine dayalı Monte Carlo
    simülasyonu ile `horizon_days` işlem günü sonrası için bir fiyat
    dağılımı üretir; %10-%90 persentil aralığını döndürür.
    """
    close = df["Close"]
    log_returns = np.log(close / close.shift(1)).dropna()

    if len(log_returns) < 20:
        return {"available": False, "reason": "Yeterli geçmiş veri yok (en az 20 gün gerekli)."}

    mu = log_returns.mean()
    sigma = log_returns.std()

    if not sigma or np.isnan(sigma):
        return {"available": False, "reason": "Volatilite hesaplanamadı."}

    last_price = close.iloc[-1]

    rng = np.random.default_rng()
    random_shocks = rng.normal(mu, sigma, size=(num_simulations, horizon_days))
    cumulative_log_returns = random_shocks.cumsum(axis=1)
    ending_prices = last_price * np.exp(cumulative_log_returns[:, -1])

    p10, p50, p90 = np.percentile(ending_prices, [10, 50, 90])

    return {
        "available": True,
        "horizon_days": horizon_days,
        "last_price": round(float(last_price), 2),
        "median": round(float(p50), 2),
        "p10": round(float(p10), 2),
        "p90": round(float(p90), 2),
        "median_change_pct": round((p50 / last_price - 1) * 100, 2),
        "p10_change_pct": round((p10 / last_price - 1) * 100, 2),
        "p90_change_pct": round((p90 / last_price - 1) * 100, 2),
        "daily_volatility_pct": round(float(sigma) * 100, 2),
        "num_simulations": num_simulations,
        "method": "Monte Carlo (geometrik rastgele yürüyüş, geçmiş günlük "
                  "log-getiri ortalama/std'sine dayalı)",
    }
