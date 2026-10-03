# ADR-0068: ağırlıklı satır kalktı

## Durum

Kabul edildi. ADR-0005'in kurduğu satırı kaldırıyor.

## Bağlam

Tablonun dördüncü satırı üç senaryonun sabitleme başına ham hata
örneklerini sabit ağırlıklar altında birleştiriyor ve yüzdelikleri
birleşik örnekten yeniden hesaplıyordu. ADR-0005 bunu doğru yapmanın
yolunu kaydediyor, ve o kısım hâlâ doğru: üç P95 değerinin ortalaması
bir P95 üretmez.

Sorun hesapta değil, girdisindeydi. Ağırlıklar bir alıcının yolculuğunun
ne kadarını nerede geçirdiğini söylüyor, ve bunu kimse ölçmedi. Depo
%50, %40, %10 kullanıyordu; sunumun dipnotu %50, %35, %15 diyordu. İkisi
de bir varsayım, ve satırın bütün sayıları o varsayımın üzerinde
duruyordu.

Sunum satırı çıkarıyor. Depo da çıkarıyor, çünkü raporda karşılığı
olmayan bir satır üretmek bu deponun tek çıktısını genişletmek olurdu.

## Karar

**Tablo üç satır**: şehir içi, kırsal, tünel. Her biri bir yerleşim, ve
her yerleşim kendi zemininde koşuyor.

**Yalnız o satır için var olan her şey gitti.** Kalan kod, bir daha
kullanılmayacak bir satırın makinesi olurdu:

| ne | nerede |
|---|---|
| `report.weighted` ve `WEIGHTED_ROW` | report.py |
| `evaluate.combine` | evaluate.py |
| `Deployed.weight`, `DEFAULT_WEIGHTS`, `reweighted` | scenarios.py |
| `--weight` ve `_weights` | cli.py |
| dağılımdaki ağırlıklı satır | budget.py |
| künyedeki ağırlık satırı | report.footnotes |
| sayfadaki "üçü birden (+ ağırlıklı satır)" | words.js |

**Anasayfa artık üç satırın P95'ini gösteriyor.** Önce ağırlıklı satırın
dört figürünü gösteriyordu, ve o satır olmayınca yerine tek bir sayı
koymak yanlış olurdu: üç senaryo üç ayrı cevap. Yüzdelik olarak doksan
beşinci seçildi, çünkü ellinci olanı kayıran taraf.

**Yüzdelik ortalamama kuralı kalıyor.** Gölge çekilişleri hâlâ
havuzlanıyor (ADR-0055), ve bunun gerekçesi artık ADR-0005'e değil kendi
ADR'sine bakıyor.

## Sonuçlar

Tablo yeniden koşuldu ve yayımlandı. Üç satırın sayıları değişmedi;
değişen, dördüncünün olmaması.

`yerkon budget` de üç dağılım veriyor, dört değil.

## Yapılmayanlar

**Yolculuk payları hiç ölçülmedi.** Satır gitti ama sorusu duruyor: bir
alıcı zamanının ne kadarını şehirde, ne kadarını açık yolda, ne kadarını
tünelde geçiriyor. Ölçülürse ağırlıklı bir satır yeniden anlamlı olur, ve
o zaman ADR-0005'in hesabı hâlâ yerinde duruyor olacak.

**Geçmiş ölçümler yeniden yazılmadı.** `docs/HANDOFF.md` ve
`docs/TRY-IT.md` içindeki eski karşılaştırma tablolarında ağırlıklı satır
geçiyor. Onlar o gün ne ölçüldüğünün kaydı, ve olmamış gibi yazılmaları
kaydı bozardı.
