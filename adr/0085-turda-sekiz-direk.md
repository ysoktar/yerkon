# ADR-0085: turda sekiz direk, üç satırda da

## Durum

Kabul edildi. ADR-0072'nin şehir içi ve ADR-0022'nin kırsal için
bıraktığı on ikinin yerine geçer.

## Bağlam

Bir birim her turda en çok `<satır>.anchors_per_round` direği yokluyor.
Şehir içi ve kırsal on iki, tünel sekizdi. On iki, kullanılabilirlik
"turda en az bir mesafe varsa konum var" diye sayılırken ölçülmüştü: daha
çok direk yoklamak daha çok konum getiriyordu.

ADR-0084 kullanılabilirliği doğruluğa bağladı: filtrenin yatay
belirsizliği 5,78 m'yi geçen tur konum sayılmıyor. Bundan sonra tam
takımda kırsal turun on direğinin sekize karşı kazandığını söyleyen
sınama dört tohumun dördünde kırıldı.

## Ölçüm

Tam çözünürlük, tek gölge çekilişi, satırın kendi senaryosu, yalnızca tur
boyu değişiyor.

Kırsal (3000 m, 49 direk):

| Tohum | 6 | 8 | 10 | 12 |
|---|---|---|---|---|
| 202 | %58,13 | %58,15 | %57,64 | %55,89 |
| 404 | %57,41 | %57,66 | %57,34 | %56,55 |
| 606 | %57,14 | %58,62 | %57,33 | %55,82 |
| 808 | %57,07 | %58,66 | %57,87 | %55,82 |

Şehir içi (600 m, 25 direk):

| Tohum | 8 | 10 | 12 |
|---|---|---|---|
| 101 | %72,67 | %72,06 | %68,66 |
| 303 | %71,99 | %72,69 | %69,30 |
| 505 | %73,68 | %73,49 | %69,81 |
| 707 | %72,54 | %70,73 | %69,94 |

Sekiz on ikiyi iki satırda da dört tohumun dördünde geçiyor: şehir
içinde ortalama +3,3 puan, kırsalda +2,3. Tohumlar arası saçılım 0,4
puan kadar. HPE P95 tohum saçılımı içinde kalıyor (şehir içi 6,76 ve 6,70 m, kırsal 7,08 ve
6,92 m; sekiz ve on iki sırasıyla).

## Neden

Bir SX1280 alışverişi 31,8 ms. On iki direkli tur sekiz direkliden yarı
yarıya uzun, yani saniyede üçte bir daha az tur. Filtrenin belirsizliği
iki tur arasında aracın hareketiyle büyüyor. Sık gelen tur onu çıtanın
altında daha sık yakalıyor. Fazladan dört mesafenin getirdiği, bu
kaybı karşılamıyor: gerçek rölyefte yoklananın bir kısmı zaten cevap
vermiyor ve cevap vermeyen direğin payı da turun süresine ekleniyor.

## Karar

Şehir içi ve kırsal `anchors_per_round` sekiz. Üç satır da sekiz.

## Sonuçlar

- Kullanılabilirlik bedava artıyor: direk, montaj, işletme aynı.
- Yayın biriminin kanalı daha kısa süre meşgul; aynı bantta daha çok
  birim sığar.
- `yerkon solve` şehir içinde hâlâ 8 ile 12 arasında arıyor; çıta
  değişirse sıralama yeniden dönebilir, sınama bunu yakalar.

## Sonradan (ADR-0091)

Direkte ve araçta anten ve SX1280'in resmî duyarlılığıyla kırsalda
sekiz ile on iki berabere: dört tohumda fark -0,1 puan, tohum saçılımı
0,35 puan. Sekiz kalıyor, çünkü aynı kullanılabilirliği havayı üçte bir
daha az meşgul ederek veriyor.
