# ADR-0116: Yaya alıcısında e-kâğıt ekran ve güneş paneli

## Durum

Kabul edildi (proje sahibinin isteği, 30 Eylül 2026).

## Bağlam

Yaya alıcısı konumu ESP32-S3 üzerinden BLE ile telefona gönderiyordu;
kendi ekranı yoktu. Sunumun 9. sayfası ise kurulum personelinin "YERKON
Yaya Alıcısı ekranındaki" yönlendirmeleri izleyeceğini söylüyor. Alıcı
dışarıda, uzun süre ve telefonsuz da kullanılabilmeli.

## Karar

- Ekran: Good Display GDEY0154D67, 1,54 inç e-kâğıt, 200x200, SPI
  (SSD1681). Görüntü değişirken 4,5 mW, beklerken 0,003 mW çekiyor
  (üreticinin sayfası); güneş altında okunuyor. Çıplak panel: üreticinin
  yükselteci (AOS AO3400A, 10 µH bobin, üç MBR0530) ve 24 uçlu 0,5 mm
  FPC bağlantısı (XUNPU FPC-05F-24PH20) karta eklendi. Fiyat 4,51 $,
  3 adette %5 indirimle 4,2845 $; üstü yayımlanmamış, indirim
  varsayılmadı.
- Güneş paneli: Seeed Studio 313070004, 0,5 W, 5,5 V, 55x70 mm, 2,50 $;
  büyük adet fiyatı yayımlanmamış. G517 kutusunun (92x66,5x21 mm)
  arkasına sığıyor; ekran (31,8x37,3 mm) önüne. Panel TP4056'ya doğrudan
  bağlanır; dördüncü MBR0530 pilin panele geri boşalmasını önler.
- Yeni yaya alıcısı fiyatı (1 / 100 / 1000 adet): 3.935,42 / 3.179,93 /
  2.672,21 TL (önce 1000 adette 2.330,11 TL).

## Seçenekler

| Seçenek | Not | 1000 adet |
|---|---|---|
| GDEY0154D67 e-kâğıt (seçilen) | güneşte okunur, beklerken güç çekmez | 4,2845 $ + yükselteç ve bağlantı |
| 2,8 inç ILI9341 TFT (araç alıcısındaki) | arka ışık sürekli güç çeker | 6,00 $ |
| Seeed 0,5 W panel (seçilen) | 55x70 mm, 5,5 V | 2,50 $ |
| ANYSOLAR SM141K10L | 0,307 W, 70x23 mm, DigiKey | 5,73 $ |

Alibaba'daki markasız küçük paneller daha ucuz görünüyor, ama sayfa
doğrulama (CAPTCHA) istediği için fiyat okunamadı ve kullanılmadı.

## Sonuçlar

- Tablonun maliyet satırları değişmiyor: alıcılar kuruluma sayılmıyor.
- Tam güneşte panel yaklaşık 90 mA verir (0,5 W / 5,5 V); 1.000 mAh pil
  boştan yaklaşık 11 saatte dolar (hesap, ölçülmedi). Panel pili
  tamamlar; USB-C şarjı yerinde kalıyor.
- Dizgi satırı her kart için 150 lehim noktası varsayıyor; ekran ve
  yükselteç yaklaşık 40 nokta daha ekler (1000 adette kart başına
  yaklaşık 0,06 $), bu fiyata ayrıca eklenmedi.
- Sitenin Sistem ve Maliyet sayfaları, sunumun 7. ve 15. slaytları ve
  başvuru formunun bütçe alanı yeni fiyatla güncellendi.
