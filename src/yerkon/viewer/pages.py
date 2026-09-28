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

import hashlib
import html
import pathlib
import re
from dataclasses import dataclass
from typing import Optional, Sequence

from yerkon import sources
from yerkon.viewer import costing
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
    #: Closed until opened: a long table most readers do not need, kept
    #: on the page for the ones who do.
    folded: bool = False
    #: A section inside the one before it, so its heading is a level down.
    sub: bool = False


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
        # Served, this is the running simulator. Loose, it is the same
        # simulator running in the visitor's browser, one folder up from
        # the English pages (ADR-0080).
        if not self.loose:
            return SIMULATOR
        if self.language == "en":
            return "../" + BROWSER_SIMULATOR + "?dil=en"
        return BROWSER_SIMULATOR

    @staticmethod
    def file(page: "Page") -> str:
        return "index.html" if not page.slug else page.slug + ".html"


# --- what the site says ---------------------------------------------------

HOME = Page(
    slug="",
    nav=_w("Anasayfa", "Home"),
    title=_w("YERKON", "YERKON"),
    lead=_w(
        "YERKON, karayolunda konumun yabancı uydulara bağımlılığını "
        "azaltmak için bir öneri. Yol kenarında zaten duran direklere ve "
        "kabinlere ucuz birer yayın kartı takılıyor; araçtaki alıcı da "
        "çevresindeki birimlere olan mesafesini ölçerek nerede olduğunu "
        "kendi buluyor.",
        "YERKON is a proposal for road transport to depend less on "
        "foreign satellites for position. A cheap broadcast board goes "
        "onto masts and cabinets already standing by the road, and the "
        "receiver in a vehicle finds where it is by measuring its distance "
        "to the units around it.",
    ),
    parts=(
        Part(
            kind="picture",
            picture="road.webp",
            lines=(_w(
                "Rapordan. Yayın birimleri yol kenarında zaten duran "
                "noktalara takılıyor. Alıcı hem uyduyu hem yerdeki "
                "birimleri görüyor ve uydu kesilince yerdekilerle devam "
                "ediyor.",
                "From the report. The broadcast units go onto points "
                "already standing by the road. A receiver sees both the "
                "satellites and the units on the ground, and carries on "
                "with the ground ones when the satellites go.",
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
                    "kurulumda ölçülmüş konumunu yayınlar. Bu noktaların "
                    "seyrek kaldığı yerde yol boyundaki diğer direkler "
                    "kullanılıyor: simülasyonda şehirde aydınlatma "
                    "direkleri, kırsalda çoğunlukla elektrik dağıtım "
                    "direkleri.",
                    "The Ministry of Transport and Infrastructure already "
                    "has points on the power and communications network: "
                    "intelligent transport cabinets, roadside units, "
                    "traffic lights, tunnel lighting and toll gates. "
                    "YERKON adds a low cost radio board to those points. "
                    "The board broadcasts its identity and the position "
                    "surveyed when it was installed. Where those points "
                    "are sparse, the other poles along the road are used: "
                    "in the simulation, lighting columns in town and "
                    "mostly electricity distribution poles in open "
                    "country.",
                ),
                _w(
                    "Bir yayın birimi 1000 adetlik üretimde, kutusu, "
                    "baskılı devresi ve dizgisiyle yaklaşık 1400 ile 1700 "
                    "lira arasında. Hedef, AUS "
                    "noktalarında zaten "
                    "duran elektrik ve haberleşme altyapısını yeniden "
                    "kullanmak; maliyeti aşağıda tutan da bu.",
                    "A broadcast unit costs roughly 1400 to 1700 lira at "
                    "a thousand units, box, printed board and assembly "
                    "included. The aim is to reuse "
                    "the power and "
                    "communications already standing at intelligent "
                    "transport points, and that is what keeps the cost "
                    "down.",
                ),
                _w(
                    "YERKON uydunun yerine geçmeyi hedeflemiyor. Uydu "
                    "çalışırken iki konum yan yana duruyor ve ikisini "
                    "karşılaştırmak bir aldatma saldırısını tespit etmeye "
                    "yarayabilir.",
                    "YERKON does not aim to replace the satellites. While "
                    "they work, the two positions sit side by side, and "
                    "comparing them can help detect a spoofing attack.",
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
        "Bugün konum bulmanın, yol tarif etmenin ve saati hassas tutmanın "
        "neredeyse tamamı GPS, Galileo, GLONASS ve BeiDou'dan geliyor. Bu "
        "bağımlılık araç navigasyonuyla bitmiyor: acil çağrı ekipleri, "
        "kamu araç filoları, telefon şebekeleri, elektrik şebekesi ve "
        "kargo taşımacılığı da aynı dört sisteme bağlı.",
        "Nearly everything that finds a position, gives directions or "
        "keeps precise time today runs on GPS, Galileo, GLONASS and "
        "BeiDou. The dependency does not stop at vehicle navigation: "
        "emergency crews, public fleets, telephone networks, the "
        "electrical grid and freight all hang on the same four systems.",
    ),
    parts=(
        Part(
            kind="picture",
            picture="gnss.webp",
            lines=(_w(
                "Dördü de yabancı devletlerin elinde ve dördünün de "
                "aynı zayıf noktası var: uydudan gelen sinyal yere "
                "vardığında çok cılızdır.",
                "All four are in the hands of foreign states, and all "
                "four have the same weak spot: the signal from a satellite "
                "is faint by the time it reaches the ground.",
            ),),
        ),
        Part(
            kind="points",
            heading=_w("Nerede işe yaramıyor", "Where it breaks"),
            lines=(
                _w(
                    "Tünelde, kapalı alanda ve yüksek binaların "
                    "arasında sinyal kayboluyor.",
                    "The signal is lost in tunnels, indoors and between "
                    "tall buildings.",
                ),
                _w(
                    "Sinyal zayıf olduğu için bastırmak kolay ve "
                    "bastırma cihazları gitgide yaygınlaşıyor.",
                    "The signal is weak, so it is easy to drown out, and "
                    "the equipment for doing it keeps spreading.",
                ),
                _w(
                    "Sahte sinyal alıcıya yanlış bir konum hesaplatır. "
                    "Alıcı bu konumu doğruymuş gibi, üstelik yüksek "
                    "güvenle gösterir. Tehlikeli olan da bu.",
                    "A fake signal makes the receiver work out a wrong "
                    "position. The receiver then shows that position as "
                    "though it were right, and with high confidence. That "
                    "is what makes it dangerous.",
                ),
                _w(
                    "Kritik hizmetler tek bir teknoloji ailesine "
                    "bağımlı.",
                    "Critical services depend on a single family of "
                    "technology.",
                ),
                _w(
                    "Kriz anında sistem üzerindeki karar yetkisi "
                    "Türkiye'de değil.",
                    "In a crisis the authority over the system does not "
                    "sit in Turkey.",
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
                    "Ruidoso'ya varamadan bir dağa çarptı. "
                    "[NTSB üzerine haber](https://www.military.com/"
                    "air-medevac-crew-lost-gps-during-military-jamming-"
                    "before-fatal-crash-ntsb-says?utm_source=gemini)",
                    "**United States, May 2026.** An air ambulance out of "
                    "Roswell flew into military GPS jamming and hit a "
                    "mountain short of Ruidoso. "
                    "[Report on the NTSB finding](https://www.military.com/"
                    "air-medevac-crew-lost-gps-during-military-jamming-"
                    "before-fatal-crash-ntsb-says?utm_source=gemini)",
                ),
                _w(
                    "**Baltık, Nisan 2024.** Finnair, Tartu uçuşlarını bir "
                    "ay boyunca tamamen durdurmak zorunda kaldı. İki yolcu "
                    "uçağı yaklaşma sırasında sinyali kaybedip inemeden "
                    "Helsinki'ye döndü; havalimanının tek yaklaşma sistemi "
                    "GPS tabanlı olduğu için uçuşlar haftalarca durduruldu. "
                    "[Anadolu Ajansı](https://www.aa.com.tr/en/europe/"
                    "suspected-russian-gps-jamming-too-dangerous-to-ignore-"
                    "baltic-officials/3205763)",
                    "**The Baltic, April 2024.** Finnair had to stop "
                    "flying to Tartu altogether for a month. Two airliners "
                    "lost the signal on approach and turned back to "
                    "Helsinki without landing; the flights stayed suspended "
                    "for weeks because the airport's only approach system "
                    "was GPS based. "
                    "[Anadolu Agency](https://www.aa.com.tr/en/europe/"
                    "suspected-russian-gps-jamming-too-dangerous-to-ignore-"
                    "baltic-officials/3205763)",
                ),
                _w(
                    "**Norveç, 2019'dan bu yana.** Kola Yarımadası'ndan "
                    "yayılan düzenli karıştırma, Finnmark'taki polis, "
                    "ambulans ve kurtarma ekiplerinin navigasyonunu "
                    "defalarca kör etti. Bir kar fırtınasında kaybolan "
                    "kişinin acil durum vericisi çalışmadı ve kurtarma "
                    "helikopterleri kör uçtu. "
                    "[The Barents Observer](https://www.thebarentsobserver"
                    ".com/security/gps-jamming-jeopardizes-public-safety-in-"
                    "norways-northernmost-region/157622)",
                    "**Norway, 2019 onwards.** Steady jamming from the "
                    "Kola Peninsula has repeatedly blinded police, "
                    "ambulance and rescue navigation in Finnmark. During "
                    "one snowstorm a missing person's emergency beacon "
                    "failed and the rescue helicopters flew blind. "
                    "[The Barents Observer](https://www.thebarentsobserver"
                    ".com/security/gps-jamming-jeopardizes-public-safety-in-"
                    "norways-northernmost-region/157622)",
                ),
                _w(
                    "**Karadeniz, 2017.** Rus elektronik harp birimleri "
                    "GNSS sinyallerini değiştirdi ve yirmiden fazla ticari "
                    "geminin alıcısı aynı anda yanlış konum bildirdi: "
                    "gemiler denizin ortasındayken ekranları onları 40 km "
                    "içerideki bir havalimanında gösterdi. "
                    "[GalileoGNSS](https://galileognss.eu/"
                    "mass-gps-spoofing-attack-in-black-sea/)",
                    "**The Black Sea, 2017.** Russian electronic warfare "
                    "units altered the GNSS signals and receivers on more "
                    "than twenty commercial ships reported a wrong "
                    "position at the same time: at sea, their screens put "
                    "them at an airport 40 km inland. "
                    "[GalileoGNSS](https://galileognss.eu/"
                    "mass-gps-spoofing-attack-in-black-sea/)",
                ),
            ),
        ),
        Part(kind="shows", shows="when"),
        Part(
            kind="text",
            heading=_w("YERKON'un cevabı", "What YERKON answers"),
            lines=(
                _w(
                    "Kırsal yayın birimi için 8-10 km'lik bir haberleşme ve "
                    "kapsama hedefi var; o uzaklıktaki ölçüm doğruluğu "
                    "saha deneyleriyle ayrıca doğrulanacak. Tutarsa "
                    "alçaktan uçan bir uçak da birimi duyabilir. "
                    "Havalimanı çevresine kurulan birimler ise uydular "
                    "susturulsa bile yerde çalışmaya devam eden ayrı bir "
                    "ağ bırakabilir. Bunlar raporun hedefi; hiçbiri henüz "
                    "sahada ölçülmedi.",
                    "For the rural unit, 8 to 10 km is a communications "
                    "and coverage target; how accurately it can measure "
                    "distance at that range is to be confirmed by field "
                    "trials. If it holds, a low flying aircraft can hear "
                    "the unit too. Units around an airport could leave a "
                    "separate network that keeps working on the ground "
                    "even with the satellites silenced. These are the "
                    "report's targets, and this repository measured none "
                    "of them in the field.",
                ),
                _w(
                    "Sahte sinyale karşı YERKON yedekten fazlası: bir "
                    "doğrulama mekanizması. Araç ya da gemi, uydunun "
                    "verdiği konumla yerden gelen konumu karşılaştırarak "
                    "bir aldatma saldırısı altında olduğunu tespit "
                    "edebilir.",
                    "Against a fake signal YERKON is more than a standby: "
                    "it is a cross-check. A vehicle or a ship can compare "
                    "the satellite's position with the one from the ground "
                    "and so detect that it is under a spoofing attack.",
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
        "kendi hesaplayan alıcılar ve kimlikleri güncel tutan merkezi "
        "yönetim sistemi.",
        "Three parts: broadcast units standing at surveyed positions, "
        "receivers that work out their own position, and a management "
        "system that keeps the identities current.",
    ),
    parts=(
        Part(
            kind="picture",
            picture="architecture.webp",
            lines=(_w(
                "Rapordan. Alıcı mesafeyi karşılıklı mesajlaşarak "
                "ölçüyor. Merkezi yönetim sistemiyle birimler arasındaki "
                "hat ise mesafe değil, kimlik ve anahtar taşıyor.",
                "From the report, with Turkish labels. The receiver "
                "measures distance by sending messages back and forth. "
                "The line between the management system and the units "
                "carries identity and keys rather than distance.",
            ),),
        ),
        Part(
            kind="points",
            heading=_w("Üç parça", "Three parts"),
            lines=(
                _w(
                    "**Yayın birimi.** Sabit bir noktaya, direğe, yol "
                    "kenarı ünitesine, haberleşme tesisine ya da tünelin "
                    "içine takılan verici. Alıcı sorduğunda üç şey "
                    "yayınlar: kim olduğunu, kurulumda ölçülen sabit "
                    "konumunu ve bunların sahte olmadığını gösteren "
                    "imzayı.",
                    "**The broadcast unit.** A transmitter fixed to one "
                    "point: a mast, a roadside unit, a communications "
                    "site, or inside a tunnel. When a receiver asks, it "
                    "broadcasts three things: who it is, the fixed "
                    "position surveyed at installation, and the signature "
                    "that shows neither is forged.",
                ),
                _w(
                    "**Alıcı.** Araca ya da cebe girer. Yayın "
                    "birimlerinden ölçtüğü mesafeleri, aracın kendi "
                    "sensörleriyle birleştirir: hareketi ölçen atalet "
                    "birimi, tekerleğin kaç tur döndüğü ve harita. "
                    "Böylece uydu hiç görünmese de konum vermeye devam "
                    "eder. Tablodaki simülasyonda atalet birimi ve "
                    "tekerlek kullanılmadı; yalnız mesafeler ve haritadan "
                    "gelen yükseklik.",
                    "**The receiver.** It goes in a vehicle or in a "
                    "pocket. It combines the distances it measures to the "
                    "units with the vehicle's own sensors: an inertial "
                    "unit that measures movement, how far the wheels have "
                    "turned, and the map. So it keeps giving a position "
                    "with no satellite in sight. The simulation behind "
                    "the table uses neither the inertial unit nor the "
                    "wheels; only the ranges and the height from the "
                    "map.",
                ),
                _w(
                    "**Merkezi yönetim sistemi.** Hangi birimin hangi "
                    "anahtara sahip olduğunun listesini tutar. Alıcı bu "
                    "listeyi indirip her birimin imzasını kontrol eder, "
                    "böylece sahte bir birimle konuşmaz.",
                    "**The management system.** It keeps the list of which "
                    "unit holds which key. A receiver downloads that list "
                    "and checks each unit's signature, so it never talks "
                    "to a forged one.",
                ),
            ),
        ),
        Part(
            kind="text",
            heading=_w("Neden çift yönlü ölçüm", "Why two way ranging"),
            lines=(
                _w(
                    "Bir sinyalin iki birime kaç saniye arayla vardığına "
                    "bakan sistemlerde (TDoA), aynı doğruluğa ulaşmak için "
                    "birimler arasında hassas bir ağ geneli zaman "
                    "senkronizasyonu ve bunu sağlayan ek altyapı "
                    "gerekebilir. Örneğin milyarda bir saniyenin altına "
                    "inmek, her birimde bir atomik saat ve IEEE 1588 PTP "
                    "altyapısı demek. Çip ölçekli bir atomik saatin "
                    "(Microchip SA65) tek adedi yaklaşık 5500 dolar, "
                    "yaklaşık 266400 lira ([Analog IC Tips, Eylül 2021]"
                    "(https://www.analogictips.com/the-pc-board-atomic-clock-part-3-the-csac-cesium-physics-cell-faq/)). "
                    "Çift yönlü "
                    "ölçümde bu ağ geneli senkronizasyona gerek yok: "
                    "sinyalin havada geçirdiği süre, birimle alıcı "
                    "arasındaki kısa bir gidiş gelişten çıkıyor.",
                    "Systems that look at how much later a signal reaches "
                    "one unit than another (TDoA) may need precise network "
                    "wide time synchronisation between the units, and the "
                    "infrastructure to supply it, to reach the same "
                    "accuracy. Going below a billionth of a second, for "
                    "instance, means an atomic clock and IEEE 1588 PTP at "
                    "every unit. One chip-scale atomic clock (Microchip "
                    "SA65) costs about 5500 dollars, roughly 266400 lira "
                    "([Analog IC Tips, September 2021]"
                    "(https://www.analogictips.com/the-pc-board-atomic-clock-part-3-the-csac-cesium-physics-cell-faq/)). "
                    "Two way ranging needs no "
                    "network wide synchronisation: the time the signal "
                    "spends in the air comes out of one short "
                    "there-and-back between the unit and the receiver.",
                ),
                _w(
                    "Her telsiz yongası zamanı kendi kristaliyle sayar ve "
                    "iki yonganın kristali birebir aynı hızda çalışmaz. "
                    "Çift yönlü ölçümde bu fark yalnız birimin cevap "
                    "vermeden önce beklediği kısa süre boyunca hataya "
                    "dönüşür; alıcı farkı gelen sinyalden kestirip "
                    "düzeltir. Simülasyonda düzeltmeden sonra kalan hata "
                    "bir mesafe ölçümünde 20 santimetreyi geçmiyor.",
                    "Every radio chip counts time with its own crystal, and "
                    "no two crystals run at exactly the same rate. In two "
                    "way ranging that difference only turns into error "
                    "over the short wait before the unit answers, and the "
                    "receiver estimates it from the incoming signal and "
                    "removes it. In the simulation what is left after that "
                    "correction stays under 20 centimetres on one range.",
                ),
                _w(
                    "Her yayın birimi kendi özel anahtarını gizli tutar ve "
                    "açık anahtarını merkezi sisteme aktarır. Anahtar 256 "
                    "bit ECC, imza ECDSA. Kaydedilip sonradan yeniden "
                    "yayınlanan eski bir mesajı sıra numarası ele verir.",
                    "Each unit keeps its own private key and hands its "
                    "public key to the management system. The key is 256 "
                    "bit ECC and the signature is ECDSA. A sequence number "
                    "gives away an old message recorded and sent again later.",
                ),
            ),
        ),
        Part(kind="shows", shows="clocks"),
        Part(
            kind="points",
            heading=_w("Üç kurulum grubu", "Three kinds of installation"),
            lines=(
                _w(
                    "**Şehir içi.** Çok sayıda, kısa menzilli birim: baz "
                    "istasyonları, trafik levhaları ve lambaları, reklam "
                    "panoları, yol kenarı aydınlatmaları. Birimde EBYTE'nin "
                    "E28-2G4M20S modülü kullanılıyor; içindeki 2,4 GHz "
                    "telsiz yongası Semtech SX1280. Semtech bu yonga için "
                    "açık görüş hattında yaklaşık ±1 m mesafe ölçüm "
                    "doğruluğu veriyor. Bu bir birim ile alıcı arasındaki tek "
                    "mesafenin doğruluğu; nihai konum hatası değil. Konum "
                    "hatası birimlerin geometrisine, çok yollu yayılıma ve "
                    "engellere de bağlı ve ayrıca HPE P50 ile HPE P95 "
                    "üzerinden değerlendirilecek.",
                    "**Urban.** Many short range units: base station "
                    "sites, traffic signs and lights, advertising boards, "
                    "roadside lighting. The unit uses EBYTE's E28-2G4M20S "
                    "module, whose 2,4 GHz radio chip is the Semtech "
                    "SX1280; Semtech states about ±1 m of ranging accuracy "
                    "for that chip with clear line of sight. That is "
                    "the accuracy of one distance between one unit and a "
                    "receiver, not the final position error. Position "
                    "error also depends on the units' geometry, on "
                    "multipath and on obstruction, and is judged "
                    "separately on HPE P50 and HPE P95.",
                ),
                _w(
                    "**Kırsal.** Az sayıda ama geniş alana ulaşan nokta: "
                    "akıllı ulaşım sistemi ve yol kenarı üniteleri, baz "
                    "istasyonu sahaları, demiryolu ve karayolu altyapısı; "
                    "bunlar seyrek olduğu için simülasyonda birimlerin "
                    "çoğu yol boyundaki elektrik dağıtım direklerinde, "
                    "güneş paneli ve aküyle. "
                    "Cihaz uyarlamalı frekans atlamalı olarak "
                    "belgelendiriliyor; bu belgeyle 2,4 GHz'de yoğunluk "
                    "sınırı kalkıyor ve 20 dBm yayılan güç kalıyor. Kırsal "
                    "birim şehir içindekiyle aynı kart: yükselteçli modül "
                    "(E28-2G4M20S) ve dış ortam tipi 5 dBi çubuk anten. "
                    "Şehirdeki birimden farkı kartta değil yerinde: "
                    "kırsalda arada bina olmadığı için sinyal çok daha "
                    "uzağa ulaşıyor, elektriği olmayan direklerde de güneş "
                    "paneli ve akü var. "
                    "YERKON'da 8-10 km'lik bir "
                    "menzil haberleşme ve kapsama hedefi olarak alınıyor; o "
                    "uzaklıktaki ölçüm doğruluğu saha deneyleriyle "
                    "doğrulanacak. Simülasyondaki Polatlı arazisi "
                    "seyrek yapılı bir bozkır olduğu için, 486 m'lik iniş "
                    "çıkışına rağmen kırsal satır şehir içinden biraz daha "
                    "iyi çıktı; orman, sarp engebe ve kapalı görüş olan "
                    "yerlerde "
                    "kırsal performansın düşmesi bekleniyor. Sonuç HPE "
                    "P50 ve HPE P95 ile raporlanıyor.",
                    "**Open country.** A few points with wide reach: "
                    "intelligent transport and roadside units, base "
                    "station sites, rail and road infrastructure; these "
                    "are sparse, so in the simulation most units are on "
                    "the electricity distribution poles along the road, "
                    "with a solar panel and a battery. The "
                    "equipment is certified as adaptive frequency hopping, "
                    "which lifts the 2,4 GHz density limit and leaves "
                    "20 dBm of radiated power. The rural unit is the same "
                    "board as the urban one: the amplified module "
                    "(E28-2G4M20S) and an outdoor 5 dBi rod antenna. Its "
                    "difference from the town unit is not the board but "
                    "where it stands: with no buildings in the way the "
                    "signal reaches much further, and poles with no mains "
                    "carry a solar panel and a battery. YERKON takes 8 to 10 km as a communications and "
                    "coverage target, and how accurately it ranges at that "
                    "distance is to be confirmed by field trials. The "
                    "Polatlı ground in the simulation is steppe "
                    "with few buildings, so despite its 486 m of relief "
                    "the rural row came out a little better than the "
                    "urban one; where there is forest, steep ground or "
                    "blocked sight, rural performance is expected to fall. "
                    "The result is reported as HPE P50 and HPE P95.",
                ),
                _w(
                    "**Kritik bölge.** Tüneller, metro ve istasyon "
                    "alanları, liman ve havalimanları, afet lojistik "
                    "alanları. Birimde Qorvo'nun 6,5-8 GHz DWM3000 UWB "
                    "modülü kullanılıyor; bu modül görüş hattı açıkken "
                    "yaklaşık 10 cm sınıfında mesafe ölçüm hassasiyetini "
                    "hedefliyor. Nihai konum hatası buna eşit değil: "
                    "geometriye, kalibrasyona, çok yollu yayılıma ve "
                    "engellere bağlı ve saha testlerinde HPE P50 ile HPE "
                    "P95 üzerinden ayrıca ölçülecek.",
                    "**Critical areas.** Tunnels, metro and station areas, "
                    "ports and airports, disaster logistics areas. The "
                    "unit uses Qorvo's 6,5 to 8 GHz DWM3000 UWB module, "
                    "which aims at about 10 cm of ranging precision where "
                    "the line of sight is clear. The final position error "
                    "is not the same thing: it depends on geometry, "
                    "calibration, multipath and obstruction, and is "
                    "measured separately in field tests as HPE P50 and HPE "
                    "P95.",
                ),
            ),
        ),
        Part(
            kind="points",
            heading=_w("Alıcı modülleri", "Receiver modules"),
            lines=(
                _w(
                    "**Yaya.** Az pil harcasın ve cepte taşınsın diye "
                    "tasarlandı. Şehirde ve kırsalda EBYTE E28-2G4M12S "
                    "modülünü (SX1280 yongalı), tünelde ve kapalı alanda "
                    "Qorvo DWM3000'i kullanır. ESP32-S3 ile telefona "
                    "bağlanır; sinyal kesilirse BNO085 hareket sensörüyle "
                    "son konumdan devam eder. UWB için seramik anten, "
                    "2,4 GHz için kart üzerinde çip anten.",
                    "**Pedestrian.** Designed to draw little power and "
                    "fit in a pocket. It uses the EBYTE E28-2G4M12S "
                    "module (an SX1280 chip) in town and in open country "
                    "and the Qorvo DWM3000 in tunnels and indoors. An "
                    "ESP32-S3 connects it to a phone; if the signal drops, "
                    "a BNO085 motion sensor carries on from the last "
                    "position. A ceramic antenna for UWB, a chip antenna "
                    "on the board for 2,4 GHz.",
                ),
                _w(
                    "**Kara aracı.** STM32 üzerine kurulu, LCD harita "
                    "ekranı var. Uyumlu araçların CAN hattına bağlanıp "
                    "tekerlek hız sensörlerinden ve direksiyon açısından "
                    "anlık veri alır. Yaya modülü gibi iki telsizi birden "
                    "taşır: geniş alan için yükselteçli EBYTE E28-2G4M20S "
                    "modülü (SX1280 yongalı), kritik bölge için Qorvo "
                    "DWM3000. DWM3000 kendi dahili antenini kullanır; "
                    "E28-2G4M20S araç tavanındaki dış ortam tipi 5 dBi "
                    "çubuk antenle çalışır.",
                    "**Road vehicle.** Built on an STM32 with an LCD map "
                    "screen. It connects to the CAN bus of vehicles that "
                    "support one and takes live data from the wheel speed "
                    "sensors and the steering angle. Like the pedestrian "
                    "module it carries both radios: the amplified EBYTE "
                    "E28-2G4M20S module (an SX1280 chip) for wide areas "
                    "and the Qorvo DWM3000 for critical ones. The DWM3000 "
                    "uses its own on-board antenna; the E28-2G4M20S works "
                    "with an outdoor 5 dBi rod antenna on the vehicle's "
                    "roof.",
                ),
                _w(
                    "**Nesnelerin interneti alıcısı.** Kapalı ve yarı açık "
                    "alanda çalışan robot filoları için. Yaygın robot "
                    "işletim "
                    "sistemleriyle doğrudan konuşur; tekerleğin kaç tur "
                    "döndüğüne ve kendi hareket sensörüne bakarak konumunu "
                    "sürekli düzeltir. Çoğu depo ve fabrikada DWM3000 "
                    "yeter.",
                    "**Internet of things.** For robot fleets indoors and "
                    "in half open areas. It talks directly to the common "
                    "robot operating systems and keeps correcting its "
                    "position from how far the wheels have turned and its "
                    "own motion sensor. A DWM3000 is enough for most "
                    "warehouse and factory work.",
                ),
            ),
        ),
        Part(
            kind="points",
            heading=_w("Donanım ve fiyatı", "The hardware and its price"),
            lines=(
                _w(
                    "1000 adette bir yayın birimi yaklaşık 1400-1700 lira, "
                    "bir alıcı yaklaşık 2300-3300 lira. Her ürünün 1, 100 "
                    "ve 1000 adetlik fiyat tablosu Maliyet sayfasında.",
                    "At a thousand units a broadcast unit is roughly 1400 "
                    "to 1700 lira and a receiver roughly 2300 to 3300 "
                    "lira. Every product's price at one, a hundred and a "
                    "thousand is tabled on the Cost page.",
                ),
                _w(
                    "Her ürünün 1, 100 ve 1000 adetteki fiyatı, kartın "
                    "parçalarının satıcılarının kendi kademe fiyatlarıyla "
                    "toplanıyor: telsiz modülü, mikrodenetleyici, anten, "
                    "besleme, koruma, kutu, pasifler, baskılı devre ve "
                    "dizgi. Tablo 1000 adetlik fiyatla hesaplanıyor, çünkü "
                    "işletme modeli bin birimlik bir ağ varsayıyor. Her "
                    "parça, satıcısı ve fiyatı Maliyet sayfasında.",
                    "Each product's price at one, a hundred and a thousand "
                    "is the sum of its parts at their sellers' own tier "
                    "prices: radio module, microcontroller, antenna, "
                    "supply, protection, box, passives, printed board and "
                    "assembly. The table prices at a thousand, because the "
                    "operating model assumes a network of a thousand "
                    "units. Every part, its seller and its price are on "
                    "the Cost page.",
                ),
                _w(
                    "Fiyatlar kartın bütün parçalarını kapsıyor: ana "
                    "parçalar, besleme ve koruma, klemensler, anten "
                    "kablosu, kutu, direnç ve kondansatörler, baskılı devre "
                    "ve dizgi. Test, ayar, belgelendirme, vergi ve kargo "
                    "bu rakamların dışında; sahadaki montaj ayrı bir kalem "
                    "olarak tabloya giriyor.",
                    "The prices cover every part of the board: the main "
                    "parts, supply and protection, terminals, antenna "
                    "cable, box, the passive components, the printed "
                    "board and its assembly. Test, calibration, "
                    "certification, tax and shipping are outside them; "
                    "installation goes into the table as a line of its "
                    "own.",
                ),
                _w(
                    "İki alıcı da hem SX1280 yongalı EBYTE modülünü hem "
                    "DWM3000'i taşıyor. Bu "
                    "sayede aynı cihaz yolda şehir birimleriyle, tünele "
                    "girince tünel birimleriyle ölçüyor; kullanıcı hiçbir "
                    "şeyi değiştirmiyor.",
                    "Both receivers carry an EBYTE module with an SX1280 "
                    "chip and a DWM3000. That is "
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
        "Proje dört soruya cevap arıyor. Hiçbiri kapanmış değil ve her "
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
                    "**Yerden gelen yayınlar, araç sensörleri ve harita "
                    "bir araya getirilirse, uydu olmadan yeterince iyi bir "
                    "konum çıkar mı?** Önce şehirde denenecek. Çevredeki "
                    "modemlerin kimliğinden, baz istasyonlarına olan "
                    "uzaklıktan ve kameradan gelen görüntüden de "
                    "yararlanılacak.",
                    "**If broadcasts from the ground, vehicle sensors and "
                    "the map are put together, does a good enough position "
                    "come out without the satellites?** It gets tried in a "
                    "city first. What nearby modems call themselves, the "
                    "distance to base stations and the picture from a "
                    "camera all get used as well.",
                ),
                _w(
                    "**Mevcut altyapıya en az dokunarak, sonradan "
                    "büyütülebilen bir sistem kurulabilir mi?** 12. "
                    "Ulaştırma ve Haberleşme Şurası akıllı ulaşım "
                    "altyapısının geliştirilmesini hedef koydu. Yol "
                    "kenarındaki ünitelerin ve trafik kontrol noktalarının "
                    "elektriğini ve hattını kullanmak, montajı ucuza "
                    "getirmenin yolu.",
                    "**Can a system be built by touching the existing "
                    "infrastructure as little as possible, and grown "
                    "later?** The 12th Transport and Communications "
                    "Council set developing intelligent transport "
                    "infrastructure as a goal. Using the power and the "
                    "line already at roadside units and traffic control "
                    "points is the way to make installation cheap.",
                ),
                _w(
                    "**Çift yönlü ölçümün iki eksisi giderilebilir mi?** "
                    "Bu eksiler şunlar: havada daha çok mesaj dolaşıyor "
                    "ve alıcı sayısı arttıkça sıra beklemek gerekiyor. "
                    "Tek yönlü yayın yapan sistemler alıcıdan cevap "
                    "beklemediği için bu yükü taşımıyor. TWR CDMA "
                    "gibi yaklaşımlar ve yazılım tanımlı radyo bu farkı "
                    "kapatmak için denenecek. "
                    "[TWR CDMA makalesi](https://ieeexplore.ieee.org/"
                    "abstract/document/11435291)",
                    "**Can two way ranging's two drawbacks be brought "
                    "down?** They are these: more messages travel through "
                    "the air, and receivers have to wait their turn as "
                    "their number grows. Systems that broadcast one way "
                    "expect no answer from the receiver, so they carry "
                    "neither cost. Approaches such as "
                    "TWR CDMA and software defined radio will be tried to "
                    "close that gap. "
                    "[The TWR CDMA paper](https://ieeexplore.ieee.org/"
                    "abstract/document/11435291)",
                ),
                _w(
                    "**Konum hizmeti veren bir altyapının güvenliği ne "
                    "ister?** İki tehdide karşı çözüm denenecek: birinin "
                    "sahte bir yayın birimi kurması ve izinsiz alıcıların "
                    "sistemi doldurması. Her modüle şifreleme işini "
                    "üstlenen ayrı bir yonga (ATECC608B) konacak; her "
                    "mesajın kimden geldiği ve yolda değiştirilmediği "
                    "imzayla doğrulanacak.",
                    "**What does security ask of an infrastructure that "
                    "gives out position?** Answers get tried against two "
                    "threats: somebody setting up a fake broadcast unit, "
                    "and unauthorised receivers filling the system. Every "
                    "module gets a separate chip that does the encryption "
                    "(ATECC608B), and a signature verifies who each "
                    "message came from and that it was not altered on the "
                    "way.",
                ),
            ),
        ),
        Part(
            kind="text",
            heading=_w("Sahte sinyali erken görmek", "Seeing spoofing early"),
            lines=(
                _w(
                    "Sahte sinyal altında alıcı, dışarıdan bakınca "
                    "kusursuz görünen ama yanlış bir konum ve hız verir. "
                    "YERKON uydudan tamamen ayrı çalıştığı için bir "
                    "bütünlük referansı olabilir. İki konum sürekli "
                    "karşılaştırılacak ve şunlara bakılacak: hataların "
                    "ortancası (P50), yüzde 95'i (P95) ve en kötüsü, "
                    "konumun kesintisiz gelip gelmediği, sinyal koptuktan "
                    "sonra yeniden yakınsama süresi, boşuna verilen alarm "
                    "oranı ve aldatma ile karıştırmanın yakalanma "
                    "oranı.",
                    "Under a spoofing attack the receiver gives a "
                    "position and speed that look flawless from outside "
                    "and are wrong. YERKON runs entirely apart from the "
                    "satellites, so it can serve as a reference for "
                    "integrity. The two positions will be compared "
                    "continuously and judged on the median error (P50), "
                    "the ninety fifth percentile (P95) and the worst case, "
                    "whether the position arrives without gaps, how long "
                    "reconvergence takes after the signal drops, how often "
                    "an alarm fires for nothing, and how often spoofing "
                    "and jamming are caught.",
                ),
                _w(
                    "Kurulumun kendisi de araştırma konusu. Amaç, "
                    "birimleri uzman olmayan birinin de doğru yere "
                    "koyabilmesi: afette ya da askeri bir durumda geçici "
                    "ağ kuracak personel, ekrandaki "
                    "\"en iyi sinyal için 120 derece yönünde 50 metre "
                    "ilerleyin\" gibi yönlendirmeleri takip ederek "
                    "birimleri yerleştirebilecek.",
                    "Installation is itself part of the research. The aim "
                    "is that somebody who is not an expert can put the "
                    "units in the right place: personnel setting up a "
                    "temporary network after a disaster or in a military "
                    "situation would follow directions on the screen, "
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
                    "prototipleri açık alanda, tünelde, yüksek binaların "
                    "arasında ve kapsamanın bittiği yerde denenecek.",
                    "Between 10 and 15 units will go up along one "
                    "transport corridor. Vehicle, handheld and fixed "
                    "receiver prototypes will be tried in the open, in a "
                    "tunnel, between tall buildings and where coverage "
                    "runs out.",
                ),
                _w(
                    "Açık alanda, karşılaştırılacak gerçek konumu "
                    "RTK-GNSS verecek. Uydunun girmediği tünelde ve kapalı "
                    "alanda ise önceden ölçülmüş noktalar ve güzergâh "
                    "kullanılacak.",
                    "In the open, the true position to compare against "
                    "comes from RTK-GNSS. In tunnels and indoors, where "
                    "the satellites do not reach, it comes from points and "
                    "a route surveyed beforehand.",
                ),
                _w(
                    "Hedef: hataların yarısı 5 metrenin, yüzde 95'i 10 "
                    "metrenin altında kalsın.",
                    "The target: half the errors under 5 metres, and 95 "
                    "per cent of them under 10.",
                ),
                _w(
                    "Gerçek bir karıştırıcı kullanılmayacak; hem yasak "
                    "hem tehlikeli. Onun yerine uydu sinyali kontrollü "
                    "biçimde kesilecek, önceden kaydedilmiş sinyaller "
                    "çalınacak ve saldırılar laboratuvarda taklit "
                    "edilecek.",
                    "No real jammer will be used: it is both illegal and "
                    "dangerous. Instead the satellite signal will be cut "
                    "under control, recorded signals will be played back, "
                    "and attacks will be imitated in a laboratory.",
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
        "Konumun hayati olduğu, ama uydu sinyalinin kesildiği, "
        "zayıfladığı ya da artık güvenilmediği yerlerde ulaşımın ve "
        "haberleşmenin durmaması için; sayfanın sonunda ticarileşmesi.",
        "So that transport and communications do not stop where position "
        "is vital and the satellite signal is cut, weakened or no longer "
        "trusted; how it is commercialised closes the page.",
    ),
    parts=(
        Part(
            kind="points",
            heading=_w("Sahada", "In the field"),
            lines=(
                _w(
                    "**Acil yardım ve afet.** 112, AFAD ve diğer "
                    "ekiplerin nerede olduğu tünelde, kapalı alanda, "
                    "yüksek binaların arasında ve afet bölgesinde "
                    "görünmeye devam eder. Telsiz ya da şebeke "
                    "tutmadığında cihaz, üzerindeki harita ve sensörlerle "
                    "konum vermeyi sürdürür.",
                    "**Emergency services and disasters.** It "
                    "keeps ambulance, disaster response and other teams "
                    "visible in tunnels, indoors, between tall buildings "
                    "and in disaster areas. Where the radio or the network "
                    "will not hold, the map and sensors on the device keep "
                    "giving a position.",
                ),
                _w(
                    "**Karayolu, kargo ve toplu taşıma.** Kamu araçları, "
                    "otobüsler, tehlikeli madde taşıyan tankerler ve "
                    "değerli yükler uyduya bakmayan ikinci bir takip "
                    "kazanır. Tünel ve otoyol işletmelerinde konum "
                    "sürekliliğini korumaya yardım eder.",
                    "**Road, freight and public transport.** Public "
                    "vehicles, buses, tankers carrying dangerous goods and "
                    "valuable loads gain a second way of being tracked "
                    "that does not look at the satellites. In tunnel and "
                    "motorway operations it helps keep the position "
                    "continuous.",
                ),
                _w(
                    "**Karıştırma haritası.** Uydunun verdiği konumla "
                    "YERKON'unki tutmadığında bu bir olaydır. Olaylar "
                    "merkezde toplanınca Bakanlık, ülke genelinde nerede "
                    "ne zaman karıştırma ve sahte sinyal olduğunu gösteren "
                    "bir harita elde eder.",
                    "**A map of jamming.** Every time the satellite "
                    "position and YERKON's disagree, that is an event. "
                    "Collected centrally, the events give the Ministry a "
                    "map of where and when jamming and spoofing happen "
                    "across the country.",
                ),
            ),
        ),
        Part(
            kind="points",
            heading=_w("Stratejik katkı", "Strategic"),
            lines=(
                _w("Konum tek bir yabancı teknolojiye bağlı kalmaz.",
                   "Position stops depending on one foreign technology."),
                _w("Hayati hizmetlerde tek bir şeyin bozulmasıyla her şeyin "
                   "durması ihtimali azalır.",
                   "It gets less likely that one thing breaking stops "
                   "everything in a critical service."),
                _w("Kriz çıktığında yerde çalışan ikinci bir konum "
                   "katmanı hazır olur.",
                   "In a crisis a second layer of position, working from "
                   "the ground, is already there."),
                _w("Sınır bölgeleri ve yoğun koridorlar kesintiye daha "
                   "dayanıklı olur.",
                   "Border regions and busy corridors hold up better "
                   "against interruption."),
                _w("Böyle bir sistemi kurma, yazma ve bir araya getirme "
                   "bilgisi ülkede kalır.",
                   "The knowledge of how to build, write and put together "
                   "such a system stays in the country."),
            ),
        ),
        Part(
            kind="points",
            heading=_w("Kurumsal ve akademik katkı",
                       "Institutional and academic"),
            lines=(
                _w("Hangi hizmetin uyduya ne kadar bağlı olduğu "
                   "çıkarılır ve olaylar ülke haritasına işlenir.",
                   "It comes out which service depends on the satellites "
                   "how much, and the events go onto a national map."),
                _w("Kurumlar aynı olay verisine bakar; hizmetin ne kadar "
                   "iyi olması gerektiği bu veriyle tanımlanabilir.",
                   "Institutions look at the same event data, and how good "
                   "the service has to be can be defined from it."),
                _w("Geriye birden çok sensörden toplanmış, uydunun "
                   "kesildiği ve kandırıldığı durumları da içeren bir veri "
                   "kümesi kalır.",
                   "What is left is a dataset gathered from several "
                   "sensors, covering satellites cut off and satellites "
                   "fooled."),
                _w("Konum hesaplayan yöntemler burada yazılır ve "
                   "üniversite, kamu ve sanayi aynı işin üzerinde çalışır.",
                   "The methods that work out position get written here, "
                   "with universities, the state and industry on the same "
                   "work."),
            ),
        ),
        Part(
            kind="text",
            heading=_w("Ticarileşme", "Commercialisation"),
            lines=(
                _w("YERKON'un amacı kamu değeri üretmek. Aşağıdakiler, "
                   "işletme maliyetini karşılayacak gelirin nereden "
                   "geleceği, ilk ticari adımlar ve satılacak ürünler.",
                   "YERKON's aim is public value. What follows is where "
                   "the income to meet the running cost can come from, "
                   "the first commercial steps and the products to be "
                   "sold."),
            ),
        ),
        Part(
            kind="text",
            sub=True,
            heading=_w("Kendini nasıl döndürür",
                       "How it pays for itself"),
            lines=(
                _w(
                    "Amaç kamu altyapısını özelleştirmek değil. Çekirdek "
                    "kamuda kalır; üzerine eklenen denetimli hizmetler "
                    "işletme masrafını karşılar.",
                    "The model is not privatising public infrastructure. "
                    "The aim is controlled extra services on top of a "
                    "public core, enough to cover what running it costs.",
                ),
                _w(
                    "İlk yer, GNSS erişiminin yapısal olarak sınırlı "
                    "olduğu tüneller ve kritik ulaşım koridorları. Orada ihtiyaç açıkça "
                    "söylenebiliyor ve sonuç denetimli biçimde "
                    "ölçülebiliyor, yani ilk kurulumun sınırları belli. "
                    "Doğruluğun ne çıktığı, ne kadar alanın kapsandığı, "
                    "hizmetin kesilip kesilmediği, kaç birim gerektiği ve "
                    "mevcut altyapının ne kadarının kullanılabildiği "
                    "pilotta belli olacak.",
                    "The first area is tunnels and critical transport "
                    "corridors, where satellite access is structurally "
                    "limited. "
                    "There the need can be stated plainly and performance "
                    "measured under control, so the boundaries of a first "
                    "deployment are clear. The pilot is what settles "
                    "accuracy, coverage, service continuity, how dense the "
                    "units have to be, and how much of the existing "
                    "infrastructure can be reused.",
                ),
                _w(
                    "Kısa vadede pilot, hazır satılan donanımla "
                    "doğrulanacak; yerli yazılım ve haberleşme kuralları "
                    "yazılacak, ilk yayın ve alıcı kartları tasarlanacak. "
                    "Orta vadede yerli gömülü sistem ve telsiz "
                    "firmalarıyla ortaklık, savunma ve haberleşme "
                    "ekosistemiyle birlikte donanım geliştirme ve kritik "
                    "parçaların iki ayrı yerden tedariki.",
                    "In the short term the pilot is proved on hardware "
                    "bought off the shelf, while the domestic software and "
                    "the rules the radios follow get written and the first "
                    "broadcast and receiver boards are designed. In the "
                    "medium term, partnership with domestic embedded and "
                    "radio firms, hardware developed together with the "
                    "defence and communications industry, and two "
                    "suppliers for every critical part.",
                ),
            ),
        ),
        Part(
            kind="points",
            sub=True,
            heading=_w("Uzun vadede", "In the long term"),
            lines=(
                _w("Komşu ve gelişmekte olan ülkelere karasal "
                   "konumlandırma çözümü.",
                   "A terrestrial positioning answer for neighbouring and "
                   "developing countries."),
                _w("Kritik koridor ve liman odaklı bölgesel kurulumlar.",
                   "Regional installations around critical corridors and "
                   "ports."),
                _w("YERKON protokolünün ve alıcı ailesinin lisanslanması.",
                   "Licensing the YERKON protocol and the receiver "
                   "family."),
                _w("Afet ve GNSS karıştırma riski yüksek ülkelere kurulum "
                   "ve entegrasyon hizmeti.",
                   "Installation and integration for countries at high "
                   "risk of disaster and of GNSS jamming."),
                _w("Yan çıktı: yerli konumlandırma ve navigasyon "
                   "ekosisteminin gelişmesi.",
                   "A side output: a domestic positioning and navigation "
                   "industry growing up around it."),
            ),
        ),
        Part(
            kind="points",
            sub=True,
            heading=_w("Ürünler", "The products"),
            lines=(
                _w(
                    "**Altyapı.** Şehir içi ve kırsal yayın birimi (aynı "
                    "kart; kırsalda güneş paneli ve aküyle), kritik bölge "
                    "yayın birimi ve güvenli anahtar ile yayın birimi "
                    "yönetim sistemi.",
                    "**Infrastructure.** The urban and rural broadcast "
                    "unit (one board; in open country with a solar panel "
                    "and a battery), the critical area broadcast unit, and "
                    "the system that manages the units and their keys.",
                ),
                _w(
                    "**Kullanıcı.** Kara aracı alıcısı, yaya alıcısı "
                    "(taşınabilir saha alıcısı) ve nesnelerin interneti "
                    "alıcısı. "
                    "Sonraki ürünler: insansız hava aracı entegrasyon "
                    "modülü, demiryolu ve denizcilik alıcısı.",
                    "**User.** The vehicle receiver, the pedestrian receiver "
                    "(a portable field receiver), and the internet of "
                    "things receiver. "
                    "Later products: an integration module for unmanned "
                    "aircraft, and a receiver for rail and maritime.",
                ),
                _w(
                    "**Yazılım.** Merkezi yönetim paneli, GNSS bütünlük ve "
                    "olay haritası, filolar ve kritik altyapı için "
                    "arayüzler, analiz ve raporlama yazılımı ve "
                    "çevrimdışı yayın birimi konum haritası.",
                    "**Software.** The management panel, the GNSS "
                    "integrity and event map, interfaces for fleets and "
                    "critical infrastructure, analysis and reporting "
                    "software, and an offline map of where the units "
                    "are.",
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
        "On üç sistem, aynı sütunlarla yan yana. Koyu zeminli üç satırı "
        "simülasyon doldurdu; geri kalan on satır, o sistemlerin kendi "
        "kaynaklarının yayımladığı değerler. Bir sayıya ne yapıldığı "
        "altındaki dipnotta yazıyor. Boş hücre, o kaynağın bu sütuna "
        "uyan bir şey yayımlamadığı anlamına geliyor.",
        "Thirteen systems side by side under the same columns. The three "
        "shaded rows are the YERKON rows the simulation filled; the rest "
        "are what their own sources publish. What was done to a cell is "
        "in the note under it, and an empty cell means the source "
        "publishes nothing that fits that column.",
    ),
    parts=(
        Part(kind="shows", shows="landscape"),
        Part(kind="shows", shows="published"),
        Part(
            kind="shows", shows="accuracy",
            heading=_w("Doğruluk yan yana", "Accuracy side by side"),
        ),
        Part(kind="shows", shows="cost"),
        Part(
            kind="table",
            heading=_w("Sütunlar ne demek", "What the columns mean"),
            rows=(
                (_w("Sütun", "Column"), _w("Anlamı", "Meaning")),
                (
                    _w("HPE, VPE", "HPE, VPE"),
                    _w(
                        "Konumun yatayda ve düşeyde kaç metre şaştığı. "
                        "P50 hataların yarısının, P95 yüzde 95'inin altında "
                        "kaldığı değer.",
                        "How far the position is out, horizontally and "
                        "vertically, in metres. P50 is the value half the "
                        "errors stay under, P95 the one 95 per cent of "
                        "them stay under.",
                    ),
                ),
                (
                    _w("Kullanılabilirlik", "Availability"),
                    _w(
                        "Konum hesaplama denemelerinin yüzde kaçının "
                        "geçerli bir sonuç verdiği. Yalnızca modele giren "
                        "aksaklıkları sayar; bir hizmet garantisi "
                        "değildir.",
                        "What share of the attempts to work out a "
                        "position gave a valid one. It counts only the "
                        "failures in the model, and is not a promise about "
                        "a service.",
                    ),
                ),
                (
                    _w("Alan", "Area"),
                    _w(
                        "Konum hesaplamaya yetecek kadar birimin "
                        "duyulduğu zemin, gerçek arazi taranarak bulundu. "
                        "Sinyalin ulaştığı zeminle aynı şey değil.",
                        "The ground where enough units can be heard to "
                        "work out a position, found by sweeping the real "
                        "terrain. Not the same as the ground the signal "
                        "reaches.",
                    ),
                ),
                (
                    _w("CAPEX", "CAPEX"),
                    _w(
                        "Yayın birimlerinin donanım maliyeti, hizmet "
                        "verilen alana bölündü; kartın bütün parçaları ve "
                        "montaj dahil.",
                        "Unit hardware cost divided by the service area; "
                        "every part of the board and the fitting included.",
                    ),
                ),
                (
                    _w("OPEX", "OPEX"),
                    _w(
                        "Bir km²'yi bir yıl işletmenin masrafı; tek tek "
                        "yazılmış gider kalemlerinden çıkıyor.",
                        "What a year of running one km² costs, from an "
                        "itemised list of what recurs.",
                    ),
                ),
            ),
        ),
        Part(
            kind="points",
            heading=_w("Tabloyu okurken üç uyarı",
                       "Three warnings for reading the table"),
            lines=(
                _w(
                    "**Tünel satırının maliyeti kilometre başına, "
                    "diğerleri kilometrekare başına.** 12 m genişliğinde "
                    "2 km'lik bir tünel bir km²'nin ellide biri kadar yer "
                    "kaplar; alana bölmek sayıyı tünel pahalı olduğu için "
                    "değil payda küçük olduğu için büyütür. Tünel bir "
                    "alana değil bir hatta hizmet ediyor, o yüzden o iki "
                    "hücre güzergâh kilometresine bölündü ve \"/km\" ile "
                    "işaretli. Aynı ölçü olmadığı için diğer satırlarla "
                    "yan yana okunmamalı.",
                    "**The tunnel row is priced per kilometre, the other "
                    "two per square kilometre.** Twelve metres wide over "
                    "two kilometres is a fiftieth of a square kilometre, "
                    "so dividing by area makes the number large because "
                    "the denominator is small rather than because a "
                    "tunnel is dear. A tunnel serves a line, so those two "
                    "cells are divided by route kilometre and marked "
                    "\"/km\". They are not the same measure as the other "
                    "rows and should not be read beside them.",
                ),
                _w(
                    "**Hizmet alanı, konum alınabilen yerdir**, sinyalin "
                    "ulaştığı yer değil. Sinyalin ulaştığı zemin daha "
                    "geniş: bir birimi duymak yetmiyor, konum için aynı "
                    "anda dört birim gerekiyor.",
                    "**The service area is where a position can be had**, "
                    "not where the signal arrives. The ground the signal "
                    "reaches is wider: hearing one unit is not enough, a "
                    "position needs four at once.",
                ),
                _w(
                    "**Yüzdeler aynı şeyi ölçmüyor.** Uydu sistemlerinin "
                    "yayımladığı kullanılabilirlik değerleri farklı "
                    "testlerden, farklı sürelerden ve farklı eşiklerden "
                    "geliyor. Aynı ölçüm gibi yan yana okunmamalı.",
                    "**The percentages do not measure the same thing.** "
                    "The availability figures the satellite systems "
                    "publish come from different tests, over different "
                    "durations, against different thresholds. They should "
                    "not be read side by side as one measurement.",
                ),
            ),
        ),
    ),
)

SIMULATION = Page(
    slug="simulasyon",
    nav=_w("Simülasyon", "The simulation"),
    title=_w("Simülasyon", "The simulation"),
    lead=_w(
        "Simülasyon bu projenin bir parçası, tamamı değil. Tek bir işi "
        "vardı: karşılaştırma tablosundaki üç YERKON satırını tahminle "
        "değil, her sayısı kaynağına kadar izlenebilen bir modelle "
        "doldurmak. Sahada yapılmış bir ölçüm değildir. Yerleşimler maliyet "
        "yapılabilirliğini göstermek için; birim sayısı ve yeri "
        "değiştirilerek istenilen yerde istenilen doğruluğa ulaşılabilir.",
        "The simulation is one part of this project rather than the whole "
        "of it. It had one job: to fill the three YERKON rows of the "
        "comparison table with a model whose every number can be traced, "
        "instead of with an estimate. It is not a field measurement. The "
        "placements are there to show cost feasibility; with more units, or "
        "units elsewhere, the accuracy wanted can be had where it is "
        "wanted.",
    ),
    parts=(
        Part(
            kind="picture",
            picture="simulator.webp",
            lines=(_w(
                "Şehir içi satırı, koşusu bitmiş hâlde: Kızılay'ın "
                "gerçek arazisi, aydınlatma direklerine takılmış yayın "
                "birimleri ve zemine boyanmış kapsama haritası. Renkler o "
                "noktada kaç birimin duyulduğunu gösteriyor; konum hesabı "
                "için en az dört gerekiyor. Sağdaki panel o sekmenin "
                "kendi koşusu, sekiz gölge çekilişi havuzlanmış.",
                "The urban row with its run finished: the real terrain "
                "at Kızılay, the broadcast units on lighting columns, and "
                "the coverage painted onto the ground. The colours show "
                "how many units can be heard at that point; working out a "
                "position needs at least four. The panel on the right is "
                "that tab's own run, pooled over eight draws of the "
                "shadows.",
            ),),
        ),
        Part(
            kind="points",
            heading=_w("Arazi gerçek", "The ground is real"),
            lines=(
                _w(
                    "Üç satır da Ankara'nın gerçek arazisi üzerinde "
                    "koşuldu. Yükseklik verisi Copernicus'un 30 metrelik "
                    "haritasından bir kez indirilip paketin içine kondu, "
                    "yani depoyu indiren biri tabloyu internete hiç "
                    "çıkmadan yeniden üretebiliyor.",
                    "All three rows stand on real ground near Ankara, "
                    "fetched once from the Copernicus 30 m DEM and baked "
                    "into the package, so a clone reproduces the table "
                    "without touching the network.",
                ),
                _w(
                    "Şehir Kızılay: bir kenarı üç kilometre, en alçak ve "
                    "en yüksek noktası arasında 91 metre fark var. Açık "
                    "arazi Polatlı ovası: bir kenarı yirmi kilometre, 486 "
                    "metre yükseklik farkıyla. Tünel ise "
                    "Kızılcahamam'daki dağların içinden geçen gerçek bir 2 "
                    "kilometrelik güzergâh.",
                    "The city is Kızılay: three kilometres on a side, "
                    "with 91 metres between its lowest and highest point. "
                    "The open country is the Polatlı plain, twenty "
                    "kilometres on a side with 486 metres of it. The "
                    "tunnel is a real two kilometre bore through the "
                    "mountains at Kızılcahamam.",
                ),
                _w(
                    "Hiçbir yerde \"düz zemin\" seçeneği yok. Düz bir "
                    "yüzey modelin çizebileceği en tarafsız arazi değil, "
                    "en elverişli arazidir: sonucu olduğundan iyi "
                    "gösterirdi.",
                    "Nowhere is there a \"flat ground\" option. A flat "
                    "surface is not the most neutral terrain the model can "
                    "draw, it is the most favourable one: it would make "
                    "the result look better than it is.",
                ),
            ),
        ),
        Part(
            kind="points",
            heading=_w("Menzili tek bir hesap belirler",
                       "One calculation decides the range"),
            lines=(
                _w(
                    "Kodun hiçbir yerinde \"azami menzil şu kadardır\" "
                    "diye bir sayı yok. Menzil, sinyalin yolda ne kadar "
                    "zayıfladığı hesaplanarak çıkıyor. Aynı hesap iki "
                    "şeye birden karar veriyor: bağlantı kuruluyor mu ve "
                    "kurulduysa ne kadar hassas ölçüyor.",
                    "Nowhere in the code is there a number saying \"the "
                    "maximum range is this\". Range comes out of working "
                    "out how much the signal weakens on its way. The same "
                    "calculation decides two things at once: whether the "
                    "link holds, and how precisely it measures when it "
                    "does.",
                ),
                _w(
                    "Sinyal alıcıya iki yoldan gelir: doğrudan ve "
                    "zeminden sekerek. Belli bir mesafeden sonra bu ikisi "
                    "ters düşüp birbirini zayıflatır. O mesafe anten "
                    "yüksekliğiyle birlikte arttığı için, birimi alçağa "
                    "koymak menzilden götürür.",
                    "The signal reaches the receiver two ways: directly, "
                    "and bouncing off the ground. Past a certain distance "
                    "those two fall out of step and weaken each other. "
                    "That distance grows with antenna height, so mounting "
                    "a unit low costs range.",
                ),
                _w(
                    "Sinyal engellerin üzerinden bükülerek geçer ve bu "
                    "sırada zayıflar. Hesap, yoldaki en kötü tek engele "
                    "değil bütün araziye bakıyor (ITU-R P.526-15 §4.5.2, "
                    "delta-Bullington). Kızılay'da bir bağlantının önünde "
                    "ortalama üç engel var, en kötüsünde on altı.",
                    "The signal bends over obstacles and weakens doing "
                    "it. The calculation looks at the whole terrain rather "
                    "than the worst single obstacle on the path (ITU-R "
                    "P.526-15 §4.5.2, delta Bullington). A link across "
                    "Kızılay has three obstacles in front of it at the "
                    "median, sixteen at the worst.",
                ),
                _w(
                    "Arazi on metrede bir okunuyor. Sabit 64 noktada "
                    "okunsaydı 6,9 km'lik bir kırsal bağlantıda bu 108 "
                    "metrede bir demek olurdu; aradaki tümsekler "
                    "atlandığı için kayıp 37,60 dB yerine 31,28 dB "
                    "çıkardı.",
                    "The terrain is read every ten metres. Read at a "
                    "fixed 64 points, a 6,9 km rural link would be read "
                    "every 108 metres, and skipping the rises in between "
                    "would put the loss at 31,28 dB where the answer is "
                    "37,60.",
                ),
                _w(
                    "Bir bağlantıda bu iki kayıptan büyük olan hesaba "
                    "giriyor, ikisi toplanmıyor. İkisi de aynı arazinin aynı bağlantıya "
                    "yaptığını anlatıyor; toplamak aynı tepeyi iki kez "
                    "saymak olurdu.",
                    "A link counts the larger of those two losses, not "
                    "their sum. Both describe what the same terrain does "
                    "to the same link, and adding them would count the "
                    "same hill twice.",
                ),
                _w(
                    "Bunların üstüne bir de gölgeleme biniyor: aynı "
                    "mesafedeki iki bağlantının, arada ne olduğuna göre "
                    "farklı çıkması. Yol açıkken 4 dB, kapalıyken 7,8 dB kadar "
                    "(3GPP TR 38.901). Rastgele olduğu için hesap sekiz kez "
                    "tekrarlanıyor ve sekiz denemenin bütün sonuçları bir "
                    "arada değerlendiriliyor.",
                    "Shadowing sits on top of those: two links the same "
                    "distance apart come out different depending on what "
                    "stands between. 4 dB with a clear path, about 7,8 dB without "
                    "(3GPP TR 38.901). It is random, so the calculation "
                    "is repeated eight times and all the results of the "
                    "eight are read together.",
                ),
            ),
        ),
        Part(
            kind="points",
            heading=_w("Mesajlaşma ve konum hesabı",
                       "The messages and the position"),
            lines=(
                _w(
                    "Mesafe hesapla çıkarılmaz, ölçülür. İki telsiz "
                    "karşılıklı mesaj gönderir; SX1280'de bir ölçüm "
                    "alışverişi, frekans atlamanın istediği %5 sessizlikle "
                    "birlikte 33,4 milisaniye sürüyor.",
                    "A distance is measured rather than calculated. Two "
                    "radios send messages back and forth; on the SX1280 "
                    "one ranging exchange takes 33,4 milliseconds, "
                    "including the 5 % rest frequency hopping asks for.",
                ),
                _w(
                    "On iki birimle sırayla ölçüşmek 401 milisaniye "
                    "sürüyor. Bu sürede 100 km/sa giden araç 11,1 metre yol "
                    "alıyor, yani bir turdaki ölçümler aynı ana ait değil. "
                    "Hesap da onları aynı anda alınmış gibi kabul "
                    "etmiyor.",
                    "Measuring against twelve units in turn takes 401 "
                    "milliseconds. A car doing 100 km/h covers 11,1 metres "
                    "in that time, so the measurements in one round do not "
                    "belong to one instant. The calculation does not "
                    "pretend they do.",
                ),
                _w(
                    "Konumu hesaplayan kod, aracın gerçekte nerede "
                    "olduğunu hiç görmez. Yalnızca şunları görür: ölçülen "
                    "mesafe, birimin kurulumda ölçülmüş konumu, ölçümün "
                    "saati ve o ölçüme ne kadar güvenildiği.",
                    "The code that works out the position never sees "
                    "where the vehicle really is. It sees only these: the "
                    "measured distance, the unit's position as surveyed at "
                    "installation, the time of the measurement, and how "
                    "much that measurement is trusted.",
                ),
                _w(
                    "Yol kenarına dizilmiş birimler hep aynı yükseklikte "
                    "olduğu için yüksekliği mesafelerle ölçmek zor. Filtre "
                    "bu yüzden alıcının haritasındaki yol yüksekliğini bir "
                    "ölçüm olarak alıyor, 2,43 m'lik bir harita hatasıyla; "
                    "hata yol boyunca parça parça çekiliyor. Tablodaki VPE "
                    "sütunu bu hesabın sonucu.",
                    "Units strung along a roadside are all at much the "
                    "same height, which leaves the vertical hard to "
                    "measure from ranges. The filter therefore takes the "
                    "road's height from the receiver's map as a measurement, "
                    "with a map error of 2,43 m drawn in patches along the "
                    "road. The VPE column is the result.",
                ),
            ),
        ),
        Part(kind="shows", shows="spread"),
        Part(
            kind="points",
            heading=_w("Ortalamayla geçmeyen üç hata",
                       "Three errors that averaging will not remove"),
            lines=(
                _w(
                    "**Önü kapalı bir bağlantı olduğundan uzun ölçer.** "
                    "Sinyal engelin üzerinden dolaşıyor ve ölçüm bu uzun "
                    "yolu sayıyor. Hata hep aynı yöne, artı yöne gidiyor; "
                    "bu yüzden çok ölçüp ortalamak onu götürmüyor.",
                    "**A blocked link measures longer than it is.** The "
                    "signal goes around the obstacle and the measurement "
                    "counts that longer way. The error always goes the "
                    "same way, so measuring more often and averaging does "
                    "not remove it.",
                ),
                _w(
                    "**Birimin konumu kurulumda yanlış ölçüldüyse, o "
                    "yanlış orada kalır.** Her birim için bir kez "
                    "çekiliyor ve sonuna kadar taşınıyor. Tünelde "
                    "hataların ortancası, birimler kusursuz ölçülmüş "
                    "olsaydı 0,12 m çıkıyor; 15 cm'lik bir ölçüm hatasıyla "
                    "bunun yaklaşık beş katı. Konum, birimlerin yerinin "
                    "ölçüldüğünden daha iyi olamaz.",
                    "**If a unit's position is surveyed wrong at "
                    "installation, it stays wrong.** It is drawn once per "
                    "unit and carried to the end. In the tunnel the median "
                    "error is 0,12 m with a perfect survey and about five "
                    "times that with 15 cm of survey error. A position "
                    "cannot be better than the survey of the units.",
                ),
                _w(
                    "**Kaybolan mesaj ölçüm vermez.** Kullanılan 2,4 GHz "
                    "bandı kablosuz ağlarla ortak, yani kalabalık. Şehirde "
                    "mesajların %15'i kayboluyor, açık yolda %5'i, tünelde "
                    "hiçbiri.",
                    "**A lost message gives no measurement.** The 2,4 GHz "
                    "band is shared with wireless networks, so it is "
                    "crowded. 15% of messages are lost in the city, 5% on "
                    "the open road, none in the tunnel.",
                ),
            ),
        ),
        Part(
            kind="points",
            heading=_w("Modele girmeyenler", "What is left out"),
            lines=(
                _w(
                    "Aracın hareket sensörü ve tekerlek turu hesaba "
                    "katılmadı. Filtre yalnız telsiz ölçümlerini ve "
                    "haritadan gelen yüksekliği birleştiriyor. Rapordaki "
                    "tasarımda ikisi de var; buradaki sayılar bu yüzden "
                    "gerçek bir araçtan daha kötü.",
                    "The vehicle's motion sensor and wheel turns are left "
                    "out. The filter combines only the radio measurements "
                    "and the height from the map. The report's design has "
                    "both, so these numbers are worse than a real "
                    "vehicle's.",
                ),
                _w(
                    "Sinyalin bina duvarlarından sekerek birden çok "
                    "yoldan gelmesi (çok yollu yayılım) ayrıca "
                    "modellenmedi; modelde yalnız zeminden sekme ve önü "
                    "kapalı bağlantının uzun ölçmesi var. Telsizin kendi "
                    "gürültüsü ve mesajlaşma sırasında saatin kayması ise "
                    "modelde.",
                    "The signal arriving by several paths after bouncing "
                    "off building walls (multipath) is not modelled on its "
                    "own; the model has the bounce off the ground and the "
                    "long reading of a blocked link. The radio's own noise "
                    "and the clock drifting during the exchange are in the "
                    "model.",
                ),
                _w(
                    "Tünel kaybı gerçek bir karayolu tünelinde 2,8-5 GHz'de "
                    "ölçülmüş bir modelden geliyor ve 6,5 GHz'e taşındı; "
                    "6,5 GHz'de ölçülmedi.",
                    "The tunnel loss comes from a model measured in a real "
                    "road tunnel at 2,8 to 5 GHz and carried to 6,5 GHz; "
                    "it was not measured at 6,5 GHz.",
                ),
                _w(
                    "Güvenlik katmanı da yok. İmza doğrulama, anahtar "
                    "yönetimi ve birimlerin merkeze gönderdiği yaşam "
                    "sinyalleri tasarımın parçası, simülasyonun değil.",
                    "The security layer is absent too. Signature checking, "
                    "key management and the \"still working\" messages the "
                    "units send the centre belong to the design rather than "
                    "to the simulation.",
                ),
            ),
        ),
        Part(
            kind="text",
            heading=_w("Zaten yüksek yerler",
                       "Places that are already high"),
            lines=(
                _w(
                    "Şehir içi ve kırsal satırlarda direkler bir ızgarada "
                    "değil, bir yerleşim aramasının seçtiği yerlerde "
                    "durur; simülatördeki **En iyi yerleşimi bul** bölümü "
                    "ve **Hızlı başla** kutusu aynı aramayı haritadan "
                    "seçilen başka bir yer için koşar. Aday yerler "
                    "var olan "
                    "aydınlatma direkleri ve tabelalar, yol kenarındaki "
                    "direkler (şehirde aydınlatma, kırsalda elektrik "
                    "dağıtım direği) ve tepelere dikilecek 25 m'lik "
                    "direklerdir. Çatılar bina sahibinden kiralandığı için "
                    "aday sayılmıyor. "
                    "Her aday bağlantı bütçesiyle denenir; seçim, ömür "
                    "boyu maliyete göre bir örtme aramasıdır. Bir noktanın "
                    "kapsandığı sayılması için dört birime ulaşması ve bu "
                    "birimlerin noktanın etrafındaki dört yönün (kuzey, "
                    "güney, doğu, batı çeyrekleri) en az üçüne dağılmış "
                    "olması gerekiyor. Birimlerin hepsi aynı caddeye, aynı "
                    "yöne dizilirse konum o cadde boyunca belirlenemez.",
                    "In the urban and rural rows the anchors do not stand "
                    "on a grid but where a placement search put them; the "
                    "simulator's **Find the best layout** section and its "
                    "**Quick start** box run the same search for another "
                    "place picked on the map. The candidates are "
                    "existing "
                    "lighting columns and signs, poles along the road "
                    "(lighting columns in town, electricity distribution "
                    "poles in open country) and 25 m masts to be put up "
                    "on hilltops. Roofs are rented from their owners, so they "
                    "are not offered. "
                    "Every candidate is tried with the link budget, and "
                    "the choice is a cover search by lifecycle cost. A "
                    "point counts as covered once four units reach it "
                    "and they are spread over at least three of the four "
                    "quarters around it. Units all strung along one "
                    "street, on one side, cannot fix a position along "
                    "that street.",
                ),
                _w(
                    "Arama yerleri bulur ve kendi hızlı tahminini verir; o "
                    "yerleşimin gerçek doğruluğunu simülasyon ölçer. "
                    "Önerilen yerleşimi uygulayıp **Simülasyonu çalıştır** "
                    "düğmesine basınca eski yerleşimle aynı yolculukta "
                    "karşılaştırılır.",
                    "The search finds the places and gives its own quick "
                    "estimate; the simulation measures how accurate that "
                    "placement really is. Apply the proposed layout and press **Run the "
                    "simulation** to compare it with the layout it replaces "
                    "on the same journey.",
                ),
            ),
        ),
        Part(
            kind="text",
            heading=_w("Tarayıcıda ve kendi makinende",
                       "In the browser, and on your own machine"),
            lines=(
                _w(
                    "**Simülasyonu çalıştır** düğmesi simülatörü bu "
                    "tarayıcıda açar. Hiçbir sunucu hesap yapmaz: Python, "
                    "numpy ve bu projenin kendi paketi sayfaya iner ve her "
                    "şey bu bilgisayarda koşar. İlk açılış yaklaşık 20 MB "
                    "indirir ve bir dakika kadar sürebilir; sonra tarayıcı "
                    "saklar. Tarayıcıda tek işlemci kullanıldığı için bir "
                    "koşu yerel kurulumdakinden yavaştır; **Hızlı dene** "
                    "bunu kısaltır.",
                    "The **Run the simulation** button opens the simulator "
                    "in this browser. No server computes anything: Python, "
                    "numpy and this project's own package come down to "
                    "the page and everything runs on this computer. The "
                    "first load fetches about 20 MB and can take a minute; "
                    "after that the browser keeps it. In a browser one "
                    "processor does the work, so a run is slower than in "
                    "a local install; **Try it fast** shortens it.",
                ),
                _w(
                    "Tabloyu yeniden yayımlamak, başka bir şehrin zeminini "
                    "indirmek ya da üç satırı birden tam çözünürlükte "
                    "koşturmak için yerel kurulum gerekir. Dört komut:",
                    "Republishing the table, fetching another city's "
                    "ground, or running all three rows at full resolution "
                    "needs a local install. Four commands:",
                ),
            ),
        ),
        Part(
            kind="text",
            heading=_w("Hızlı okuma", "The fast reading"),
            lines=(
                _w(
                    "Simülatördeki **Hızlı dene** düğmesi ve komut "
                    "satırındaki `--fast` iki şeyi kabalaştırır: yoldaki "
                    "engellerin rastgele etkisi sekiz yerine bir kez "
                    "denenir ve arazi 10 m'de bir yerine her bağlantıda "
                    "sabit 64 noktada okunur. Hesap on beş dakikadan bir "
                    "dakikaya iner.",
                    "The **Try it fast** button in the simulator and `--fast` on "
                    "the command line coarsen the same two figures: the "
                    "shadows are drawn once instead of pooled over eight, "
                    "and the ground profile is read at a fixed 64 samples "
                    "instead of every 10 m. A run drops from fifteen "
                    "minutes to about one.",
                ),
                _w(
                    "Arazi seyrek okununca tepelerin arkasındaki zayıflama "
                    "eksik hesaplanıyor, bu da hızlı sonucu çoğunlukla "
                    "olduğundan iyi gösteriyor. Engellerin etkisini bir kez "
                    "denemek ise iki yöne de saptırabiliyor: aynı "
                    "yerleşimde bir satır hızlıda iyi, başka biri kötü "
                    "çıkabiliyor. Hızlı hesap yalnız denemek için; Sonuçlar "
                    "sayfasındaki tablo yalnızca yavaş ve tam hesaptan "
                    "gelir.",
                    "The coarse ground reads diffraction loss low, which "
                    "mostly makes a fast answer flatter the deployment. "
                    "The single shadow draw can err either way: on the same "
                    "placement one row can come out better fast and "
                    "another worse. A fast run is for trying things; the "
                    "table on the Results page comes from the slow, full "
                    "run only.",
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
        "Buradaki her sayının dayanağı altı türden biri: yayımlanmış bir "
        "fiyat ya da veri sayfası, bir ölçüm, bir standart ya da mevzuat, "
        "kaynaklı sayılardan yapılmış bir hesap, bir tasarım kararı ya "
        "da açıkça yazılmış bir varsayım.",
        "Every number here rests on one of six kinds of thing: a "
        "published price or datasheet, a measurement, a standard or "
        "regulation, a calculation from sourced figures, a design choice, "
        "or an assumption written down.",
    ),
    parts=(
        Part(
            kind="points",
            heading=_w("Standartlar ve veri", "Standards and data"),
            lines=(
                _w("ITU-R P.526-15 §4.5.2, delta-Bullington kırınımı.",
                   "ITU-R P.526-15 §4.5.2, delta Bullington diffraction."),
                _w("ITU-R P.452 ve P.1812: sinyalin yolda nasıl zayıfladığı.",
                   "ITU-R P.452 and P.1812: how the signal weakens on its way."),
                _w("3GPP TR 38.901 Tablo 7.4.1-1: gölgeleme genişlikleri.",
                   "3GPP TR 38.901 Table 7.4.1-1: shadowing widths."),
                _w("Copernicus DEM 30 m: arazinin yükseklikleri.",
                   "Copernicus DEM 30 m: ground heights."),
                _w("OpenStreetMap ve Overture: binalar ve yol kenarındaki "
                   "direkler, levhalar, panolar.",
                   "OpenStreetMap and Overture: buildings, and the masts, "
                   "signs and boards along the road."),
                _w("Semtech SX1280, EBYTE E28-2G4M20S ve E28-2G4M12S, Qorvo "
                   "DWM3000 veri sayfaları ve SX1280 uzun menzil testi.",
                   "Semtech SX1280, EBYTE E28-2G4M20S and E28-2G4M12S, "
                   "Qorvo DWM3000 datasheets, and the SX1280 long range "
                   "test."),
                _w("DigiKey, LCSC, JLCPCB, Mouser, Gainta ve diğer "
                   "satıcıların kademe fiyatları, 25-28 Eylül 2026. Kur 4 "
                   "Eylül 2026, 48,44 TL/USD ve 1,1622 USD/EUR.",
                   "Tier prices from DigiKey, LCSC, JLCPCB, Mouser, Gainta "
                   "and other sellers, 25 to 28 September 2026. Exchange "
                   "rates of 4 September 2026, 48,44 TL a dollar and "
                   "1,1622 dollars a euro."),
                _w("Karşılaştırma tablosunun bizim olmayan satırları "
                   "aşağıdaki kaynakçadan gelir. Tablonun altındaki her "
                   "dipnot, dayandığı girdiye bağlıdır.",
                   "The rows of the comparison table that are not ours "
                   "come from the bibliography below. Every note under the "
                   "table links to the entry it rests on."),
            ),
        ),
        Part(
            kind="text",
            heading=_w("Kaynakça", "Bibliography"),
            lines=(
                _w(
                    "Raporun kaynakça bağlantılarının tamamı, raporda "
                    "yazıldığı hâliyle ve sitenin maliyet ve mevzuat "
                    "hesapları için eklediği kaynaklar. Bir girdiyi hiçbir "
                    "dipnot anmıyorsa da listede kalır.",
                    "Every hyperlink in the report's bibliography, as the "
                    "report wrote it, and the sources the site added for "
                    "its cost and regulation figures. An entry no note "
                    "cites is still listed.",
                ),
            ),
        ),
        Part(kind="shows", shows="bibliography"),
        Part(
            kind="code",
            heading=_w("Tabloyu yeniden üretmek", "Reproducing the table"),
            code=_w(
                "pip install -e \".[dev]\"\n"
                "yerkon table          # yayımlanan sayılar, ~15 dk\n"
                "yerkon table --fast   # denemek için, ~1 dk, yayımlanmaz\n"
                "yerkon view           # bu site ve simülasyon",
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
                    "Arazi verisi paketin içinde geliyor, yani tablo "
                    "internete hiç çıkmadan yeniden üretiliyor. Rastgele "
                    "sayıların başlangıcı sabit, o yüzden her koşu aynı "
                    "sonucu veriyor.",
                    "The terrain data ships inside the package, so the "
                    "table reproduces with no network at all. The random "
                    "seed is fixed, so every run gives the same answer.",
                ),
                _w("`CONTEXT.md` sözlüktür: her terimin kodda kullanılan "
                   "adı ve raporda kullanılan karşılığı.",
                   "`CONTEXT.md` is the glossary: the name the code uses "
                   "for each term beside the one the report uses."),
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
                    "tablosundaki üç YERKON satırını üreten simülasyondur.",
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

COST = Page(
    slug="maliyet",
    nav=_w("Maliyet", "Cost"),
    title=_w("Ne kadara mal oluyor", "What it costs"),
    lead=_w(
        "Tablodaki her maliyet hücresinin kalem kalem dökümü: hangi parça, "
        "kaça, kimden; hangi sayı, neye dayanarak. Bu sayfadaki sayılar "
        "modelden ve parça listesinden hesaplanıyor; biri değişince sayfa "
        "da değişiyor. Yalnız direk fiyatları tablosu kaynaklarından "
        "aktarıldı.",
        "Every cost cell in the table, line by line: which part, for how "
        "much, from whom; which figure, resting on what. The numbers on "
        "this page are worked out from the model and the parts list, so "
        "when one changes the page does too. Only the pole price table is copied from its "
        "sources.",
    ),
    parts=(
        Part(
            kind="shows", shows="cost-rows",
            heading=_w("Satır satır", "Row by row"),
        ),
        Part(
            kind="points",
            lines=(
                _w(
                    "Şehir içi ve kırsal satırlar hizmet verdikleri alana, "
                    "tünel ise uzunluğuna bölünüyor; tablodaki hücreler bu "
                    "dökümün son satırlarıdır.",
                    "The urban and rural rows are divided by the ground "
                    "they serve and the tunnel by its length; the cells in "
                    "the table are the last lines of this breakdown.",
                ),
                _w(
                    "Alıcılar bu dökümde yok. Onları kimin alacağı "
                    "başvuruda belirlenmedi, o yüzden kilometrekare başına "
                    "rakamlara girmiyorlar.",
                    "Receivers are not in this breakdown. The application "
                    "does not settle who buys them, so they never enter the "
                    "per square kilometre figures.",
                ),
            ),
        ),
        Part(
            kind="shows", shows="units",
            heading=_w("Yayın birimleri: bir birim nerede ne kadar",
                       "Broadcast units: what one costs where"),
        ),
        Part(
            kind="text",
            lines=(
                _w(
                    "Yapı iki şey sağlıyor: elektrik ve merkeze giden bir "
                    "hat. Işıklı bir kavşakta sinyal dolabı durur; hem "
                    "besleme hem de trafik yönetim merkezine giden hat "
                    "oradadır ve belediyenin kameraları o hattı zaten "
                    "kullanıyor. Hattı olan yapıdaki birim merkeze o "
                    "hattan bağlanıyor: şehirde ışıklı kavşak, tünelde "
                    "tünelin haberleşme omurgası, kırsalda yol üzerindeki "
                    "AUS noktası. Hattı olmayan birim, örneğin kırsalda "
                    "AUS'tan uzak bir dağıtım direğindeki, güneş paneliyle "
                    "çalışmaya devam ediyor ve mesajlarını kendi telsiziyle "
                    "hattı olan en yakın birime iletiyor; hiçbir birime SIM "
                    "kartı konmuyor. Her birim merkeze düzenli aralıklarla "
                    "kısa bir \"çalışıyorum\" mesajı (yaşam sinyali) "
                    "gönderiyor; mesajı gelmeyen birim arızalı sayılıyor ve "
                    "ekip gönderiliyor. Alıcılar GPS karıştırması ya da "
                    "aldatması gördüğünde bunu yakındaki yayın birimine "
                    "iletiyor, uyarı da aynı yoldan merkeze ulaşıyor.",
                    "A structure gives two things: power and a line to the "
                    "centre. A signalised junction carries a controller "
                    "cabinet with both the mains and a line to the traffic "
                    "management centre, which the municipality's cameras "
                    "already use. A unit on a structure with a line reaches "
                    "the centre over it: a signalised junction in town, "
                    "the tunnel's communications spine in a tunnel, an ITS "
                    "point on the road in open country. A unit with no "
                    "line, such as one on a distribution pole far from an "
                    "ITS point, keeps running on its solar panel and passes "
                    "its messages by its own radio to the nearest unit that "
                    "has a line; no unit carries a SIM card. Each unit "
                    "sends the centre a short \"still working\" message at "
                    "regular intervals, and a unit whose message stops "
                    "coming is taken as failed and a crew is sent. When a "
                    "receiver sees GPS jamming or spoofing it passes that "
                    "to a nearby broadcast unit, and the warning reaches "
                    "the centre the same way.",
                ),
                _w(
                    "Direk eklemek kullanılabilirliği yükseltiyor ama "
                    "bedava değil. Mevcut yapılar bunu karşılanabilir "
                    "kılıyor: her ek birim yeni bir saha değil, bir kart ve "
                    "bir montaj.",
                    "Adding anchors raises availability, but not for "
                    "nothing. What the existing structures do is make that "
                    "trade affordable, because each extra unit is a board "
                    "and a fitting rather than a site.",
                ),
            ),
        ),
        Part(
            kind="table",
            heading=_w("Direklerin boyu ve fiyatı", "Pole heights and prices"),
            rows=(
                (_w("Yapı", "Structure"), _w("Boy", "Height"), _w("Fiyat", "Price"), _w("Kaynak", "Source")),
                (_w("Aydınlatma direği, TEDAŞ tipi galvaniz poligon", "Lighting column, TEDAŞ-type galvanised polygonal"), _w("6 / 8 / 10 / 12 / 14 / 15 m", "6 / 8 / 10 / 12 / 14 / 15 m"), _w("6500 / 9750 / 14750 / 18250 / 24750 / 27500 TL", "6500 / 9750 / 14750 / 18250 / 24750 / 27500 TL"), _w("Pana Bayrak Direği, Eylül 2026", "Pana Bayrak Direği, September 2026")),
                (_w("Aydınlatma direği, galvaniz yol direği", "Lighting column, galvanised road column"), _w("8-10 m", "8-10 m"), _w("14000-28000 TL", "14000-28000 TL"), _w("Palmiye Aydınlatma, Ocak 2026", "Palmiye Aydınlatma, January 2026")),
                (_w("Galvaniz direk", "Galvanised pole"), _w("20 / 30 m", "20 / 30 m"), _w("120000 / 475000 TL", "120000 / 475000 TL"), _w("Pana Bayrak Direği, Eylül 2026", "Pana Bayrak Direği, September 2026")),
                (_w("Dağıtım direği, santrifüj betonarme", "Distribution pole, spun concrete"), _w("9,3-25 m", "9,3-25 m"), _w("yayımlanmamış", "not published"), _w("TEDAŞ-MLZ/99-34 şartnamesi", "TEDAŞ specification MLZ/99-34")),
            ),
        ),
        Part(
            kind="text",
            lines=(
                _w("YERKON var olan direği kullanıyor, direk satın almıyor; "
                   "bu fiyatlar yeni bir direk dikmenin ne tuttuğunu ve "
                   "25 m direğin bedelinin nereden geldiğini gösteriyor. "
                   "Aydınlatma direği boyları TEDAŞ'ın yol sınıfı "
                   "çizelgesinden (6-14 m), dağıtım direği boyları "
                   "TEDAŞ-MLZ/99-34'ten; kaynakları Mevzuat sayfasında.",
                   "YERKON uses the pole that stands and buys none; these "
                   "prices show what raising a new one costs and where the "
                   "25 m mast's figure comes from. The column heights come "
                   "from TEDAŞ's road class table (6 to 14 m), the "
                   "distribution pole lengths from TEDAŞ-MLZ/99-34; their "
                   "sources are on the Regulation page."),
            ),
        ),
        Part(
            kind="shows", shows="bill",
            heading=_w("YERKON yayın birimleri fiyatları",
                       "YERKON broadcast unit prices"),
        ),
        Part(
            kind="shows", shows="parts", folded=True,
            heading=_w("Her kartın parçaları", "Every board's parts"),
        ),
        Part(
            kind="points",
            heading=_w("Fiyatlar nereden geldi", "Where the prices came from"),
            lines=(
                _w(
                    "Her parça satıcısının kendi kademe tablosuyla yazılı: "
                    "ana parçalar ve kartın geri kalanı, yani şebeke "
                    "beslemesi, düşürücü, koruma, klemens, anten kablosu, "
                    "kutu, pasifler, baskılı devre ve dizgi. Bir parça bir "
                    "kartta birden çok varsa (klemens, pasifler) kademe o "
                    "kadar kart için alınan adete göre seçiliyor.",
                    "Every part carries its seller's own price ladder: the "
                    "main parts and the rest of the board, that is the "
                    "mains supply, regulator, protection, terminals, "
                    "antenna cable, box, passives, the printed board and "
                    "its assembly. Where a board holds more than one of a "
                    "part (terminals, passives), the tier is the one the "
                    "pieces for that many boards reach.",
                ),
                _w(
                    "Satıcı bir adette kademe yayımlamamışsa indirim "
                    "varsayılmıyor, bilinen son kademe kullanılıyor. "
                    "Kutuların 100 adet üstü fiyatı teklifle veriliyor; "
                    "baskılı devrenin ve pilin büyük adet fiyatı okunamadı; "
                    "bunlar her adette tek adet fiyatıyla giriyor. Dizginin "
                    "kurulum, şablon ve parça yükleme bedeli siparişe bir "
                    "kez ödendiği için karta düşen payı adet büyüdükçe "
                    "küçülüyor. Maliyet tablosu 1000 adeti kullanıyor.",
                    "Where a seller published no tier for a quantity, no "
                    "discount is assumed and the last known tier holds. "
                    "The boxes are priced on request above a hundred, and "
                    "no volume price could be read for the printed board "
                    "or the battery; those enter at their one-unit price "
                    "at every quantity. Assembly setup, stencil and part "
                    "loading fees are paid once an order, so each board's "
                    "share shrinks as the order grows. The cost table uses "
                    "the thousand.",
                ),
                _w(
                    "Parça fiyatları satıcıların 25-28 Eylül 2026 liste "
                    "fiyatları; bağlantılar yukarıda. Sipariş öncesinde "
                    "teklifle doğrulanmalı. Bir fiyat değişirse bom.toml "
                    "dosyasındaki tek satır değişir, bu sayfa da tablo da "
                    "onu izler.",
                    "The part prices are the sellers' list prices of 25 "
                    "to 28 September 2026; the links are above. They are "
                    "to be confirmed by quotation before ordering. If a "
                    "price changes, one line in bom.toml changes and this "
                    "page and the table follow.",
                ),
            ),
        ),
        Part(
            folded=True,
            kind="shows", shows="assumptions",
            heading=_w("Her sayının dayanağı", "What every figure rests on"),
        ),
    ),
)

LAW = Page(
    slug="mevzuat",
    nav=_w("Mevzuat", "Regulation"),
    title=_w("Hangi kurallar, hangi sınırlar", "Which rules, which limits"),
    lead=_w(
        "YERKON'un gücünü, piyasaya çıkışını ve bakım maliyetini belirleyen "
        "kurallar, resmî kaynaklarıyla. Güç, bakım ve kira için burada "
        "yazan her sınır modelde de aynen kullanılıyor; prototip "
        "cihazlarının frekans kuralları sahadaki denemeler için.",
        "The rules that set YERKON's power, its route to market and its "
        "maintenance cost, with their official sources. Every limit on power, "
        "maintenance and rent written here is the one the model uses; the "
        "frequency rules for the prototype devices are for the field "
        "trials.",
    ),
    parts=(
        Part(
            kind="table",
            heading=_w("2,4 GHz'de ne kadar güç", "How much power at 2,4 GHz"),
            rows=(
                (_w("Kip", "Mode"), _w("Sınır", "Limit"),
                 _w("YERKON için ne demek", "What it means for YERKON")),
                (
                    _w("Frekans atlamasız", "Not hopping"),
                    _w("20 dBm e.i.r.p. ve 10 dBm/MHz",
                       "20 dBm e.i.r.p. and 10 dBm/MHz"),
                    _w("Sinyal 1,6 MHz genişliğinde. MHz başına 10 dBm "
                       "sınırı yüzünden toplam yayın gücü 12,1 dBm'yi "
                       "geçemiyor; 20 dBm'lik genel sınıra hiç "
                       "ulaşılamıyor.",
                       "The signal is 1,6 MHz wide. The 10 dBm a MHz "
                       "limit holds the total to 12,1 dBm, so the general "
                       "20 dBm limit is never reached."),
                ),
                (
                    _w("Uyarlamasız frekans atlama", "Non-adaptive hopping"),
                    _w("20 dBm; yayın dizisi en çok 5 ms, ara en az 5 ms; "
                       "bir frekansta 15 ms × N içinde en çok 15 ms; havayı "
                       "meşgul etme payı en çok %10",
                       "20 dBm; transmissions at most 5 ms with gaps of at "
                       "least 5 ms; at most 15 ms on one frequency in "
                       "15 ms × N; medium utilisation at most 10 %"),
                    _w("Uymuyor: bir ölçüm paketi SF10'da yaklaşık 15 ms "
                       "sürüyor ve araç sürekli soruyor.",
                       "Does not fit: one ranging frame lasts about 15 ms "
                       "at SF10 and a vehicle polls continuously."),
                ),
                (
                    _w("Uyarlamalı frekans atlama (dinle, sonra konuş)",
                       "Adaptive hopping (listen before talk)"),
                    _w("20 dBm; her beklemeden önce kanal kontrolü, eşik "
                       "-70 dBm/MHz; kanal kullanımı 60 ms'den kısa, "
                       "ardından onun en az %5'i kadar sessizlik; bandın en "
                       "az %70'inde çalışabilmeli",
                       "20 dBm; a channel check before each dwell, threshold "
                       "-70 dBm/MHz; channel occupancy under 60 ms, then "
                       "silence of at least 5 % of it; able to use at least "
                       "70 % of the band"),
                    _w("YERKON'un seçtiği kip, şehir içi ve kırsalda: tek "
                       "açık yol. Bir ölçüm alışverişi 31,8 ms, 60 ms'ye "
                       "sığıyor. Cevap veren direk de kendi yayınından önce "
                       "kanalı kontrol ediyor; bu, alışverişe 0,1 ms'den az "
                       "ekliyor. Laboratuvar testiyle belgelendirilmeli.",
                       "The mode YERKON uses in town and open country, and "
                       "the one open road. A ranging exchange is 31,8 ms "
                       "and fits in 60 ms. The replying pole checks the "
                       "channel before its own transmission too, which "
                       "adds under 0,1 ms. It must be certified by a test "
                       "laboratory."),
                ),
            ),
        ),
        Part(
            kind="table",
            heading=_w("Tünelde UWB, 6-8,5 GHz",
                       "UWB in the tunnel, 6-8,5 GHz"),
            rows=(
                (_w("Kullanım", "Use"),
                 _w("Sınır (e.i.r.p.)", "Limit (e.i.r.p.)"),
                 _w("YERKON için ne demek", "What it means for YERKON")),
                (
                    _w("Genel amaçlı UWB (Madde 18(1), Tablo 16)",
                       "General purpose UWB (Article 18(1), Table 16)"),
                    _w("Ortalama -41,3 dBm/MHz, tepe 0 dBm/50 MHz",
                       "Mean -41,3 dBm/MHz, peak 0 dBm/50 MHz"),
                    _w("Açık alanda sabit kullanılan ya da sabit bir dış "
                       "antene bağlı cihazlar ve kara taşıtlarındakiler bu "
                       "maddenin dışında. Yaya alıcısı bu satırda.",
                       "Devices fixed outdoors or on a fixed outdoor "
                       "antenna, and those in road vehicles, are outside "
                       "this article. The pedestrian receiver is in this "
                       "row."),
                ),
                (
                    _w("Konum izleme tip 1, LT1 (Madde 18(4), Tablo 19)",
                       "Location tracking type 1, LT1 (Article 18(4), "
                       "Table 19)"),
                    _w("Ortalama -41,3 dBm/MHz, tepe 0 dBm; TS EN 302 065-2",
                       "Mean -41,3 dBm/MHz, peak 0 dBm; TS EN 302 065-2"),
                    _w("İnsanların ve nesnelerin konumunu izleyen sistemler "
                       "için. Tünel birimleri bu satırda: 499,2 MHz'lik "
                       "kanalda -14,3 dBm e.i.r.p., model de bunu "
                       "kullanıyor.",
                       "For systems that track where people and objects "
                       "are. The tunnel units are in this row: -14,3 dBm "
                       "e.i.r.p. over a 499,2 MHz channel, which is what "
                       "the model uses."),
                ),
                (
                    _w("Karayolu ve demiryolu taşıtları (Madde 18(2), "
                       "Tablo 17)",
                       "Road and rail vehicles (Article 18(2), Table 17)"),
                    _w("Ortalama -53,3 dBm/MHz, tepe -13,3 dBm/50 MHz. "
                       "LDC ya da TPC ile ortalama -41,3 dBm/MHz, tepe "
                       "0 dBm/50 MHz; 0°'den büyük yükselme açılarında "
                       "-53,3 dBm/MHz harici sınırla. TS EN 302 065-3",
                       "Mean -53,3 dBm/MHz, peak -13,3 dBm/50 MHz. With "
                       "LDC or TPC, mean -41,3 dBm/MHz and peak 0 dBm/50 "
                       "MHz, with an exterior limit of -53,3 dBm/MHz at "
                       "elevation angles above 0°. TS EN 302 065-3"),
                    _w("Araç alıcısı bu satırda ve gücünü denetleyebilmeli "
                       "(TPC). Araçtaki cihaz kendi yüksekliğinin üstüne "
                       "daha az güç yayabiliyor (-53,3 dBm/MHz); altına "
                       "-41,3 dBm/MHz serbest (EN 302 065-3, 4.3.4.2 ve "
                       "Tablo 4). Tünel birimleri araç anteninin altında, "
                       "yoldan 1,2 m yüksekte durunca bu sınıra takılmıyor; "
                       "model de böyle hesaplıyor. Kapalı alan için otomatik bir istisna "
                       "yok, Ek C.1 eşdeğer korumanın kanıtlanmasına izin "
                       "veriyor.",
                       "The vehicle receiver is in this row and has to "
                       "control its power (TPC). The vehicle's device may "
                       "send less power above its own height (-53,3 "
                       "dBm/MHz); below it -41,3 dBm/MHz holds (EN 302 "
                       "065-3, 4.3.4.2 and table 4). Tunnel units below the "
                       "vehicle's antenna, 1,2 m above the road, stay clear "
                       "of that limit, and the model works it out that "
                       "way. There is no automatic "
                       "exemption for enclosed spaces; Annex C.1 allows "
                       "equivalent protection to be demonstrated."),
                ),
            ),
        ),
        Part(
            kind="points",
            heading=_w("UWB tanımları", "UWB definitions"),
            lines=(
                _w("Düşük görev çevrimi (LDC): gönderilen bütün sinyallerin "
                   "toplamı her saniyenin %5'inden ve her saatin %0,5'inden "
                   "az, tek bir sinyal en çok 5 ms.",
                   "Low duty cycle (LDC): all transmissions together under "
                   "5 % of every second and under 0,5 % of every hour, no "
                   "single transmission over 5 ms."),
                _w("Verici gücü kontrolü (TPC): cihazın, başka sistemlere "
                   "girişimi azaltmak için çıkış gücünü denetleyebilmesi.",
                   "Transmit power control (TPC): the device's ability to "
                   "control its output power to reduce interference with "
                   "other systems."),
                _w("Kaynak: BTK, Frekans Tahsisinden Muaf Telsiz Cihaz ve "
                   "Sistemlerine İlişkin Teknik Ölçütler, Madde 1 ve "
                   "Madde 18.",
                   "Source: BTK, Technical Criteria for Radio Equipment "
                   "and Systems Exempt from Frequency Assignment, "
                   "Articles 1 and 18."),
            ),
        ),
        Part(
            kind="points",
            heading=_w("Anten kazancı", "Antenna gain"),
            lines=(
                _w("Sınır yayılan güç için; anten kazancı da ona dahil. "
                   "Daha güçlü bir antenle yayın yapan cihaz gücünü o kadar "
                   "kısmak zorunda.",
                   "The limit is on radiated power, antenna gain included. "
                   "A device transmitting through a stronger antenna has "
                   "to turn its power down by as much."),
                _w("Alışta sınır yok: güçlü anten zayıf sinyali daha iyi "
                   "duyar. Her ölçüm iki yönlü olduğu için kazanç iki uçta "
                   "da gerekiyor.",
                   "There is no limit on receiving: a stronger antenna "
                   "hears a weak signal better. Every range goes both ways, "
                   "so the gain is needed at both ends."),
                _w("Güç sınırı antenin en güçlü yayın yaptığı yöne göre "
                   "uygulanıyor; başka yönlerde alıcıya daha az güç "
                   "ulaşıyor.",
                   "The power limit is applied in the direction the "
                   "antenna sends strongest; in other directions less "
                   "power reaches the receiver."),
            ),
        ),
        Part(
            kind="points",
            heading=_w("Piyasaya çıkış", "Going to market"),
            lines=(
                _w("BTK, 5 Şubat 2021'den beri piyasaya arz öncesi bildirim "
                   "başvurusu almıyor. Telsiz Ekipmanları Yönetmeliği "
                   "kapsamında ayrı bir BTK başvurusu ya da ücreti yok.",
                   "Since 5 February 2021 the BTK takes no notification "
                   "before a product is placed on the market. Under the "
                   "Radio Equipment Regulation there is no separate BTK "
                   "application or fee."),
                _w("Üretici CE işaretinden, AB uygunluk beyanından ve temel "
                   "gereklere uygunluktan sorumlu; kutuda kısa ya da uzun "
                   "uygunluk beyanı bulunmalı.",
                   "The manufacturer is responsible for the CE mark, the EU "
                   "declaration of conformity and the essential "
                   "requirements; the box carries the short or the full "
                   "declaration."),
                _w("Gereken testler: EN 300 328 (telsiz), EN 301 489-1 ve "
                   "-17 (elektromanyetik uyumluluk), EN 62368-1 (güvenlik) "
                   "ve EN 62311 (insanın elektromanyetik alana maruziyeti). "
                   "Laboratuvarlar teklifle çalışıyor. Yayımlanmış piyasa "
                   "göstergesine göre dördü birlikte vergi hariç 2500-8000 "
                   "€, bir kerelik ([LCAS v1.0, Multicert, Haziran 2026]"
                   "(https://lcas.info/)). Birim merkeze bağlandığı için "
                   "RED Madde 3(3) siber güvenlik şartı (EN 18031) da "
                   "kapsama girebilir; o kanıtın bedeli bu aralığın dışında. "
                   "UWB (Qorvo DWM3000) taşıyan tünel birimi, yaya ve araç "
                   "alıcısına EN 302 065 de gerekiyor: yaya alıcısına genel "
                   "amaçlı UWB için [-1]"
                   "(https://www.etsi.org/deliver/etsi_en/302000_302099/30206501/02.01.01_60/en_30206501v020101p.pdf), "
                   "tünel birimine konum izleme için [-2]"
                   "(https://www.etsi.org/deliver/etsi_en/302000_302099/30206502/02.01.01_60/en_30206502v020101p.pdf), "
                   "araç alıcısına taşıtlar için [-3]"
                   "(https://www.etsi.org/deliver/etsi_en/302000_302099/30206503/02.01.01_60/en_30206503v020101p.pdf). "
                   "LCAS aralığı bu testi kapsamıyor. "
                   "Türkiye'de bu testleri akredite yapan laboratuvarlar "
                   "var, örneğin [Ege Test Center]"
                   "(https://www.egetestcenter.com/akredite-red-emc-testleri/) "
                   "ve [TSE Elektroteknik Laboratuvarı]"
                   "(https://www.tse.org.tr/deney-kalibrasyon-lak-yt-onaylanmis-laboratuvar-hizmetleri/); "
                   "hiçbiri fiyat yayımlamıyor, bedel teklifle belli "
                   "olacak.",
                   "Tests needed: EN 300 328 (radio), EN 301 489-1 and -17 "
                   "(electromagnetic compatibility), EN 62368-1 (safety) "
                   "and EN 62311 (human exposure to electromagnetic "
                   "fields). Laboratories work by quotation. A published "
                   "market indication puts the four together at 2500-8000 "
                   "€ before tax, once ([LCAS v1.0, Multicert, June 2026]"
                   "(https://lcas.info/)). The unit is connected to the "
                   "centre, so the RED Article 3(3) cybersecurity "
                   "requirement (EN 18031) may apply as well; that "
                   "evidence costs extra. The tunnel unit and the "
                   "pedestrian and vehicle receivers carry UWB (Qorvo "
                   "DWM3000) and also need EN 302 065: [-1]"
                   "(https://www.etsi.org/deliver/etsi_en/302000_302099/30206501/02.01.01_60/en_30206501v020101p.pdf) "
                   "for general purpose UWB in the pedestrian receiver, [-2]"
                   "(https://www.etsi.org/deliver/etsi_en/302000_302099/30206502/02.01.01_60/en_30206502v020101p.pdf) "
                   "for location tracking in the tunnel unit and [-3]"
                   "(https://www.etsi.org/deliver/etsi_en/302000_302099/30206503/02.01.01_60/en_30206503v020101p.pdf) "
                   "for vehicles in the vehicle receiver. The LCAS range "
                   "does not cover that test. Accredited laboratories in "
                   "Türkiye run these tests, for instance [Ege Test Center]"
                   "(https://www.egetestcenter.com/akredite-red-emc-testleri/) "
                   "and the [TSE Electrotechnical Laboratory]"
                   "(https://www.tse.org.tr/deney-kalibrasyon-lak-yt-onaylanmis-laboratuvar-hizmetleri/); "
                   "none publishes a price, so the cost will come from a "
                   "quotation."),
                _w("Uyumlaştırılmış standartlar uygulanırsa Onaylanmış "
                   "Kuruluşa gitmek zorunlu değil: RED 2014/53/AB Madde "
                   "17(3), Ek II'deki iç üretim kontrolüne izin veriyor. "
                   "Bu, uygunluğun bedelsiz olduğu anlamına gelmiyor; "
                   "üretici uygunluğu teknik dosya ve ölçüm sonuçlarıyla "
                   "göstermek zorunda.",
                   "Where the harmonised standards are applied, a notified "
                   "body is not required: Article 17(3) of RED 2014/53/EU "
                   "allows internal production control under Annex II. "
                   "That does not make conformity free; the manufacturer "
                   "still has to show it with a technical file and "
                   "measurement results."),
            ),
        ),
        Part(
            kind="points",
            heading=_w("Prototip cihazları için frekans",
                       "Frequency for the prototype devices"),
            lines=(
                _w("Prototipteki Meshtastic cihazları 868 MHz ya da 915 MHz "
                   "bandında çalışıyor. 902-928 MHz bandı Türkiye'de "
                   "tahsisten muaf değil; yalnız 917,4-919,4 MHz gibi dar "
                   "alt bantlar koşullu.",
                   "The prototype's Meshtastic devices work at 868 or "
                   "915 MHz. The 902-928 MHz band is not licence-exempt in "
                   "Turkey; only narrow sub-bands such as 917,4-919,4 MHz "
                   "are, under conditions."),
                _w("863-870 MHz alt bantlarının çoğunda 25 mW e.r.p. ve "
                   "%0,1 ile %1 görev döngüsü; 869,4-869,65 MHz'de 500 mW ve "
                   "%10. Prototipler bu koşullara göre ayarlanmalı.",
                   "Most 863-870 MHz sub-bands allow 25 mW e.r.p. at a "
                   "0,1 to 1 % duty cycle; 869,4-869,65 MHz allows 500 mW "
                   "at 10 %. The prototypes should be set to these."),
            ),
        ),
        Part(
            kind="text",
            heading=_w("Kurulumun ve maliyetin dayandığı mevzuat",
                       "The rules installation and cost rest on"),
            lines=(
                _w("Buraya kadarki kurallar telsizin kendisi ve piyasaya "
                   "çıkışı içindi. Aşağıdakiler birimin nereye ve nasıl "
                   "takıldığı ile kurulum ve bakım maliyetinin hangi "
                   "kurallara dayandığı.",
                   "The rules so far were for the radio itself and for "
                   "putting it on the market. Those below are about where "
                   "and how a unit is fitted, and which rules the cost of "
                   "fitting and maintaining it rests on."),
            ),
        ),
        Part(
            kind="points", sub=True,
            heading=_w("Harcırah", "Per diem"),
            lines=(
                _w("Harcırah, görev yeri dışına geçici bir görevle "
                   "gönderilen çalışana yol gideriyle birlikte ödenen "
                   "gündeliktir (6245 sayılı Harcırah Kanunu). Kanun kamu "
                   "görevlileri için; özel sektörde işveren ödemeyi "
                   "kendisi belirler, ama vergiden istisna kısım 193 "
                   "sayılı Gelir Vergisi Kanunu'nun 24. maddesinin 2. "
                   "bendine göre aynı aylık seviyesindeki devlet "
                   "memuruna ödenen gündeliktir. Model bu yüzden kamu "
                   "cetvelini kullanıyor.",
                   "A per diem is the daily allowance paid, with the "
                   "fare, to a worker sent on a temporary duty outside "
                   "the place of duty (Travel Allowance Law 6245). The "
                   "law is for public servants; a private employer sets "
                   "its own, but the tax-exempt part is the allowance of "
                   "a civil servant on the same salary level (Income Tax "
                   "Law 193, Article 24(2)). The model uses the public "
                   "schedule for that reason."),
                _w("Ne kadar: 2026 Merkezi Yönetim Bütçe Kanunu'nun (7567) "
                   "H Cetveli, aylık/kadro derecesi 5-15 için yurt içi "
                   "gündelik 850 TL. Bir saha teknisyeninin maaşı bu "
                   "aralığa düşüyor.",
                   "How much: Schedule H of the 2026 Central Government "
                   "Budget Law (7567), grades 5-15, domestic allowance "
                   "850 TL a day. A field technician's salary falls in "
                   "this range."),
                _w("Nerede: büyükşehirlerde görev yeri, çalışanın bağlı "
                   "olduğu ilçenin belediye sınırı ve onun devamı olan "
                   "yerleşim yerleridir (Madde 3/g). Çankaya'daki bir ekip "
                   "Kızılay'a giderken görev yerinde; Polatlı'ya ya da "
                   "Kızılcahamam'a giderken görev yeri dışında. Görev yeri "
                   "içinde gündelik ödenmez (Madde 39).",
                   "Where: in a metropolitan province the place of duty "
                   "is the district the worker belongs to and the "
                   "built-up area that continues it (Article 3(g)). A "
                   "crew based in Çankaya is at its place of duty in "
                   "Kızılay and away from it in Polatlı or Kızılcahamam. "
                   "No allowance is paid inside the place of duty "
                   "(Article 39)."),
                _w("Günübirlik görevde: öğle (13.00) ya da akşam (19.00) "
                   "yemeği zamanlarından birini dışarıda geçirene "
                   "gündeliğin 1/3'ü, ikisini geçirene 2/3'ü, geceyi de "
                   "geçirene tamamı (Madde 39). Bir bakım ziyareti sabah "
                   "çıkıp öğleden sonra dönüyor: kişi başı 283,33 TL, "
                   "iki kişilik ekip için gün başına 566,67 TL. Ekip o gün "
                   "birkaç birime uğradığı için bu, ziyaretlere bölünüyor: "
                   "kırsalda günde dört direk, ziyaret başına 141,67 TL.",
                   "On a day trip: a third of the allowance for being "
                   "away over one of the lunch (13.00) or dinner (19.00) "
                   "times, two thirds for both, all of it for a night "
                   "(Article 39). A maintenance visit leaves in the "
                   "morning and is back in the afternoon: 283,33 TL a "
                   "person, 566,67 TL a day for a crew of two. The crew "
                   "calls at several units that day, so this is shared "
                   "among the visits: four poles a day in open country, "
                   "141,67 TL a visit."),
                _w("YERKON'da bugün sıfır: şehir içinde ekip kendi "
                   "ilçesinde; kırsalda ve tünelde bakımı o ilçedeki "
                   "yerel bir teknik firma yapıyor, yani kimse görev "
                   "yeri dışına çıkmıyor. Bakım Ankara merkezden "
                   "yapılsaydı ekip gününe 566,67 TL eklenirdi; kural "
                   "modelde bu yüzden duruyor.",
                   "Zero in YERKON today: in town the crew is in its own "
                   "district; in open country and the tunnel a local "
                   "firm in that district does the maintenance, so "
                   "nobody leaves the place of duty. Were it done from "
                   "central Ankara, each crew day would add 566,67 TL; "
                   "that is why the rule stays in the model."),
            ),
        ),
        Part(
            kind="points",
            sub=True,
            heading=_w("Bakım maliyetinde mevzuat",
                       "Regulation in the maintenance cost"),
            lines=(
                _w("Amortisman (GİB listesi): telsiz cihaz ve sistemleri "
                   "10 yıl (3.49.4), akümülatörler 5 yıl (3.14.7), güneş "
                   "enerjisi santrali 10 yıl (45.1.9). Yenileme kalemi her "
                   "parçayı kendi ömrüne bölüyor.",
                   "Depreciation (Revenue Administration list): radio "
                   "devices and systems 10 years (3.49.4), batteries 5 "
                   "years (3.14.7), solar power plant 10 years (45.1.9). "
                   "The replacement line divides each part by its own "
                   "life."),
            ),
        ),
        Part(
            kind="points",
            sub=True,
            heading=_w("Direk boyunu ve birimin yerini belirleyen kurallar",
                       "The rules that set pole heights and where the "
                       "unit goes"),
            lines=(
                _w("Aydınlatma direği: TEDAŞ'ın LED'li Yol Aydınlatma "
                   "Tasarımına İlişkin Usul ve Esasları (Ağustos 2022, Ek-1) "
                   "direk boyunu yol sınıfına bağlıyor: M1 sınıfı yollarda "
                   "12-14 m, M2 ve M3'te 10-12 m, M4'te 8-10 m, M5'te 8 m, "
                   "yaya yollarında (P2, P3) 6-8 m. Bu boyların "
                   "fiyatları Maliyet sayfasında.",
                   "Lighting column: TEDAŞ's rules for LED road lighting "
                   "design (August 2022, annex 1) tie the column height to "
                   "the road class: 12 to 14 m on M1 roads, 10 to 12 m on "
                   "M2 and M3, 8 to 10 m on M4, 8 m on M5, 6 to 8 m on "
                   "footways (P2, P3). What these heights cost is on the "
                   "Cost page."),
                _w("Dağıtım direği: TEDAŞ-MLZ/99-34 santrifüj betonarme "
                   "direk şartnamesi boyları 9,3 m'den 25 m'ye kadar "
                   "sayıyor (9,3-10-11 m, 12-13-14 m, 15-16 m ve üstü). "
                   "Direğin toprak altında kalan boyunu denetlemek için "
                   "tabanından 4 m yukarıya bir çizgi çekiliyor.",
                   "Distribution pole: TEDAŞ-MLZ/99-34, the specification "
                   "for spun concrete poles, lists lengths from 9,3 m to "
                   "25 m (9,3-10-11 m, 12-13-14 m, 15-16 m and up). A line "
                   "4 m above the base marks where the buried length is "
                   "checked."),
                _w("Birimle iletkenler arasındaki mesafe: Elektrik Kuvvetli "
                   "Akım Tesisleri Yönetmeliği'nin hava hattı iletkenlerinin "
                   "en küçük düşey uzaklıkları çizelgesi, iletkenlerin "
                   "haberleşme hatlarına en küçük "
                   "düşey uzaklığını alçak gerilimde 1 m, 1-36 kV orta "
                   "gerilimde 2,5 m veriyor. Birim bu yüzden orta gerilim "
                   "iletkenlerinin en az 2,5 m altına takılıyor. Aynı "
                   "çizelge orta gerilim iletkenlerinin köy ve şehir içi "
                   "yollarda yerden en az 7 m, tarlada 6 m yüksekte "
                   "olmasını istiyor.",
                   "Distance from the conductors: the table of least "
                   "vertical distances in the Regulation on Electrical "
                   "Power Installations gives the least vertical distance "
                   "from overhead "
                   "conductors to communication lines as 1 m at low "
                   "voltage and 2,5 m at 1 to 36 kV medium voltage. A unit "
                   "therefore goes at least 2,5 m below medium-voltage "
                   "conductors. The same table wants medium-voltage "
                   "conductors at least 7 m above village and town roads "
                   "and 6 m above fields."),
            ),
        ),
        Part(
            kind="points",
            sub=True,
            heading=_w("Kamu yapısında yer kullanımı",
                       "Using space on public structures"),
            lines=(
                _w("3194 sayılı İmar Kanunu, Ek Madde 9/7: kamu kurumları "
                   "elektronik haberleşme istasyonlarına yer "
                   "kullandırırken alacakları yıllık bedel, büyükşehirde "
                   "Ulaştırma ve Altyapı Bakanlığının yer seçim belgesi "
                   "ücretinin beş katını, diğer yerlerde üç katını geçemez. "
                   "2025 yer seçim ücreti 27503,44 TL; üst sınır "
                   "büyükşehirde yılda 137517,20 TL, diğer yerlerde "
                   "82510,32 TL (Tarım ve Orman Bakanlığı, 2025 rayiç "
                   "bedelleri). İstanbul Büyükşehir Belediyesi'nin tarifesi "
                   "bu kuralla kuruluyor. YERKON birimleri kamu protokolüyle "
                   "konduğu için modelde dağıtım direği kirası sıfır.",
                   "Zoning Law 3194, Additional Article 9(7): the yearly "
                   "fee a public body charges an electronic communications "
                   "station for space may not exceed five times the "
                   "Ministry of Transport's site selection fee in a "
                   "metropolitan municipality and three times elsewhere. "
                   "The 2025 site selection fee is 27503,44 TL, so the cap "
                   "is 137517,20 TL a year in a metropolitan municipality "
                   "and 82510,32 TL elsewhere (Ministry of Agriculture and "
                   "Forestry, 2025 rates). Istanbul's municipal tariff is "
                   "built on this rule. YERKON units go up under a public "
                   "agreement, so the model charges no pole rent."),
                _w("Genel Aydınlatma Yönetmeliği: aydınlatma tesisinin "
                   "bağlantı noktasından genel aydınlatma dışında bir "
                   "amaca enerji verilmez; aydınlatma tesisleri TEDAŞ'ın "
                   "mülkiyetinde. Birim bu yüzden ayrı sayaçlı bir abone "
                   "sayılıyor ve ticarethane tarifesinden ödüyor.",
                   "General Lighting Regulation: no energy may be taken "
                   "from a public lighting connection for anything but "
                   "public lighting, and the lighting installations belong "
                   "to TEDAŞ. A unit is therefore a separately metered "
                   "subscriber and pays the commercial tariff."),
            ),
        ),
        Part(
            kind="points",
            sub=True,
            heading=_w("Harita ve uydu görüntüsü", "Maps and imagery"),
            lines=(
                _w("Yer seçme haritası OpenStreetMap'in karolarını kullanıyor "
                   "ve onu anıyor. Uydu görüntüsü Esri World Imagery; atfı: "
                   "Esri, Maxar, Earthstar Geographics, GIS User Community. "
                   "Görüntü yalnız zemini boyuyor, hesaba girmiyor.",
                   "The place picker uses OpenStreetMap's tiles and credits "
                   "it. The imagery is Esri World Imagery, credited to "
                   "Esri, Maxar, Earthstar Geographics and the GIS User "
                   "Community. It paints the ground and enters no "
                   "calculation."),
            ),
        ),
        Part(
            kind="links",
            heading=_w("Resmî kaynaklar", "Official sources"),
            links=(
                Link(label=_w("ETSI EN 300 328 V2.2.2 (2019-07)",
                              "ETSI EN 300 328 V2.2.2 (2019-07)"),
                     url="https://www.etsi.org/deliver/etsi_en/300300_300399/300328/02.02.02_60/en_300328v020202p.pdf"),
                Link(label=_w("BTK: Sınıf 2 bildirim uygulamasına son verildi",
                              "BTK: the Class 2 notification has ended"),
                     url="https://btk.gov.tr/sinif-2-bildirim-formu-ile-bilgi-teknolojileri-ve-iletisim-kurumuna-basvuruda-bulunulmasi-uygulamasina-son-verilmistir"),
                Link(label=_w("ETSI EN 302 065-3 V2.1.1 (2016-11), taşıtlarda UWB",
                              "ETSI EN 302 065-3 V2.1.1 (2016-11), UWB in vehicles"),
                     url="https://www.etsi.org/deliver/etsi_en/302000_302099/30206503/02.01.01_60/en_30206503v020101p.pdf"),
                Link(label=_w("RED 2014/53/AB (EUR-Lex)",
                              "RED 2014/53/EU (EUR-Lex)"),
                     url="https://eur-lex.europa.eu/eli/dir/2014/53/oj"),
                Link(label=_w("BTK: piyasa gözetimi, sıkça sorulan sorular",
                              "BTK: market surveillance, frequently asked questions"),
                     url="https://www.btk.gov.tr/piyasa-gozetimi-ve-denetimi-sikca-sorulan-sorular"),
                Link(label=_w("BTK: frekans tahsisinden muaf telsiz cihazların teknik ölçütleri",
                              "BTK: technical criteria for licence-exempt radio devices"),
                     url="https://www.btk.gov.tr/uploads/pages/frekans-tahsisinden-muaf-telsiz-cihaz-sistemleri-olcutler-633d4ca68c0b1.pdf"),
                Link(label=_w("6245 sayılı Harcırah Kanunu (Madde 3/g ve 39)",
                              "Travel Allowance Law 6245 (Articles 3(g) and 39)"),
                     url="https://www.mevzuat.gov.tr/mevzuatmetin/1.3.6245.pdf"),
                Link(label=_w("193 sayılı Gelir Vergisi Kanunu (Madde 24)",
                              "Income Tax Law 193 (Article 24)"),
                     url="https://www.mevzuat.gov.tr/mevzuatmetin/1.4.193.pdf"),
                Link(label=_w("SBB: 2026 H Cetveli", "SBB: 2026 Schedule H"),
                     url="https://www.sbb.gov.tr/wp-content/uploads/2025/12/8-H-Cetveli_2026Butcesi.pdf"),
                Link(label=_w("Elektrik Kuvvetli Akım Tesisleri Yönetmeliği",
                              "Regulation on Electrical Power Installations"),
                     url="https://www.mevzuat.gov.tr/mevzuat?MevzuatNo=9949&MevzuatTur=7&MevzuatTertip=5"),
                Link(label=_w("TEDAŞ: LED'li yol aydınlatma tasarımına ilişkin usul ve esaslar (Ağustos 2022)",
                              "TEDAŞ: rules for LED road lighting design (August 2022)"),
                     url="https://www.tedas.gov.tr/FileUpload/MediaFolder/c09a508b-c5f8-4b60-bb0c-e907e7438670.pdf"),
                Link(label=_w("TEDAŞ-MLZ/99-34: santrifüj betonarme direk teknik şartnamesi",
                              "TEDAŞ-MLZ/99-34: spun concrete pole specification"),
                     url="https://www.tedas.gov.tr/FileUpload/MediaFolder/8aef4429-1647-4a50-9a9e-a44250bc486f.pdf"),
                Link(label=_w("Tarım ve Orman Bakanlığı: 2025 baz istasyonu yıllık kira rayiç bedelleri (3194 Ek 9/7)",
                              "Ministry of Agriculture and Forestry: 2025 base station rent rates (Law 3194, Additional Article 9(7))"),
                     url="https://www.tarimorman.gov.tr/DKMP/Belgeler/KORUNAN%20ALANLAR%20%C3%9CCRET%20TAR%C4%B0FES%C4%B0/2025/Ek-11%20Baz%20ve%20Radyo%20Verici%20%C4%B0stasyonlar%C4%B1%20Y%C4%B1ll%C4%B1k%20Kira%20Rayi%C3%A7%20Bedeli-2025-1.pdf"),
                Link(label=_w("Genel Aydınlatma Yönetmeliği", "General Lighting Regulation"),
                     url="https://www.mevzuat.gov.tr/File/GeneratePdf?mevzuatNo=18646&mevzuatTur=KurumVeKurulusYonetmeligi&mevzuatTertip=5"),
                Link(label=_w("GİB: amortisman oranları tablosu",
                              "Revenue Administration: depreciation rates"),
                     url="https://cdn.gib.gov.tr/api/gibportal-file/file/getFileResources?objectKey=arsiv/yardim-kaynaklar/yararli-bilgiler/AmortismanOranlariTablosu.pdf"),
            ),
        ),
    ),
)

#: Every page, in the order the navigation shows them.
PAGES = (HOME, WHY, SYSTEM, RESEARCH, VALUE, RESULTS, COST, LAW,
         SIMULATION, SOURCES)

#: Where the running simulator lives, and what the link to it is
#: called. Not the same thing as the SIMULATION page: that page says
#: what the simulation models and what it leaves out, and this address
#: is the thing itself. They had the same name once, and a reader had
#: no way to tell which one a link meant (ADR-0071). The address has to
#: differ from every page's slug or the page becomes unreachable, and a
#: test holds that.
SIMULATOR = "/calistir"
SIMULATOR_LABEL = _w("Simülasyonu çalıştır", "Run the simulation")

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
    "{run_on} tarihinde {source} okunarak koşuldu. Gölgeleme {draws} kez "
    "çekildi, arazi {spacing} metrede bir okundu. İlk üç sütun rapora "
    "giren adlardır, o yüzden çevrilmiyor.",
    "Run on {run_on} against {source}. The shadows were drawn {draws} "
    "times and the ground profile was read every {spacing} m. The first "
    "three columns are the names that go into the Turkish report, so they "
    "are not translated.",
)

FOOTER = _w(
    "YERKON, Ulaştırma ve Altyapı Bakanlığı UDHAM fikir yarışmasına "
    "sunulan bir proje. İstenilen yerde istenilen doğruluk.",
    "YERKON is a project submitted to the UDHAM idea competition of the "
    "Ministry of Transport and Infrastructure. The accuracy wanted, where "
    "it is wanted.",
)

WEIGHTING = _w(
    "Simülasyonun doldurduğu üç satır. Her biri, hataların yüzde "
    "95'inin altında kaldığı yatay sapmayı gösteriyor ve her biri "
    "Ankara'nın gerçek arazisi üzerinde koşuldu.",
    "The three rows the simulation filled. Each shows the horizontal "
    "error that 95 per cent of the measurements stayed under, and each was "
    "run over real ground near Ankara.",
)

NO_RUN = _w(
    "Yayımlanmış bir koşu yok. Önce `yerkon table --publish` çalıştırın.",
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
    level = 'h3 class="sub"' if part.sub else "h2"
    heading = (
        "<{0}>{1}</{2}>".format(level, _said(part.heading, language),
                                level.split()[0])
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
        # The size is given so the page does not jump when the picture
        # arrives, and a picture below the fold waits until it is near.
        wide, high = PICTURE_SIZES.get(part.picture, (0, 0))
        size = ' width="{}" height="{}"'.format(wide, high) if wide else ""
        drawn = '<figure><img src="{}"{} loading="lazy" decoding="async" ' \
            'alt="{}"><figcaption>{}</figcaption></figure>'.format(
                html.escape(where.asset(part.picture), quote=True),
                size,
                html.escape(part.lines[0].said(language), quote=True),
                _said(part.lines[0], language),
            )
    elif part.kind == "shows" and part.shows == "bibliography":
        drawn = "".join(
            "<h3>{}</h3><ul>{}</ul>".format(
                html.escape(group.said(language)),
                "".join(
                    '<li><a href="{}">{}</a></li>'.format(
                        html.escape(entry.url, quote=True),
                        html.escape(entry.said(language)),
                    )
                    for entry in group.entries
                ),
            )
            for group in sources.read().groups
        )
    elif part.kind == "shows" and part.shows == "headline":
        drawn = _headline(published, language)
    elif part.kind == "shows" and part.shows == "published":
        drawn = _published(published, language)
    elif part.kind == "shows" and part.shows == "landscape":
        drawn = _landscape(published, language)
    elif part.kind == "shows" and part.shows == "accuracy":
        drawn = _accuracy(published, language)
    elif part.kind == "shows" and part.shows == "cost":
        drawn = _cost(published, language)
    elif part.kind == "shows" and part.shows == "spread":
        drawn = _spread(published, language)
    elif part.kind == "shows" and part.shows == "clocks":
        drawn = _clocks(language)
    elif part.kind == "shows" and part.shows == "when":
        drawn = _when(language)
    elif part.kind == "shows" and part.shows == "structures":
        drawn = costing.structures(language, _table)
    elif part.kind == "shows" and part.shows == "units":
        drawn = costing.units(published, language, _table)
    elif part.kind == "shows" and part.shows == "cost-rows":
        drawn = (costing.rows(published, language, _table)
                 if published is not None
                 else '<p class="warn">{}</p>'.format(_said(NO_RUN, language)))
    elif part.kind == "shows" and part.shows == "bill":
        drawn = costing.summary(language, _table)
    elif part.kind == "shows" and part.shows == "parts":
        drawn = costing.parts(language, _table)
    elif part.kind == "shows" and part.shows == "assumptions":
        drawn = costing.assumptions(language, _table)
    else:
        raise ValueError("no way to draw a {} part".format(part.kind))
    if part.folded and heading:
        return '<section><details class="fold"><summary>{}</summary>{}' \
            "</details></section>".format(heading, drawn)
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


#: What each drawing is about, and the caveat under it.
LANDSCAPE = _w(
    "Ne kadara ne kadar doğruluk",
    "What the accuracy costs",
)
LANDSCAPE_UNDER = _w(
    "Yatayda kilometrekare başına kurulum maliyeti, dikeyde yatay hata. "
    "İki eksen de sıfırdan başlıyor. Sola ve aşağıya doğru daha iyi: ucuz ve "
    "hassas. Uydu sistemlerinin paydası dünyanın bütün kara yüzeyi, "
    "YERKON'unki satırın kendi alanı. YERKON'un kırsal satırı uydu "
    "sistemlerinden ucuz, şehir içi satırı pahalı: şehirde binalar "
    "sinyali kestiği için kilometrekareye daha çok birim gerekiyor. İkisi "
    "de uydularla aynı doğruluk kuşağında. Oklu işaret, kaynağın \"en "
    "fazla şu kadar\" dediği bir değer; gerçek değer okun gösterdiği "
    "yönde. Tünel satırı burada yok: o "
    "kilometreye bölünüyor, yani aynı eksene konamaz. Hem maliyetini "
    "hem doğruluğunu yayımlamayan sistem de çizilemedi.",
    "Capital per square kilometre across, horizontal error up, both "
    "from nought. Left and down is better: cheap and precise. The "
    "satellite systems are divided by all the land on earth, YERKON by "
    "each row's own area. YERKON's rural row costs less than the "
    "satellite systems and its town row more: in town buildings cut the "
    "signal, so a square kilometre needs more units. Both sit in the "
    "satellites' band of accuracy. A mark with an "
    "arrow is a value the source gave as \"at most this\"; the true "
    "value lies the way the arrow points. The tunnel row is absent: "
    "it is divided by route kilometre and does not belong on this axis. "
    "A system that publishes only one of the two cannot be drawn "
    "either.",
)
#: The four events the problem page describes, on a line. The year is
#: the fractional one the event happened in, so April 2024 sits a third
#: of the way through its year rather than on its first day.
WHEN = (
    (2017.9, _w("Karadeniz", "The Black Sea"),
     _w("20+ gemi, 40 km sapma", "20+ ships, 40 km out")),
    (2019.0, _w("Norveç", "Norway"),
     _w("Finnmark, süregelen", "Finnmark, still going")),
    (2024.3, _w("Baltık", "The Baltic"),
     _w("Tartu bir ay kapalı", "Tartu shut for a month")),
    (2026.4, _w("ABD", "United States"),
     _w("ambulans uçağı düştü", "air ambulance down")),
)
WHEN_TITLE = _w("Dört olay, dokuz yıl", "Four events, nine years")
WHEN_UNDER = _w(
    "Yukarıdaki dört olay zaman içinde. Hiçbiri tarihi bir merak değil: "
    "en eskisi 2017, en yenisi bu yıl ve aradaki boşluklar kapanıyor.",
    "The four events above, in time. None of them is a historical "
    "curiosity: the oldest is 2017, the newest is this year, and the "
    "gaps between them are closing.",
)
CLOCKS = (
    ("~266400 TL", _w("birim başına atomik saat, TDoA",
                       "an atomic clock per unit, TDoA")),
    ("0 TL", _w("saat senkronizasyonu, YERKON (çift yönlü ölçüm)",
                "clock synchronisation, YERKON (two way ranging)")),
)
CLOCKS_UNDER = _w(
    "TDoA'da birimlerin saatlerini birbirine eşitlemek, birim başına "
    "atomik saat ve IEEE 1588 PTP gibi pahalı bir altyapı istiyor. "
    "YERKON mesafeyi çift yönlü ölçtüğü için bu senkronizasyona hiç "
    "gerek duymuyor.",
    "In TDoA, keeping the units' clocks equal to each other takes costly "
    "infrastructure such as an atomic clock and IEEE 1588 PTP at every "
    "unit. YERKON measures range two ways, so it needs no such "
    "synchronisation at all.",
)
SPREAD = _w("Üç satırın hatası: ortancadan en kötü %5'e",
            "Each row's error, median to ninety fifth")
SPREAD_UNDER = _w(
    "Dolu nokta hataların yüzde 95'inin altında kaldığı değer, boş nokta "
    "ortancası; aradaki çizgi ne kadar dağıldıklarını gösteriyor. "
    "Baklava, aynı konumun düşey hatası. Yol kenarına dizilmiş "
    "birimlerin hepsi aşağı yukarı aynı yükseklikte, o yüzden yüksekliği "
    "mesafelerden ölçecek geometri yok; düşeyi haritadan gelen yükseklik "
    "taşıyor.",
    "The filled dot is the value 95 % of the errors stay under, the "
    "hollow one the median; the line between them is how far they "
    "spread. The diamond is the same position's vertical error. Units strung "
    "along a roadside are all at much the same height, so there is no "
    "geometry to measure height from ranges; the height from the map "
    "carries the vertical.",
)
COST = _w("Kilometrekare başına kurulum maliyeti",
          "Capital per square kilometre")
COST_UNDER = _w(
    "Kurulum maliyetini yayımlayan sistemler. Uydu satırlarının paydası "
    "dünyanın bütün kara yüzeyi, YERKON satırlarınınki kendi alanı. "
    "Tünel "
    "satırı burada yok: o kilometrekareye değil güzergâh kilometresine "
    "bölünüyor, yani aynı eksene konamaz. Tablodaki dipnotu bunu "
    "anlatıyor.",
    "The systems that publish a capital cost. The satellite rows are "
    "divided by all the land on earth, the YERKON rows by their own "
    "area. The tunnel row is absent: it is divided by "
    "route kilometre rather than by square kilometre, so it does not "
    "belong on this axis. Its note in the table says so.",
)
ACCURACY = _w("Yatay hata, en kötü %5 hariç (HPE P95)",
              "Horizontal error, worst 5 % excluded (HPE P95)")
ACCURACY_UNDER = _w(
    "Sola doğru daha iyi. Oklu işaret, kaynağın \"en fazla şu kadar\" "
    "dediği bir değer; gerçek değer okun gösterdiği yönde. İki değer "
    "verilmişse (ortalama ve en kötü konum) nokta ortalamada duruyor, "
    "ince çizgi en kötü konuma kadar uzanıyor. Eksen logaritmik, çünkü "
    "değerler santimetreden on beş metreye uzanıyor. Hücresi boş olan "
    "sistem çizilmedi.",
    "Further left is better. A mark with an arrow is a value the source "
    "gave as \"at most this\"; the true value lies the way the arrow "
    "points. Where two figures are given, an average and a worst "
    "place, the dot sits on the average and a thin line runs to the "
    "worst. The axis is logarithmic because the figures run from "
    "centimetres to fifteen metres. A system with an empty cell is not "
    "drawn.",
)


def _marks(published, language: str, at: int):
    """Every system's figure for one column, ours among the others."""
    from yerkon import comparison
    from yerkon.viewer.charts import Mark, figure_in, second_in

    table = comparison.read()
    out = []
    for row in table.rows:
        cell = comparison.without_markers(row.cells[at])
        figure = figure_in(cell)
        if figure is not None:
            out.append(Mark(label=row.system, figure=figure,
                            shown=figure.text,
                            short=row.system.split()[0],
                            second=second_in(cell)))
    for row in published.rows:
        cells = list(row.cells())
        # The two cost columns. A row priced by its length is not on
        # the same axis as one priced by its area, so it is left out of
        # a drawing of them rather than plotted as though it were
        # (ADR-0073).
        if at in (5, 6) and row.costed_by != "area":
            continue
        figure = figure_in(cells[at + 3])
        if figure is not None:
            out.append(Mark(
                label=cells[0], figure=figure, ours=True,
                shown=cells[at + 3].strip(),
                short=cells[0].replace("YERKON ", "").strip("()"),
            ))
    return out


def _figure(drawn: str, under, language: str, narrow: str = "") -> str:
    """One drawing and what it says, with a phone sized twin.

    A chart drawn for a laptop and then scrolled on a phone opens on
    its label column with no data in view, which is worse than a table
    doing the same: a table's first columns still say something. So the
    narrow one is drawn again at a phone's width, with shorter names,
    and the stylesheet shows whichever fits.
    """
    if not drawn:
        return ""
    body = drawn if not narrow else (
        '<div class="only-wide">{}</div><div class="only-narrow">{}</div>'
        .format(drawn, narrow)
    )
    return '<figure class="chart">{}<figcaption>{}</figcaption></figure>' \
        .format(body, _said(under, language))


def _accuracy(published, language: str) -> str:
    """HPE P95 across the table, ours lit."""
    if published is None:
        return ""
    from yerkon.viewer import charts

    marks = _marks(published, language, 1)
    return _figure(
        charts.bars(marks, title=ACCURACY.said(language), unit="m"),
        ACCURACY_UNDER, language,
        narrow=charts.bars(marks, title=ACCURACY.said(language), unit="m",
                           width=344.0, label_width=96.0, narrow=True),
    )


def _landscape(published, language: str) -> str:
    """Coverage against error: the trade the whole table is about."""
    if published is None:
        return ""
    from yerkon.viewer import charts

    errors = {mark.label: mark for mark in _marks(published, language, 1)}
    costs = {mark.label: mark.figure
             for mark in _marks(published, language, 5)}
    points = [(errors[name], costs[name]) for name in errors
              if name in costs]
    return _figure(
        charts.scatter(
            points, title=LANDSCAPE.said(language),
            across_title="TL/km²", up_title="HPE P95 [m]",
            logarithmic=False,
        ),
        LANDSCAPE_UNDER, language,
        narrow=charts.scatter(
            points, title=LANDSCAPE.said(language),
            across_title="TL/km²", up_title="HPE P95 [m]",
            width=344.0, height=430.0, narrow=True, logarithmic=False,
        ),
    )


def _when(language: str) -> str:
    """The four incidents on one line."""
    from yerkon.viewer import charts

    return _figure(
        charts.timeline(
            [(year, where.said(language), what.said(language))
             for year, where, what in WHEN],
            title=WHEN_TITLE.said(language),
        ),
        WHEN_UNDER, language,
    )


def _clocks(language: str) -> str:
    """Two numbers, side by side: what synchronising the units' clocks
    costs a TDoA system, and what it costs YERKON."""
    figures = "".join(
        '<div class="figure"><b>{}</b><span>{}</span></div>'.format(
            html.escape(value), _said(label, language))
        for value, label in CLOCKS
    )
    return ('<div class="figures">{}</div>'
            '<p class="under">{}</p>').format(
        figures, _said(CLOCKS_UNDER, language))


def _spread(published, language: str) -> str:
    """Our three rows, median to ninety fifth, with the vertical beside."""
    if published is None:
        return ""
    from yerkon.viewer import charts

    rows = []
    for row in published.rows:
        cells = list(row.cells())
        rows.append((
            cells[0].replace("YERKON ", "").strip("()"),
            charts.figure_in(cells[3]),
            charts.figure_in(cells[4]),
            charts.figure_in(cells[5]),
        ))
    return _figure(
        charts.spread(rows, title=SPREAD.said(language), unit="m"),
        SPREAD_UNDER, language,
        narrow=charts.spread(rows, title=SPREAD.said(language), unit="m",
                             width=344.0, label_width=76.0, narrow=True),
    )


def _cost(published, language: str) -> str:
    """The capital column, for the six systems that publish one."""
    if published is None:
        return ""
    from yerkon.viewer import charts

    marks = _marks(published, language, 5)
    return _figure(
        charts.bars(marks, title=COST.said(language), unit="TL/km²",
                    label_width=160.0, logarithmic=False),
        COST_UNDER, language,
        narrow=charts.bars(marks, title=COST.said(language), unit="TL/km²",
                           width=344.0, label_width=96.0, narrow=True,
                           logarithmic=False),
    )


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
        # The same note says what the running cost is made of.
        rest[6] += mark(table.yerkon["capex"])
        # A row priced by its length says so on both cost cells: the
        # column head says TL/km² and for this one row it is not.
        if row.costed_by == "route":
            note = mark(table.yerkon["by_route"])
            rest[5] += note
            rest[6] += note
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
    bibliography = sources.read()
    listed = "".join(
        '<li id="note{0}">{1}{2} <a class="back" href="#back{0}">↑</a></li>'
        .format(at, _marked(table.said(key, language)),
                _cited(table.notes[key].get("sources", ()), bibliography,
                       language))
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


def _cited(keys, bibliography, language: str) -> str:
    """The bibliography entries a note rests on, as links."""
    if not keys:
        return ""
    return ' <span class="cited">{}</span>'.format(" · ".join(
        '<a href="{}">{}</a>'.format(
            html.escape(bibliography.entry(key).url, quote=True),
            html.escape(bibliography.entry(key).said(language)),
        )
        for key in keys
    ))


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
CARRIED = ("site.css", "theme.js", "road.webp", "gnss.webp",
           "architecture.webp", "simulator.webp")

#: Each picture's pixel size. WebP rather than PNG: the four came to
#: 1,5 MB as PNG and 216 KB as WebP at quality 85, with the lettering in
#: the diagrams still sharp.
PICTURE_SIZES = {
    "road.webp": (1200, 900),
    "gnss.webp": (700, 701),
    "architecture.webp": (1200, 800),
    "simulator.webp": (1600, 1000),
}

STATIC = pathlib.Path(__file__).parent / "static"


#: The simulator's page on the published site, and what it needs beside it.
BROWSER_SIMULATOR = "calistir.html"
BROWSER_SCRIPTS = ("app.js", "draw.js", "words.js", "map.js", "style.css",
                   "local.js", "sim-worker.js")
#: What of the package the browser does not need: caches, the fetch
#: cache of raw elevation tiles, and the files the server sends.
LEFT_OUT = ("__pycache__", "_tiles", "static")

#: A place the simulator fetched is saved under this prefix. It belongs to
#: whoever fetched it, so it stays out of the published package.
FETCHED = "yer-"


def _loose(text: str, swaps) -> str:
    """Absolute addresses made relative, refusing any that has moved.

    The published site sits under a path of its own, so "/app.js" would
    be looked for at the root of somebody else's domain. A swap whose
    source is not there any more fails here rather than as a blank page.
    """
    for before, after in swaps:
        if before not in text:
            raise ValueError("the simulator no longer says {!r}".format(before))
        text = text.replace(before, after)
    return text


def browser_simulator() -> dict:
    """The simulator's files for a folder served by nothing, by name."""
    page = _loose((STATIC / "simulator.html").read_text(encoding="utf-8"), (
        ('href="/style.css"', 'href="style.css"'),
        ('<a id="back" href="/"', '<a id="back" href="index.html"'),
        ('href="/api/figures.toml"', 'href="api/figures.toml"'),
        ('<script type="module" src="/app.js"></script>',
         '<script src="local.js"></script>\n'
         '<script type="module" src="app.js"></script>'),
    ))
    # One tag from everything the page loads, put on every address it
    # loads them by. GitHub Pages lets a browser keep a file ten minutes,
    # so a fix went out and a visitor went on running the old drawing
    # code beside the new page; a changed file now has a new address.
    archive = package_zip()
    digest = hashlib.sha256(archive)
    for name in BROWSER_SCRIPTS:
        digest.update((STATIC / name).read_bytes())
    tag = "?v=" + digest.hexdigest()[:10]
    page = _loose(page, (
        ('href="style.css"', 'href="style.css{}"'.format(tag)),
        ('<script src="local.js">', '<script src="local.js{}">'.format(tag)),
        ('src="app.js"', 'src="app.js{}"'.format(tag)),
    ))
    files = {BROWSER_SIMULATOR: page.encode("utf-8")}
    for name in BROWSER_SCRIPTS:
        body = (STATIC / name).read_bytes()
        if name == "app.js":
            body = _loose(body.decode("utf-8"), (
                ('from "/words.js"', 'from "./words.js{}"'.format(tag)),
                ('from "/draw.js"', 'from "./draw.js{}"'.format(tag)),
                ('from "/map.js"', 'from "./map.js{}"'.format(tag)),
            )).encode("utf-8")
        elif name == "local.js":
            body = _loose(body.decode("utf-8"), (
                ('new Worker("sim-worker.js"',
                 'new Worker("sim-worker.js{}"'.format(tag)),
            )).encode("utf-8")
        elif name == "sim-worker.js":
            body = _loose(body.decode("utf-8"), (
                ('fetch("yerkon.zip")', 'fetch("yerkon.zip{}")'.format(tag)),
            )).encode("utf-8")
        files[name] = body
    files["yerkon.zip"] = archive
    return files


def package_zip() -> bytes:
    """This package as one archive the browser unpacks and imports.

    Written the same way every time: sorted, with one fixed date, so the
    folder in the repository only changes when the package does.
    """
    import io
    import zipfile

    root = pathlib.Path(__file__).resolve().parent.parent
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(root.rglob("*")):
            relative = path.relative_to(root)
            if path.is_dir() or any(part in LEFT_OUT or part.startswith(FETCHED)
                                    for part in relative.parts):
                continue
            if path.suffix == ".pyc":
                continue
            info = zipfile.ZipInfo(
                "yerkon/" + relative.as_posix(), date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            archive.writestr(info, path.read_bytes())
    return buffer.getvalue()


def write_pages(into, published=None) -> tuple:
    """Draw the whole site into a folder, both languages.

    For somewhere that serves files and runs nothing, GitHub Pages being
    the one this was written for. The simulator comes too, and runs in
    the visitor's browser rather than on the server (ADR-0080).

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
    # The simulator itself, running in the visitor's browser (ADR-0080).
    for name, body in browser_simulator().items():
        path = into / name
        path.write_bytes(body)
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
    # [what it is](where it is). Only http and https: a phrase is data
    # as far as this function is concerned, and javascript: in a link is
    # the one thing that turns data into behaviour.
    # The whole text went through html.escape above, so the address the
    # regex hands back is already safe to sit in an attribute. Escaping
    # it again would turn & into &amp;amp; and break the address.
    out = re.sub(
        r"\[([^\]]+)\]\((https?://[^)\s]+)\)",
        r'<a href="\2">\1</a>',
        out,
    )
    return out
