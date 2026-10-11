# ADR-0108: sitenin bölümleri yerinde toplanır, tekrarlar kalkar

## Durum

Kabul edildi (proje sahibinin onayıyla, 28 Eylül 2026). Menünün sırası
değişmedi.

## Bağlam

Bazı bölümler iki sayfada birden duruyordu, bazıları da okuyanın
beklediği sayfada değildi:

- Maliyet sayfası açıkken yaklaşık 24000 piksel uzunluğundaydı; çoğunu
  kartların parça parça dökümü ile her sayının dayanağı tutuyordu.
- Sistem sayfasındaki fiyat tablosu Maliyet sayfasındakinin kopyasıydı.
- Mevzuat sayfasında direk boyları Maliyet'teki direk fiyatları
  tablosuyla aynı bilgiyi yeniden veriyordu. Kurulum ve bakım maliyetinin
  dayandığı kurallar ise telsiz kurallarıyla aynı düzeyde, ayrı ayrı
  duruyordu.
- "Hızlı okuma" simülatörün bir düğmesini anlatıyordu ama Sonuçlar
  sayfasındaydı.
- Fayda sayfasında ticarileşmeyle ilgili üç bölüm başlıksız, öteki
  faydaların arasında kalıyordu.

## Karar

- Maliyet: "Her kartın parçaları" ile "Her sayının dayanağı" kapalı
  açılıyor; başlığa tıklayınca açılıyor. Sayfa kapalıyken yaklaşık 4900
  piksel.
- Sistem: fiyat tablosu yerine tek cümle var: 1000 adette yayın birimi
  yaklaşık 1400-1700 lira, alıcı yaklaşık 2300-3300 lira; 1, 100 ve 1000
  adetlik tablo Maliyet sayfasında.
- Mevzuat: harcırah, bakım maliyeti, direk boyu ve birimin yeri, kamu
  yapısında yer kullanımı ve harita ile uydu görüntüsü "Kurulumun ve
  maliyetin dayandığı mevzuat" başlığı altında alt bölüm oldu. Direk
  boylarını anlatan cümle, fiyatların Maliyet sayfasında olduğunu
  söylüyor.
- "Hızlı okuma" Simülasyon sayfasına, "Tarayıcıda ve kendi makinende"
  bölümünün arkasına taşındı.
- Fayda: "Kendini nasıl döndürür", "Uzun vadede" ve "Ürünler",
  "Ticarileşme" başlığı altında toplandı; sayfanın girişi bunun sonda
  olduğunu söylüyor.
- Alt bölümün başlığı büyük harfle değil, normal yazılıyor; üstteki
  büyük harfli başlık grubun adı olarak okunuyor.

## Sonuç

Hiçbir sayı değişmedi; yalnız yerleri ve başlıkları değişti. Aynı bilgi
artık tek bir sayfada duruyor, öteki sayfa oraya yönlendiriyor.
