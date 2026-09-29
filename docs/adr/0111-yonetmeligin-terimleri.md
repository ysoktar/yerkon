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
