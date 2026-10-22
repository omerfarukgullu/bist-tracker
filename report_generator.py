# -*- coding: utf-8 -*-
"""
Tüm verileri (fiyat, gösterge, haber, backtest) tek bir Markdown
rapor dosyasında birleştirir.
"""

import os
from datetime import datetime
from urllib.parse import urlparse

# Raporun bir kısmı DIŞ KAYNAKLI: haber başlıkları/linkleri Google News
# RSS'inden geliyor, AI yorumları ise model çıktısı. Rapor, web panelinde
# Markdown'dan HTML'e çevrilip `{{ content | safe }}` ile basılıyor ve
# Python-Markdown ham HTML'i olduğu gibi geçiriyor — yani bir haber
# başlığındaki <script> etiketi panelde ÇALIŞIRDI (depolanmış XSS).
# Aşağıdaki iki yardımcı, dış kaynaklı veriyi rapora gömmeden önce
# etkisizleştirir.
#
# `&` kasıtlı olarak escape EDİLMEZ: rapor aynı zamanda Telegram'a düz metin
# olarak gönderiliyor ve haber başlıklarında `&` sık geçtiği için orada
# "&amp;" gibi görünürdü. Etiket açmak için `<` gerekli olduğundan `<` ve `>`
# etkisizleştirmek XSS'i kapatmaya yeter.
_ALLOWED_URL_SCHEMES = ("http", "https")


def safe_text(value) -> str:
    """Dış kaynaklı metni rapora gömmek için etkisizleştirir."""
    text = str(value if value is not None else "")
    text = text.replace("<", "&lt;").replace(">", "&gt;")
    # Markdown link sözdizimini ([başlık](url)) bozacak köşeli parantezler
    return text.replace("[", r"\[").replace("]", r"\]")


def safe_url(value):
    """
    Sadece http/https linkleri döndürür; `javascript:` gibi şemalar None olur
    (Python-Markdown link hedeflerini doğrulamaz, `[x](javascript:...)` çalışır).
    """
    raw = str(value if value is not None else "").strip()
    if not raw:
        return None
    try:
        scheme = urlparse(raw).scheme.lower()
    except ValueError:
        return None
    if scheme not in _ALLOWED_URL_SCHEMES:
        return None
    # Parantezler markdown link hedefini erken kapatır
    return raw.replace("(", "%28").replace(")", "%29")


def build_volatility_section(vol: dict) -> str:
    lines = ["### Volatilite Rejimi (EGARCH)"]
    if not vol or not vol.get("available"):
        reason = (vol or {}).get("reason", "Hesaplanamadı")
        lines.append(f"- {reason}")
        lines.append("")
        return "\n".join(lines)

    lines.append(f"- Güncel koşullu volatilite: %{vol['current_volatility_pct']} (günlük)")
    lines.append(f"- Rejim: **{vol['regime']} Volatilite** (tarihsel %33/%67 persentile göre)")
    if vol.get("leverage_ratio_30d") is not None:
        lines.append(
            f"- Kaldıraç etkisi (son 30 gün): düşüş günlerinde ortalama koşullu "
            f"volatilite, yükseliş günlerine göre {vol['leverage_ratio_30d']}× "
            f"(EGARCH asimetri katsayısı: {vol.get('gamma')})"
        )
    lines.append(
        "- *(Not: Bu bir volatilite TAHMİNİ değildir — geçmiş fiyat "
        "hareketlerinden hesaplanan güncel durumun özetidir. Model kısa veri "
        "pencerelerinde belirsizlik taşıyabilir; yatırım tavsiyesi değildir.)*"
    )
    if vol["regime"] == "Yüksek":
        lines.append("")
        lines.append(
            "> ⚠️ **Yüksek Volatilite Rejimi.** Fiyat hareketleri tarihsel "
            "olarak geniş bantta seyrediyor. Bu bir tavsiye değildir; "
            "pozisyon büyüklüğü ve stop-loss disiplinine dikkat etmek "
            "isteyebilirsin."
        )
    lines.append("")
    return "\n".join(lines)


def build_rd_section(ticker: str, rd: dict) -> str:
    lines = ["### AR-GE Sinyali (Çeyreklik/Yıllık — Ayrı Job, `arge_sinyali.py`)"]
    if not rd or not rd.get("available"):
        reason = (rd or {}).get("reason", "Henüz hesaplanmamış (`python arge_sinyali.py` çalıştırılmalı).")
        lines.append(f"- {reason}")
        lines.append("")
        return "\n".join(lines)

    trend_arrow = {"Artıyor": "↑", "Azalıyor": "↓", "Stabil": "→"}.get(rd["trend"], "")
    lines.append(
        f"- AR-GE Yoğunluğu (ortalama, son {len(rd['years_used'])} yıl — "
        f"{', '.join(rd['years_used'])}): %{rd['avg_intensity'] * 100:.1f} "
        f"({trend_arrow} {rd['trend'].lower()})"
    )
    if rd.get("efficiency_ratio") is not None:
        lines.append(f"- Verimlilik Katsayısı (bilgilendirici oran): {rd['efficiency_ratio']}")
    lines.append(f"- Grup (bilgilendirici sınıflandırma): {rd['group']}")
    lines.append(
        "- *(Not: Bu sınıflandırma ve oran doğrulanmış bir yatırım sinyali "
        "değildir — geçmiş AR-GE gideri/satış oranını geçmiş getiriyle "
        "karşılaştıran basit, şeffaf bir özet istatistiktir. AR-GE'nin fiyata "
        "etkisi literatürde genelde gecikmeli olur; azalan trend uzun vadeli "
        "rekabet gücü açısından izlenmesi gereken bir sinyal olabilir, kesin "
        "bir öngörü değildir. Yatırım tavsiyesi değildir.)*"
    )
    lines.append("")
    return "\n".join(lines)


def build_chart_readings_section(chart_readings: dict) -> str:
    labels = {"price": "Fiyat / SMA", "rsi": "RSI", "macd": "MACD"}
    lines = ["### Grafik Okumaları (AI, görsel)"]

    if not chart_readings or not any(chart_readings.values()):
        lines.append("- Henüz üretilmemiş (ANTHROPIC_API_KEY ayarlı değil ya da üretim başarısız oldu).")
        lines.append("")
        return "\n".join(lines)

    for key, label in labels.items():
        reading = chart_readings.get(key)
        if reading:
            lines.append(f"**{label}:** {safe_text(reading)}")
            lines.append("")
    lines.append(
        "*(Bu okumalar, ilgili grafik yapay zeka ile görsel olarak "
        "incelenerek üretilmiştir; yatırım tavsiyesi değildir.)*"
    )
    lines.append("")
    return "\n".join(lines)


def build_ipo_signal_section(ipo: dict) -> str:
    lines = ["### Yeni Halka Arz — Tavan/Taban Seri Analizi"]
    if not ipo or not ipo.get("available"):
        return ""  # Yeni halka arz olmayan hisseler için bölüm hiç eklenmez.

    if ipo.get("current_streak_type"):
        lines.append(
            f"- Mevcut seri: **{ipo['current_streak_length']} gündür üst üste "
            f"{ipo['current_streak_type']}**."
        )
    else:
        lines.append("- Şu anda aktif bir tavan/taban serisi yok.")

    lines.append(
        f"- Bugüne kadar: {ipo['total_tavan_days']} tavan günü, "
        f"{ipo['total_taban_days']} taban günü (borsaya giriş: {ipo['listing_date']}, "
        f"{ipo['trading_days_since_listing']} işlem günü geçti)."
    )
    lines.append(
        f"- En uzun tavan serisi: {ipo['longest_tavan_streak']} gün, "
        f"en uzun taban serisi: {ipo['longest_taban_streak']} gün."
    )

    bs = ipo.get("break_stats") or {}
    if bs.get("available"):
        lines.append(
            f"- Geçmişte kırılan {bs['sample_size']} tavan serisinden sonraki 5 işlem "
            f"gününde ortalama getiri: %{bs['avg_return_5d_pct']:+.2f} "
            f"(pozitif kapanma oranı: %{bs['win_rate']})."
        )
    else:
        lines.append(f"- {bs.get('reason', 'Kırılma sonrası istatistiği için yeterli geçmiş yok.')}")

    if ipo.get("ai_assessment"):
        lines.append("")
        lines.append(f"**AI Değerlendirmesi (spekülatif):** {safe_text(ipo['ai_assessment'])}")

    lines.append(
        "- *(Not: Bu, GELECEK TAHMİNİ değildir — 'kaç tavan daha yapar' ya da "
        "'ne zaman bozar' sorusuna kesin bir cevap üretilemez. Sadece hissenin "
        "kendi geçmişine dayalı şeffaf bir seri özetidir. Tavan/taban günleri, "
        "BIST'in standart günlük fiyat bandına (~%10) yakın getiri eşiğiyle "
        "yaklaşık olarak belirlenir. Yatırım tavsiyesi değildir.)*"
    )
    lines.append("")
    return "\n".join(lines)


def build_ticker_section(ticker: str, snapshot: dict, ind: dict,
                          news_items: list, sentiment: dict, bt: dict,
                          forecast: dict = None, ai_comment: str = None,
                          volatility: dict = None, rd: dict = None,
                          chart_readings: dict = None, ipo_signal: dict = None) -> str:
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

    lines.append(build_chart_readings_section(chart_readings))

    lines.append("### Geçmiş İstatistik (RSI Aşırı Satım Sonrası, 5 gün)")
    if bt["sample_size"] > 0:
        lines.append(f"- Geçmişte {bt['sample_size']} kez bu koşul oluşmuş.")
        lines.append(f"- Bu durumlarda 5 gün sonra ortalama getiri: %{bt['avg_return_pct']}")
        lines.append(f"- Pozitif kapanan durum oranı: %{bt['win_rate']}")
        lines.append("- *(Not: Küçük örneklem boyutları istatistiksel olarak güvenilir olmayabilir.)*")
    else:
        lines.append("- Son dönemde bu koşul (RSI ≤ 30) hiç oluşmamış.")
    lines.append("")

    lines.append("### Önümüzdeki Ay İçin İstatistiksel Aralık (Tahmin Değil)")
    if forecast and forecast.get("available"):
        lines.append(f"- Yöntem: {forecast['method']}")
        lines.append(
            f"- {forecast['horizon_days']} işlem günü sonrası %10-%90 aralık: "
            f"{forecast['p10']} TL – {forecast['p90']} TL (medyan {forecast['median']} TL)"
        )
        lines.append(f"- Medyan senaryo değişimi: %{forecast['median_change_pct']:+.2f}")
        lines.append(
            "- *(Bu bir tahmin/garanti değildir — geçmiş volatiliteye dayalı "
            "istatistiksel bir aralıktır. Gerçek fiyat bu aralığın dışında da "
            "kalabilir; trend/haber gibi hiçbir sinyali hesaba katmaz.)*"
        )
    else:
        reason = (forecast or {}).get("reason", "Hesaplanamadı")
        lines.append(f"- {reason}")
    lines.append("")

    lines.append(build_volatility_section(volatility))

    if ai_comment:
        lines.append("### AI Yorumu (Veri Sentezi)")
        lines.append(safe_text(ai_comment))
        lines.append("")
        lines.append(
            "*(Bu paragraf yukarıdaki veriler temel alınarak yapay zeka ile "
            "üretilmiştir; yeni bir analiz değil, mevcut verinin özetidir. "
            "Yatırım tavsiyesi değildir.)*"
        )
        lines.append("")

    ipo_section = build_ipo_signal_section(ipo_signal)
    if ipo_section:
        lines.append(ipo_section)

    lines.append(build_rd_section(ticker, rd))

    lines.append(f"### Haber Duyarlılığı ({sentiment['count']} haber tarandı)")
    lines.append(f"- Genel eğilim: {sentiment['label']} (skor: {sentiment['average_score']})")
    if news_items:
        lines.append("")
        lines.append("**Son haberler:**")
        for item in news_items[:5]:
            tag = "🟢" if item["score"] > 0 else ("🔴" if item["score"] < 0 else "⚪")
            title = safe_text(item.get("title"))
            published = safe_text(item.get("published"))
            url = safe_url(item.get("link"))
            if url:
                lines.append(f"- {tag} [{title}]({url}) — {published}")
            else:
                # Link güvenli değil/yok — başlığı linksiz göster, atlama.
                lines.append(f"- {tag} {title} — {published}")
    lines.append("")
    lines.append("---")
    lines.append("")

    return "\n".join(lines)


def build_report(sections: list, output_dir: str) -> str:
    os.makedirs(output_dir, exist_ok=True)

    today = datetime.now().strftime("%Y-%m-%d")
    filename = os.path.join(output_dir, f"rapor_{today}.md")

    header = [
        f"# BIST Tracker — Günlük Rapor: {today}",
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
