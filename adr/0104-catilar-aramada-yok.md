# ADR-0104: çatılar aramada yok; yükseklikler 12 m ve 10 m

## Durum

Kabul edildi (proje sahibinin kararı, 28 Eylül 2026: çatılar kiralı
kalsın ama mümkün olduğunca kullanılmasın; aydınlatma direği 12 m,
dağıtım direğinde birim 10 m kalsın).

## Karar

- Çatı bina sahibinden kiralanıyor (yılda 1200 TL, varsayım); kamu
  protokolü özel binaya uzanmıyor. Yerleşim araması artık çatıları aday
  saymıyor (`placement.OFFER_ROOFS`); simülatörde ve testlerde istenirse
  açılabiliyor.
- Yükseklikler ADR-0103'teki taramalardan sonra değişmedi: aydınlatma
  direği 12 m, dağıtım direğinde birim 10 m.

## Sonuç

Kırsal arama çatısız yeniden koşuldu: 52 birim, 47 elektrik dağıtım
direği ve 5 aydınlatma direği.

| Kırsal | HPE P50 | P95 | VPE P95 | Kullanılabilirlik | Alan | CAPEX | OPEX |
|---|---|---|---|---|---|---|---|
| 2 çatıyla | 2,16 | 8,02 | 4,95 | %94,85 | 354,83 km² | 1107 | 329 |
| Çatısız | 2,16 | 8,16 | 4,96 | %94,52 | 354,00 km² | 1125 | 328 |

Fark küçük: P95'te 0,14 m, kurulumda km² başına 18 TL.

Dağıtım direğinde birimin yüksekliği aynı çatısız yerleşimle yeniden
tarandı:

| Birim | HPE P95 | Kullanılabilirlik | Alan km² | CAPEX TL/km² |
|---|---|---|---|---|
| 6 m | 8,58 | %91,11 | 327,50 | 1216 |
| 8 m | 8,15 | %93,17 | 344,58 | 1156 |
| 10 m | 8,16 | %94,52 | 354,00 | 1125 |

10 m hem en geniş alanı hem en düşük maliyeti veriyor; 8 m'nin P95'i
aynı.

## Site denetimi (28 Eylül 2026)

Sitenin kendi içindeki tutarsızlıklar tek tek düzeltildi:

- Sistem: saat kayması cümlesi 0,0793 ppm'i kaymanın kendisi ve
  projedeki tek ölçüm diye anıyordu. O değer düzeltme sonrası kalan
  kayma (MATLAB kestirici koşusu) ve ayarlarda ölçüm türünde sekiz değer
  var.
- Sistem: Polatlı "düz" deniyordu; Simülasyon sayfası 486 m iniş çıkış
  veriyor. "Seyrek yapılı bozkır" oldu.
- Sonuçlar: "sinyal konum alınabilen zeminin iki katına ulaşıyor"
  yanlıştı (437,75 / 354,00 = 1,24). Oran kaldırıldı.
- Sonuçlar ve CLI: hızlı okuma "8,6 puan iyi" ve "kötü görünen gerçekten
  kötüdür" diyordu. Bugünkü yerleşimde kırsal fark 2,2 puan, tünelin
  P95'i hızlıda 7,58 m ile kötü çıkıyor: gölgelemenin tek çekilişi iki
  yöne de sapabiliyor.
- Simülasyon: tünelde kusursuz etütle ortanca "0,24 m, yedi katından
  fazla" deniyordu (ADR-0019, eski tünel modeli). Bugün 0,12 m, P95
  0,46 m; tablodaki ortanca bunun yaklaşık beş katı.
- Simülasyon ve simülatör: aday listesi çatıları sayıyor, kırsaldaki
  dağıtım direklerini saymıyordu.
- Maliyet: parça tablosunda "Rapordaki karşılığı" sütunu kaymıştı
  (antenin yanında eski mikrodenetleyici). `Board.swapped` sırayla
  eşliyor; yayın biriminin parça sırası düzeltildi ve bir sınama eklendi.
- Maliyet: fiyat tarihi 23-25 Eylül yazıyordu, parçalar 28 Eylül'e kadar
  okundu. Kademesi doğrulanmayan aynı parçanın ürüne göre farklı 1000
  adet fiyatı aldığı yazıldı.
- Maliyet: harcırah her satırda sıfır ama nedeni (ekip görev yeri dışına
  çıkmıyor) listede yoktu; üç satırın ayarı eklendi. Işıklı kavşak
  aralığı yalnız ızgara yerleşiminde işliyor, listeden çıktı.
- Maliyet: çatı kirası "dağıtım direği kirasıyla aynı" diyordu, o kira
  artık sıfır. Çatıdaki ekip gününün kaynağı sepetli aracı anıyordu.
  Kırsal ekip notu "direk kirası anlaşması" diyordu, kamu protokolü oldu.
- Mevzuat: "burada yazan her sınır modelde" deniyordu, prototip frekans
  kuralları modelde yok.
- Fayda: alıcı adları Sistem sayfasıyla aynı oldu.
