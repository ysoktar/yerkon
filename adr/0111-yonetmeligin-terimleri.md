# ADR-0111: 2,4 GHz kuralı yönetmeliğin terimleriyle ve bağlantılarıyla

## Durum

Kabul edildi (proje sahibinin kararı, 29 Eylül 2026).

## Bağlam

Site 2,4 GHz kipini "uyarlamalı frekans atlama (dinle, sonra konuş)"
diye anlatıyordu ve sınırları dBm ile veriyordu. Bu sözcükler
yönetmelikte geçmiyor. BTK'nın Frekans Tahsisinden Muaf Telsiz Cihaz ve
Sistemlerine İlişkin Teknik Ölçütleri sınırları mW ile veriyor ve kendi
terimlerini tanımlıyor.

## Karar

- Site yönetmeliğin terimlerini kullanır: Frekans Atlamalı Spektrum
  Yayılımı (FHSS), Göndermeden Önce Dinle (LBT), Algıla ve Kaçın (DAA),
  e.i.r.p. Tanımlar Madde 1'den, sözü sözüne yakın.
- 2,4 GHz sınırı Madde 5, Tablo 3, satır 3'ten: 2400-2483,5 MHz, en çok
  100 mW e.i.r.p.; yeterli spektrum paylaşım mekanizması (örneğin LBT,
  DAA); referans standart TS EN 300 328; FHSS'te en çok 100 mW/100 kHz,
  FHSS dışındaki genişband modülasyonlarda en çok 10 mW/MHz. dBm karşılığı
  parantez içinde.
- Kanal kontrolü, süreler ve eşikler TS EN 300 328'den geliyor ve öyle
  yazılıyor; Madde 2 referans standarda en az eş değer teknik istiyor.
- Mevzuat sayfasındaki madde ve tablo atıfları BTK belgesinin ilgili
  sayfasına bağlanıyor (`#page=N`).

## Sonuç

Model değişmedi: sınırlar zaten bunlardı (20 dBm = 100 mW, 10 dBm/MHz =
10 mW/MHz). Simülatördeki bölge ve kurulum adları, Sistem sayfası, sunum
ve başvuru formu aynı terimlere geçti.

## Ek: birim birim yasal güç (29 Eylül 2026)

- Mevzuat sayfasına 2,4 GHz birimlerinin yasal güç tablosu eklendi:
  E28-2G4M20S'nin çıkışı EBYTE'nin veri sayfasından (19 / 20 / 21 dBm),
  her birimin anteni, tam güçteki e.i.r.p. ve sınırı aşmayan en yüksek
  ayar (FHSS ve LBT ile 20 dBm, FHSS olmadan 12,1 dBm e.i.r.p.).
- Anten takmak yasal: TS EN 300 328 cihazın o antenle test edilmesini ve
  hiçbir güç ayarının sınırı aşmamasını istiyor (4.2.4, 4.3.1.2). 20S
  5 dBi antenle en çok 15,3 dBm'ye kısılıyor; anten yayında değil alışta
  kazandırıyor (ADR-0100).
- BTK bağlantısı BTK'nın sayfasındaki güncel dosyaya geçti (Kurul Kararı
  23.09.2022, 2022/İK-SYD/245); metni önceki dosyayla aynı.
- Seçenek modüller (12S, 27S, O4) sitede değil, yalnız tarayıcıdaki
  simülatörde; onların yasal gücü yerel rapordadır.
