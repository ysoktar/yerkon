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
import json
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
    #: Parts shown one card each in a strip that slides: (key in
    #: bom.toml or PILOT_ITEMS, photo file under photos/ or "" while
    #: there is none).
    slides: tuple[tuple[str, str], ...] = ()
    #: For a list of where the project stands: "done" or "todo" for each
    #: line, drawn green or yellow. Empty for every other list.
    states: tuple[str, ...] = ()


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
    #: The English page's address, in English. Empty means the same as
    #: `slug`.
    slug_en: str = ""

    def slug_in(self, code: str) -> str:
        """The page's address in a language: the English pages are named
        in English, the Turkish ones in Turkish."""
        return (self.slug_en or self.slug) if code == "en" else self.slug


def _w(tr: str, en: str) -> Words:
    return Words(tr=tr, en=en)


@dataclass(frozen=True)
class Where:
    """How one page names another.

    A server answers `/sorun` and a folder of files answers
    `tr/sorun/`, and that is the only thing the two disagree about.
    Keeping it in one object means the pages are written once and the
    static export is not a second copy of them (ADR-0065).

    In the folder each language has its own folder and each page a
    folder of its own inside it, so an address never ends in ".html":
    `tr/` is the Turkish front page, `tr/sistem/` a page, `en/system/`
    its English (ADR-0112). Links are relative, so the folder works at
    the domain's root and under a path of its own alike.
    """

    #: The language of the page doing the naming.
    language: str = "tr"
    #: A folder of files rather than a running server.
    loose: bool = False
    #: The page doing the naming: how deep it sits decides the way up.
    at: Optional["Page"] = None

    def _up(self) -> str:
        # `tr/` is one folder below the root, `tr/sistem/` two.
        return "../" if self.at is None or not self.at.slug else "../../"

    def page(self, page: "Page") -> str:
        if not self.loose:
            return "/" + page.slug
        return self._up() + self.folder(page, self.language)

    def tongue(self, page: "Page", code: str) -> str:
        if not self.loose:
            return "/{}?dil={}".format(page.slug, code)
        return self._up() + self.folder(page, code)

    def asset(self, name: str) -> str:
        if not self.loose:
            return "/" + name
        return self._up() + name

    def simulator(self) -> str:
        # Served, this is the running simulator. Loose, it is the same
        # simulator running in the visitor's browser (ADR-0080).
        if not self.loose:
            return SIMULATOR
        return self._up() + BROWSER_SIMULATOR + (
            "?dil=en" if self.language == "en" else "")

    @staticmethod
    def folder(page: "Page", code: str) -> str:
        slug = page.slug_in(code)
        return code + "/" + (slug + "/" if slug else "")

    @staticmethod
    def file(page: "Page", code: str) -> str:
        return Where.folder(page, code) + "index.html"


# --- what the site says ---------------------------------------------------

HOME = Page(
    slug="",
    nav=_w("Anasayfa", "Home"),
    title=_w("YERKON", "YERKON"),
    lead=_w(
        "YERKON, karayolu ulaşımı için uydudan bağımsız, yer "
        "tabanlı bir konumlandırma katmanıdır. GNSS sinyali "
        "kesildiğinde konum bilgisini sağlamakta, GNSS çalışırken "
        "ise uydunun verdiği konumu doğrulamaktadır. Yol kenarında "
        "hâlihazırda bulunan direk ve kabinlere düşük maliyetli "
        "yayın birimleri yerleştirilmekte; araçtaki alıcı, bu "
        "birimlere olan uzaklığını ölçerek kendi konumunu "
        "hesaplamaktadır.",
        "YERKON is a ground-based positioning layer for roads that does "
        "not depend on satellites: when GNSS is lost it gives the "
        "position, and while GNSS works it checks the position GNSS "
        "gives. Low cost broadcast units go onto masts and "
        "cabinets already standing by the road, and the receiver in a "
        "vehicle works out its own position by measuring its distance to "
        "them.",
    ),
    parts=(
        Part(
            kind="text",
            lines=(_w(
                "Proje dokümanı: [YERKON raporu (PDF, 20 sayfa)]"
                "(https://yerkon.com/yerkon-rapor.pdf)",
                "Project document, in Turkish: [YERKON report "
                "(PDF, 20 pages)](https://yerkon.com/yerkon-rapor.pdf)",
            ),),
        ),
        Part(
            kind="picture",
            picture="road.webp",
            lines=(_w(
                "Yayın birimleri yol kenarındaki direk ve kabinlere "
                "yerleştirilmektedir. Alıcı, uydu sistemlerini ve yer "
                "tabanlı birimleri her zaman birlikte kullanmaktadır. Uydu "
                "sinyali mevcutken iki konumun karşılaştırılması, "
                "karıştırma (jamming) ve aldatma (spoofing) girişimlerinin "
                "tespit edilmesini sağlamaktadır; uydu sinyali kesildiğinde"
                " ise konum yer tabanlı birimler üzerinden "
                "hesaplanmaktadır.",
                "The broadcast units sit on roadside masts and cabinets. "
                "The receiver always uses the satellites and the ground "
                "units together: while the satellites work, comparing the "
                "two positions helps catch jamming and spoofing; when the "
                "satellite signal is lost, the position comes from the "
                "ground units.",
            ),),
        ),
        Part(kind="shows", shows="headline"),
        Part(
            kind="text",
            heading=_w("Önerilen sistem", "What it proposes"),
            lines=(
                _w(
                    "Ulaştırma ve Altyapı Bakanlığı'nın elektrik ve haberleşme "
                    "hattına bağlı noktaları hâlihazırda mevcuttur: akıllı "
                    "ulaşım sistemi (AUS) kabinleri, yol kenarı üniteleri, "
                    "trafik ışıkları, tünel aydınlatma sistemleri ve ücretli "
                    "yol gişeleri. YERKON, bu noktalara düşük maliyetli bir "
                    "radyo yayın birimi eklemeyi önermektedir. Yayın birimi, "
                    "kendi kimliğini ve kurulum sırasında ölçülmüş konumunu "
                    "yayınlamaktadır. Bu noktaların seyrek kaldığı bölgelerde "
                    "yol boyundaki diğer direklerden yararlanılmaktadır; "
                    "simülasyonda şehir içinde aydınlatma direkleri, kırsalda "
                    "ise çoğunlukla elektrik dağıtım direkleri kullanılmıştır.",
                    "The Ministry of Transport and Infrastructure already "
                    "has points on the power and communications network: "
                    "intelligent transport cabinets, roadside units, "
                    "traffic lights, tunnel lighting and toll gates. "
                    "YERKON adds a low cost radio broadcast unit to those "
                    "points. The unit broadcasts its identity and the position "
                    "surveyed when it was installed. Where those points "
                    "are sparse, the other poles along the road are used: "
                    "in the simulation, lighting columns in town and "
                    "mostly electricity distribution poles in open "
                    "country.",
                ),
                _w(
                    "Bir yayın biriminin 1000 adetlik üretimdeki maliyeti; "
                    "muhafazası, baskılı devre kartı, dizgi ve lehim işçiliği "
                    "dahil yaklaşık 1400 TL'dir. Maliyetin düşük "
                    "tutulabilmesinin temel nedeni, AUS noktalarında "
                    "hâlihazırda bulunan elektrik ve haberleşme altyapısının "
                    "yeniden kullanılmasıdır.",
                    "A broadcast unit costs roughly 1400 lira at "
                    "a thousand units, box, printed board, assembly and "
                    "soldering included. The aim is to reuse "
                    "the power and "
                    "communications already standing at intelligent "
                    "transport points, and that is what keeps the cost "
                    "down.",
                ),
                _w(
                    "YERKON, yalnızca GNSS kesildiğinde devreye giren bir yedek"
                    " sistem değil, GNSS çalışırken de onu denetleyen bağımsız "
                    "bir doğrulama katmanıdır. Alıcı, uydunun verdiği konumu "
                    "YERKON'un hesapladığı konumla sürekli olarak "
                    "karşılaştırmaktadır; iki konum arasında anlamlı bir fark "
                    "oluştuğunda karıştırma veya aldatma (spoofing) girişimi "
                    "tespit edilmektedir.",
                    "YERKON is not only a backup that takes over when GNSS "
                    "is lost; while GNSS works, it is an independent layer "
                    "that checks it. The receiver keeps comparing the "
                    "position from the satellites with the position from "
                    "YERKON, and when the two part ways, jamming or "
                    "spoofing is caught.",
                ),
            ),
        ),
        Part(
            kind="points",
            heading=_w("Kullanım alanları", "Who it serves"),
            lines=(
                _w("**Acil yardım ve afet yönetimi.** 112 ve AFAD ekiplerinin "
                   "konumu tünellerde, kapalı alanlarda, yüksek binalar "
                   "arasında ve afet bölgelerinde de izlenebilmektedir.",
                   "**Emergency services and disasters.** Ambulance and "
                   "disaster teams stay visible in tunnels, indoors, "
                   "between tall buildings and in disaster areas."),
                _w("**Karayolu, kargo ve toplu taşıma.** Kamu araçları, "
                   "otobüsler ve tehlikeli madde taşıyan araçlar için uydudan "
                   "bağımsız ikinci bir takip imkânı sağlanmaktadır.",
                   "**Road, freight and public transport.** Public "
                   "vehicles, buses and dangerous goods carriers gain a "
                   "second way of being tracked that does not depend on "
                   "the satellites."),
                _w("**Tüneller.** Uydu sinyalinin ulaşmadığı tünellerde konum "
                   "bilgisi kesintisiz olarak sürdürülmektedir; bu nedenle "
                   "tüneller ilk kurulum için en uygun alanlardır.",
                   "**Tunnels.** Position carries on where the satellites "
                   "cannot reach; the best place for a first deployment."),
                _w("**Karıştırma ve aldatma haritası.** Uydu konumu ile YERKON"
                   " konumu arasında fark oluştuğunda olay merkezî sisteme "
                   "iletilmekte; böylece Bakanlık ülke genelinde bir olay "
                   "haritasına sahip olmaktadır.",
                   "**A map of jamming and spoofing.** When the satellite "
                   "position and YERKON's part ways, the event goes to the "
                   "centre, and the Ministry gets a map of such events "
                   "across the country."),
            ),
        ),
        Part(
            kind="points",
            heading=_w("Projenin durumu", "Where the project stands"),
            lines=(
                _w("**Tamamlandı: simülasyon.** Şehir içi, kırsal ve tünel "
                   "senaryoları Ankara'nın gerçek arazi verisi üzerinde simüle"
                   " edilmiştir; sonuçlar Karşılaştırma sayfasında "
                   "sunulmaktadır.",
                   "**Done: the simulation.** Urban, rural and tunnel, over "
                   "real ground near Ankara; the results are on the "
                   "Comparison page."),
                _w("**Tamamlandı: tasarım ve maliyet.** Yayın birimi ve "
                   "alıcıların parça listesi, 1000 adetlik üretim fiyatları ve"
                   " mevzuat incelemesi hazırlanmıştır.",
                   "**Done: design and cost.** The parts list of the "
                   "broadcast unit and the receivers, their prices at a "
                   "thousand, and the regulatory review."),
                _w("**Sonraki adım: mevcut donanımla denemeler.** Haberleşme, "
                   "kapsama, konumlandırma ve şifreleme mantığı, ekibin "
                   "hâlihazırda sahip olduğu cihazlarla sınanacaktır.",
                   "**Next: trials on the team's own hardware.** "
                   "Communication, coverage, positioning and signing logic "
                   "get tried on devices the team already has."),
                _w("**Ardından: 10-15 birimlik pilot koridor.** Projeye özel "
                   "kartlar üretildikten sonra seçilecek bir ulaşım koridoruna"
                   " 10-15 yayın birimi kurulacaktır.",
                   "**Then: a corridor of 10 to 15 units.** Once the "
                   "project's own boards are made, 10 to 15 broadcast units "
                   "go up along a chosen transport corridor."),
                _w("**Henüz yapılmadı: saha ölçümü.** Sitede yer alan doğruluk"
                   " ve kapsama değerleri simülasyon sonuçlarıdır; saha "
                   "ölçümleriyle ayrıca doğrulanacaktır.",
                   "**Not yet done: field measurement.** The accuracy and "
                   "coverage figures on this site are simulation results."),
            ),
            states=("done", "done", "todo", "todo", "todo"),
        ),
        Part(kind="map", heading=_w("Sayfalar", "Pages")),
        # One column a person, a line between them; each line of a
        # person's entry is a line of the column.
        Part(
            kind="people",
            heading=_w("Ekip ve iletişim", "Team and contact"),
            lines=(
                _w("**Mehmet GÖNÜL**\nTOBB ETÜ Bilgisayar Mühendisliği, "
                   "4. sınıf\n[mgonul@etu.edu.tr](mailto:mgonul@etu.edu.tr)",
                   "**Mehmet GÖNÜL**\nTOBB ETÜ Computer Engineering, fourth "
                   "year\n[mgonul@etu.edu.tr](mailto:mgonul@etu.edu.tr)"),
                _w("**Mustafa Göktürk BİNAY**\nTOBB ETÜ Bilgisayar "
                   "Mühendisliği, 2. sınıf\n"
                   "[gokturkbnay@gmail.com](mailto:gokturkbnay@gmail.com)",
                   "**Mustafa Göktürk BİNAY**\nTOBB ETÜ Computer "
                   "Engineering, second year\n"
                   "[gokturkbnay@gmail.com](mailto:gokturkbnay@gmail.com)"),
                _w("**Yavuz Selim OKTAR**\nTOBB ETÜ Yapay "
                   "Zekâ Mühendisliği, 3. sınıf\n"
                   "[yavuzselimoktar@gmail.com](mailto:yavuzselimoktar@gmail.com)",
                   "**Yavuz Selim OKTAR**\nTOBB ETÜ "
                   "Artificial Intelligence Engineering, third year\n"
                   "[yavuzselimoktar@gmail.com](mailto:yavuzselimoktar@gmail.com)"),
            ),
        ),
        Part(
            kind="text",
            lines=(
                _w("Simülasyonun kaynak kodu ve yöntemi: "
                   "[GitHub](https://github.com/ysoktar/yerkon)",
                   "The simulation's code and method: "
                   "[GitHub](https://github.com/ysoktar/yerkon)"),
            ),
        ),
    ),
)

WHY = Page(
    slug="sorun",
    slug_en="problem",
    nav=_w("Sorun", "The problem"),
    title=_w("GNSS'in yetersiz kaldığı durumlar", "Why GNSS is not enough"),
    lead=_w(
        "Günümüzde konum ve seyrüsefer hizmetlerinin neredeyse "
        "tamamı GPS, Galileo, GLONASS ve BeiDou sistemlerinden "
        "sağlanmaktadır. Bu bağımlılık yalnızca araç navigasyonunu "
        "değil; acil çağrı ekiplerini, kamu araç filolarını, "
        "insansız araçları ve kargo taşımacılığını da "
        "kapsamaktadır.",
        "Nearly everything that finds a position or gives directions "
        "today runs on GPS, Galileo, GLONASS and BeiDou. The dependency "
        "does not stop at vehicle navigation: emergency crews, public "
        "fleets, unmanned vehicles and freight all hang on the same four "
        "systems.",
    ),
    parts=(
        Part(
            kind="picture",
            picture="gnss.webp",
            lines=(_w(
                "Bu dört sistemin tamamı yabancı devletlerin kontrolündedir"
                " ve hepsi aynı zayıflığı taşımaktadır: uydudan gelen "
                "sinyal yeryüzüne ulaştığında son derece zayıftır.",
                "All four are in the hands of foreign states, and all "
                "four have the same weak spot: the signal from a satellite "
                "is faint by the time it reaches the ground.",
            ),),
        ),
        Part(
            kind="points",
            heading=_w("Mevcut GNSS sistemlerindeki kırılganlıklar", "Where it breaks"),
            lines=(
                _w(
                    "Tünellerde, kapalı alanlarda ve yüksek binalar arasında "
                    "(kentsel kanyon) sinyal kaybı yaşanmaktadır.",
                    "The signal is lost in tunnels, indoors and between "
                    "tall buildings.",
                ),
                _w(
                    "Düşük güçlü GNSS sinyalleri karıştırmaya açıktır ve bu "
                    "amaçla kullanılan elektronik harp ürünleri giderek "
                    "yaygınlaşmaktadır.",
                    "The signal is weak, so it is easy to drown out, and "
                    "the equipment for doing it keeps spreading.",
                ),
                _w(
                    "Sahte sinyaller alıcının yanlış bir konum hesaplamasına "
                    "neden olmaktadır. Alıcının bu yanlış konumu yüksek güven "
                    "düzeyiyle doğruymuş gibi göstermesi, aldatma saldırılarını"
                    " özellikle tehlikeli kılmaktadır.",
                    "A fake signal makes the receiver work out a wrong "
                    "position. The receiver then shows that position as "
                    "though it were right, and with high confidence. That "
                    "is what makes it dangerous.",
                ),
                _w(
                    "Kritik hizmetler tek bir teknoloji ailesine bağımlıdır.",
                    "Critical services depend on a single family of "
                    "technology.",
                ),
                _w(
                    "Kriz anında sistem üzerindeki karar yetkisi Türkiye'de "
                    "bulunmamaktadır.",
                    "In a crisis the authority over the system does not "
                    "sit in Türkiye.",
                ),
            ),
        ),
        Part(
            kind="points",
            heading=_w("Dünyadan örnekler", "What has already happened"),
            lines=(
                _w(
                    "**ABD, 14 Mayıs 2026.** Roswell'de konuşlu bir ambulans "
                    "uçağı, hasta almak üzere Ruidoso'daki Sierra Blanca Bölge "
                    "Havalimanı'na giderken Capitan Dağları'na çarpmış ve dört "
                    "kişi hayatını kaybetmiştir. Uçuş boyunca bölgede önceden "
                    "duyurulmuş askerî GPS karıştırması sürmekteydi; "
                    "mürettebat, kalkıştan 8 dakika sonra GPS sinyalini "
                    "kaybettiğini bildirmiştir. NTSB'nin ön raporu kazanın "
                    "nedenini henüz belirlememiştir; ancak olay, karıştırma "
                    "sırasında acil durum uçuşlarının tek konum kaynağını "
                    "kaybedebildiğini göstermektedir. [NTSB ön "
                    "raporu](https://data.ntsb.gov/carol-repgen/api/Aviation/ReportMain/GenerateNewestReport/202990/pdf)",
                    "**United States, 14 May 2026.** An air ambulance based "
                    "in Roswell, on its way to Sierra Blanca Regional "
                    "Airport in Ruidoso to pick up a patient, hit the "
                    "Capitan Mountains; four people died. Previously "
                    "announced military GPS jamming was active in the area "
                    "throughout the flight, and the crew reported losing "
                    "GPS 8 minutes after take-off. The NTSB preliminary "
                    "report has not yet determined the cause; the accident "
                    "still shows that an emergency flight can lose its "
                    "only source of position while jamming is on. "
                    "[NTSB preliminary report](https://data.ntsb.gov/"
                    "carol-repgen/api/Aviation/ReportMain/"
                    "GenerateNewestReport/202990/pdf)",
                ),
                _w(
                    "**Baltık, Nisan 2024.** Finlandiya ulusal havayolu "
                    "Finnair, Estonya'nın Tartu kentine olan uçuşlarını bir ay "
                    "süreyle tamamen durdurmak zorunda kalmıştır. İki yolcu "
                    "uçağı, yaklaşma sırasında GPS sinyalini kaybettiği için "
                    "iniş yapamayarak Helsinki'ye geri dönmüştür. Havalimanının"
                    " tek yaklaşma sistemi GPS tabanlı olduğundan uçuşlar "
                    "haftalarca durdurulmuştur. [Anadolu "
                    "Ajansı](https://www.aa.com.tr/en/europe/suspected-russian-gps-jamming-too-dangerous-to-ignore-baltic-officials/3205763)",
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
                    "**Tel Aviv, 4 Nisan 2024.** İsrail ordusu, olası "
                    "saldırılara karşı GPS sinyallerini kasıtlı olarak "
                    "yanıltmıştır. Sürücülerin Waze ve Google Maps uygulamaları"
                    " kullanıcıları yaklaşık 210 km kuzeydeki Beyrut'ta "
                    "göstermiş; taksiler yolunu bulamamış, taksi çağırma ve "
                    "yemek siparişi uygulamaları aksamıştır. Ordu, bu "
                    "müdahalenin savunma amaçlı olduğunu doğrulamıştır. "
                    "Aldatmanın en tehlikeli yönü fark edilmemesidir: Anadolu "
                    "Ajansı'nın aktardığına göre bir pilot, sinyalin sahte "
                    "olduğunu bildiren hiçbir uyarı bulunmadığını ifade "
                    "etmiştir. [Anadolu "
                    "Ajansı](https://www.aa.com.tr/en/middle-east/israel-spoofs-gps-signals-amid-gaza-onslaught/3202337)"
                    " · [GPS "
                    "World](https://www.gpsworld.com/gps-disruptions-in-tel-aviv-as-israel-braces-for-possible-iranian-attacks/)",
                    "**Tel Aviv, 4 April 2024.** The Israeli army spoofed "
                    "GPS signals on purpose to guard against possible "
                    "attacks. Drivers' Waze and Google Maps apps put them "
                    "in Beirut, about 210 km to the north; taxis could not "
                    "find their way, and ride-hailing and food ordering "
                    "apps faltered. The army confirmed the disruption was "
                    "defensive. The worst of spoofing is that it goes "
                    "unnoticed: in words Anadolu Agency reported, a pilot "
                    "says there is no warning that the signal is fake. "
                    "[Anadolu Agency](https://www.aa.com.tr/en/middle-east/"
                    "israel-spoofs-gps-signals-amid-gaza-onslaught/3202337) · "
                    "[GPS World](https://www.gpsworld.com/gps-disruptions-in-"
                    "tel-aviv-as-israel-braces-for-possible-iranian-attacks/)",
                ),
                _w(
                    "**Norveç, 2017 sonbaharından bu yana.** Finnmark "
                    "bölgesinde GPS sinyalleri defalarca kesilmiştir; Norveç "
                    "Savunma Bakanlığı kaynağın Rusya'nın Kola Yarımadası "
                    "olduğunu doğrulamıştır. Bölgedeki polis, ambulans ve "
                    "kurtarma ekipleri navigasyonda GPS'e dayanmaktadır. Bölge "
                    "polis şefi, bir kar fırtınasında kaybolan bir kişinin "
                    "GPS'li acil durum vericisi sayesinde kurtarıldığını ve GPS"
                    " olmasaydı yoğun kar içinde bulunamayacağını belirterek "
                    "karıştırmanın bu tür kurtarma operasyonlarını tehlikeye "
                    "attığını vurgulamıştır. [The Barents "
                    "Observer](https://www.thebarentsobserver.com/security/gps-jamming-jeopardizes-public-safety-in-norways-northernmost-region/157622)",
                    "**Norway, since autumn 2017.** GPS signals in "
                    "Finnmark have been cut again and again; Norway's "
                    "defence ministry confirmed the source as Russia's "
                    "Kola Peninsula. Police, ambulance and rescue teams "
                    "there navigate by GPS. The regional police chief "
                    "told of a person lost in a snowstorm who was saved "
                    "because his GPS emergency beacon worked and could "
                    "not have been found in the deep snow without GPS, "
                    "to stress that jamming puts such rescues at risk. "
                    "[The Barents Observer](https://www.thebarentsobserver"
                    ".com/security/gps-jamming-jeopardizes-public-safety-in-"
                    "norways-northernmost-region/157622)",
                ),
                _w(
                    "**Karadeniz, 22 Haziran 2017.** Yirmiden fazla ticari "
                    "geminin konum alıcısı aynı anda yanlış konum vermiştir: "
                    "gemiler açık denizdeyken ekranlar onları 32 km'den daha "
                    "içeride bulunan Gelencik Havalimanı'nda göstermiştir. "
                    "Olayın arkasında Rusya'nın bulunduğundan "
                    "şüphelenilmektedir. Olay, aldatmanın tek bir aracı değil, "
                    "bir bölgedeki bütün alıcıları aynı anda yanıltabildiğini "
                    "göstermektedir; aynı saldırı bir karayolu koridorunda da "
                    "gerçekleştirilebilir. "
                    "[GalileoGNSS](https://galileognss.eu/mass-gps-spoofing-attack-in-black-sea/)",
                    "**The Black Sea, 22 June 2017.** The position "
                    "receivers of more than twenty commercial ships gave a "
                    "wrong position at the same time: out at sea, their "
                    "screens put them at Gelendzhik Airport, more than "
                    "32 km inland. Russia is suspected to be behind it. "
                    "It shows that spoofing can fool not one vehicle but "
                    "every receiver in an area at once; the same attack "
                    "could be made on a road corridor. "
                    "[GalileoGNSS](https://galileognss.eu/"
                    "mass-gps-spoofing-attack-in-black-sea/)",
                ),
            ),
        ),
        Part(kind="shows", shows="when"),
        Part(
            kind="text",
            heading=_w("YERKON'un önerdiği çözüm", "YERKON's solution"),
            lines=(
                _w(
                    "Kırsal yayın birimi için 8-10 km'lik bir haberleşme ve "
                    "kapsama hedefi belirlenmiştir; bu mesafelerdeki ölçüm "
                    "doğruluğu saha deneyleriyle ayrıca doğrulanacaktır. Hedefe"
                    " ulaşılması durumunda alçak irtifada uçan hava araçları da"
                    " yayın birimlerinden yararlanabilecektir. Havalimanı "
                    "çevresine kurulacak yayın birimleri ise uydu sinyalleri "
                    "kullanılamaz hâle geldiğinde de çalışmaya devam eden "
                    "karasal bir konumlandırma hizmeti sunabilecektir. Bu "
                    "değerler projenin hedefleridir ve henüz sahada "
                    "ölçülmemiştir.",
                    "For the rural unit, 8 to 10 km is a communications "
                    "and coverage target; how accurately it can measure "
                    "distance at that range is to be confirmed by field "
                    "trials. If it holds, a low flying aircraft can hear "
                    "the unit too. Units around an airport could offer a "
                    "terrestrial positioning service that keeps working "
                    "even with the satellites silenced. These are the "
                    "report's targets; none of them has been measured in "
                    "the field yet.",
                ),
                _w(
                    "YERKON, sahte sinyallere karşı bir yedek olmanın ötesinde "
                    "bir doğrulama mekanizmasıdır. Araç, uydunun verdiği konumu"
                    " yer tabanlı birimlerden elde edilen konumla "
                    "karşılaştırarak bir aldatma saldırısı altında olup "
                    "olmadığını tespit edebilmektedir.",
                    "Against a fake signal YERKON is more than a standby: "
                    "it is a cross-check. A vehicle can compare "
                    "the satellite's position with the one from the ground "
                    "and so detect that it is under a spoofing attack.",
                ),
            ),
        ),
    ),
)

#: The final product's main parts, in the order a unit is built up:
#: radios, what drives them, the antenna, power, and the boxes. Names and
#: roles come from bom.toml, so they never differ from the cost page.
FINAL_PARTS = (
    ("e28-2g4m20s", "e28-2g4m20s.webp"),
    ("dwm3000-lcsc", "dwm3000-lcsc.webp"),
    ("stm32g031k8t6", "stm32g031k8t6.webp"),
    ("at32f403argt7", "at32f403argt7.webp"),
    ("atecc608b", "atecc608b.webp"), ("esp32-s3", "esp32-s3.webp"),
    ("bno085", "bno085.webp"), ("atgm336h-5nr32", "atgm336h-5nr32.webp"),
    ("pro-ob-430", "pro-ob-430.webp"), ("zdemmc04ga", "zdemmc04ga.webp"),
    ("gw-22-5151", "gw-22-5151.webp"), ("hlk-5m12", "hlk-5m12.webp"),
    ("lipo-1000", "lipo-1000.webp"),
    ("seeed-solar-0.5w", "seeed-solar-0.5w.webp"),
    ("ili9341-2.8", "ili9341-2.8.webp"),
    ("gdey0154d67", "gdey0154d67.webp"),
    ("gainta-g203", "gainta-g203.webp"), ("gainta-g212", "gainta-g212.webp"),
    ("gainta-g517", "gainta-g517.webp"),
)

#: Where each photo was taken from: the maker's or the seller's own
#: picture of the part, named under it on the card.
PHOTO_SOURCES = {
    "e28-2g4m20s.webp": ("EBYTE", "https://www.cdebyte.com/products/E28-2G4M20S"),
    "dwm3000-lcsc.webp": ("LCSC", "https://www.lcsc.com/product-detail/C5299931.html"),
    "stm32g031k8t6.webp": ("LCSC", "https://www.lcsc.com/product-detail/C432203.html"),
    "at32f403argt7.webp": ("LCSC", "https://www.lcsc.com/product-detail/C528440.html"),
    "atecc608b.webp": ("LCSC", "https://www.lcsc.com/product-detail/C1518773.html"),
    "esp32-s3.webp": ("LCSC", "https://www.lcsc.com/product-detail/C2913198.html"),
    "bno085.webp": ("LCSC", "https://www.lcsc.com/product-detail/C5189642.html"),
    "atgm336h-5nr32.webp": ("LCSC", "https://www.lcsc.com/product-detail/C5117921.html"),
    "pro-ob-430.webp": ("LCSC", "https://www.lcsc.com/product-detail/C3284500.html"),
    "zdemmc04ga.webp": ("LCSC", "https://www.lcsc.com/product-detail/C3010207.html"),
    "gw-22-5151.webp": ("Westward Sales", "https://westwardsales.com/taoglas-gw.22.5151-rp-sma-antenna"),
    "hlk-5m12.webp": ("LCSC", "https://www.lcsc.com/product-detail/C209908.html"),
    "lipo-1000.webp": ("YDL Battery", "https://ydlbattery.com/products/50pcs-3-7v-1000mah-803040-lithium-polymer-battery"),
    "seeed-solar-0.5w.webp": ("Seeed Studio", "https://www.seeedstudio.com/0-5W-Solar-Panel-55x70.html"),
    "ili9341-2.8.webp": ("Elecrow", "https://www.elecrow.com/2-8-inch-320x240-spi-serial-tft-lcd-module-display-with-driver-ic-ili9341.html"),
    "gdey0154d67.webp": ("buy-lcd.com", "https://www.buy-lcd.com/products/154-inch-electronic-paper-display-200x200-partial-refresh-digital-price-tags-sreen-gdey0154d67"),
    "gainta-g203.webp": ("Gainta", "https://www.gainta.com/en/g203.html"),
    "gainta-g212.webp": ("Gainta", "https://www.gainta.com/en/g212.html"),
    "gainta-g517.webp": ("Gainta", "https://www.gainta.com/en/g517gbc-1.html"),
    "rak-r1.webp": ("muzi works", "https://muzi.works/products/r1"),
    "rak-wisblock.webp": ("RAKwireless", "https://store.rakwireless.com/products/wisblock-meshtastic-starter-kit"),
    "atgm336h.webp": ("LCSC", "https://www.lcsc.com/product-detail/C90770.html"),
    "whip.webp": ("RAKwireless", "https://store.rakwireless.com/products/lora-antenna"),
    "sdr.webp": ("Great Scott Gadgets", "https://greatscottgadgets.com/hackrf/one/"),
    "t1000-e.webp": ("Seeed Studio", "https://www.seeedstudio.com/SenseCAP-Card-Tracker-T1000-E-for-Meshtastic-p-5913.html"),
}

#: The hardware the team already has for the pilot, as the proposal's
#: "Pilot Doğrulama" slide lists it. None of it is bought for the
#: project, so it is not in bom.toml: its name and what it is live here.
PILOT_ITEMS = {
    "rak-r1": (_w("RAKwireless R1 Meshtastic", "RAKwireless R1 Meshtastic"),
               _w("Meshtastic cihazı", "Meshtastic device")),
    "rak-wisblock": (_w("RAK WisBlock", "RAK WisBlock"),
                     _w("geliştirme kiti", "development kit")),
    "t1000-e": (_w("Seeed Studio SenseCAP Card Tracker T1000-E",
                   "Seeed Studio SenseCAP Card Tracker T1000-E"),
                _w("kart tipi izleyici", "card tracker")),
    "atgm336h": (_w("ATGM336H", "ATGM336H"),
                 _w("GNSS modülü", "GNSS module")),
    "whip": (_w("Whip anten", "Whip antenna"),
             _w("harici anten", "external antenna")),
    "sdr": (_w("SDR geliştirme altyapısı", "SDR development setup"),
            _w("TWR mesajlaşması, kanal erişimi ve ölçeklenebilirlik "
               "yaklaşımlarının projeye özel kartlara aktarılmadan önce "
               "denenmesi için",
               "to try TWR messaging, channel access and scaling before "
               "they go onto the boards")),
}

#: The pilot's strip, in the slide's order.
PILOT_PARTS = tuple(
    (key, key + ".webp") for key in PILOT_ITEMS)

SYSTEM = Page(
    slug="sistem",
    slug_en="system",
    nav=_w("Sistem", "The system"),
    title=_w("YERKON mimarisi", "The architecture"),
    lead=_w(
        "YERKON üç bileşenden oluşmaktadır: koordinatları ölçülmüş "
        "noktalara yerleştirilen yayın birimleri, kendi konumunu "
        "hesaplayan alıcılar ve yayın birimlerinin kimlik ve açık "
        "anahtarlarını güncel tutan Merkezî Yönetim Sistemi.",
        "Three parts: broadcast units standing at surveyed positions, "
        "receivers that work out their own position, and a management "
        "system that keeps the identities current.",
    ),
    parts=(
        Part(
            kind="picture",
            picture="architecture.webp",
            lines=(_w(
                "Alıcı, yayın birimine olan mesafeyi karşılıklı mesajlaşma "
                "yoluyla ölçmektedir. Merkezî Yönetim Sistemi ile yayın "
                "birimleri arasındaki bağlantı ise mesafe ölçümü için "
                "değil, kimlik ve anahtar bilgilerinin aktarılması için "
                "kullanılmaktadır.",
                "The labels are in Turkish. The receiver "
                "measures distance by sending messages back and forth. "
                "The line between the management system and the units "
                "carries identity and keys rather than distance.",
            ),),
        ),
        Part(
            kind="points",
            heading=_w("Sistem bileşenleri", "Three parts"),
            lines=(
                _w(
                    "**Yayın birimi.** Direk, yol kenarı ünitesi, haberleşme "
                    "tesisi veya tünel gibi sabit bir noktaya yerleştirilen "
                    "vericidir. Alıcı konum verisi talep ettiğinde üç bilgiyi "
                    "yayınlamaktadır: birim kimliği, kurulum sırasında ölçülmüş"
                    " sabit koordinatı ve bu bilgilerin özgünlüğünü kanıtlayan "
                    "dijital imza.",
                    "**The broadcast unit.** A transmitter fixed to one "
                    "point: a mast, a roadside unit, a communications "
                    "site, or inside a tunnel. When a receiver asks, it "
                    "broadcasts three things: who it is, the fixed "
                    "position surveyed at installation, and the signature "
                    "that shows neither is forged.",
                ),
                _w(
                    "**Alıcı.** Araçlara veya taşınabilir cihazlara "
                    "yerleştirilmektedir. Yayın birimlerinden ölçtüğü "
                    "mesafeleri atalet ölçüm birimi, tekerlek odometrisi ve "
                    "harita verileriyle birleştirerek uydu sinyali hiç "
                    "bulunmadığında da konum üretmeye devam etmektedir. "
                    "Karşılaştırma tablosundaki simülasyonda atalet ölçüm "
                    "birimi ve odometri kullanılmamış; yalnızca mesafe "
                    "ölçümleri ve yükseklik haritasından elde edilen yükseklik "
                    "bilgisi kullanılmıştır.",
                    "**The receiver.** It goes in a vehicle or in a "
                    "pocket. It combines the distances it measures to the "
                    "units with the vehicle's own sensors: an inertial "
                    "unit that measures movement, how far the wheels have "
                    "turned, and the map. So it keeps giving a position "
                    "with no satellite in sight. The simulation behind "
                    "the table uses neither the inertial unit nor the "
                    "wheels; only the ranges and the height from the "
                    "elevation map.",
                ),
                _w(
                    "**Merkezî Yönetim Sistemi.** Yayın birimlerinin "
                    "kimliklerini ve açık anahtarlarını içeren listeyi güncel "
                    "tutmaktadır. Alıcı bu listeyi indirerek her yayın "
                    "biriminin imzasını doğrulamakta; böylece taklit bir yayın "
                    "birimiyle iletişim kurulması önlenmektedir.",
                    "**The management system.** It keeps the list of which "
                    "unit holds which key. A receiver downloads that list "
                    "and checks each unit's signature, so it never talks "
                    "to a forged one.",
                ),
            ),
        ),
        Part(
            kind="text",
            heading=_w("Çift yönlü mesafe ölçümünün (TWR) tercih edilme nedeni", "Why two way ranging"),
            lines=(
                _w(
                    "Sinyalin farklı yayın birimlerine ulaşma süreleri "
                    "arasındaki farkı kullanan sistemlerde (TDoA), aynı "
                    "doğruluk seviyesine ulaşabilmek için yayın birimleri "
                    "arasında hassas, ağ geneli bir zaman senkronizasyonu ve "
                    "bunu sağlayan ek altyapı gerekebilmektedir. Örneğin "
                    "nanosaniyenin altında bir senkronizasyon, her yayın "
                    "biriminde bir atomik saat ve IEEE 1588 PTP altyapısı "
                    "gerektirmektedir. Çip ölçekli bir atomik saatin (Microchip"
                    " SA65) birim fiyatı yaklaşık 5500 ABD doları, yani "
                    "yaklaşık 270000 TL'dir ([Analog IC Tips, Eylül "
                    "2021](https://www.analogictips.com/the-pc-board-atomic-clock-part-3-the-csac-cesium-physics-cell-faq/))."
                    " Çift yönlü mesafe ölçümünde (TWR) bu ağ geneli "
                    "senkronizasyona gerek duyulmamaktadır; sinyalin havada "
                    "geçirdiği süre, yayın birimi ile alıcı arasındaki kısa bir"
                    " karşılıklı mesajlaşmadan hesaplanmaktadır.",
                    "Systems that look at how much later a signal reaches "
                    "one unit than another (TDoA) may need precise network "
                    "wide time synchronisation between the units, and the "
                    "infrastructure to supply it, to reach the same "
                    "accuracy. Going below a billionth of a second, for "
                    "instance, means an atomic clock and IEEE 1588 PTP at "
                    "every unit. One chip-scale atomic clock (Microchip "
                    "SA65) costs about 5500 dollars, roughly 270000 lira "
                    "([Analog IC Tips, September 2021]"
                    "(https://www.analogictips.com/the-pc-board-atomic-clock-part-3-the-csac-cesium-physics-cell-faq/)). "
                    "Two way ranging needs no "
                    "network wide synchronisation: the time the signal "
                    "spends in the air comes out of one short "
                    "there-and-back between the unit and the receiver.",
                ),
                _w(
                    "YERKON'u benzer ticari sistemlerden ayıran temel teknik "
                    "fark da buradan kaynaklanmaktadır. NextNav TerraPoiNT ve "
                    "Locata sistemlerinde alıcı yalnızca dinlemektedir; bu "
                    "nedenle vericilerin saatlerinin nanosaniye düzeyinde "
                    "eşitlenmesi gerekmektedir. NextNav bu amaçla atomik saatli"
                    " vericiler ve ABD'de lisanslı 920-928 MHz bandını, Locata "
                    "ise vericilerin birbirini dinleyerek eşitlendiği TimeLoc "
                    "yöntemini ve kendine özgü verici donanımını "
                    "kullanmaktadır. Pozyx ise UWB teknolojisiyle yalnızca "
                    "küçük kapalı alanlara hizmet vermektedir. YERKON, yayın "
                    "birimleri arasında saat eşitlemesi gerektirmemekte; "
                    "lisanssız 2,4 GHz ve UWB bantlarında, yol kenarında "
                    "hâlihazırda bulunan yapılara yerleştirilen birimlerle açık"
                    " yolu ve tüneli aynı alıcıyla kapsamaktadır. Bu yaklaşımın"
                    " bedeli, alıcının da yayın yapması ve eşzamanlı kullanıcı "
                    "sayısının sınırlanmasıdır; bu kısıtı aşmak için TWR CDMA "
                    "ve yazılım tanımlı radyo (SDR) tabanlı yöntemler sisteme "
                    "eklenecektir.",
                    "The technical difference from similar commercial "
                    "systems comes from the same place. In NextNav "
                    "TerraPoiNT and Locata the receiver only listens, so "
                    "the transmitters' clocks have to agree to within "
                    "nanoseconds: NextNav uses transmitters with atomic "
                    "clocks and its licensed 920-928 MHz band in the United "
                    "States, Locata its TimeLoc method, where transmitters "
                    "listen to each other to stay in step, and its own "
                    "transmitter hardware. Pozyx serves only small indoor "
                    "areas with UWB. YERKON needs no clock agreement "
                    "between units; in the licence-free 2,4 GHz and UWB "
                    "bands, with units fixed to structures already by the "
                    "road, one receiver covers the open road and the "
                    "tunnel. The price is that the receiver transmits too "
                    "and the number of users is limited; methods built on "
                    "TWR CDMA and software defined radio will be added for "
                    "that.",
                ),
                _w(
                    "Her telsiz yongası zamanı kendi kristal osilatörüyle "
                    "ölçmektedir ve iki yonganın kristali birebir aynı "
                    "frekansta çalışmamaktadır. Çift yönlü ölçümde bu fark, "
                    "yalnızca yayın biriminin yanıt vermeden önce beklediği "
                    "kısa süre boyunca hataya dönüşmekte; alıcı bu farkı gelen "
                    "sinyalden kestirerek düzeltmektedir. Simülasyonda düzeltme"
                    " sonrasında kalan hata, tek bir mesafe ölçümünde 20 "
                    "santimetreyi aşmamaktadır.",
                    "Every radio chip counts time with its own crystal, and "
                    "no two crystals run at exactly the same rate. In two "
                    "way ranging that difference only turns into error "
                    "over the short wait before the unit answers, and the "
                    "receiver estimates it from the incoming signal and "
                    "removes it. In the simulation what is left after that "
                    "correction stays under 20 centimetres on one range.",
                ),
                _w(
                    "Her yayın birimi kendi özel anahtarını gizli tutmakta ve "
                    "açık anahtarını Merkezî Yönetim Sistemi'ne aktarmaktadır. "
                    "Anahtar 256 bit ECC, imza algoritması ise ECDSA'dır. "
                    "Kaydedilip daha sonra yeniden yayınlanan eski bir mesaj, "
                    "sıra numarası sayesinde tespit edilmektedir.",
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
            heading=_w("Yayın birimi kurulum grupları", "Three kinds of installation"),
            lines=(
                _w(
                    "**Şehir içi.** Kırsal bölgedeki ile aynı yayın birimi "
                    "kullanılmakta; binalar sinyali engellediği için birimler "
                    "daha sık yerleştirilmektedir. Kurulum için uygun noktalar "
                    "baz istasyonları, trafik levhaları ve lambaları, reklam "
                    "panoları ve yol kenarı aydınlatmalarıdır. Yayın biriminde "
                    "EBYTE E28-2G4M20S modülü kullanılmaktadır; modülün 2,4 GHz"
                    " telsiz yongası Semtech SX1280'dir. Üretici, bu yonga için"
                    " doğrudan görüş hattı (LoS) koşullarında yaklaşık ±1 m "
                    "mesafe ölçüm doğruluğu belirtmektedir. Bu değer, tek bir "
                    "yayın birimi ile alıcı arasındaki mesafe ölçümünün "
                    "doğruluğunu ifade etmekte olup nihai konum hatası "
                    "değildir. Nihai konum hatası; yayın birimi geometrisine, "
                    "çok yollu yayılıma (multipath) ve engellere bağlıdır ve "
                    "ayrıca HPE P50 ile HPE P95 metrikleriyle "
                    "değerlendirilecektir.",
                    "**Urban.** The same broadcast unit as in open "
                    "country, placed closer together because buildings "
                    "cut the signal. It can go on base station sites, "
                    "traffic signs and lights, advertising boards and "
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
                    "**Kırsal.** Az sayıda fakat geniş alana hizmet veren "
                    "noktalar kullanılmaktadır: akıllı ulaşım sistemi ve yol "
                    "kenarı üniteleri, baz istasyonu sahaları, demiryolu ve "
                    "karayolu altyapısı. Bu noktalar seyrek olduğundan "
                    "simülasyonda yayın birimlerinin çoğu, yol boyundaki "
                    "elektrik dağıtım direklerine güneş paneli ve aküyle "
                    "birlikte yerleştirilmiştir. Cihaz, Frekans Atlamalı "
                    "Spektrum Yayılımı (FHSS) ve Göndermeden Önce Dinle (LBT) "
                    "ile TS EN 300 328'e göre belgelendirilecektir; FHSS'teki "
                    "100 mW/100 kHz yoğunluk sınırı 1,625 MHz genişliğindeki "
                    "sinyal için sınırlayıcı olmadığından 100 mW (20 dBm) "
                    "e.i.r.p. kullanılabilmektedir. Kırsal birim, şehir "
                    "içindeki ile aynı yayın birimidir: yükselteçli E28-2G4M20S"
                    " modülü ve dış ortam tipi 5 dBi çubuk anten. İki birim "
                    "arasındaki fark donanımda değil, kurulum yerindedir: "
                    "kırsalda arada bina bulunmadığı için sinyal çok daha uzağa"
                    " ulaşmakta, elektrik bağlantısı olmayan direklerde ise "
                    "güneş paneli ve akü kullanılmaktadır. YERKON kapsamında "
                    "8-10 km'lik menzil bir haberleşme ve kapsama hedefi olarak"
                    " değerlendirilmektedir; bu mesafelerdeki ölçüm doğruluğu "
                    "saha deneyleriyle ayrıca doğrulanacaktır. Simülasyonda "
                    "kullanılan Polatlı arazisi seyrek yapılaşmış bir bozkır "
                    "olduğundan, 486 m'lik yükselti farkına rağmen kırsal "
                    "senaryo şehir içi senaryosundan biraz daha iyi sonuç "
                    "vermiştir. Orman, sarp arazi ve görüş hattının kapalı "
                    "olduğu bölgelerde kırsal performansın azalması "
                    "beklenmektedir. Sonuçlar HPE P50 ve HPE P95 metrikleriyle "
                    "raporlanmaktadır.",
                    "**Open country.** A few points with wide reach: "
                    "intelligent transport and roadside units, base "
                    "station sites, rail and road infrastructure; these "
                    "are sparse, so in the simulation most units are on "
                    "the electricity distribution poles along the road, "
                    "with a solar panel and a battery. The "
                    "equipment is certified to TS EN 300 328 with "
                    "frequency hopping spread spectrum (FHSS) and listen "
                    "before talk (LBT); under FHSS the density limit is "
                    "100 mW/100 kHz, which a 1,625 MHz signal does not "
                    "reach, so 100 mW (20 dBm) e.i.r.p. holds. The rural "
                    "unit is the same "
                    "broadcast unit as the urban one: the amplified module "
                    "(E28-2G4M20S) and an outdoor 5 dBi rod antenna. Its "
                    "difference from the town unit is not the hardware but "
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
                    "**Kritik bölgeler.** Tüneller, metro ve istasyon alanları,"
                    " liman ve havalimanları ile afet lojistik alanlarını "
                    "kapsamaktadır. Yayın biriminde Qorvo'nun 6,5-8 GHz "
                    "bandında çalışan DWM3000 UWB modülü kullanılmaktadır; bu "
                    "modül, doğrudan görüş hattı koşullarında yaklaşık 10 cm "
                    "sınıfında mesafe ölçüm hassasiyetini hedeflemektedir. "
                    "Nihai konum hatası bu değere eşit değildir; yayın birimi "
                    "geometrisine, kalibrasyona, çok yollu yayılıma ve "
                    "engellere bağlı olduğundan saha testlerinde HPE P50 ve HPE"
                    " P95 metrikleriyle ayrıca ölçülecektir.",
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
            heading=_w("YERKON alıcı modülleri", "Receiver modules"),
            lines=(
                _w(
                    "**Yaya alıcı modülü.** Düşük güç tüketimi ve "
                    "taşınabilirlik esas alınarak tasarlanmıştır. Şehir içi ve "
                    "kırsal alanlarda yayın birimleri ve araç alıcısıyla aynı "
                    "yükselteçli EBYTE E28-2G4M20S (SX1280 yongalı) modülünü "
                    "kullanmaktadır; modülün gücü yazılımla ayarlanmakta ve "
                    "kısa mesafeli bağlantılarda daha düşük güçle yayın "
                    "yapılmaktadır. Tünel ve kapalı alanlarda Qorvo DWM3000 "
                    "modülü kullanılmaktadır. ESP32-S3 mikrodenetleyicisi "
                    "üzerinden kullanıcının akıllı telefonuyla bağlantı "
                    "kurmakta; sinyal kesildiğinde BNO085 atalet ölçüm birimi "
                    "ile son bilinen konumdan ölü hesaplama (dead reckoning) "
                    "yaparak devam etmektedir. Uydu sinyali mevcut olduğunda "
                    "konum bilgisini ATGM336H-5NR32 uydu konum modülünden de "
                    "almaktadır (GPS, GLONASS, BeiDou, QZSS). UWB için seramik "
                    "anten, 2,4 GHz için kart üzerinde çip anten, uydu konumu "
                    "için ise kart üzerinde Abracon PRO-OB-430 yama anten "
                    "bulunmaktadır. Türkiye'nin yükseklik haritası, kart "
                    "üzerindeki 4 GB'lık Zetta eMMC bellekte saklanmaktadır. "
                    "Konum, güneş ışığı altında da okunabilen ve yalnızca "
                    "görüntü değişirken güç tüketen 1,54 inç e-kâğıt ekranda "
                    "gösterilmektedir; kutunun arkasındaki 0,5 W güneş paneli "
                    "pili şarj etmektedir.",
                    "**Pedestrian.** Designed to draw little power and "
                    "fit in a pocket. In town and in open country it uses "
                    "the same amplified EBYTE E28-2G4M20S module (an "
                    "SX1280 chip) as the poles and the vehicle; its power "
                    "is set in software and turned down on a short link. "
                    "It uses the Qorvo DWM3000 in tunnels and indoors. An "
                    "ESP32-S3 connects it to a phone; if the signal drops, "
                    "a BNO085 motion sensor carries on from the last "
                    "position. While the satellites are there it also "
                    "takes a position from an ATGM336H-5NR32 satellite "
                    "positioning module (GPS, GLONASS, BeiDou, QZSS). A "
                    "ceramic antenna for UWB, a chip antenna on the board "
                    "for 2,4 GHz, and an Abracon PRO-OB-430 patch on the "
                    "board for the satellites. Türkiye's elevation model "
                    "is kept on the board, in 4 GB of Zetta eMMC storage. "
                    "It shows its position on a 1,54 inch "
                    "e-paper screen, "
                    "which stays readable in sunlight and draws power only "
                    "when the picture changes; a 0,5 W solar panel on the "
                    "back of the box tops up its battery.",
                ),
                _w(
                    "**Kara aracı alıcı modülü.** Artery AT32F403A "
                    "mikrodenetleyicisi üzerine kurulu olup LCD harita "
                    "ekranıyla desteklenmektedir. Uyumlu araçların CAN-Bus "
                    "hattına bağlanarak tekerlek hız sensörlerinden (odometri) "
                    "ve direksiyon açısından anlık veri almaktadır. Yaya "
                    "modülünde olduğu gibi iki telsiz taşımaktadır: geniş alan "
                    "kapsaması için yükselteçli EBYTE E28-2G4M20S (SX1280 "
                    "yongalı) modülü, kritik bölgeler için Qorvo DWM3000 "
                    "modülü. DWM3000 kendi dahili antenini kullanmakta; "
                    "E28-2G4M20S ise araç tavanındaki dış ortam tipi 5 dBi "
                    "çubuk antenle çalışmaktadır. Yaya alıcısındaki uydu konum "
                    "modülü, anteni ve 4 GB bellek bu modülde de bulunmaktadır.",
                    "**Road vehicle.** Built on an Artery AT32F403A with an LCD map "
                    "screen. It connects to the CAN bus of vehicles that "
                    "support one and takes live data from the wheel speed "
                    "sensors and the steering angle. Like the pedestrian "
                    "module it carries both radios: the amplified EBYTE "
                    "E28-2G4M20S module (an SX1280 chip) for wide areas "
                    "and the Qorvo DWM3000 for critical ones. The DWM3000 "
                    "uses its own on-board antenna; the E28-2G4M20S works "
                    "with an outdoor 5 dBi rod antenna on the vehicle's "
                    "roof. It has the pedestrian receiver's satellite "
                    "positioning module, its antenna and the 4 GB of "
                    "storage too.",
                ),
                _w(
                    "**Nesnelerin interneti alıcı modülü.** Kapalı ve yarı açık"
                    " alanlarda çalışan otonom robot filoları için "
                    "tasarlanmıştır. Robotlarda yaygın olarak kullanılan ROS "
                    "(Robot Operating System) yazılım çerçevesiyle doğrudan "
                    "haberleşmekte; tekerlek enkoderleri ve dahili atalet ölçüm"
                    " birimi sayesinde konum tahminini sürekli olarak "
                    "iyileştirmektedir. Depo ve fabrika senaryolarının çoğu "
                    "için DWM3000 UWB modülü yeterli olacaktır.",
                    "**Internet of things.** For robot fleets indoors and "
                    "in half open areas. It talks directly to ROS, the "
                    "framework most robots use, and keeps correcting its "
                    "position from how far the wheels have turned and its "
                    "own motion sensor. A DWM3000 is enough for most "
                    "warehouse and factory work.",
                ),
            ),
        ),
        Part(
            kind="points",
            heading=_w("Donanım ve fiyatlandırma", "The hardware and its price"),
            lines=(
                _w(
                    "1000 adetlik üretimde bir yayın biriminin maliyeti "
                    "yaklaşık 1400 TL, yaya alıcısının yaklaşık 2700 TL, kara "
                    "aracı alıcısının ise yaklaşık 3170 TL'dir. Her ürünün 1, "
                    "100 ve 1000 adetlik fiyat tablosu Maliyet sayfasında yer "
                    "almaktadır.",
                    "At a thousand units a broadcast unit is roughly 1400 "
                    "lira, a pedestrian receiver roughly 2700 lira and a "
                    "vehicle receiver roughly 3170 lira. Every product's price at one, a hundred and a "
                    "thousand is tabled on the Cost page.",
                ),
                _w(
                    "Her ürünün 1, 100 ve 1000 adetlik fiyatı, parçaların "
                    "satıcılarının kendi kademe fiyatları toplanarak "
                    "hesaplanmaktadır: telsiz modülü, mikrodenetleyici, anten, "
                    "besleme, koruma devreleri, muhafaza, pasif bileşenler, "
                    "baskılı devre kartı, dizgi ve lehim. İşletme modeli bin "
                    "birimlik bir ağ öngördüğünden karşılaştırma tablosunda "
                    "1000 adetlik fiyatlar kullanılmaktadır. Her parça, "
                    "satıcısı ve fiyatıyla birlikte Maliyet sayfasında "
                    "listelenmektedir.",
                    "Each product's price at one, a hundred and a thousand "
                    "is the sum of its parts at their sellers' own tier "
                    "prices: radio module, microcontroller, antenna, "
                    "supply, protection, box, passives, printed board, "
                    "assembly and soldering. The table prices at a thousand, because the "
                    "operating model assumes a network of a thousand "
                    "units. Every part, its seller and its price are on "
                    "the Cost page.",
                ),
                _w(
                    "Fiyatlar birimin tüm parçalarını kapsamaktadır: ana "
                    "bileşenler, besleme ve koruma devreleri, klemensler, anten"
                    " kablosu, muhafaza, direnç ve kondansatörler, baskılı "
                    "devre kartı, dizgi ve lehim. Test, kalibrasyon, "
                    "belgelendirme, vergi ve kargo giderleri bu tutarlara dahil"
                    " değildir; sahadaki montaj ise karşılaştırma tablosuna "
                    "ayrı bir kalem olarak eklenmektedir.",
                    "The prices cover every part of the unit: the main "
                    "parts, supply and protection, terminals, antenna "
                    "cable, box, the passive components, the printed "
                    "board, its assembly and soldering. Test, calibration, "
                    "certification, tax and shipping are outside them; "
                    "installation goes into the table as a line of its "
                    "own.",
                ),
                _w(
                    "Her iki alıcı da SX1280 yongalı EBYTE modülünü ve DWM3000 "
                    "modülünü birlikte taşımaktadır. Bu sayede aynı cihaz, açık"
                    " yolda şehir içi ve kırsal yayın birimleriyle, tünele "
                    "girildiğinde ise tünel birimleriyle ölçüm yapmakta; "
                    "kullanıcının herhangi bir işlem yapmasına gerek "
                    "kalmamaktadır.",
                    "Both receivers carry an EBYTE module with an SX1280 "
                    "chip and a DWM3000. That is "
                    "what lets one unit range against urban units on the "
                    "road and against tunnel units inside the bore, with "
                    "nothing switched over.",
                ),
            ),
        ),
        Part(
            kind="slides", slides=FINAL_PARTS,
            heading=_w("Nihai ürünün bileşenleri", "The final product's parts"),
        ),
    ),
)

RESEARCH = Page(
    slug="arge",
    slug_en="research",
    nav=_w("AR-GE", "Research"),
    title=_w("Araştırma soruları", "The research questions"),
    lead=_w(
        "YERKON projesi aşağıdaki altı araştırma sorusuna yanıt "
        "aramaktadır. Soruların tamamı araştırma süreci boyunca "
        "açık kalacak olup her birinin altında izlenecek yöntem "
        "açıklanmıştır.",
        "The project is looking for answers to six questions. None of "
        "them is closed, and under each one is what will be done.",
    ),
    parts=(
        Part(
            kind="points",
            heading=_w("Araştırma soruları", "Six questions"),
            lines=(
                _w(
                    "**Karasal yayınlar, araç sensörleri ve harita kısıtları "
                    "birleştirilerek GNSS olmadan kabul edilebilir düzeyde bir "
                    "konum hizmeti üretilebilir mi?** YERKON'un temel çalışma "
                    "mantığının uygulanabilirliği öncelikle şehir içinde test "
                    "edilecektir. Bu süreçte çevredeki modemlerin MAC "
                    "adreslerinden konum iyileştirme, baz istasyonları "
                    "yardımıyla üçgenleme ve görüntü işlemeyle konum "
                    "iyileştirme gibi yöntemlerin de sürece dahil edilmesi "
                    "değerlendirilecektir.",
                    "**If broadcasts from the ground, vehicle sensors and "
                    "the map are put together, does a good enough position "
                    "come out without the satellites?** It gets tried in a "
                    "city first. Using what nearby modems call themselves, "
                    "the distance to base stations and the picture from a "
                    "camera will be considered as well.",
                ),
                _w(
                    "**Mevcut ulaştırma altyapısına en az müdahaleyle "
                    "ölçeklenebilir bir sistem kurulabilir mi?** 12. Ulaştırma "
                    "ve Haberleşme Şûrası ve 2053 Ulaştırma ve Lojistik Ana "
                    "Planı, akıllı ulaşım sistemleri altyapısının "
                    "geliştirilmesini hedefler arasında saymaktadır. Yol kenarı"
                    " ünitelerinin ve trafik kontrol noktalarının sunduğu "
                    "enerji ve haberleşme kaynaklarının kullanılmasıyla yayın "
                    "birimlerinin en düşük maliyetle kurulmasına yönelik "
                    "yöntemler araştırılacaktır.",
                    "**Can a system be built by touching the existing "
                    "infrastructure as little as possible, and grown "
                    "later?** The 12th Transport and Communications "
                    "Council and the 2053 Transport and Logistics Master "
                    "Plan set developing intelligent transport "
                    "infrastructure as a goal. Using the power and the "
                    "line already at roadside units and traffic control "
                    "points is the way to make installation cheap.",
                ),
                _w(
                    "**TWR'nin ağ trafiği ve ölçeklenebilirlik dezavantajları, "
                    "TDoA tabanlı sistemlerin düşük alıcı etkileşimine "
                    "yaklaşacak ölçüde azaltılabilir mi?** Çift yönlü ölçümde "
                    "havada daha fazla mesaj dolaşmakta ve alıcı sayısı "
                    "arttıkça kanal erişimi için bekleme gerekmektedir. Tek "
                    "yönlü yayın yapan sistemler alıcıdan yanıt beklemediği "
                    "için bu yükü taşımamaktadır. İki yaklaşımın doğasındaki "
                    "ödünleşimler incelenecek; mesajlaşma yükünü azaltmak ve "
                    "eşzamanlı kullanıcı kapasitesini artırmak amacıyla TWR "
                    "CDMA ve yazılım tanımlı radyo (SDR) tabanlı yöntemler "
                    "sisteme eklenecektir. [TWR CDMA "
                    "makalesi](https://ieeexplore.ieee.org/abstract/document/11435291)",
                    "**Can two way ranging's two drawbacks be brought "
                    "down?** They are these: more messages travel through "
                    "the air, and receivers have to wait their turn as "
                    "their number grows. Systems that broadcast one way "
                    "expect no answer from the receiver, so they carry "
                    "neither cost. Methods built on TWR CDMA and software "
                    "defined radio will be added to the system to close "
                    "that gap. "
                    "[The TWR CDMA paper](https://ieeexplore.ieee.org/"
                    "abstract/document/11435291)",
                ),
                _w(
                    "**Konumlandırma hizmeti sunan bir altyapının güvenlik "
                    "gereksinimleri nelerdir ve bu gereksinimler nasıl "
                    "karşılanmalıdır?** Geliştirilecek çözümler iki tehdide "
                    "karşı test edilecektir: sahte bir yayın biriminin "
                    "kurulması ve izinsiz alıcıların sistemi meşgul etmesi. Bu "
                    "kapsamda modüllere donanımsal kriptografik hızlandırıcı "
                    "(ATECC608B) entegre edilecek; mesajların kaynağı ve "
                    "bütünlüğü ECDSA imzasıyla doğrulanacaktır.",
                    "**What does security ask of an infrastructure that "
                    "gives out position?** Answers get tried against two "
                    "threats: somebody setting up a fake broadcast unit, "
                    "and unauthorised receivers filling the system. Every "
                    "module gets a separate chip that does the encryption "
                    "(ATECC608B), and a signature verifies who each "
                    "message came from and that it was not altered on the "
                    "way.",
                ),
                _w(
                    "**GNSS'in aldatıldığını erken aşamada tespit eden bir "
                    "mekanizma geliştirilebilir mi?** GNSS aldatma "
                    "saldırılarında alıcı, teknik olarak tutarlı ve yüksek "
                    "güven düzeyine sahip görünen ancak gerçekte yanlış olan "
                    "bir konum ve hız bilgisi üretebilmektedir. YERKON, "
                    "GNSS'ten tamamen bağımsız çalıştığı için bir bütünlük "
                    "referansı olarak kullanılabilecektir. GNSS çıktısı ile "
                    "YERKON çözümü sürekli olarak karşılaştırılacak; "
                    "mekanizmanın etkinliği şu ölçütlerle değerlendirilecektir:"
                    " hata dağılımının ortancası (P50), yüzde 95'lik değeri "
                    "(P95) ve en büyük hata, konum sürekliliği, sinyal "
                    "kesintisi sonrasında yeniden yakınsama süresi "
                    "(reconvergence time), yanlış alarm oranı ve aldatma ile "
                    "karıştırma tespit oranı.",
                    "**Can a way be built to notice early that GNSS is "
                    "being spoofed?** "
                    "Under a spoofing attack the receiver gives a "
                    "position and speed that look flawless from outside "
                    "and are wrong. YERKON runs entirely apart from the "
                    "satellites, so it can serve as a reference for "
                    "integrity. The two positions will be compared "
                    "continuously, and the mechanism will be measured by "
                    "these criteria: the median error (P50), "
                    "the ninety fifth percentile (P95) and the worst case, "
                    "whether the position arrives without gaps, how long "
                    "reconvergence takes after the signal drops, how often "
                    "an alarm fires for nothing, and how often spoofing "
                    "and jamming are caught.",
                ),
                _w(
                    "**Kurulum işlemleri en pratik hâle nasıl getirilebilir?** "
                    "Kurulum sürecinin uzmanlık gerektirmeyen bir yapıya "
                    "kavuşturulması amacıyla cihazlarla bütünleşik saha "
                    "asistanı yazılımları geliştirilecektir. Örneğin afet veya "
                    "askerî durumlarda geçici bir YERKON ağı kuracak personel, "
                    'alıcı ekranındaki "Optimum sinyal için 120 derece yönünde '
                    '50 metre ilerleyin" gibi yönlendirmeleri adım adım takip '
                    "ederek yayın birimlerini yerleştirebilecektir.",
                    "**How can installation be made as practical as "
                    "possible?** The aim "
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
            heading=_w("Uygulama süreci", "How it will be carried out"),
            lines=(
                _w(
                    "Uygulama sürecinin ilk adımında, projeye özel YERKON "
                    "kartları geliştirilmeden önce haberleşme mimarisinin ve "
                    "temel sistem bileşenlerinin hızlı ve düşük maliyetli "
                    "biçimde sınanabilmesi amacıyla ekibin hâlihazırda sahip "
                    "olduğu donanımlardan yararlanılacaktır. Bu donanımlar; "
                    "yayın birimi ile alıcı arasındaki haberleşmenin, paket ve "
                    "protokol yapısının, saha kapsamasının, hareketli alıcı "
                    "davranışının, GNSS ile karasal konum çıktılarının "
                    "karşılaştırılmasının ve radyo ortamının deneysel olarak "
                    "incelenmesinde kullanılacaktır. Mevcut donanımla "
                    "konumlandırma ve şifreleme mantığı doğrulanacak; "
                    "T1000-E'nin LR1110 yongasıyla HPE ve VPE ölçümleri de "
                    "yapılabilecek, ancak bu sonuçlar nihai yayın birimleriyle "
                    "birebir karşılaştırılabilir olmayacaktır.",
                    "Before the YERKON boards are made, the communication "
                    "design and the basic parts will be tried quickly and "
                    "cheaply on hardware the team already has: how the "
                    "unit and the receiver talk, the packet and protocol "
                    "layout, coverage in the field, how a moving receiver "
                    "behaves, the satellite position against the "
                    "terrestrial one, and the radio environment. This "
                    "hardware will verify the positioning and signing "
                    "logic; the LR1110 chip in the T1000-E can also take "
                    "HPE and VPE measurements, but the results will not be "
                    "fully comparable with the final units.",
                ),
                _w(
                    "Sonraki adımda, projeye özel kartlar üretildikten sonra "
                    "seçilecek bir ulaşım koridoruna 10-15 yayın birimi "
                    "kurulacaktır. Araç, el tipi ve sabit alıcı prototipleri "
                    "açık alan, tünel, kentsel kanyon ve kapsama sınırı "
                    "koşullarında test edilecektir.",
                    "In the next step, once the project's own boards are "
                    "made, between 10 and 15 units will go up along one "
                    "transport corridor. Vehicle, handheld and fixed "
                    "receiver prototypes will be tried in the open, in a "
                    "tunnel, between tall buildings and where coverage "
                    "runs out.",
                ),
                _w(
                    "Açık alan testlerinde referans konum (yer gerçeği) olarak "
                    "RTK-GNSS, GNSS erişiminin bulunmadığı tünel ve kapalı "
                    "alanlarda ise önceden ölçülmüş referans noktaları ve "
                    "güzergâh kullanılacaktır.",
                    "In the open, the true position to compare against "
                    "comes from RTK-GNSS. In tunnels and indoors, where "
                    "the satellites do not reach, it comes from points and "
                    "a route surveyed beforehand.",
                ),
                _w(
                    "Yatay konum hatası için hedef, P50 değerinin 5 metrenin ve"
                    " P95 değerinin 10 metrenin altında kalmasıdır.",
                    "The target: half the errors under 5 metres, and 95 "
                    "per cent of them under 10.",
                ),
                _w(
                    "Yasal ve operasyonel güvenlik nedeniyle testlerde gerçek "
                    "bir karıştırıcı (jammer) kullanılmayacaktır. Karıştırıcı, "
                    "çevredeki diğer telsiz sistemlerinde zararlı "
                    "elektromanyetik girişime yol açmaktadır; ruhsatsız telsiz "
                    "cihazlarının zararlı girişime neden olmadan kullanılmasını"
                    " şart koşan [Frekans Tahsisinden Muaf Telsiz Cihaz ve "
                    "Sistemleri Hakkında "
                    "Yönetmelik](https://www.resmigazete.gov.tr/eskiler/2018/11/20181127-18.htm)"
                    " (Madde 5) ve 5809 sayılı Elektronik Haberleşme Kanunu "
                    "çerçevesinde bu kullanım mevzuata aykırıdır. Ayrıca "
                    "karıştırıcı, test alanının çevresindeki havacılık, acil "
                    "durum ve haberleşme hizmetlerinin konum bilgisini bozarak "
                    "can ve mal güvenliğini tehlikeye atabilir. Bu nedenle "
                    "karıştırma ve aldatma senaryoları; uydu sinyalinin "
                    "kontrollü biçimde kesilmesi, önceden kaydedilmiş "
                    "sinyallerin yeniden oynatılması ve saldırıların "
                    "laboratuvar ortamında benzetilmesi yoluyla sınanacaktır.",
                    "No real jammer will be used: it is both illegal and "
                    "dangerous. Instead the satellite signal will be cut "
                    "under control, recorded signals will be played back, "
                    "and attacks will be imitated in a laboratory.",
                ),
            ),
        ),
        Part(
            kind="slides", slides=PILOT_PARTS,
            heading=_w("Uygulama sürecinin ilk adımında kullanılacak donanım", "Hardware for the first step"),
        ),
    ),
)

VALUE = Page(
    slug="fayda",
    slug_en="benefits",
    nav=_w("Fayda", "What it is for"),
    title=_w("Projenin sektöre faydası", "Who it is for"),
    lead=_w(
        "YERKON, konum bilgisinin hayati önem taşıdığı ancak uydu "
        "sinyalinin kesildiği, zayıfladığı veya güvenilirliğini "
        "yitirdiği durumlarda ulaşımın ve konuma bağlı hizmetlerin "
        "kesintisiz sürmesini amaçlamaktadır. Projenin ticarileşme "
        "potansiyeli sayfanın sonunda açıklanmıştır.",
        "So that transport and the services that need a position do not "
        "stop where position "
        "is vital and the satellite signal is cut, weakened or no longer "
        "trusted; how it is commercialised closes the page.",
    ),
    parts=(
        Part(
            kind="points",
            heading=_w("Sahadaki faydalar", "In the field"),
            lines=(
                _w(
                    "**Acil yardım ve afet yönetimi.** 112, AFAD ve diğer "
                    "ekiplerin konumu tünellerde, kapalı alanlarda, yüksek "
                    "binalar arasında ve afet bölgelerinde izlenmeye devam "
                    "edilebilmektedir. Telsiz veya şebeke bağlantısı "
                    "bulunmadığında cihaz, üzerindeki harita ve sensörlerle "
                    "konum üretmeyi sürdürmektedir.",
                    "**Emergency services and disasters.** It "
                    "keeps ambulance, disaster response and other teams "
                    "visible in tunnels, indoors, between tall buildings "
                    "and in disaster areas. Where the radio or the network "
                    "will not hold, the map and sensors on the device keep "
                    "giving a position.",
                ),
                _w(
                    "**Karayolu, kargo ve toplu taşıma.** Kamu araçları, "
                    "otobüsler, tehlikeli madde taşıyan tankerler ve değerli "
                    "yükler için uydudan bağımsız ikinci bir takip imkânı "
                    "sağlanmaktadır. Sistem, tünel ve otoyol işletmelerinde "
                    "konum sürekliliğinin korunmasına katkı sunmaktadır.",
                    "**Road, freight and public transport.** Public "
                    "vehicles, buses, tankers carrying dangerous goods and "
                    "valuable loads gain a second way of being tracked "
                    "that does not look at the satellites. In tunnel and "
                    "motorway operations it helps keep the position "
                    "continuous.",
                ),
                _w(
                    "**Karıştırma ve aldatma haritası.** Uydunun verdiği konum "
                    "ile YERKON'un hesapladığı konum arasındaki tutarsızlık bir"
                    " olay olarak kaydedilmektedir. Olayların merkezde "
                    "toplanmasıyla Bakanlık, ülke genelinde karıştırma ve sahte"
                    " sinyal olaylarının yerini ve zamanını gösteren bir "
                    "haritaya sahip olacaktır.",
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
            heading=_w("Stratejik katkılar", "Strategic"),
            lines=(
                _w("Konum hizmetlerinin tek bir yabancı teknolojiye "
                   "bağımlılığı azaltılmaktadır.",
                   "Position stops depending on one foreign technology."),
                _w("Hayati hizmetlerde tek bir bileşenin arızalanmasıyla tüm "
                   "sistemin durması riski (tek hata noktası) azaltılmaktadır.",
                   "It gets less likely that one thing breaking stops "
                   "everything in a critical service."),
                _w("Kriz durumlarında devreye alınabilecek, yer tabanlı ikinci"
                   " bir konum katmanı hazır bulunmaktadır.",
                   "In a crisis a second layer of position, working from "
                   "the ground, is already there."),
                _w("Sınır bölgeleri ve yoğun ulaşım koridorları kesintilere "
                   "karşı daha dayanıklı hâle gelmektedir.",
                   "Border regions and busy corridors hold up better "
                   "against interruption."),
                _w("Böyle bir sistemin tasarımı, yazılımı ve entegrasyonuna "
                   "ilişkin bilgi birikimi ülke içinde kalmaktadır.",
                   "The knowledge of how to build, write and put together "
                   "such a system stays in the country."),
            ),
        ),
        Part(
            kind="points",
            heading=_w("Kurumsal ve akademik katkılar",
                       "Institutional and academic"),
            lines=(
                _w("Hizmetlerin uydu sistemlerine bağımlılık düzeyi ortaya "
                   "konmakta ve olaylar ülke haritası üzerinde kayıt altına "
                   "alınmaktadır.",
                   "It comes out which service depends on the satellites "
                   "how much, and the events go onto a national map."),
                _w("Kurumlar ortak bir olay verisi üzerinden çalışabilmekte; "
                   "hizmet kalitesine ilişkin gereksinimler bu veriye "
                   "dayanarak tanımlanabilmektedir.",
                   "Institutions look at the same event data, and how good "
                   "the service has to be can be defined from it."),
                _w("Birden fazla sensörden toplanan ve uydu sinyalinin "
                   "kesildiği ve aldatıldığı durumları da içeren bir veri "
                   "kümesi oluşturulmaktadır.",
                   "What is left is a dataset gathered from several "
                   "sensors, covering satellites cut off and satellites "
                   "fooled."),
                _w("Konum hesaplama yöntemleri yurt içinde geliştirilmekte; "
                   "üniversite, kamu ve sanayi ortak bir çalışma alanında "
                   "buluşmaktadır.",
                   "The methods that work out position get written here, "
                   "with universities, the state and industry on the same "
                   "work."),
            ),
        ),
        Part(
            kind="text",
            heading=_w("Projenin ticarileşme potansiyeli", "Commercialisation"),
            lines=(
                _w("YERKON'un temel amacı kamu değeri üretmektir. Bu bölümde "
                   "işletme maliyetini karşılayacak gelir kaynakları, ilk "
                   "ticari adımlar ve ürün ailesi açıklanmaktadır.",
                   "YERKON's aim is public value. What follows is where "
                   "the income to meet the running cost can come from, "
                   "the first commercial steps and the products to be "
                   "sold."),
            ),
        ),
        Part(
            kind="text",
            sub=True,
            heading=_w("Sürdürülebilir işletme modeli",
                       "How it pays for itself"),
            lines=(
                _w(
                    "Amaç kamu altyapısının özelleştirilmesi değildir. Sistemin"
                    " çekirdeği kamuda kalacak; bu çekirdek üzerine eklenecek "
                    "denetimli hizmetler işletme giderlerini karşılayacaktır.",
                    "The model is not privatising public infrastructure. "
                    "The aim is controlled extra services on top of a "
                    "public core, enough to cover what running it costs.",
                ),
                _w(
                    "İlk kurulum alanı olarak GNSS erişiminin yapısal olarak "
                    "sınırlı olduğu tüneller ve kritik ulaşım koridorları "
                    "öngörülmektedir. Bu alanlarda ihtiyaç açıkça "
                    "tanımlanabilmekte ve sonuçlar denetimli biçimde "
                    "ölçülebilmektedir; dolayısıyla ilk kurulumun kapsamı "
                    "bellidir. Elde edilen doğruluk, kapsanan alan, hizmet "
                    "sürekliliği, gereken birim sayısı ve mevcut altyapının ne "
                    "ölçüde kullanılabildiği uygulama sürecinde netleşecektir.",
                    "The first area is tunnels and critical transport "
                    "corridors, where satellite access is structurally "
                    "limited. "
                    "There the need can be stated plainly and performance "
                    "measured under control, so the boundaries of a first "
                    "deployment are clear. Carrying it out is what settles "
                    "accuracy, coverage, service continuity, how dense the "
                    "units have to be, and how much of the existing "
                    "infrastructure can be reused.",
                ),
                _w(
                    "Kısa vadede uygulama süreci ekibin hâlihazırda sahip "
                    "olduğu donanımla başlayacak; yerli yazılım ve haberleşme "
                    "protokolleri geliştirilecek, ilk yayın ve alıcı kartları "
                    "tasarlanacaktır. Ulaştırma ve Altyapı Bakanlığı'nın "
                    "desteğinin sağlanması durumunda, akıllı ulaşım sistemleri "
                    "kurulu olan seçilmiş bir yol kesiminde yayın birimlerinin "
                    "mevcut kabin ve direklere yerleştirildiği ortak bir saha "
                    "çalışması yürütülebilecektir. Orta vadede yerli gömülü "
                    "sistem ve telsiz firmalarıyla ortaklık kurulması, savunma "
                    "ve haberleşme ekosistemiyle birlikte donanım "
                    "geliştirilmesi ve kritik bileşenlerin en az iki farklı "
                    "kaynaktan tedarik edilmesi hedeflenmektedir.",
                    "In the short term the work starts on off-the-shelf "
                    "hardware the team already has, while the domestic software and "
                    "the rules the radios follow get written and the first "
                    "broadcast and receiver boards are designed. With the "
                    "Ministry of Transport and Infrastructure's support, if "
                    "it can be had, a joint field trial could fit the units "
                    "to existing cabinets and poles on a chosen stretch of "
                    "road already fitted with intelligent transport "
                    "systems. In the "
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
            heading=_w("Uzun vadeli hedefler", "In the long term"),
            lines=(
                _w("Komşu ve gelişmekte olan ülkelere karasal konumlandırma "
                   "çözümü sunulması.",
                   "A terrestrial positioning answer for neighbouring and "
                   "developing countries."),
                _w("Kritik koridor ve liman odaklı bölgesel kurulumların "
                   "yapılması.",
                   "Regional installations around critical corridors and "
                   "ports."),
                _w("YERKON protokolünün ve alıcı ailesinin lisanslanması.",
                   "Licensing the YERKON protocol and the receiver "
                   "family."),
                _w("Afet ve GNSS karıştırma riski yüksek ülkelere kurulum ve "
                   "entegrasyon hizmeti verilmesi.",
                   "Installation and integration for countries at high "
                   "risk of disaster and of GNSS jamming."),
                _w("Yan çıktı olarak yerli konumlandırma ve navigasyon "
                   "ekosisteminin gelişmesine katkı sağlanması.",
                   "A side output: a domestic positioning and navigation "
                   "industry growing up around it."),
            ),
        ),
        Part(
            kind="points",
            sub=True,
            heading=_w("Ürün ailesi", "The products"),
            lines=(
                _w(
                    "**Altyapı ürünleri.** Şehir içi ve kırsal yayın birimi "
                    "(aynı donanım; kırsalda güneş paneli ve akü ile), kritik "
                    "bölge yayın birimi ve güvenli anahtar ile yayın birimi "
                    "yönetim sistemi.",
                    "**Infrastructure.** The urban and rural broadcast "
                    "unit (one set of hardware; in open country with a solar panel "
                    "and a battery), the critical area broadcast unit, and "
                    "the system that manages the units and their keys.",
                ),
                _w(
                    "**Kullanıcı ürünleri.** Kara aracı alıcısı, yaya alıcısı "
                    "(taşınabilir saha alıcısı) ve nesnelerin interneti "
                    "alıcısı. İlerleyen aşamalarda insansız hava aracı "
                    "entegrasyon modülü ile demiryolu ve denizcilik "
                    "alıcılarının geliştirilmesi planlanmaktadır.",
                    "**User.** The vehicle receiver, the pedestrian receiver "
                    "(a portable field receiver), and the internet of "
                    "things receiver. "
                    "Later products: an integration module for unmanned "
                    "aircraft, and a receiver for rail and maritime.",
                ),
                _w(
                    "**Yazılım ürünleri.** Merkezî yönetim paneli, GNSS "
                    "bütünlük ve olay haritası, filolar ve kritik altyapı için "
                    "arayüzler, analiz ve raporlama yazılımı ile çevrimdışı "
                    "yayın birimi konum haritası.",
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
    slug_en="results",
    nav=_w("Karşılaştırma", "Comparison"),
    title=_w("Diğer sistemlerin yanında YERKON",
             "YERKON beside the other systems"),
    lead=_w(
        "YERKON ve diğer on konumlandırma sistemi, aynı sütunlarla yan "
        "yana. Koyu zeminli satırlar YERKON'un simülasyon sonuçları; "
        "diğerleri o sistemlerin kendi kaynaklarının yayımladığı değerler.",
        "YERKON and ten other positioning systems side by side under the "
        "same columns. The shaded rows are YERKON's simulation results; the "
        "rest are what those systems' own sources publish.",
    ),
    parts=(
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
                        "geçerli bir sonuç verdiği. Yalnızca simülasyona giren "
                        "aksaklıkları sayar; bir hizmet garantisi "
                        "değildir.",
                        "What share of the attempts to work out a "
                        "position gave a valid one. It counts only the "
                        "failures in the simulation, and is not a promise about "
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
                        "verilen alana bölündü; birimin bütün parçaları ve "
                        "montaj dahil.",
                        "Unit hardware cost divided by the service area; "
                        "every part of the unit and the fitting included.",
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
            heading=_w("Tabloyu okurken",
                       "Reading the table"),
            lines=(
                _w(
                    "**Her sayının açıklaması tabloda.** Bir sayıya ne "
                    "yapıldığı, satırın sonundaki düğmeyle açılan kutuda ve "
                    "sayfanın sonundaki dipnotlarda yazıyor. Boş hücre, o "
                    "kaynağın bu sütuna uyan bir şey yayımlamadığı anlamına "
                    "geliyor.",
                    "**Every figure is explained in the table.** What was "
                    "done to a cell is in the box the button at the end of "
                    "its row opens and in the notes at the foot of the page; "
                    "an empty cell means the source publishes nothing that "
                    "fits that column.",
                ),
                _w(
                    "**Tünel satırının maliyeti kilometre başına, "
                    "diğerleri kilometrekare başına.** 12 m genişliğinde "
                    "2 km'lik bir tünel bir km²'nin ellide biri kadar yer "
                    "kaplar; alana bölünce sayı, tünel pahalı olduğu için "
                    "değil payda küçük olduğu için büyür. Tünel bir "
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
        Part(kind="shows", shows="published"),
        Part(kind="shows", shows="landscape",
             heading=_w("Maliyet ve doğruluk", "Cost and accuracy")),
        Part(
            kind="shows", shows="accuracy",
            heading=_w("Doğruluk yan yana", "Accuracy side by side"),
        ),
        Part(kind="shows", shows="cost"),
    ),
)

SIMULATION = Page(
    slug="simulasyon",
    slug_en="simulation",
    nav=_w("Simülasyon", "The simulation"),
    title=_w("Simülasyon nasıl çalışıyor", "How the simulation works"),
    lead=_w(
        "Simülasyon, yayın birimlerini Ankara'nın gerçek arazisine "
        "yerleştirir ve bir alıcıyı yol boyunca yürütür. Alıcı her adımda "
        "birimlere olan mesafeyi ölçer ve konumunu bu ölçümlerden hesaplar; "
        "hesaplanan konum gerçek konumla karşılaştırılarak hata bulunur. "
        "Sahada yapılmış bir ölçüm değildir.",
        "The simulation places the broadcast units on Ankara's real terrain "
        "and moves a receiver along the road. At every step the receiver "
        "measures its distance to the units and works out its position from "
        "those measurements; the error is found by comparing that position "
        "with the true one. It is not a field measurement.",
    ),
    parts=(
        Part(
            kind="picture",
            picture="simulator.webp",
            lines=(_w(
                "Şehir içi satırı, simülasyonu tamamlanmış hâliyle: "
                "Kızılay'ın gerçek arazisi, aydınlatma direklerindeki yayın "
                "birimleri ve zemine boyanmış kapsama. Renkler o noktada kaç "
                "birimin duyulabildiğini gösteriyor; konum hesaplamak için en"
                " az dördü gerekiyor. Sağdaki panel o sekmenin kendi sonucu; "
                "gölgelemenin sekiz ayrı çekilişinin birleşimi.",
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
                    "Üç satırın hepsi Ankara yakınındaki gerçek arazi "
                    "üzerinde duruyor. Arazi Copernicus'un 30 m'lik yükseklik"
                    " modelinden bir kez indirildi ve pakete gömüldü; depoyu "
                    "kopyalayan biri tabloyu internete bağlanmadan yeniden "
                    "üretebilir.",
                    "All three rows stand on real ground near Ankara, "
                    "fetched once from the Copernicus 30 m DEM and baked "
                    "into the package, so a clone reproduces the table "
                    "without touching the network.",
                ),
                _w(
                    "Şehir Kızılay: bir kenarı üç kilometre, en alçak ve en "
                    "yüksek noktası arasında 91 metre var. Açık arazi Polatlı"
                    " ovası: bir kenarı yirmi kilometre, arada 486 metre. "
                    "Tünel, Kızılcahamam'daki dağların içinden geçen gerçek, "
                    "iki kilometrelik bir tünel.",
                    "The city is Kızılay: three kilometres on a side, "
                    "with 91 metres between its lowest and highest point. "
                    "The open country is the Polatlı plain, twenty "
                    "kilometres on a side with 486 metres of it. The "
                    "tunnel is a real two kilometre bore through the "
                    "mountains at Kızılcahamam.",
                ),
                _w(
                    "Hiçbir yerde \"düz zemin\" seçeneği yok. Düz bir yüzey, "
                    "simülasyonun çizebileceği en tarafsız arazi değil, en "
                    "elverişli arazidir: sonucu olduğundan iyi gösterirdi.",
                    "Nowhere is there a \"flat ground\" option. A flat "
                    "surface is not the most neutral terrain the simulation can "
                    "draw, it is the most favourable one: it would make "
                    "the result look better than it is.",
                ),
            ),
        ),
        Part(
            kind="points",
            heading=_w("Menzile tek bir hesap karar verir",
                       "One calculation decides the range"),
            lines=(
                _w(
                    "Kodun hiçbir yerinde \"azami menzil budur\" diyen bir sayı"
                    " yok. Menzil, sinyalin yolda ne kadar zayıfladığının "
                    "hesabından çıkar. Aynı hesap iki şeye birden karar "
                    "verir: bağlantının kurulup kurulmadığına ve kurulduysa "
                    "ne kadar hassas ölçtüğüne.",
                    "Nowhere in the code is there a number saying \"the "
                    "maximum range is this\". Range comes out of working "
                    "out how much the signal weakens on its way. The same "
                    "calculation decides two things at once: whether the "
                    "link holds, and how precisely it measures when it "
                    "does.",
                ),
                _w(
                    "Sinyal alıcıya iki yoldan ulaşır: doğrudan ve zeminden "
                    "sekerek. Belli bir mesafeden sonra bu ikisinin adımı "
                    "kayar ve birbirini zayıflatırlar. Bu mesafe anten "
                    "yüksekliğiyle büyür; birimi alçağa takmak menzilden "
                    "götürür.",
                    "The signal reaches the receiver two ways: directly, "
                    "and bouncing off the ground. Past a certain distance "
                    "those two fall out of step and weaken each other. "
                    "That distance grows with antenna height, so mounting "
                    "a unit low costs range.",
                ),
                _w(
                    "Sinyal engellerin üzerinden bükülür ve bunu yaparken "
                    "zayıflar. Hesap, yoldaki en kötü tek engele değil bütün "
                    "araziye bakar (ITU-R P.526-15 §4.5.2, delta-Bullington)."
                    " Kızılay'daki bir bağlantının önünde ortancada üç, en "
                    "kötü durumda on altı engel var.",
                    "The signal bends over obstacles and weakens doing "
                    "it. The calculation looks at the whole terrain rather "
                    "than the worst single obstacle on the path (ITU-R "
                    "P.526-15 §4.5.2, delta Bullington). A link across "
                    "Kızılay has three obstacles in front of it at the "
                    "median, sixteen at the worst.",
                ),
                _w(
                    "Arazi her on metrede bir okunur. Sabit 64 noktada "
                    "okunsaydı 6,9 km'lik bir kırsal bağlantı 108 metrede bir"
                    " okunmuş olurdu; aradaki tümsekler atlanınca kayıp, "
                    "doğrusu 37,60 dB iken 31,28 dB çıkardı.",
                    "The terrain is read every ten metres. Read at a "
                    "fixed 64 points, a 6,9 km rural link would be read "
                    "every 108 metres, and skipping the rises in between "
                    "would put the loss at 31,28 dB where the answer is "
                    "37,60.",
                ),
                _w(
                    "Bir bağlantıda bu iki kaybın toplamı değil, büyük olanı "
                    "sayılır. İkisi de aynı arazinin aynı bağlantıya "
                    "yaptığını anlatır; toplamak aynı tepeyi iki kez saymak "
                    "olur.",
                    "A link counts the larger of those two losses, not "
                    "their sum. Both describe what the same terrain does "
                    "to the same link, and adding them would count the "
                    "same hill twice.",
                ),
                _w(
                    "Bunların üstüne gölgeleme biner: aynı uzaklıktaki iki "
                    "bağlantı, arada ne durduğuna göre farklı çıkar. Yol "
                    "açıkken 4 dB, kapalıyken 7,8 dB kadar (3GPP TR 38.901). "
                    "Rastgele olduğu için hesap sekiz kez tekrarlanır ve "
                    "sekizinin bütün sonuçları birlikte okunur.",
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
            heading=_w("Mesajlar ve konum",
                       "The messages and the position"),
            lines=(
                _w(
                    "Mesafe hesaplanmaz, ölçülür. İki telsiz karşılıklı mesaj"
                    " gönderir; SX1280'de bir ölçüm alışverişi, Göndermeden "
                    "Önce Dinle (LBT) kuralının istediği %5 bekleme dahil "
                    "33,4 milisaniye sürer.",
                    "A distance is measured rather than calculated. Two "
                    "radios send messages back and forth; on the SX1280 "
                    "one ranging exchange takes 33,4 milliseconds, "
                    "including the 5 % rest listen before talk (LBT) "
                    "asks for.",
                ),
                _w(
                    "On iki birimle sırayla ölçüşmek 401 milisaniye sürer. "
                    "100 km/sa giden bir araç bu sürede 11,1 metre yol alır; "
                    "yani bir turdaki ölçümler tek bir ana ait değildir. "
                    "Hesap da öyleymiş gibi davranmaz.",
                    "Measuring against twelve units in turn takes 401 "
                    "milliseconds. A car doing 100 km/h covers 11,1 metres "
                    "in that time, so the measurements in one round do not "
                    "belong to one instant. The calculation does not "
                    "pretend they do.",
                ),
                _w(
                    "Konumu hesaplayan kod aracın gerçekte nerede olduğunu "
                    "hiç görmez. Yalnızca şunları görür: ölçülen mesafe, "
                    "birimin kurulumda ölçülen konumu, ölçümün zamanı ve o "
                    "ölçüme ne kadar güvenildiği.",
                    "The code that works out the position never sees "
                    "where the vehicle really is. It sees only these: the "
                    "measured distance, the unit's position as surveyed at "
                    "installation, the time of the measurement, and how "
                    "much that measurement is trusted.",
                ),
                _w(
                    "Yol kenarına dizilmiş birimler aşağı yukarı aynı "
                    "yükseklikte durduğu için düşey konumu mesafelerden "
                    "ölçmek zordur. Filtre bu yüzden yolun yüksekliğini "
                    "alıcıdaki yükseklik haritasından bir ölçüm olarak alır; "
                    "haritanın 2,43 m'lik hatası yol boyunca parça parça "
                    "çekilir. VPE sütunu bunun sonucudur.",
                    "Units strung along a roadside are all at much the "
                    "same height, which leaves the vertical hard to "
                    "measure from ranges. The filter therefore takes the "
                    "road's height from the receiver's elevation map as a "
                    "measurement, with the map's error of 2,43 m drawn in "
                    "patches along the "
                    "road. The VPE column is the result.",
                ),
            ),
        ),
        Part(kind="shows", shows="spread"),
        Part(
            kind="points",
            heading=_w("Ortalama almanın gidermediği üç hata",
                       "Three errors that averaging will not remove"),
            lines=(
                _w(
                    "**Önü kapalı bir bağlantı, olduğundan uzun ölçer.** "
                    "Sinyal engelin çevresinden dolaşır ve ölçüm bu uzun yolu"
                    " sayar. Hata hep aynı yöne gider; bu yüzden daha sık "
                    "ölçüp ortalama almak onu gidermez.",
                    "**A blocked link measures longer than it is.** The "
                    "signal goes around the obstacle and the measurement "
                    "counts that longer way. The error always goes the "
                    "same way, so measuring more often and averaging does "
                    "not remove it.",
                ),
                _w(
                    "**Birimin konumu kurulumda yanlış ölçüldüyse yanlış "
                    "kalır.** Bu hata her birim için bir kez çekilir ve "
                    "sonuna kadar taşınır. Tünelde hataların ortancası "
                    "kusursuz bir ölçümle 0,12 m; 15 cm'lik ölçüm hatasıyla "
                    "bunun yaklaşık beş katı. Konum, birimlerin yerinin "
                    "ölçümünden daha iyi olamaz.",
                    "**If a unit's position is surveyed wrong at "
                    "installation, it stays wrong.** It is drawn once per "
                    "unit and carried to the end. In the tunnel the median "
                    "error is 0,12 m with a perfect survey and about five "
                    "times that with 15 cm of survey error. A position "
                    "cannot be better than the survey of the units.",
                ),
                _w(
                    "**Kaybolan mesaj ölçüm vermez.** 2,4 GHz bandı kablosuz "
                    "ağlarla ortak, bu yüzden kalabalık. Mesajların şehirde "
                    "%15'i, açık yolda %5'i kaybolur, tünelde hiçbiri.",
                    "**A lost message gives no measurement.** The 2,4 GHz "
                    "band is shared with wireless networks, so it is "
                    "crowded. 15% of messages are lost in the city, 5% on "
                    "the open road, none in the tunnel.",
                ),
            ),
        ),
        Part(
            kind="points",
            heading=_w("Simülasyonun dışında kalanlar", "What is left out"),
            lines=(
                _w(
                    "Aracın hareket sensörü ve tekerlek turu dışarıda "
                    "bırakıldı. Filtre yalnız telsiz ölçümlerini ve yükseklik"
                    " haritasından gelen yüksekliği birleştirir.",
                    "The vehicle's motion sensor and wheel turns are left "
                    "out. The filter combines only the radio measurements "
                    "and the height from the elevation map.",
                ),
                _w(
                    "Sinyalin bina duvarlarından sekip birkaç yoldan gelmesi "
                    "(çok yollu yayılım) simülasyona ayrıca katılmadı; "
                    "simülasyonda zeminden sekme ve önü kapalı bağlantının "
                    "uzun okunması var. Telsizin kendi gürültüsü ve "
                    "alışveriş sırasında saatin kayması da simülasyonda "
                    "var.",
                    "The signal arriving by several paths after bouncing "
                    "off building walls (multipath) is not in the "
                    "simulation on its own; the simulation has the bounce "
                    "off the ground and the long reading of a blocked link. "
                    "The radio's own noise and the clock drifting during "
                    "the exchange are in the simulation too.",
                ),
                _w(
                    "Ağaçlar simülasyonda yok. Zemin ve binalar gerçek "
                    "veriden geliyor, ama ağaçlar için ayrı bir kayıp "
                    "hesaplanmıyor. Ağacın arkasındaki bir bağlantı gerçekte "
                    "daha zayıf olabilir.",
                    "Trees are not in the simulation. The ground and the "
                    "buildings come from real data, but no separate loss "
                    "is worked out for trees. A link behind a tree may be "
                    "weaker in reality.",
                ),
                _w(
                    "Tünel kaybı, gerçek bir karayolu tünelinde 2,8-5 GHz'de "
                    "ölçülmüş bir modelden gelir ve 6,5 GHz'e taşındı; 6,5 "
                    "GHz'de ölçülmedi.",
                    "The tunnel loss comes from a model measured in a real "
                    "road tunnel at 2,8 to 5 GHz and carried to 6,5 GHz; "
                    "it was not measured at 6,5 GHz.",
                ),
                _w(
                    "Güvenlik katmanı da simülasyona katılmadı: imza doğrulama, "
                    "anahtar yönetimi ve birimlerin merkeze gönderdiği "
                    "yaşam sinyalleri simülasyonda yok.",
                    "The security layer is not simulated either: signature "
                    "checking, key management and the \"still working\" "
                    "messages the units send the centre are not in the "
                    "simulation.",
                ),
            ),
        ),
        Part(
            kind="text",
            heading=_w("Zaten yüksek olan yerler",
                       "Places that are already high"),
            lines=(
                _w(
                    "Şehir içi ve kırsal satırlarda yayın birimleri bir "
                    "ızgaraya değil, bir yerleşim aramasının koyduğu yerlere "
                    "dizilir; simülatörün **En iyi yerleşimi bul** bölümü ve "
                    "**Hızlı başla** kutusu aynı aramayı haritadan seçilen "
                    "başka bir yer için çalıştırır. Adaylar var olan "
                    "aydınlatma direkleri ve tabelalar, yol boyundaki "
                    "direkler (şehirde aydınlatma direkleri, açık arazide "
                    "elektrik dağıtım direkleri) ve tepelere dikilecek 25 "
                    "m'lik direklerdir. Çatılar sahiplerinden kiralandığı "
                    "için aday değildir. Her aday bağlantı bütçesiyle denenir"
                    " ve seçim, ömür boyu maliyete göre bir örtme aramasıdır."
                    " Bir noktanın kapsandığı sayılması için ona dört birimin"
                    " ulaşması ve bu birimlerin çevresindeki dört çeyreğin en"
                    " az üçüne dağılmış olması gerekir. Hepsi tek bir "
                    "caddeye, tek bir yana dizilmiş birimler o cadde boyunca "
                    "konum belirleyemez.",
                    "In the urban and rural rows the units do not stand "
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
                    "yerleşimin gerçekte ne kadar doğru olduğunu simülasyon "
                    "ölçer. Önerilen yerleşimi uygulayıp **Simülasyonu "
                    "çalıştır** düğmesine basınca, yerini aldığı yerleşimle "
                    "aynı yolculukta karşılaştırılır.",
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
            heading=_w("Tarayıcıda ve kendi bilgisayarında",
                       "In the browser, and on your own machine"),
            lines=(
                _w(
                    "**Simülasyonu çalıştır** düğmesi simülatörü bu "
                    "tarayıcıda açar. Hiçbir sunucu hesap yapmaz: Python, "
                    "numpy ve projenin kendi paketi sayfaya iner ve her şey "
                    "bu bilgisayarda çalışır. İlk açılış yaklaşık 20 MB "
                    "indirir ve bir dakika sürebilir; sonrasında tarayıcı "
                    "bunları saklar. Tarayıcıda işi tek işlemci yaptığı için "
                    "bir çalıştırma, bilgisayara kurulu sürümden yavaştır; "
                    "**Hızlı deneme** süreyi kısaltır.",
                    "The **Run the simulation** button opens the simulator "
                    "in this browser. No server computes anything: Python, "
                    "numpy and this project's own package come down to "
                    "the page and everything runs on this computer. The "
                    "first load fetches about 20 MB and can take a minute; "
                    "after that the browser keeps it. In a browser one "
                    "processor does the work, so a run is slower than in "
                    "a local install; **Quick trial** shortens it.",
                ),
                _w(
                    "Tabloyu yeniden üretmenin, başka bir şehrin zeminini "
                    "indirmenin ya da üç satırı birden tam çözünürlükte "
                    "çalıştırmanın kodu ve talimatları "
                    "[GitHub'da](https://github.com/ysoktar/yerkon).",
                    "The code and the instructions for reproducing the "
                    "table, fetching another city's ground, or running all "
                    "three rows at full resolution are [on GitHub](https://github.com/ysoktar/yerkon).",
                ),
            ),
        ),
        Part(
            kind="text",
            heading=_w("Hızlı deneme", "The quick trial"),
            lines=(
                _w(
                    "Simülatördeki **Hızlı deneme** düğmesi iki şeyi "
                    "kabalaştırır: gölgeleme sekiz çekilişin birleşimi yerine"
                    " tek çekilişle hesaplanır ve arazi kesiti 10 m'de bir "
                    "yerine sabit 64 noktada okunur. Bir çalıştırma on beş "
                    "dakikadan bir dakika kadara iner.",
                    "The **Quick trial** button in the simulator coarsens "
                    "two figures: the "
                    "shadows are drawn once instead of pooled over eight, "
                    "and the ground profile is read at a fixed 64 samples "
                    "instead of every 10 m. A run drops from fifteen "
                    "minutes to about one.",
                ),
                _w(
                    "Seyrek okunan arazi, engellerin üzerinden bükülmedeki "
                    "kaybı düşük hesaplar; bu da hızlı sonucu çoğunlukla "
                    "olduğundan iyi gösterir. Gölgelemenin tek çekilişi iki "
                    "yöne de saptırabilir: aynı yerleşimde bir satır hızlıda "
                    "daha iyi, başka biri daha kötü çıkabilir. Hızlı "
                    "çalıştırma denemek içindir; Karşılaştırma sayfasındaki tablo "
                    "yalnızca yavaş ve tam çalıştırmadan gelir.",
                    "The coarse ground reads diffraction loss low, which "
                    "mostly makes a fast answer flatter the deployment. "
                    "The single shadow draw can err either way: on the same "
                    "placement one row can come out better fast and "
                    "another worse. A fast run is for trying things; the "
                    "table on the Comparison page comes from the slow, full "
                    "run only.",
                ),
            ),
        ),
    ),
)

SOURCES = Page(
    slug="kaynaklar",
    slug_en="sources",
    nav=_w("Kaynaklar", "Sources"),
    title=_w("Neye dayanıyor", "What it rests on"),
    lead=_w(
        "Sitedeki bütün kaynaklar, konularına göre. Her sayı şunlardan "
        "birine dayanıyor: yayımlanmış bir fiyat ya da veri sayfası, bir "
        "ölçüm, bir standart ya da yönetmelik, bu kaynaklarla yapılmış bir "
        "hesap, bir tasarım kararı ya da açıkça yazılmış bir varsayım.",
        "Every source on the site, grouped by subject. Each number rests on "
        "one of these: a published price or datasheet, a measurement, a "
        "standard or regulation, a calculation from those sources, a "
        "design choice, or an assumption written down.",
    ),
    parts=(
        Part(
            kind="text",
            lines=(_w(
                "Proje dokümanı: [YERKON raporu (PDF, 20 sayfa)]"
                "(https://yerkon.com/yerkon-rapor.pdf)",
                "Project document, in Turkish: [YERKON report "
                "(PDF, 20 pages)](https://yerkon.com/yerkon-rapor.pdf)",
            ),),
        ),
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
                   "satıcıların kademe fiyatları, 24-30 Eylül 2026. Kur: "
                   "TCMB'nin 29 Eylül 2026 gösterge niteliğindeki döviz "
                   "satış kurları, 49,0013 TL/USD ve 55,6103 TL/EUR.",
                   "Tier prices from DigiKey, LCSC, JLCPCB, Mouser, Gainta "
                   "and other sellers, 24 to 30 September 2026. Exchange "
                   "rates: the central bank's indicative forex selling "
                   "rates of 29 September 2026, 49,0013 TL a dollar and "
                   "55,6103 TL a euro."),
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
                    "Başvurunun kaynakçasındaki bütün bağlantılar ve "
                    "maliyet ile mevzuat hesapları için eklenen kaynaklar. "
                    "Hiçbir dipnotun anmadığı kaynaklar da listede.",
                    "Every link in the application's bibliography, and "
                    "the sources added for the cost and regulation "
                    "figures. A source no note cites is still listed.",
                ),
            ),
        ),
        Part(kind="shows", shows="bibliography"),
        Part(
            kind="text",
            lines=(
                _w("Sonuçları yeniden üretmek için kod ve talimatlar "
                   "GitHub'da.",
                   "The code and the instructions for reproducing the "
                   "results are on GitHub."),
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
    slug_en="cost",
    nav=_w("Maliyet", "Cost"),
    title=_w("Ne kadara mal oluyor", "What it costs"),
    lead=_w(
        "Tablodaki her maliyet hücresinin kalem kalem dökümü: hangi parça, "
        "kaça, kimden; hangi sayı, neye dayanarak. Bu sayfadaki sayılar "
        "simülasyondan ve parça listesinden hesaplanıyor; biri değişince sayfa "
        "da değişiyor. Yalnız direk fiyatları tablosu kaynaklarından "
        "aktarıldı.",
        "Every cost cell in the table, line by line: which part, for how "
        "much, from whom; which figure, resting on what. The numbers on "
        "this page are worked out from the simulation and the parts list, so "
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
                    "Direk ekleme kullanılabilirliği yükseltiyor ama "
                    "bedava değil. Mevcut yapılar bunu karşılanabilir "
                    "kılıyor: her ek birim yeni bir saha değil, bir yayın birimi ve "
                    "bir montaj.",
                    "Adding units raises availability, but not for "
                    "nothing. What the existing structures do is make that "
                    "trade affordable, because each extra unit is a device "
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
            heading=_w("Yayın ve alıcı birimlerinin parçaları",
                       "The parts of every broadcast unit and receiver"),
        ),
        Part(
            kind="points",
            heading=_w("Fiyatlar nereden geldi", "Where the prices came from"),
            lines=(
                _w(
                    "Her parça satıcısının kendi kademe tablosuyla yazılı: "
                    "ana parçalar ve birimin geri kalanı, yani şebeke "
                    "beslemesi, düşürücü, koruma, klemens, anten kablosu, "
                    "kutu, pasifler, baskılı devre, dizgi ve lehim. Bir "
                    "parça bir "
                    "birimde birden çok varsa (klemens, pasifler) kademe o "
                    "kadar birim için alınan adete göre seçiliyor.",
                    "Every part carries its seller's own price ladder: the "
                    "main parts and the rest of the unit, that is the "
                    "mains supply, regulator, protection, terminals, "
                    "antenna cable, box, passives, the printed board, its "
                    "assembly and soldering. Where a unit holds more than one of a "
                    "part (terminals, passives), the tier is the one the "
                    "pieces for that many units reach.",
                ),
                _w(
                    "Satıcı bir adette kademe yayımlamamışsa indirim "
                    "varsayılmıyor, bilinen son kademe kullanılıyor. "
                    "Kutuların 100 adet üstü fiyatı teklifle veriliyor; "
                    "baskılı devrenin ve pilin büyük adet fiyatı okunamadı; "
                    "bunlar her adette tek adet fiyatıyla giriyor. Dizginin "
                    "kurulum, şablon ve parça yükleme bedeli siparişe bir "
                    "kez ödendiği için birime düşen payı adet büyüdükçe "
                    "küçülüyor. Maliyet tablosu 1000 adeti kullanıyor.",
                    "Where a seller published no tier for a quantity, no "
                    "discount is assumed and the last known tier holds. "
                    "The boxes are priced on request above a hundred, and "
                    "no volume price could be read for the printed board "
                    "or the battery; those enter at their one-unit price "
                    "at every quantity. Assembly setup, stencil and part "
                    "loading fees are paid once an order, so each unit's "
                    "share shrinks as the order grows. The cost table uses "
                    "the thousand.",
                ),
                _w(
                    "Parça fiyatları satıcıların 25-28 Eylül 2026 liste "
                    "fiyatları; bağlantılar yukarıda. Sipariş öncesinde "
                    "teklifle doğrulanmalı. Bir fiyat değişirse bu sayfa da "
                    "tablo da kendiliğinden güncellenir.",
                    "The part prices are the sellers' list prices of 25 "
                    "to 28 September 2026; the links are above. They are "
                    "to be confirmed by quotation before ordering. If a "
                    "price changes, this page and the table follow on "
                    "their own.",
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

#: The BTK's criteria for licence-exempt radio equipment; a page is linked
#: with #page=N.
BTK_EXEMPT = ("https://www.btk.gov.tr/s3/web-btk-site/"
              "7708c26c-5161-4919-8b3d-daa31d4ac8fb/2026/07/"
              "b02b513d-09b2-4035-bc04-64f59d02f707.pdf")
#: The regulation that makes a device within the criteria licence-free.
EXEMPT_REGULATION = ("https://www.resmigazete.gov.tr/eskiler/2018/11/"
                     "20181127-18.htm")
#: The BTK's call for comments on the draft that would bring in the
#: cyber security requirements of RED Article 3(3).
CYBER_DRAFT = ("https://www.btk.tr/duyurular/bilgi-teknolojileri-ve-"
               "iletisim-kurulunun-06-05-2025-tarihli-ve-2025-ik-ted-128-"
               "sayili-karari-ile-internet-baglantili-telsiz-ekipmanlarinin-"
               "ek-temel-gereklerinin-uygulanmasina-dair-teblig-taslagi-na-"
               "iliskin-olarak-kurum-disi-goruslerin-alinmasi")
#: The 2018 amendment that gave the safety certificate regulation its
#: name and its present scope (Article 2).
SAFETY_CERTIFICATE = ("https://www.resmigazete.gov.tr/eskiler/2018/04/"
                      "20180417-2.htm")
EN_300_328 = ("https://www.etsi.org/deliver/etsi_en/300300_300399/300328/"
              "02.02.02_60/en_300328v020202p.pdf")

LAW = Page(
    slug="mevzuat",
    slug_en="regulation",
    nav=_w("Mevzuat", "Regulation"),
    title=_w("Hangi kurallar, hangi sınırlar", "Which rules, which limits"),
    lead=_w(
        "YERKON'un gücünü, piyasaya çıkışını ve bakım maliyetini belirleyen "
        "kurallar, resmî kaynaklarıyla. Güç, bakım ve kira için burada "
        "yazan her sınır simülasyonda da aynen kullanılıyor; prototip "
        "cihazlarının frekans kuralları sahadaki denemeler için.",
        "The rules that set YERKON's power, its route to market and its "
        "maintenance cost, with their official sources. Every limit on power, "
        "maintenance and rent written here is the one the simulation uses; the "
        "frequency rules for the prototype devices are for the field "
        "trials.",
    ),
    parts=(
        Part(
            kind="text",
            heading=_w("2,4 GHz'de ne kadar güç", "How much power at 2,4 GHz"),
            lines=(
                _w("Şehir içi ve kırsal birimler 2400-2483,5 MHz bandında "
                   "genişband veri iletim sistemi olarak çalışıyor: [BTK, "
                   "Frekans Tahsisinden Muaf Telsiz Cihaz ve Sistemlerine "
                   "İlişkin Teknik Ölçütler, Madde 5, Tablo 3, satır 3]("
                   + BTK_EXEMPT + "#page=11) (Kurul Kararı 23.09.2022, "
                   "2022/İK-SYD/245; [BTK'nın sayfası]"
                   "(https://www.btk.gov.tr/frekans-tahsisinden-muaf-telsiz-"
                   "cihaz-ve-sistemleri)). En çok 100 mW e.i.r.p. "
                   "(20 dBm); yeterli spektrum paylaşım mekanizması "
                   "gerekli (örneğin LBT, DAA); referans standart "
                   "[TS EN 300 328](" + EN_300_328 + "). Frekans Atlamalı "
                   "Spektrum Yayılımı (FHSS) kullanıldığında e.i.r.p. "
                   "yoğunluğu en çok 100 mW/100 kHz, FHSS dışındaki "
                   "genişband modülasyonlarda en çok 10 mW/MHz.",
                   "The town and open country units work in the "
                   "2400-2483,5 MHz band as a wideband data transmission "
                   "system: [BTK, Technical Criteria for Radio Equipment "
                   "and Systems Exempt from Frequency Assignment, Article "
                   "5, Table 3, row 3](" + BTK_EXEMPT + "#page=11) (Board "
                   "decision 23.09.2022, 2022/İK-SYD/245; [the BTK's page]"
                   "(https://www.btk.gov.tr/frekans-tahsisinden-muaf-telsiz-"
                   "cihaz-ve-sistemleri)). At most "
                   "100 mW e.i.r.p. (20 dBm); an adequate spectrum sharing "
                   "mechanism is required (for example LBT, DAA); the "
                   "reference standard is [TS EN 300 328](" + EN_300_328
                   + "). With frequency hopping spread spectrum (FHSS) the "
                   "e.i.r.p. density is at most 100 mW/100 kHz; with other "
                   "wideband modulations at most 10 mW/MHz."),
                _w("Tablodaki güç sınırları yönetmelikten; kanal "
                   "kontrolü, süreler ve eşikler TS EN 300 328'den (ETSI "
                   "EN 300 328 V2.2.2, 4.3.1). Yönetmelik, referans "
                   "standarttaki tekniklere en az eş değer spektrum erişim "
                   "ve girişimi azaltma tekniklerini şart koşuyor ([Madde "
                   "2](" + BTK_EXEMPT + "#page=6)).",
                   "The power limits in the table are the regulation's; "
                   "the channel check, the durations and the thresholds "
                   "are TS EN 300 328's (ETSI EN 300 328 V2.2.2, 4.3.1). "
                   "The regulation requires spectrum access and "
                   "interference mitigation techniques at least equivalent "
                   "to those of the reference standard ([Article 2]("
                   + BTK_EXEMPT + "#page=6))."),
                _w("Bu ölçütlere uyan cihaz ruhsatsız kullanılıyor: "
                   "telsiz ruhsatnamesi, telsiz kurma ve kullanma izni, "
                   "frekans tahsisi ve tescili gerekmiyor ([Frekans "
                   "Tahsisinden Muaf Telsiz Cihaz ve Sistemleri Hakkında "
                   "Yönetmelik](" + EXEMPT_REGULATION + "), Madde 5). Cihaz "
                   "başka telsizlere zararlı girişim yapamaz ve onlardan "
                   "gelen girişime karşı koruma isteyemez (Madde 5(3)). "
                   "Muafiyet dışında ve mevzuata aykırı kullanımda "
                   "Elektronik Haberleşme Kanunu'nun 63. maddesine göre "
                   "işlem yapılıyor (Madde 7).",
                   "A device within these criteria is used without a "
                   "licence: no radio licence, no permit to set up and "
                   "use it, no frequency assignment or registration "
                   "([Regulation on Radio Equipment and Systems Exempt "
                   "from Frequency Assignment](" + EXEMPT_REGULATION + "), "
                   "Article 5). It may not cause harmful interference to "
                   "other radio systems and may not claim protection from "
                   "theirs (Article 5(3)). Use outside the exemption and "
                   "against the rules is dealt with under Article 63 of "
                   "the Electronic Communications Law (Article 7)."),
                _w("Açık bir soru: Teknik Ölçütler'in [Madde 8]("
                   + BTK_EXEMPT + "#page=17)'i radyo-tespit cihazlarını, "
                   "yani bir nesnenin konumunu telsizle belirleyen "
                   "cihazları ayrıca düzenliyor; 2400-2483,5 MHz'de sınır "
                   "25 mW e.i.r.p., referans standart TS EN 300 440. Aynı "
                   "madde noktadan noktaya ve noktadan çok noktaya telsiz "
                   "haberleşmesini kapsam dışı sayıyor. YERKON konumu "
                   "birimler arasındaki paket alışverişiyle bulduğu için "
                   "iki maddeye de girebilir. Site ve simülasyon Madde 5'i "
                   "esas alıyor. Madde 8 geçerli sayılırsa yayın gücü "
                   "dörtte bire (6 dB) iner, menzil kısalır (engelsiz "
                   "yayılmada kabaca yarıya), daha çok birim gerekir ve "
                   "km² başına maliyet artar. Kesin cevap BTK'dan görüş "
                   "istenerek alınacak.",
                   "An open question: [Article 8](" + BTK_EXEMPT
                   + "#page=17) of the Technical Criteria deals separately "
                   "with radiodetermination devices, those that find an "
                   "object's position by radio; at 2400-2483,5 MHz the "
                   "limit is 25 mW e.i.r.p. and the reference standard TS "
                   "EN 300 440. The same article leaves out point-to-point "
                   "and point-to-multipoint radio communication. YERKON "
                   "finds position through packets exchanged between "
                   "units, so it can be read under either article. The "
                   "site and the simulation rest on Article 5. Were "
                   "Article 8 to apply, the transmit power would fall to a "
                   "quarter (6 dB), the range would shrink (roughly by "
                   "half without obstacles), more units would be needed "
                   "and the cost per km² would rise. The definitive answer "
                   "will come from asking the BTK for its opinion."),
            ),
        ),
        Part(
            kind="table",
            rows=(
                (_w("Kip", "Mode"), _w("Sınır", "Limit"),
                 _w("YERKON için ne demek", "What it means for YERKON")),
                (
                    _w("FHSS olmadan (FHSS dışındaki genişband "
                       "modülasyon)",
                       "Without FHSS (other wideband modulation)"),
                    _w("100 mW e.i.r.p. ve en çok 10 mW/MHz",
                       "100 mW e.i.r.p. and at most 10 mW/MHz"),
                    _w("Sinyal 1,625 MHz genişliğinde. MHz başına 10 mW "
                       "sınırı yüzünden toplam yayın gücü 16,25 mW'ı "
                       "(12,1 dBm) geçemiyor; 100 mW'lık sınıra hiç "
                       "ulaşılamıyor.",
                       "The signal is 1,625 MHz wide. The 10 mW a MHz "
                       "limit holds the total to 16,25 mW (12,1 dBm), so "
                       "the 100 mW limit is never reached."),
                ),
                (
                    _w("FHSS, LBT ya da DAA olmadan (TS EN 300 328'de "
                       "uyarlamasız cihaz)",
                       "FHSS without LBT or DAA (non-adaptive equipment in "
                       "TS EN 300 328)"),
                    _w("100 mW e.i.r.p.; yayın dizisi en çok 5 ms, ara en "
                       "az 5 ms; bir frekansta 15 ms × N içinde en çok "
                       "15 ms; ortamı meşgul etme payı en çok %10",
                       "100 mW e.i.r.p.; transmissions at most 5 ms with "
                       "gaps of at least 5 ms; at most 15 ms on one "
                       "frequency in 15 ms × N; medium utilisation at most "
                       "10 %"),
                    _w("Uymuyor: bir ölçüm paketi SF10'da yaklaşık 15 ms "
                       "sürüyor ve araç sürekli soruyor.",
                       "Does not fit: one ranging frame lasts about 15 ms "
                       "at SF10 and a vehicle polls continuously."),
                ),
                (
                    _w("FHSS ve Göndermeden Önce Dinle (LBT) (TS EN 300 "
                       "328'de uyarlamalı cihaz)",
                       "FHSS with listen before talk (LBT) (adaptive "
                       "equipment in TS EN 300 328)"),
                    _w("100 mW e.i.r.p. ve en çok 100 mW/100 kHz; her "
                       "kanal kullanımından önce kanal kontrolü, eşik "
                       "-70 dBm/MHz; kanal kullanımı 60 ms'den kısa, "
                       "ardından onun en az %5'i kadar sessizlik; bandın en "
                       "az %70'inde çalışabilmeli",
                       "100 mW e.i.r.p. and at most 100 mW/100 kHz; a "
                       "channel check before each use of a channel, "
                       "threshold -70 dBm/MHz; channel occupancy under "
                       "60 ms, then silence of at least 5 % of it; able to "
                       "use at least 70 % of the band"),
                    _w("YERKON'un seçtiği kip, şehir içi ve kırsalda: tek "
                       "açık yol. 1,625 MHz'lik sinyalde yoğunluk sınırı "
                       "bağlamıyor, 100 mW (20 dBm) kalıyor. Bir ölçüm "
                       "alışverişi 31,8 ms, 60 ms'ye sığıyor. Cevap veren "
                       "direk de kendi yayınından önce kanalı kontrol "
                       "ediyor; bu, alışverişe 0,1 ms'den az ekliyor. "
                       "Laboratuvar testiyle belgelendirilmeli.",
                       "The mode YERKON uses in town and open country, and "
                       "the one open road. On a 1,625 MHz signal the "
                       "density limit does not bind and 100 mW (20 dBm) "
                       "holds. A ranging exchange is 31,8 ms and fits in "
                       "60 ms. The replying pole checks the channel before "
                       "its own transmission too, which adds under 0,1 ms. "
                       "It must be certified by a test laboratory."),
                ),
            ),
        ),
        Part(
            kind="table",
            heading=_w("Birim birim yasal güç, 2,4 GHz",
                       "Legal power unit by unit, 2,4 GHz"),
            rows=(
                (_w("Birim", "Unit"),
                 _w("E28-2G4M20S\nçıkışı, en az /\ntipik / en çok",
                    "E28-2G4M20S\noutput, min /\ntyp / max"),
                 _w("Anten,\nnet kazanç", "Antenna,\nnet gain"),
                 _w("Tam güçte\ne.i.r.p.", "E.i.r.p.\nat full power"),
                 _w("FHSS ve LBT ile\nen yüksek ayar",
                    "Highest, with\nFHSS and LBT"),
                 _w("FHSS olmadan\nen yüksek ayar",
                    "Highest,\nwithout FHSS")),
                (_w("Yayın\u00a0birimi, şehir\u00a0içi\u00a0ve\u00a0kırsal",
                    "Broadcast\u00a0unit, town and open\u00a0country"),
                 _w("19 / 20 / 21\u00a0dBm", "19 / 20 / 21\u00a0dBm"),
                 _w("Taoglas GW.22.5151, 4,7\u00a0dBi",
                    "Taoglas GW.22.5151, 4,7\u00a0dBi"),
                 _w("234-372\u00a0mW, sınırı aşıyor",
                    "234-372\u00a0mW, over the limit"),
                 _w("15,3\u00a0dBm (34\u00a0mW)", "15,3\u00a0dBm (34\u00a0mW)"),
                 _w("7,4\u00a0dBm (5,5\u00a0mW)", "7,4\u00a0dBm (5,5\u00a0mW)")),
                (_w("Kara\u00a0aracı alıcısı", "Vehicle\u00a0receiver"),
                 _w("19 / 20 / 21\u00a0dBm", "19 / 20 / 21\u00a0dBm"),
                 _w("Taoglas GW.22.5151, 4,7\u00a0dBi",
                    "Taoglas GW.22.5151, 4,7\u00a0dBi"),
                 _w("234-372\u00a0mW, sınırı aşıyor",
                    "234-372\u00a0mW, over the limit"),
                 _w("15,3\u00a0dBm (34\u00a0mW)", "15,3\u00a0dBm (34\u00a0mW)"),
                 _w("7,4\u00a0dBm (5,5\u00a0mW)", "7,4\u00a0dBm (5,5\u00a0mW)")),
                (_w("Yaya\u00a0alıcısı", "Pedestrian\u00a0receiver"),
                 _w("19 / 20 / 21\u00a0dBm", "19 / 20 / 21\u00a0dBm"),
                 _w("kart üstü, 3,2\u00a0dBi (hesapta kullanılan değer; üretici "
                    "kazancı vermiyor)",
                    "on-board, 3,2\u00a0dBi (the figure used in the calculation; "
                    "the maker gives none)"),
                 _w("166-263\u00a0mW, sınırı aşıyor",
                    "166-263\u00a0mW, over the limit"),
                 _w("16,8\u00a0dBm (48\u00a0mW)", "16,8\u00a0dBm (48\u00a0mW)"),
                 _w("8,9\u00a0dBm (7,8\u00a0mW)", "8,9\u00a0dBm (7,8\u00a0mW)")),
            ),
        ),
        Part(
            kind="text",
            lines=(
                _w("Modülün gücü [EBYTE'nin E28-2G4M20S veri sayfasından]("
                   "https://www.ebyte.com/downpdf/304.html): 100 mW, en az "
                   "19, tipik 20, en çok 21 dBm; bu antene giden güç. "
                   "Sınır antenden çıkan güç için: FHSS ve LBT ile 100 mW "
                   "e.i.r.p. (20 dBm), FHSS olmadan 1,625 MHz'lik sinyalde "
                   "16,25 mW (12,1 dBm). En yüksek ayar, modülün en çok "
                   "çıkışıyla bile sınırın aşılmadığı iletilen güç: sınır "
                   "eksi antenin net kazancı. Tipik çıkış bundan 1 dB "
                   "aşağıda kalır. Anten takılması serbest, ama TS EN 300 328 "
                   "cihazın o antenle test edilmesini ve yazılımın izin "
                   "verdiği hiçbir güç ayarının sınırı aşmamasını istiyor "
                   "(4.2.4 ve 4.3.1.2). Simülasyon her birimin gücünü antenin "
                   "en güçlü yönünde sınıra kısıyor; sonuçlar bu güçle.",
                   "The module's power is from [EBYTE's E28-2G4M20S "
                   "datasheet](https://www.ebyte.com/downpdf/304.html): "
                   "100 mW, at least 19, typically 20, at most 21 dBm; that "
                   "is the power fed to the antenna. The limit is on the "
                   "power leaving the antenna: 100 mW e.i.r.p. (20 dBm) "
                   "with FHSS and LBT, 16,25 mW (12,1 dBm) without FHSS on "
                   "a 1,625 MHz signal. The highest setting is the "
                   "conducted power at which even the module's highest "
                   "output stays within the limit: the limit less the "
                   "antenna's net gain. The typical output stays 1 dB "
                   "below it. An antenna may be fitted, but TS EN 300 328 "
                   "has the equipment tested with that antenna and no "
                   "power setting the software allows may exceed the limit "
                   "(4.2.4 and 4.3.1.2). The simulation holds every unit to the "
                   "limit in its antenna's strongest direction; the "
                   "results use that power."),
                _w("UWB birimleri (DWM3000) kendi antenleriyle -41,3 "
                   "dBm/MHz'te; tünel ve yaya birimi aşağıdaki tabloya "
                   "olduğu gibi uyuyor; araç alıcısının gücünü denetlemesi "
                   "(TPC) ve yukarıya doğru harici sınırı uygulaması gerekiyor.",
                   "The UWB units (DWM3000) run at -41,3 dBm/MHz on their "
                   "own antennas; the tunnel and pedestrian units fit the "
                   "table below as they are, the vehicle receiver has to "
                   "control its power (TPC) and keep to the exterior limit "
                   "upward."),
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
                    _w("Genel amaçlı UWB ([Madde 18(1), Tablo 16]("
                       + BTK_EXEMPT + "#page=28))",
                       "General purpose UWB ([Article 18(1), Table 16]("
                       + BTK_EXEMPT + "#page=28))"),
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
                    _w("Konum izleme tip 1, LT1 ([Madde 18(4), Tablo 19]("
                       + BTK_EXEMPT + "#page=31))",
                       "Location tracking type 1, LT1 ([Article 18(4), "
                       "Table 19](" + BTK_EXEMPT + "#page=31))"),
                    _w("Ortalama -41,3 dBm/MHz, tepe 0 dBm; TS EN 302 065-2",
                       "Mean -41,3 dBm/MHz, peak 0 dBm; TS EN 302 065-2"),
                    _w("İnsanların ve nesnelerin konumunu izleyen sistemler "
                       "için. Tünel birimleri bu satırda: 499,2 MHz'lik "
                       "kanalda -14,3 dBm e.i.r.p., simülasyon da bunu "
                       "kullanıyor.",
                       "For systems that track where people and objects "
                       "are. The tunnel units are in this row: -14,3 dBm "
                       "e.i.r.p. over a 499,2 MHz channel, which is what "
                       "the simulation uses."),
                ),
                (
                    _w("Karayolu ve demiryolu taşıtları ([Madde 18(2), "
                       "Tablo 17](" + BTK_EXEMPT + "#page=29))",
                       "Road and rail vehicles ([Article 18(2), Table 17]("
                       + BTK_EXEMPT + "#page=29))"),
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
                       "simülasyon da böyle hesaplıyor. Kapalı alan için otomatik bir istisna "
                       "yok, Ek C.1 eşdeğer korumanın kanıtlanmasına izin "
                       "veriyor.",
                       "The vehicle receiver is in this row and has to "
                       "control its power (TPC). The vehicle's device may "
                       "send less power above its own height (-53,3 "
                       "dBm/MHz); below it -41,3 dBm/MHz holds (EN 302 "
                       "065-3, 4.3.4.2 and table 4). Tunnel units below the "
                       "vehicle's antenna, 1,2 m above the road, stay clear "
                       "of that limit, and the simulation works it out that "
                       "way. There is no automatic "
                       "exemption for enclosed spaces; Annex C.1 allows "
                       "equivalent protection to be demonstrated."),
                ),
            ),
        ),
        Part(
            kind="points",
            heading=_w("Yönetmelikteki tanımlar", "Definitions in the regulation"),
            lines=(
                _w("Frekans Atlamalı Spektrum Yayılımı (FHSS): alıcı ve "
                   "vericinin eş zamanlı olarak bir frekanstan diğerine "
                   "atlayabilmesi.",
                   "Frequency hopping spread spectrum (FHSS): the receiver "
                   "and transmitter hopping together from one frequency to "
                   "another."),
                _w("Göndermeden Önce Dinle (LBT): cihazın, kullandığı "
                   "banttaki doluluğu algılayıp bant boşalana ya da boş "
                   "bir banda geçene kadar beklemesi.",
                   "Listen before talk (LBT): the device senses whether its "
                   "band is busy and waits until it is free or it has moved "
                   "to a free one."),
                _w("Algıla ve Kaçın (DAA): cihazın göndermeden önce "
                   "kanalları kontrol etmesi, başka sistemlerin "
                   "kullandıklarından kaçınması ve boş bulduğu kanaldan "
                   "göndermesi.",
                   "Detect and avoid (DAA): the device checks the channels "
                   "before sending, avoids those other systems are using "
                   "and sends on one it finds free."),
                _w("e.i.r.p. (etkin izotropik yayılım gücü): antene "
                   "verilen güç ile antenin o yöndeki, izotropik antene "
                   "göre kazancının çarpımı. 100 mW 20 dBm, 10 mW 10 dBm.",
                   "e.i.r.p. (effective isotropic radiated power): the "
                   "power fed to the antenna times the antenna's gain in "
                   "that direction over an isotropic antenna. 100 mW is "
                   "20 dBm, 10 mW is 10 dBm."),
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
                _w("Kaynak: [BTK, Frekans Tahsisinden Muaf Telsiz Cihaz ve "
                   "Sistemlerine İlişkin Teknik Ölçütler, Madde 1]("
                   + BTK_EXEMPT + "#page=1).",
                   "Source: [BTK, Technical Criteria for Radio Equipment "
                   "and Systems Exempt from Frequency Assignment, Article "
                   "1](" + BTK_EXEMPT + "#page=1)."),
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
                _w("E28-2G4M20S zaten 20 dBm verdiği için 5 dBi anten "
                   "yayında bir şey kazandırmıyor: modül 15,3 dBm'ye "
                   "kısılıyor ve antenden yine 100 mW çıkıyor. Kazanç alışta: "
                   "her uç karşıyı 4,7 dB daha iyi duyuyor. Modülün kart "
                   "üstü anteni kutunun içinde kalıyor ve EBYTE kazancını "
                   "vermiyor; kart üstü antenle kapsanan alan küçülüyor, "
                   "km² başına maliyet artıyor.",
                   "The E28-2G4M20S already gives 20 dBm, so the 5 dBi "
                   "antenna adds nothing on transmit: the module is turned "
                   "down to 15,3 dBm and 100 mW still leaves the antenna. "
                   "The gain is on receive: each end hears the other 4,7 dB "
                   "better. The module's on-board antenna stays inside the "
                   "box and EBYTE gives no gain for it; with it the covered "
                   "area shrinks and the cost per km² rises."),
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
                _w("Gereken testler: [EN 300 328](" + EN_300_328 + ") "
                   "(telsiz; FHSS ve LBT burada sınanıyor), EN 301 489-1 ve "
                   "-17 (elektromanyetik uyumluluk), EN 62368-1 (güvenlik) "
                   "ve EN 62311 (insanın elektromanyetik alana maruziyeti). "
                   "Laboratuvarlar teklifle çalışıyor. Yayımlanmış piyasa "
                   "göstergesine göre dördü birlikte vergi hariç 2500-8000 "
                   "€, bir kerelik ([LCAS v1.0, Multicert, Haziran 2026]"
                   "(https://lcas.info/)). Birim merkeze bağlandığı için "
                   "[Telsiz Ekipmanları Yönetmeliği (2014/53/AB)]"
                   "(https://www.resmigazete.gov.tr/eskiler/2020/11/20201105-6.htm) Madde 5(3)'teki ağa zarar "
                   "vermeme, kişisel verilerin korunması ve sahtekârlığa "
                   "karşı korunma gerekleri (EN 18031) de kapsama "
                   "girebilir; Madde 5(4)'e göre bunları BTK kendi "
                   "düzenlemesiyle uygulamaya alıyor. BTK bunun için "
                   "[İnternet Bağlantılı Telsiz Ekipmanlarının Ek Temel "
                   "Gereklerinin Uygulanmasına Dair Tebliğ Taslağı]("
                   + CYBER_DRAFT + ")'nı 6 Mayıs 2025 tarihli ve "
                   "2025/İK-TED/128 sayılı kararla görüşe açtı (son gün "
                   "3 Temmuz 2025); AB'deki karşılığı 2022/30 sayılı "
                   "tüzük. Tebliğin yürürlüğe girdiğini gösteren bir "
                   "duyuru bulunamadı (1 Ekim 2026). O kanıtın bedeli bu "
                   "aralığın dışında. "
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
                   "Tests needed: [EN 300 328](" + EN_300_328 + ") "
                   "(radio; FHSS and LBT are tested here), EN 301 489-1 and -17 "
                   "(electromagnetic compatibility), EN 62368-1 (safety) "
                   "and EN 62311 (human exposure to electromagnetic "
                   "fields). Laboratories work by quotation. A published "
                   "market indication puts the four together at 2500-8000 "
                   "€ before tax, once ([LCAS v1.0, Multicert, June 2026]"
                   "(https://lcas.info/)). The unit is connected to the "
                   "centre, so the requirements of Article 5(3) of "
                   "Türkiye's [Radio Equipment Regulation (2014/53/AB)]"
                   "(https://www.resmigazete.gov.tr/eskiler/2020/11/20201105-6.htm) on harm to the network, "
                   "personal data and fraud (EN 18031) may apply as "
                   "well; under Article 5(4) the BTK brings them into "
                   "force by its own rules. For this the BTK opened the "
                   "[draft communiqué on the additional essential "
                   "requirements for internet-connected radio equipment]("
                   + CYBER_DRAFT + ") for comment by Board decision "
                   "2025/İK-TED/128 of 6 May 2025 (deadline 3 July 2025); "
                   "its EU counterpart is Regulation 2022/30. No notice "
                   "was found that it has come into force (1 October "
                   "2026). That evidence costs extra. "
                   "The tunnel unit and the "
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
                   "Kuruluşa gitme zorunluluğu yok: [Telsiz Ekipmanları "
                   "Yönetmeliği (2014/53/AB)](https://www.resmigazete.gov.tr/eskiler/2020/11/20201105-6.htm) Madde 20(3), "
                   "Ek-2'deki iç üretim kontrolüne izin veriyor. "
                   "Bu, uygunluğun bedelsiz olduğu anlamına gelmiyor; "
                   "üretici uygunluğu teknik dosya ve ölçüm sonuçlarıyla "
                   "göstermek zorunda.",
                   "Where the harmonised standards are applied, a notified "
                   "body is not required: Article 20(3) of Türkiye's "
                   "[Radio Equipment Regulation (2014/53/AB)](https://www.resmigazete.gov.tr/eskiler/2020/11/20201105-6.htm) "
                   "allows internal production control under Annex 2. "
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
                   "Türkiye; only narrow sub-bands such as 917,4-919,4 MHz "
                   "are, under conditions."),
                _w("863-870 MHz alt bantlarının çoğunda 25 mW e.r.p. ve "
                   "%0,1 ile %1 görev çevrimi (vericinin açık kaldığı zaman oranı); "
                   "869,4-869,65 MHz'de 500 mW ve "
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
                   "memuruna ödenen gündeliktir. Simülasyon bu yüzden kamu "
                   "cetvelini kullanıyor.",
                   "A per diem is the daily allowance paid, with the "
                   "fare, to a worker sent on a temporary duty outside "
                   "the place of duty (Travel Allowance Law 6245). The "
                   "law is for public servants; a private employer sets "
                   "its own, but the tax-exempt part is the allowance of "
                   "a civil servant on the same salary level (Income Tax "
                   "Law 193, Article 24(2)). The simulation uses the public "
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
                   "away over one of the lunch (13:00) or dinner (19:00) "
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
                   "simülasyonda bu yüzden duruyor.",
                   "Zero in YERKON today: in town the crew is in its own "
                   "district; in open country and the tunnel a local "
                   "firm in that district does the maintenance, so "
                   "nobody leaves the place of duty. Were it done from "
                   "central Ankara, each crew day would add 566,67 TL; "
                   "that is why the rule stays in the simulation."),
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
                   "konduğu için simülasyonda dağıtım direği kirası sıfır.",
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
                   "agreement, so the simulation charges no pole rent."),
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
            heading=_w("Güvenlik sertifikası", "Safety certificate"),
            lines=(
                _w("[Elektronik Haberleşme Cihazları Güvenlik Sertifikası "
                   "Yönetmeliği](" + SAFETY_CERTIFICATE + "), elektromanyetik "
                   "alan bakımından sabit vericilerin yerini, kurulumunu, "
                   "denetimini ve güvenlik sertifikasını düzenliyor. "
                   "Yönetmeliğin 2. maddesi, hücresel sistemler dışında, son "
                   "kullanıcı terminal cihazlarını ve çıkış gücü 5 W ve "
                   "altındaki cihazları kapsam dışı tutuyor. YERKON'un yayın "
                   "birimleri en çok 100 mW yayıyor, alıcılar son kullanıcı "
                   "cihazı; bu yüzden hiçbiri için güvenlik sertifikası "
                   "gerekmiyor.",
                   "The [Regulation on Safety Certificates for Electronic "
                   "Communications Devices](" + SAFETY_CERTIFICATE + ") "
                   "governs where fixed transmitters go, how they are "
                   "installed and inspected, and their safety certificate, "
                   "with regard to electromagnetic fields. Its Article 2 "
                   "leaves out, cellular systems aside, end-user terminal "
                   "devices and devices with an output power of 5 W or "
                   "less. YERKON's broadcast units put out at most 100 mW "
                   "and the receivers are end-user devices, so none of them "
                   "needs a safety certificate."),
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
                Link(label=_w("Telsiz Ekipmanları Yönetmeliği (2014/53/AB), "
                              "Resmî Gazete, 5 Kasım 2020, sayı 31295",
                              "Radio Equipment Regulation (2014/53/AB), "
                              "Resmî Gazete, 5 November 2020, issue 31295"),
                     url="https://www.resmigazete.gov.tr/eskiler/2020/11/20201105-6.htm"),
                Link(label=_w("Yönetmeliğin dayandığı AB direktifi 2014/53/AB (EUR-Lex)",
                              "The EU directive it transposes, 2014/53/EU (EUR-Lex)"),
                     url="https://eur-lex.europa.eu/eli/dir/2014/53/oj"),
                Link(label=_w("BTK: piyasa gözetimi, sıkça sorulan sorular",
                              "BTK: market surveillance, frequently asked questions"),
                     url="https://www.btk.gov.tr/piyasa-gozetimi-ve-denetimi-sikca-sorulan-sorular"),
                Link(label=_w("BTK: frekans tahsisinden muaf telsiz cihazların teknik ölçütleri",
                              "BTK: technical criteria for licence-exempt radio devices"),
                     url=BTK_EXEMPT),
                Link(label=_w("Frekans Tahsisinden Muaf Telsiz Cihaz ve "
                              "Sistemleri Hakkında Yönetmelik, Madde 5 ve 7 "
                              "(Resmî Gazete, 27 Kasım 2018, sayı 30608)",
                              "Regulation on Radio Equipment and Systems "
                              "Exempt from Frequency Assignment, Articles 5 "
                              "and 7 (Resmî Gazete, 27 November 2018, issue "
                              "30608)"),
                     url=EXEMPT_REGULATION),
                Link(label=_w("BTK: İnternet bağlantılı telsiz ekipmanları "
                              "tebliğ taslağı, 2025/İK-TED/128",
                              "BTK: draft communiqué on internet-connected "
                              "radio equipment, 2025/İK-TED/128"),
                     url=CYBER_DRAFT),
                Link(label=_w("Elektronik Haberleşme Cihazları Güvenlik "
                              "Sertifikası Yönetmeliği, Madde 2 (Resmî "
                              "Gazete, 17 Nisan 2018, sayı 30394)",
                              "Regulation on Safety Certificates for "
                              "Electronic Communications Devices, Article 2 "
                              "(Resmî Gazete, 17 April 2018, issue 30394)"),
                     url=SAFETY_CERTIFICATE),
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
#: The same button on a narrow phone, where the long one pushes the bar
#: past the screen.
SIMULATOR_SHORT = _w("Çalıştır", "Run")

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

ROW_BASIS = _w("Bu satırın kaynakları ve açıklamaları",
               "This row's sources and notes")

NOTES_HEADING = _w("Dipnotlar ({count})", "Notes ({count})")

#: The round "i" at the end of each row of the comparison table.
INFO_ICON = (
    '<svg viewBox="0 0 16 16" aria-hidden="true"><circle cx="8" cy="8" '
    'r="7" fill="none" stroke="currentColor" stroke-width="1.4"/>'
    '<circle cx="8" cy="4.8" r="1" fill="currentColor"/><path d="M8 7v5" '
    'stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/></svg>'
)

#: The typeface, IBM Plex Sans, is declared in the stylesheets and served
#: from fonts/ beside them: the Turkish letters and the equal-width figures
#: the tables line up on, and no request to anybody else's server.
FONTS = ("ibm-plex-sans-latin.woff2", "ibm-plex-sans-latin-ext.woff2",
         "OFL.txt")

FOOTER = _w(
    "YERKON ekibi tarafından sevgiyle hazırlanmıştır",
    "Made with love by the YERKON team",
)

WEIGHTING = _w(
    "Simülasyonun doldurduğu üç satır. Her biri, hataların yüzde "
    "95'inin altında kaldığı yatay sapmayı gösteriyor ve her biri "
    "Ankara'nın gerçek arazisi üzerinde çalıştırıldı.",
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
    from yerkon.numbers import grouped_html

    # Every quantity on the page with its thousands marked, whichever
    # file it was written in (the page, the table's notes, the settings).
    return _pdfs_apart(grouped_html(_document(
        title=named if named == "YERKON" else "{} · YERKON".format(named),
        language=language,
        stylesheet=where.asset(_tagged("site.css")),
        script=where.asset(_tagged("theme.js")),
        body="\n".join(body),
        description=_described(_said(page.lead, language)),
        icon=where.asset(""), front=page is PAGES[0],
        addresses=_addresses(page, language),
    )))


def _addresses(page: Page, language: str) -> str:
    """The page's own address and its twin in the other language, for
    search engines: one canonical address, and hreflang to say the
    Turkish and English pages are the same page (Turkish by default)."""
    tr = "https://{}/{}".format(DOMAIN, Where.folder(page, "tr"))
    en = "https://{}/{}".format(DOMAIN, Where.folder(page, "en"))
    return (
        '<link rel="canonical" href="{own}">\n'
        '<link rel="alternate" hreflang="tr" href="{tr}">\n'
        '<link rel="alternate" hreflang="en" href="{en}">\n'
        '<link rel="alternate" hreflang="x-default" href="{tr}">\n'
    ).format(own=tr if language == "tr" else en, tr=tr, en=en)


def _described(lead: str) -> str:
    """The page's lead as a search result shows it: plain words, no
    markup, no long dashes, and short enough not to be cut mid-word."""
    text = re.sub(r"<[^>]+>", "", lead)
    text = html.unescape(text).replace("—", ",").replace("–", "-")
    text = " ".join(text.split())
    if len(text) <= 160:
        return text
    cut = text[:157].rsplit(" ", 1)[0].rstrip(",;:")
    return cut + "…"


def _document(title: str, language: str, stylesheet: str, script: str,
              body: str, description: str = "", icon: str = "",
              front: bool = False, addresses: str = "") -> str:
    # The front pages say what the site is called and which picture is
    # its logo, in the form search engines read (schema.org JSON-LD).
    named = ""
    if front:
        named = ('<script type="application/ld+json">{}</script>\n'.format(
            json.dumps({
                "@context": "https://schema.org",
                "@graph": [
                    {"@type": "WebSite", "name": "YERKON",
                     "url": "https://{}/".format(DOMAIN)},
                    {"@type": "Organization", "name": "YERKON",
                     "url": "https://{}/".format(DOMAIN),
                     "logo": "https://{}/icon-512.png".format(DOMAIN)},
                ],
            }, ensure_ascii=False)))
    return (
        "<!doctype html>\n"
        '<html lang="{language}">\n'
        "<head>\n"
        '<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        '<meta http-equiv="Content-Security-Policy" content="{policy}">\n'
        "{referrer}\n"
        "<title>{title}</title>\n"
        '<meta name="description" content="{description}">\n'
        '<meta property="og:title" content="{title}">\n'
        '<meta property="og:description" content="{description}">\n'
        '<link rel="icon" href="{icon}favicon.ico" sizes="48x48">\n'
        '<link rel="icon" href="{icon}favicon.svg" type="image/svg+xml">\n'
        '<link rel="icon" href="{icon}icon-192.png" type="image/png" '
        'sizes="192x192">\n'
        '<link rel="apple-touch-icon" href="{icon}apple-touch-icon.png">\n'
        '<meta name="theme-color" content="#2178fe">\n'
        '<meta property="og:site_name" content="YERKON">\n'
        '{addresses}{named}'
        '<link rel="stylesheet" href="{stylesheet}">\n'
        '<script src="{script}" defer></script>\n'
        "</head>\n"
        "<body>\n{body}\n</body>\n</html>\n"
    ).format(language=language, title=html.escape(title),
             policy=PAGE_POLICY, referrer=REFERRER,
             description=html.escape(description, quote=True),
             icon=html.escape(icon, quote=True), named=named,
             addresses=addresses,
             stylesheet=html.escape(stylesheet, quote=True),
             script=html.escape(script, quote=True), body=body)


def _header(page: Page, language: str, where: Where) -> str:
    links = []
    for other in PAGES:
        here = ' class="here"' if other.slug == page.slug else ""
        links.append('<a href="{}"{}>{}</a>'.format(
            where.page(other), here, _said(other.nav, language)
        ))
    # The language being read is lit and is not a link: a lit button that
    # took a press and did nothing read as a switch that had not worked.
    # Only the other one can be pressed.
    tongues = "".join(
        '<span class="here" aria-current="true">{}</span>'.format(label)
        if code == language else
        '<a href="{}" hreflang="{}" lang="{}">{}</a>'.format(
            where.tongue(page, code), code, code, label)
        for code, label in LANGUAGES
    )
    # The brand on the left, the pages in the middle, and on the right,
    # outward: the simulator, the theme, then the language at the edge.
    return (
        "<header>\n"
        '<a class="brand" href="{home}"><img src="{logo}" alt="" '
        'width="26" height="26"><b>YERKON</b></a>\n'
        '<nav class="pages">{links}</nav>\n'
        '<div class="actions">'
        '<a class="run" href="{simulator}" title="{label}">'
        '<span class="long">{label}</span><span class="short">{short}</span>'
        '</a>'
        '<button class="theme" id="theme" type="button" hidden></button>'
        '<nav class="tongues">{tongues}</nav>'
        "</div>\n"
        "</header>"
    ).format(
        home=where.page(HOME),
        logo=where.asset("favicon.svg"),
        links="".join(links),
        tongues=tongues,
        simulator=where.simulator(),
        label=_said(SIMULATOR_LABEL, language),
        short=_said(SIMULATOR_SHORT, language),
    )


#: A heart after the footer's words, drawn rather than typed so it looks
#: the same everywhere.
HEART = ('<svg class="heart" viewBox="0 0 24 24" aria-hidden="true">'
         '<path d="M12 21s-7.5-4.6-10-9.3C.4 8.5 2.2 4.5 6 4.5c2.2 0 3.6 1.2 '
         '6 3.6 2.4-2.4 3.8-3.6 6-3.6 3.8 0 5.6 4 4 7.2C19.5 16.4 12 21 '
         '12 21z"/></svg>')


def _footer(language: str) -> str:
    return "<footer><p>{} {}</p></footer>".format(_said(FOOTER, language), HEART)


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
        if part.states:
            drawn = '<ul class="status">{}</ul>'.format("".join(
                '<li class="{}">{}</li>'.format(state, _said(line, language))
                for state, line in zip(part.states, part.lines)))
        else:
            drawn = "<ul>{}</ul>".format("".join(
                "<li>{}</li>".format(_said(line, language))
                for line in part.lines
            ))
    elif part.kind == "people":
        drawn = '<div class="people">{}</div>'.format("".join(
            '<div class="person">{}</div>'.format("".join(
                "<p>{}</p>".format(_marked(row))
                for row in line.said(language).split("\n")))
            for line in part.lines))
    elif part.kind == "table":
        # In a scroller, because a price column that will not wrap is
        # wider than a phone and would otherwise push the whole page
        # sideways.
        drawn = '<div class="scroll" tabindex="0">{}</div>'.format(_table(
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
            '<a class="card" href="{}"><i>{:02d}</i><b>{}</b>'
            '<span>{}</span><em>{} →</em></a>'.format(
                where.page(other), at, _said(other.nav, language),
                _said(other.lead, language), _said(CARD_OPEN, language),
            )
            for at, other in enumerate(
                (one for one in PAGES if one.slug), start=1)
        )
        # The same strip and arrows as the parts' photos: a reader sees
        # there is more to the right without having to find a scrollbar.
        drawn = (
            '<div class="slider pages"><button class="slide-back" '
            'type="button" hidden aria-label="{back}">‹</button>'
            '<div class="cards slides">{cards}</div>'
            '<button class="slide-on" type="button" hidden '
            'aria-label="{on}">›</button></div>'
        ).format(back=_said(SLIDE_BACK, language),
                 on=_said(SLIDE_ON, language), cards=drawn)
        heading = heading.replace("<h2>", '<h2 class="centred">', 1)
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
    elif part.kind == "slides":
        if not part.slides:
            return ""
        drawn = _slides(part.slides, language, where)
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


#: The line at the foot of each page card on the front page.
CARD_OPEN = _w("Sayfaya git", "Open the page")

#: The arrows either side of a strip of slides.
SLIDE_BACK = _w("Önceki", "Previous")
SLIDE_ON = _w("Sonraki", "Next")
#: What stands in a card before its photo: a plain drawing of a part.
PHOTO_CREDIT = _w("Görsel", "Photo")
NO_PHOTO = (
    '<svg viewBox="0 0 48 48" aria-hidden="true" fill="none" '
    'stroke="currentColor" stroke-width="2"><rect x="12" y="12" width="24" '
    'height="24" rx="3"/><path d="M18 12V6M24 12V6M30 12V6M18 42v-6M24 '
    '42v-6M30 42v-6M12 18H6M12 24H6M12 30H6M42 18h-6M42 24h-6M42 30h-6"/>'
    '</svg>'
)


def _slides(slides, language: str, where: Optional["Where"]) -> str:
    """Parts one card each, with the photo when there is one, in a strip
    that slides; the arrows are shown by the script, and without it the
    strip still scrolls."""
    from yerkon.bom import read

    parts = read().parts
    cards = []
    for key, photo in slides:
        if key in parts:
            name = parts[key].called(language)
            role = parts[key].role(language)
        else:
            name = _said(PILOT_ITEMS[key][0], language)
            role = _said(PILOT_ITEMS[key][1], language)
        if photo:
            src = where.asset("photos/" + photo) if where else "photos/" + photo
            shown = '<img src="{}" alt="{}" loading="lazy">'.format(
                html.escape(src, quote=True), html.escape(name, quote=True))
        else:
            shown = '<span class="nophoto">{}</span>'.format(NO_PHOTO)
        credit = ""
        if photo in PHOTO_SOURCES:
            label, url = PHOTO_SOURCES[photo]
            credit = ('<small>{}: <a href="{}" rel="noopener">{}</a></small>'
                      .format(_said(PHOTO_CREDIT, language),
                              html.escape(url, quote=True),
                              html.escape(label)))
        cards.append(
            '<figure class="slide"><div class="photo">{}</div><figcaption>'
            "<b>{}</b><span>{}</span>{}</figcaption></figure>".format(
                shown, html.escape(name), html.escape(role), credit))
    return (
        '<div class="slider"><button class="slide-back" type="button" '
        'hidden aria-label="{back}">‹</button><div class="slides">{cards}'
        '</div><button class="slide-on" type="button" hidden '
        'aria-label="{on}">›</button></div>'
    ).format(back=_said(SLIDE_BACK, language), on=_said(SLIDE_ON, language),
             cards="".join(cards))


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
    "sinyali kestiği için kilometrekareye daha çok birim gerekiyor. "
    "İkisinin de doğruluğu GPS'inkine yakın. Tünel satırı burada yok: o "
    "kilometreye bölünüyor, yani aynı eksene konamaz. Hem maliyetini "
    "hem doğruluğunu yayımlamayan sistem de çizilemedi.",
    "Capital per square kilometre across, horizontal error up, both "
    "from nought. Left and down is better: cheap and precise. The "
    "satellite systems are divided by all the land on earth, YERKON by "
    "each row's own area. YERKON's rural row costs less than the "
    "satellite systems and its town row more: in town buildings cut the "
    "signal, so a square kilometre needs more units. Both are close "
    "to GPS in accuracy. The tunnel row is absent: "
    "it is divided by route kilometre and does not belong on this axis. "
    "A system that publishes only one of the two cannot be drawn "
    "either.",
)
#: The five events the problem page describes, on a line. The year is
#: the fractional one the event happened in, so April 2024 sits a third
#: of the way through its year rather than on its first day.
WHEN = (
    (2017.47, _w("Karadeniz", "The Black Sea"),
     _w("20+ gemi, 32 km sapma", "20+ ships, 32 km out")),
    (2017.75, _w("Norveç", "Norway"),
     _w("Finnmark, 2017'den beri", "Finnmark, since 2017")),
    (2024.3, _w("Baltık", "The Baltic"),
     _w("Tartu bir ay kapalı", "Tartu shut for a month")),
    (2024.26, _w("Tel Aviv", "Tel Aviv"),
     _w("sürücüler Beyrut'ta göründü", "drivers shown in Beirut")),
    (2026.4, _w("ABD", "United States"),
     _w("ambulans uçağı düştü", "air ambulance down")),
)
#: Not drawn: the chart has no heading. Kept as the drawing's name for
#: screen readers.
WHEN_TITLE = _w("Olayların tarihi", "When the events happened")
CLOCKS = (
    ("~270000 TL", _w("birim başına atomik saat, TDoA",
                       "an atomic clock per unit, TDoA")),
    ("0 TL", _w("saat senkronizasyonu, YERKON (çift yönlü ölçüm)",
                "clock synchronisation, YERKON (two way ranging)")),
)
CLOCKS_UNDER = _w(
    "TDoA'da birimlerin saatlerinin birbirine eşitlenmesi, birim başına "
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
    "Yol kenarına dizilmiş "
    "birimlerin hepsi aşağı yukarı aynı yükseklikte, o yüzden yüksekliği "
    "mesafelerden ölçecek geometri yok; düşeyi yükseklik haritasından "
    "gelen yükseklik taşıyor.",
    "Units strung "
    "along a roadside are all at much the same height, so there is no "
    "geometry to measure height from ranges; the height from the "
    "elevation map carries the vertical.",
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
    "Sola doğru daha iyi. Eksen logaritmik, çünkü "
    "değerler santimetreden on beş metreye uzanıyor. Hücresi boş olan "
    "sistem çizilmedi.",
    "Further left is better. The axis is logarithmic because the "
    "figures run from "
    "centimetres to fifteen metres. A system with an empty cell is not "
    "drawn.",
)


#: What each symbol in the drawings means, for the legend under them.
SYMBOLS = {
    "ours": _w("YERKON: bu simülasyonun sonucu",
               "YERKON: what this simulation found"),
    "others": _w("Diğer sistemler: kendi kaynaklarının yayımladığı değer",
                 "Other systems: the figure their own sources publish"),
    "at_most": _w("Üst sınır: kaynak \"en fazla bu kadar\" diyor, gerçek "
                  "değer okun gösterdiği yönde",
                  "A ceiling: the source says \"at most this\", the true "
                  "value lies the way the arrow points"),
    "at_least": _w("Alt sınır: kaynak \"en az bu kadar\" diyor, gerçek "
                   "değer okun gösterdiği yönde",
                   "A floor: the source says \"at least this\", the true "
                   "value lies the way the arrow points"),
    "below": _w("Üst sınır: gerçek değer işaretin altında",
                "A ceiling: the true value lies below the mark"),
    "pair": _w("İki değer: nokta ortalamada, çizginin ucu en kötü konumda",
               "Two figures: the dot on the average, the end of the line "
               "on the worst place"),
    "median": _w("Yatay hatanın ortancası (HPE P50)",
                 "Median horizontal error (HPE P50)"),
    "worst": _w("Yatay hata, en kötü %5 hariç (HPE P95)",
                "Horizontal error, worst 5 % excluded (HPE P95)"),
    "spread": _w("Hataların ortancadan P95'e dağılımı",
                 "How the errors spread, median to P95"),
    "vertical": _w("Düşey hata, en kötü %5 hariç (VPE P95)",
                   "Vertical error, worst 5 % excluded (VPE P95)"),
    "event": _w("Olayın tarihi", "When it happened"),
}


def _legend(kinds, language: str) -> str:
    from yerkon.viewer import charts

    return charts.legend([(kind, SYMBOLS[kind].said(language))
                          for kind in kinds])


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
                label=_in(cells[0], language), figure=figure, ours=True,
                shown=cells[at + 3].strip(),
                short=_in(cells[0], language).replace("YERKON ", "").strip("()"),
            ))
    return out


def _figure(drawn: str, under, language: str, narrow: str = "",
            legend: str = "") -> str:
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
    said = _said(under, language) if under is not None else ""
    caption = "<figcaption>{}</figcaption>".format(said) if said else ""
    return '<figure class="chart">{}{}{}</figure>'.format(body, legend,
                                                          caption)


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
        legend=_legend(charts.symbols_in(marks), language),
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
        legend=_legend(charts.symbols_in([mark for mark, _ in points],
                                         upright=True), language),
    )


def _when(language: str) -> str:
    """The five incidents on one line."""
    from yerkon.viewer import charts

    events = [(year, where.said(language), what.said(language))
              for year, where, what in WHEN]
    return _figure(
        charts.timeline(events, title=WHEN_TITLE.said(language),
                        drawn=False),
        None, language, legend=_legend(("event",), language),
        narrow=charts.timeline_narrow(events,
                                      title=WHEN_TITLE.said(language),
                                      drawn=False),
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
            _in(cells[0], language).replace("YERKON ", "").strip("()"),
            charts.figure_in(cells[3]),
            charts.figure_in(cells[4]),
            charts.figure_in(cells[5]),
        ))
    return _figure(
        charts.spread(rows, title=SPREAD.said(language), unit="m"),
        SPREAD_UNDER, language,
        narrow=charts.spread(rows, title=SPREAD.said(language), unit="m",
                             width=344.0, label_width=76.0, narrow=True),
        legend=_legend(("median", "worst", "spread") + (
            ("vertical",) if any(row[3] is not None for row in rows) else ()),
            language),
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
        legend=_legend(charts.symbols_in(marks), language),
    )


#: The comparison table's YERKON row names, technology and environment
#: columns, in English.
#: They are written once, in Turkish, in comparison.toml and in the
#: scenarios; a new one without an entry here fails a test rather than
#: showing Turkish on the English page.
IN_ENGLISH = {
    "YERKON (Şehir içi)": "YERKON (Urban)",
    "YERKON (Kırsal)": "YERKON (Rural)",
    "YERKON (Tüm Türkiye)": "YERKON (All of Türkiye)",
    "YERKON (Tünel)": "YERKON (Tunnel)",
    "Dış": "Outdoor",
    "İç + dış": "Indoor and outdoor",
    "GNSS": "GNSS",
    "Bölgesel GNSS düzeltme servisi": "Regional GNSS augmentation service",
    "Bölgesel GNSS": "Regional GNSS",
    "Karasal konumlandırma, UHF": "Terrestrial positioning, UHF",
    "Karasal pseudolite konumlandırma": "Terrestrial pseudolite positioning",
    "UWB RTLS": "UWB RTLS",
    "Karasal düşük frekanslı konumlandırma":
        "Terrestrial low frequency positioning",
    "Karasal konumlandırma (E28-2G4M20S, LoRa TWR)":
        "Terrestrial positioning (E28-2G4M20S, LoRa TWR)",
    "Karasal konumlandırma (DWM3000, UWB TWR)":
        "Terrestrial positioning (DWM3000, UWB TWR)",
}


def _in(text: str, language: str) -> str:
    """A row name, technology or environment in the page's language."""
    return text if language == "tr" else IN_ENGLISH.get(text, text)


#: Share of Türkiye under artificial (urban) surfaces in CORINE 2018,
#: 1,99 %, rounded to the 2 % the whole-country row weights by; the rest
#: is taken as rural. Şen (2024), Menba Journal 10(1), table 1.
URBAN_SHARE = 0.02
#: Türkiye's surface area, the General Directorate of Mapping (HGM).
TURKIYE_LAND_KM2 = 780043


def nationwide(published):
    """The whole-country row: urban and rural weighted by area, no tunnels.

    Not a run of its own. Every column is the area weighted mean of the
    two rows it comes from, which for the percentile columns is an
    approximation, and the note on the row says so.
    """
    from dataclasses import replace

    if "urban" not in published.keys or "rural" not in published.keys:
        return None
    urban, rural = published.row("urban"), published.row("rural")

    def mix(name: str) -> float:
        return ((1 - URBAN_SHARE) * getattr(rural, name)
                + URBAN_SHARE * getattr(urban, name))

    return replace(
        rural,
        system="YERKON (Tüm Türkiye)",
        area_km2=float(TURKIYE_LAND_KM2),
        reached_km2=None,
        **{name: mix(name) for name in (
            "hpe_p50_m", "hpe_p95_m", "vpe_p95_m", "availability",
            "capex_tl_per_unit", "opex_tl_per_unit_year")},
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
    # The notes each row points at, in the order it points at them, for
    # the panel its button opens.
    per_row: list = []

    def mark(key: str) -> str:
        if key not in numbered:
            numbered[key] = len(numbered) + 1
        if per_row and key not in per_row[-1][1]:
            per_row[-1][1].append(key)
        at = numbered[key]
        return (
            '<sup class="note"><a id="back{0}" href="#note{0}">{0}</a>'
            "</sup>".format(at)
        )

    def said_in(text: str) -> str:
        return _in(text, language)

    def words(text: str) -> str:
        return html.escape(said_in(text))

    def cell(text: str) -> str:
        from yerkon.comparison import keys_of, without_markers

        shown = html.escape(without_markers(text))
        return shown + "".join(mark(key) for key in keys_of(text))

    head = [_said(column, language) for column in COLUMNS]
    # The warning about the availability column belongs to the column.
    head[6] += mark(table.availability_note)

    body = []
    for row in table.rows:
        per_row.append((row.system, []))
        body.append(
            [html.escape(row.system), words(row.technology),
             words(row.environment)] + [cell(one) for one in row.cells]
        )
    ours = len(body)
    for key, row in zip(published.keys, published.rows):
        cells = list(row.cells())
        per_row.append((said_in(cells[0]), []))
        marked = [words(cells[0]), words(cells[1]), words(cells[2])]
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
    whole = nationwide(published)
    if whole is not None:
        cells = list(whole.cells())
        per_row.append((said_in(cells[0]), []))
        marked = [words(cells[0]), words(cells[1]), words(cells[2])]
        marked[0] += mark(table.yerkon["nationwide"])
        rest = [html.escape(one) for one in cells[3:]]
        rest[3] += mark(table.yerkon["availability"])
        rest[4] = "≈ " + decimal_comma(TURKIYE_LAND_KM2, 0)
        rest[5] += mark(table.yerkon["capex"])
        rest[6] += mark(table.yerkon["capex"])
        body.append(marked + rest)
    # The template is escaped once, by `_said`. What comes out of the
    # record is escaped here, and escaping the result again would put
    # `&amp;#x27;` on the page where an apostrophe belongs.
    bibliography = sources.read()

    def explained(key: str) -> str:
        return _marked(table.said(key, language)) + _cited(
            table.notes[key].get("sources", ()), bibliography, language)

    listed = "".join(
        '<li id="note{0}">{1} <a class="back" href="#back{0}">↑</a></li>'
        .format(at, explained(key))
        for key, at in sorted(numbered.items(), key=lambda pair: pair[1])
    )
    # A button at the end of each row opens every note the row points
    # at, with its sources, over the page. The panels are drawn here and
    # kept hidden; the script only moves one into view.
    head.append('<span class="hide">{}</span>'.format(
        _said(ROW_BASIS, language)))
    panels = []
    for line, (system, keys) in enumerate(per_row):
        body[line].append(
            '<button class="rowinfo" type="button" data-row="{0}" '
            'title="{1}" aria-label="{1}: {2}">{3}</button>'.format(
                line, _said(ROW_BASIS, language), html.escape(system),
                INFO_ICON))
        panels.append(
            '<section data-row="{}"><h2>{}</h2><ol>{}</ol></section>'.format(
                line, html.escape(system), "".join(
                    '<li value="{}">{}</li>'.format(numbered[key],
                                                    explained(key))
                    for key in keys)))
    if language == "en":
        body = [[_english_cell(cell) for cell in row] for row in body]
    return (
        '<div class="wide"><div class="scroll" tabindex="0">{table}</div></div>'
        '<div class="rowpanels" hidden>{panels}</div>'
        '<details class="fold notes"><summary><h2>{heading}</h2></summary>'
        '<ol class="notes">{notes}</ol></details>'
    ).format(
        table=_table([head] + body, numeric_from=3, ours_from=ours,
                     last="info"),
        notes=listed, panels="".join(panels),
        heading=_said(NOTES_HEADING, language).format(count=len(numbered)),
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


def _english_cell(cell: str) -> str:
    """A table cell as English writes it: "million" for "milyon" and the
    per cent sign after the number, the way the English notes write it
    ("95 %"). The record keeps the Turkish forms the report prints."""
    cell = cell.replace(" milyon", " million")
    return re.sub(r"%(\d[\d.,]*)", r"\1 %", cell)


def _table(
    rows: Sequence[Sequence[str]],
    numeric_from: int = 99,
    ours_from: Optional[int] = None,
    last: str = "",
) -> str:
    """One table. ``ours_from`` marks where this project's rows start;
    ``last`` names a class for the final column when it is not data."""
    head, body = rows[0], rows[1:]

    def kind(at: int, width: int) -> str:
        if last and at == width - 1:
            return ' class="{}"'.format(last)
        return ' class="num"' if at >= numeric_from else ""

    out = ["<table><thead><tr>"]
    for at, cell in enumerate(head):
        # A heading is kept on one line, so a long one is broken where it
        # says, with a newline, rather than wherever the column ends.
        out.append('<th{}>{}</th>'.format(
            kind(at, len(head)), cell.replace("\n", "<br>")))
    out.append("</tr></thead><tbody>")
    for line, row in enumerate(body):
        ours = ours_from is not None and line >= ours_from
        out.append('<tr class="ours">' if ours else "<tr>")
        for at, cell in enumerate(row):
            out.append('<td{}>{}</td>'.format(kind(at, len(row)), cell))
        out.append("</tr>")
    out.append("</tbody></table>")
    return "".join(out)


# --- writing it out -------------------------------------------------------

#: Files copied beside the pages rather than rendered.
CARRIED = ("site.css", "theme.js", "road.webp", "gnss.webp",
           "architecture.webp", "simulator.webp", "yerkon-rapor.pdf",
           "favicon.svg",
           "favicon.ico", "apple-touch-icon.png", "icon-192.png",
           "icon-512.png")

#: Each picture's pixel size. WebP rather than PNG: the four came to
#: 1,5 MB as PNG and 216 KB as WebP at quality 85, with the lettering in
#: the diagrams still sharp.
PICTURE_SIZES = {
    "road.webp": (1200, 896),
    "gnss.webp": (700, 701),
    "architecture.webp": (1200, 800),
    "simulator.webp": (1600, 1000),
}

STATIC = pathlib.Path(__file__).parent / "static"


#: The simulator's page on the published site, and what it needs beside it.
BROWSER_SIMULATOR = "calistir/"
#: Its page, in a folder of its own so the address needs no ".html".
BROWSER_SIMULATOR_PAGE = "calistir/index.html"
#: Where the site lives. GitHub Pages reads this file to serve the
#: domain, and the folder is pushed afresh each time, so it is drawn with
#: the pages rather than set once by hand (ADR-0112).
DOMAIN = "yerkon.com"
BROWSER_SCRIPTS = ("app.js", "draw.js", "bore.js", "words.js", "map.js",
                   "style.css", "local.js", "sim-worker.js")
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


#: What a page of the site may load and talk to, said in the page because
#: GitHub Pages sends no headers of its own: its own scripts, pictures
#: and fonts, and nothing else. No page has an inline script or
#: style to allow, and the one place that writes a script, the address
#: forwarders, carries no rule because it carries no content.
PAGE_POLICY = (
    "default-src 'self'; script-src 'self'; "
    "style-src 'self'; font-src 'self'; img-src 'self' data:; "
    "connect-src 'self'; object-src 'none'; base-uri 'self'; "
    "form-action 'none'; upgrade-insecure-requests"
)

#: The simulator's, wider by exactly what it reaches for from the page:
#: the map's tiles, the place search, the satellite picture, and the
#: ground, buildings and roads a fetch brings. The engine itself runs in
#: a worker, which answers to its own address rather than to this rule.
SIMULATOR_POLICY = (
    "default-src 'self'; script-src 'self'; worker-src 'self' blob:; "
    "style-src 'self' 'unsafe-inline'; font-src 'self'; "
    "img-src 'self' data: blob: https://tile.openstreetmap.org "
    "https://server.arcgisonline.com; "
    "connect-src 'self' data: blob: https://nominatim.openstreetmap.org "
    "https://tile.openstreetmap.org https://server.arcgisonline.com "
    "https://cdn.jsdelivr.net https://overpass-api.de "
    "https://*.amazonaws.com https://api.opentopodata.org; "
    "object-src 'none'; base-uri 'self'; form-action 'none'; "
    "upgrade-insecure-requests"
)

#: Where a link from the site goes, the receiving site sees the domain
#: and not the page.
REFERRER = '<meta name="referrer" content="strict-origin-when-cross-origin">'


def browser_simulator() -> dict:
    """The simulator's files for a folder served by nothing, by name."""
    page = _loose((STATIC / "simulator.html").read_text(encoding="utf-8"), (
        # The page sits in calistir/ and everything it loads at the root:
        # one base puts every relative address, the worker's included,
        # where the files are.
        ('<meta charset="utf-8">',
         '<meta charset="utf-8">\n<base href="../">\n'
         '<meta http-equiv="Content-Security-Policy" content="{}">\n{}'.format(
             SIMULATOR_POLICY, REFERRER)),
        ('href="/style.css"', 'href="style.css"'),
        ('href="/favicon.ico"', 'href="favicon.ico"'),
        ('href="/favicon.svg"', 'href="favicon.svg"'),
        ('<a id="back" href="/"', '<a id="back" href="tr/"'),
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
    files = {BROWSER_SIMULATOR_PAGE: page.encode("utf-8")}
    for name in BROWSER_SCRIPTS:
        body = (STATIC / name).read_bytes()
        if name == "app.js":
            body = _loose(body.decode("utf-8"), (
                ('from "/words.js"', 'from "./words.js{}"'.format(tag)),
                ('from "/draw.js"', 'from "./draw.js{}"'.format(tag)),
                ('from "/map.js"', 'from "./map.js{}"'.format(tag)),
                ('from "/bore.js"', 'from "./bore.js{}"'.format(tag)),
            )).encode("utf-8")
        elif name == "bore.js":
            body = _loose(body.decode("utf-8"), (
                ('from "/draw.js"', 'from "./draw.js{}"'.format(tag)),
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
    written = []

    def put(name: str, body: bytes) -> None:
        path = into / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(body)
        written.append(path)

    for code, _ in LANGUAGES:
        for page in PAGES:
            where = Where(language=code, loose=True, at=page)
            put(Where.file(page, code),
                render(page, code, published, where).encode("utf-8"))
    for name in CARRIED:
        put(name, (STATIC / name).read_bytes())
    # The typeface and its licence, which travels with it (OFL 1.1, §2).
    for name in FONTS:
        put("fonts/" + name, (STATIC / "fonts" / name).read_bytes())
    # The parts' photos, whatever is in the folder (Part.slides).
    for photo in sorted((STATIC / "photos").iterdir()):
        if photo.suffix.lower() in (".webp", ".jpg", ".jpeg", ".png"):
            put("photos/" + photo.name, photo.read_bytes())
    # The simulator itself, running in the visitor's browser (ADR-0080).
    for name, body in browser_simulator().items():
        put(name, body)
    # The domain's root and every address the site had before its pages
    # moved into folders: each sends the visitor on, so a link somebody
    # kept still arrives (ADR-0112).
    # The domain's own address is the Turkish front page itself rather
    # than a page that sends the visitor there: a reader that does not
    # run scripts or follow a refresh, as most AI tools and some search
    # engines do not, found only the word YERKON at yerkon.com.
    put("index.html", _at_root(
        render(PAGES[0], "tr", published,
               Where(language="tr", loose=True, at=PAGES[0]))))
    put("robots.txt", _robots())
    put("sitemap.xml", _sitemap())
    put("llms.txt", _llms())
    for page in PAGES:
        # The front pages are tr/ and en/ themselves: en/index.html is the
        # English front page, not a way to it.
        if page.slug:
            put(page.slug + ".html", _onward(Where.folder(page, "tr")))
            put("en/" + page.slug + ".html", _onward(page.slug_in("en") + "/"))
            # The English pages were once at their Turkish names; those
            # addresses send the visitor on to the English ones.
            if page.slug_in("en") != page.slug:
                put("en/" + page.slug + "/index.html",
                    _onward("../" + page.slug_in("en") + "/"))
    put("calistir.html", _onward(BROWSER_SIMULATOR, keep_query=True))
    put("CNAME", (DOMAIN + "\n").encode("utf-8"))
    # Without this the pages are handed to Jekyll, which is a static site
    # generator this site is not written for.
    put(".nojekyll", b"")
    # A page that has been renamed or dropped leaves its file behind,
    # and a stale page nothing links to is still a page the address
    # serves. Only the pages are swept: the folder holds other things.
    kept = set(written)
    swept = list(into.glob("*.html"))
    for folder in ("tr", "en", "calistir"):
        swept += list((into / folder).rglob("*.html"))
    for stale in swept:
        if stale not in kept:
            stale.unlink()
    return tuple(written)


def _at_root(page: str) -> bytes:
    """The Turkish front page, drawn for tr/, served at the root.

    One base puts every relative address where it points from tr/, and
    the canonical address tells a search engine which copy is the page.
    """
    return page.replace(
        '<meta charset="utf-8">',
        '<meta charset="utf-8">\n<base href="tr/">', 1,
    ).encode("utf-8")


def _robots() -> bytes:
    """Every reader is welcome, and told where the list of pages is."""
    return ("User-agent: *\nAllow: /\n\nSitemap: https://{}/sitemap.xml\n"
            .format(DOMAIN)).encode("utf-8")


def _sitemap() -> bytes:
    """Every page in both languages, for a search engine to find."""
    addresses = "".join(
        "<url><loc>https://{}/{}</loc></url>\n".format(
            DOMAIN, Where.folder(page, code))
        for code, _ in LANGUAGES for page in PAGES
    )
    return ('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
            "{}</urlset>\n").format(addresses).encode("utf-8")


def _plain(words: str) -> str:
    """A phrase without its emphasis marks, its links kept as Markdown."""
    return words.replace("**", "").replace("`", "")


def _llms() -> bytes:
    """The site in a few lines of Markdown, for a language model.

    The llms.txt convention: a title, a summary, then the pages worth
    reading with a line on each.
    """
    lines = ["# YERKON", "", "> " + _plain(PAGES[0].lead.tr), "",
             "> " + _plain(PAGES[0].lead.en), "",
             "- [Proje dokümanı / Project document (PDF, Türkçe)]"
             "(https://{}/yerkon-rapor.pdf)".format(DOMAIN), ""]
    for code, heading in (("tr", "## Sayfalar (Türkçe)"),
                          ("en", "## Pages (English)")):
        lines += [heading, ""]
        for page in PAGES:
            lines.append("- [{}](https://{}/{}): {}".format(
                page.nav.said(code), DOMAIN, Where.folder(page, code),
                _plain(page.lead.said(code))))
        lines.append("")
    return "\n".join(lines).encode("utf-8")


def _tagged(name: str) -> str:
    """A file's address with a tag drawn from its contents.

    GitHub Pages lets a browser keep a file ten minutes, so a changed
    header went out beside the old stylesheet and the bar broke in two;
    a changed file now has a new address, as the simulator's do.
    """
    digest = hashlib.sha256((STATIC / name).read_bytes()).hexdigest()
    return "{}?v={}".format(name, digest[:10])


def _onward(to: str, keep_query: bool = False) -> bytes:
    """A page that only sends the visitor to `to`."""
    target = html.escape(to, quote=True)
    carry = "+location.search+location.hash" if keep_query else "+location.hash"
    return (
        "<!doctype html>\n<html>\n<head>\n<meta charset=\"utf-8\">\n"
        '<meta http-equiv="refresh" content="0; url={0}">\n'
        '<link rel="canonical" href="{0}">\n'
        "<title>YERKON</title>\n"
        "<script>location.replace({1}{2})</script>\n"
        "</head>\n<body><a href=\"{0}\">YERKON</a></body>\n</html>\n"
    ).format(target, json.dumps(to), carry).encode("utf-8")


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
    # mailto: too, for the team's addresses on the front page.
    out = re.sub(
        r"\[([^\]]+)\]\(((?:https?://|mailto:)[^)\s]+)\)",
        r'<a href="\2">\1</a>',
        out,
    )
    # A range ("10-15", "2.500-8.000") stays on one line: a browser
    # breaks after a hyphen, and "10-" at the end of a line with "15" on
    # the next reads as two numbers. Text only, never inside a tag.
    return "".join(
        piece if piece.startswith("<") else _RANGED.sub(
            r'<span class="nb">\g<0></span>', piece)
        for piece in re.split(r"(<[^>]+>)", out))


_RANGED = re.compile(r"(?<![\w\-])\d[\d.,]*-\d[\d.,]*(?![\w\-])")


def _pdfs_apart(page: str) -> str:
    """Every link to a PDF opens in a tab of its own, so the page the
    reader came from stays where it was."""
    def opened(found) -> str:
        address = html.unescape(found.group(1)).lower().split("#")[0]
        path = address.split("://", 1)[-1].split("?")[0].split("/")[1:]
        # A maker's download page can hand over a PDF from an address
        # that never ends in .pdf (pdf-down.aspx, downpdf/304.html).
        if not (address.endswith(".pdf") or any("pdf" in part
                                                 for part in path)):
            return found.group(0)
        return found.group(0)[:-1] + ' target="_blank" rel="noopener">'

    return re.sub(r'<a href="([^"]+)"(?![^>]*target=)[^>]*>', opened, page)
