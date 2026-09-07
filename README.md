# YERKON karşılaştırma tablosu simülasyonu

Bu depo tek bir iş yapar: YERKON sunumunda tarif edilen şehir içi, kırsal
ve kritik bölge kurulumlarını simüle eder ve karşılaştırma tablosuna
girecek dört satırı üretir. Sayılar varsayılmaz, hesaplanır; her girdinin
nereden geldiği çıktıya iliştirilir.

```bash
python run.py
```

Çıktı `output/yerkon_rows.csv`: sadece dört satır.

## Üretilen satırlar

| Sistem | Teknoloji | Ortam | HPE P50 | HPE P95 | VPE P95 | Kullanılabilirlik | Alan | CAPEX |
|---|---|---|---|---|---|---|---|---|
| YERKON (Şehir İçi - Kalibreli)¹ | Karasal PNT (SX1280/LoRa TWR) | Dış | 1,26 m | 3,00 m | 30,89 m | ≈ %97,9 | 1,00 km² | ≈ 66.937 TL/km² |
| YERKON (Şehir İçi - Ham)² | Karasal PNT (SX1280/LoRa TWR) | Dış | 1,52 m | 5,08 m | 50,68 m | ≈ %97,9 | 1,00 km² | ≈ 66.937 TL/km² |
| YERKON (Kırsal)³ | Karasal PNT (E28-SX1280 TWR) | Dış | 4,04 m | 14,15 m | 24,18 m | ≈ %98,8 | 1,01 km² | ≈ 471.524 TL/km² |
| YERKON (Kritik Bölge/Tünel)⁴ | Karasal PNT (UWB/DWM3000 TWR) | İç + dış | 0,26 m | 1,89 m | 5,55 m | ≈ %97,0 | 1,00 km² | ≈ 545.903 TL/km² |

Dipnotlar:

1. 1 km × 1 km şehir hücresi, 150 m aralıklı 49 yayın birimi (8/20/35 m
   montaj yüksekliği). Modül başına menzil ofseti kalibrasyonu uygulanmış.
2. Aynı kurulum, kalibrasyon adımı atlanmış. Tek fark bu; anchor sayısı,
   geometri ve maliyet birebir aynı.
3. 42 km karayolu koridoru. 200 m'de bir, yolun iki tarafında karşılıklı
   levha montajı (6 m) ve 2,5 km'de bir kule (35-45 m). Kapsama, levha
   hatları arasındaki 24 m genişliğindeki taşıt yolu.
4. 50 km tünel/metro ağı, 150 m aralıklı 334 UWB düğümü. UWB için
   kalibreli ölçüm verisi yok; hata modeli sunumun kendi hedefine
   parametrelendi ve bu yüzden donanım-kalibreli olarak etiketlenmedi.

OPEX her satırda "-". Sunum yıllık işletme maliyeti vermiyor ve
karşılaştırma tablosu, yayımlanmış işletme maliyeti olmayan diğer
sistemler için zaten "-" kullanıyor. Oraya bir tahmin yazmak, tablodaki
tek uydurma sayı olurdu.

## Sonuçlar nasıl okunmalı

**Yatay doğruluk üç senaryoda da kullanılabilir seviyede.** Şehir içinde
metre altı P50'ye yaklaşıyor, tünelde 26 cm.

**Dikey doğruluk her yerde yataydan çok daha kötü.** Sebebi donanım değil,
geometri. Karasal bir sistemde her anchor alıcıya göre neredeyse aynı
yükseklikte durur; yükseklik eksenini kısıtlayacak dik bakış açısı yoktur.
Alıcıdan bir yol levhasına 100 m mesafede bakış açısı 2,6 derece, 250
m'de 1,0 derecedir. GNSS'te aynı açı 45 derece civarındadır. Ayrıntılı
açıklama: [docs/METHOD.md](docs/METHOD.md#dikey-hata-neden-yatay-hatadan-kötü).

**Kalibrasyon bedava ve büyük fark yaratıyor.** Robinson'un yayımladığı
SX1280 verisinde 2,83 m'lik sabit bir sapma var. Modül başına ofset
kalibrasyonu bunu siler; yatay hatayı biraz, dikey hatayı 50,68 m'den
30,89 m'ye düşürür. Sunumun mimarisi bu adımı zaten öngörüyor, iki satır
uygulanması ile atlanması arasındaki farkı gösteriyor.

**CAPEX/km² koridor kurulumlarını haksız gösteriyor.** Bir tünel ya da
yol şeridi ince bir kurdeledir; km² başına maliyet, alan tipi bir
kurulumla karşılaştırıldığında yanıltır. Koridorlar için km başına
maliyet daha anlamlıdır: kırsal 11.317 TL/km, tünel 10.918 TL/km.

## Kurulum ve çalıştırma

```bash
pip install -r requirements.txt     # numpy, scipy
python run.py                       # output/yerkon_rows.csv

python run.py --details             # + tüm metrikler (JSON)
python run.py --image               # + tablo görseli (matplotlib gerekir)
python run.py --repeats 1000        # daha çok Monte Carlo tekrarı
```

Aynı seed aynı sayıları verir. Varsayılan seed 42, varsayılan tekrar
sayısı örnek başına 300.

Testler:

```bash
pip install pytest && python -m pytest -q
```

## Depo yapısı

```
run.py                  tek giriş noktası
yerkon/
  evidence.py           bir sayının nereden geldiğini taşıyan kayıt
  geometry.py           3B menzil geometrisi, HDOP/VDOP, geometri kalitesi
  ranging_error.py      SX1280 (ölçüme dayalı) ve DWM3000 (yapılandırılmış) hata modelleri
  path.py               test yörüngeleri
  simulate.py           menzil kısıtlı Monte Carlo konum çözümü
  metrics.py            doğruluk, güvenilirlik, maliyet
  scenarios.py          dört kurulum senaryosunun tanımı
  table.py              satır biçimlendirme ve CSV
  render.py             PNG görsel (opsiyonel)
docs/
  METHOD.md             her tablo değerinin nasıl hesaplandığı
  SCENARIOS.md          her senaryonun tam parametre dökümü
  EVIDENCE.md           kanıt sınıfları ve sınırlar
```

## Sınırlar

Kısa liste; tamamı [docs/EVIDENCE.md](docs/EVIDENCE.md) içinde.

- SX1280 hata modeli altı yayımlanmış ölçüm noktasından geliyor ve
  yalnızca 0-250 m aralığını kapsıyor. Kırsal bağlantıların %83'ü bu
  aralığın dışında; bu bir çıkarsama (extrapolation) ve çıktıda oran
  olarak raporlanıyor.
- DWM3000 için kalibreli veri yok. Tünel satırı bir tasarım hedefinin
  simülasyonu, bir ölçümün değil.
- Bağlantı menzilleri, NLOS oranları, montaj yükseklikleri ve anchor
  aralıkları bu projenin varsayımları. Sunum bunları vermiyor.
- CAPEX yalnızca bileşen maliyeti. Montaj, sertifikasyon, altyapı, enerji
  ve işçilik dahil değil. Gerçek CAPEX daha yüksek olacak.
- Sonuçlar tek atımlık (single-epoch) konum hatası. Kalman filtresi veya
  harita kısıtı gibi izleme katmanları modellenmedi; gerçek sistem
  bunlarla daha iyi sonuç verir.
