# ADR-0105: fiyatlar satıcı kademelerinden; raporun fiyatları kullanılmıyor

## Durum

Kabul edildi (proje sahibinin kararı, 28 Eylül 2026: başvuru raporundaki
fiyatlar yanlış; sitede gösterilmesin, sunumda sitenin 1, 100 ve 1000
adet tablosu kullanılsın; 1000 adet bulunamazsa 1 ve 100 yeter). ADR-0079,
ADR-0093 ve ADR-0102'nin fiyat yönteminin, ADR-0103'ün "raporun kalanı"
satırının yerine geçer.

## Bağlam

Malzeme listesi raporun 14. sayfasındaki iki toplamdan yola çıkıyordu:
ana parçalar çıkarılınca kalan "diğer" satırı, raporun 1'den 100'e
indirim oranı ve 1000 adet için %90. Kademesi doğrulanmayan her parça bu
oranla indiriliyordu; oran ürüne göre değiştiği için aynı kutu ürüne göre
farklı bir 1000 adet fiyatı alıyordu. Rapor fiyatları yanlış olunca bu
oranların da dayanağı kalmadı.

Kademeler yeniden okununca bir hata daha çıktı: bazı parçaların "1 adet"
fiyatı aslında büyük bir kademenin fiyatıydı. STM32G031K8T6 için bom 1,93 $
yazıyordu; LCSC'de 1 adet 3,11 $, 1,94 $ 250 adet kademesi.

## Karar

- Her parça satıcısının kademe tablosunu taşıyor (`ladder`: en küçük adet
  ve o adetten başlayan birim fiyat). LCSC parçalarında tablonun tamamı,
  28 Eylül 2026'da LCSC'nin ürün arayüzünden okundu.
- Bir ürünün fiyatı, her parçanın o kadar kart için alınan adetteki
  fiyatlarının toplamı. Bir kartta iki klemens varsa 100 kart 200 klemens
  alır.
- Satıcının yayımlamadığı kademede indirim varsayılmıyor; bilinen son
  kademe geçerli. Kutular (Gainta, 100+ teklifle), baskılı devre ve pil her
  adette tek adet fiyatıyla giriyor.
- Dizginin kurulum, şablon ve parça yükleme bedeli siparişe bir kez
  ödeniyor; karta düşen payı JLCPCB'nin kendi formülüyle adetle küçülüyor.
- Raporun iki toplamı, "diğer" kalanı, `was` listesi ve yalnız rapor
  karşılığı olan parçalar (LAMBDA80-24S, W24P-U, E28-2G4M27S, DigiKey
  DWM3000, NHD-2.8, TL-ANT2412D, HGV-2409U, LMR-200) bom'dan çıktı.
- Sitede rapor sütunları yok: ürün tablosu 1, 100 ve 1000 adet; parça
  tablosu her parçayı üç kademede gösteriyor.
- Sunumun fiyat tablosu şablondaki iki sütunla 1 ve 100 adeti gösteriyor;
  1000 adet fiyatları hemen altındaki fiyat kapsamı notunda.

## Sonuç

| Ürün | 1 adet | 100 adet | 1000 adet | Önceki 1000 adet |
|---|---|---|---|---|
| Şehir içi ve kırsal yayın birimi | 2049,79 | 1531,32 | 1381,83 | 1288,87 |
| Kritik bölge yayın birimi | 2276,48 | 1755,47 | 1680,26 | 1595,56 |
| Yaya alıcısı | 3082,55 | 2586,76 | 2309,77 | 2232,52 |
| Kara aracı alıcısı | 4528,63 | 4069,88 | 3309,05 | 3218,03 |

Fiyatlar yükseldi, çünkü artık hiçbir parça dayanaksız bir oranla
indirilmiyor ve STM32'nin tek adet fiyatı doğru okundu.

Tablo yeniden yayımlandı. Doğruluk, kullanılabilirlik ve alan değişmedi;
yalnız maliyet sütunları:

| Satır | CAPEX önce | CAPEX şimdi | OPEX önce | OPEX şimdi |
|---|---|---|---|---|
| Şehir içi (TL/km²) | 8844 | 9061 | 1919 | 1940 |
| Kırsal (TL/km²) | 1125 | 1138 | 328 | 330 |
| Tünel (TL/km) | 106855 | 108294 | 21963 | 22107 |

Çatı kirası da aynı gün yayımlanmış en yakın bedele çekildi: İBB'nin
2025 tarifesinde küçük bir telsiz cihazı için yıllık 24500 TL. Çatılar
aramaya girmediği için tabloya etkisi yok (ADR-0104).
