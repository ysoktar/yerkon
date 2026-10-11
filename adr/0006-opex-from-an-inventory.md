# 0006. OPEX bir envanterden gelir, bir yüzdeden değil

## Durum
Kabul edildi.

## Bağlam
Rapor OPEX'i her YERKON satırı için boş bırakıyor. Yaygın kestirme —
sermaye maliyetinin sabit bir yüzdesi — arkasında hiçbir mekanizma olmayan
ve denetlenmesinin hiçbir yolu bulunmayan bir sayı üretirdi.

## Karar
Yıllık işletme maliyeti, her biri yerleşimdeki sayılabilir bir şeye bağlı,
adlandırılmış yinelenen kalemlerin toplamıdır: direk başına enerji, direk ya
da geçit başına bağlantı, açıkça belirtilmiş bir hizmet ömründen donanım
yenileme, saha başına planlı bakım ziyaretleri ve yerleşimlere yayılmış
merkezî sistem işletmesi.

Her oran, kaynağı kaydedilmiş adlandırılmış bir sabittir — donanım
fiyatlarıyla aynı şekilde. Kaynak yoksa sabit bunu söyler ve satır bir
varsayım olarak işaretlenir.

## Sonuçlar
OPEX düğüm sayısına tepki verir, yani direkleri yarıya indiren bir tasarım
değişikliği işletme maliyetinin çoğunu da yarıya indirir. Projenin kaynak
bulamadığı oranlar, bir yüzdenin içinde gizlenmek yerine varsayım olarak
görünür.
