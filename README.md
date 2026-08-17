# BIST Günlük Takip Botu

TRALT, SARAE, ASELS, TUPRS, EMPAE hisselerini her gün otomatik takip edip,
teknik gösterge + haber duyarlılığı + geçmiş istatistik içeren bir Markdown
raporu üreten script.

## ÖNEMLİ — Ne yapar, ne yapmaz

- ✅ Fiyat verisini, teknik göstergeleri ve haberleri **objektif olarak özetler**.
- ✅ Geçmişte benzer koşullarda ne olduğunu **şeffaf istatistiklerle** gösterir.
- ❌ "Al/Sat" tavsiyesi **vermez**, gelecekteki fiyatı **tahmin etmez**.
- ❌ Yatırım danışmanlığı değildir; kararları sen verirsin.

Haber duyarlılık analizi basit bir anahtar-kelime yöntemidir (yapay zeka
modeli değildir) — hızlı bir özet sunar ama haberlerin kendisini okumanın
yerini tutmaz.

## Web App (Panel)

Script'lerin ürettiği veriyi tarayıcıdan (telefon veya bilgisayar) görmek için
bir Flask web app'i eklendi: dashboard, hisse detay sayfası ve geçmiş
raporlar. Telegram bot (rapor + soru-cevap) kaldırılmadı — web app'in
yanında çalışmaya devam ediyor.

### Lokalde çalıştırma

```bash
pip install -r requirements.txt
cp .env.example .env   # değerleri gir (bkz. aşağıdaki "Telegram Bot Kurulumu")
python app.py
```

Tarayıcıda `http://localhost:5000` açılır. `APP_USERNAME`/`APP_PASSWORD`
`.env`'de boşsa giriş istemez; doldurursan Basic Auth ister.

### Render'a deploy (her yerden erişim için)

1. Bu klasörü bir GitHub reposuna push et.
2. [render.com](https://render.com)'da hesap aç, "New +" → "Blueprint" ile bu
   repoyu bağla (`render.yaml` ayarları otomatik okur, free plan).
3. Render dashboard'ında servisin "Environment" sekmesinden şu değişkenleri
   gir: `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`, `TELEGRAM_WEBHOOK_SECRET`,
   `REFRESH_TOKEN`, `APP_USERNAME`, `APP_PASSWORD` (`REFRESH_TOKEN`,
   `TELEGRAM_WEBHOOK_SECRET`, `APP_PASSWORD` için rastgele birer değer
   üretebilirsin, ör. `openssl rand -hex 16`).
4. Deploy tamamlanınca Render sana bir URL verir (ör.
   `https://bist-takip.onrender.com`). O URL'i tarayıcıdan aç.

**Not (free plan sınırları):** Disk kalıcı değil — `cache.json` ve
`raporlar/*.md` servis yeniden başladığında silinir. Sorun değil, çünkü her
günün raporu zaten Telegram'a gönderilip orada kalıcı kalıyor; web app'teki
"Raporlar" listesi sadece son restart'tan beri üretilenleri gösterir. Ayrıca
servis 15 dakika boyunca istek almazsa uyur; bir sonraki istek onu birkaç
saniyede uyandırır (Telegram webhook ve cron isteği de bu "istek" sayılır).

### Telegram webhook'unu bağlama

Deploy'dan sonra, botun mesajlara webhook üzerinden cevap vermesi için
TOKEN ve URL'i kendi değerlerinle bir kere şunu çalıştır (terminalden):

```bash
curl "https://api.telegram.org/bot<TOKEN>/setWebhook?url=https://<render-url>/telegram/webhook&secret_token=<TELEGRAM_WEBHOOK_SECRET>"
```

Yanıt `"ok":true` dönerse webhook aktiftir; artık `bot_listener.py`'yi ayrıca
çalıştırmana gerek yok (o script hâlâ lokal/manuel test için duruyor).

### Günlük analizi otomatik tetikleme (GitHub Actions)

Render free plan'da uygulama içi zamanlayıcı güvenilir çalışmadığı için
(`servis idle'da uyuyor`), günlük analiz dışarıdan tetikleniyor:
`.github/workflows/refresh.yml` hafta içi her gün `/api/refresh`'i çağırır.
Bunun çalışması için GitHub reposunun "Settings → Secrets and variables →
Actions" kısmına ekle:

- `REFRESH_URL` — ör. `https://bist-takip.onrender.com/api/refresh`
- `REFRESH_TOKEN` — Render'da girdiğin aynı değer

İstersen "Actions" sekmesinden workflow'u elle de (`workflow_dispatch`)
tetikleyip test edebilirsin.

## Kurulum (script'leri lokalde/zamanlanmış görevle çalıştırma)

Web app kullanmak istemiyorsan, script'ler eskisi gibi tek başına da çalışır:

1. Python 3.9+ kurulu olmalı.
2. Bu klasördeki dosyaları bilgisayarına indir.
3. Terminal/CMD'de klasöre gir ve bağımlılıkları kur:

```bash
pip install -r requirements.txt
```

4. Test için elle çalıştır:

```bash
python main.py
```

Başarılıysa `raporlar/rapor_YYYY-MM-DD.md` dosyası oluşur.

## Hisse Listesini Değiştirme

`config.py` içindeki `TICKERS` listesini düzenle:

```python
TICKERS = ["TRALT", "SARAE", "ASELS", "TUPRS", "EMPAE"]
```

## Her Gün Otomatik Çalıştırma

### Windows (Görev Zamanlayıcı)
1. Başlat menüsünden "Görev Zamanlayıcı" (Task Scheduler) aç.
2. "Temel Görev Oluştur" → günlük, istediğin saat (örn. 09:00).
3. "Program başlat" adımında:
   - Program: `python` (veya `python.exe`'nin tam yolu, örn. `C:\Python311\python.exe`)
   - Argümanlar: `main.py`
   - Başlangıç dizini: bu klasörün tam yolu (örn. `C:\Users\KullaniciAdi\bist_tracker`)

### macOS / Linux (cron)
Terminalde:

```bash
crontab -e
```

Şu satırı ekle (her gün saat 09:00'da çalışsın, borsa açılışından sonra):

```
0 9 * * 1-5 cd /tam/yol/bist_tracker && /usr/bin/python3 main.py >> log.txt 2>&1
```

`1-5` = Pazartesi-Cuma (hafta sonu borsa kapalı olduğu için gerek yok).

## Telegram Bot Kurulumu

### 1. Bot Oluştur
1. Telegram'da **@BotFather** hesabını bul, `/start` yaz.
2. `/newbot` komutunu gönder, bot için bir isim ve kullanıcı adı belirle.
3. BotFather sana bir **token** verecek (örn. `123456789:AAExxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`).
   Bunu `.env` dosyandaki (veya Render'da environment variable olarak)
   `TELEGRAM_BOT_TOKEN` alanına yapıştır — **artık `config.py`'ye elle
   yazılmıyor**, `config.py` bunu ortam değişkeninden okuyor.

### 2. Chat ID'ni Bul
1. Oluşturduğun bota Telegram'dan git, herhangi bir mesaj gönder (örn. "merhaba").
2. Tarayıcıda şu adresi aç (TOKEN yerine kendi tokenını yaz):
   ```
   https://api.telegram.org/botTOKEN/getUpdates
   ```
3. Dönen JSON içinde `"chat":{"id":123456789...}` kısmındaki sayıyı bul,
   bunu `.env` dosyandaki `TELEGRAM_CHAT_ID` alanına yaz.

### 3. Günlük Rapor Gönderimi
`main.py` her çalıştığında (elle, Task Scheduler/cron ile, veya web app
üzerinden `/api/refresh` ile), `TELEGRAM_BOT_TOKEN`/`TELEGRAM_CHAT_ID`
ortam değişkenleri girilmişse raporu otomatik olarak Telegram'a mesaj
olarak gönderir.

### 4. Soru-Cevap Botu (bot_listener.py)
İki yöntem var:

- **Web app kullanıyorsan** (yukarıdaki "Web App" bölümü): ayrıca bir şey
  çalıştırmana gerek yok — `/telegram/webhook` bu işi zaten yapıyor,
  `setWebhook` ile bir kez bağlaman yeterli.
- **Sadece script'leri lokalde kullanıyorsan**: `bot_listener.py`,
  `main.py`'dan FARKLI ve SÜREKLİ açık kalması gereken ayrı bir script.
  Çalıştığı sürece Telegram'dan gelen mesajları polling ile dinler ve
  cache.json'daki (en son main.py çalıştığında kaydedilen) veriyle cevap
  verir.

```bash
python bot_listener.py
```

**Desteklenen soru formatları:**
- `ASELS rsi`
- `ASELS macd`
- `ASELS trend`
- `ASELS haber`
- `ASELS özet`
- `yardım` (tüm komutları gösterir)

**Bunu sürekli açık tutmak için:**

*macOS/Linux:*
```bash
nohup python3 bot_listener.py > bot_log.txt 2>&1 &
```
(Bilgisayar kapanırsa bot da durur — 7/24 için ucuz bir VPS'e taşımak gerekir.)

*Windows:*
En basit yol, bir CMD penceresinde `python bot_listener.py` çalıştırıp
pencereyi açık bırakmak. Kalıcı çözüm için görev olarak "sistem başlarken
çalıştır" seçeneğiyle Task Scheduler'a eklenebilir (görev "sürekli çalışan"
olacağı için "tekrarla: 1 dakikada bir, süresiz" gibi bir ayar gerekebilir).

**Not:** Cevaplar önceden tanımlı kurallara göre üretilir (yapay zeka
modeli değildir) — hızlı ve şeffaftır ama esnek doğal dil anlama
yeteneği yoktur. Örneğin "ASELS ne durumda dostum" değil, "ASELS özet"
gibi net formatlar bekler.

## Sorun Giderme

- **"X için veri bulunamadı" hatası:** Hisse kodunun yfinance'ta doğru
  listelendiğinden emin ol. BIST kodları `.IS` uzantısıyla aranır
  (script bunu otomatik ekler), ama bazı yeni/az işlem gören hisseler
  yfinance'ta bulunmayabilir.
- **Haberler boş geliyor:** Google News RSS bazen şirket adına göre daha
  iyi sonuç verir; `news_sentiment.py` içindeki `fetch_news` çağrısına
  `company_hint` parametresi ekleyebilirsin (örn. `fetch_news("ASELS", "Aselsan")`).
- **İnternet bağlantısı gerekiyor:** Script hem fiyat hem haber verisini
  canlı çektiği için bilgisayarının internete bağlı olması gerekir
  (zamanlanmış görev çalışırken bilgisayarın açık ve bağlı olmalı).
