# ADR-0054: kırpmak yalnızca küçültür

## Durum

Kabul edildi.

## Bağlam

Haritadan 19,31 × 12,33 km'lik bir kutu çizip getirdim, "Kullan"a
bastım. Saha **2970 × 2940 m** kaldı — yani önceki zeminin, Kızılay'ın
ölçüsü. Az önce indirilen zeminin **%1,5'i**, ve dışarıda kalan %98,5
hakkında ekranda tek kelime yok.

Sebep basit: ADR-0037 sahayı ölçülen zemine **kırpıyor**, ve kırpmak
yalnızca küçültür. Zemin sahanın altında küçüldüğünde bu doğru; zemin
büyüdüğünde saha geride kalıyor.

Bu, ADR-0048'in ve ADR-0052'nin akrabası: bir denetimin gösterdiği ile
yürürlükte olanın ayrışması. Orada kolun iki yarısı, burada zeminle
saha.

## Karar

**Zemini adlandırmak sahayı büyütebilir de.** Kural tek cümle: *zemininin
tamamı olan bir saha, yeni zeminin de tamamı olur.*

- Sahayı birinin eliyle küçülttüğü durumda (zemininin tamamı değilse)
  verdiği ölçü korunuyor — bu bir dilek değil, saha hakkında bir olgu.
- **Koridor koridor kalıyor.** Eni sıfır olan bir saha yeni boyu alıyor
  ve sıfırı koruyor; onu koridor yapan şey o sıfır.
- **Ölçülmemiş zemin hiçbir şey oynatmıyor.** Bir delik tepenin içinden
  gidiyor (kırpma zaten onu atlıyor), ve modellenmiş zeminin
  doldurulmuş sayılacak bir ölçüsü yok — oradan gelirken sayı korunuyor
  ve kararı kırpma veriyor.

**Panel önden söylüyor, ve iki sebebi ayırıyor.** Zemin değişimi zaten
onay panelinden geçiyordu (ADR-0009). Şimdi büyüme de orada görünüyor ve
gerekçesi ayrı bir cümle: küçülme "bir saha kendisi için indirilen
zeminden büyük olamaz", büyüme "saha, getirilen zeminin tamamıydı ve öyle
kalıyor".

## Sonuçlar

Tarayıcıda, Kızılay'dan Polatlı'ya geçerken panel:

| | | |
|---|---|---|
| İSTEDİĞİN DEĞİŞİKLİK | Zemin | kizilay → polatli |
| BUNLAR DA DEĞİŞİYOR | Sahanın boyu | 2970 → 22800 |
| | Sahanın eni | 2940 → 19860 |

Evet dedikten sonra iki kol da, iki kutu da, motor da 22800 × 19860.

Beş sınama: dolan saha dolmaya devam ediyor, elle küçültülen korunuyor,
koridor koridor kalıyor, delik ve modellenmiş zemin kımıldamıyor, ve
panel büyümeyi kendi gerekçesiyle gösteriyor. Kuralı kaldırdığımda
ikisi düştü.
