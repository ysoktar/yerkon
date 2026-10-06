# ADR-0112: Adreslerde ".html" yok; her dil ve her sayfa kendi klasöründe

## Durum

Kabul edildi (proje sahibinin isteği, 29 Eylül 2026).

## Bağlam

Site yerkon.com alan adına bağlandı. Adresler `sistem.html` gibi dosya
adlarıydı; Türkçe kökte, İngilizce `en/` altındaydı. Yayın dalı her
seferinde `docs/`'tan sıfırdan itildiği için GitHub'ın özel alan adını
tuttuğu `CNAME` dosyası da her yayında siliniyordu.

## Karar

- Her dil kendi klasöründe, her sayfa kendi klasöründe: `tr/`,
  `tr/sistem/`, `en/sistem/`. Adres hiçbir yerde ".html" ile bitmiyor.
- Simülatör `calistir/` altında. Sayfası kökteki dosyaları `<base>` ile
  yüklüyor; betikler, hesap motoru ve paket yerinde kalıyor.
- Kök `tr/`'ye yönlendiriyor. Eski her adres (`sistem.html`,
  `en/sistem.html`, `calistir.html?dil=en`) yenisine yönlendiren küçük
  bir sayfa olarak kalıyor; paylaşılmış bağlantılar kırılmıyor.
- `CNAME` (yerkon.com) sayfalarla birlikte üretiliyor.
- Bağlantılar göreli; klasör hem alan adının kökünde hem kendi yolu
  altında çalışıyor.

## Sonuç

HTTPS için ayrıca iki şey gerekiyor: `www` kaydının doğru hedefi
(`ysoktar.github.io`) ve GitHub Pages ayarında "Enforce HTTPS".
