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

    oversold_days = rsi[rsi <= 30].index
    if len(oversold_days) == 0:
        return {"sample_size": 0, "win_rate": None, "avg_return_pct": None}

    returns = []
    for day in oversold_days:
        idx = close.index.get_loc(day)
        if idx + forward_days < len(close):
            future_price = close.iloc[idx + forward_days]
            current_price = close.iloc[idx]
            returns.append((future_price - current_price) / current_price * 100)

    if not returns:
        return {"sample_size": 0, "win_rate": None, "avg_return_pct": None}

    wins = sum(1 for r in returns if r > 0)
    return {
        "sample_size": len(returns),
        "win_rate": round(wins / len(returns) * 100, 1),
        "avg_return_pct": round(sum(returns) / len(returns), 2),
        "forward_days": forward_days,
    }
