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
