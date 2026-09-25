# ADR-0091: SX1280'in resmî duyarlılığı ve menzili geri kazandıran antenler

## Durum

Kabul edildi (proje sahibinin kararı, 24 Eylül 2026). Duyarlılık kararı
geçerli; direk ve araç antenlerinin yerini ADR-0094'teki 5 dBi çubuk
anten aldı.

## Bağlam

Model SX1280'in SF10 ve 1625 kHz'de -125,9 dBm'ye kadar duyduğunu
varsayıyordu: 6 dB gürültü sayısı ve "veri sayfası, SF10" diye
etiketlenmiş -20 dB'lik bir eşik. O eşik SF12'ninkine benziyordu ve
resmî bir kaynaktan doğrulanamadı. Veri sayfasının SF10/1625 kHz satırı
da resmî kaynaktan bulunamadı.

Semtech'in kendi ürün sayfasındaki tek resmî nokta: en iyi duyarlılık
-132 dBm (SF12, 203 kHz). Bant genişliği 1625 kHz'e çıkınca +9,03 dB,
SF12'den SF10'a +5 dB (LoRa'da her adım 2,5 dB): SF10 ve 1625 kHz'de
-117,97 dBm. Model yaklaşık 8 dB iyimserdi.

Bu 8 dB, kısa bir koşuda şehir içi kullanılabilirliği %81'den %62'ye,
kırsalı %73'ten %48'e indiriyordu. Proje sahibi menzili geri kazanacak
bir anten istedi.

## Karar

**Duyarlılık resmî değerden.** `radio.sx1280.demodulation_threshold_db`
= -12,08 dB (türetilmiş); model -118,0 dBm'de kapanıyor.

**Anten yalnız alışta kazandırır, ve yasaldır.** Türkiye sınırı
(12,1 dBm e.i.r.p., 1625 kHz'de yoğunluk sınırı) anten kazancını da
içeriyor: daha güçlü bir antenle yayın yapan cihaz gücünü o kadar
kısmak zorunda. Alışta böyle bir sınır yok. Her mesafe ölçümü iki yönlü
(birim sorar, direk cevaplar), bu yüzden anten iki uçta da gerekiyor.

**Seçilen antenler (üretici değerleri):**

| Yer | Anten | Kazanç | Düşey hüzme | Kablo kaybı | Fiyat |
|---|---|---|---|---|---|
| Direk (şehir içi, kırsal) | TP-Link TL-ANT2412D | 12 dBi | 6,5° | 0,47 dB | 50,66 USD |
| Araç çatısı (şehir içi, kırsal) | L-com HGV-2409U | 8 dBi | 16,8° | 0,47 dB | 58,95 USD |
| Yaya, tünel | Inventek W24P-U (değişmedi) | 3,2 dBi | geniş | 0 | 1,48 USD |

- Düşey hüzme McDonald'ın çok yönlü anten yaklaşımıyla kazançtan
  türetildi (TL-ANT2412D'nin veri sayfası "en çok 12°" diyor; daha dar
  olan temkinli okuma). Desen 3GPP TR 36.814'ün düşey deseni: hüzmenin
  yarısında 3 dB, en çok 20 dB aşağı. Direğin dibindeki araç zayıf
  duyuluyor, bu modelde var.
- Kablo: 0,3 m LMR-200 (Times Microwave: 2,5 GHz'de 100 ft'de 16,9 dB)
  ve iki konnektör (0,15 dB, varsayım). Araçta telsiz çatıda antenin
  yanındaki kutuda, kabine CAN hattıyla bağlı; birim bu hattı zaten
  taşıyor. 3 m kabloyla kabine inmek 1,96 dB ve kullanılabilirlikte üç
  puan kaybettiriyordu.
- Kablo fiyatı: 9,50 USD (genel bir LMR-200 kablo ilanı).
- Yaya bir direk anteni taşıyamaz; küçük anteninde kalıyor.
- Tünel UWB ile ölçüyor; değişmedi.

**Yasal sınır antenin tepesinde ölçülüyor.** Model sınırı alıcıya doğru
kazançla uyguluyordu; dar hüzmeli bir anten bu yüzden kendi tepesinde
sınırı aşabilirdi. Artık güç, sınır hüzmenin tepesinde tutacak şekilde
ayarlanıyor; alıcıya doğru ne düşüyorsa o.

## Ölçüm (400 s, tek çekiliş, karşılaştırma için)

| Hâl | Şehir içi kullanılabilirlik | Kırsal |
|---|---|---|
| Eski duyarlılık (-125,9), küçük antenler | %81,3 | %73,4 |
| Resmî duyarlılık (-118), küçük antenler | %61,5 | %47,7 |
| Resmî duyarlılık, direk 12 dBi, araç 8 dBi, araçta 3 m kablo | %76,9 | %67,3 |
| Resmî duyarlılık, aynı antenler, telsiz çatıda | %79,5 | %70,6 |

## Sonuçlar

- Menzil büyük ölçüde geri geliyor; yaya bağlantıları küçük antende
  kaldığı için tamamı gelmiyor.
- Maliyet artıyor. Şehir içi ve kırsal yayın biriminin fiyatına anten ve
  kablo ekleniyor (1000 adet kademesinde birim 718 TL'den yaklaşık
  2480 TL'ye). Araç alıcısına çatı anteni ekleniyor.
- Fiyatlar perakende ilanlardan; toplu alım teklifleri düşürür.
- Maliyetsiz bir yol daha var: SX1280'in mesafe ölçümü doğruluk için
  kanal atlıyor. Sistem frekans atlamalı olarak belgelendirilirse
  Türkiye sınırı 12,1 dBm'den 20 dBm'ye çıkar, bu da tek başına
  yaklaşık 8 dB. BTK ya da bir test laboratuvarının onayı gerekir.
