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

## EN 300 328 V2.2.2'nin koşulları (ETSI, 2019-07)

- **Uyarlamasız FHSS** (10 dBm e.i.r.p.'nin üstünde): en uzun yayın
  dizisi 5 ms, en kısa ara 5 ms (4.3.1.3); her atlama frekansında 15 ms x
  N içinde en çok 15 ms (4.3.1.4.3.1); havayı meşgul etme payı
  MU = (P / 100 mW) x DC <= %10 (4.3.1.6).
  **YERKON için kapalı:** SF10 ve 1625 kHz'de bir ölçüm paketi yaklaşık
  15 ms sürüyor, 5 ms'yi aşıyor; araç da sürekli sorduğu için %10'u
  aşıyor. Paketi 5 ms'ye sığdırmak için SF7'ye inmek yaklaşık 7,5 dB
  duyarlılık kaybettiriyor, 20 dBm'nin kazandırdığını geri alıyor.
- **Uyarlamalı FHSS, dinle-sonra-konuş (LBT)** (4.3.1.4.3.2, 4.3.1.7.2.2):
  bandın en az %70'inde çalışabilmeli; her atlama frekansında 400 ms x N
  içinde en çok 400 ms; her bekleme başında enerji algılamalı kanal
  kontrolü (en az 18 us ve kanal kullanım süresinin %0,2'si, eşik 20 dBm
  için -70 dBm/MHz); kanal kullanım süresi 60 ms'den kısa, ardından onun
  en az %5'i kadar sessizlik. Bir ölçüm alışverişi 31,8 ms, 60 ms'ye
  sığıyor. **YERKON için tek açık yol bu.** Modelde turu %5 uzatan
  sessizlik payıyla koşuluyor.

## BTK

BTK, 5 Şubat 2021'den beri piyasaya arz öncesi Sınıf 2 bildirim
başvurusu almıyor. Telsiz Ekipmanları Yönetmeliği kapsamında ayrı bir
BTK başvurusu ya da ücreti yok. Üretici CE işareti, AB uygunluk beyanı
ve temel gereklere uygunluktan sorumlu; kutuda kısa ya da uzun uygunluk
beyanı bulunmalı. Bedel yalnız laboratuvar testleri.

## Açık

- Test ücreti (EN 300 328, EN 301 489-1/-17, EN 62368-1): TSE'nin
  sorgusu CAPTCHA istiyor, TÜBİTAK UME teklifle çalışıyor; yayımlanmış
  bir fiyat bulunamadı.
- Kanal kontrolünü yanıt veren direk de mi yapmalı, yoksa sorunun
  kanal kullanım süresi içinde cevap verebilir mi: standardın ilgili
  maddesi okunmalı. Her iki ucun da kontrol yapması gerekirse tur biraz
  daha uzar.
- Şehir içinde 2,4 GHz Wi-Fi yoğun; -70 dBm/MHz eşiği sık sık kanalı dolu
  gösterebilir. Bu, paket kaybını artırır. Sahada SDR kaydıyla
  (ADR-0083) ölçülmeli.
