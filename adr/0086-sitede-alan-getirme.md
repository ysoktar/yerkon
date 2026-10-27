# ADR-0086: yayımlanmış sitede alan getirme; uydu görüntüsü bir onay kutusu

## Durum

Kabul edildi. Sayfa için ADR-0041'in "hazır adres yok" kararının yerine
geçer; kütüphane (`TileImagery`) ve komut satırı yine adres istemiyor.

## Bağlam

Yayımlanmış sitede simülatör ziyaretçinin tarayıcısında çalışıyor
(ADR-0080): WebAssembly'ye derlenmiş Python, bir tarayıcı işçisinde.
"Yeni bir yer getir" orada hiç çalışmıyordu. Getirme üç masaüstü paketi
istiyordu (rasterio, requests, pyarrow); tarayıcıda hiçbiri yok, bu
yüzden düğme ve harita kapalı geliyordu. Ayrıca getirilen bir sahanın
fotoğrafı sayfaya ikili bir yanıt olarak gidiyordu ve tarayıcı yolu ikili
yanıtı 404 ile geri çeviriyordu.

Uydu görüntüsü için de kişinin bir karo sunucusu bulup adresini
yapıştırması gerekiyordu. Proje sahibi bunu istemedi: bir onay kutusu
olsun, adres gösterilmesin.

## Karar

**İstek tek yerden.** `yerkon.site.http` masaüstünde `requests`'i,
tarayıcıda işçinin kendi eşzamanlı isteğini kullanıyor. İşçi beklemeye
izinli (sayfa değil), bu yüzden istek döngüsü olarak yazılmış bir
getirici iki yerde de aynen çalışıyor.

**Tarayıcının ulaşabildiği kaynaklar.**

| | Masaüstü | Tarayıcı |
|---|---|---|
| Zemin | Copernicus, sonra arazi karoları, sonra OpenTopoData | Arazi karoları |
| Bina | Overture, sonra OpenStreetMap (Overpass) | OpenStreetMap (Overpass) |
| Yol | Overture, sonra OpenStreetMap (Overpass) | OpenStreetMap (Overpass) |
| Sokak donanımı | Overture | yok |

Arazi karoları AWS'deki açık "Terrarium" karoları: her pikselin
rengi bir yükseklik. Türkiye'de EU-DEM (25 m), başka yerlerde SRTM
(30 m). Her sayfaya yanıt veriyor; Copernicus kovası vermiyor. Kızılay'da
3 km'lik kutuda Copernicus'la farkı: ortalama 2,6 m, RMS 4,5 m
(Copernicus binaları da içeren bir yüzey modeli). Yakınlık ızgara
aralığına göre seçiliyor, en çok 64 karo.

Pillow (karoları çözmek için) işçiye ilk getirmede yükleniyor; hiç
getirmeyen ziyaretçi onu beklemiyor.

**Fotoğraf sayfaya base64 olarak geçiyor.** `answer` metin olmayan bir
yanıtı base64 ve dördüncü bir "base64" alanıyla döndürüyor; `local.js`
onu bayta çeviriyor. Sayfa fotoğrafı `fetch` ile istiyor, çünkü bir
resmin kendi isteği işçiye değil ağa gider.

**Uydu görüntüsü bir onay kutusu.** "Uydu görüntüsünü de getir",
işaretli geliyor. Sağlayıcı Esri World Imagery; adres sayfada yok,
`site/fetch.py`'de `AERIAL_TILES`. Esri'nin istediği atıf kutunun altında
ve sahanın kaydında yazıyor. Yakınlık da sorulmuyor: 17'den başlıyor ve
kutu 120 karodan fazlasını istiyorsa kaba yakınlığa iniyor: 2 km'lik
kutu 17'de kalıyor (piksel başına yaklaşık 0,9 m), varsayılan 3 km'lik
kutu 16'ya (1,8 m), 10 km'lik kutu 14'e iniyor. Reddetmek yerine daha
kaba bir fotoğraf.

## Sonuçlar

- Yayımlanmış sitede bir yer getirilebiliyor: zemin, bina, yol ve
  fotoğrafla. Sokak donanımı (direk yerleşiminin aday noktaları) yalnız
  masaüstünde.
- Tarayıcıda getirilen saha o sekmenin belleğinde duruyor; sayfa
  yenilenince gidiyor. Kalıcı olması gerekirse tarayıcı deposuna
  yazılabilir.
- Esri'nin kullanım koşulları bu seçimle proje sahibinin sorumluluğunda;
  atıf zorunlu.
- İşçinin eşzamanlı isteği bu ortamdan uçtan uca denenemedi (Pyodide
  paketlerinin sunucusu buradan kapalı). Aynı kod yerel sunucular ve
  kayıtlı Overpass yanıtlarıyla sınanıyor; tarayıcıya özgü tek satır
  yanıtın baytlarını okuyan satır.
