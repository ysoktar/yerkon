# 0009. Bir değişiklik ve zorladığı her şey birlikte onaylanır

## Durum
Kabul edildi.

## Bağlam
Bu projedeki ayarların çoğu bağımsız değil. Bölgeyi değiştirmek yasal
yayılan gücü, o da bir bağlantının tolerans içinde ne kadar uzağa
ölçebildiğini, o da direklerin ne kadar aralıklı durabileceğini, o da kaç
tane olduklarını ve neye mal olduklarını değiştirir. Montaj yapısını ya da
hedef hassasiyeti değiştirmek aynı zinciri tetikler.

Gerisini sessizce yeniden hesaplayan bir araç, bir maliyet değerini okuyan
birini, ayarlarının hangisinin onu ürettiğini bilmeden bırakırdı. Her sonucu
ayrı ayrı onaylatan bir araç ise tek bir düzenleme için dört soru sorardı ve
ikinciyi cevaplayan kişi dördüncünün ne olacağını henüz bilmezdi.

## Karar
Bir düzenleme bir onay üretir. Panel değişecek her değeri listeler —
istenen ve ondan çıkan her biri — her birini eski değeri, yeni değeri ve
türetilmiş olanlar için neden takip ettiğiyle. Cevap tek bir evet/hayırdır
ve evet gelene kadar hiçbir şey uygulanmaz.

Türetilmiş değerler benzetimin kullandığı fonksiyonların kendisiyle
hesaplanır. Neyin neyi zorladığını söyleyen ayrı bir kural tablosu yoktur:
sonuçlar fizikten okunur ve onları yalnızca ilan edilmiş değil doğru kılan
budur. ADR-0002'ye bak.

Panel, tek bir tanım üreten tek bir fonksiyondur ve hem komut satırı hem
uygulama onu çizer. ADR-0001'e bak.

## Sonuçlar
Sonuçları kabul edilemez olan bir düzenleme, hiçbir şey değişmeden önce
reddedilir; yani geri alınacak yarı uygulanmış bir durum olmaz.

Panel model büyüdükçe büyür. Kestirici geldiğinde zincir, ölçüm
hassasiyetinden geometri üzerinden konum hatasına uzanır ve aynı onay, nasıl
cevaplandığında hiçbir değişiklik olmadan yeni halkaları gösterir.

Toplu bir cevap bazı sonuçları kabul edip bazılarını reddedemez. Bu
bilerektir: sonuçlar isteğe bağlı değildir, ayarların anlamının ta
kendisidir. Birini reddetmek, fiziği ezmek değil, farklı ayarlar seçmek
demektir.
