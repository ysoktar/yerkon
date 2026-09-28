# YERKON simülasyonu

YERKON yayın birimlerinden kurulan karasal bir konumlandırma ağının ne
kadar doğru konum verdiğini ve kurmanın ile işletmenin neye mal olduğunu
kestirir. Çıktısı, başvurudaki karşılaştırma tablosunun üç YERKON
satırıdır. Site: **<https://ysoktar.github.io/yerkon/>**

Sayılar bir modelden gelir, sahada yapılmış bir ölçümden değil. Her sayı
bir veri sayfasına, yayımlanmış bir ölçüme, bir standarda ya da açıkça
yazılmış bir varsayıma kadar izlenebilir.

## Nereden başlamalı

| Dosya | İçinde ne var |
|---|---|
| `CONTEXT.md` | Sözlük: her terimin Türkçe adı ve kodda kullanılan İngilizce karşılığı |
| `docs/adr/README.md` | Kararların dizini; hangisi geçerli, hangisi yerini başkasına bıraktı |
| `src/yerkon/defaults.toml` | Kimsenin vermediği her değer, kaynağı ve türüyle |
| `src/yerkon/bom.toml` | Her kartın parçaları ve satıcıların kademe fiyatları |
| `src/yerkon/published.toml` | Sitenin ve bu dosyanın gösterdiği yayımlanan koşu |
| `docs/WINDOWS.md` | Komutları Windows PowerShell'de çalıştırmak |
| `matlab/README.md` | Saat düzeltmesinden kalan kaymayı ölçen MATLAB betiği |

Belgeler Türkçe, kod İngilizce.

## Kurulum ve sınama

```bash
pip install -e ".[dev]"
pytest              # yaklaşık 20 dakika
```

## Tablo

```bash
yerkon table            # yayımlanan sayılar, yaklaşık 15 dakika
yerkon table --fast     # denemek için, yaklaşık 1 dakika, yayımlanmaz
yerkon table --publish  # koşuyu src/yerkon/published.toml'a yazar
```

| Sistem | Teknoloji | Ortam | HPE P50 [m] | HPE P95 [m] | VPE P95 [m] | Kullanılabilirlik | Alan [km²] | CAPEX [TL/km²] | OPEX [TL/km²/yıl] |
|---|---|---|---|---|---|---|---|---|---|
| YERKON (Şehir içi) | Karasal konumlandırma (SX1280/LoRa TWR) | Dış | 2,28 | 8,94 | 3,92 | %96,64 | 8,14 | 9061 | 1940 |
| YERKON (Kırsal) | Karasal konumlandırma (E28-SX1280 TWR) | Dış | 2,16 | 8,16 | 4,96 | %94,52 | 354,00 | 1138 | 330 |
| YERKON (Tünel) | Karasal konumlandırma (UWB/DWM3000 TWR) | İç + dış | 0,58 | 2,43 | 3,31 | %94,32 | 0,02 | 108294 /km | 22107 /km |

Tünel satırının maliyeti km² değil güzergâh km'si başına ("/km").

- **Şehir içi:** Ankara Kızılay, 3 km x 3 km, 91 m iniş çıkış. Birimler
  yerleşim aramasının seçtiği aydınlatma direklerinde, 12 m'de.
- **Kırsal:** Polatlı, 20 km x 20 km, 486 m iniş çıkış. Birimler çoğunlukla
  yol boyundaki elektrik dağıtım direklerinde, 10 m'de, güneş paneli ve
  aküyle.
- **Tünel:** Kızılcahamam'da 2 km'lik bir güzergâh, UWB (DWM3000), birimler
  yoldan 1,2 m yüksekte. Maliyeti km² değil güzergâh km'si başına.

Zemin Copernicus 30 m yükseklik verisinden, binalar ve yollar Overture ve
OpenStreetMap'ten bir kez getirilip paketin içine kondu; bir klon tabloyu
ağa çıkmadan yeniden üretir. `--fast` gölgelemeyi bir kez çeker ve zemini
kaba okur; sonucu yayımlanamaz.

## Fiyatlar

Her kartın her parçası `src/yerkon/bom.toml` içinde satıcısının kademe
tablosuyla yazılı. Bir ürünün 1, 100 ve 1000 adetlik fiyatı, parçaların o
kadar kart için alınan adetteki fiyatlarının toplamıdır. Satıcının
yayımlamadığı bir kademede indirim varsayılmaz. Tablo 1000 adeti kullanır,
çünkü merkezî sistem bin birime yayılıyor (ADR-0105).

Kurulum ve işletme kalemleri (montaj, bakım, elektrik, kira, merkezî
sistem) `defaults.toml` içinde; her birinin değeri, türü (yayımlanmış
fiyat, ölçüm, standart, hesap, tasarım kararı, varsayım) ve kaynağı
sitenin Maliyet sayfasında listeleniyor.

```bash
yerkon defaults --full                     # bütün değerler ve kaynakları
yerkon table --defaults benim-degerlerim.toml
```

## Site ve simülatör

```bash
yerkon view     # siteyi yerelde açar; simülatör /calistir adresinde
yerkon pages    # siteyi docs/ klasörüne dosya olarak yazar
```

`docs/` klasörü `gh-pages` dalına kopyalanır ve GitHub Pages onu sunar;
yayımlamak bir push. Simülatör ziyaretçinin tarayıcısında Pyodide ile
çalışır, hiçbir sunucu hesap yapmaz (ADR-0080). Her sayfa Türkçe ve
İngilizce.

Simülatörde üç satır aynı anda tutulur. Zemin, yerleşim, hedef ve
dayanaklar paneldeki altı adımda değiştirilir. Başka ayarları da
değiştiren bir değişiklik hemen uygulanır; neyi değiştirdiği sahnenin
altındaki notta yazar ve oradan geri alınabilir (ADR-0107). Panelin
başındaki **Hızlı başla** kutusu, haritadan seçilen bir yeri getirir, en
iyi yerleşimi bulur ve hızlı bir simülasyon koşar.

## Yerleşim araması

```bash
yerkon place --scenario urban --aim cheaper --save
yerkon place --scenario rural --aim better --save
```

Birimleri ızgaraya değil zaten duran yapılara koyar: aydınlatma direkleri
ve tabelalar, yol boyundaki direkler (şehirde aydınlatma, kırsalda
elektrik dağıtım direği) ve tepelere dikilecek 25 m'lik direkler. Çatılar
kiralık olduğu için aday sayılmaz (ADR-0104). Seçim ömür boyu maliyete
göre bir örtme aramasıdır; sonuç `src/yerkon/placements/` altında durur ve
tablonun şehir içi ve kırsal satırları onu kullanır (ADR-0096).

## Diğer komutlar

| Komut | Ne yapar |
|---|---|
| `yerkon options` | Adlandırılmış yerleşim seçenekleri; `--option AD` ile tabloya uygulanır |
| `yerkon solve` | Bir hedefi karşılayan en ucuz düzeni arar ve seçenek olarak kaydeder |
| `yerkon budget` | Hatayı kaynaklarına ayırır: hangi kaynak kalkarsa ne kazanılır |
| `yerkon deliver --into KLASÖR` | Tabloyu, hata bütçesini, değerleri ve seçenekleri Markdown olarak yazar |
| `yerkon calibrate KAYIT` | SDR kaydından paket kaybını ya da MATLAB çıktısından saat kaymasını okur |
| `yerkon design` | Bir ayar değişikliğinin başka neleri değiştirdiğini gösterir ve bir kez sorar |
| `python tools/hardware.py` | Telsiz donanımı seçeneklerini (EBYTE 12S, 20S, 27S, belgesiz 12S ve eski O4 kurulumu) şehir içi ve kırsal satırda, bütün sütunlarla ve iki yönü de sınayarak karşılaştırır. Yalnız yerel; site ve tarayıcıdaki simülatör bunu görmez. `--list` seçenekleri sayar |

## Yeni bir saha getirmek

```bash
yerkon fetch --centre 37.8716,32.4847 --size 12 --into konya
```

Merkez enlem ve boylam, boyut km. Zemin Copernicus 30 m paftalarından
gelir ve diske alınır; binalar, yollar ve yol kenarı yapıları Overture'dan,
olmazsa OpenStreetMap'ten. `--into` çıplak bir ad alırsa saha paketin
kendi klasörüne yazılır ve simülatörün zemin listesinde hemen görünür.
Simülatördeki **Yeni bir yer getir** kutusu aynı işi haritada çizilen bir
kutu için yapar.

Uydu görüntüsü isteğe bağlıdır ve yalnız çizime girer, hesaba girmez.
Komut satırında karo adresi `--imagery` ile verilir, örneğin Esri World
Imagery: `https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}`
(atıf: Esri, Maxar, Earthstar Geographics, GIS User Community). Her
sağlayıcının kendi kullanım koşulları var.

## Arşiv

`docs/ANTEN-KARSILASTIRMASI.md` ve `docs/MALIYET-KARSILASTIRMASI.md`
kararlardan önce yapılan karşılaştırmaları tutar. Kararlar verildi
(ADR-0094, ADR-0104, ADR-0105); sayıları o günün modeline aittir.
