# ADR-0066: PNT demiyoruz

## Durum

Kabul edildi.

## Bağlam

Karşılaştırma tablosunun teknoloji sütununda YERKON satırları "Karasal
PNT" yazıyordu. Tablodaki komşuları da öyle: TerraPoiNT ve eLoran
gerçekten PNT sistemleri, yani konum, seyrüsefer **ve zamanlama**
sunuyorlar. eLoran'ın zamanlama çıktısı sistemin ana ürünlerinden biri.

YERKON bunu yapmıyor. Yayın birimi kimliğini ve ölçülmüş konumunu
yayınlıyor, alıcı çift yönlü menzil ölçümünden kendi konumunu çıkarıyor.
Ortada bir zamanlama hizmeti yok: ne bir saat dağıtımı, ne bir frekans
referansı, ne de zamanlama için bir doğruluk iddiası. Seyrüsefer de
alıcının kendi işi.

Aynı satırda "PNT" yazmak, olmayan iki hizmeti varmış gibi gösteriyor.
Bir karşılaştırma tablosunda bu, yanlış bir sütun değil yanlış bir
kategori.

## Karar

**Teknoloji sütunu "Karasal konumlandırma" diyor.** Üç senaryo satırı da,
ağırlıklı satır da.

| önce | sonra |
|---|---|
| Karasal PNT (SX1280/LoRa TWR) | Karasal konumlandırma (SX1280/LoRa TWR) |
| Karasal PNT (E28-SX1280 TWR) | Karasal konumlandırma (E28-SX1280 TWR) |
| Karasal PNT (UWB/DWM3000 TWR) | Karasal konumlandırma (UWB/DWM3000 TWR) |
| Karasal PNT | Karasal konumlandırma |

**Sitede de geçmiyor**, ve ADR'ler dışında depoda hiç geçmiyor. Zaman
dağıtımı bir gün eklenirse o zaman yeniden konuşulur.

**Sayılar değişmedi.** Değişen yalnızca bir etiket, ama etiket
`published.toml` içinde duruyor ve o dosyayı bir koşu yazıyor. Bu yüzden
tablo yeniden koşuldu ve yeniden yayımlandı; README ile kaydın aynı
olduğunu söyleyen sınama da bu yüzden ikisini birden gördü.

## Sonuçlar

Tablonun kendisi aynı kaldı: aynı tohum, aynı ayarlar, aynı dört satır.
Teknoloji sütunu artık sistemin yaptığını söylüyor.

## Yapılmayanlar

**Ortam sütunu hâlâ iki dilde de Türkçe.** "Dış" ve "İç + dış" rapora
giren adlar ve çevrilmiyorlar. Sonuç sayfası bunu bir satırla söylüyor.

**Raporun kendisi bu depoda değil.** Sunumun tablosunda da aynı düzeltme
gerekiyor, ve onu buradan yapamayız.
