# ADR-0096: şehir içi ve kırsalda alıcılar gerçek yollarda, direkler yerleşim aramasının yerlerinde

## Durum

Kabul edildi (proje sahibinin kararı). ADR-0081'in yerleşim araması
artık tablonun şehir içi ve kırsal satırlarını kuruyor.

## Bağlam

- **Güzergâh.** Şehir içi ve kırsal satırlarda alıcılar, alanın
  çevresinden ve köşegeninden geçen düz çizgileri sürüyordu: binaların ve
  tarlaların içinden. Modeldeki "gerçek yol" güzergâhı getirilmiş yol
  ağının yalnız en uzun kesintisiz parçasını sürüyordu (Kızılay'da 3,2
  km, alanın beşte biri).
- **Izgara.** Şehir içi ızgaranın 25 noktasından 10'u bina içine
  düşüyordu; oraya aydınlatma direği dikilemez.
- **Denenenler,** alıcılar gerçek yollarda, tam çözünürlükte:

| Şehir içi (Kızılay) | Direk | HPE P95 | Kullanılabilirlik | Alan km² | CAPEX/km² | OPEX/km²/yıl |
|---|---|---|---|---|---|---|
| Izgara | 25 | 9,49 | %95,90 | 8,59 | 11477 | 2209 |
| Yolun iki yanı, 450 m | 31 | 9,81 | %95,50 | 8,61 | 14204 | 2734 |
| Arama, daha iyi | 25 | 8,97 | %94,84 | 8,66 | 11388 | 2192 |
| **Arama, daha ucuz** | 23 | 9,16 | %95,30 | 8,51 | 10658 | 2051 |

| Kırsal (Polatlı) | Direk | HPE P95 | Kullanılabilirlik | Alan km² | CAPEX/km² | OPEX/km²/yıl |
|---|---|---|---|---|---|---|
| Izgara | 49 | 8,95 | %90,94 | 305,75 | 1350 | 416 |
| Yolun iki yanı, 2200 m | 48 | 9,46 | %81,68 | 249,33 | 1622 | 500 |
| **Arama, daha iyi** | 50 | 8,30 | %93,40 | 359,58 | 1331 | 335 |
| Arama, daha ucuz | 34 | 9,01 | %88,12 | 308,42 | 1129 | 262 |

Yolun iki yanına tek başına dizmek en kötüsü: direkler birkaç çizgi
üstünde toplanıyor ve yola dik yöndeki konum zayıf ölçülüyor.

## Karar

- **Güzergâh `road`.** Tur köşeleri, getirilmiş yol ağı üstünde
  Dijkstra'nın en kısa yoluyla birleştiriliyor (`routes._road`): Kızılay'da
  19,7 km, Polatlı'da 104,5 km. Ayar: `urban.route`, `rural.route`.
- **Yerleşim `placed`.** Şehir içinde arama "daha ucuz" (ızgaranın
  kapsamasını en az maliyetle), kırsalda "daha iyi" (ızgaranın maliyetiyle
  en çok kapsama) hedefiyle koşuldu. Ayar: `urban.layout`, `rural.layout`.
  - Şehir içi, 23 direk: 16 yol kenarı, 4 ızgara noktası, 3 mevcut yapı.
  - Kırsal, 50 direk: 24 yol kenarı, 20 ızgara noktası, 4 mevcut yapı,
    1 çatı, 1 tepe.
- **Veri olarak saklanıyor.** Arama dakikalar sürüyor; tablo ve
  simülatörün sekmesi onu her seferinde koşamaz. Sonuç
  `src/yerkon/placements/urban.toml` ve `rural.toml`'da; ikisi de oradan
  okuyor (`yerkon.placed`). `yerkon place --scenario urban --aim cheaper
  --save` yeniden yazar. Başka bir zemin seçilirse satır ızgaraya döner.

## Sonuç

- **Yayımlanan satırlar:**

| | HPE P50 | HPE P95 | VPE P95 | Kullanılabilirlik | Alan km² | CAPEX/km² | OPEX/km²/yıl |
|---|---|---|---|---|---|---|---|
| Şehir içi, önce (ızgara, düz çizgi tur) | 1,85 | 5,47 | 3,75 | %85,67 | 8,59 | 11477 | 2209 |
| **Şehir içi, şimdi** | 2,14 | 9,35 | 3,89 | %95,40 | 8,51 | 10658 | 2051 |
| Kırsal, önce (ızgara, düz çizgi tur) | 1,76 | 4,65 | 4,71 | %66,47 | 305,75 | 1350 | 416 |
| **Kırsal, şimdi** | 2,00 | 8,22 | 4,97 | %93,34 | 359,58 | 1331 | 335 |

Tutarlar TL. Şehir içinde km² başına CAPEX %7, OPEX %7 düştü; kırsalda
alan %18 büyüdü, OPEX %19 düştü.

- **Gerçek yollarda kullanılabilirlik yükseldi, HPE P95 kötüleşti.**
  Araç artık sokaklarda; düz çizgi turun binaların içinden geçen
  kısımları yok.
- **Şehir içinde 3 direk hâlâ bina içinde:** aramanın ızgaradan aldığı
  noktalar. Arama ızgara noktalarını her zaman aday tutuyor; bina
  içindekileri ayıklamak bir sonraki adım.
- **Simülatör** gerçek yol ağını ve uydu görüntüsünü gösteriyor; aracın
  güzergâhı yolların üstünde.
