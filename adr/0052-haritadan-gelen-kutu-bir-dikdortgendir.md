# ADR-0052: haritadan gelen kutu bir dikdörtgendir, kol bir sayı tutar

## Durum

Kabul edildi.

## Bağlam

Haritada serbestçe bir kutu çizdim, "Al"a bastım. Panel şunu gösterdi:

> **Haritadan: 19,31 × 12,33 km**
>
> **Kutunun boyu** — 3 km — [sürgü solda] — [3]
>
> *3 × 3 km, 10.000 ızgara noktası.*

Üç satırın üçü de aynı şeyi tarif ediyor ve ikisi yanlış. Getirilecek
kutu 19,31 × 12,33 km; kol 3 km diyor; altındaki satır 10.000 nokta
diyor, oysa gerçek kutu **264.273** nokta — dakikalarla saniyeler
arasındaki fark, ve o satır tam olarak bunu söylemek için var.

Kod aslında hangisinin kazandığını biliyordu — köşeler telde boyu
yener — ve kola dokunmanın haritadaki kutuyu bıraktığı da yazılıydı.
Eksik olan, **kutu yürürlükteyken kolun bunu söylememesiydi.**

Bu, bu projede dördüncü kez: gri bir sürgünün yanında canlı bir kutu
(ADR-0036), sınırlanmış bir sürgünün yanında her sayıyı kabul eden bir
kutu (ADR-0048), hesaplanırken eski sayıyı gösteren bir panel
(ADR-0050), ve şimdi yürürlükte olmayan bir kutuyu tarif eden bir kol.

Bir de ikinci, daha sessiz hâli: nokta sayısı iki yerde söyleniyordu —
harita çubuğunda kutu sürüklenirken, panelde kolun altında — ve **iki
ayrı yerde hesaplanıyordu.** Aynı kutu haritada 9.900, panelde 10.000
okunuyordu.

## Karar

**Haritadan bir kutu geldiğinde kol çekilir.** Sürgü ve sayı kutusu
kapanır, etiket grileşir, çıktısı `—` olur. Bir dikdörtgeni tek sayıyla
tarif edemez; yanlış bir sayı söylemektense hiçbir şey söylemez
(ADR-0036).

**Altındaki satır gerçek kutunun maliyetini verir.** 174.768 nokta,
haritanın kendi çubuğuyla birebir aynı sayı.

**Geri dönüş yolu görünür.** Eskiden kola dokunmak kutuyu bırakıyordu,
ama kol artık kapalı — kapalı bir denetim olay üretmez. "Haritadan…"
satırının yanında bir **Bırak** düğmesi var: kutuyu bırakıyor, kolu
açıyor, haritanın seçimini kolun boyuna geri kareye alıyor.

**Nokta sayısı tek bir yerde hesaplanır.** `gridPoints(across, along,
step)` `map.js` içinde, kutu aritmetiğinin geri kalanının yanında —
node'un gerçekten çalıştırabildiği yarıda, yani sayıyı bir sınama
söyleyebiliyor.

## Sonuçlar

Tarayıcıda, haritada 15,84 × 9,94 km'lik bir kutu çizip alınca:

| | önce | sonra |
|---|---|---|
| kolun çıktısı | `3 km` | `—` (gri, kapalı) |
| sayı kutusu | `3` | boş, kapalı |
| altındaki satır | `3 × 3 km, 10.000 nokta` | `174.768 nokta — haritadan seçilen kutu` |
| haritanın çubuğu | `174.768 nokta` | `174.768 nokta` |

"Bırak"a basınca üçü de 3 km'ye dönüyor ve harita yeniden kare seçiyor.

Sınamalar: `gridPoints` node'da beş boyutta çalıştırılıyor ve
Python'un yere seriveceği sayıyla karşılaştırılıyor; iki kenarı da tek
kenardan hesaplayan hâli kasten geri konduğunda üçü düşüyor. Sayfanın
kendi dalı kaynaktan okunuyor — `app.js` yüklenirken `document`'e
uzanıyor, node'da içe aktarılamıyor — ve o dalı kapattığımda sınama
düştü.
