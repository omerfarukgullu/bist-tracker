# -*- coding: utf-8 -*-
"""
Grafik Okuması — hissenin Fiyat/SMA, RSI ve MACD grafiklerinin HER BİRİNİ
ayrı ayrı görsel olarak render edip Claude'un vision özelliğiyle teknik bir
"grafik okuması" üretir. AI burada gerçekten GRAFİĞİ GÖRÜYOR (sayı/metin
değil, görsel) — bir teknik analistin grafiğe bakıp yorum yapması gibi.

ÖNEMLİ SINIRLAMA: Bu bir fiyat tahmini veya al/sat tavsiyesi değildir —
sadece o grafikte görülen trend/momentum gibi gözlemlerin şeffaf bir
özetidir. ANTHROPIC_API_KEY ayarlanmamışsa bu özellik tamamen devre dışı
kalır (main.py diğer her şeyi eskisi gibi üretmeye devam eder).
"""

import base64
import io
from typing import Optional

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

import anthropic
from config import ANTHROPIC_API_KEY, SMA_SHORT, SMA_LONG
from indicators import compute_rsi, compute_macd

BG = "#0b0d11"
SURFACE = "#11141a"
BORDER = "#262b36"
TEXT = "#eef0f3"
MUTED = "#8b93a1"
ACCENT = "#4c8dff"
UP = "#3ecf8e"
DOWN = "#ef5350"

# Her grafik türü için AI'ya ne "aramasını" söylediğimiz odak noktası —
# tek bir genel prompt yerine grafiğe özel, daha isabetli bir okuma verir.
CHART_TYPES = {
    "price": {
        "label": "Fiyat / SMA",
        "focus": (
            "Fiyatın zaman içindeki genel trend yönü, kısa (SMA{short}) ve "
            "uzun (SMA{long}) vadeli hareketli ortalamalara göre konumu, "
            "ortalamaların birbirine göre kesişimleri (varsa) ve dikkat "
            "çeken formasyonlar."
        ).format(short=SMA_SHORT, long=SMA_LONG),
    },
    "rsi": {
        "label": "RSI",
        "focus": (
            "RSI çizgisinin aşırı alım (70 üzeri) veya aşırı satım (30 "
            "altı) bölgelerine yakınlığı, momentumun yönü ve son "
            "dönemdeki dalgalanma karakteri."
        ),
    },
    "macd": {
        "label": "MACD",
        "focus": (
            "MACD çizgisinin sinyal çizgisine göre konumu, histogramın "
            "büyüyüp küçülmesi, kesişim noktaları (varsa) ve momentum "
            "yönü."
        ),
    },
}


def _is_enabled() -> bool:
    return bool(ANTHROPIC_API_KEY)


def _new_fig():
    fig, ax = plt.subplots(figsize=(9, 4.2), dpi=110)
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(SURFACE)
    ax.tick_params(colors=MUTED, labelsize=8)
    ax.grid(True, color=BORDER, linewidth=0.5, alpha=0.6)
    for spine in ax.spines.values():
        spine.set_color(BORDER)
    fig.autofmt_xdate()
    return fig, ax


def _legend(ax):
    ax.legend(loc="upper left", fontsize=8, facecolor=SURFACE, edgecolor=BORDER, labelcolor=TEXT)


def _fig_to_base64(fig) -> str:
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)
    buf.seek(0)
    return base64.standard_b64encode(buf.read()).decode("utf-8")


def render_price_chart_image(df: pd.DataFrame) -> str:
    close = df["Close"]
    sma_short = close.rolling(SMA_SHORT).mean()
    sma_long = close.rolling(SMA_LONG).mean()

    fig, ax = _new_fig()
    ax.plot(df.index, close, label="Kapanış", color=ACCENT, linewidth=1.6)
    ax.plot(df.index, sma_short, label=f"SMA{SMA_SHORT}", color=UP, linewidth=1.1)
    ax.plot(df.index, sma_long, label=f"SMA{SMA_LONG}", color=DOWN, linewidth=1.1)
    _legend(ax)
    return _fig_to_base64(fig)


def render_rsi_chart_image(df: pd.DataFrame) -> str:
    rsi = compute_rsi(df["Close"])

    fig, ax = _new_fig()
    ax.plot(df.index, rsi, label="RSI", color=ACCENT, linewidth=1.6)
    ax.axhline(70, color=DOWN, linestyle="--", linewidth=1)
    ax.axhline(30, color=UP, linestyle="--", linewidth=1)
    ax.set_ylim(0, 100)
    _legend(ax)
    return _fig_to_base64(fig)


def render_macd_chart_image(df: pd.DataFrame) -> str:
    macd_line, signal_line, hist = compute_macd(df["Close"])

    fig, ax = _new_fig()
    ax.bar(df.index, hist, color=MUTED, width=1.0, alpha=0.6, label="Histogram")
    ax.plot(df.index, macd_line, label="MACD", color=ACCENT, linewidth=1.4)
    ax.plot(df.index, signal_line, label="Sinyal", color=DOWN, linewidth=1.1)
    _legend(ax)
    return _fig_to_base64(fig)


RENDERERS = {
    "price": render_price_chart_image,
    "rsi": render_rsi_chart_image,
    "macd": render_macd_chart_image,
}


def _read_chart(ticker: str, chart_type: str, image_b64: str) -> Optional[str]:
    meta = CHART_TYPES[chart_type]
    system_prompt = (
        "Sen bir BIST hisse takip aracının parçasısın. Sana bir hissenin "
        f"'{meta['label']}' grafiği görsel olarak veriliyor. Görevin bu "
        "grafiği 2-4 cümlelik bir Türkçe okumayla özetlemek. "
        f"Odaklan: {meta['focus']}\n\n"
        "DİL VE ÜSLUP (ÇOK ÖNEMLİ):\n"
        "- Okuyucunun borsa/teknik analiz hakkında HİÇBİR bilgisi olmadığını "
        "varsay — 'RSI', 'MACD', 'hareketli ortalama' gibi bir terim "
        "kullanacaksan yanına parantez içinde tek cümlelik çok sade bir "
        "açıklama ekle.\n"
        "- 'Bir teknik analist gibi' değil, 'bir arkadaşına grafiği "
        "tarif ediyormuş gibi' basit ve kısa cümlelerle yaz.\n\n"
        "KESİN KURALLAR:\n"
        "- Al/sat tavsiyesi verme, gelecekteki fiyat hakkında kesin "
        "tahminde bulunma.\n"
        "- Sadece grafikte GÖRDÜĞÜN şeyleri tarif et; grafikte olmayan "
        "bilgi (haber, temel veriler) hakkında varsayımda bulunma.\n"
        "- Yatırım tavsiyesi olmadığını ayrıca hatırlatmana gerek yok."
    )

    try:
        client = anthropic.Anthropic()
        response = client.messages.create(
            model="claude-opus-5",
            max_tokens=16000,  # bkz. ai_summary.py: thinking bu sınırdan düşer
            output_config={"effort": "low"},
            system=system_prompt,
            messages=[{
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {"type": "base64", "media_type": "image/png", "data": image_b64},
                    },
                    {
                        "type": "text",
                        "text": f"{ticker} hissesinin '{meta['label']}' grafiğini teknik olarak oku ve yorumla.",
                    },
                ],
            }],
        )
        if response.stop_reason == "refusal":
            print(f"[{ticker}] {meta['label']} grafik okuması reddedildi (refusal).")
            return None
        if response.stop_reason == "max_tokens":
            print(f"[{ticker}] {meta['label']} grafik okuması token sınırında kesildi — yarım metin gösterilmiyor.")
            return None
        return next((b.text for b in response.content if b.type == "text"), None)
    except Exception as e:
        print(f"[{ticker}] {meta['label']} grafik okuması üretilemedi: {e}")
        return None


def build_chart_readings(ticker: str, df: pd.DataFrame) -> dict:
    """
    Fiyat/SMA, RSI ve MACD grafiklerinin HER BİRİ için ayrı bir AI grafik
    okuması üretir — sabit/tek bir okuma değil, her grafik türüne özel.
    ANTHROPIC_API_KEY yoksa hepsi None döner, hiçbir hata oluşmaz.
    """
    readings = {}
    for chart_type, renderer in RENDERERS.items():
        if not _is_enabled():
            readings[chart_type] = None
            continue
        try:
            image_b64 = renderer(df)
        except Exception as e:
            print(f"[{ticker}] {CHART_TYPES[chart_type]['label']} grafiği render edilemedi: {e}")
            readings[chart_type] = None
            continue
        readings[chart_type] = _read_chart(ticker, chart_type, image_b64)
    return readings
