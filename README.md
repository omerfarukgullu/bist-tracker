# BIST Tracker

TRALT, SARAE, ASELS, TUPRS, EMPAE hisselerini her gün otomatik takip edip,
teknik gösterge + haber duyarlılığı + geçmiş istatistik içeren bir Markdown
raporu üreten script.

## ÖNEMLİ — Ne yapar, ne yapmaz

- ✅ Fiyat verisini, teknik göstergeleri ve haberleri **objektif olarak özetler**.
- ✅ Geçmişte benzer koşullarda ne olduğunu **şeffaf istatistiklerle** gösterir.
- ✅ Önümüzdeki ay için, geçmiş volatiliteye dayalı **istatistiksel bir olasılık
  aralığı** (Monte Carlo simülasyonu) ve isteğe bağlı olarak bu veriyi
  özetleyen bir **AI yorumu** sunar (bkz. "İstatistiksel Aralık ve AI Yorumu").
- ❌ "Al/Sat" tavsiyesi **vermez**. İstatistiksel aralık ve AI yorumu da dahil
  hiçbir çıktı, fiyatın gelecekte kesin olarak ne olacağının **garantisi
  değildir** — geçmiş veriye dayalı, şeffaf bir olasılık özetidir.
- ❌ Yatırım danışmanlığı değildir; kararları sen verirsin.

Haber duyarlılık analizi basit bir anahtar-kelime yöntemidir (yapay zeka
modeli değildir) — hızlı bir özet sunar ama haberlerin kendisini okumanın
yerini tutmaz.

## Web App (Panel)

Script'lerin ürettiği veriyi tarayıcıdan (telefon veya bilgisayar) görmek için
bir Flask web app'i eklendi: dashboard, hisse detay sayfası ve geçmiş
raporlar. Telegram bot (rapor + soru-cevap) kaldırılmadı — web app'in
yanında çalışmaya devam ediyor.

Sağ üstteki **TR/EN** butonuyla arayüz dili değiştirilebilir (tercih bir
cookie'de saklanır, kalıcıdır). Kapsam: tüm sayfa metinleri, göstergeler
(RSI/MACD/trend notları, volatilite rejimi, AR-GE grubu/trendi, haber
duyarlılığı etiketi) ve grafik etiketleri. **Kapsam dışı** (bilinçli
tercih): AI Yorumu, Grafik Okuması ve Telegram bot mesajları günde bir kez
üretilip önbelleğe yazıldığı için hep üretildikleri dilde (Türkçe) kalır —
her görüntüleyen için anlık iki dilde üretmek AI maliyetini ikiye katlardı.
`raporlar/*.md` dosyaları da üretildikleri anda Türkçe yazılır.

### Lokalde çalıştırma

```bash
pip install -r requirements.txt
cp .env.example .env   # değerleri gir (bkz. aşağıdaki "Telegram Bot Kurulumu")
python app.py
```

Tarayıcıda `http://127.0.0.1:5000` açılır.

Geliştirme sunucusu varsayılan olarak **sadece kendi bilgisayarına** bağlanır
ve debugger kapalıdır. İki ortam değişkeniyle değiştirilebilir:

- `FLASK_DEBUG=1` — Flask debugger'ını açar. **Yalnızca lokalde kullan:**
  debugger, tarayıcı üzerinden sunucuda kod çalıştırılmasına izin verir.
- `HOST=0.0.0.0` — aynı ağdaki diğer cihazların (telefon vb.) erişmesine
  izin verir. Bunu `FLASK_DEBUG=1` ile birlikte kullanma.
 `/kayit` sayfasından kullanıcı adı/
e-posta/şifre ile hesap açılır, `/giris` ile giriş yapılır — birden fazla
kişi kayıt olabilir, **her kullanıcının kendi hisse takip listesi** vardır
(bkz. "Çoklu Kullanıcı ve Hisse Listeleri"). E-posta doğrulaması veya şifre
sıfırlama yoktur; e-posta sadece profil bilgisi olarak saklanır. Kullanıcı
bilgileri lokal `users.db` (SQLite) dosyasında tutulur.

`python app.py` çalıştığı sürece (uygulama açık kaldığı sürece), fiyat/gösterge/
istatistiksel aralık verisi arka planda her `PRICE_REFRESH_MINUTES` (varsayılan
5) dakikada bir otomatik tazelenir — bu hafif yenileme haberleri tekrar
taramaz, AI yorumunu tekrar üretmez, Telegram'a mesaj göndermez (sadece daha
önce `main.py`/`/api/refresh` ile tam analiz çalışmış hisseleri günceller).
Haber + AI yorumu + Telegram raporu içeren tam günlük analiz ayrı ve bağımsız
çalışır (bkz. "Her Gün Otomatik Çalıştırma").

### Render'a deploy (her yerden erişim için)

1. Bu klasörü bir GitHub reposuna push et.
2. [render.com](https://render.com)'da hesap aç, "New +" → "Blueprint" ile bu
   repoyu bağla (`render.yaml` ayarları otomatik okur, free plan).
3. Render dashboard'ında servisin "Environment" sekmesinden şu değişkenleri
   gir: `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`, `TELEGRAM_WEBHOOK_SECRET`,
   `REFRESH_TOKEN`, `SECRET_KEY` (oturum çerezlerini imzalamak için —
   girilmezse otomatik üretilip yerel bir dosyada saklanır, ama Render'ın
   diski kalıcı olmadığından her restart'ta oturumlar düşer; production'da
   `SECRET_KEY`'i elle set etmen önerilir). Rastgele değer üretmek için:
   `openssl rand -hex 32`.
4. Deploy tamamlanınca Render sana bir URL verir (ör.
   `https://bist-tracker.onrender.com`). O URL'i tarayıcıdan aç.

**Not (free plan sınırları):** Disk kalıcı değil — `cache.json`,
`raporlar/*.md` ve **`users.db` (kayıtlı kullanıcılar)** servis yeniden
başladığında silinir. Rapor/cache verisi için sorun değil, çünkü her günün
raporu zaten Telegram'a gönderilip orada kalıcı kalıyor. Ama kullanıcı
hesapları için bu, her restart'ta herkesin yeniden kayıt olması gerektiği
anlamına gelir — kalıcı kullanım için Render'da bir "Persistent Disk"
eklemen (paralı) ya da harici bir veritabanına geçmen gerekir. Ayrıca
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

- `REFRESH_URL` — ör. `https://bist-tracker.onrender.com/api/refresh`
- `REFRESH_TOKEN` — Render'da girdiğin aynı değer

İstersen "Actions" sekmesinden workflow'u elle de (`workflow_dispatch`)
tetikleyip test edebilirsin.

`/api/refresh` analizi **arka planda** başlatır ve hemen `202 {"status":
"started"}` döner (tam analiz dakikalar sürüyor ve gunicorn'un 30 saniyelik
worker timeout'una takılıyordu). Analiz hâlâ sürüyorsa `409 {"status":
"already_running"}` döner. Durumu görmek için:

```bash
curl -H "Authorization: Bearer <REFRESH_TOKEN>" https://<url>/api/refresh/status
```

## İstatistiksel Aralık ve AI Yorumu

Her hisse için iki ek bilgi üretilir (rapor, web panel ve Telegram `tahmin`
komutunda görünür):

1. **İstatistiksel aralık** (`forecast.py`) — geçmiş günlük getirilerin
   volatilitesine dayalı bir Monte Carlo simülasyonu, önümüzdeki ~1 ay
   (21 işlem günü) için %10-%90 persentil fiyat aralığı üretir. Ekstra
   kurulum gerekmez, her zaman çalışır. **Bu bir fiyat tahmini değildir** —
   trend, haber veya momentum gibi hiçbir sinyali kullanmaz, sadece "geçmiş
   oynaklık aynı şekilde sürerse istatistiksel olarak beklenen aralık nedir"
   sorusuna şeffaf bir cevap verir.

2. **AI yorumu** (`ai_summary.py`, opsiyonel) — yukarıdaki istatistiksel
   aralık, teknik göstergeler ve haber duyarlılığını Claude API ile 3-5
   cümlelik okunabilir bir Türkçe paragrafa çevirir. AI burada **kendi
   başına fiyat üretmez veya tahmin yapmaz** — sadece zaten hesaplanmış
   veriyi sentezler; sistem promptu al/sat tavsiyesini ve kesin
   yükselecek/düşecek ifadelerini açıkça yasaklıyor.

Aktif etmek için `.env` dosyana (veya Render'da environment variable olarak)
`ANTHROPIC_API_KEY` ekle ([console.anthropic.com](https://console.anthropic.com)
üzerinden alınır). **Girilmemişse bu özellik tamamen devre dışı kalır** —
hiçbir hata oluşmaz, sadece AI yorumu boş geçilir; istatistiksel aralık
yine üretilir. Maliyet düşüktür (günde 5 hisse × 1 istek — birkaç kuruş
seviyesinde).

## Volatilite Rejimi (EGARCH)

`volatilite_rejimi.py`, `arch` paketiyle her hisse için günlük olarak
EGARCH(1,1) modeli uyumlayıp koşullu volatiliteyi hesaplar; bunu kendi
tarihsel dağılımına göre **Düşük / Normal / Yüksek** rejime sınıflandırır
ve kaldıraç etkisini (düşüş günlerinin volatiliteye pozitif şoklardan farklı
etkisi) hem EGARCH'ın asimetri katsayısıyla hem de son 30 günün basit
düşüş/yükseliş volatilite oranıyla raporlar. Rapor, web panel ve Telegram
`volatilite` komutunda görünür. Rejim "Yüksek" olduğunda raporda ayrıca
nötr bir uyarı bloğu çıkar (tavsiye değildir).

Bu **bir volatilite tahmini değildir** — sadece geçmiş fiyat hareketlerinden
güncel durumun şeffaf bir özetidir. GARCH modeli kısa fiyat pencerelerinde
(ör. yeni halka arz olmuş hisseler) yeterli veri bulamayıp "Hesaplanamadı"
diyebilir; bu normaldir. Ekstra kurulum gerekmez, günlük `main.py`
akışının bir parçasıdır.

## Yeni Halka Arz Tespiti ve Tavan/Taban Seri Analizi

`halka_arz_sinyali.py`, bir hissenin **yeni halka arz** olup olmadığını iki
katmanlı tespit eder: birincil olarak Borsa İstanbul'un resmi BIST Halka Arz
Endeksi'nin (XHARZ) güncel üye listesini (`hisse_endeks_ds.csv`, halka
arzdan sonra 2 yıl üyelik) çeker; CSV çekilemezse hissenin toplam işlem günü
sayısına (`RECENT_IPO_TRADING_DAYS`) dayalı bir yaklaşık tespite düşer.

Yeni halka arz olarak sınıflandırılan hisseler için, kendi fiyat geçmişine
dayanan şeffaf bir **tavan/taban seri özeti** üretir: mevcut kaç gündür üst
üste tavan/taban yapıldığı, bugüne kadarki toplam tavan/taban gün sayısı,
en uzun seri, ve (varsa) geçmişte kırılan tavan serilerinden sonraki 5
işlem gününde ortalama getiri. Web panelde hisse detay sayfasında (sadece
yeni IPO'larda görünen bir bölüm), raporlarda ve Telegram `tavan`/`taban`
komutunda görünür.

ANTHROPIC_API_KEY ayarlıysa, ek olarak bu istatistikleri, hissenin son 10
işlem gününün kapanış/hacim verisini ve haber duyarlılığını birlikte
değerlendiren, kısa ve açıkça **"AI Değerlendirmesi (spekülatif)"** olarak
etiketlenmiş bir yorum da üretilir — devam mı yoksa kırılma mı daha olası
görünüyor gibi tedbirli bir tartışma, her zaman "bu bir AI tahminidir"
uyarısıyla biter. Ayarlı değilse bu kısım sessizce görünmez, geri kalan
istatistikler etkilenmez.

**Bu, "kaç tavan daha yapar" ya da "ne zaman bozar" tarzında bir GELECEK
TAHMİNİ değildir** — hiçbir yöntem bunu dürüstçe veremez. Kendi geçmişinde
daha önce kırılan bir seri yoksa (çoğu yeni IPO'da bu geçerlidir), modül bir
sayı uydurmaz; "yeterli geçmiş yok" der. Tavan/taban günleri, BIST'in
standart ±%10 günlük fiyat bandına yakın bir getiri eşiğiyle (`TAVAN_TABAN_BAND_PCT`)
yaklaşık olarak belirlenir — resmi bir eşik verisi yfinance'ta yok. Ekstra
kurulum gerekmez, günlük `main.py` akışının ve hisse eklerken çalışan ilk
analizin bir parçasıdır.

## AR-GE Sinyali (ayrı, periyodik çalışan modül)

`arge_sinyali.py`, [isyatirimhisse](https://github.com/urazakgul/isyatirimhisse)
üzerinden her hissenin yıllık AR-GE gideri ve satış geliri kalemlerini çekip
**AR-GE Yoğunluğu** (AR-GE gideri / satış geliri) ve buna dayalı basit bir
**"Verimlilik Katsayısı"** (ortalama getiri % / ortalama AR-GE yoğunluğu %)
hesaplar; hisseyi 4 bilgilendirici gruptan birine ("Yüksek Getiri/Yüksek
AR-GE" vb.) atar ve yoğunluk trendini (artıyor/azalıyor/stabil) çıkarır.

**Önemli sınırlamalar (şeffaflık için):**
- Bu oran ve gruplama **doğrulanmış, akademik olarak kanıtlanmış bir
  yatırım sinyali değildir** — geçmiş AR-GE harcamasını geçmiş getiriyle
  kıyaslayan basit, açıklayıcı bir istatistiktir. Al/Sat tavsiyesi değildir.
- AR-GE yoğunluğu ihmal edilebilir düzeydeyse (gelirin ~%0.1'inden az —
  ör. AR-GE yapmayan şirketler) Verimlilik Katsayısı hesaplanmaz (sıfıra
  bölme nedeniyle anlamsız derecede büyük çıkardı); bunun yerine "AR-GE
  Yoğunluğu İhmal Edilebilir Düzeyde" etiketi gösterilir.
- Yakın zamanda halka arz olmuş hisselerde (Yahoo Finance'ta yeterli
  fiyat geçmişi yoksa) çok yıllı getiri hesaplanamaz; bu durumda modül
  net bir "veri yok" mesajı üretir, uydurma sayı göstermez.
- `isyatirimhisse` API'si zaman zaman zaman aşımına uğrayabiliyor (birkaç
  deneme otomatik yapılır). Bu yüzden bu modül **günlük `main.py`
  akışına dahil değildir** — elle veya çeyreklik/yıllık finansal tablo
  yayınlandığında ayrıca çalıştır:

```bash
python arge_sinyali.py
```

Bu, sonuçları `rd_cache.json`'a yazar; `main.py` (ve web panel/Telegram)
bu dosyayı sadece **okur**, kendisi yeniden hesaplamaz — dosya yoksa veya
güncel değilse ilgili bölüm "henüz hesaplanmamış" der.

## Grafik Okuması (AI, görsel)

`grafik_okuma.py`, her hissenin **Fiyat/SMA**, **RSI** ve **MACD**
grafiklerinin HER BİRİNİ ayrı ayrı `matplotlib` ile görsel bir PNG olarak
render edip Claude'un vision özelliğiyle "okutur" — AI burada sayı/metin
değil, gerçek bir grafik görseline bakıp bir teknik analist gibi 2-4
cümlelik yorum üretir. Sabit tek bir okuma değildir; web panelde hangi
grafik sekmesindeysen (Fiyat/SMA, RSI, MACD) altındaki "Grafik Okuması"
metni ona göre değişir. Rapor ve Telegram `grafik` komutunda üçü birden
görünür.

Bu, günlük `main.py` akışının bir parçasıdır (her gün otomatik güncellenir)
ve `ANTHROPIC_API_KEY` gerektirir (yukarıdaki "İstatistiksel Aralık ve AI
Yorumu" bölümündeki aynı key) — ayarlanmamışsa bu özellik sessizce devre
dışı kalır. "Anlık" (gün-içi) grafik için okuma üretilmez — bu okumalar
günde bir kez üretilir, sürekli değişen anlık grafiğe uymaz.

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

## Çoklu Kullanıcı ve Hisse Listeleri

Panelde birden fazla kişi kayıt olabilir, her kullanıcının **kendi bağımsız
hisse takip listesi** vardır — biri panelinde bir hisse ekleyip çıkarsa bu
sadece kendi listesini etkiler, diğer kullanıcıların dashboard'unu değiştirmez.
Hisse verisinin kendisi (fiyat/gösterge/haber/AI yorumu) ise paylaşımlıdır:
bir hisseyi ilk takip eden kullanıcı için tam analiz çalıştırılır, aynı
hisseyi sonradan takip eden başka bir kullanıcı için tekrar hesaplanmaz —
mevcut veri kullanılır. Bir hissenin detay sayfasına (`/hisse/<kod>`), kayıtlı
herhangi bir kullanıcı tarafından takip ediliyorsa, giriş yapmış her
kullanıcı URL üzerinden erişebilir (dashboard'da listelenmesi ayrı, görülmesi
ayrı).

**Panelden ekleme/çıkarma:** Panelin üstündeki "Hisse kodu ekle" kutusuna
BIST kodunu yaz (ör. `THYAO`) ve "+ Ekle"ye bas — kod doğrulanır (yfinance'ta
gerçekten var mı diye kontrol edilir). Her kartın sağ üstündeki **×** ile
kendi listenden çıkarabilirsin.

Kullanıcı hesapları ve hisse listeleri `users.db` (SQLite) dosyasında
tutulur — `auth.py` bu veriyi yönetir. `main.py`, `bot_listener.py` ve
`arge_sinyali.py` gibi script'ler, tüm kullanıcıların birleşik (union) hisse
listesi üzerinde çalışır (`auth.get_all_tracked_tickers()`), tek bir
kullanıcıya bağlı değildir. Yeni kayıt olan bir kullanıcının başlangıç
listesi `config.py`'deki `DEFAULT_TICKERS`'tan gelir:

```python
DEFAULT_TICKERS = ["TRALT", "SARAE", "ASELS", "TUPRS", "EMPAE"]
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
- `ASELS tahmin` (istatistiksel aralık + AI yorumu)
- `ASELS volatilite` (EGARCH volatilite rejimi)
- `ASELS arge` (AR-GE yoğunluğu ve verimlilik katsayısı)
- `ASELS grafik` (Fiyat/RSI/MACD grafiklerinin AI ile görsel okuması)
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

## Geliştirme

Her push ve pull request'te `.github/workflows/ci.yml` çalışır: lint
(`ruff`, pyflakes kuralları), tüm dosyaların derlenmesi,
`from config import ...` tutarlılık kontrolü ve modüllerin ağ erişimi
olmadan içe aktarılabildiğinin doğrulanması.

Aynı kontrolleri lokalde çalıştırmak için:

```bash
pip install ruff
ruff check --select F,E9 .
python -m compileall -q .
python tools/check_config_imports.py
```

Modüllerin akademik dayanağı ve tasarım notları:
[`docs/modul-tasarim-notlari.md`](docs/modul-tasarim-notlari.md).

## Lisans

[MIT](LICENSE) — serbestçe kullanabilir, değiştirebilir ve dağıtabilirsin.
Yazılım "olduğu gibi", garanti verilmeksizin sunulur; bu bir yatırım
tavsiyesi aracı değildir (bkz. yukarıdaki "ÖNEMLİ — Ne yapar, ne yapmaz").
