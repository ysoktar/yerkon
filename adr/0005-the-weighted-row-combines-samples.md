# 0005. Ağırlıklı satır yüzdelikleri değil örnekleri birleştirir

## Durum
Kabul edildi.

## Bağlam
Raporun 32 numaralı dipnotu zaten ağırlıklı satırın üç senaryonun P50 ve P95
değerlerinin ortalamasını aldığını ve bunun örnekleri birleştirmekle aynı şey
olmadığını söylüyor. Aynı şey değildir ve ortalaması alınmış değerin
dağılımsal bir anlamı yoktur.

## Karar
Ağırlıklı satır, üç senaryonun sabitleme başına ham hata örneklerinden
ağırlıklarla orantılı olarak çeker, sonra yüzdelikleri o birleşik örnekten
hesaplar.

Ağırlıklar yapılandırmadır; varsayılanı raporun %50 şehir içi, %35 kırsal,
%15 tünel değerleridir.

## Sonuçlar
Ağırlıklı satırın P95'i, girdi olan üç P95 değerinin aralığının dışında
kalabilir ve bu doğrudur: bir karışımın kuyruğunu en kötü bileşeni sürükler.

Bu tablo yayımlandığında 32 numaralı dipnotun yeniden yazılması gerekecek.
