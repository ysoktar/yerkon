# 0004. Yolların eğimi vardır

## Durum
Kabul edildi.

## Bağlam
Önceki kod tabanı her yol alıcısını sabit 1,5 m yüksekliğe koyuyor, sonra da
süzgecin yüksekliğini aynı yüksekliğe sahip bir harita yüzeyine
kısıtlıyordu. Düşey hata, haritanın varsayılan hassasiyetini ölçüyordu,
başka hiçbir şeyi değil.

## Karar
Bir Site bir arazi yükseklik alanı taşır. Yollar onu bir eğimle izler ve bir
alıcının gerçek yüksekliği, arazi yüksekliği artı aracın anten montaj
farkıdır. Köprüler ve tünel portalları o yüksekliği keskin biçimde
değiştirir.

Hiçbir senaryo alıcının yüksekliğini sabitlemez ve kestiricinin düşey
bileşeni her zaman serbesttir.

## Sonuçlar
Düşey hassasiyet seyrelmesinin artık üzerine etki edeceği bir şey var. Yol
senaryolarında bildirilen düşey hata büyük olacaktır, çünkü benzer
yüksekliklerdeki direklerden oluşan bir ağ yüksekliği gerçekten iyi
çözemez. Bu bir kusur değil, bulgunun kendisidir.
