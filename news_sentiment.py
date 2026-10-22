# -*- coding: utf-8 -*-
"""
Google News RSS üzerinden hisseyle ilgili haberleri çeker ve
basit bir anahtar-kelime tabanlı duyarlılık skoru üretir.

ÖNEMLİ SINIRLAMA: Bu, gelişmiş bir NLP modeli değil; şeffaf ve
denetlenebilir olsun diye kelime listesine dayalı basit bir yaklaşımdır.
Ciddi kararlar için haberlerin kendisini mutlaka oku.
"""

import feedparser
import requests
from urllib.parse import quote
from config import NEWS_LIMIT_PER_TICKER

# feedparser.parse(url) kendi indirmesini yapar ve HİÇBİR timeout uygulamaz —
# Google News yanıt vermediğinde günlük analiz süresiz askıda kalıyordu.
# İndirmeyi requests ile (timeout'lu) yapıp feedparser'a hazır metni veriyoruz.
NEWS_FETCH_TIMEOUT = 15

POSITIVE_WORDS = [
    "kar", "kâr", "artış", "yükseldi", "yükseliş", "rekor", "büyüme",
    "anlaşma", "ihracat", "yeni yatırım", "temettü", "başarı", "güçlü",
    "olumlu", "iyileşme", "kazanç", "genişleme", "ödül", "onay",
]

NEGATIVE_WORDS = [
    "zarar", "düşüş", "düştü", "kayıp", "iflas", "soruşturma", "ceza",
    "kriz", "gerileme", "olumsuz", "iptal", "dava", "grev", "kesinti",
    "risk", "endişe", "belirsizlik", "kapatma", "borç",
]


def _score_text(text: str) -> int:
    text_lower = text.lower()
    score = 0
    for w in POSITIVE_WORDS:
        if w in text_lower:
            score += 1
    for w in NEGATIVE_WORDS:
        if w in text_lower:
            score -= 1
    return score


def fetch_news(ticker: str, company_hint: str = "") -> list:
    """
    Google News RSS'ten hisseyle ilgili son haberleri çeker.
    company_hint: arama kalitesini artırmak için şirket adı ipucu (opsiyonel).
    """
    query = quote(f"{ticker} {company_hint} hisse".strip())
    url = f"https://news.google.com/rss/search?q={query}&hl=tr&gl=TR&ceid=TR:tr"

    try:
        resp = requests.get(
            url, timeout=NEWS_FETCH_TIMEOUT, headers={"User-Agent": "Mozilla/5.0"}
        )
        resp.raise_for_status()
    except requests.RequestException as e:
        print(f"[{ticker}] haberler çekilemedi: {e}")
        return []

    feed = feedparser.parse(resp.content)
    items = []
    for entry in feed.entries[:NEWS_LIMIT_PER_TICKER]:
        title = entry.get("title", "")
        summary = entry.get("summary", "")
        published = entry.get("published", "")
        score = _score_text(f"{title} {summary}")
        items.append({
            "title": title,
            "link": entry.get("link", ""),
            "published": published,
            "score": score,
        })
    return items


def summarize_sentiment(news_items: list) -> dict:
    if not news_items:
        return {"average_score": 0, "label": "Haber bulunamadı", "count": 0}

    total = sum(item["score"] for item in news_items)
    avg = total / len(news_items)

    if avg > 0.3:
        label = "Genel olarak olumlu"
    elif avg < -0.3:
        label = "Genel olarak olumsuz"
    else:
        label = "Nötr / karışık"

    return {"average_score": round(avg, 2), "label": label, "count": len(news_items)}
