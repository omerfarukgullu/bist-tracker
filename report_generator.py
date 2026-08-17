# -*- coding: utf-8 -*-
"""
Tüm verileri (fiyat, gösterge, haber, backtest) tek bir Markdown
rapor dosyasında birleştirir.
"""

import os
from datetime import datetime


def build_ticker_section(ticker: str, snapshot: dict, ind: dict,
                          news_items: list, sentiment: dict, bt: dict) -> str:
    lines = [f"## {ticker}", ""]

    lines.append(f"**Son Kapanış:** {snapshot['last_close']} TL "
                 f"({snapshot['change']:+.2f} / {snapshot['change_pct']:+.2f}%) "
                 f"— {snapshot['date']}")
    lines.append(f"**Hacim:** {snapshot['volume']:,}")
    lines.append("")

    lines.append("### Teknik Göstergeler")
    lines.append(f"- RSI ({ind['rsi']}): {ind['rsi_note']}")
    lines.append(f"- MACD ({ind['macd']} / sinyal {ind['macd_signal']}): {ind['macd_note']}")
    lines.append(f"- SMA20 ({ind['sma_short']}) vs SMA50 ({ind['sma_long']}): {ind['trend_note']}")
    lines.append("")

    lines.append("### Geçmiş İstatistik (RSI Aşırı Satım Sonrası, 5 gün)")
    if bt["sample_size"] > 0:
        lines.append(f"- Geçmişte {bt['sample_size']} kez bu koşul oluşmuş.")
        lines.append(f"- Bu durumlarda 5 gün sonra ortalama getiri: %{bt['avg_return_pct']}")
        lines.append(f"- Pozitif kapanan durum oranı: %{bt['win_rate']}")
        lines.append("- *(Not: Küçük örneklem boyutları istatistiksel olarak güvenilir olmayabilir.)*")
    else:
        lines.append("- Son dönemde bu koşul (RSI ≤ 30) hiç oluşmamış.")
    lines.append("")

    lines.append(f"### Haber Duyarlılığı ({sentiment['count']} haber tarandı)")
    lines.append(f"- Genel eğilim: {sentiment['label']} (skor: {sentiment['average_score']})")
    if news_items:
        lines.append("")
        lines.append("**Son haberler:**")
        for item in news_items[:5]:
            tag = "🟢" if item["score"] > 0 else ("🔴" if item["score"] < 0 else "⚪")
            lines.append(f"- {tag} [{item['title']}]({item['link']}) — {item['published']}")
    lines.append("")
    lines.append("---")
    lines.append("")

    return "\n".join(lines)


def build_report(sections: list, output_dir: str) -> str:
    os.makedirs(output_dir, exist_ok=True)

    today = datetime.now().strftime("%Y-%m-%d")
    filename = os.path.join(output_dir, f"rapor_{today}.md")

    header = [
        f"# BIST Günlük Takip Raporu — {today}",
        "",
        "> Bu rapor otomatik üretilmiştir. Teknik göstergeler ve haber "
        "duyarlılığı mevcut durumun özetidir; **yatırım tavsiyesi değildir** "
        "ve gelecekteki fiyat hareketini garanti etmez.",
        "",
        "---",
        "",
    ]

    content = "\n".join(header) + "\n".join(sections)

    with open(filename, "w", encoding="utf-8") as f:
        f.write(content)

    return filename
