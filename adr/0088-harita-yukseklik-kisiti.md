# ADR-0088: yükseklik haritadan, haritanın kendi hatasıyla

## Durum

Kabul edildi. ADR-0011'in "yükseklik kısıtı yok" kararının yerine geçer.

## Bağlam

Yayımlanan tabloda VPE P95 şehir içinde 72,81 m, kırsalda 115,90 m idi.
Sebep geometri: yayın birimleri yol kenarında birbirine yakın
yükseklikte duruyor, alıcı da yolda. Mesafeler yataydaki konumu iyi
belirliyor, yüksekliği neredeyse hiç. Kalman filtresi zaten vardı;
filtre yüksekliği bilmediğini dürüstçe söylüyordu.

ADR-0011 yükseklik kısıtını bilerek koymamıştı: filtreye gerçek
yüksekliği söylemek, bulması gereken cevabı vermek olurdu. Sunum ise
"harita kısıtı kullanılacaktır" diyor ve proje sahibi VPE'nin
iyileştirilmesini istedi.

## Karar

Her turda filtre bir yükseklik ölçümü alıyor: birimin haritasının,
filtrenin kendini bulduğu yerdeki yol yüksekliği, artı anten yüksekliği.

- **Gerçek değil, harita.** Harita, filtrenin tahmin ettiği konumda
  sorgulanıyor; yataydaki hata eğimli bir yolda yükseklik hatasına
  dönüyor, gerçek bir alıcıda olduğu gibi. Harita en yakın yol noktasını
  alıyor; bir döngüde bu başka bir turun aynı yolu olabilir.
- **Haritanın hatası.** Copernicus DEM'in yayımlanmış mutlak düşey
  doğruluğu < 4 m (LE90); normal dağılımda 4 / 1,645 = 2,43 m, bir
  sigma. Hata yol boyunca her 500 m'de bir çekiliyor ve çeyrek çember
  ağırlıklarıyla birleştiriliyor, böylece her noktada aynı büyüklükte
  kalıyor. 500 m'yi bir araç yarım dakikada geçiyor; filtrenin düşey
  belleğinden uzun, yani hata filtre için bir sapma gibi ve ortalamayla
  silinmiyor.
- **Kendi rastgele akışı.** Harita hatası ayrı bir tohumdan; kısıt açılıp
  kapandığında hiçbir mesafe çekilişi yer değiştirmiyor.
- `estimator.height_aid_sigma_m` = 2,43 (0 kısıtı kapatır),
  `estimator.height_aid_correlation_m` = 500.

## Ölçüm

400 saniyelik yolculuklar, tek gölge çekilişi:

| Satır | Kısıt | HPE P50 | HPE P95 | VPE P95 | Kullanılabilirlik |
|---|---|---|---|---|---|
| Şehir içi | yok | 2,32 | 7,09 | 65,50 | %78,66 |
| Şehir içi | 2,43 m | 2,04 | 6,13 | 2,98 | %81,27 |
| Kırsal | yok | 2,44 | 6,89 | 126,68 | %66,88 |
| Kırsal | 2,43 m | 2,16 | 5,66 | 3,00 | %73,38 |
| Tünel | yok | 0,83 | 3,18 | 3,54 | %100,00 |
| Tünel | 2,43 m | 0,81 | 2,77 | 1,85 | %100,00 |

(Bu ön koşuda harita hatası düğümler arasında küçülüyordu; düzeltildi.
Yayımlanan sayılar düzeltilmiş hâlle koşuldu.)

## Sonuçlar

- VPE onlarca metreden birkaç metreye iniyor; yataydaki hata ve
  kullanılabilirlik de iyileşiyor, çünkü yükseklikteki belirsizlik
  yataya sızıyordu.
- Sonuç haritaya dayanıyor. Haritası olmayan ya da yoldan çıkan bir
  birim (yaya bir binaya girdiğinde) bu kısıtı kullanamaz; o durum
  modelde yok.
- Tünelde yol yüksekliği tünelin proje profilinden gelir ve DEM'den
  daha iyidir; aynı 2,43 m kullanıldı, ihtiyatlı taraf.
