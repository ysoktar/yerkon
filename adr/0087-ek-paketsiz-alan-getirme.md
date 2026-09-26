# ADR-0087: bir yer getirmek ek paket istemiyor; uydu görüntüsünü sayfa çiziyor

## Durum

Kabul edildi. ADR-0051'in "eksik paketi baştan söyle" kararının yerine
geçer: artık eksik bir şey yok. ADR-0086'nın fotoğraf yolunu da sayfa
için değiştirir.

## Bağlam

Yerel uygulamada (`yerkon view`) "Yeni bir yer getir" paneli, kurulumda
rasterio, requests ve pyarrow yoksa şunu yazıp düğmeleri kapatıyordu:
"Bu kurulum saha indiremiyor: rasterio, requests, pyarrow eksik. Kurmak
için: pip install ...". Düz bir kurulumda yalnızca numpy var, Pillow bile
yok. Proje sahibi bunun düzelmesini istedi: bir yer getirmek bir kurulum
talimatı olmadan çalışmalı ve uydu görüntüsü de binalar gibi bir onay
kutusu olmalı, adresi arka planda ayarlanmış.

## Karar

**İstek standart kütüphaneyle.** `yerkon.site.http`, `requests` yoksa
`urllib` kullanıyor.

**PNG numpy ile.** `yerkon.site.png` 8 bitlik, taramalı olmayan PNG'yi
okuyup yazıyor: beş süzgeç, zlib. Arazi karolarını ve kaydedilmiş
fotoğrafı Pillow yoksa bununla okuyoruz. Pillow varsa o kullanılıyor,
daha hızlı. Pillow'un yazdığı RGB, RGBA, gri, gri+alfa ve paletli
PNG'leri bayt bayt aynı okuyor; bir karo 0,04 s.

**Uydu görüntüsünü sayfa çiziyor.** Sağlayıcının karoları JPEG ve JPEG'i
numpy ile çözmek makul değil; tarayıcı ise zaten çözüyor. Kutu
işaretliyse getirme hiçbir karo indirmiyor, sahanın kaydına hangi
karoların onu kapladığını yazıyor (`Drape`: şablon, yakınlık, karo
aralığı). Sayfa karoları kendisi istiyor, bir tuvalde birleştiriyor ve
zemini onunla boyuyor. Yakınlık 17'den başlıyor; kutu 200 karoyu
geçerse iniyor (3 km 17'de, 5 km 16'da, 10 km 15'te).

**Hiçbir şey eksik değil.** `missing_for_a_fetch()` boş dönüyor, panel
kurulum talimatı göstermiyor. Üç paket artık yalnızca daha iyisini
getiriyor (`FETCH_BETTER_WITH`): Copernicus zemini, Overture binaları,
sokak donanımı.

## Sonuçlar

- Düz bir kurulumda ve yayımlanmış sitede bir yer getirilebiliyor:
  zemin, bina, yol ve uydu görüntüsü.
- Sayfanın çizdiği fotoğraf çevrimdışı değil: sahayı her açışta karolar
  yeniden isteniyor (tarayıcının önbelleği tutarsa istenmiyor).
- Fotoğraf sayfada okunabilsin diye sağlayıcının tarayıcılara izin
  vermesi gerekiyor. Esri'nin karo sunucusu bunu yaygın olarak veriyor;
  bu ortamdan sınanamadı (sunucu buradan kapalı). Vermezse zemin düz
  renkle çiziliyor, hesap değişmiyor.
- Komut satırındaki `yerkon fetch --imagery ADRES` eskisi gibi karoları
  indirip birleştiriyor ve bunun için Pillow istiyor.
