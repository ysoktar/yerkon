"""Which language the study speaks, and the sentences it builds itself.

Two, and they are not a translation of one another in the sense that one
is the original: the figures, the notes and the reasons are written in
both and the file carries both. Turkish because the report this answers
is Turkish and the people who will check it work in Turkish; English
because the code, the decisions and the tests are in English and a reader
of those should not have to leave them to read what a figure means.

Nothing here decides anything. A language chooses which of two strings is
shown, and no number, no geometry and no result differs between them. A
test pins that: the whole table is built twice and the figures match.

Two kinds of text live in two different places, on purpose.

Text somebody *wrote* — what a figure rests on, what an option buys —
lives beside the value it describes, in ``defaults.toml`` and in the
option files, as ``note`` and ``note_en``. Keeping both beside one value
is what stops the two languages drifting into two different claims about
the same number.

Text this project *builds* — "rolling, 400 m over 1200 m" — lives here,
as a pair of format strings under one name. There are few of them and
they are the ones that would otherwise be hardcoded mid-computation.
"""

from __future__ import annotations

#: The languages, in the order a chooser should offer them.
LANGUAGES = ("tr", "en")

#: What each is called, in itself.
LANGUAGE_NAMES = {"tr": "Türkçe", "en": "English"}

#: The one a caller gets when it does not say.
#:
#: Turkish, because the report is Turkish and the viewer is the main way
#: into this project (ADR-0035).
DEFAULT_LANGUAGE = "tr"


#: Numbers are written the same way in both.
#:
#: A comma decimal mark and no thousands separator, which is what the
#: report uses. The English here is a way into the same study rather than
#: a second study, and a figure with two written forms is a figure
#: somebody can quote two ways.
NUMBERS_ARE_TURKISH = True


def chosen(language: str | None) -> str:
    """A language name, checked, or the default when none was given."""
    if language is None:
        return DEFAULT_LANGUAGE
    if language not in LANGUAGES:
        raise ValueError(
            "no language called {!r}. There are: {}".format(
                language, ", ".join(LANGUAGES)
            )
        )
    return language


#: Every sentence this project builds rather than reads from a file.
#:
#: One name, two format strings, the same fields in both. A sentence
#: missing from either language fails a test rather than falling back,
#: because a fallback is a half-translated page nobody notices.
CATALOGUE: dict[str, dict[str, str]] = {
    # -- the three rows of the table ---------------------------------------
    "row.urban": {"tr": "Şehir içi", "en": "Urban"},
    "row.rural": {"tr": "Kırsal", "en": "Rural"},
    "row.tunnel": {"tr": "Tünel", "en": "Tunnel"},
    "row.weighted": {"tr": "Ağırlıklı Ortalama", "en": "Weighted mean"},
    # -- what the ground is -----------------------------------------------
    "terrain.flat": {
        "tr": "{elevation_m:.0f} m'de düz",
        "en": "flat at {elevation_m:.0f} m",
    },
    "terrain.flat.plain": {"tr": "düz", "en": "flat"},
    "terrain.rolling": {
        "tr": "tepeli, {wavelength_m:.0f} m'de {amplitude_m:.0f} m",
        "en": "rolling, {amplitude_m:.0f} m over {wavelength_m:.0f} m",
    },
    "terrain.bore": {
        "tr": "tünel, {length_m:.0f} m'de %{grade}",
        "en": "bore, {grade}% over {length_m:.0f} m",
    },
    "terrain.bore.through": {
        "tr": "{site} içinden tünel, portalları {source} kaynağından",
        "en": "bore through {site}, portals from {source}",
    },
    # -- what a fetched site is -------------------------------------------
    "site.ground": {
        "tr": "{source} kaynağından zemin, {resolution_m:.0f} m çözünürlükte",
        "en": "ground from {source} at {resolution_m:.0f} m",
    },
    "site.buildings": {
        "tr": "{source} kaynağından {count} bina",
        "en": "{count} buildings from {source}",
    },
    "site.no_buildings": {
        "tr": "bina verisi yok, bu yüzden her yerde açık arazi varsayıldı",
        "en": "no building data, so open ground is assumed everywhere",
    },
    "site.heights_tagged": {
        "tr": "{tagged} bina yüksekliği etiketlenmiş, {levels} tanesi kat "
              "sayısından, {defaulted} tanesi {default_m:.0f} m varsayıldı",
        "en": "{tagged} building heights tagged, {levels} from storey "
              "counts, {defaulted} defaulted to {default_m:.0f} m",
    },
    "site.footprints": {
        "tr": "Taban alanları, yükseklikten çıkarılan bir alana sahip "
              "dairelerdir; çünkü OpenStreetMap'ten dış hatlar değil "
              "merkezler getirildi. Bir link bütçesi yalnızca bir binanın "
              "yolda olup olmadığını sorar.",
        "en": "Footprints are circles of an area implied by height, "
              "because OpenStreetMap centres were fetched rather than "
              "outlines. A link budget only asks whether a building is in "
              "the way.",
    },
    "site.unreachable": {
        "tr": "{name} erişilemedi: {error}",
        "en": "{name} unavailable: {error}",
    },
    "site.no_answer": {
        "tr": "{name} cevap vermedi: {error}",
        "en": "{name} did not answer: {error}",
    },
    "site.footprints_measured": {
        "tr": "Taban alanları, her binanın kendi sınır kutusundan ölçüldü "
              "({release} sürümü); yükseklikten çıkarılmadı.",
        "en": "Footprints are measured from each building's own bounding "
              "box (release {release}), not implied by height.",
    },
    "point.none": {
        "tr": "Merkez girilmedi. Haritada yere sağ tıklayıp koordinatı "
              "yapıştır, örneğin 39,9250 32,8370",
        "en": "No centre given. Right-click the place on a map and paste "
              "what it gives you, for example 39.9250, 32.8370",
    },
    "point.unreadable": {
        "tr": "{text!r} bir enlem ve boylam olarak okunmuyor. 39,9250 "
              "32,8370 ya da 39.9250, 32.8370 gibi yaz.",
        "en": "{text!r} does not read as a latitude and a longitude. Write "
              "them as 39,9250 32,8370 or 39.9250, 32.8370",
    },
    "point.not_a_latitude": {
        "tr": "{value} bir enlem değil; enlem -90 ile 90 arasındadır. "
              "Önce enlem yazılır.",
        "en": "{value} is not a latitude; it runs from -90 to 90. Latitude "
              "comes first.",
    },
    "point.not_a_longitude": {
        "tr": "{value} bir boylam değil; boylam -180 ile 180 arasındadır.",
        "en": "{value} is not a longitude; it runs from -180 to 180.",
    },
    # -- routes a receiver drives (ADR-0045) -------------------------------
    "route.site": { "tr": "Sahanın kendi şekli", "en": "The site's own shape" },
    "route.line": { "tr": "Düz çizgi", "en": "A straight line" },
    "route.out-and-back": { "tr": "Gidiş-dönüş", "en": "Out and back" },
    "route.circuit": { "tr": "Çevre turu", "en": "A circuit" },
    "route.figure-eight": { "tr": "Sekiz çizme", "en": "A figure of eight" },
    "route.lawnmower": { "tr": "Tarama (biçerdöver)", "en": "Lawnmower passes" },
    "route.waypoints": { "tr": "Rastgele duraklar", "en": "Random waypoints" },
    "route.road": { "tr": "Gerçek yol", "en": "The real road" },
    "route.no_road": {
        "tr": "Bu zemin yol geometrisi taşımıyor, o yüzden gerçek yol "
              "çizilemiyor. Getirmenin yolları da alması gerekir.",
        "en": "This ground carries no road geometry, so the real road "
              "cannot be drawn. A fetch has to bring roads too.",
    },
    "deployment.no_anchors": {
        "tr": "Direk yok: ya her dizi hiç yerleştirmiyor ya da hepsi "
              "silinmiş. `manual` yerleşimi bilerek hiç koymaz — elle "
              "direk sürükle ya da başka bir yöntem seç. (Boş bir düzenleme "
              "çizilebilir; koşturulamaz.)",
        "en": "No anchors: every run either places none or has had them all "
              "removed. The `manual` layout places none on purpose — drag "
              "anchors in, or choose another method. (An empty arrangement "
              "can be drawn; it cannot be run.)",
    },
    # -- named arrangements (ADR-0043) ------------------------------------
    "preset.bad_name": {
        "tr": "{name!r} bir düzenleme adı değil: harf ya da rakamla başlar, "
              "içinde harf, rakam, tire ve alt çizgi olur.",
        "en": "{name!r} is not an arrangement name: it starts with a letter "
              "or a digit and holds letters, digits, dashes and underscores.",
    },
    "preset.unknown": {
        "tr": "{directory} içinde {name!r} diye bir düzenleme yok. "
              "Olanlar: {known}",
        "en": "No arrangement called {name!r} in {directory}. "
              "There are: {known}",
    },
    "preset.unreadable": {
        "tr": "{path} okunamadı: {error}",
        "en": "{path} could not be read: {error}",
    },
    "preset.incomplete": {
        "tr": "{source} bir düzenleme değil; eksik olan: {missing}",
        "en": "{source} is not an arrangement; it is missing: {missing}",
    },
    "preset.from": {
        "tr": "{mode} satırı {name!r} düzenlemesinden koştu "
              "({source}, içerik {digest})",
        "en": "the {mode} row ran from the arrangement {name!r} "
              "({source}, contents {digest})",
    },
    "preset.default": {"tr": "Varsayılan", "en": "Default"},
    "preset.empty": {"tr": "Boş", "en": "Empty"},
    "site.roads": {
        "tr": "{name} kaynağından {count} yol parçası ({classes})",
        "en": "{count} road segments from {name} ({classes})",
    },
    "site.no_roads": {
        "tr": "{name} bu kutuda sürülecek yol bulamadı",
        "en": "{name} found no road to drive in this box",
    },
    "site.furniture": {
        "tr": "{name} kaynağından direğe uygun {count} yapı ({kinds})",
        "en": "{count} mountable structures from {name} ({kinds})",
    },
    "site.no_furniture": {
        "tr": "{name} bu kutuda direğe uygun yapı bulamadı",
        "en": "{name} found no mountable structure in this box",
    },
    "site.needs_pillow": {
        "tr": "Hava görüntüsü Pillow paketini gerektirir: "
              "pip install \"yerkon[sites]\"",
        "en": "Aerial imagery needs Pillow: pip install \"yerkon[sites]\"",
    },
    "site.no_imagery_url": {
        "tr": "Hava görüntüsü için bir karo adresi verilmedi. Sağlayıcıyı "
              "sen seçiyorsun: her birinin kendi koşulları var ve çoğu "
              "anahtar istiyor. Örnekler docs/TRY-IT.md içinde.",
        "en": "No tile URL given for the imagery. You choose the provider: "
              "each has its own terms and most want a key. Examples are in "
              "docs/TRY-IT.md.",
    },
    "site.too_many_tiles": {
        "tr": "{tiles} karo, {zoom} yakınlıkta — sınır {most}. Daha düşük "
              "bir yakınlık ya da daha küçük bir kutu seç.",
        "en": "{tiles} tiles at zoom {zoom}, and the limit is {most}. Pick a "
              "lower zoom or a smaller box.",
    },
    "site.no_tiles": {
        # No name in it: the note that carries this to a person already
        # names the source, and "aerial imagery unreachable: aerial
        # imagery returned no tiles" is a sentence nobody wrote on
        # purpose.
        "tr": "hiçbir karo dönmedi. Adres şablonunu, anahtarı ve ağı "
              "denetle.",
        "en": "no tiles came back at all. Check the URL template, the key "
              "and the network.",
    },
    "site.aerial": {
        # Pre-formatted by the caller rather than `:.2f` here, because
        # this project writes a comma decimal mark and a format spec
        # would write a dot. The neighbouring elevation phrase gets away
        # with `:.0f` only because no separator ever shows.
        "tr": "{source} kaynağından hava görüntüsü, {resolution_m} m/piksel",
        "en": "aerial imagery from {source} at {resolution_m} m/pixel",
    },
    "site.needs_pyarrow": {
        "tr": "Overture erişimi pyarrow paketini gerektirir: "
              "pip install \"yerkon[sites]\"",
        "en": "Overture access needs pyarrow: pip install \"yerkon[sites]\"",
    },
    "site.needs_requests": {
        "tr": "OpenStreetMap erişimi requests paketini gerektirir.",
        "en": "OpenStreetMap access needs requests.",
    },
    "site.no_elevation": {
        "tr": "Hiçbir yükseklik kaynağı cevap vermedi.\n  {detail}",
        "en": "No elevation source answered.\n  {detail}",
    },
    "site.no_sources": {
        "tr": "hiçbir kaynak verilmedi",
        "en": "no sources were given",
    },
    # -- what the solver was asked for, and what it found ------------------
    "target.availability": {
        "tr": "kullanılabilirlik ≥ %{availability}",
        "en": "availability ≥ {availability} %",
    },
    "target.hpe_p50": {"tr": "HPE P50 ≤ {value} m", "en": "HPE P50 ≤ {value} m"},
    "target.hpe_p95": {"tr": "HPE P95 ≤ {value} m", "en": "HPE P95 ≤ {value} m"},
    "target.fixes": {
        "tr": "saniyede {value} sabitleme",
        "en": "{value} fixes a second",
    },
    "target.nothing": {
        "tr": "belirli bir şey değil",
        "en": "nothing in particular",
    },
    "solve.none_met": {
        "tr": "{target} koşulunu hiçbir düzen karşılamadı; kaydedilecek bir "
              "seçenek yok",
        "en": "nothing met {target}; there is no option to save",
    },
    "solve.already_met": {
        "tr": "ayarlar {target} koşulunu zaten karşılıyor; onu karşılayan en "
              "ucuz düzen elindeki düzenin kendisi, yani kaydedilecek bir "
              "şey yok",
        "en": "the settings already meet {target}; the cheapest arrangement "
              "that meets it is the one you have, so there is nothing to "
              "save",
    },
    "solve.title": {
        "tr": "{scenario}: {target} — {anchors} direk, {capex} TL",
        "en": "{scenario}: {target} — {anchors} anchors, {capex} TL",
    },
    "solve.note": {
        "tr": "{scenario} satırının {tried} düzeni, üzerinde durduğu gerçek "
              "zemine karşı denenerek bulundu; {target} koşulunu "
              "karşılayanların en ucuzu tutuldu.\n\n"
              "{anchors} direkle, %{availability} kullanılabilirlik, "
              "ellinci yüzdelikte {hpe_p50} m ve doksan beşinci yüzdelikte "
              "{hpe_p95} m, saniyede {fixes} sabitleme veriyor.\n\n"
              "Her aday, uydurulmuş bir model değil tam bir benzetimdi; "
              "yani bu sayılar tablonun geldiği motorun ta kendisinden "
              "geliyor (ADR-0023).",
        "en": "Found by searching {tried} arrangements of the {scenario} "
              "row against the real ground it stands on, and keeping the "
              "cheapest that met {target}.\n\n"
              "It delivers {availability} % availability, {hpe_p50} m at "
              "the fiftieth percentile and {hpe_p95} m at the ninety-fifth, "
              "at {fixes} fixes a second, from {anchors} anchors.\n\n"
              "Every candidate was a full simulation rather than a fitted "
              "model, so these figures come from the same engine the table "
              "does (ADR-0023).",
    },
    # -- the named ways of laying anchors out ------------------------------
    #
    # Each one says what it does rather than what it is called, because
    # "hex" means nothing to somebody who has not read the module and
    # "the fewest anchors that cover an area" means everything.
    "layout.grid": {
        "tr": "Kare ızgara — kaydırmalı satırlar",
        "en": "Square grid — staggered rows",
    },
    "layout.hex": {
        "tr": "Altıgen kafes — bir alanı en az direkle örter",
        "en": "Hexagonal lattice — fewest anchors to cover an area",
    },
    "layout.corridor": {
        "tr": "Yol boyunca — iki yanda dönüşümlü",
        "en": "Along the route — alternating sides",
    },
    "layout.perimeter": {
        "tr": "Çevre — yalnızca sahanın kenarında",
        "en": "Perimeter — round the edge of the site only",
    },
    "layout.greedy-coverage": {
        "tr": "Arama: en çok zemini örten (klasik kapsama)",
        "en": "Search: most ground covered (the coverage classic)",
    },
    "layout.greedy-dop": {
        "tr": "Arama: en iyi geometri (konum için doğru ölçüt)",
        "en": "Search: best geometry (the right score for a fix)",
    },
    "layout.k-cover": {
        "tr": "Arama: her noktaya yeter sayıda direk",
        "en": "Search: enough anchors over every point",
    },
    "layout.manual": {
        "tr": "Elle — hiçbiri; boştan başla",
        "en": "By hand — none; start from empty",
    },
    "layout.needs_map": {
        "tr": "Bu yöntem yol kenarındaki yapıları kullanır; bu zemin "
              "getirilmiş yol verisi taşımıyor.",
        "en": "This method uses the structures beside the road, and this "
              "ground carries no fetched road data.",
    },
    # -- why the confirmation panel says a figure has to move ------------
    "panel.past_the_site": {
        "tr": "sahanın ucunu geçen bir direk, hiçbir şeyin modellemediği "
              "zeminde durur ve hiçbir birim oradan geçmez",
        "en": "an anchor past the end of the site stands on ground nothing "
              "models and nothing drives past",
    },
    "panel.past_the_measurement": {
        "tr": "bir saha, kendisi için indirilen zeminden büyük olamaz; "
              "kenarın ötesinde yalnızca sınır satırının bir düzleme "
              "uzatılmışı vardır",
        "en": "a site is no larger than the ground fetched for it; past the "
              "edge there is only the boundary row extruded into a plane",
    },
    "panel.site_length": {"tr": "Sahanın boyu", "en": "The site's length"},
    "panel.site_width": {"tr": "Sahanın eni", "en": "The site's width"},
    "panel.ground": {"tr": "Zemin", "en": "Ground"},
    # -- what a long task says while it runs -------------------------------
    #
    # These are the lines the page shows while a job is going. They are
    # here rather than beside the code that prints them for the same
    # reason everything else is: a task started from the page in English
    # that reports in Turkish is the half-and-half surface ADR-0035 was
    # written to end.
    "task.table.running": {
        "tr": "{rows} satır {workers} süreçte çalışıyor.",
        "en": "Running {rows} row{s} on {workers} processes.",
    },
    "task.budget.running": {
        "tr": "{runs} benzetim çalışıyor: {rows} senaryo, {sources} hata "
              "kaynağına karşı, {workers} süreçte.",
        "en": "Running {runs} simulations: {rows} scenario{s} against "
              "{sources} sources, on {workers} processes.",
    },
    "task.done": {"tr": "Bitti.", "en": "Done."},
    "task.solve.searching": {
        "tr": "{scenario} için {candidates} düzen, {target} hedefine karşı, "
              "{workers} süreçte aranıyor.",
        "en": "Searching {candidates} arrangements of {scenario} for "
              "{target}, on {workers} processes.",
    },
    "task.solve.candidate": {
        "tr": "[{seen}/{candidates}] {anchors} direk · {availability} "
              "kullanılabilirlik · HPE50 {hpe_p50} m · {capex} TL{meets}",
        "en": "[{seen}/{candidates}] {anchors} anchors · {availability} "
              "availability · HPE50 {hpe_p50} m · {capex} TL{meets}",
    },
    "task.solve.meets": {"tr": "  ← karşılıyor", "en": "  ← meets"},
    "task.solve.none_met": {
        "tr": "Hiçbiri karşılamadı.",
        "en": "Nothing met it.",
    },
    "task.solve.met": {
        "tr": "{tried} düzenin {met} tanesi karşıladı.",
        "en": "{met} of {tried} met it.",
    },
    "task.solve.saved": {
        "tr": "{name} olarak kaydedildi.",
        "en": "Saved as {name}.",
    },
    # A middle dot rather than a comma between the two halves of a
    # coordinate: the decimal mark here is a comma too (ADR-0035), and
    # "39,9208,32,8541" is four numbers to anybody reading it.
    "task.fetch.fetching": {
        "tr": "{south} · {west} ile {north} · {east} arası {spacing_m} m "
              "aralıkla indiriliyor.",
        "en": "Fetching {south} · {west} to {north} · {east} at "
              "{spacing_m} m.",
    },
    "task.fetch.slow": {
        "tr": "Buradaki ağı kullanan tek şey. Bir süre alabilir.",
        "en": "The only thing here that uses the network. It can take a "
              "while.",
    },
    "task.fetch.got": {
        "tr": "{width_m} x {height_m} m, engebe {relief_m} m, pürüzlülük "
              "{roughness_m} m",
        "en": "{width_m} x {height_m} m, relief {relief_m} m, roughness "
              "{roughness_m} m",
    },
    "task.deliver.table": {
        "tr": "Tablo çalışıyor.",
        "en": "Running the table.",
    },
    "task.deliver.budget": {
        "tr": "Hata parçalarına ayrılıyor. Yavaş olan kısım bu.",
        "en": "Taking the error apart. This is the slow part.",
    },
    "task.deliver.wrote": {"tr": "{path} yazıldı", "en": "Wrote {path}"},
}


def say(key: str, language: str | None = None, **fields) -> str:
    """One built sentence, in the language asked for.

    Raises rather than falling back to the other language: a missing
    sentence is a half-translated page, and a page half in English is
    something nobody notices until somebody else does.
    """
    try:
        both = CATALOGUE[key]
    except KeyError:
        raise KeyError(
            "nothing to say for {!r}. Add it to CATALOGUE in both "
            "languages.".format(key)
        ) from None
    return both[chosen(language)].format(**fields)
