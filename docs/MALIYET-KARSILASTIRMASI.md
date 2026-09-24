# Maliyet karşılaştırması: görüş dışı seçenekleri ve direk aralığı

25 Eylül 2026. Amaç: km² ve km başına maliyeti düşürmek, doğruluğu ve
kullanılabilirliği kaybetmeden.

Sayılar kaba okuma (profil kaba, iki gölge çekilişi): karşılaştırma için,
yayımlamak için değil. Kullanılabilirlik yeni tanımla (ADR-0084): filtrenin
yatay belirsizliği 5,78 m'yi geçmeyen turlar.

- **A**: görüş dışı yanlılık yok.
- **B**: SX1280 için ortalama 5 m, DWM3000 için 0,5 m, filtrede 3 sigma kapısı.
- **C**: B ile aynı, SX1280 için 15 m.

Maliyet A, B ve C'de aynı: görüş dışı yanlılık doğruluğu değiştiriyor,
kaç direk ve nerede olduğunu değil.

## Toplam, km² ve km başına (tam alan taraması)

Alan tam çözünürlükte, ilk üç gölge çekilişinin ortalaması; tablonun
kendi yöntemi. Güzergâh km'si birimlerin sürdüğü yol. On yıl: CAPEX artı
on yıllık OPEX, faizsiz. A, B ve C'de aynı.

| Satır | Direk | Alan | Güzergâh | CAPEX | OPEX/yıl | On yıl | CAPEX/km² | OPEX/km²/yıl | CAPEX/km | OPEX/km/yıl |
|---|---|---|---|---|---|---|---|---|---|---|
| Şehir içi, 500 m (eski) | 36 | 6,68 km² | 12,82 km | 114050 | 25177 | 365820 | 17065 | 3767 | 8899 | 1965 |
| **Şehir içi, 600 m (yeni)** | 25 | 5,96 km² | 12,82 km | **79201** | **17035** | **249551** | **13281** | **2857** | **6180** | **1329** |
| Kırsal, 3000 m | 49 | 209,00 km² | 86,40 km | 374754 | 123345 | 1608204 | 1793 | 590 | 4337 | 1428 |
| Tünel, 250 m | 9 | yalnız tüp | 2,00 km | 63821 | 6468 | 128501 | yok | yok | 31910 | 3234 |

Tutarlar TL. OPEX 24 Eylül akşamından beri resmî harcırah ve amortisman
değerleriyle (ADR-0089): kırsalda ve tünelde bakım ekibi şehir dışına
giderse harcırah eklenir; bakımı yerel bir teknik firma yaptığı için
kırsalda ve tünelde sıfır (ADR-0090). Şehir içinde 600 m, toplamı ve güzergâh km'si başına
maliyeti %30,6 düşürüyor (11 direk eksik). km² başına düşüş daha küçük,
%22,2, çünkü seyrek ızgaranın kapsadığı alan da 6,68'den 5,96 km²'ye
iniyor.

## Yerel bakım ekibi (uygulandı, 24 Eylül, ADR-0090)

Bugünkü model: ekip Ankara merkezde, Polatlı ve Kızılcahamam'a her
ziyarette iki kişi için kişi başı 850 TL harcırah (ADR-0089). Yerel ekip:
aynı ziyaretler, harcırah yok.

| Satır | Ekip | OPEX/yıl | OPEX | Harcırah | On yıl toplam |
|---|---|---|---|---|---|
| Kırsal | Ankara'dan | 156665 | 750 TL/km² | 33320 | 1941404 |
| Kırsal | yerel | 123345 | 590 TL/km² | 0 | 1608204 |
| Tünel | Ankara'dan | 9528 | 4764 TL/km | 3060 | 159105 |
| Tünel | yerel | 6468 | 3234 TL/km | 0 | 128505 |

Değişen yalnız harcırah kalemi: kırsalda OPEX %21,3, tünelde %32,1
düşüyor. CAPEX, doğruluk ve kullanılabilirlik değişmiyor.

Modelin göremediği: ziyaret bedeli (1800 TL, varsayım) mesafeye bağlı
değil. Ankara'dan 70-80 km gidip gelmenin yakıtı ve yolda geçen iş
saati bu bedelin içinde ayrı sayılmıyor, yani yerel ekibin gerçek
kazancı tablodakinden biraz daha büyük olabilir. Karşılığında yerel ekip
bir anlaşma demek: Polatlı'da elektrik dağıtım şirketinin ekipleri
(direkler zaten onların), tünelde Karayolları'nın tünel bakım ekibi
(tünele giriş ve şerit kapatma zaten onların işi). Arıza anında ne kadar
sürede gidecekleri anlaşmaya bağlı.

## Şehir içi (Kızılay)

| Aralık | Direk | CAPEX TL/km² | OPEX TL/km²/yıl | A: P95, kull. | B: P95, kull. | C: P95, kull. |
|---|---|---|---|---|---|---|
| 250 m | 144 | 51201 | 11303 | 5,94 m, %85,16 | 10,73 m, %81,82 | 42,10 m, %69,36 |
| 300 m | 100 | 35899 | 7925 | 5,76 m, %81,72 | 11,86 m, %77,07 | 35,33 m, %63,28 |
| 400 m | 60 | 22888 | 5053 | 5,80 m, %84,04 | 11,75 m, %79,43 | 36,67 m, %66,40 |
| 500 m (eski) | 36 | 16589 | 3662 | 6,71 m, %78,82 | 11,55 m, %75,51 | 29,03 m, %57,45 |
| **600 m (seçilen)** | 25 | 12713 | 2806 | 6,74 m, %72,61 | 12,85 m, %68,85 | 31,68 m, %53,44 |
| 700 m | 23 | 12728 | 2810 | 7,33 m, %57,99 | 12,87 m, %54,17 | 41,77 m, %33,34 |
| 800 m | 16 | 10762 | 2376 | 7,36 m, %61,88 | 13,80 m, %58,66 | 30,61 m, %34,84 |

## Kırsal (Polatlı)

| Aralık | Direk | CAPEX TL/km² | OPEX TL/km²/yıl | A: P95, kull. | B: P95, kull. | C: P95, kull. |
|---|---|---|---|---|---|---|
| 1500 m | 189 | 3484 | 1199 | 5,32 m, %76,89 | 9,99 m, %75,31 | 25,41 m, %65,34 |
| 2000 m | 105 | 2354 | 810 | 5,62 m, %67,93 | 10,11 m, %65,37 | 20,76 m, %59,82 |
| 2500 m | 68 | 1951 | 671 | 6,54 m, %65,10 | 10,66 m, %61,13 | 22,40 m, %53,69 |
| **3000 m (bugün)** | 49 | 1509 | 519 | 6,55 m, %63,00 | 11,15 m, %60,49 | 24,57 m, %53,07 |
| 3500 m | 36 | 2203 | 758 | 6,87 m, %41,97 | 12,07 m, %39,47 | 22,05 m, %33,65 |
| 4000 m | 28 | 1724 | 593 | 7,59 m, %20,81 | 12,39 m, %18,22 | 21,75 m, %15,53 |

## Tünel (Kızılcahamam, güzergâh km başına)

Tam okuma, sekiz gölge çekilişi, turda sekiz direk, A seçeneği.

| Aralık | Askı | CAPEX TL/km | OPEX TL/km/yıl | HPE P50 | HPE P95 | Kullanılabilirlik |
|---|---|---|---|---|---|---|
| 225 m (eski) | 9 | 31910 | 3357 | 0,79 m | 3,21 m | %98,25 |
| **250 m (yeni)** | 9 | 31910 | 3357 | 0,85 m | 2,97 m | %98,57 |
| 275 m | 8 | 28365 | 2984 | 1,04 m | 3,80 m | %91,21 |
| 300 m | 7 | 24819 | 2611 | 0,80 m | 3,68 m | %88,29 |

2 km'lik tünelde 225 ve 250 m aynı sayıda askı veriyor. Uzun bir tünelde
250 m kilometre başına 4,4 yerine 4,0 askı demek: aynı doğrulukla %10
daha ucuz. Tünel CAPEX'inin %85'i askı montajı (askı başına 6000 TL,
varsayım); birim yalnızca 1091 TL. En büyük kaldıraç aralık değil montaj.

## Ne gösteriyor

1. **Direk sıklaştırmak görüş dışı hatayı düzeltmiyor.** B'de şehir içi
   P95, dört kat direkle bile 11-12 m'de kalıyor; C'de hiç iyileşmiyor.
   Hata engellenmiş her bağlantının üstünde; daha fazla verici onu
   silmiyor. B ve C'nin maliyeti A'yla aynı; bedeli doğrulukta ödeniyor.
2. **Şehir içinde 600 m, km² maliyetini %23 düşürüyor.** 25 direkle
   CAPEX 16589'dan 12713 TL/km²'ye, OPEX 3662'den 2806'ya iniyor. A'da P95
   hâlâ hedefin altında (6,74 m); kullanılabilirlik 6 puan düşüyor
   (%78,82'den %72,61'e). 700 ve 800 m'de kullanılabilirlik çöküyor.
3. **Kırsalda 3000 m zaten en ucuzu.** Seyreltmek alanı küçültüyor
   (209 km²'den yaklaşık 125 km²'ye), km² maliyetini artırıyor ve
   kullanılabilirliği çökertiyor. Kırsal maliyet başka kalemlerden düşer
   (aşağıda).
4. **Tünelde 225 m gerekli.** 300 m km maliyetini %22 düşürüyor ama
   kullanılabilirliği %98'den %76'ya indiriyor. DWM3000'in bağlantısı
   yaklaşık 375 m'de kesin bir duvara çarpıyor.

## Simülasyon gerektirmeyen maliyet kalemleri

Aynı yerleşim, yalnız maliyet varsayımı değişince (23 Eylül tablosunun
alanlarıyla):

| Kaldıraç | Şehir içi CAPEX / OPEX (TL/km²) | Kırsal CAPEX / OPEX (TL/km²) | Tünel CAPEX / OPEX (TL/km) |
|---|---|---|---|
| Bugün | 17065 / 3767 | 1793 / 617 | 31910 / 3357 |
| Montaj yarıya (direk 1225, dağıtım direği 2300, askı 3000 TL) | **10466** / 3767 | **1254** / 617 | **18410** / 3357 |
| Bakım ziyareti yılda 0,2'den 0,1'e | 17065 / **2798** | 1793 / 575 | 31910 / **2547** |
| Dağıtım direği kirası 1200'den 0 TL'ye | 17065 / 3767 | 1793 / **335** | 31910 / 3357 |
| Merkezî sistem 1000 değil 10000 birimle paylaşılır | 17065 / **2604** | 1793 / 566 | 31910 / **2385** |
| Kırsal direklerin yarısı şebekeden (güneş paneli yok) | 17065 / 3767 | **1526** / 533 | 31910 / 3357 |

Hepsi varsayım; her biri bir teklif ya da bir anlaşmayla gerçeğe döner.

## Öneri: km² ve km maliyetini düşürmek için

- **Şehir içi:** 600 m aralık ve montajın belediyenin aydınlatma bakım
  turlarına eklenmesi. İkisi birlikte CAPEX'i yaklaşık 17065'ten 8000
  TL/km² civarına indirir (montaj kalemi aralıkla birlikte küçülür).
  Yöneylem yerleşimi (ADR-0081) aynı hizmeti yaklaşık beşte bir daha
  ucuza veriyordu; 600 m ile birleştirilmesi denenmeli.
- **Kırsal:** aralık aynı kalsın. Direk kirası için dağıtım şirketiyle
  kamu yararı anlaşması (OPEX yarıya yakın), şebekesi olan noktalara
  öncelik (yöneylem yerleşimi bunu maliyetle birlikte seçiyor) ve montaj.
- **Tünel:** aralık aynı kalsın (225 m). Askı montajı tünelin kendi bakım
  kapanışlarında yapılırsa km maliyeti yaklaşık %42 düşer.
- **Hepsi:** bakımı uzaktan izlemeyle yarıya indirmek ve merkezî sistemi
  ulusal ölçekte paylaştırmak birlikte OPEX'i şehir içinde 3767'den
  yaklaşık 1635 TL/km²'ye, tünelde 3357'den yaklaşık 1575 TL/km'ye
  indirir. Kırsalda etkisi küçük (617'den yaklaşık 524'e), çünkü orada
  işletmenin büyük kalemi direk kirası.

Görüş dışı seçeneğin kararı maliyeti değiştirmez; hangi doğruluğun
yayımlanacağını belirler.
