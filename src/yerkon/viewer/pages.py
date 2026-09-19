"""Everything the site says, in both languages, and how it is drawn.

The simulator is a page for somebody already inside the study: it opens
onto a slider for the noise figure. Anybody else needs to be told what
YERKON is, what this project measured, and what the measurement does not
cover, before a slider means anything.

So the same server carries a small site in front of the simulator. The
pages are rendered here rather than written as files, for two reasons.
A page that shows the published table has to read it from the run that
produced it (`published.py`) instead of carrying a typed copy. And the
language belongs to the person rather than to the page, so one set of
words is drawn in whichever language the session is set to, the same
way the panel's are (ADR-0035, ADR-0064).

Nothing here computes anything. Every number on the results page comes
out of the published record; every other figure quoted in the prose is a
measurement this repository records, with the decision it came from.
"""

from __future__ import annotations

import html
import re
from dataclasses import dataclass
from typing import Optional, Sequence

from yerkon.numbers import decimal_comma


@dataclass(frozen=True)
class Words:
    """One phrase, in both languages.

    Both are required. A page half in Turkish is the failure ADR-0035
    was written about, and a dataclass with two fields makes a test for
    it one line long.
    """

    tr: str
    en: str

    def said(self, language: str) -> str:
        return self.en if language == "en" else self.tr


@dataclass(frozen=True)
class Link:
    """Somewhere else, with what it is called."""

    label: Words
    url: str


@dataclass(frozen=True)
class Part:
    """One piece of a page.

    ``kind`` decides how it is drawn: paragraphs, a list, a table whose
    first row is its head, a block of commands, links, or a named thing
    the renderer fills from the published record.
    """

    kind: str
    heading: Optional[Words] = None
    lines: tuple[Words, ...] = ()
    rows: tuple[tuple[Words, ...], ...] = ()
    links: tuple[Link, ...] = ()
    #: A block of commands. The commands are the same in both languages
    #: and the comments beside them are not, so it is a phrase like the
    #: rest of the page rather than one string.
    code: Optional[Words] = None
    shows: str = ""


@dataclass(frozen=True)
class Page:
    """One address on the site."""

    #: The address under the root. Empty for the home page.
    slug: str
    #: What the navigation calls it.
    nav: Words
    title: Words
    lead: Words
    parts: tuple[Part, ...] = ()


def _w(tr: str, en: str) -> Words:
    return Words(tr=tr, en=en)


# --- what the site says ---------------------------------------------------

HOME = Page(
    slug="",
    nav=_w("Anasayfa", "Home"),
    title=_w("YERKON benzetimi", "The YERKON simulation"),
    lead=_w(
        "YERKON, yabancı uydu sistemleri kesildiğinde ya da yanıltıldığında "
        "konum üretmeyi sürdüren karasal bir yedek katman önerisidir. Bu "
        "site, o ağın ne verdiğini ve neye mal olduğunu ölçen benzetimi "
        "anlatır ve tarayıcıda çalıştırır.",
        "YERKON is a proposed terrestrial layer that keeps producing a "
        "position when foreign satellite systems are jammed or spoofed. "
        "This site describes the simulation that measures what such a "
        "network delivers and what it costs, and runs it in the browser.",
    ),
    parts=(
        Part(kind="shows", shows="headline"),
        Part(
            kind="text",
            heading=_w("Tek bir çıktı", "One output"),
            lines=(
                _w(
                    "Bu projenin tek çıktısı, raporun 15. sayfasındaki "
                    "karşılaştırma tablosunun YERKON bloğudur: dört satır, "
                    "on sütun. Her sayı ya bir veri sayfasına, ya "
                    "yayımlanmış bir ölçüme, ya da açıkça yazılmış bir "
                    "varsayıma kadar izlenir.",
                    "This project produces one thing: the YERKON block of "
                    "the comparison table on page 15 of the report, four "
                    "rows and ten columns. Every number traces back to a "
                    "datasheet, a published measurement, or an assumption "
                    "written down where it can be argued with.",
                ),
                _w(
                    "Sayılar bir iddia değil, bir koşunun çıktısıdır. Aynı "
                    "koşuyu simülasyondan kendin başlatabilir, bir direği "
                    "taşıyıp sonucun ne yaptığına bakabilirsin.",
                    "The numbers are the output of a run rather than a "
                    "claim. You can start the same run yourself from the "
                    "simulator, move an anchor, and watch what the answer "
                    "does.",
                ),
            ),
        ),
        Part(
            kind="points",
            heading=_w("Üç senaryo", "Three scenarios"),
            lines=(
                _w(
                    "**Şehir içi**: Kızılay, bir kenarı üç kilometre olan "
                    "gerçek zemin, aydınlatma direklerine monte SX1280 "
                    "yayın birimleri.",
                    "**Urban**: Kızılay, three kilometres of real ground "
                    "on a side, SX1280 anchors bolted to lighting columns.",
                ),
                _w(
                    "**Kırsal**: Polatlı ovası, bir kenarı yirmi "
                    "kilometre, yüksek direklerde E28-SX1280.",
                    "**Rural**: the Polatlı plain, twenty kilometres on a "
                    "side, E28-SX1280 on tall masts.",
                ),
                _w(
                    "**Tünel**: Kızılcahamam'da dağın içinden geçen gerçek "
                    "bir 2 km'lik güzergâh, tavana asılı DWM3000 UWB.",
                    "**Tunnel**: a real two kilometre bore through the "
                    "mountains at Kızılcahamam, DWM3000 UWB on brackets.",
                ),
            ),
        ),
        Part(kind="map", heading=_w("Sayfalar", "Pages")),
        Part(
            kind="text",
            heading=_w("Bu sayıların sınırı", "What these numbers are"),
            lines=(
                _w(
                    "Benzetim yalnızca radyo menzil ölçümünü çözer. IMU, "
                    "odometri, harita kısıtı ve sensör füzyonu yoktur, ki "
                    "raporun mimarisi bunları öngörüyor. Dolayısıyla "
                    "buradaki sayılar bir taban, bir üst sınır değil.",
                    "The simulation solves radio ranging and nothing else. "
                    "There is no inertial unit, no odometry, no map "
                    "constraint and no sensor fusion, all of which the "
                    "report's architecture calls for. So read these "
                    "numbers as a floor rather than as a ceiling.",
                ),
            ),
        ),
    ),
)

WHY = Page(
    slug="sorun",
    nav=_w("Sorun", "The problem"),
    title=_w("GNSS neden yetmiyor", "Why GNSS is not enough"),
    lead=_w(
        "Konum, seyrüsefer ve hassas zamanlama hizmetlerinin büyük bölümü "
        "GPS, Galileo, GLONASS ve BeiDou'dan gelir. Dördü de yabancı "
        "devletlerin kontrolündedir ve dördü de aynı zayıflığı paylaşır: "
        "uydudan gelen sinyal yere vardığında çok zayıftır.",
        "Most positioning, navigation and timing comes from GPS, Galileo, "
        "GLONASS and BeiDou. All four are controlled by foreign states, "
        "and all four share one weakness: the signal is very weak by the "
        "time it reaches the ground.",
    ),
    parts=(
        Part(
            kind="points",
            heading=_w("Kırılganlıklar", "Where it breaks"),
            lines=(
                _w(
                    "Tünelde, kapalı alanda ve kentsel kanyonda sinyal "
                    "kaybolur.",
                    "The signal is lost in tunnels, indoors and in urban "
                    "canyons.",
                ),
                _w(
                    "Düşük güçlü sinyal karıştırmaya açıktır ve elektronik "
                    "harp ürünleri yaygınlaşıyor.",
                    "A weak signal is easy to jam, and jamming equipment "
                    "keeps getting cheaper.",
                ),
                _w(
                    "Sahte sinyal yanlış bir konum üretir, üstelik alıcı "
                    "onu tutarlı ve yüksek güvenli bir konum olarak "
                    "gösterir.",
                    "A spoofed signal produces a wrong position, and the "
                    "receiver reports it as a consistent one with high "
                    "confidence.",
                ),
                _w(
                    "Kritik hizmetler tek bir teknoloji ailesine bağlıdır.",
                    "Critical services depend on a single family of "
                    "technology.",
                ),
                _w(
                    "Kriz anında sistem üzerindeki karar yetkisi Türkiye'de "
                    "değildir.",
                    "In a crisis, nobody in Turkey decides what the system "
                    "does.",
                ),
            ),
        ),
        Part(
            kind="points",
            heading=_w("Dünyadan örnekler", "What has already happened"),
            lines=(
                _w(
                    "**ABD, Mayıs 2026.** Roswell'den kalkan bir ambulans "
                    "uçağı askeri GPS karıştırmasına maruz kaldı ve "
                    "Ruidoso'ya varamadan bir dağa çarptı.",
                    "**United States, May 2026.** An air ambulance out of "
                    "Roswell flew into military GPS jamming and hit a "
                    "mountain short of Ruidoso.",
                ),
                _w(
                    "**Baltık, Nisan 2024.** Finnair, Tartu uçuşlarını bir "
                    "ay boyunca durdurdu. Havalimanının yalnızca GPS "
                    "tabanlı yaklaşma sistemi vardı.",
                    "**The Baltic, April 2024.** Finnair stopped flying to "
                    "Tartu for a month. The airport had only a GPS based "
                    "approach.",
                ),
                _w(
                    "**Norveç, 2019'dan bu yana.** Finnmark'taki düzenli "
                    "karıştırma, polis, ambulans ve kurtarma ekiplerinin "
                    "navigasyonunu defalarca kör etti.",
                    "**Norway, 2019 onwards.** Steady jamming over "
                    "Finnmark has repeatedly blinded police, ambulance and "
                    "rescue navigation.",
                ),
                _w(
                    "**Karadeniz, 2017.** Yirmiden fazla geminin alıcısı, "
                    "gemiler denizin ortasındayken konumu 40 km içerideki "
                    "bir havalimanında gösterdi.",
                    "**The Black Sea, 2017.** Receivers on more than twenty "
                    "ships put them at an airport 40 km inland while they "
                    "were at sea.",
                ),
            ),
        ),
        Part(
            kind="text",
            heading=_w("YERKON'un cevabı", "What YERKON answers"),
            lines=(
                _w(
                    "YERKON GNSS'in yerine geçmeyi hedeflemez. Mevcut "
                    "ulaşım altyapısına takılan yayın birimlerinden "
                    "bağımsız bir konum üretir. GNSS çalışırken de işe "
                    "yarar: iki cevap yan yana konduğunda aldatma "
                    "görünür hale gelir.",
                    "YERKON does not try to replace GNSS. It produces an "
                    "independent position from units bolted to transport "
                    "infrastructure that is already standing. It is useful "
                    "while GNSS works too: put the two answers side by "
                    "side and spoofing becomes visible.",
                ),
                _w(
                    "Yukarıdaki dört olayın kaynakları raporun "
                    "kaynakçasındadır. Bu sayfa raporun anlattığını "
                    "özetler; bu depo onlardan hiçbirini ölçmedi.",
                    "The four events above are sourced in the report's "
                    "bibliography. This page summarises what the report "
                    "says; this repository measured none of them.",
                ),
            ),
        ),
    ),
)

SYSTEM = Page(
    slug="sistem",
    nav=_w("Sistem", "The system"),
    title=_w("YERKON nasıl kurulur", "How YERKON is built"),
    lead=_w(
        "YERKON üç parçadır: ölçülmüş konumlarda duran yayın birimleri, "
        "konumunu kendi hesaplayan alıcılar, ve kimlikleri güncel tutan "
        "merkezi yönetim sistemi.",
        "YERKON has three parts: broadcast units standing at surveyed "
        "positions, receivers that work out their own position, and a "
        "management system that keeps the identities current.",
    ),
    parts=(
        Part(
            kind="points",
            heading=_w("Üç parça", "Three parts"),
            lines=(
                _w(
                    "**Yayın birimi.** Kule, yol kenarı ünitesi, trafik "
                    "ışığı ya da tünel aydınlatması gibi zaten duran bir "
                    "noktaya takılan düşük maliyetli verici. Kendi "
                    "kimliğini ve ölçülmüş konumunu yayar.",
                    "**The broadcast unit.** A low cost transmitter bolted "
                    "to something already standing: a mast, a roadside "
                    "unit, a traffic light, a tunnel light. It broadcasts "
                    "its identity and its surveyed position.",
                ),
                _w(
                    "**Alıcı.** Araçta ya da elde. Çevresindeki yayın "
                    "birimleriyle mesafe ölçer ve konumunu kendi çıkarır.",
                    "**The receiver.** In a vehicle or in a hand. It "
                    "measures range against the units around it and works "
                    "out where it is.",
                ),
                _w(
                    "**Merkezi yönetim sistemi.** Açık anahtarları ve "
                    "kimlikleri tutar, böylece alıcı taklit bir yayın "
                    "birimini kabul etmez.",
                    "**The management system.** It holds the public keys "
                    "and identities, so a receiver will not accept an "
                    "impostor.",
                ),
            ),
        ),
        Part(
            kind="text",
            heading=_w("Neden TWR, TDoA değil", "Why two way ranging"),
            lines=(
                _w(
                    "TDoA'da yayın birimlerinin saatleri nanosaniye "
                    "düzeyinde senkron olmak zorundadır; bu, atomik saat "
                    "ve IEEE 1588 PTP altyapısı demektir. Çift yönlü "
                    "menzil ölçümü bunu gerektirmez, çünkü hava süresi iki "
                    "uç arasındaki kısa bir diyalogla ölçülür.",
                    "TDoA needs the broadcast units synchronised to the "
                    "nanosecond, which means atomic clocks and an IEEE "
                    "1588 PTP backbone. Two way ranging does not, because "
                    "the time of flight comes out of a short exchange "
                    "between the two ends.",
                ),
                _w(
                    "Benzetim bu farkı da ölçüyor. Düzeltilmemiş 10 ppm'lik "
                    "bir saat kayması tek yönlü ölçümde 24,1 m hata "
                    "verirken çift yönlüde 0,3 mm bırakıyor. Kayma ölçüldü: "
                    "0,0793 ppm, ve bu projede artık tahmin olmayan tek "
                    "değer (ADR-0018).",
                    "The simulation measures that difference. An "
                    "uncorrected 10 ppm clock offset costs 24,1 m one way "
                    "and 0,3 mm two ways. The offset itself was measured "
                    "at 0,0793 ppm, and it is the one figure in this "
                    "project that is no longer a guess (ADR-0018).",
                ),
            ),
        ),
        Part(
            kind="table",
            heading=_w("Donanım ve fiyatı", "The hardware and its price"),
            rows=(
                (
                    _w("Ürün", "Product"),
                    _w("Telsiz", "Radio"),
                    _w("100 adette birim fiyat", "Unit price at 100"),
                ),
                (
                    _w("Şehir içi yayın birimi", "Urban broadcast unit"),
                    _w("SX1280 + 2,4 GHz anten", "SX1280 + 2,4 GHz antenna"),
                    _w("1366,07 TL", "1366,07 TL"),
                ),
                (
                    _w("Kırsal yayın birimi", "Rural broadcast unit"),
                    _w("E28-2G4M27S", "E28-2G4M27S"),
                    _w("1082,68 TL", "1082,68 TL"),
                ),
                (
                    _w("Kritik bölge yayın birimi", "Critical area unit"),
                    _w("DWM3000 UWB", "DWM3000 UWB"),
                    _w("1634,44 TL", "1634,44 TL"),
                ),
                (
                    _w("Yaya alıcısı", "Pedestrian receiver"),
                    _w("SX1280 + DWM3000 + ESP32-S3",
                       "SX1280 + DWM3000 + ESP32-S3"),
                    _w("3117,74 TL", "3117,74 TL"),
                ),
                (
                    _w("Kara aracı alıcısı", "Vehicle receiver"),
                    _w("SX1280 + DWM3000 + STM32", "SX1280 + DWM3000 + STM32"),
                    _w("4002,29 TL", "4002,29 TL"),
                ),
            ),
        ),
        Part(
            kind="points",
            lines=(
                _w(
                    "Fiyatlar 6 Eylül 2026 tarihli distribütör liste "
                    "fiyatlarından, 100 adetlik kademede. PCB üretimi ve "
                    "dizgisi, kablolama, mekanik işleme, test, "
                    "sertifikasyon, vergi, kargo ve saha kurulumu dahil "
                    "değildir.",
                    "Prices come from distributor list prices dated 6 "
                    "September 2026, at the hundred unit break. Board "
                    "manufacture and assembly, cabling, machining, test, "
                    "certification, tax, shipping and installation are all "
                    "outside them.",
                ),
                _w(
                    "İki alıcı da hem SX1280 hem DWM3000 taşır. Bir birimin "
                    "yolda şehir direkleriyle, tünelin içinde tünel "
                    "direkleriyle hiçbir şey değiştirmeden ölçmesini "
                    "sağlayan budur (ADR-0014).",
                    "Both receivers carry an SX1280 and a DWM3000. That is "
                    "what lets one unit range against urban anchors on the "
                    "road and against tunnel anchors inside the bore, with "
                    "nothing switched over (ADR-0014).",
                ),
            ),
        ),
    ),
)

METHOD = Page(
    slug="yontem",
    nav=_w("Yöntem", "Method"),
    title=_w("Benzetim nasıl çalışıyor", "How the simulation works"),
    lead=_w(
        "Bu bir benzetimdir, saha ölçümü değil. Neyi modellediğini ve neyi "
        "modellemediğini olduğu gibi yazar: bir sayının nereden geldiği "
        "sorulduğunda cevabı olan bir tablo, olmayanından başka bir şeydir.",
        "This is a simulation rather than a field measurement. It states "
        "what it models and what it does not, because a table that can "
        "answer where a number came from is a different object from one "
        "that cannot.",
    ),
    parts=(
        Part(
            kind="points",
            heading=_w("Zemin gerçek", "The ground is real"),
            lines=(
                _w(
                    "Üç satır da gerçek Ankara zemininin üzerinde durur. "
                    "Zemin Copernicus 30 m DEM'inden bir kez getirilip "
                    "paketin içine işlenmiştir, yani bir klon tabloyu ağa "
                    "hiç çıkmadan yeniden üretir (ADR-0008).",
                    "All three rows stand on real ground near Ankara, "
                    "fetched once from the Copernicus 30 m DEM and baked "
                    "into the package, so a clone reproduces the table "
                    "without touching the network (ADR-0008).",
                ),
                _w(
                    "Kızılay'da 91 m iniş çıkış var, Polatlı'da 486 m "
                    "rölyef, tünelde iki portal arasında %1,79 düşüş.",
                    "Kızılay carries 91 m of rise and fall, Polatlı 486 m "
                    "of relief, and the tunnel drops 1,79% between its two "
                    "portals.",
                ),
                _w(
                    "Hiçbir yerde düz zemin seçeneği yok. Düz bir düzlem "
                    "bu modelin çizebileceği en tarafsız değil en elverişli "
                    "yüzeydir (ADR-0021).",
                    "Nowhere is there a flat option. A flat plane is not "
                    "the most neutral surface this model can draw, it is "
                    "the most flattering one (ADR-0021).",
                ),
            ),
        ),
        Part(
            kind="points",
            heading=_w("Bir bağlantıya tek bir hesap karar verir",
                       "One calculation decides a link"),
            lines=(
                _w(
                    "Azami menzil diye bir sabit yok. Menzil bir girdi "
                    "değil, link bütçesinin sonucudur; aynı hesap "
                    "bağlantının kapanıp kapanmadığına da, ne kadar hassas "
                    "ölçtüğüne de karar verir (ADR-0002).",
                    "There is no maximum range constant anywhere. Range is "
                    "a result rather than an input, and the same "
                    "calculation decides both whether a link closes and "
                    "how precisely it measures (ADR-0002).",
                ),
                _w(
                    "İki ışınlı zemin yansıması düz zeminde bile çalışır: "
                    "kırılma mesafesinin ötesinde doğrudan ışınla zeminden "
                    "yansıyan ışın ters fazda gelip birbirini götürür, ve "
                    "o mesafe anten yüksekliğiyle doğrusal olduğu için "
                    "alçak montaj pahalıdır (ADR-0007).",
                    "The two ray ground reflection works even over flat "
                    "ground: past the break distance the direct ray and "
                    "the reflected one arrive out of phase and cancel, and "
                    "because that distance scales with antenna height, "
                    "mounting low is expensive (ADR-0007).",
                ),
                _w(
                    "Kırınım en kötü tek nokta üzerinden değil, bütün "
                    "profil üzerinden hesaplanır: ITU-R P.526-15 §4.5.2, "
                    "delta-Bullington. Kızılay'da bir bağlantının ortanca "
                    "üç engeli var, en kötüsünün on altı (ADR-0053).",
                    "Diffraction comes from the whole profile rather than "
                    "from its worst single point: ITU-R P.526-15 §4.5.2, "
                    "delta Bullington. A link across Kızılay has three "
                    "obstacles at the median and sixteen at the worst "
                    "(ADR-0053).",
                ),
                _w(
                    "Zemin profili on metrede bir okunur. Sabit 64 örnekte "
                    "6,9 km'lik bir kırsal bağlantı 108 m'de bir okunuyordu "
                    "ve kırınımı 37,60 dB yerine 31,28 dB veriyordu "
                    "(ADR-0062).",
                    "The ground profile is read every ten metres. At a "
                    "fixed 64 samples a 6,9 km rural link was read every "
                    "108 m, and it put diffraction at 31,28 dB where the "
                    "answer is 37,60 (ADR-0062).",
                ),
                _w(
                    "Bir bağlantı yansımayla kırınımın toplamını değil, "
                    "büyüğünü öder. İkisi de aynı yer parçasının aynı "
                    "bağlantıya yaptığını anlatır; toplamak o yer parçasını "
                    "iki kez faturalandırmaktır (ADR-0058).",
                    "A link pays the larger of reflection and diffraction "
                    "rather than their sum. Both describe what the same "
                    "piece of ground does to the same link, and adding "
                    "them bills that ground twice (ADR-0058).",
                ),
                _w(
                    "Gölgeleme ikisinin üstüne eklenir ve genişliği yolun "
                    "açık olup olmamasına bağlıdır: görüş hattı varken 4 "
                    "dB, yokken 7,82 (3GPP TR 38.901). Tablo sekiz "
                    "çekilişin havuzudur, tek bir çekilişin değil "
                    "(ADR-0055, ADR-0061).",
                    "Shadowing sits on top of both, and its width depends "
                    "on whether the path is clear: 4 dB with line of "
                    "sight, 7,82 without (3GPP TR 38.901). The table pools "
                    "eight draws rather than showing one (ADR-0055, "
                    "ADR-0061).",
                ),
            ),
        ),
        Part(
            kind="points",
            heading=_w("Alışveriş ve kestirici",
                       "The exchange and the estimator"),
            lines=(
                _w(
                    "Bir menzil link bütçesinden okunmaz. İki telsiz çerçeve "
                    "alışverişi yapar; SX1280'de SF10'da bir çift yönlü "
                    "alışveriş 47,86 ms sürer.",
                    "A range is not read off a link budget. Two radios "
                    "exchange frames, and on the SX1280 at SF10 one two way "
                    "exchange takes 47,86 ms.",
                ),
                _w(
                    "Altı direğe karşı bir tur 239 ms sürer. Bu sürede 100 "
                    "km/sa giden bir araç 6,7 m yol alır, yani bir turun "
                    "menzilleri eşzamanlı değildir ve öyleymiş gibi "
                    "çözülmez.",
                    "A round against six anchors takes 239 ms. A car doing "
                    "100 km/h covers 6,7 m in that time, so the ranges in "
                    "one round are not simultaneous and are not solved as "
                    "though they were.",
                ),
                _w(
                    "Kestirici gerçeği hiç görmez. Yalnızca gözlemleri "
                    "görür: ölçülmüş mesafe, direğin ölçülmüş konumu, bir "
                    "zaman damgası ve bir varyans (ADR-0003).",
                    "The estimator never sees the truth. It sees "
                    "observations: a measured distance, an anchor's "
                    "surveyed position, a timestamp and a variance "
                    "(ADR-0003).",
                ),
                _w(
                    "Hiçbir yerde yükseklik kısıtı yok. Yol kenarına "
                    "dizilmiş direkler düşeyi neredeyse gözlenemez bırakır, "
                    "ve VPE sütunu bunu gizlemek yerine bildirir "
                    "(ADR-0011).",
                    "There is no height constraint anywhere. Anchors strung "
                    "along a roadside leave the vertical barely "
                    "observable, and the VPE column reports that instead of "
                    "hiding it (ADR-0011).",
                ),
            ),
        ),
        Part(
            kind="points",
            heading=_w("Gürültü olmayan üç hata",
                       "Three errors that are not noise"),
            lines=(
                _w(
                    "**Engellenmiş bir yol uzun ölçer.** Sinyal engelin "
                    "üzerinden gider ve menzil o sapmayı zamanlar. Sapma "
                    "her zaman pozitiftir, yani ortalamayla asla kaybolmaz.",
                    "**A blocked path measures long.** The signal goes over "
                    "the obstacle and the range times that detour. The "
                    "error is always positive, so averaging never removes "
                    "it.",
                ),
                _w(
                    "**Etüt hatası kurulumun özelliğidir**, direk başına "
                    "bir kez çekilir ve tutulur. Tünelin HPE P50 değeri "
                    "kusursuz etütte 0,24 m, 15 cm'lik etüt hatasında 1,76 "
                    "m: direkleri ölçtüğünden daha iyi konumlanamazsın.",
                    "**A survey error belongs to an installation**, drawn "
                    "once per anchor and kept. The tunnel's HPE P50 is 0,24 "
                    "m with perfect survey and 1,76 m with 15 cm of it: you "
                    "cannot position better than you surveyed.",
                ),
                _w(
                    "**Kaybolan bir paket hiçbir şey üretmez.** Bant 2,4 "
                    "GHz kablosuz ağlarla aynıdır; şehirde kayıp %15, açık "
                    "yolda %5, tünelde sıfır (ADR-0019).",
                    "**A lost packet produces nothing.** The band is shared "
                    "with 2,4 GHz wireless networks: 15% loss in the city, "
                    "5% on the open road, none in the tunnel (ADR-0019).",
                ),
            ),
        ),
        Part(
            kind="points",
            heading=_w("Modellenmeyenler", "What is left out"),
            lines=(
                _w(
                    "IMU, odometri, harita kısıtı ve Kalman füzyonu yok. "
                    "Rapordaki mimari bunları öngörüyor; buradaki sayılar "
                    "yalnızca radyo menzil ölçümünden çözülmüş serbest 3B "
                    "konumlardır.",
                    "No inertial unit, no odometry, no map constraint, no "
                    "Kalman fusion. The report's architecture calls for "
                    "them; these numbers are free 3D fixes solved from "
                    "radio ranging alone.",
                ),
                _w(
                    "Faz gürültüsü, çok yolluluk ve alışveriş sırasında "
                    "saat sürüklenmesi modellenmiyor.",
                    "Phase noise, multipath and drift during an exchange "
                    "are not modelled.",
                ),
                _w(
                    "Tünelde dalga kılavuzu etkisi yok, yani tünel satırı "
                    "gerçek bir tünelin vereceğinden azını gösterir.",
                    "There is no waveguide term in the tunnel, so that row "
                    "understates what a real bore delivers.",
                ),
                _w(
                    "Kullanılabilirlik yalnızca modellenen başarısızlıkları "
                    "sayar: kapanmayan bağlantı, yetersiz menzil, oturmayan "
                    "çözüm. Bir hizmet kullanılabilirliği değeri değildir "
                    "ve GNSS satırlarına karşı öyle okunmamalıdır.",
                    "Availability counts modelled failures only: a link "
                    "that did not close, a round with too few ranges, a "
                    "solve that did not settle. It is not a service "
                    "availability figure and should not be read against the "
                    "GNSS rows as though it were.",
                ),
            ),
        ),
    ),
)

RESULTS = Page(
    slug="sonuclar",
    nav=_w("Sonuçlar", "Results"),
    title=_w("Dört satır", "The four rows"),
    lead=_w(
        "Raporun 15. sayfasına giren blok. Aşağıdaki sayılar yayımlanan "
        "koşunun çıktısıdır ve bu sayfa onları koşunun yazdığı dosyadan "
        "okur; sitede elle yazılmış bir tablo yok.",
        "The block that goes into page 15 of the report. These numbers are "
        "the output of the published run, read from the file that run "
        "wrote. No table on this site was typed by hand.",
    ),
    parts=(
        Part(kind="shows", shows="published"),
        Part(
            kind="table",
            heading=_w("Sütunlar ne demek", "What the columns mean"),
            rows=(
                (_w("Sütun", "Column"), _w("Anlamı", "Meaning")),
                (
                    _w("HPE, VPE", "HPE, VPE"),
                    _w(
                        "Yatay ve düşey konum hatası, metre, belirtilen "
                        "yüzdelikte, değerlendirilen yolculuklar üzerinden.",
                        "Horizontal and vertical position error in metres, "
                        "at the stated percentile, over the journeys "
                        "evaluated.",
                    ),
                ),
                (
                    _w("Kullanılabilirlik", "Availability"),
                    _w(
                        "Denenen sabitlemelerin geçerli bir konum üretenleri. "
                        "Yalnızca modellenen başarısızlıkları sayar.",
                        "The share of attempted fixes that produced a valid "
                        "position. It counts modelled failures only.",
                    ),
                ),
                (
                    _w("Alan", "Area"),
                    _w(
                        "Bir konum üretmeye yetecek kadar direğin "
                        "erişilebilir olduğu zemin, gerçek arazi üzerinde "
                        "taranarak. Bir paketin ulaştığı zemin değildir.",
                        "The ground where enough anchors are reachable for "
                        "a position, swept over the real terrain. It is not "
                        "the ground a packet reaches.",
                    ),
                ),
                (
                    _w("CAPEX", "CAPEX"),
                    _w(
                        "Direk donanım maliyetinin hizmet alanına bölümü. "
                        "Yalnızca donanım.",
                        "Anchor hardware cost divided by the service area. "
                        "Hardware only.",
                    ),
                ),
                (
                    _w("OPEX", "OPEX"),
                    _w(
                        "km² başına yıllık işletme maliyeti. Rapor bu "
                        "sütunu boş bırakır; buradaki değer adlandırılmış "
                        "yinelenen kalemlerden gelir (ADR-0006).",
                        "Yearly operating cost per km². The report leaves "
                        "this column empty; this one comes from an "
                        "itemised inventory (ADR-0006).",
                    ),
                ),
            ),
        ),
        Part(
            kind="points",
            heading=_w("Tablonun söylemeden yapmayacağı üç şey",
                       "Three things the table will not do quietly"),
            lines=(
                _w(
                    "**Tünelin km² başına maliyeti diğer satırlarla "
                    "karşılaştırılamaz.** 2 km boyunca 12 m genişliğinde "
                    "bir tünel yaklaşık iki yüz dönümdür; buna bölmek büyük "
                    "bir sayıyı yargıyla değil aritmetikle üretir. Tünel "
                    "bir çizgiye hizmet eder, bu yüzden güzergâh "
                    "kilometresi başına maliyetle karşılaştırılır ve "
                    "`yerkon table` o değeri satırın yanında yazar.",
                    "**The tunnel's cost per km² does not compare to the "
                    "other rows.** Twelve metres wide over two kilometres "
                    "is a fiftieth of a square kilometre, so dividing by it "
                    "produces a large number by arithmetic rather than by "
                    "judgement. A tunnel serves a line, so compare it on "
                    "cost per route kilometre, which `yerkon table` prints "
                    "beside the row.",
                ),
                _w(
                    "**Hizmet alanı, bir konumun alınabildiği yerdir**, bir "
                    "paketin ulaştığı yer değil. Kırsalda bir paket, konum "
                    "alınabilen zeminin 2,6 katına ulaşır, ve notlar her "
                    "seferinde ikisini de yazar (ADR-0012).",
                    "**The service area is where a position can be had**, "
                    "not where a packet arrives. In open country a packet "
                    "reaches 2,6 times the ground a position can be had on, "
                    "and the notes print both every time (ADR-0012).",
                ),
                _w(
                    "**Kırsal kullanılabilirliğe arazi ve turun uzunluğu "
                    "karar verir.** Tek bir kırsal bağlantı bile mesafe "
                    "yüzünden düşmez; her başarısızlık zemin kaldırılsa "
                    "kapanırdı. Daha çok direk yanlış içgüdüdür (ADR-0022).",
                    "**Terrain and the length of a round decide rural "
                    "availability.** Not one rural link fails on distance; "
                    "every failure would close with the ground taken away. "
                    "More anchors is the wrong instinct (ADR-0022).",
                ),
            ),
        ),
        Part(
            kind="text",
            heading=_w("Hızlı okuma", "The fast reading"),
            lines=(
                _w(
                    "Simülasyondaki **Hızlı dene** düğmesi ve komut "
                    "satırındaki `--fast` aynı iki figürü kabalaştırır: "
                    "gölgeler sekiz yerine bir kez çekilir, profil 10 m "
                    "yerine sabit 64 örnekle okunur. Koşu on beş dakikadan "
                    "bir dakikaya iner.",
                    "The **fast** button in the simulator and `--fast` on "
                    "the command line coarsen the same two figures: the "
                    "shadows are drawn once instead of pooled over eight, "
                    "and the profile is read at a fixed 64 samples instead "
                    "of every 10 m. A run drops from fifteen minutes to "
                    "about one.",
                ),
                _w(
                    "İki kabalık da kaybı eksik okur, yani hızlı bir cevap "
                    "yerleşimi kayırır: kırsal satırın P95'i 4,13 m iyimser "
                    "çıkıyor. Bu yüzden hızlı okumada kötü görünen bir satır "
                    "gerçekten kötüdür, ve bu sayfa yalnızca yayımlanan "
                    "koşuyu gösterir (ADR-0063).",
                    "Both coarsenings read the loss low, so a fast answer "
                    "flatters the deployment: the rural row's P95 came out "
                    "4,13 m optimistic. A row that looks bad under a fast "
                    "reading is genuinely bad, and this page shows the "
                    "published run only (ADR-0063).",
                ),
            ),
        ),
    ),
)

SOURCES = Page(
    slug="kaynaklar",
    nav=_w("Kaynaklar", "Sources"),
    title=_w("Neye dayanıyor", "What it rests on"),
    lead=_w(
        "Bir sayı ya bir veri sayfasından, ya yayımlanmış bir ölçümden, ya "
        "da açıkça yazılmış bir varsayımdan gelir. Üçüncüsü bu projede "
        "ayrı bir tip taşır, böylece hangi sayının kaynağı olmadığı "
        "sayılabilir.",
        "A number comes from a datasheet, from a published measurement, or "
        "from an assumption written down. The third kind carries its own "
        "type in this project, so the ones nobody supplied can be counted.",
    ),
    parts=(
        Part(
            kind="code",
            heading=_w("Nasıl yeniden üretilir", "How to reproduce it"),
            code=_w(
                "pip install -e \".[dev]\"\n"
                "yerkon table          # yayımlanan sayılar, ~15 dk\n"
                "yerkon table --fast   # denemek için, ~1 dk, yayımlanmaz\n"
                "yerkon view           # bu site ve simülatör",
                "pip install -e \".[dev]\"\n"
                "yerkon table          # the published numbers, about 15 min\n"
                "yerkon table --fast   # about 1 min, not publishable\n"
                "yerkon view           # this site and the simulator",
            ),
        ),
        Part(
            kind="points",
            lines=(
                _w(
                    "Zemin pakete işlenmiştir, yani yukarıdaki tablo ağa "
                    "hiç çıkmadan yeniden üretilir. Tohum sabittir.",
                    "The ground is baked into the package, so the table "
                    "above reproduces with no network at all. The seed is "
                    "fixed.",
                ),
            ),
        ),
        Part(
            kind="points",
            heading=_w("Standartlar ve veri", "Standards and data"),
            lines=(
                _w("ITU-R P.526-15 §4.5.2, delta-Bullington kırınımı.",
                   "ITU-R P.526-15 §4.5.2, delta Bullington diffraction."),
                _w("ITU-R P.452 ve P.1812: kaybın nasıl kurulduğu.",
                   "ITU-R P.452 and P.1812: how loss is built up."),
                _w("3GPP TR 38.901 Tablo 7.4.1-1: gölgeleme genişlikleri.",
                   "3GPP TR 38.901 Table 7.4.1-1: shadowing widths."),
                _w("Copernicus DEM 30 m: zemin yükseklikleri.",
                   "Copernicus DEM 30 m: ground heights."),
                _w("OpenStreetMap ve Overture: binalar ve yol kenarı "
                   "donanımı.",
                   "OpenStreetMap and Overture: buildings and roadside "
                   "furniture."),
                _w("Semtech SX1280, EBYTE E28-2G4M27S ve Qorvo DWM3000 veri "
                   "sayfaları.",
                   "Semtech SX1280, EBYTE E28-2G4M27S and Qorvo DWM3000 "
                   "datasheets."),
                _w("DigiKey, LCSC ve Mouser liste fiyatları, 6 Eylül 2026.",
                   "DigiKey, LCSC and Mouser list prices, 6 September 2026."),
            ),
        ),
        Part(
            kind="points",
            heading=_w("Depodaki belgeler", "What the repository holds"),
            lines=(
                _w("`CONTEXT.md` sözlüktür: her terimin kodda kullanılan "
                   "adı ve raporda kullanılan karşılığı.",
                   "`CONTEXT.md` is the glossary: the name the code uses "
                   "for each term beside the one the report uses."),
                _w("`docs/adr/` her kararı ve neyin yerine geçtiğini tutar.",
                   "`docs/adr/` holds every decision and what it replaced."),
                _w("`docs/HANDOFF.md` açık soruları ve hâlâ vekil olan "
                   "değerleri tutar.",
                   "`docs/HANDOFF.md` holds the open questions and the "
                   "figures still standing in for real ones."),
                _w("Belgeler Türkçe, kod İngilizce.",
                   "The documents are in Turkish and the code is in "
                   "English."),
            ),
        ),
        Part(
            kind="points",
            heading=_w("Proje", "The project"),
            lines=(
                _w(
                    "YERKON, Ulaştırma ve Altyapı Bakanlığı UDHAM'ın "
                    "\u201cUlaşan ve Erişen Türkiye 2053\u201d üniversiteler "
                    "arası fikir yarışmasına sunulan bir fikirdir, Temmuz "
                    "2026.",
                    "YERKON is an idea submitted to UDHAM's \u201cUlaşan ve "
                    "Erişen Türkiye 2053\u201d inter-university competition, "
                    "run by the Ministry of Transport and Infrastructure, "
                    "July 2026.",
                ),
                _w(
                    "Proje ekibi, TOBB Ekonomi ve Teknoloji Üniversitesi: "
                    "Mustafa Göktürk Binay, Mehmet Gönül, Yavuz Selim Oktar "
                    "(grup temsilcisi).",
                    "The team, at TOBB University of Economics and "
                    "Technology: Mustafa Göktürk Binay, Mehmet Gönül, Yavuz "
                    "Selim Oktar (group representative).",
                ),
                _w(
                    "Bu depo raporun kendisi değil, raporun 15. sayfasındaki "
                    "YERKON bloğunu üreten benzetimdir.",
                    "This repository is not the report. It is the simulation "
                    "that produces the YERKON block on page 15 of it.",
                ),
            ),
        ),
        Part(
            kind="links",
            heading=_w("Kod", "Code"),
            links=(
                Link(
                    label=_w("Depo: github.com/ysoktar/yerkon",
                             "Repository: github.com/ysoktar/yerkon"),
                    url="https://github.com/ysoktar/yerkon",
                ),
            ),
        ),
    ),
)

#: Every page, in the order the navigation shows them.
PAGES = (HOME, WHY, SYSTEM, METHOD, RESULTS, SOURCES)

#: Where the simulator lives, and what the link to it is called.
SIMULATOR = "/simulasyon"
SIMULATOR_LABEL = _w("Simülasyon", "Simulator")

#: The one line under the wordmark, on every page.
STANDFIRST = _w(
    "Karasal konumlandırma benzetimi",
    "A terrestrial positioning simulation",
)

BACK_TO_SITE = _w("Siteye dön", "Back to the site")

LANGUAGES = (("tr", "TR"), ("en", "EN"))

#: What the headline figures on the home page are called.
HEADLINE = (
    ("hpe_p50_m", _w("Yatay hata, P50", "Horizontal error, P50"), "m"),
    ("hpe_p95_m", _w("Yatay hata, P95", "Horizontal error, P95"), "m"),
    ("availability", _w("Kullanılabilirlik", "Availability"), "%"),
    ("area_km2", _w("Hizmet alanı", "Service area"), "km²"),
)

COLUMNS = (
    _w("Sistem", "System"),
    _w("Teknoloji", "Technology"),
    _w("Ortam", "Environment"),
    _w("HPE P50 [m]", "HPE P50 [m]"),
    _w("HPE P95 [m]", "HPE P95 [m]"),
    _w("VPE P95 [m]", "VPE P95 [m]"),
    _w("Kullanılabilirlik", "Availability"),
    _w("Alan [km²]", "Area [km²]"),
    _w("CAPEX [TL/km²]", "CAPEX [TL/km²]"),
    _w("OPEX [TL/km²/yıl]", "OPEX [TL/km²/yr]"),
)

RUN_NOTE = _w(
    "{run_on} tarihinde {source} okunarak koşuldu. Gölgeler {draws} kez "
    "çekildi, zemin profili {spacing} m'de bir okundu. İlk üç sütun rapora "
    "giren adlardır ve çevrilmez.",
    "Run on {run_on} against {source}. The shadows were drawn {draws} "
    "times and the ground profile was read every {spacing} m. The first "
    "three columns are the names that go into the Turkish report, so they "
    "are not translated.",
)

FOOTER = _w(
    "YERKON benzetimi. Sayılar yayımlanan koşudan gelir; yöntemi ve "
    "sınırları Yöntem sayfasında.",
    "The YERKON simulation. The numbers come from the published run; the "
    "method and its limits are on the Method page.",
)

WEIGHTING = _w(
    "Ağırlıklı ortalama satırı: %50 şehir içi, %40 kırsal, %10 tünel. Üç "
    "senaryonun ham hata örneklerini birleştirir, yüzdeliklerini değil "
    "(ADR-0005).",
    "The weighted row: 50% urban, 40% rural, 10% tunnel. It combines the "
    "three scenarios' raw per fix samples rather than their percentiles "
    "(ADR-0005).",
)

NO_RUN = _w(
    "Yayımlanmış bir koşu yok. `yerkon table --publish` çalıştır.",
    "There is no published run. Run `yerkon table --publish`.",
)


def page_at(slug: str) -> Optional[Page]:
    """The page an address asks for, or nothing."""
    for page in PAGES:
        if page.slug == slug.strip("/"):
            return page
    return None


# --- drawing it -----------------------------------------------------------


def render(
    page: Page,
    language: str = "tr",
    published=None,
) -> str:
    """One page as a whole HTML document."""
    body = [
        _header(page, language),
        '<main>',
        '<h1>{}</h1>'.format(_said(page.title, language)),
        '<p class="lead">{}</p>'.format(_said(page.lead, language)),
    ]
    for part in page.parts:
        body.append(_part(part, language, published))
    body += ['</main>', _footer(language)]
    return _document(
        title="{} · YERKON".format(_said(page.title, language)),
        language=language,
        body="\n".join(body),
    )


def _document(title: str, language: str, body: str) -> str:
    return (
        "<!doctype html>\n"
        '<html lang="{language}">\n'
        "<head>\n"
        '<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        "<title>{title}</title>\n"
        '<link rel="stylesheet" href="/site.css">\n'
        "</head>\n"
        "<body>\n{body}\n</body>\n</html>\n"
    ).format(language=language, title=html.escape(title), body=body)


def _header(page: Page, language: str) -> str:
    links = []
    for other in PAGES:
        where = "/" + other.slug
        here = ' class="here"' if other.slug == page.slug else ""
        links.append('<a href="{}"{}>{}</a>'.format(
            where, here, _said(other.nav, language)
        ))
    tongues = "".join(
        '<a href="{}?dil={}"{}>{}</a>'.format(
            "/" + page.slug, code, ' class="here"' if code == language else "",
            label,
        )
        for code, label in LANGUAGES
    )
    return (
        "<header>\n"
        '<a class="brand" href="/"><b>YERKON</b> <span>{standfirst}</span></a>\n'
        '<nav class="pages">{links}</nav>\n'
        '<nav class="tongues">{tongues}</nav>\n'
        '<a class="run" href="{simulator}">{label} →</a>\n'
        "</header>"
    ).format(
        standfirst=_said(STANDFIRST, language),
        links="".join(links),
        tongues=tongues,
        simulator=SIMULATOR,
        label=_said(SIMULATOR_LABEL, language),
    )


def _footer(language: str) -> str:
    return "<footer><p>{}</p></footer>".format(_said(FOOTER, language))


def _part(part: Part, language: str, published) -> str:
    heading = (
        "<h2>{}</h2>".format(_said(part.heading, language))
        if part.heading else ""
    )
    if part.kind == "text":
        drawn = "".join(
            "<p>{}</p>".format(_said(line, language)) for line in part.lines
        )
    elif part.kind == "points":
        drawn = "<ul>{}</ul>".format("".join(
            "<li>{}</li>".format(_said(line, language)) for line in part.lines
        ))
    elif part.kind == "table":
        drawn = _table(
            [[_said(cell, language) for cell in row] for row in part.rows]
        )
    elif part.kind == "code":
        # Escaped and not marked: a backtick inside a command block is a
        # backtick.
        drawn = "<pre><code>{}</code></pre>".format(
            html.escape(part.code.said(language))
        )
    elif part.kind == "links":
        drawn = "<ul>{}</ul>".format("".join(
            '<li><a href="{}">{}</a></li>'.format(
                html.escape(one.url, quote=True), _said(one.label, language)
            )
            for one in part.links
        ))
    elif part.kind == "map":
        drawn = "".join(
            '<a class="card" href="/{}"><b>{}</b><span>{}</span></a>'.format(
                other.slug, _said(other.nav, language),
                _said(other.lead, language),
            )
            for other in PAGES if other.slug
        )
        drawn = '<div class="cards">{}</div>'.format(drawn)
    elif part.kind == "shows" and part.shows == "headline":
        drawn = _headline(published, language)
    elif part.kind == "shows" and part.shows == "published":
        drawn = _published(published, language)
    else:
        raise ValueError("no way to draw a {} part".format(part.kind))
    return "<section>{}{}</section>".format(heading, drawn)


def _headline(published, language: str) -> str:
    """The weighted row, four figures wide, on the home page."""
    if published is None:
        return '<p class="warn">{}</p>'.format(_said(NO_RUN, language))
    row = published.row("weighted")
    figures = []
    for name, label, unit in HEADLINE:
        value = getattr(row, name)
        if name == "availability":
            shown = "%" + decimal_comma(100.0 * value, 2)
        else:
            shown = decimal_comma(value, 2) + " " + unit
        figures.append(
            '<div class="figure"><b>{}</b><span>{}</span></div>'.format(
                shown, _said(label, language)
            )
        )
    return (
        '<div class="figures">{}</div>'
        '<p class="under">{}</p>'
    ).format("".join(figures), _said(WEIGHTING, language))


def _published(published, language: str) -> str:
    """The four rows, exactly as the run printed them."""
    if published is None:
        return '<p class="warn">{}</p>'.format(_said(NO_RUN, language))
    head = [_said(column, language) for column in COLUMNS]
    body = [list(row.cells()) for row in published.rows]
    # The template is escaped once, by `_said`. What comes out of the
    # record is escaped here, and escaping the result again would put
    # `&amp;#x27;` on the page where an apostrophe belongs.
    note = _said(RUN_NOTE, language).format(
        run_on=html.escape(published.run_on),
        source=html.escape(published.source),
        draws=published.shadow_draws,
        spacing=decimal_comma(published.profile_spacing_m, 0),
    )
    return (
        '<div class="wide"><div class="scroll">{}</div>'
        '<p class="under">{}</p></div>'
    ).format(_table([head] + body, numeric_from=3), note)


def _table(rows: Sequence[Sequence[str]], numeric_from: int = 99) -> str:
    head, body = rows[0], rows[1:]
    out = ["<table><thead><tr>"]
    for at, cell in enumerate(head):
        out.append('<th{}>{}</th>'.format(
            ' class="num"' if at >= numeric_from else "", cell
        ))
    out.append("</tr></thead><tbody>")
    for row in body:
        out.append("<tr>")
        for at, cell in enumerate(row):
            out.append('<td{}>{}</td>'.format(
                ' class="num"' if at >= numeric_from else "", cell
            ))
        out.append("</tr>")
    out.append("</tbody></table>")
    return "".join(out)


def _said(words: Words, language: str) -> str:
    """One phrase, escaped, with its emphasis and its code kept."""
    return _marked(words.said(language))


def _marked(text: str) -> str:
    out = html.escape(text)
    out = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", out)
    out = re.sub(r"`(.+?)`", r"<code>\1</code>", out)
    return out
