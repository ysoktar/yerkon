# ADR-0090: bakımı yerel bir teknik firma yapıyor

## Durum

Kabul edildi (proje sahibinin kararı, 24 Eylül 2026). ADR-0089'daki
"ekip Ankara'dan gidiyor" varsayımının yerine geçer; harcırah hesabı
modelde duruyor, yalnız bu iki satır için sıfır.

## Bağlam

ADR-0089 ile bakım ekibi Ankara merkezde varsayılmıştı. Kırsal
(Polatlı, yaklaşık 80 km) ve tünel (Kızılcahamam, yaklaşık 70 km) için
her ziyarette iki kişiye kişi başı 850 TL harcırah ödeniyordu: kırsalda
yılda 33320 TL, tünelde 3060 TL.

## Karar

Bakımı sahaya yakın yerel bir teknik firma yapıyor. Ekip şehir dışına
çıkmadığı için harcırah yok (`rural.crew_travels` = 0,
`tunnel.crew_travels` = 0).

Elektrik dağıtım şirketinin kendi ekiplerine dayanılmadı: şirket bu işi
yapmak istemeyebilir. Yerel bir firma bu yüzden daha sağlam bir varsayım.

Ziyaret bedeli değişmedi (1800 TL, varsayım): yerel firmanın bir
ziyaret için isteyeceği ücret. Bir teklifle gerçeğe dönmeli.

## Sonuçlar

| Satır | OPEX önce (TL/yıl) | OPEX şimdi | Birim başına |
|---|---|---|---|
| Kırsal | 156665 | 123345 | 750 → 590 TL/km² |
| Tünel | 9528 | 6468 | 4764 → 3234 TL/km |

- CAPEX, doğruluk ve kullanılabilirlik değişmiyor.
- Yerel firma yine iki izne bağlı. Kırsalda direkler dağıtım şirketinin:
  direğe çıkmak için onun izni ve koşulları gerekebilir (yetkili
  personel, enerji hattı yakınında çalışma). Bu, direk kirası
  anlaşmasının içinde çözülmeli. Tünelde giriş ve şerit kapatma
  Karayolları'nın izniyle; ziyaretler onların bakım kapanışlarına denk
  getirilebilir.
- Firmanın arızaya ne kadar sürede gideceği sözleşmeye yazılmalı.
