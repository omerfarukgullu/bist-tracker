# -*- coding: utf-8 -*-
"""
Basit backtest: "RSI aşırı satımdayken sonraki 5 günde ne olmuş?" gibi
geçmişe dönük şeffaf istatistikler üretir. Bu bir GARANTİ değil,
sadece geçmişte o koşulda ne sıklıkla ne olduğunun özetidir.
"""

import pandas as pd
from indicators import compute_rsi
from config import RSI_PERIOD


def rsi_oversold_stats(df: pd.DataFrame, forward_days: int = 5) -> dict:
    close = df["Close"]
    rsi = compute_rsi(close, RSI_PERIOD)

    # Örtüşmeyen pencereler: RSI art arda birkaç gün 30'un altında kaldığında
    # her gün ayrı örnek sayılıyordu. Ardışık günlerin 5 günlük ileri
    # getirileri büyük ölçüde AYNI fiyat hareketini ölçtüğünden örneklem
    # şişiyor ve tek bir düşüş epizodu sonucu domine ediyordu. Artık bir örnek
    # alındıktan sonra onun ileri penceresi bitene kadar yeni örnek alınmaz.
    # (Konum tabanlı döngü, index'te tekrar eden tarih olsa da güvenli —
    # get_loc o durumda slice döndürüyordu.)
    oversold = (rsi <= 30).to_numpy()
    returns = []
    next_allowed = 0
    for idx in range(len(close) - forward_days):
        if idx < next_allowed or not oversold[idx]:
            continue
        current_price = close.iloc[idx]
        future_price = close.iloc[idx + forward_days]
        returns.append((future_price - current_price) / current_price * 100)
        next_allowed = idx + forward_days

    if not returns:
        return {"sample_size": 0, "win_rate": None, "avg_return_pct": None}

    wins = sum(1 for r in returns if r > 0)
    return {
        "sample_size": len(returns),
        "win_rate": round(wins / len(returns) * 100, 1),
        "avg_return_pct": round(float(sum(returns) / len(returns)), 2),
        "forward_days": forward_days,
    }
