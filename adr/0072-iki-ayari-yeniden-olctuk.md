# ADR-0072: iki yerleşim ayarını yeniden ölçtük

## Durum

Kabul edildi. ADR-0022'nin şehir içi ve tünel için verdiği kararın
yerine geçer; kırsal için verdiği karar yerinde duruyor.

## Bağlam

ADR-0022 turun kaç direği yoklayacağına karar verirken kırsalı üç
tohumda ölçtü ve sekizden on ikiye çıkardı. Aynı ADR şehir içini ve
tüneli sekizde bıraktı, ama **bunu ölçmedi**; gerekçe yazılıydı:

> bir şehirde 500 m ızgarada ve bir tünelde 150 m aralıkta yoklananın
> neredeyse hepsi cevap veriyor ve daha uzun bir tur hiçbir şey satın
> almaz, güncelleme hızına mal olur.

Makul bir gerekçe. Ölçülmemiş bir gerekçe.

Araya ADR-0053 girdi: kırınım hesabı en kötü tek noktadan bütün profile
geçti ve ortanca kayıp 24,5 dB'den 38,9 dB'ye çıktı. Tablo aşağı indi.
ADR-0022'nin bütün sayıları o günün yayılım modeline aitti, ve o modelde
verilmiş "yoklananın neredeyse hepsi cevap veriyor" yargısı yeni modelde
denenmemişti.

`yerkon solve` tam bu iş için yazılmıştı ve ADR-0053'ten beri bu
ayarlara doğrultulmamıştı.

## Ölçüm

Hepsi tam çözünürlükte (sekiz gölge çekilişi havuzlanmış), üç tohumda,
donanım ve sermaye sabit.

**Şehir içi, tur başına direk.** Aynı 36 direk, aynı 157 179 TL.

| tohum | 8 | 12 | 16 |
|---|---|---|---|
| 1 | %78,86 | %83,38 | %84,72 |
| 2 | %79,20 | %82,74 | %84,38 |
| 3 | %82,26 | %85,61 | %83,53 |

8 → 12 üç tohumda da pozitif: +4,52, +3,54, +3,35. Ortalama +3,80.
12 → 16 ise +1,34, +1,64, −2,08 — üçüncü tohumda kaybediyor, yani
ADR-0022'nin kırsalda on ikinin üstünde gördüğü gürültünün aynısı.

Ortanca hata 2,49 m'den 2,59 m'ye çıkıyor. ADR-0022 kırsalda aynı takası
+0,4 m'ye kabul etmişti.

**Tünel, askı aralığı.**

| aralık | askı | sermaye | ortanca hata (3 tohum) | kullanılabilirlik |
|---|---|---|---|---|
| 150 m | 14 | 106 882 TL | 1,86 / 1,91 / 1,81 | %100 |
| 175 m | 12 | 91 613 TL | 1,18 / 1,46 / 1,06 | %100 |
| 200 m | 11 | 83 979 TL | 1,05 / 1,07 / 1,13 | %100 / %99,4 / %99,4 |
| **225 m** | **9** | **68 710 TL** | **0,80 / 0,96 / 0,61** | %99,0 / %100 / %98,9 |
| 250 m | 9 | 68 710 TL | 0,77 / 1,20 / 0,81 | %100 / %98,2 / %99,1 |
| 300 m | 7 | 53 441 TL | 0,62 | %82,7 |

Eski not "aralığı maliyet değil geometri belirler" diyordu. İlke doğru,
sayı yanlıştı: bir koridorda direkleri sıkıştırmak hepsini neredeyse
aynı noktaya toplar ve tabanı kısaltır, yani geometri **kötüleşir**.
225 m hem üçte bir ucuz hem iki kat hassas. 300 m'de bağlantılar toptan
kopuyor, yani 225 m sınırın hemen berisi.

**Kırsal, tur başına direk.** Aynı 28 direk, aynı 2 676 315 TL.

| tohum | 12 | 16 | 20 |
|---|---|---|---|
| 1 | %40,18 | %41,85 | %44,15 |
| 2 | %41,54 | %45,01 | %45,91 |
| 3 | %43,19 | %47,45 | %46,08 |

12 → 16 üç tohumda da pozitif, ortalama +3,13. Ama ortanca hatayı
3,79 m'den 4,34 m'ye götürüyor.

## Karar

**Şehir içi: 8 → 12.** Sermaye değişmiyor, kullanılabilirlik dört puan
artıyor, ortanca hata 0,10 m kötüleşiyor.

**Tünel: 150 m → 225 m.** 14 askı yerine 9. Sermaye üçte bir aşağı,
ortanca hata yarıdan fazla aşağı, kullanılabilirlik %100'den yaklaşık
%99,3'e. Küçük kesintinin kabul edilebilir olduğunu proje sahibi
söyledi.

**Kırsal: 12'de kalıyor.** Gerekçe ataletsizlik değil, ölçümün kendisi:
kazanç gerçek ama bedeli doğruluk, ve kırsal satırın doğruluğu zaten
bloğun en kötüsü. %45 kullanılabilirlik %42 kadar kötü bir sayı;
22,72 m'lik hatayı daha da büyütmek karşılığında dört puan almak bir
kazanç değil, bir takas.

## Sonuçlar

Yayımlanan tabloda tünel satırı ortanca hatada 1,84 m'den 0,78 m'ye,
sermayede üçte bir aşağı indi. Şehir içi kullanılabilirlik %79,88'den
%83,98'e çıktı, yatay hata 8,19 m'den 8,84 m'ye. Kırsal satır **bit
düzeyinde aynı çıktı**, ki bu değişmemesi gereken hiçbir şeyin
değişmediğinin kontrolü.

Taşınmaya değer genelleme: **yazılmış bir gerekçe ölçülmüş bir gerekçe
değildir.** ADR-0022'nin şehir içi cümlesi makuldü, tutarlıydı ve
yanlıştı; onu yanlış yapan da modelin altından değişmesiydi. Bir modeli
değiştiren her karar, o modele dayanan kararları yeniden açar.

## Yapılmayanlar

**Kırsalın %41,83'ü için yapılabilecek bir şey bulunamadı.** Çözücü 36
düzen denedi; direk sayısını dört katına çıkarmak bile %80'de (hızlı
okumada) duvara tosluyor. Sınırlayıcı olan mesafe değil arazi, ki
ADR-0022 bunu zaten ölçmüştü: düşen kırsal bağlantıların %0,0'ı mesafe
yüzünden düşüyor, %46,1'ini zemin öldürüyor. Bunu aşmanın yolu daha
güçlü telsiz ya da daha iyi anten, ve raporun malzeme listesi ikisini de
yasaklıyor.

**Ölçüm toleransı denendi ve hiçbir şey değiştirmedi**, dördüncü haneye
kadar. `defaults.toml` bunu zaten yazmıştı; ölçüm o notu doğruladı.
