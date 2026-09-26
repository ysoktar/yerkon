# ADR-0095: tünelde UWB kanal 5, yoldan 1,2 m yükseklik ve 60 m aralık

## Durum

Kabul edildi (proje sahibinin ölçütüyle: en düşük maliyet, doğruluk ve
kullanılabilirlikten aşırı ödün vermeden). ADR-0020'nin tünel
geometrisi ve tünel satırının güzergâh km başına maliyeti geçerli.

## Bağlam

Tünel satırı DWM3000 ile iki yönlü ölçüm yapıyor. Satırın hesabında dört
hata vardı:

- **Frekans.** UWB bağlantıları 2,45 GHz'de hesaplanıyordu. Serbest
  uzayda 6,5 GHz 8,5 dB, 8 GHz 10,3 dB daha fazla kayıp demek.
- **Güç.** BTK'nın konum izleme satırı -41,3 dBm/MHz; 499,2 MHz'de
  -14,32 dBm e.i.r.p. (Muafiyet Kriterleri, Madde 18(4), Tablo 19).
- **Duyarlılık ve anten.** Eşik veri sayfasından alınmamıştı; tünelde
  2,4 GHz baskılı anten kullanılıyordu. DWM3000'in anteni için Qorvo
  örüntü veriyor, dBi vermiyor.
- **Araçtaki UWB.** Karayolu taşıtındaki UWB, anteninin montaj
  düzleminin üstüne -53,3 dBm/MHz'den fazla yayamıyor (ETSI EN 302 065-3
  V2.1.1, 4.3.4.2 ve Tablo 4; BTK Madde 18(2), Tablo 17). Kapalı alan
  için istisna yok; Ek C.1 eşdeğer korumanın kanıtlanmasına izin veriyor.

## Karar

- **Kanal 5 (6489,6 MHz).** Duyarlılık -100 dBm/500 MHz (DW3000 Data
  Sheet Rev 1.3, §3.4, Tablo 8, s. 13: 1024 preamble, 850 kbps); eşik
  11,12 dB. Kanal 9'dan (-99,3 dBm, Tablo 9) 0,7 dB daha duyarlı; yol kaybı
  serbest uzayda 1,8 dB, tünel modelinde 0,7 dB daha az. İkisi de BTK'nın 6-8,5 GHz satırında.
- **Güç** -14,32 dBm e.i.r.p., **anten** 0 dBi (ölçülene kadar).
- **Tünelde kayıp:** Molina-Garcia-Pardo, Lienard, Degauque, EURASIP JWCN
  2009, makale 560571, Denklem (2): PL = 86 + 8,2 log10(f, GHz) + 5,7
  log10(d, km). 3,4 km'lik düz bir karayolu tünelinde, 2,8-5 GHz'de,
  50-500 m arasında ölçülmüş; 50 m'nin altında serbest uzay. 6,5 GHz
  ölçülen aralığın dışında, frekans terimi oraya taşınıyor.
- **Harici sınır modelde.** Araç, yol üstünde kendi anteninden (1,5 m)
  yüksekte duran bir birime -53,3 dBm/MHz ile cevap veriyor. Karşılaştırma
  yolun düzleminde: eğimli bir tünelde gerçek yataya göre değil.
- **Birim yoldan 1,2 m yüksekte.** Araç anteninin altında; sınır bağlamıyor.
  0,5 m ek bir şey kazandırmıyor (50 m aralıkta %84,27 ve %84,88, kanal 9).
- **Aralık 60 m.** Kanal 5, 1,2 m, tam çözünürlük:

| Aralık | Askı | HPE P95 | Kullanılabilirlik | CAPEX TL/km |
|---|---|---|---|---|
| 40 m | 51 | 1,07 | %99,66 | 196133 |
| 50 m | 41 | 1,30 | %92,04 | 157675 |
| 55 m | 37 | 1,59 | %91,90 | 142292 |
| **60 m** | 34 | 2,43 | %94,32 | 130755 |
| 65 m | 31 | 2,89 | %89,50 | 119218 |
| 70 m | 29 | 2,61 | %83,46 | 111526 |
| 75 m | 27 | 2,79 | %86,87 | 103835 |
| 90 m | 23 | 3,18 | %70,03 | 88452 |

50-65 m arası bir düzlük; 70 m'den sonra kullanılabilirlik düşüyor. 60 m
düzlüğün en ucuz noktası: 40 m'den km başına %33 ucuz, bedeli 5 puan
kullanılabilirlik.

## Denenip bırakılanlar

- **Kanal 9.** Her aralıkta kanal 5'in gerisinde: 75 m'de %71,72.
- **Tünel ekseni boyunca yönlü anten (6 ve 9 dBi).** Araca yarıyor, yayaya
  yaramıyor: 150-200 m'de kullanılabilirlik %50 civarında, çünkü eldeki
  cihaz konum alamıyor. Modül yerine DW3110 yongası (DigiKey 1000 adet
  6,91 USD) ve harici anten gerekiyor. Bulunan tek dış ortam ürünü bir
  ölçüm anteni (Aaronia HyperLOG PRO 18300, 11 dBi, 2698 €, 1000 adet
  fiyatı yok).

## Sonuç

- **Yayımlanan tünel satırı:**

| | HPE P50 | HPE P95 | VPE P95 | Kullanılabilirlik | CAPEX/km | OPEX/km/yıl |
|---|---|---|---|---|---|---|
| Önce (250 m, 2,45 GHz ile) | 0,79 | 2,73 | 2,06 | %98,61 | 34612 | 3504 |
| **Şimdi (60 m, kanal 5)** | 0,58 | 2,43 | 3,31 | %94,32 | 130755 | 13239 |

Tutarlar TL. 2 km'lik tünelde 34 askı; birimler yolun iki yanında,
sırayla bir sağ, bir sol duvarda.

- **Kilometre başına maliyet arttı.** Eski satır 250 m aralıkla
  hesaplanıyordu, ama 2,45 GHz'lik hatalı bir bağlantıyla. Doğru frekans
  ve güçle bir UWB bağlantısı açıkta yaklaşık 50-60 m kapanıyor.
- **Sahada ölçülmeli.** Tünel modeli 6,5 GHz'de ölçülmedi; DWM3000'in
  anten kazancı yayımlanmıyor. İkisi de ilk saha denemesinde ölçülmeli.
- **Ağır araçlar** 1,2 m'deki birimin önünü kapatabilir; modelde yok.

## Kaynaklar

- BTK, Kısa Mesafeli Telsiz Cihazları için Muafiyet Kriterleri, Madde 1,
  Madde 18(1), 18(2) Tablo 17, 18(4) Tablo 19.
- ETSI EN 302 065-3 V2.1.1 (2016-11), 4.3.4.2, Tablo 4, Ek C.1.
- Qorvo, DW3000 Data Sheet Version 1.3, §3.4, Tablo 7, 8 ve 9, s. 13.
- Qorvo, DWM3000 Data Sheet Rev B, §5, Tablo 10 ve 11.
- J.-M. Molina-Garcia-Pardo, M. Lienard, P. Degauque, "Propagation in
  Tunnels: Experimental Investigations and Channel Modeling in a Wide
  Frequency Band for MIMO Applications", EURASIP Journal on Wireless
  Communications and Networking, 2009, makale 560571, Denklem (2) ve
  Şekil 5.
- DigiKey ve Mouser, Qorvo DW3110TR13 ürün sayfaları (1000 adet kademesi).
- Aaronia, HyperLOG PRO 18300 ürün sayfası ve örüntü belgesi.
