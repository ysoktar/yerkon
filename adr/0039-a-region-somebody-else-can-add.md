# ADR-0039: başkasının da ekleyebileceği bir bölge

## Durum

Kabul edildi.

## Bağlam

Bu projenin dört sahası Ankara'da, çünkü rapor Ankara'yı soruyor. Ama
tek çıktısı bir tablo değil, bir yöntem: başka bir yerde aynı donanımın
ne verdiğini sormak. O soruyu sormanın yolu `yerkon fetch`'ti ve yolun
her adımı, onu daha önce yapmamış birini durduruyordu.

**Dört ondalık derece isteniyordu.** `--south --west --north --east`.
Haritaya bakan birinin elinde bir iğne ve "şu kadar etraf" vardır; sınır
kutusu yoktur ve onu hesaplamak, boylam derecesinin enlem derecesinden
kısa olduğunu bilmeyi gerektirir.

**`--into konya` yanlış yere yazıyordu.** Kabuğun bulunduğu yere. Komut
başarıyla dönüyordu, saha yazılıyordu ve `fetched()` ile zemin seçicisi
onu asla görmüyordu. Bunu ben de yaşadım: dört sahayı yeniden indirdim
ve dördü de depo kökünde belirdi.

**Sayfadan indirilen bir yer listede belirmiyordu.** İş bitiyor, künye
yazılıyor, sonuç tablosu çiziliyor — ve zemin seçicisinde yok. Başka bir
şey sahneyi tazeleyene kadar.

**"Bu zemini kullan" düğmesi onay panelini atlıyordu.** Zemin seçicisi
ADR-0037'den sonra panelden geçiyordu; yanındaki düğme geçmiyordu. Yani
yeni bir bölgeyle en olası yol — getir, sonra kullan — sahanın boyunu,
enini ve direk dizilerini söylemeden değiştiren yoldu.

**Ve klasörün adı `ankara`ydı.** Konya'yı ekleyen biri verisinin
`site/ankara/konya` altına indiğini görüyordu.

## Karar

**Merkez ve boy, dört köşe değil.** `box_around(latitude, longitude,
size_km)` kareyi metre cinsinden kurar; iki yarı genişlik farklıdır,
çünkü boylam derecesi ekvator dışında her yerde daha kısadır. Hem komut
satırı hem sayfa bunu kullanır, yani aritmetik tek yerde. Dört köşe
kalıyor — elinde kutu olan için — ama ikisini birlikte vermek iki farklı
kutu tarif ettiği için reddediliyor.

**Çıplak bir ad paketin saha klasörüne yazar.** İçinde ayırıcı olan bir
şey yoldur ve olduğu gibi kullanılır. Görmediğin bir yere yazılan bir
indirme, başarıyla dönen ve hiçbir şey üretmeyen bir komuttur.

**Klasörün adı `places`.** Ankara'daki dört saha orada duruyor ve
Konya'yı ekleyen biri onu bir Ankara klasörüne koymuyor.

**İş bitince yer hemen listede.** Motor her sahnede neyin indirildiğini
buluyor, dolayısıyla sonucun tek bir tazeleme istemesi yetiyor.

**"Bu zemini kullan" da panelden geçiyor**, yanındaki seçici gibi. Bir
sınama artık zemini seçmenin *her* yolunun panelden geçtiğini söylüyor,
tek tek düğmeleri değil.

**Ne kadar iş olacağı önce söyleniyor.** Sayfada sürgünün altındaki
satır kutu boyu ile ızgara aralığından kaç nokta çıkacağını yazar; komut
satırı aynısını yazar ve büyük bir ızgarada daha seyrek bir aralığın ne
getireceğini söyler. Otuz metre Copernicus'un kendi çözünürlüğü: daha
sıkı istemek yeni bilgi getirmez.

**Ve bulguya giden iki adım adıyla yazılıyor.** Bir indirme, kendi
başına, kimsenin bir şey sormadığı zemindir.

## Sonuçlar

Konya, iki komutta:

```
yerkon fetch --centre 37.8716,32.4847 --size 12 --into konya
yerkon table --only rural --defaults <rural.site = "konya" yapılmış dosya>
```

| kırsal satır | HPE P50 | HPE P95 | Kullanılabilirlik | Alan |
|---|---|---|---|---|
| Polatlı'da | 3,11 m | 15,09 m | %72,75 | 218,75 km² |
| Konya'da | 2,59 m | 7,62 m | %100,00 | 62,50 km² |

Aynı yerleşim, aynı direkler, aynı telsizler, başka zemin. Polatlı'nın
20 km'de 486 m engebesi bağlantıları kesiyor; Konya ovası kesmiyor.
Tablonun bunu söylemesi olanaksızdı, çünkü tabloda yalnızca Polatlı var.

`docs/TRY-IT.md` artık bu yolu baştan sona yazıyor: sayfadan üç alan,
komut satırından bir satır, getirdikten sonra neyin kilitlendiği ve neyin
sınanmadığı.

**Genelleşen ders, yine ADR-0027'nin bıraktığı yer.** Beş engelin dördü
"var ama ulaşılmıyor" türündendi: saha yazıldı ama görülmedi, yer
indirildi ama listelenmedi, panel kuruldu ama bir düğme onu atladı.
Hiçbiri hata yükseltmedi. Dördünü de bulan şey bir sınama değil, yolu
baştan sona kendim yürümekti — ve `--into konya`'nın yanlış yere
yazdığını, o yüzden kendi ayağıma takılarak öğrendim.
