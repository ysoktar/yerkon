# ADR-0097: bağlantı bütçesinde binalar gerçek ayak izleriyle

## Durum

Kabul edildi (proje sahibinin isteği). ADR-0046'nın "zeminin yüzeyi
çatıları da içerir" kararı geçerli; değişen, bir noktanın bir binanın
içinde olup olmadığına nasıl karar verildiği. ADR-0096'nın yayımlanan
satırlarının yerine geçiyor.

## Bağlam

- **Daire.** Bağlantı bütçesi her binayı merkezinin çevresinde bir daire
  olarak okuyordu; yarıçapı, ayak izinin sınır kutusunun ortalama
  kenarının yarısı. Simülatör ise binaları Overture'ın gerçek ayak
  izleriyle çiziyordu (Overture Maps, sürüm 2026-08-19.0). Ekranda görülen
  ile hesaplanan aynı bina değildi.
- **Fark.** Bir daire L biçimli bir binanın avlusunu çatı sayıyor, uzun
  bir binanın uçlarını boş sayıyor. Sahanın binaların kapladığı payı,
  200000 rastgele noktada:

| Saha | Bina | Daireyle | Ayak iziyle |
|---|---|---|---|
| Kızılay | 5231 | %33,73 | %23,38 |
| Polatlı | 20899 | %1,25 | %0,97 |

Daireler Kızılay'ın üçte birini bina sayıyordu; gerçekte dörtte biri.

## Karar

- **Bir bina, ayak izi varsa ayak izidir.** Bir nokta, ayak izinin
  içindeyse (çift-tek kuralı: noktadan çıkan yatay bir ışın sınırı tek
  sayıda keser) o binanın çatısını okur. Ayak izi olmayan bina eskisi gibi
  daire. Dört sahanın bütün binalarının ayak izi var.
- **Hızlı kalıyor.** Hücre ızgarası ayak izinin sınır kutusunu kapsıyor;
  bir hücredeki bütün noktalar hücredeki bütün kenarlarla tek geçişte
  deneniyor. Kızılay'da 200000 noktada 0,27 sn (dairelerle 1,05 sn).
- **Çatı direği çatının üstünde.** L ya da U biçimli bir binanın merkezi
  avlusunda kalabiliyor. Çatı adayı, merkezin yüksekliğinde binayı kesen
  çizginin en geniş çatı parçasının ortasına konuyor
  (`Buildings.roof_point`).
- **Yerleşim aramaları yeniden koşuldu** (`yerkon place --save`): şehir
  içi "daha ucuz", kırsal "daha iyi", ADR-0096'daki gibi.

## Sonuç

- **Yayımlanan satırlar:**

| | Direk | HPE P50 | HPE P95 | VPE P95 | Kullanılabilirlik | Alan km² | CAPEX/km² | OPEX/km²/yıl |
|---|---|---|---|---|---|---|---|---|
| Şehir içi, önce (daire) | 23 | 2,14 | 9,35 | 3,89 | %95,40 | 8,51 | 10658 | 2051 |
| **Şehir içi, şimdi** | 21 | 2,03 | 9,84 | 4,00 | %96,86 | 8,32 | 9949 | 1915 |
| Kırsal, önce (daire) | 50 | 2,00 | 8,22 | 4,97 | %93,34 | 359,58 | 1331 | 335 |
| **Kırsal, şimdi** | 50 | 1,97 | 8,58 | 4,96 | %94,21 | 361,83 | 1322 | 333 |

Tutarlar TL. Şehir içinde arama aynı örtmeyi iki direk eksikle buluyor:
km² başına CAPEX %7, OPEX %7 düştü, kullanılabilirlik 1,5 puan arttı, HPE
P95 0,49 m kötüleşti. Kırsalda binalar az; fark küçük.

- **Arama, aynı zeminde ızgarayla:**

| | Direk | HPE P50 | HPE P95 | Kullanılabilirlik | Alan km² | CAPEX/km² | OPEX/km²/yıl |
|---|---|---|---|---|---|---|---|
| Şehir içi, ızgara | 25 | 1,88 | 9,15 | %97,06 | 8,50 | 11594 | 2231 |
| **Şehir içi, arama** | 21 | 2,03 | 9,92 | %96,98 | 8,32 | 9949 | 1915 |
| Kırsal, ızgara | 49 | 2,06 | 8,93 | %91,73 | 307,08 | 1344 | 414 |
| **Kırsal, arama** | 50 | 1,97 | 8,69 | %94,28 | 362,08 | 1322 | 333 |

Aramanın kendi değerlendirmesi; yayımlanan satırdan farklı gölge
çekilişleriyle, dolayısıyla küçük farklar var.

- **Şehir içinde 4 direk bina içinde.** Şehir içi 21 direğin 5'i ızgara
  noktası; bunlardan 4'ü gerçek ayak izinde bir binanın içinde kalıyor
  (dairelerle 3'tü). Arama ızgara noktalarını her zaman aday tutuyor.
  Onları ayıklamak ya da en yakın sokağa taşımak ayrı bir karar.
- **Kırsal:** 26 yol kenarı, 18 ızgara noktası, 4 mevcut yapı, 1 çatı,
  1 tepe. Şehir içi: 15 yol kenarı, 5 ızgara noktası, 1 mevcut yapı.

## Kaynaklar

- Overture Maps Foundation, buildings teması, sürüm 2026-08-19.0
  (ayak izi geometrisi, WKB).
