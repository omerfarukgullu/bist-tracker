# BIST Takip Botuma Yeni Modül Ekleme — Geliştirme Prompt'u

> Bu prompt, "Finans Alanında Uluslararası Derleme, Araştırma ve Çalışmalar" (2025) kitabındaki
> **Bölüm 6 (AR-GE Yoğunluğu ve Hisse Getirisi)** ve **Bölüm 10 (Türkiye Finansal Piyasalarında
> Volatilite)** bulgularından yola çıkılarak hazırlanmıştır. Doğrudan bir kod editörüne / Claude Code'a
> yapıştırıp kullanabilirsin.

---

## Bağlam (Context)

Elimde Python ile yazılmış, her gün otomatik çalışan bir BIST takip botu var. Bot şu anda:
- TRALT, SARAE, ASELS, TUPRS, EMPAE hisselerini takip ediyor
- Teknik indikatörler, haber sentiment analizi ve backtest istatistiklerini birleştirip
  günlük bir Markdown rapor üretiyor
- Raporu Telegram üzerinden gönderiyor
- Sabit formatlı (rule-based) soru-cevap desteği var (örn: "ASELS RSI kaç?")

Bu bota **iki yeni analiz modülü** eklemek istiyorum. Aşağıdaki iki modülü, mevcut mimariye
(veri çekme → hesaplama → rapor birleştirme → Telegram gönderimi) uyacak şekilde tasarla.

---

## Modül 1: AR-GE Verimliliği / Büyüme Sinyali Katmanı

**Akademik dayanak:** BIST teknoloji ve bilişim şirketleri üzerine yapılan bir çalışma (Karaca &
Karaca, 2025), AR-GE yoğunluğu (AR-GE harcaması / satış) ile hisse getirisi arasındaki ilişkiyi
panel veri regresyonuyla incelemiş. Öne çıkan bulgular:

- AR-GE yoğunluğu tek başına getiriyi garanti etmiyor; asıl belirleyici olan **"Verimlilik
  Katsayısı" = Ortalama Getiri / Ortalama AR-GE Yoğunluğu**. Bu oran şirketleri 4 stratejik
  gruba ayırıyor:
  1. **Yüksek Getiri / Düşük AR-GE** ("pazar fırsatçısı" — teknoloji üretmeden dağıtım/ticaretten kazanan)
  2. **Yüksek Getiri / Yüksek AR-GE** ("gerçek teknoloji şirketi" — sürdürülebilir, teknolojik bariyeri yüksek)
  3. **Düşük Getiri / Yüksek AR-GE** ("yatırım aşamasında" — getiri henüz gelmemiş, potansiyel kırılma noktası)
  4. **Düşük AR-GE / Düşük Getiri**
- AR-GE'nin hisse fiyatına etkisi **eş zamanlı değil**; literatürde genelde yatırımı izleyen
  1-3 yıl içinde ortaya çıkıyor ("zaman gecikmesi" / time-lag etkisi).
- AR-GE yoğunluğu bir noktadan sonra "azalan verimler" nedeniyle piyasa değerine katkı
  sağlamayabiliyor (Ters-U eğrisi fenomeni).
- 2020 gibi genel piyasa şoklarında (pandemi) getiri artışı AR-GE'den değil makro koşullardan
  kaynaklanabiliyor — bu yüzden AR-GE sinyali makro rejimden ayrıştırılmalı.

**İstenen özellik:**

1. KAP (Kamu Aydınlatma Platformu) veya finansal tablo verisinden, takip edilen her hisse için
   yıllık **AR-GE Yoğunluğu** (AR-GE gideri / net satış) hesapla. (Not: TRALT, SARAE, ASELS,
   TUPRS, EMPAE için bu veri KAP finansal tablolarından çekilebilir; ASELS savunma/teknoloji
   şirketi olduğu için burada anlamlı bir sinyal üretme ihtimali en yüksek.)
2. Her hisse için **Verimlilik Katsayısı** = (son N yıllık ortalama getiri) / (son N yıllık
   ortalama AR-GE yoğunluğu) hesapla ve hisseyi yukarıdaki 4 stratejik gruptan birine ata.
3. Yıllık AR-GE yoğunluğundaki **trend yönünü** (artıyor / azalıyor / stabil) tespit et — azalan
   AR-GE trendini "uzun vadeli rekabet gücü zayıflama riski" olarak günlük rapora bir uyarı
   etiketi şeklinde ekle.
4. Bu modülün çıktısı günlük olarak değil, **çeyreklik/yıllık finansal tablo yayınlandığında**
   güncellenmeli (KAP'tan yeni bilanço geldiğinde tetiklenecek ayrı bir job olsun).
5. Rapora eklenecek örnek satır formatı:
   `ASELS | AR-GE Yoğunluğu: 0.18 (↑ artıyor) | Verimlilik Katsayısı: 9.4 | Grup: Yüksek Getiri/Yüksek AR-GE`

---

## Modül 2: Rejim-Duyarlı Volatilite Katmanı (GARCH ailesi)

**Akademik dayanak:** Türkiye piyasaları üzerine yapılan bir literatür taraması (Şahin, 2025),
şu noktaları vurguluyor:

- BIST'te volatilite **kümelenen ve kalıcı** bir süreç; klasik sabit varyans varsayımı yerine
  koşullu değişen varyans modelleri (ARCH/GARCH ailesi) çok daha başarılı sonuç veriyor.
- **Kaldıraç etkisi** doğrulanmış: negatif şoklar (fiyat düşüşleri), pozitif şoklara göre BIST'te
  daha güçlü volatilite tepkisi yaratıyor → simetrik GARCH yerine **EGARCH veya TGARCH**
  kullanmak Türkiye piyasası için daha isabetli.
- **Rejim değişimi** önemli: Markov Rejim Değişimli GARCH (MS-GARCH) modelleriyle BIST 100'de
  düşük / normal / yüksek volatilite rejimleri zamansal olarak ayrışıyor; kriz dönemlerinde
  yüksek volatilite rejimi baskın hale geliyor.
- Sektörler arası farklılık var: bazı sektörlerde faiz/kur oynaklığı, bazılarında küresel risk
  iştahı göstergeleri volatiliteyi daha çok belirliyor.

**İstenen özellik:**

1. Mevcut teknik indikatör hesaplama katmanına, her takip edilen hisse için günlük olarak
   **EGARCH(1,1)** (veya `arch` Python kütüphanesindeki TARCH/GJR-GARCH) modeliyle koşullu
   volatilite tahmini ekle. (Kütüphane önerisi: `arch` paketi — `arch_model(returns, vol='EGARCH', p=1, o=1, q=1)`)
2. Basit bir eşik/rejim sınıflandırması ekle: son N günlük koşullu volatiliteyi tarihsel
   dağılıma göre **Düşük / Normal / Yüksek Volatilite Rejimi** olarak etiketle (örn. yüzdelik
   dilim bazlı: <33. persentil = düşük, 33-67 = normal, >67 = yüksek).
3. Kaldıraç etkisini görünür kıl: negatif ve pozitif günlük getirilerin volatiliteye etkisini
   ayrı ayrı raporla (örn. "son 30 günde düşüş günleri volatiliteyi yükseliş günlerinden X kat
   daha fazla artırdı" gibi basit bir oran).
4. Bu rejim bilgisini, mevcut rule-based Q&A özelliğine yeni bir sabit soru formatı olarak ekle:
   örn. "ASELS volatilite rejimi ne?" → "Yüksek Volatilite Rejimi (son 30 gün, EGARCH tahmini)"
5. Rejim "Yüksek"e geçtiğinde günlük Telegram raporunda otomatik bir uyarı bloğu oluştur
   (pozisyon büyüklüğü/stop-loss disiplinine dikkat çeken, tavsiye niteliği taşımayan nötr bir not).

---

## Teknik Kısıtlar / Tercihler

- Python, mevcut proje yapısına (script tabanlı, Telegram entegrasyonlu) uygun şekilde entegre et.
- Yeni bağımlılıklar: `arch` (GARCH modelleri için). KAP/finansal tablo verisi çekimi için
  mevcut veri kaynağı neyse onu kullan; yoksa `isyatirimhisse` veya benzeri açık kütüphaneleri öner.
- Ağır hesaplamaları (GARCH fit) günlük job'dan ayır, cache'le — her gün sıfırdan fit etmek
  yerine parametreleri periyodik güncelle.
- Rapor formatı mevcut Markdown şablonuyla tutarlı olsun; yeni bölüm başlıkları ekle
  ("## AR-GE Sinyali", "## Volatilite Rejimi") ama mevcut RSI/haber sentiment bölümlerini bozma.
- Tüm çıktılar bilgilendirici olsun, "AL/SAT tavsiyesi" dili kullanma — bot zaten rule-based
  Q&A ile çalışıyor, serbest yorum üretmiyor.

---

## Beklenen Teslim

1. `arge_sinyali.py` — AR-GE yoğunluğu + verimlilik katsayısı hesaplama modülü
2. `volatilite_rejimi.py` — EGARCH tabanlı rejim sınıflandırma modülü
3. Mevcut günlük rapor oluşturucuya bu iki modülün entegrasyonu (rapor şablonuna yeni bölümler)
4. Rule-based Q&A'ya yeni soru kalıplarının eklenmesi
