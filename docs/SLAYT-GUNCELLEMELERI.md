# Slayt güncellemeleri

`YERKON.pptx` için yapılacaklar, slayt slayt. Her madde ne değişecek,
önerilen metin ve neden. Yapılan maddenin kutusunu işaretleyin; yeni
bir bulgu çıktığında buraya eklenir. Ayrıntılı gerekçe
`BASVURU-INCELEMESI.md` dosyasında.

Sayı biçimi: ondalık virgül, binlik ayırıcı yok (sitedeki gibi).

Son güncelleme: 24 Eylül 2026.

## Bütün sunum

- [ ] Başlıklar 14 pt kalın, Times New Roman (şartname IV). Slayt içi
  başlıklar ("Dünyadan Örnekler", "YERKON Mimarisi", "Grup 1", "Pilot
  Doğrulama" vb.) kendi boyutu olmadan gövde boyutunu alıyor;
  PowerPoint'te 14 pt kalın yapılmalı.
- [ ] İngilizce kelimeler Türkçe karşılıklarıyla: "cross-check" →
  "çapraz doğrulama", "reconvergence time" → "yeniden yakınsama süresi"
  (parantez içinde İngilizcesi kalabilir), "deployment" → "kurulum".
- [ ] Slayt 10 ve 16'daki İngilizce kısaltma (sitenin kullanmadığı,
  ADR-0066) hiçbir yerde kalmamalı: "karasal konumlandırma" yazılmalı.
- [ ] Sayfa sınırı: sunum ve form birlikte 20 sayfa olabilir. UDHAM'a
  sorulmalı (seval.cinar@uab.gov.tr, erkan.hacioglu@uab.gov.tr). Cevap
  gelene kadar sunumu 18 slayta indirecek yer: slayt 17 ve 18'i tek
  dipnot slaytında birleştirmek, slayt 20'yi kaldırmak.

## Slayt 1: kapak

- [ ] "TEMMUZ 2026" tarihi başvuru tarihine göre güncellenmeli.

## Slayt 2: proje ekibi

- Değişiklik yok.

## Slayt 3: proje konusu

- [ ] "istenilen yerde istenilen doğrulukta" ölçülü bir ifadeyle
  değişmeli. Öneri: "ortama göre metre sınıfında doğrulukla".
- [ ] Web sitesi adresi burada var; formun "Projeyi açıkladığımız web
  sitesi" satırına da yazılmalı: https://ysoktar.github.io/yerkon/

## Slayt 4: dünyadan örnekler

- [ ] New Mexico: "askeri GPS karıştırma aktivitesine maruz kalarak bir
  dağa çarptı" yerine: "NTSB'nin ön raporuna göre askeri bir GPS
  karıştırma tatbikatının sürdüğü bir uçuşta Capitan Dağları'na çarptı;
  kazanın nedeni henüz belirlenmedi."
- [ ] Aynı paragraftaki "Grup 2 Kırsal Yayın Birimi'nin 8 kilometreyi
  bulabilen menzili sayesinde alçak irtifada bu tür kazalar önlenebilir"
  cümlesi çıkarılmalı. Yol kenarındaki direkler yerdeki alıcı için
  konumlandırılıyor; modelde düşey hata (VPE P95) şehirde 64 m, kırsalda
  141 m. Bir uçağa düşeyde yardım edecek bir sistem değil.
- [ ] Baltık (Tartu): "Grup 3 ... uçakların güvenle iniş yapabilmesini
  sağlayabilecek" iddiası çıkarılmalı ya da "apron ve yer araçları"
  ile sınırlanmalı.
- [ ] Karadeniz: "40 km (25 mil)" kaynaklarla uyuşmuyor. Kaynaklar "25
  deniz mili" (yaklaşık 46 km) ya da "yaklaşık 32 km" diyor. Kullanılan
  kaynağın sayısı yazılmalı.

## Slayt 5: mimari

- [ ] "100 adet üretimde yaklaşık 1000-1600 TL" iki yerde geçiyor.
  Güncel: "100 adette 798-1212 TL, 1000 adette 718-1091 TL (ana
  bileşenler)". Formdaki aralıkla aynı olmalı.
- [ ] TDoA için "yayın birimi başına ~100.000 TL" kaynaksız. Ya kaynak
  eklenmeli ya da sayı çıkarılıp "ağ genelinde nanosaniye düzeyinde
  senkronizasyon altyapısı gerektirir" denmeli.
- [ ] ECDSA: "alıcı konum verisi talep ettiğinde yayınlar" ve imza
  anlatımı her yanıtın imzalandığı izlenimini veriyor. 64 baytlık imza
  SX1280'de bir mesafe ölçümünü 31,8 ms'den 63,9 ms'ye çıkarıyor. Öneri:
  "Yayın birimi kimliğini, koordinatını ve bir sayacı seyrek aralıklarla
  imzalı olarak yayınlar; mesafe ölçüm alışverişleri kısa tutulur ve bu
  imzalı kimliğe bağlanır."

## Slayt 6: kurulum türleri

- [ ] Grup 1, SX1280 "±1 m": Semtech'in yaklaşık 1 m'si 40 kanalda 80
  ölçümün ortalaması (AN1200.29). Öneri: "Üretici, 40 kanalda frekans
  atlamalı yaklaşık 80 ölçümün ortalamasıyla LoS koşulunda yaklaşık 1 m
  bildirmektedir; tek bir ölçümün hatası daha büyüktür (bağımsız bir
  ölçümde yaklaşık 2,9 m)."
- [ ] Grup 2, E28-2G4M27S ve "8-10 km": bu cümle değişmeli. Önerilen metin:

  > "SX1280 tabanlı 2,4 GHz sistemlerin kırsal kapsaması, Türkiye'deki
  > 2400-2483,5 MHz e.i.r.p. ve güç spektral yoğunluğu sınırlarına uygun
  > olarak değerlendirilecektir. Genel sınır 20 dBm e.i.r.p.'dir; ancak
  > TS EN 300 328 kapsamındaki frekans atlamasız geniş bant iletimlerde
  > geçerli 10 dBm/MHz güç yoğunluğu sınırı, SX1280'in 1,625 MHz'lik
  > yüksek doğruluklu mesafe ölçümü ayarında yaklaşık 12,1 dBm e.i.r.p.
  > üst sınırına karşılık gelir. Bu nedenle 27 dBm çıkışlı
  > E28-2G4M27S'nin üretici tarafından 27 dBm'de bildirilen 8 km
  > haberleşme menzili YERKON için doğrudan kullanılamaz. Yasal güç
  > seviyesindeki haberleşme ve mesafe ölçüm menzili saha testleriyle
  > belirlenecektir."

  Bu metin bir başka değerlendirmeden alındı ve modelle uyumlu: model
  aynı iki sınırı uygulayıp düşük olanı alıyor (`regulatory.py`).
- [ ] İsteğe bağlı ek cümle, doğrulanırsa: "Mesafe ölçümü EN 300 328
  anlamında frekans atlamalı yapılırsa güç yoğunluğu sınırı yerine
  20 dBm'lik toplam sınır geçerli olur; bu durumda amplifikatörlü modül
  yeniden anlam kazanır." Modelde bu, 10 m direkte 5 m hassasiyetli
  menzili 3,5 km'den 5,5 km'ye çıkarıyor. BTK ya da bir test laboratuvarı
  doğrulamadan sunuma girmemeli.
- [ ] Sayı verilecekse model sonucu olarak verilmeli: "Simülasyonda, düz
  zeminde ve 10 m direkte, bağlantı yaklaşık 7,4 km'ye kadar kuruluyor;
  5 m menzil hassasiyeti yaklaşık 3,5 km'de bitiyor. Bu sayılar alıcı
  duyarlılığı varsayımına çok bağlı ve saha ölçümüyle doğrulanacak."
  Bu bir yasal ya da fiziksel sınır değil, model çıktısı.
- [ ] Grup 3, DWM3000 "yaklaşık 10 cm": tek bir mesafe ölçümünün sınıfı
  olduğu söylenmiş, iyi. Yanına modelin tünel sonucu eklenebilir: HPE
  P50 0,78 m.

## Slayt 7: alıcı modülleri

- [ ] Araç alıcısı "3-5 dBi çubuk anten" diyor; model W24P-U anteniyle
  çalışıyor. Hangisi olacaksa ikisi aynı olmalı.
- [ ] IMU, odometri ve harita kısıtı henüz modelde yok. "Kullanılacaktır"
  yerine "pilotta eklenecek ve etkisi ölçülecek" denmeli.

## Slayt 8: Ar-Ge soruları

- [ ] TWR ölçeklenebilirlik sorusuna sayı eklenmeli: "SX1280'de bir
  mesafe ölçümü 31,8 ms sürüyor; turda 8 yayın birimi sorulursa bir
  alıcı yaklaşık 0,25 s'de bir konum alıyor. Aynı kanalı paylaşan her
  yeni alıcı bu süreyi uzatır." Soru böylece ölçülebilir hâle gelir.
  (Turda 12 değil 8: kısa tur kullanılabilirliği artırıyor, ADR-0085.)
- [ ] "SDR vasıtasıyla" ifadesi netleşmeli: TWR-CDMA denemesi, örnek
  düzeyinde zaman damgası veren bir SDR (ör. USRP ve UHD) ister. SDR++
  yalnız alıcıdır; SDRangel verici olsa da USB üzerinden bu zamanlamayı
  sağlamaz.
- [ ] Yeni bir cümle eklenebilir: "Pilot sahada 2,4 GHz bandının
  doluluğu SDR++ ya da SDRangel ile kaydedilecek ve simülasyondaki paket
  kaybı varsayımının yerine bu ölçüm konacaktır" (`yerkon calibrate`
  bu kayıtları artık okuyor, ADR-0083).

## Slayt 9: aldatma tespiti ve pilot

- [ ] Pilot için bir zaman çizelgesi eklenmeli (iş paketleri ve aylar).
  Şartnamenin özet bölümünde "uygulama süreci" isteniyor ve şu an yok.
- [ ] Başarı ölçütlerinin yanına kullanılabilirliğin nasıl tanımlandığı
  yazılmalı (bkz. dipnot 1 ve `BASVURU-INCELEMESI.md`, "Model
  doğruluğu").

- [ ] Prototip ve son ürün donanımı ayrı yazılmalı (proje sahibinin
  kararı, 24 Eylül). Önerilen metin:

  > "Prototipler ekibin elindeki cihazlarla gerçekleştirilecektir:
  > RAKwireless R1 (harici antenli ve antensiz), Seeed Studio SenseCAP
  > Card Tracker T1000-E, ATGM336H GPS modülü, RAK WisBlock Meshtastic
  > Starter Kit, RAK WisBlock Starter Kit (pil, OLED ve IO modülüyle) ve
  > 17 cm kırbaç anten. Son üründe sunumda verilen bileşenler (SX1280
  > tabanlı E28-2G4M12S, DWM3000, W24P-U anten ve diğerleri)
  > kullanılacaktır."

- [ ] Bu cihazların hangi radyo yongasını taşıdığı, hangi bantta çalıştığı
  ve mesafe ölçümü yapıp yapamadığı doğrulanıyor (GPT'ye verilen
  soru listesi). Cevap gelince buraya, prototipin neyi gösterip neyi
  gösteremeyeceği yazılacak: tablodaki doğruluk SX1280 ve DWM3000'in
  mesafe ölçümüne dayanıyor.

## Slayt 10: yenilikçi yön

- [ ] "Ticari karasal ..." satırındaki İngilizce kısaltma → "Ticari
  karasal konumlandırma".

## Slayt 11 ve 12: sektöre fayda

- [ ] Çevresel sürdürülebilirlik eklenmeli: "Bir yayın birimi yılda
  yaklaşık 3 kWh tüketiyor; şebeke olmayan kırsal noktalarda güneş
  paneli ve aküyle çalışıyor."

## Slayt 13 ve 14: ticarileşme

- Değişiklik yok.

## Slayt 15: fiyat tablosu

- [ ] Tablo güncellenmeli (sitenin "Maliyet" sayfası ve `bom.toml`):

  | Ürün | 1 adet | 100 adet | 1000 adet |
  |---|---|---|---|
  | Şehir içi ve kırsal yayın birimi | 1158,56 TL | 797,84 TL | 718,05 TL |
  | Kritik bölge yayın birimi | 1662,69 TL | 1212,43 TL | 1091,19 TL |
  | Yaya alıcısı | 2987,03 TL | 2379,86 TL | 2141,87 TL |
  | Kara aracı alıcısı | 3748,56 TL | 2883,67 TL | 2595,30 TL |

- [ ] Kırsal birim satırı E28-2G4M27S'den E28-2G4M12S'ye geçmeli (ya da
  frekans atlama doğrulanırsa 27S kalıp gerekçesi yazılmalı).
- [ ] Kaynak satırı: LAMBDA80-24S yerine E28-2G4M12S (LCSC),
  STM32G0B1 yerine yayın birimlerinde STM32G031 (LCSC).
- [ ] Bir cümle: "Yatırımın büyük kısmı kart değil montaj: şehir içinde
  25 birim 17951 TL, montaj 61250 TL; tünelde 9 birim 9821 TL, askı
  montajı 54000 TL."

## Slayt 16: karşılaştırma tablosu

- [ ] Üç YERKON satırı sitenin tablosuyla değiştirilmeli:

  | Satır | HPE P50 | HPE P95 | VPE P95 | Kullanılabilirlik | Alan | CAPEX | OPEX |
  |---|---|---|---|---|---|---|---|
  | Şehir içi | 2,39 | 6,65 | 72,81 | %71,68 | 5,96 km² | 13281 TL/km² | 2932 TL/km²/yıl |
  | Kırsal | 2,27 | 6,80 | 115,90 | %57,43 | 209,00 km² | 1793 TL/km² | 617 TL/km²/yıl |
  | Tünel | 0,85 | 2,97 | 6,81 | %98,57 | güzergâh | 31910 TL/km | 3357 TL/km/yıl |

  (24 Eylül koşusu: A seçeneği, doğruluğa bağlı kullanılabilirlik, şehir
  içi 600 m, turda sekiz direk, tünel 250 m.)

- [ ] TerraPoiNT ve eLoran satırlarının teknoloji sütunundaki İngilizce
  kısaltma → "Karasal konumlandırma".
- [ ] Kullanılabilirlik düştü görünüyor ama tanım değişti: artık
  yalnız 10 m hedefini karşılayan konumlar sayılıyor. Dipnot 1 bunu
  söylemeli (bkz. "Sorular").

## Slayt 17 ve 18: dipnotlar

- [ ] Dipnot 28-32 bugünkü yöntemle yeniden yazılmalı. Taslak:

  > "YERKON satırları, projenin açık kaynak simülasyonunun 24 Eylül 2026
  > koşusudur: gerçek Ankara zemini (Copernicus yükseklik modeli) ve
  > binaları (OpenStreetMap), ITU-R P.526 kırınımı, gölgelenme, her satır
  > için sekiz gölge çekilişi, sahanın çevresinden ve köşegeninden geçen
  > araç ve yaya yolculukları. Mesafeler tek tek, sabit hızlı bir Kalman
  > filtresine verilir; IMU, odometri ve harita kısıtı kullanılmamıştır.
  > SX1280'in mesafe tabanı yayımlanmış bir ölçümden (2,94 m) alınmıştır.
  > Alan, dört yayın biriminin 5 m menzil hassasiyetiyle ulaştığı
  > hücrelerin taramasıdır. CAPEX ve OPEX; kart, montaj, enerji, kira,
  > bakım ve merkezî sistem kalemlerinden toplanır. Saha ölçümü değil,
  > simülasyondur."

- [ ] Dipnot 1 (kullanılabilirlik tanımı) modelin tanımıyla aynı olmalı.

## Slayt 19: kaynakça

- [ ] Eklenecekler: Semtech AN1200.29 (SX1280 ile mesafe ölçümü), BTK
  kısa mesafe cihazları teknik ölçütleri ve TS EN 300 328, NTSB ön
  raporu (New Mexico), Karadeniz olayı için kullanılan kaynak.

## Slayt 20: kapanış

- [ ] Sayfa sınırı için kaldırılabilir.

## Sorular (cevaplandıkça buraya)

- Kullanılabilirlik hangi tanımla verilsin? **Cevap: doğruluğa bağlı.**
  Bir tur, filtrenin kendi yatay belirsizliği 5,78 m'yi (HPE P95 < 10 m
  hedefinden) geçmiyorsa konum sayılıyor (ADR-0084). Dipnot 1 için metin:
  "YERKON kullanılabilirliği, denenen konum turlarından, alıcının kendi
  tahminine göre yatay hatası %95 olasılıkla 10 m'nin altında kalan bir
  konum üretenlerin oranıdır."
- Görüş dışı (çok yollu) yanlılık modele girsin mi? **Cevap: A, yanlılık
  yok** (24 Eylül). Tablo bu hâlle yeniden yayımlandı. B ve C'nin
  sayıları ADR-0084'te duruyor; pilot ölçümü gelince yeniden bakılacak.
- Şehir içi direk aralığı? **Cevap: 600 m** (500 m idi). 25 direk,
  toplam maliyet %30,6 düşük (`MALIYET-KARSILASTIRMASI.md`).
- SX1280'in SF10 ve 1625 kHz'deki duyarlılığı: model −125,9 dBm
  varsayıyor; veri sayfasının tablosu gerekli. Yayımlanan sayılar buna çok
  bağlı (bkz. `BASVURU-INCELEMESI.md`, "Model doğruluğu").

## Slayt 16'yı etkileyen model değişiklikleri

- Simülatörün sekmeleri tablonun satırlarından farklı değerlerle
  koşuyordu (ölçüm hatası, paket kaybı, kabul eşiği, turdaki birim sayısı,
  tünelde yöntem, tohum, tur, kamyon anteni). Düzeltildi (ADR-0084).
- Kullanılabilirlik tanımı değişti; tablo 24 Eylül'de A seçeneğiyle
  yeniden yayımlandı. Slayt 16 yukarıdaki sayılarla güncellenmeli.
- Şehir içi 600 m (500 idi), turda sekiz direk (12 idi, ADR-0085), tünel
  250 m (225 idi).
