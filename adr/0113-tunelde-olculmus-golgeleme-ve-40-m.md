# ADR-0113: Tünelde ölçülmüş gölgeleme payı ve 40 m aralık

## Durum

Kabul edildi (proje sahibinin kararı, 29 Eylül 2026). ADR-0095'in 60 m
aralık kısmının yerini alıyor; kanal 5 ve 1,2 m yükseklik geçerli.

## Bağlam

Tünel, gölgeleme payını açık havadan alıyordu: 3GPP TR 38.901'in görüş
hattı için verdiği 4 dB. Tünelin ortalama kaybını veren ölçüm
(Molina-Garcia-Pardo, Lienard, Degauque, EURASIP JWCN 2009, §3.1) aynı
tünelde ölçülen kaybın modelden sapmasını da veriyor: 2,7 dB standart
sapma (Denklem 3).

Tünelde kayıp 50 m'den sonra mesafeyle çok yavaş artıyor (üs 0,57).
60 m aralıkta en yakın komşunun ortanca payı tam 0,0 dB; 120 m'dekininki
-1,7 dB, 300 m'dekininki -4,0 dB. Kapsamanın deseni bu yüzden her yerde
aynı değil: her bağlantı yazı tura. 4 dB'lik açık hava sapması uzaktaki
birimlerin bir kısmını şansla kapatıyordu ve kullanılabilirliği
yükseltiyordu.

## Karar

- Tünel satırı kendi ölçülmüş sapmasını kullanıyor:
  `tunnel.shadow_sigma_db` = 2,7 dB. Diğer satırlar 4 dB'de kalıyor.
- Birimler 40 m arayla, iki duvara sırayla.

Tam çözünürlükte, 2,7 dB ile:

| Aralık | HPE P95 | Kullanılabilirlik | CAPEX [TL/km] |
|---|---|---|---|
| 40 m | 1,08 m | %99,55 | 162442 |
| 45 m | 1,13 m | %91,04 | 143331 |
| 50 m | 1,28 m | %88,82 | 130590 |
| 60 m | 1,93 m | %84,07 | 108294 |

## Sonuç

Tünel satırı HPE P50 0,37 m, P95 1,08 m, VPE P95 2,57 m, %99,55; km
başına 162442 TL kurulum, 33160 TL/yıl işletme. 60 m'ye göre %50 daha
pahalı, ama tünelin her yerinde konum veriyor.
