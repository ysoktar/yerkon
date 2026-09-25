# ADR-0092: frekans atlamalı belgelendirme bir seçenek olarak

## Durum

Önerildi. Kural modelde (`TR-FHSS`), tabloya uygulanmadı; seçim ve belge
ücreti proje sahibinin.

## Bağlam

Türkiye'de 2,4 GHz için TS EN 300 328 geçerli. Frekans atlamalı olmayan
cihazlarda yoğunluk sınırı (10 dBm/MHz) SX1280'in 1625 kHz'lik
dalgasında gücü 12,1 dBm e.i.r.p.'ye bağlıyor. Frekans atlamalı (FHSS)
olarak belgelendirilen cihazda yalnız 20 dBm e.i.r.p. sınırı var.
SX1280'in mesafe ölçümü doğruluk için zaten kanal atlıyor.

## Karar

`regulatory.TURKEY_FREQUENCY_HOPPING` ("TR-FHSS"): 20 dBm e.i.r.p.,
yoğunluk sınırı yok. Bu kuralla direk ve araç birimleri 27 dBm'lik
E28-2G4M27S modülüne geçiyor; yaya E28-2G4M12S'de kalıyor.

Yedi seçenek tam çözünürlükte koşuldu (`docs/ANTEN-KARSILASTIRMASI.md`).
Baskılı antenle bile FHSS, şehir içi kullanılabilirliği %66,55'ten
%84,26'ya, kırsalı %49,13'ten %64,80'e çıkarıyor ve şehir içinde km²
başına en düşük CAPEX'i veriyor.

## Açık

- Belge ücreti (akredite laboratuvarda EN 300 328 testi): bulunamadı.
- EN 300 328'in FHSS koşulları (bekleme süresi, havayı meşgul etme payı
  ya da dinle-sonra-konuş): cihazın bunları karşıladığı laboratuvarda
  görülmeli. Karşılamazsa bu seçenek geçersiz.
