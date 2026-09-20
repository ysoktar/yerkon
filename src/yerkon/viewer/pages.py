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
import pathlib
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
    #: A file beside the page, with what it shows.
    picture: str = ""
    #: Columns from here on hold numbers, so they are set right and kept
    #: on one line. Nothing does by default.
    numbers_from: int = 99
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


@dataclass(frozen=True)
class Where:
    """How one page names another.

    A server answers `/sorun` and a folder of files answers
    `sorun.html`, and that is the only thing the two disagree about.
    Keeping it in one object means the pages are written once and the
    static export is not a second copy of them (ADR-0065).
    """

    #: The language of the page doing the naming. Only the static export
    #: needs it, because there each language is its own folder.
    language: str = "tr"
    #: A folder of files rather than a running server.
    loose: bool = False

    def page(self, page: "Page") -> str:
        if not self.loose:
            return "/" + page.slug
        return self.file(page)

    def tongue(self, page: "Page", code: str) -> str:
        if not self.loose:
            return "/{}?dil={}".format(page.slug, code)
        if code == self.language:
            return self.file(page)
        return ("en/" if code == "en" else "../") + self.file(page)

    def asset(self, name: str) -> str:
        if not self.loose:
            return "/" + name
        return ("../" if self.language == "en" else "") + name

    def simulator(self) -> str:
        # Served, this is the simulator itself. Loose, it is the page
        # that says the simulator runs on your own machine, because a
        # folder of files cannot run a link budget.
        return SIMULATOR if not self.loose else self.file(SIMULATION)

    @staticmethod
    def file(page: "Page") -> str:
        return "index.html" if not page.slug else page.slug + ".html"


# --- what the site says ---------------------------------------------------

HOME = Page(
    slug="",
    nav=_w("Anasayfa", "Home"),
    title=_w("YERKON", "YERKON"),
    lead=_w(
        "YERKON, karayolu ulaşımında konumun yabancı uydu sistemlerine "
        "bağımlılığını azaltmak için bir fikirdir. Yol kenarında zaten "
        "duran noktalara düşük maliyetli yayın birimleri takılır, ve "
        "bir alıcı çevresindeki birimlerle mesafe ölçerek konumunu kendi "
        "hesaplar.",
        "YERKON is a proposal for road transport to depend less on "
        "foreign satellite systems for position. Low cost broadcast "
        "units go onto roadside points that are already standing, and a "
        "receiver works out where it is by measuring range against the "
        "units around it.",
    ),
    parts=(
        Part(
            kind="picture",
            picture="road.png",
            lines=(_w(
                "Rapordan. Yayın birimleri yol kenarındaki mevcut "
                "noktalara takılır; alıcı hem uyduyu hem karasal "
                "birimleri görebilir, ve uydu kesildiğinde karasal "
                "olanla devam eder.",
                "From the report. The broadcast units go onto existing "
                "roadside points. A receiver can see both the satellites "
                "and the terrestrial units, and carries on with the "
                "terrestrial ones when the satellites go.",
            ),),
        ),
        Part(
            kind="text",
            heading=_w("Ne öneriyor", "What it proposes"),
            lines=(
                _w(
                    "Ulaştırma ve Altyapı Bakanlığı'nın elektrik ve "
                    "haberleşme hattına bağlı noktaları zaten var: akıllı "
                    "ulaşım sistemi kabinleri, yol kenarı üniteleri, "
                    "trafik ışıkları, tünel aydınlatması ve ücretli yol "
                    "gişeleri. YERKON bu noktalara düşük maliyetli bir "
                    "radyo yayın kartı ekler. Kart, kimliğini ve "
                    "kurulumda ölçülmüş konumunu yayınlar.",
                    "The Ministry of Transport and Infrastructure already "
                    "has points on the power and communications network: "
                    "intelligent transport cabinets, roadside units, "
                    "traffic lights, tunnel lighting and toll gates. "
                    "YERKON adds a low cost radio board to those points. "
                    "The board broadcasts its identity and the position "
                    "surveyed when it was installed.",
                ),
                _w(
                    "Bir yayın birimi 1000 ile 1600 lira arasında. Yeni "
                    "direk dikmek, yeni enerji hattı çekmek ya da ağ "
                    "geneli atomik saat kurmak gerekmiyor; maliyeti bu "
                    "kadar aşağıda tutan da bu.",
                    "A broadcast unit costs between 1000 and 1600 lira. "
                    "Nothing here needs a new mast, a new power feed or a "
                    "network of atomic clocks, which is what keeps the "
                    "cost this low.",
                ),
                _w(
                    "YERKON uydu sistemlerinin yerine geçmeyi hedeflemez. "
                    "Uydu çalışırken iki cevap yan yana konur, ve "
                    "aralarındaki tutarsızlık bir aldatma saldırısını "
                    "görünür kılar.",
                    "YERKON does not try to replace the satellite "
                    "systems. While they work, the two answers sit side "
                    "by side, and a disagreement between them makes a "
                    "spoofing attack visible.",
                ),
            ),
        ),
        Part(kind="shows", shows="headline"),
        Part(kind="map", heading=_w("Sayfalar", "Pages")),
    ),
)

WHY = Page(
    slug="sorun",
    nav=_w("Sorun", "The problem"),
    title=_w("GNSS neden yetmiyor", "Why GNSS is not enough"),
    lead=_w(
        "Konum, seyrüsefer ve hassas zamanlama hizmetlerinin büyük bölümü "
        "GPS, Galileo, GLONASS ve BeiDou'dan gelir. Bu bağımlılık araç "
        "navigasyonuyla kalmaz; acil müdahale koordinasyonunu, kamu "
        "filolarını, telekomünikasyon şebekelerini, elektrik sistemlerini "
        "ve lojistik operasyonlarını da kapsar.",
        "Most positioning, navigation and timing comes from GPS, Galileo, "
        "GLONASS and BeiDou. The dependency goes past vehicle navigation: "
        "emergency response, public fleets, telecommunications networks, "
        "electrical systems and logistics all sit on it.",
    ),
    parts=(
        Part(
            kind="picture",
            picture="gnss.png",
            lines=(_w(
                "Dördü de yabancı devletlerin kontrolünde, ve dördü de "
                "aynı zayıflığı paylaşır: uydudan gelen sinyal yere "
                "vardığında çok zayıftır.",
                "All four are controlled by foreign states, and all four "
                "share one weakness. The signal is very weak by the time "
                "it reaches the ground.",
            ),),
        ),
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
                    "Düşük güçlü sinyal karıştırmaya açıktır, ve "
                    "elektronik harp ürünleri yaygınlaşıyor.",
                    "A weak signal is open to jamming, and electronic "
                    "warfare equipment keeps spreading.",
                ),
                _w(
                    "Sahte sinyal yanlış bir konum üretir. Alıcı bunu "
                    "tutarlı ve yüksek güvenli bir konum olarak gösterir, "
                    "ki tehlikeli olan da budur.",
                    "A spoofed signal produces a wrong position, and the "
                    "receiver reports it as a consistent one with high "
                    "confidence. That is what makes it dangerous.",
                ),
                _w(
                    "Kritik hizmetler tek bir teknoloji ailesine "
                    "bağlıdır.",
                    "Critical services depend on a single family of "
                    "technology.",
                ),
                _w(
                    "Kriz anında sistem üzerindeki karar yetkisi "
                    "Türkiye'de değildir.",
                    "In a crisis, the authority over the system is not in "
                    "Turkey.",
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
                    "ay boyunca durdurdu. İki yolcu uçağı yaklaşma "
                    "sırasında sinyali kaybedip Helsinki'ye döndü, ve "
                    "havalimanının yalnızca GPS tabanlı yaklaşma sistemi "
                    "olduğu için haftalarca kapandı.",
                    "**The Baltic, April 2024.** Finnair stopped flying to "
                    "Tartu for a month. Two airliners lost the signal on "
                    "approach and turned back to Helsinki, and the airport "
                    "closed for weeks because its only approach system was "
                    "GPS based.",
                ),
                _w(
                    "**Norveç, 2019'dan bu yana.** Kola Yarımadası'ndan "
                    "yayılan düzenli karıştırma, Finnmark'taki polis, "
                    "ambulans ve kurtarma ekiplerinin navigasyonunu "
                    "defalarca kör etti. Bir kar fırtınasında kaybolan "
                    "kişinin acil durum vericisi çalışmadı ve kurtarma "
                    "helikopterleri kör uçtu.",
                    "**Norway, 2019 onwards.** Steady jamming from the "
                    "Kola Peninsula has repeatedly blinded police, "
                    "ambulance and rescue navigation in Finnmark. During "
                    "one snowstorm a missing person's emergency beacon "
                    "failed and the rescue helicopters flew blind.",
                ),
                _w(
                    "**Karadeniz, 2017.** Yirmiden fazla ticari geminin "
                    "alıcısı, gemiler denizin ortasındayken konumu 40 km "
                    "içerideki bir havalimanında gösterdi.",
                    "**The Black Sea, 2017.** Receivers on more than twenty "
                    "commercial ships put them at an airport 40 km inland "
                    "while they were at sea.",
                ),
            ),
        ),
        Part(
            kind="text",
            heading=_w("YERKON'un cevabı", "What YERKON answers"),
            lines=(
                _w(
                    "Kırsal yayın biriminin sekiz kilometreyi bulan "
                    "menzili alçak irtifada da okunabilir, kritik bölge "
                    "altyapısı ise havalimanı çevresinde uydular sağır "
                    "edilse bile bağımsız bir karasal ağ sunar. Bunlar "
                    "raporun iddiasıdır; bu depo hiçbirini sahada "
                    "ölçmedi.",
                    "The rural unit's eight kilometre reach can be read at "
                    "low altitude, and the critical area installation "
                    "gives an airport an independent terrestrial network "
                    "even with the satellites deafened. These are the "
                    "report's claims, and this repository measured none of "
                    "them in the field.",
                ),
                _w(
                    "Aldatmaya karşı YERKON bir yedekten fazlasıdır. "
                    "Araçlar ve gemiler uydu çözümüyle karasal çözümü "
                    "karşılaştırarak saldırı altında olduklarını "
                    "görebilir. Yukarıdaki dört olayın kaynakları raporun "
                    "kaynakçasındadır.",
                    "Against spoofing YERKON is more than a backup. "
                    "Vehicles and ships can compare the satellite solution "
                    "with the terrestrial one and see that they are under "
                    "attack. The four events above are sourced in the "
                    "report's bibliography.",
                ),
            ),
        ),
    ),
)

SYSTEM = Page(
    slug="sistem",
    nav=_w("Sistem", "The system"),
    title=_w("Mimari", "The architecture"),
    lead=_w(
        "Üç parça: ölçülmüş konumlarda duran yayın birimleri, konumunu "
        "kendi hesaplayan alıcılar, ve kimlikleri güncel tutan merkezi "
        "yönetim sistemi.",
        "Three parts: broadcast units standing at surveyed positions, "
        "receivers that work out their own position, and a management "
        "system that keeps the identities current.",
    ),
    parts=(
        Part(
            kind="picture",
            picture="architecture.png",
            lines=(_w(
                "Rapordan. Alıcı menzili çift yönlü ölçümle çıkarır; "
                "merkezi yönetim sistemiyle yayın birimleri arasındaki "
                "bağ kimlik ve anahtar taşır, menzil değil.",
                "From the report, with Turkish labels. The receiver gets "
                "range by two way measurement. What runs between the "
                "management system and the units is identity and keys "
                "rather than range.",
            ),),
        ),
        Part(
            kind="points",
            heading=_w("Üç parça", "Three parts"),
            lines=(
                _w(
                    "**Yayın birimi.** Kule, yol kenarı ünitesi, "
                    "haberleşme tesisi ya da tünel sistemi gibi sabit bir "
                    "noktaya yerleştirilen verici. Alıcı konum verisi "
                    "istediğinde kimliğini, kurulumda ölçülmüş sabit "
                    "koordinatını ve doğrulama için gereken güvenlik "
                    "bilgisini yayınlar.",
                    "**The broadcast unit.** A transmitter placed on a "
                    "fixed point: a mast, a roadside unit, a "
                    "communications site, a tunnel system. When a receiver "
                    "asks for position data it broadcasts its identity, "
                    "the fixed coordinate surveyed at installation, and "
                    "the security information needed to verify it.",
                ),
                _w(
                    "**Alıcı.** Araçlara ya da taşınabilir cihazlara "
                    "yerleştirilir. Ölçümleri atalet ölçüm birimi, "
                    "tekerlek odometrisi, araç sensörleri ve dijital "
                    "harita verisiyle birleştirerek uydu olmadan da "
                    "kesintisiz bir konum kestirimi üretir.",
                    "**The receiver.** It goes in a vehicle or a portable "
                    "device. It combines its measurements with an inertial "
                    "unit, wheel odometry, vehicle sensors and digital map "
                    "data to keep producing a position without the "
                    "satellites.",
                ),
                _w(
                    "**Merkezi yönetim sistemi.** Yayın birimlerinin açık "
                    "anahtarlarını ve kimliklerini güncel tutar. Alıcı bu "
                    "listenin güncel hâlini indirir ve birimin ECDSA "
                    "imzasını doğrular, böylece taklit bir birimle "
                    "konuşmaz.",
                    "**The management system.** It keeps the units' public "
                    "keys and identities current. A receiver downloads the "
                    "current list and checks the unit's ECDSA signature, "
                    "so it will not talk to an impostor.",
                ),
            ),
        ),
        Part(
            kind="text",
            heading=_w("Neden çift yönlü ölçüm", "Why two way ranging"),
            lines=(
                _w(
                    "Varış zamanı farkına dayanan sistemlerde aynı "
                    "doğruluğa ulaşmak için yayın birimlerinin saatleri ağ "
                    "genelinde senkron olmalıdır. Bir nanosaniyenin "
                    "altında senkronizasyon atomik saat ve IEEE 1588 PTP "
                    "altyapısı demektir. Çift yönlü ölçüm bunu "
                    "gerektirmez, çünkü paketin havada geçen süresi kule "
                    "ile alıcı arasındaki kısa bir diyalogdan çıkar.",
                    "Systems built on time difference of arrival need the "
                    "units' clocks synchronised across the network to "
                    "reach the same accuracy. Synchronisation below a "
                    "nanosecond means atomic clocks and an IEEE 1588 PTP "
                    "backbone. Two way ranging does not need it, because "
                    "the packet's time of flight comes out of a short "
                    "dialogue between the unit and the receiver.",
                ),
                _w(
                    "Benzetim bu farkı ölçtü. Düzeltilmemiş 10 ppm'lik bir "
                    "saat kayması tek yönlü ölçümde 24,1 m hata bırakır, "
                    "çift yönlüde 0,3 mm. Kaymanın kendisi 0,0793 ppm "
                    "ölçüldü, ve bu projede artık tahmin olmayan tek "
                    "değerdir.",
                    "The simulation measured that difference. An "
                    "uncorrected 10 ppm clock offset leaves 24,1 m of "
                    "error one way and 0,3 mm two ways. The offset itself "
                    "was measured at 0,0793 ppm, and it is the one figure "
                    "in this project that is no longer a guess.",
                ),
                _w(
                    "Her yayın birimi kendi özel anahtarını gizli tutar ve "
                    "açık anahtarını merkezi sisteme aktarır. Anahtar 256 "
                    "bit ECC, imza ECDSA. Mesajların tekrar gönderilmesini "
                    "sıra numarası ya da sayaç engeller.",
                    "Each unit keeps its own private key and hands its "
                    "public key to the management system. The key is 256 "
                    "bit ECC and the signature is ECDSA. A sequence number "
                    "or counter stops an old message being replayed.",
                ),
            ),
        ),
        Part(
            kind="points",
            heading=_w("Üç kurulum grubu", "Three kinds of installation"),
            lines=(
                _w(
                    "**Şehir içi.** Çok sayıda kısa menzilli istasyon: baz "
                    "istasyonları, trafik levhaları ve lambaları, reklam "
                    "panoları, yol kenarı ışıklandırmaları. Semtech SX1280 "
                    "gibi bir 2,4 GHz LoRa modülü açık alanda ve görüş "
                    "hattında yaklaşık 2-4 km menzil verir.",
                    "**Urban.** Many short range stations: base station "
                    "sites, traffic signs and lights, advertising boards, "
                    "roadside lighting. A 2,4 GHz LoRa module such as the "
                    "Semtech SX1280 reaches about 2 to 4 km in the open "
                    "with line of sight.",
                ),
                _w(
                    "**Kırsal.** Az sayıda yüksek kapsamalı nokta: akıllı "
                    "ulaşım sistemi ve yol kenarı üniteleri, baz istasyonu "
                    "sahaları, demiryolu ve karayolu altyapısı. Entegre RF "
                    "amplifikatörlü bir modülle (E28-2G4M27S, +27 dBm) "
                    "menzil uygun koşullarda 8-10 km'ye çıkar. Orman, dağ "
                    "ve bayır sinyali soğurduğu için saha doğruluğunun "
                    "10-15 m bandına gerilemesi bekleniyor.",
                    "**Open country.** A few points with wide reach: "
                    "intelligent transport and roadside units, base "
                    "station sites, rail and road infrastructure. With an "
                    "integrated RF amplifier (E28-2G4M27S, +27 dBm) the "
                    "reach goes to 8 to 10 km in good conditions. Forest, "
                    "hills and mountains absorb the signal, so field "
                    "accuracy is expected to fall to the 10 to 15 m band.",
                ),
                _w(
                    "**Kritik bölge.** Tüneller, metro ve istasyon "
                    "alanları, liman ve havalimanları, sınır kapıları, "
                    "afet lojistik alanları. Qorvo DWM3000 gibi 6,5-8 GHz "
                    "bir UWB modülü 50-100 m menzil verir ve görüş hattı "
                    "üzerinde hatayı santimetre mertebesine indirir.",
                    "**Critical areas.** Tunnels, metro and station areas, "
                    "ports and airports, border crossings, disaster "
                    "logistics areas. A 6,5 to 8 GHz UWB module such as the "
                    "Qorvo DWM3000 reaches 50 to 100 m and brings the "
                    "error down to centimetres with line of sight.",
                ),
            ),
        ),
        Part(
            kind="points",
            heading=_w("Alıcı modülleri", "Receiver modules"),
            lines=(
                _w(
                    "**Yaya.** Güç tüketimi ve taşınabilirlik merkeze "
                    "alınmış. Şehir ve kırsal koridorlar için SX1280, "
                    "tünel ve kapalı alanlar için DWM3000 taşır. ESP32-S3 "
                    "üzerinden telefona BLE ile bağlanır, BNO085 ile ölü "
                    "hesaplama yapar. UWB için seramik anten, 2,4 GHz için "
                    "PCB üzeri çip anten kullanır.",
                    "**Pedestrian.** Built around power draw and "
                    "portability. It carries an SX1280 for urban and rural "
                    "corridors and a DWM3000 for tunnels and indoors. An "
                    "ESP32-S3 connects to a phone over BLE, and a BNO085 "
                    "does dead reckoning. A ceramic antenna for UWB, a "
                    "chip antenna on the board for 2,4 GHz.",
                ),
                _w(
                    "**Kara aracı.** STM32 tabanlı, LCD harita ekranlı. "
                    "Aracın CAN-Bus hattına bağlanıp tekerlek hız "
                    "sensörlerinden ve direksiyon açısından anlık veri "
                    "çeker. Tavana 3-5 dBi kazançlı çubuk anten konur.",
                    "**Road vehicle.** Built on an STM32 with an LCD map "
                    "screen. It connects to the vehicle's CAN bus and "
                    "takes live data from the wheel speed sensors and the "
                    "steering angle. A 3 to 5 dBi rod antenna goes on the "
                    "roof.",
                ),
                _w(
                    "**Nesnelerin interneti.** Kapalı ve yarı açık alan "
                    "robot filoları için. Yaygın robot işletim "
                    "sistemleriyle doğrudan konuşur, tekerlek enkoderleri "
                    "ve kendi atalet birimiyle kestirimini sürekli "
                    "iyileştirir. Çoğu depo ve fabrika senaryosunda "
                    "DWM3000 yeter.",
                    "**Internet of things.** For robot fleets indoors and "
                    "in half open areas. It talks directly to the common "
                    "robot operating systems and keeps improving its "
                    "estimate from the wheel encoders and its own inertial "
                    "unit. A DWM3000 is enough for most warehouse and "
                    "factory work.",
                ),
            ),
        ),
        Part(
            kind="table",
            heading=_w("Donanım ve fiyatı", "The hardware and its price"),
            numbers_from=2,
            rows=(
                (
                    _w("Ürün", "Product"),
                    _w("Ana bileşenler", "Main parts"),
                    _w("1 adet", "One"),
                    _w("100 adette", "At 100"),
                ),
                (
                    _w("Şehir içi yayın birimi", "Urban broadcast unit"),
                    _w("SX1280, 2,4 GHz anten, STM32, ATECC608B",
                       "SX1280, 2,4 GHz antenna, STM32, ATECC608B"),
                    _w("1983,71 TL", "1983,71 TL"),
                    _w("1366,07 TL", "1366,07 TL"),
                ),
                (
                    _w("Kırsal yayın birimi", "Rural broadcast unit"),
                    _w("E28-2G4M27S, STM32, ATECC608B",
                       "E28-2G4M27S, STM32, ATECC608B"),
                    _w("1549,67 TL", "1549,67 TL"),
                    _w("1082,68 TL", "1082,68 TL"),
                ),
                (
                    _w("Kritik bölge yayın birimi", "Critical area unit"),
                    _w("DWM3000 UWB, STM32, ATECC608B",
                       "DWM3000 UWB, STM32, ATECC608B"),
                    _w("2241,42 TL", "2241,42 TL"),
                    _w("1634,44 TL", "1634,44 TL"),
                ),
                (
                    _w("Yaya alıcısı", "Pedestrian receiver"),
                    _w("SX1280, DWM3000, ESP32-S3, BNO085, LiPo",
                       "SX1280, DWM3000, ESP32-S3, BNO085, LiPo"),
                    _w("3913,16 TL", "3913,16 TL"),
                    _w("3117,74 TL", "3117,74 TL"),
                ),
                (
                    _w("Kara aracı alıcısı", "Vehicle receiver"),
                    _w("SX1280, DWM3000, STM32, BNO085, CAN, ekran",
                       "SX1280, DWM3000, STM32, BNO085, CAN, screen"),
                    _w("5202,69 TL", "5202,69 TL"),
                    _w("4002,29 TL", "4002,29 TL"),
                ),
            ),
        ),
        Part(
            kind="points",
            lines=(
                _w(
                    "Fiyatlar 6 Eylül 2026 tarihli distribütör liste "
                    "fiyatlarından hesaplanmış ana bileşen maliyetleridir. "
                    "PCB üretimi ve dizgisi, pasif bileşenler, kablolama, "
                    "mekanik işleme, test, kalibrasyon, sertifikasyon, "
                    "vergi, kargo ve saha kurulumu dahil değildir.",
                    "The prices are main component costs worked out from "
                    "distributor list prices dated 6 September 2026. Board "
                    "manufacture and assembly, the passive components, "
                    "cabling, machining, test, calibration, certification, "
                    "tax, shipping and installation are all outside them.",
                ),
                _w(
                    "İki alıcı da hem SX1280 hem DWM3000 taşır. Bir "
                    "birimin yolda şehir birimleriyle, tünelin içinde "
                    "tünel birimleriyle hiçbir şey değiştirmeden ölçmesini "
                    "sağlayan budur.",
                    "Both receivers carry an SX1280 and a DWM3000. That is "
                    "what lets one unit range against urban units on the "
                    "road and against tunnel units inside the bore, with "
                    "nothing switched over.",
                ),
            ),
        ),
    ),
)

RESEARCH = Page(
    slug="arge",
    nav=_w("AR-GE", "Research"),
    title=_w("Araştırma soruları", "The research questions"),
    lead=_w(
        "Proje dört soruya cevap arıyor. Hiçbiri kapanmış değil, ve her "
        "birinin altında ne yapılacağı yazılı.",
        "The project is looking for answers to four questions. None of "
        "them is closed, and under each one is what will be done.",
    ),
    parts=(
        Part(
            kind="points",
            heading=_w("Dört soru", "Four questions"),
            lines=(
                _w(
                    "**Karasal yayınlar, araç sensörleri ve harita "
                    "kısıtları birleştirilerek uydu olmadan kabul "
                    "edilebilir bir konum servisi üretilebilir mi?** "
                    "Şehir içinde uygulanabilirlik test edilecek. "
                    "Çevredeki modemlerin MAC adreslerinden konum "
                    "iyileştirme, baz istasyonlarıyla üçgenleme ve görüntü "
                    "işleme de bu sürece katılacak.",
                    "**Can terrestrial broadcasts, vehicle sensors and map "
                    "constraints together produce an acceptable position "
                    "service without the satellites?** The work starts "
                    "with whether it holds up in a city. Improving "
                    "position from nearby modems' MAC addresses, "
                    "triangulating from base stations and image processing "
                    "all go into the same process.",
                ),
                _w(
                    "**Mevcut altyapıya en az müdahaleyle ölçeklenebilir "
                    "bir sistem kurulabilir mi?** 12. Ulaştırma ve "
                    "Haberleşme Şurası akıllı ulaşım sistemi altyapısının "
                    "geliştirilmesini hedef koymuştu. Yol kenarı "
                    "üniteleri ve trafik kontrol noktalarının enerji ve "
                    "haberleşme kaynağını kullanmak, montajı en ucuz "
                    "yapmanın yolu.",
                    "**Can a system be built on the existing "
                    "infrastructure with the least possible intervention?** "
                    "The 12th Transport and Communications Council set "
                    "developing intelligent transport infrastructure as a "
                    "goal. Using the power and communications already at "
                    "roadside units and traffic control points is the way "
                    "to make installation cheapest.",
                ),
                _w(
                    "**Çift yönlü ölçümün ağ trafiği ve ölçeklenebilirlik "
                    "dezavantajları azaltılabilir mi?** Varış zamanı farkı "
                    "sistemleri tek taraflı yayın yapar ve alıcıdan mesaj "
                    "almaz, bu yüzden daha az trafik üretir. Çift yönlü "
                    "ölçümde alıcı ile birim karşılıklı konuşur. TWR CDMA "
                    "gibi yaklaşımlar ve yazılım tanımlı radyo bu farkı "
                    "kapatmak için denenecek.",
                    "**Can two way ranging's traffic and scaling costs be "
                    "brought down?** Time difference systems broadcast one "
                    "way and take no message from the receiver, so they "
                    "produce less traffic. In two way ranging the receiver "
                    "and the unit talk to each other. Approaches such as "
                    "TWR CDMA and software defined radio will be tried to "
                    "close that gap.",
                ),
                _w(
                    "**Konumlandırma hizmeti sunan bir altyapının güvenlik "
                    "gereksinimleri neler?** Yayın birimlerinin taklit "
                    "edilmesine ve izinsiz alıcıların sistemi meşgul "
                    "etmesine karşı çözümler test edilecek. Modüllere "
                    "donanımsal kriptografik hızlandırıcı (ATECC608B) "
                    "girecek; kaynak ve bütünlük ECDSA imzasıyla "
                    "doğrulanacak.",
                    "**What does an infrastructure that provides "
                    "positioning need for security?** The work will test "
                    "answers to units being impersonated and to "
                    "unauthorised receivers occupying the system. The "
                    "modules get a hardware cryptographic accelerator "
                    "(ATECC608B), and an ECDSA signature verifies origin "
                    "and integrity.",
                ),
            ),
        ),
        Part(
            kind="text",
            heading=_w("Aldatmayı erken görmek", "Seeing spoofing early"),
            lines=(
                _w(
                    "Aldatma saldırısında alıcı teknik olarak tutarlı ve "
                    "yüksek güvenli görünen, ama yanlış bir konum ve hız "
                    "üretir. YERKON uydudan tamamen bağımsız çalıştığı "
                    "için bir bütünlük referansı olabilir. İki çözüm "
                    "sürekli karşılaştırılacak ve P50, P95, maksimum hata, "
                    "konum sürekliliği, yeniden yakınsama süresi, yanlış "
                    "alarm oranı, kaçırılmış tespit oranı ve zaman sapması "
                    "üzerinden değerlendirilecek.",
                    "Under a spoofing attack the receiver produces a "
                    "position and speed that look technically consistent "
                    "and confident, and are wrong. YERKON runs completely "
                    "independently of the satellites, so it can be a "
                    "reference for integrity. The two solutions will be "
                    "compared continuously and judged on P50, P95, maximum "
                    "error, position continuity, reconvergence time, false "
                    "alarm rate, missed detection rate and time offset.",
                ),
                _w(
                    "Kurulumun kendisi de araştırma konusu. Saha asistanı "
                    "yazılımı, uzmanlık gerektirmeden yerleştirme "
                    "yapılmasını hedefliyor: afet ya da askeri durumda "
                    "geçici bir ağ kuracak personel, alıcı ekranındaki "
                    "\"optimum sinyal için 120 derece yönünde 50 metre "
                    "ilerleyin\" gibi yönlendirmeleri takip ederek "
                    "birimleri yerleştirebilecek.",
                    "Installation is itself part of the research. Field "
                    "assistant software aims to let somebody place units "
                    "without expertise. Personnel setting up a temporary "
                    "network after a disaster or in a military situation "
                    "would follow directions on the receiver's screen, "
                    "such as \"move 50 metres on a bearing of 120 degrees "
                    "for the best signal\".",
                ),
            ),
        ),
        Part(
            kind="points",
            heading=_w("Pilot doğrulama", "The pilot"),
            lines=(
                _w(
                    "Seçilecek bir ulaşım koridoruna 10 ile 15 yayın "
                    "birimi kurulacak. Araç, el tipi ve sabit alıcı "
                    "prototipleri açık alan, tünel, kentsel kanyon ve "
                    "kapsama sınırı koşullarında test edilecek.",
                    "Between 10 and 15 units will go up along one "
                    "transport corridor. Vehicle, handheld and fixed "
                    "receiver prototypes will be tested in the open, in a "
                    "tunnel, in an urban canyon and at the edge of "
                    "coverage.",
                ),
                _w(
                    "Açık alanda yer gerçeği RTK-GNSS olacak. Uydunun "
                    "ulaşmadığı tünel ve kapalı alanlarda ölçülmüş "
                    "referans noktaları ve güzergâh kullanılacak.",
                    "In the open the ground truth will be RTK-GNSS. In "
                    "tunnels and indoors, where the satellites do not "
                    "reach, it will be surveyed reference points and a "
                    "surveyed route.",
                ),
                _w(
                    "Hedeflenen yatay konum hatası: P50 5 metrenin, P95 10 "
                    "metrenin altında.",
                    "The target for horizontal position error is P50 below "
                    "5 metres and P95 below 10 metres.",
                ),
                _w(
                    "Yasal ve operasyonel güvenlik nedeniyle gerçek "
                    "karıştırıcı kullanılmayacak. Onun yerine kontrollü "
                    "uydu kesintileri, kayıtlı sinyaller ve laboratuvarda "
                    "benzetilmiş aldatma senaryoları kullanılacak.",
                    "No real jammer will be used, for legal and "
                    "operational safety reasons. Controlled satellite "
                    "outages, recorded signals and spoofing scenarios "
                    "simulated in a laboratory take its place.",
                ),
            ),
        ),
    ),
)

VALUE = Page(
    slug="fayda",
    nav=_w("Fayda", "What it is for"),
    title=_w("Kime ne sağlar", "Who it is for"),
    lead=_w(
        "YERKON, konum bilgisinin kritik olduğu ama uydu sinyalinin "
        "kesildiği, zayıfladığı ya da güvenilirliğini kaybettiği "
        "durumlarda ulaşım ve haberleşme altyapılarının çalışmayı "
        "sürdürmesini hedefler.",
        "YERKON aims to keep transport and communications infrastructure "
        "working where position matters and the satellite signal is cut, "
        "weakened or no longer trustworthy.",
    ),
    parts=(
        Part(
            kind="points",
            heading=_w("Sahada", "In the field"),
            lines=(
                _w(
                    "**Acil müdahale ve afet yönetimi.** Tünelde, kapalı "
                    "alanda, kentsel kanyonda ve afet bölgesinde 112, AFAD "
                    "ve diğer ekiplerin konum takibini sürdürür. "
                    "Haberleşme bağlantısı sınırlıyken cihaz üzerindeki "
                    "harita ve sensörlerle çevrimdışı konum desteği verir.",
                    "**Emergency response and disaster management.** It "
                    "keeps position tracking going for ambulance, disaster "
                    "response and other teams in tunnels, indoors, in "
                    "urban canyons and in disaster areas. Where the "
                    "communications link is limited, the map and sensors "
                    "on the device give offline position support.",
                ),
                _w(
                    "**Karayolu, lojistik ve toplu taşıma.** Kamu araç "
                    "filoları, toplu taşıma araçları, tehlikeli madde "
                    "taşıyan araçlar ve değerli kargolar için uydudan "
                    "bağımsız bir yedek takip sağlar. Tünel ve otoyol "
                    "işletmelerinde konum sürekliliğini korur.",
                    "**Road, logistics and public transport.** It gives "
                    "public fleets, public transport, dangerous goods "
                    "vehicles and valuable cargo a backup that does not "
                    "depend on the satellites. In tunnel and motorway "
                    "operations it keeps position continuous.",
                ),
                _w(
                    "**GNSS bütünlük haritası.** Uydu ile YERKON çıktıları "
                    "arasındaki tutarsızlıklar merkezi olarak "
                    "toplandığında, Bakanlığa karıştırma ve aldatma "
                    "olaylarını haritalayan bir olay haritası çıkar.",
                    "**A map of GNSS integrity.** Collecting the "
                    "disagreements between the satellite and YERKON "
                    "solutions centrally gives the Ministry a map of "
                    "jamming and spoofing events.",
                ),
            ),
        ),
        Part(
            kind="points",
            heading=_w("Stratejik katkı", "Strategic"),
            lines=(
                _w("Yabancı uydu sistemlerine karşı teknolojik çeşitlilik.",
                   "Technological diversity against foreign satellite "
                   "systems."),
                _w("Kritik hizmetlerde tek hata noktasının azaltılması.",
                   "Fewer single points of failure in critical services."),
                _w("Kriz anında alternatif bir karasal konumlandırma "
                   "katmanı.",
                   "An alternative terrestrial positioning layer in a "
                   "crisis."),
                _w("Sınır bölgelerinde ve kritik koridorlarda dayanıklılık.",
                   "Resilience in border regions and critical corridors."),
                _w("Yerli sistem mimarisi, yazılım ve entegrasyon "
                   "yetkinliğinin geliştirilmesi.",
                   "Domestic system architecture, software and integration "
                   "capability."),
            ),
        ),
        Part(
            kind="points",
            heading=_w("Kurumsal ve akademik katkı",
                       "Institutional and academic"),
            lines=(
                _w("GNSS bağımlılığı envanterinin çıkarılması ve karıştırma "
                   "ile aldatma olaylarının ulusal haritası.",
                   "An inventory of GNSS dependency and a national map of "
                   "jamming and spoofing events."),
                _w("İlgili kurumlar arasında ortak olay verisi, ve hizmet "
                   "düzeyi ile bütünlük kriterlerinin tanımlanmasına veri.",
                   "Shared event data between the institutions involved, "
                   "and data for defining service level and integrity "
                   "criteria."),
                _w("Çok sensörlü bir konumlandırma veri seti ile GNSS reddi "
                   "ve aldatma senaryoları.",
                   "A multi sensor positioning dataset with GNSS denial "
                   "and spoofing scenarios."),
                _w("Yerli konumlandırma algoritmaları, ve üniversite, kamu "
                   "ve sanayi arasında ortak araştırma.",
                   "Domestic positioning algorithms, and research shared "
                   "between universities, the state and industry."),
            ),
        ),
        Part(
            kind="text",
            heading=_w("Ticarileşme", "Turning it into a business"),
            lines=(
                _w(
                    "Model kamu altyapısını özelleştirmek değil. Kamu "
                    "çekirdeği üzerinde kontrollü ek hizmetlerle işletme "
                    "maliyetini karşılayacak bir yapı hedefleniyor.",
                    "The model is not privatising public infrastructure. "
                    "The aim is controlled extra services on top of a "
                    "public core, enough to cover what running it costs.",
                ),
                _w(
                    "İlk alan, uydu erişiminin düzenli olarak kesildiği "
                    "tüneller ve kritik ulaşım koridorları. Buralarda "
                    "ihtiyaç açıkça tanımlanabildiği ve performans "
                    "kontrollü olarak ölçülebildiği için ilk uygulamaların "
                    "sınırları nettir. Pilot sonucunda konum doğruluğu, "
                    "kapsama, hizmet sürekliliği, gerekli birim yoğunluğu "
                    "ve mevcut altyapının ne kadar yeniden kullanılabildiği "
                    "belirlenecek.",
                    "The first area is tunnels and critical transport "
                    "corridors, where satellite access is cut regularly. "
                    "There the need can be stated plainly and performance "
                    "measured under control, so the boundaries of a first "
                    "deployment are clear. The pilot is what settles "
                    "accuracy, coverage, service continuity, how dense the "
                    "units have to be, and how much of the existing "
                    "infrastructure can be reused.",
                ),
                _w(
                    "Kısa vadede ticari hazır donanımla pilot "
                    "doğrulanacak, yerli yazılım ve protokol geliştirilecek. "
                    "Orta vadede yerli gömülü sistem ve RF firmalarıyla "
                    "ortaklık ve kritik bileşenlerde çift kaynaklı tedarik "
                    "hedefleniyor. Uzun vadede komşu ve gelişmekte olan "
                    "ülkelere kurulum ve entegrasyon hizmeti, ve protokol "
                    "ile alıcı ailesinin lisanslanması.",
                    "In the short term the pilot gets validated with "
                    "commercial off the shelf hardware while the domestic "
                    "software and protocol are written. In the medium term "
                    "the aim is partnership with domestic embedded and RF "
                    "firms and two sources for the critical components. In "
                    "the long term, installation and integration for "
                    "neighbouring and developing countries, and licensing "
                    "the protocol and the receiver family.",
                ),
            ),
        ),
        Part(
            kind="points",
            heading=_w("Ürünler", "The products"),
            lines=(
                _w(
                    "**Altyapı.** Şehir içi yayın birimi, kırsal yayın "
                    "kartı, kritik bölge hassas konumlandırma birimi, ve "
                    "güvenli anahtar ile yayın birimi yönetim sistemi.",
                    "**Infrastructure.** The urban broadcast unit, the "
                    "rural broadcast board, the precise unit for critical "
                    "areas, and the secure key and unit management system.",
                ),
                _w(
                    "**Kullanıcı.** Araç konumlandırma birimi, taşınabilir "
                    "saha alıcısı, nesnelerin interneti alıcısı. "
                    "Sonrasında insansız hava aracı entegrasyon modülü ile "
                    "demiryolu ve denizcilik alıcısı.",
                    "**User.** The vehicle unit, the portable field "
                    "receiver and the internet of things receiver. Later, "
                    "an integration module for unmanned aircraft and a "
                    "receiver for rail and maritime.",
                ),
                _w(
                    "**Yazılım.** Merkezi yönetim paneli, GNSS bütünlük ve "
                    "olay haritası, filo ile kritik altyapı arayüzleri, "
                    "analiz ve raporlama, çevrimdışı yayın birimi konum "
                    "haritası.",
                    "**Software.** The management panel, the GNSS "
                    "integrity and event map, interfaces for fleets and "
                    "critical infrastructure, analysis and reporting, and "
                    "an offline map of where the units are.",
                ),
            ),
        ),
    ),
)

RESULTS = Page(
    slug="sonuclar",
    nav=_w("Sonuçlar", "Results"),
    title=_w("Karşılaştırma tablosu", "The comparison table"),
    lead=_w(
        "On üç sistem, aynı sütunlarla yan yana. Koyu zeminli üç satır "
        "benzetimin doldurduğu YERKON satırları; geri kalanı kendi "
        "kaynaklarının yayımladığı değerler. Bir hücreye ne yapıldığı "
        "altındaki notta yazıyor, ve boş bir hücre kaynağın o sütuna "
        "uyan bir şey yayımlamadığı anlamına geliyor.",
        "Thirteen systems side by side under the same columns. The three "
        "shaded rows are the YERKON rows the simulation filled; the rest "
        "are what their own sources publish. What was done to a cell is "
        "in the note under it, and an empty cell means the source "
        "publishes nothing that fits that column.",
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
                        "Denenen sabitlemelerin geçerli bir konum "
                        "üretenleri. Yalnızca modellenen başarısızlıkları "
                        "sayar, bir hizmet kullanılabilirliği değildir.",
                        "The share of attempted fixes that produced a valid "
                        "position. It counts modelled failures only and is "
                        "not a service availability figure.",
                    ),
                ),
                (
                    _w("Alan", "Area"),
                    _w(
                        "Bir konum üretmeye yetecek kadar birimin "
                        "erişilebilir olduğu zemin, gerçek arazi üzerinde "
                        "taranarak. Bir paketin ulaştığı zemin değildir.",
                        "The ground where enough units are reachable for a "
                        "position, swept over the real terrain. It is not "
                        "the ground a packet reaches.",
                    ),
                ),
                (
                    _w("CAPEX", "CAPEX"),
                    _w(
                        "Yayın birimi donanım maliyetinin hizmet alanına "
                        "bölümü. Yalnızca ana donanım.",
                        "Unit hardware cost divided by the service area. "
                        "Main hardware only.",
                    ),
                ),
                (
                    _w("OPEX", "OPEX"),
                    _w(
                        "km² başına yıllık işletme maliyeti. Rapor bu "
                        "sütunu boş bırakır; buradaki değer adlandırılmış "
                        "yinelenen kalemlerden gelir.",
                        "Yearly operating cost per km². The report leaves "
                        "this column empty; this one comes from an "
                        "itemised inventory.",
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
                    "bir tünel yaklaşık iki yüz dönümdür; buna bölmek "
                    "büyük bir sayıyı yargıyla değil aritmetikle üretir. "
                    "Tünel bir çizgiye hizmet eder, bu yüzden güzergâh "
                    "kilometresi başına maliyetle karşılaştırılır.",
                    "**The tunnel's cost per km² does not compare to the "
                    "other rows.** Twelve metres wide over two kilometres "
                    "is a fiftieth of a square kilometre, so dividing by it "
                    "produces a large number by arithmetic rather than by "
                    "judgement. A tunnel serves a line, so compare it on "
                    "cost per route kilometre.",
                ),
                _w(
                    "**Hizmet alanı, bir konumun alınabildiği yerdir**, bir "
                    "paketin ulaştığı yer değil. Kırsalda bir paket, konum "
                    "alınabilen zeminin 2,6 katına ulaşır.",
                    "**The service area is where a position can be had**, "
                    "not where a packet arrives. In open country a packet "
                    "reaches 2,6 times the ground a position can be had on.",
                ),
                _w(
                    "**Yüzdeler aynı metrik değil.** Uydu sağlayıcılarının "
                    "yayımladığı kullanılabilirlik farklı test "
                    "tanımlarına, farklı sürelere ve farklı eşiklere "
                    "dayanır. Aynı protokolün sonucu gibi okunmamalıdır.",
                    "**The percentages are not the same metric.** The "
                    "availability the satellite providers publish rests on "
                    "different test definitions, durations and thresholds. "
                    "It should not be read as the result of one protocol.",
                ),
            ),
        ),
        Part(
            kind="text",
            heading=_w("Hızlı okuma", "The fast reading"),
            lines=(
                _w(
                    "Benzetimdeki **Hızlı dene** düğmesi ve komut "
                    "satırındaki `--fast` aynı iki figürü kabalaştırır: "
                    "gölgeler sekiz yerine bir kez çekilir, zemin profili "
                    "10 m yerine sabit 64 örnekle okunur. Koşu on beş "
                    "dakikadan bir dakikaya iner.",
                    "The **fast** button in the simulation and `--fast` on "
                    "the command line coarsen the same two figures: the "
                    "shadows are drawn once instead of pooled over eight, "
                    "and the ground profile is read at a fixed 64 samples "
                    "instead of every 10 m. A run drops from fifteen "
                    "minutes to about one.",
                ),
                _w(
                    "İki kabalık da kaybı eksik okur, yani hızlı bir cevap "
                    "yerleşimi kayırır: kırsal satırın P95'i 4,13 m iyimser "
                    "çıkıyor. Bu yüzden hızlı okumada kötü görünen bir "
                    "satır gerçekten kötüdür, ve bu sayfa yalnızca "
                    "yayımlanan koşuyu gösterir.",
                    "Both coarsenings read the loss low, so a fast answer "
                    "flatters the deployment: the rural row's P95 came out "
                    "4,13 m optimistic. A row that looks bad under a fast "
                    "reading is genuinely bad, and this page shows the "
                    "published run only.",
                ),
            ),
        ),
    ),
)

SIMULATION = Page(
    slug="benzetim",
    nav=_w("Benzetim", "The simulation"),
    title=_w("Benzetim", "The simulation"),
    lead=_w(
        "Benzetim bu projenin bir parçası, tamamı değil. Tek bir işi "
        "vardı: karşılaştırma tablosunun üç YERKON satırını tahminle "
        "değil, her sayısı izlenebilir bir modelle doldurmak. Sahada "
        "ölçüm değildir.",
        "The simulation is one part of this project rather than the whole "
        "of it. It had one job: to fill the three YERKON rows of the "
        "comparison table with a model whose every number can be traced, "
        "instead of with an estimate. It is not a field measurement.",
    ),
    parts=(
        Part(
            kind="picture",
            picture="simulator.png",
            lines=(_w(
                "Şehir içi satırı: Kızılay'ın gerçek zemini, aydınlatma "
                "direklerine monte 36 yayın birimi, ve zemine boyanmış "
                "kapsama taraması. Renkler kaç birimin eriştiğini "
                "gösteriyor, ve bir konum için dört gerekiyor.",
                "The urban row: the real ground at Kızılay, 36 broadcast "
                "units on lighting columns, and the swept coverage painted "
                "on the ground. The colours count how many units reach, "
                "and a position needs four.",
            ),),
        ),
        Part(
            kind="points",
            heading=_w("Zemin gerçek", "The ground is real"),
            lines=(
                _w(
                    "Üç satır da gerçek Ankara zemininin üzerinde durur. "
                    "Zemin Copernicus 30 m DEM'inden bir kez getirilip "
                    "paketin içine işlenmiştir, yani bir klon tabloyu ağa "
                    "hiç çıkmadan yeniden üretir.",
                    "All three rows stand on real ground near Ankara, "
                    "fetched once from the Copernicus 30 m DEM and baked "
                    "into the package, so a clone reproduces the table "
                    "without touching the network.",
                ),
                _w(
                    "Şehir Kızılay'dır, bir kenarı üç kilometre ve 91 m "
                    "iniş çıkışla. Açık arazi Polatlı ovasıdır, bir kenarı "
                    "yirmi kilometre ve 486 m rölyefle. Tünel "
                    "Kızılcahamam'daki dağların içinden geçen gerçek bir 2 "
                    "km'lik güzergâhtır.",
                    "The city is Kızılay, three kilometres on a side with "
                    "91 m of rise and fall. The open country is the "
                    "Polatlı plain, twenty kilometres on a side with 486 m "
                    "of relief. The tunnel is a real two kilometre bore "
                    "through the mountains at Kızılcahamam.",
                ),
                _w(
                    "Hiçbir yerde düz zemin seçeneği yok. Düz bir düzlem "
                    "bu modelin çizebileceği en tarafsız değil en elverişli "
                    "yüzeydir.",
                    "Nowhere is there a flat option. A flat plane is not "
                    "the most neutral surface this model can draw, it is "
                    "the most flattering one.",
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
                    "değil, link bütçesinin sonucudur, ve aynı hesap "
                    "bağlantının kapanıp kapanmadığına da ne kadar hassas "
                    "ölçtüğüne de karar verir.",
                    "There is no maximum range constant anywhere. Range is "
                    "a result rather than an input, and the same "
                    "calculation decides both whether a link closes and "
                    "how precisely it measures.",
                ),
                _w(
                    "İki ışınlı zemin yansıması düz zeminde bile çalışır: "
                    "kırılma mesafesinin ötesinde doğrudan ışınla zeminden "
                    "yansıyan ışın ters fazda gelip birbirini götürür, ve "
                    "o mesafe anten yüksekliğiyle doğrusal olduğu için "
                    "alçak montaj pahalıdır.",
                    "The two ray ground reflection works even over flat "
                    "ground: past the break distance the direct ray and "
                    "the reflected one arrive out of phase and cancel, and "
                    "because that distance scales with antenna height, "
                    "mounting low is expensive.",
                ),
                _w(
                    "Kırınım en kötü tek nokta üzerinden değil, bütün "
                    "profil üzerinden hesaplanır: ITU-R P.526-15 §4.5.2, "
                    "delta-Bullington. Kızılay'da bir bağlantının ortanca "
                    "üç engeli var, en kötüsünün on altı.",
                    "Diffraction comes from the whole profile rather than "
                    "from its worst single point: ITU-R P.526-15 §4.5.2, "
                    "delta Bullington. A link across Kızılay has three "
                    "obstacles at the median and sixteen at the worst.",
                ),
                _w(
                    "Zemin profili on metrede bir okunur. Sabit 64 örnekte "
                    "6,9 km'lik bir kırsal bağlantı 108 m'de bir okunuyordu "
                    "ve kırınımı 37,60 dB yerine 31,28 dB veriyordu.",
                    "The ground profile is read every ten metres. At a "
                    "fixed 64 samples a 6,9 km rural link was read every "
                    "108 m, and it put diffraction at 31,28 dB where the "
                    "answer is 37,60.",
                ),
                _w(
                    "Bir bağlantı yansımayla kırınımın toplamını değil, "
                    "büyüğünü öder. İkisi de aynı yer parçasının aynı "
                    "bağlantıya yaptığını anlatır, ve toplamak o yer "
                    "parçasını iki kez faturalandırmaktır.",
                    "A link pays the larger of reflection and diffraction "
                    "rather than their sum. Both describe what the same "
                    "piece of ground does to the same link, and adding "
                    "them bills that ground twice.",
                ),
                _w(
                    "Gölgeleme ikisinin üstüne eklenir ve genişliği yolun "
                    "açık olup olmamasına bağlıdır: görüş hattı varken 4 "
                    "dB, yokken 7,82 (3GPP TR 38.901). Tablo sekiz "
                    "çekilişin havuzudur, tek bir çekilişin değil.",
                    "Shadowing sits on top of both, and its width depends "
                    "on whether the path is clear: 4 dB with line of "
                    "sight, 7,82 without (3GPP TR 38.901). The table pools "
                    "eight draws rather than showing one.",
                ),
            ),
        ),
        Part(
            kind="points",
            heading=_w("Alışveriş ve kestirici",
                       "The exchange and the estimator"),
            lines=(
                _w(
                    "Bir menzil link bütçesinden okunmaz. İki telsiz "
                    "çerçeve alışverişi yapar, ve SX1280'de SF10'da bir "
                    "çift yönlü alışveriş 47,86 ms sürer.",
                    "A range is not read off a link budget. Two radios "
                    "exchange frames, and on the SX1280 at SF10 one two way "
                    "exchange takes 47,86 ms.",
                ),
                _w(
                    "Altı birime karşı bir tur 239 ms sürer. Bu sürede 100 "
                    "km/sa giden bir araç 6,7 m yol alır, yani bir turun "
                    "menzilleri eşzamanlı değildir ve öyleymiş gibi "
                    "çözülmez.",
                    "A round against six units takes 239 ms. A car doing "
                    "100 km/h covers 6,7 m in that time, so the ranges in "
                    "one round are not simultaneous and are not solved as "
                    "though they were.",
                ),
                _w(
                    "Kestirici gerçeği hiç görmez. Yalnızca gözlemleri "
                    "görür: ölçülmüş mesafe, birimin ölçülmüş konumu, bir "
                    "zaman damgası ve bir varyans.",
                    "The estimator never sees the truth. It sees "
                    "observations: a measured distance, a unit's surveyed "
                    "position, a timestamp and a variance.",
                ),
                _w(
                    "Hiçbir yerde yükseklik kısıtı yok. Yol kenarına "
                    "dizilmiş birimler düşeyi neredeyse gözlenemez bırakır, "
                    "ve VPE sütunu bunu gizlemek yerine bildirir.",
                    "There is no height constraint anywhere. Units strung "
                    "along a roadside leave the vertical barely "
                    "observable, and the VPE column reports that instead of "
                    "hiding it.",
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
                    "her zaman pozitiftir, yani ortalamayla asla "
                    "kaybolmaz.",
                    "**A blocked path measures long.** The signal goes over "
                    "the obstacle and the range times that detour. The "
                    "error is always positive, so averaging never removes "
                    "it.",
                ),
                _w(
                    "**Etüt hatası kurulumun özelliğidir**, birim başına "
                    "bir kez çekilir ve tutulur. Tünelin HPE P50 değeri "
                    "kusursuz etütte 0,24 m, 15 cm'lik etüt hatasında 1,76 "
                    "m: birimleri ölçtüğünden daha iyi konumlanamazsın.",
                    "**A survey error belongs to an installation**, drawn "
                    "once per unit and kept. The tunnel's HPE P50 is 0,24 "
                    "m with perfect survey and 1,76 m with 15 cm of it: you "
                    "cannot position better than you surveyed.",
                ),
                _w(
                    "**Kaybolan bir paket hiçbir şey üretmez.** Bant 2,4 "
                    "GHz kablosuz ağlarla aynıdır: şehirde kayıp %15, açık "
                    "yolda %5, tünelde sıfır.",
                    "**A lost packet produces nothing.** The band is shared "
                    "with 2,4 GHz wireless networks: 15% loss in the city, "
                    "5% on the open road, none in the tunnel.",
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
                    "Güvenlik katmanı da yok. İmza doğrulaması ve anahtar "
                    "yönetimi mimarinin parçası, benzetimin değil.",
                    "The security layer is absent too. Signature checking "
                    "and key management belong to the architecture rather "
                    "than to the simulation.",
                ),
            ),
        ),
        Part(
            kind="text",
            heading=_w("Kendi makinende", "On your own machine"),
            lines=(
                _w(
                    "Benzetim bir web sayfasının içinde durmaz. Bir koşu "
                    "üç işlemciyi dakikalarca meşgul eder ve gerçek zemin "
                    "verisini okur. Kurulumu dört komut, ve açılan "
                    "sayfada her ayar canlıdır: birimler elle taşınır, yeni "
                    "bir yer getirilir, ve üç satır da yeniden koşar.",
                    "The simulation does not live inside a web page. A run "
                    "keeps three processors busy for minutes and reads real "
                    "terrain data. Four commands install it, and on the "
                    "page it opens every setting is live: units are dragged "
                    "by hand, new ground is fetched, and all three rows run "
                    "again.",
                ),
            ),
        ),
        Part(
            kind="code",
            code=_w(
                "git clone https://github.com/ysoktar/yerkon\n"
                "cd yerkon\n"
                "pip install -e \".[dev]\"\n"
                "yerkon view",
                "git clone https://github.com/ysoktar/yerkon\n"
                "cd yerkon\n"
                "pip install -e \".[dev]\"\n"
                "yerkon view",
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
                   "sayfaları, ve SX1280 uzun menzil testi.",
                   "Semtech SX1280, EBYTE E28-2G4M27S and Qorvo DWM3000 "
                   "datasheets, and the SX1280 long range test."),
                _w("DigiKey, LCSC ve Mouser liste fiyatları, 6 Eylül 2026. "
                   "Kur 4 Eylül 2026.",
                   "DigiKey, LCSC and Mouser list prices, 6 September 2026. "
                   "Exchange rate 4 September 2026."),
                _w("Karşılaştırma tablosunun uydu ve karasal satırları: "
                   "GPS.gov, European GNSS Service Centre, GOST 32454-2013, "
                   "ICAO Annex 10, QZSS, ISRO, ION, JRC ve KRISO. Hepsi "
                   "raporun kaynakçasında dipnotlarıyla.",
                   "The satellite and terrestrial rows of the comparison "
                   "table: GPS.gov, the European GNSS Service Centre, GOST "
                   "32454-2013, ICAO Annex 10, QZSS, ISRO, ION, the JRC and "
                   "KRISO. All of them are footnoted in the report's "
                   "bibliography."),
            ),
        ),
        Part(
            kind="code",
            heading=_w("Tabloyu yeniden üretmek", "Reproducing the table"),
            code=_w(
                "pip install -e \".[dev]\"\n"
                "yerkon table          # yayımlanan sayılar, ~15 dk\n"
                "yerkon table --fast   # denemek için, ~1 dk, yayımlanmaz\n"
                "yerkon view           # bu site ve benzetim",
                "pip install -e \".[dev]\"\n"
                "yerkon table          # the published numbers, ~15 min\n"
                "yerkon table --fast   # for trying things, ~1 min\n"
                "yerkon view           # this site and the simulation",
            ),
        ),
        Part(
            kind="points",
            lines=(
                _w(
                    "Zemin pakete işlenmiştir, yani tablo ağa hiç çıkmadan "
                    "yeniden üretilir. Tohum sabittir.",
                    "The ground is baked into the package, so the table "
                    "reproduces with no network at all. The seed is fixed.",
                ),
                _w("`CONTEXT.md` sözlüktür: her terimin kodda kullanılan "
                   "adı ve raporda kullanılan karşılığı.",
                   "`CONTEXT.md` is the glossary: the name the code uses "
                   "for each term beside the one the report uses."),
                _w("`docs/adr/` her kararı ve neyin yerine geçtiğini tutar. "
                   "`docs/HANDOFF.md` açık soruları tutar.",
                   "`docs/adr/` holds every decision and what it replaced. "
                   "`docs/HANDOFF.md` holds the open questions."),
            ),
        ),
        Part(
            kind="points",
            heading=_w("Proje", "The project"),
            lines=(
                _w(
                    "YERKON, Ulaştırma ve Altyapı Bakanlığı UDHAM'ın "
                    "“Ulaşan ve Erişen Türkiye 2053” üniversiteler "
                    "arası fikir yarışmasına sunulan bir fikirdir, Temmuz "
                    "2026.",
                    "YERKON is an idea submitted to UDHAM's “Ulaşan ve "
                    "Erişen Türkiye 2053” inter-university competition, "
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
                    "Bu depo raporun kendisi değil, raporun karşılaştırma "
                    "tablosundaki üç YERKON satırını üreten benzetimdir.",
                    "This repository is not the report. It is the "
                    "simulation that produces the three YERKON rows of its "
                    "comparison table.",
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
PAGES = (HOME, WHY, SYSTEM, RESEARCH, VALUE, RESULTS, SIMULATION, SOURCES)

#: Where the simulator lives, and what the link to it is called.
SIMULATOR = "/simulasyon"
SIMULATOR_LABEL = _w("Simülasyon", "Simulator")

#: The one line under the wordmark, on every page.
STANDFIRST = _w(
    "Karasal konumlandırma yedek katmanı",
    "A terrestrial positioning backup layer",
)

BACK_TO_SITE = _w("Siteye dön", "Back to the site")

LANGUAGES = (("tr", "TR"), ("en", "EN"))

#: The three rows on the home page, by key, with what each is called.
HEADLINE = (
    ("urban", _w("Şehir içi", "Urban")),
    ("rural", _w("Kırsal", "Rural")),
    ("tunnel", _w("Tünel", "Tunnel")),
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
    "YERKON, Ulaştırma ve Altyapı Bakanlığı UDHAM fikir yarışmasına "
    "sunulan bir proje. Tablodaki sayılar benzetimin yayımlanan "
    "koşusundan gelir, ve neyi modellemediği Benzetim sayfasında yazıyor.",
    "YERKON is a project submitted to the UDHAM idea competition of the "
    "Ministry of Transport and Infrastructure. The numbers in the table "
    "come from the simulation's published run, and what it does not model "
    "is written on the simulation page.",
)

WEIGHTING = _w(
    "Benzetimin doldurduğu üç satır, yatay hatanın doksan beşinci "
    "yüzdeliğinde. Her biri gerçek bir Ankara zemininin üzerinde koşuldu.",
    "The three rows the simulation filled, at the ninety fifth percentile "
    "of horizontal error. Each one was run over real ground near Ankara.",
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
    where: Optional[Where] = None,
) -> str:
    """One page as a whole HTML document.

    ``where`` decides how the links are spelled. Left out, they are the
    addresses a running server answers.
    """
    where = where or Where(language=language)
    body = [
        _header(page, language, where),
        '<main>',
        '<h1>{}</h1>'.format(_said(page.title, language)),
        '<p class="lead">{}</p>'.format(_said(page.lead, language)),
    ]
    for part in page.parts:
        body.append(_part(part, language, published, where))
    body += ['</main>', _footer(language)]
    # The home page is called YERKON, and "YERKON · YERKON" is not a
    # title.
    named = page.title.said(language)
    return _document(
        title=named if named == "YERKON" else "{} · YERKON".format(named),
        language=language,
        stylesheet=where.asset("site.css"),
        script=where.asset("theme.js"),
        body="\n".join(body),
    )


def _document(title: str, language: str, stylesheet: str, script: str,
              body: str) -> str:
    return (
        "<!doctype html>\n"
        '<html lang="{language}">\n'
        "<head>\n"
        '<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        "<title>{title}</title>\n"
        '<link rel="stylesheet" href="{stylesheet}">\n'
        '<script src="{script}" defer></script>\n'
        "</head>\n"
        "<body>\n{body}\n</body>\n</html>\n"
    ).format(language=language, title=html.escape(title),
             stylesheet=html.escape(stylesheet, quote=True),
             script=html.escape(script, quote=True), body=body)


def _header(page: Page, language: str, where: Where) -> str:
    links = []
    for other in PAGES:
        here = ' class="here"' if other.slug == page.slug else ""
        links.append('<a href="{}"{}>{}</a>'.format(
            where.page(other), here, _said(other.nav, language)
        ))
    tongues = "".join(
        '<a href="{}"{}>{}</a>'.format(
            where.tongue(page, code),
            ' class="here"' if code == language else "", label,
        )
        for code, label in LANGUAGES
    )
    return (
        "<header>\n"
        '<a class="brand" href="{home}"><b>YERKON</b> '
        "<span>{standfirst}</span></a>\n"
        '<nav class="pages">{links}</nav>\n'
        '<nav class="tongues">{tongues}'
        '<button class="theme" id="theme" type="button" hidden></button>'
        "</nav>\n"
        '<a class="run" href="{simulator}">{label} →</a>\n'
        "</header>"
    ).format(
        home=where.page(HOME),
        standfirst=_said(STANDFIRST, language),
        links="".join(links),
        tongues=tongues,
        simulator=where.simulator(),
        label=_said(SIMULATOR_LABEL, language),
    )


def _footer(language: str) -> str:
    return "<footer><p>{}</p></footer>".format(_said(FOOTER, language))


def _part(part: Part, language: str, published, where: Optional[Where] = None) -> str:
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
        # In a scroller, because a price column that will not wrap is
        # wider than a phone and would otherwise push the whole page
        # sideways.
        drawn = '<div class="scroll">{}</div>'.format(_table(
            [[_said(cell, language) for cell in row] for row in part.rows],
            numeric_from=part.numbers_from,
        ))
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
        where = where or Where(language=language)
        drawn = "".join(
            '<a class="card" href="{}"><b>{}</b><span>{}</span></a>'.format(
                where.page(other), _said(other.nav, language),
                _said(other.lead, language),
            )
            for other in PAGES if other.slug
        )
        drawn = '<div class="cards">{}</div>'.format(drawn)
    elif part.kind == "picture":
        where = where or Where(language=language)
        drawn = '<figure><img src="{}" alt="{}"><figcaption>{}</figcaption>' \
            "</figure>".format(
                html.escape(where.asset(part.picture), quote=True),
                html.escape(part.lines[0].said(language), quote=True),
                _said(part.lines[0], language),
            )
    elif part.kind == "shows" and part.shows == "headline":
        drawn = _headline(published, language)
    elif part.kind == "shows" and part.shows == "published":
        drawn = _published(published, language)
    else:
        raise ValueError("no way to draw a {} part".format(part.kind))
    return "<section>{}{}</section>".format(heading, drawn)


def _headline(published, language: str) -> str:
    """One figure per row on the home page: the ninety fifth percentile.

    The fiftieth is the flattering one and the ninety fifth is the one a
    service level rests on, so this shows the ninety fifth.
    """
    if published is None:
        return '<p class="warn">{}</p>'.format(_said(NO_RUN, language))
    figures = []
    for key, label in HEADLINE:
        shown = decimal_comma(published.row(key).hpe_p95_m, 2) + " m"
        figures.append(
            '<div class="figure"><b>{}</b><span>{}</span></div>'.format(
                shown, _said(label, language)
            )
        )
    return (
        '<div class="figures">{}</div>'
        '<p class="under">{}</p>'
    ).format("".join(figures), _said(WEIGHTING, language))


def _published(published, language: str, table=None) -> str:
    """Every system in the table, ours read from the run.

    The other systems' rows are published figures and come from
    `comparison.toml`; ours come from `published.toml`, which a run
    writes. A marker is numbered where it first appears rather than in
    the file, so a note can be added without renumbering anything
    (ADR-0069).
    """
    if published is None:
        return '<p class="warn">{}</p>'.format(_said(NO_RUN, language))
    if table is None:
        from yerkon import comparison

        table = comparison.read()

    numbered: dict = {}

    def mark(key: str) -> str:
        if key not in numbered:
            numbered[key] = len(numbered) + 1
        at = numbered[key]
        return (
            '<sup class="note"><a id="back{0}" href="#note{0}">{0}</a>'
            "</sup>".format(at)
        )

    def cell(text: str) -> str:
        from yerkon.comparison import keys_of, without_markers

        shown = html.escape(without_markers(text))
        return shown + "".join(mark(key) for key in keys_of(text))

    head = [_said(column, language) for column in COLUMNS]
    # The warning about the availability column belongs to the column.
    head[6] += mark(table.availability_note)

    body = []
    for row in table.rows:
        body.append(
            [html.escape(row.system), html.escape(row.technology),
             html.escape(row.environment)] + [cell(one) for one in row.cells]
        )
    ours = len(body)
    for key, row in zip(published.keys, published.rows):
        cells = list(row.cells())
        marked = [html.escape(one) for one in cells[:3]]
        marked[0] += mark(table.yerkon[key])
        rest = [html.escape(one) for one in cells[3:]]
        rest[3] += mark(table.yerkon["availability"])
        rest[5] += mark(table.yerkon["capex"])
        body.append(marked + rest)
    # The template is escaped once, by `_said`. What comes out of the
    # record is escaped here, and escaping the result again would put
    # `&amp;#x27;` on the page where an apostrophe belongs.
    note = _said(RUN_NOTE, language).format(
        run_on=html.escape(published.run_on),
        source=html.escape(published.source),
        draws=published.shadow_draws,
        spacing=decimal_comma(published.profile_spacing_m, 0),
    )
    listed = "".join(
        '<li id="note{0}">{1} <a class="back" href="#back{0}">↑</a></li>'
        .format(at, _marked(table.said(key, language)))
        for key, at in sorted(numbered.items(), key=lambda pair: pair[1])
    )
    return (
        '<div class="wide"><div class="scroll">{table}</div>'
        '<p class="under">{note}</p></div>'
        '<ol class="notes">{notes}</ol>'
    ).format(
        table=_table([head] + body, numeric_from=3, ours_from=ours),
        note=note, notes=listed,
    )


def _table(
    rows: Sequence[Sequence[str]],
    numeric_from: int = 99,
    ours_from: Optional[int] = None,
) -> str:
    """One table. ``ours_from`` marks where this project's rows start."""
    head, body = rows[0], rows[1:]
    out = ["<table><thead><tr>"]
    for at, cell in enumerate(head):
        out.append('<th{}>{}</th>'.format(
            ' class="num"' if at >= numeric_from else "", cell
        ))
    out.append("</tr></thead><tbody>")
    for line, row in enumerate(body):
        ours = ours_from is not None and line >= ours_from
        out.append('<tr class="ours">' if ours else "<tr>")
        for at, cell in enumerate(row):
            out.append('<td{}>{}</td>'.format(
                ' class="num"' if at >= numeric_from else "", cell
            ))
        out.append("</tr>")
    out.append("</tbody></table>")
    return "".join(out)


# --- writing it out -------------------------------------------------------

#: Files copied beside the pages rather than rendered.
CARRIED = ("site.css", "theme.js", "road.png", "gnss.png",
           "architecture.png", "simulator.png")

STATIC = pathlib.Path(__file__).parent / "static"


def write_pages(into, published=None) -> tuple:
    """Draw the whole site into a folder, both languages.

    For somewhere that serves files and runs nothing, GitHub Pages being
    the one this was written for. The simulator does not come: it needs
    the engine, and what comes instead is a page saying so (ADR-0065).

    Turkish at the root and English under `en/`, because the report is
    Turkish and whoever opens the address without asking for a language
    should get the one the project is written in.
    """
    into = pathlib.Path(into)
    (into / "en").mkdir(parents=True, exist_ok=True)
    written = []
    for code, _ in LANGUAGES:
        folder = into if code == "tr" else into / code
        where = Where(language=code, loose=True)
        for page in PAGES:
            path = folder / Where.file(page)
            path.write_text(
                render(page, code, published, where), encoding="utf-8"
            )
            written.append(path)
    for name in CARRIED:
        path = into / name
        path.write_bytes((STATIC / name).read_bytes())
        written.append(path)
    # Without this the pages are handed to Jekyll, which is a static site
    # generator this site is not written for.
    marker = into / ".nojekyll"
    marker.write_text("", encoding="utf-8")
    written.append(marker)
    # A page that has been renamed or dropped leaves its file behind,
    # and a stale page nothing links to is still a page the address
    # serves. Only the pages are swept: the folder holds other things.
    kept = set(written)
    for folder in (into, into / "en"):
        for stale in folder.glob("*.html"):
            if stale not in kept:
                stale.unlink()
    return tuple(written)


def _said(words: Words, language: str) -> str:
    """One phrase, escaped, with its emphasis and its code kept."""
    return _marked(words.said(language))


def _marked(text: str) -> str:
    out = html.escape(text)
    out = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", out)
    out = re.sub(r"`(.+?)`", r"<code>\1</code>", out)
    return out
