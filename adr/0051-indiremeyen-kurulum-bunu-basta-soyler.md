# ADR-0051: indiremeyen bir kurulum bunu baştan söyler

## Durum

Kabul edildi.

## Bağlam

Taze bir Windows makinesinde, belgelerin gösterdiği komutla:

```powershell
git pull
pip install -e ".[dev]"
yerkon view
```

Sonra sayfada saha panelini açıp bir ad yazdım, haritadan bir kutu
çizdim, "Getir"e bastım ve bunu aldım:

```
yerkon.site.fetch.Unreachable: Hiçbir yükseklik kaynağı cevap vermedi.
  Copernicus DEM 30 m: Reading a GeoTIFF needs rasterio. Install it with
  `pip install rasterio`.
  OpenTopoData SRTM 30 m: This area needs 70,756 points, which is 708
  calls to OpenTopoData SRTM 30 m...
```

Mesajın kendisi doğru ve açıklayıcı. **Sırası yanlış.** Kurulum bunu
en baştan biliyordu: `rasterio` yoktu ve olmadan hiçbir kutu inmeyecekti.
Yine de ad yazıldı, harita açıldı, kutu sürüklendi, getirme başlatıldı ve
ancak sonunda bir Python paketinden söz edildi.

`rasterio`, `requests` ve `pyarrow` bu paketin bağımlılığı değil, ve
bilerek değil: tablodaki her sayı paketin içinde sevk edilen zeminden,
ağsız ve GDAL'siz üretilebiliyor (ADR-0008). Bu korunmaya değer. Ama
"yok" ile "var" arasındaki farkı yalnızca getirme anında öğrenmek
korunmaya değmez.

Belgeler zaten `pip install -e ".[dev,sites]"` diyor (TRY-IT, WINDOWS).
Bir kişinin doğru komutu okumamış olması sayfanın çalışmayan bir düğme
sunması için gerekçe değil (ADR-0036).

## Karar

**Motor hangi paketin eksik olduğunu söyler.** `missing_for_a_fetch()`
üçünü `importlib.util.find_spec` ile soruyor — içe aktarmıyor, çünkü
rasterio'yu içe aktarmak saniyenin çoğu ve GDAL demek, buradaki soruysa
yalnızca "duruyor mu". Kurulu ama bozuk bir paket "duruyor" cevabı verir
ve kullanıldığında kendisi söyler.

**Sayfa bunu sahnenin `choices`'ında alır**, sunduğu her liste gibi:
sayfa asla motorunkinden ayrılabilecek ikinci bir kopya tutmaz.

**Panel kutuyu çizdirmeden önce söyler.** Eksikse "Getir" ve "Haritada
seç" düğmeleri kapalı, üstlerinde tek satır: hangi paketler eksik ve
yazılacak tam komut. Düğmeler gizlenmiyor, kapatılıyor — bu sayfanın
onlara sahip bir makinede ne yapacağı görünsün diye.

**Üç mesaj da iki dilde.** `site.needs_rasterio` yoktu; GeoTIFF mesajı
projedeki son İngilizce-sabit cümleydi. Üçü de aynı komutu adıyla
söylüyor: `pip install -e ".[dev,sites]"`. Öncekiler
`pip install "yerkon[sites]"` diyordu, ki bir kopyadan kuran kişide
çalışmaz.

## Sonuçlar

`rasterio` ve `pyarrow`'u görmeyen bir kurulumda panel şunu diyor:

> Bu kurulum saha indiremiyor: rasterio, pyarrow eksik. Kurmak için:
> `pip install -e ".[dev,sites]"` — Windows'ta docs/WINDOWS.md.

İngilizcesi aynı komutu veriyor. Üçü de kurulu bir makinede panel
değişmiyor, not gizli, düğmeler açık.

Sınamalar `find_spec`'i yerinden oynatarak üç durumu da kuruyor (hepsi
var, ikisi yok, soru hata veriyor), ve sayfanın notu gerçekten
öğrendiğini — `drawSites` içinden çağrıldığını — çiviliyor: çağrıyı
kaldırdığımda sınama düştü.
