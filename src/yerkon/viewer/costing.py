"""The cost page's drawings: every row's bill, every part, every assumption.

Nothing here is typed. The rows' line items are priced from the same
inventory and the same served area the published run used, the parts
come from `bom.toml`, and the assumptions come from the settings file
in whichever language the page is drawn. A price that moves in one of
those files moves here without anybody editing a page (ADR-0079).
"""

from __future__ import annotations

import html
from typing import Optional

from yerkon.evidence import Provenance
from yerkon.numbers import decimal_comma

#: What the cost model calls each line, in the page's two languages.
LINES = {
    "anchor units": ("Yayın birimleri", "Broadcast units"),
    "structures and installation": ("Yapı ve montaj", "Structure and fitting"),
    "standalone power": ("Şebeke dışı besleme", "Standalone power"),
    "energy": ("Elektrik", "Electricity"),
    "connectivity": ("Veri hattı", "Data plans"),
    "structure rent": ("Kira", "Rent"),
    "replacement": ("Yenileme", "Replacement"),
    "maintenance": ("Bakım", "Maintenance"),
    "central operation": ("Merkezî işletme payı", "Share of central operation"),
    "per diem": ("Harcırah", "Per diem"),
}

#: What each structure is called, in the page's two languages.
STRUCTURES = {
    "lighting column": ("aydınlatma direği", "lighting column"),
    "lighting column at a signalised junction": (
        "ışıklı kavşakta aydınlatma direği",
        "lighting column at a signalised junction"),
    "tall mast": ("dikilen direk", "raised mast"),
    "distribution pole": ("elektrik dağıtım direği", "distribution pole"),
    "tunnel bracket": ("tünel askısı", "tunnel bracket"),
    "roadside sign": ("yol levhası", "roadside sign"),
    "sign gantry": ("levha portalı", "sign gantry"),
    "billboard": ("reklam panosu", "billboard"),
    "rooftop": ("çatı", "rooftop"),
}

#: The settings file's units, in the page's two languages.
UNITS = {
    "TL/year": ("TL/yıl", "TL/year"),
    "TL/visit": ("TL/ziyaret", "TL/visit"),
    "TL/day": ("TL/gün", "TL/day"),
    "sites/day": ("birim/gün", "sites/day"),
    "kWh/year": ("kWh/yıl", "kWh/year"),
    "visits/year": ("ziyaret/yıl", "visits/year"),
    "years": ("yıl", "years"),
    "anchors": ("birim", "units"),
    "people": ("kişi", "people"),
    "fraction": ("oran", "fraction"),
}

#: The rows, in table order, with what each is called.
ROWS = (
    ("urban", ("Şehir içi", "Urban")),
    ("rural", ("Kırsal", "Rural")),
    ("tunnel", ("Tünel", "Tunnel")),
)

#: Every figure a cost rests on, grouped, in the order a reader meets
#: them: who does the work and what a day of it costs, how many sites
#: that day covers, what fitting a unit costs, how high it stands, what
#: it draws, how often it is visited, what is rented, and how long it
#: lasts.
GROUPS = (
    (("Ekip ve ekip günü", "The crew and its day"), (
        ("operating.crew_day_tl", ("Bir ekip günü", "One crew day")),
        ("operating.crew_size", ("Bakım ekibi", "Maintenance crew")),
        ("mounting.rooftop.crew_day_tl",
         ("Çatıda bir ekip günü", "A crew day on roofs")),
    )),
    (("Ekibin bir günde uğradığı birim", "Sites a crew covers in a day"), (
        ("mounting.lighting_column.per_crew_day",
         ("Aydınlatma direği", "Lighting columns")),
        ("mounting.distribution_pole.per_crew_day",
         ("Kırsal dağıtım direği", "Rural distribution poles")),
        ("mounting.tunnel_bracket.per_crew_day", ("Tünel", "Tunnel")),
        ("mounting.rooftop.per_crew_day", ("Çatı", "Roofs")),
        ("mounting.tall_mast.per_crew_day", ("Dikilen direk", "Raised masts")),
    )),
    (("Montaj", "Fitting"), (
        ("mounting.lighting_column.site_cost_tl",
         ("Aydınlatma direğine montaj", "Fitting to a lighting column")),
        ("mounting.distribution_pole.site_cost_tl",
         ("Dağıtım direğine montaj", "Fitting to a distribution pole")),
        ("mounting.rooftop.site_cost_tl", ("Çatıya montaj", "Fitting to a roof")),
        ("mounting.tunnel_bracket.site_cost_tl",
         ("Tünel askısı", "Tunnel bracket")),
        ("mounting.tall_mast.site_cost_tl",
         ("Direk dikmek", "Raising a mast")),
    )),
    (("Birimin yüksekliği", "How high the unit stands"), (
        ("mounting.lighting_column.height_m",
         ("Aydınlatma direğinde", "On a lighting column")),
        ("mounting.distribution_pole.height_m",
         ("Dağıtım direğinde", "On a distribution pole")),
        ("mounting.rooftop.height_m", ("Çatıda", "On a roof")),
        ("mounting.tall_mast.height_m", ("Dikilen direkte", "On a raised mast")),
    )),
    (("Enerji", "Power"), (
        ("operating.anchor_kwh_per_year",
         ("Bir birimin yıllık tüketimi", "One unit's yearly consumption")),
        ("operating.electricity_tl_per_kwh",
         ("Elektrik birim fiyatı", "Electricity tariff")),
        ("operating.off_grid_supply_tl",
         ("Güneş paneli ve akü", "Solar panel and battery")),
    )),
    (("Bakım ve harcırah", "Maintenance and per diem"), (
        ("operating.maintenance_visits_per_year",
         ("Yıllık bakım ziyareti", "Maintenance visits a year")),
        ("operating.extra_off_grid_visits_per_year",
         ("Şebeke dışı ek ziyaret", "Extra off-grid visits")),
        ("operating.per_diem_tl",
         ("Harcırah, kişi başı gündelik", "Per diem, a person a day")),
        ("operating.per_diem_share",
         ("Günübirlik görevde gündeliğin payı", "Share of it on a day trip")),
        ("urban.crew_travels",
         ("Şehir içinde ekip görev yeri dışına çıkıyor mu",
          "Does the town crew leave its duty station")),
        ("rural.crew_travels",
         ("Kırsalda ekip görev yeri dışına çıkıyor mu",
          "Does the open-country crew leave its duty station")),
        ("tunnel.crew_travels",
         ("Tünelde ekip görev yeri dışına çıkıyor mu",
          "Does the tunnel crew leave its duty station")),
    )),
    (("Kira ve veri hattı", "Rent and data"), (
        ("mounting.distribution_pole.rent_tl_per_year",
         ("Dağıtım direği kirası, yıllık", "Distribution pole rent, a year")),
        ("mounting.rooftop.rent_tl_per_year",
         ("Çatı kirası, yıllık", "Roof rent, a year")),
        ("operating.connectivity_tl_per_year",
         ("Hücresel veri hattı, yıllık", "Cellular data line, a year")),
    )),
    (("Ömür ve merkezî sistem", "Service life and the central system"), (
        ("operating.service_life_years", ("Birimin ömrü", "A unit's service life")),
        ("operating.battery_life_years", ("Akünün ömrü", "The battery's life")),
        ("operating.central_operation_tl_per_anchor_year",
         ("Merkezî sistem, birim başına yıllık",
          "Central system, a unit a year")),
    )),
)

#: The same figures as one flat list, for whatever counts them.
ASSUMED = tuple(item for _, items in GROUPS for item in items)

#: How much weight each kind of figure carries, said plainly.
KINDS = {
    Provenance.DATASHEET: ("yayımlanmış fiyat", "published price"),
    Provenance.MEASUREMENT: ("ölçüm", "measurement"),
    Provenance.STANDARD: ("standart", "standard"),
    Provenance.DERIVED: ("hesaplanmış", "worked out"),
    Provenance.DESIGN: ("tasarım kararı", "design choice"),
    Provenance.ASSUMPTION: ("varsayım", "assumption"),
}


def _say(pair, language: str) -> str:
    return pair[1] if language == "en" else pair[0]


def _tl(value: float) -> str:
    return decimal_comma(value, 2) + " TL"


def costed(key: str, area_km2: float):
    """One row priced exactly as the published run priced it."""
    from yerkon.cost import price
    from yerkon.scenarios import CHOICES

    deployed = CHOICES[key]
    return deployed, price(deployed.inventory(area_km2))


def rows(published, language: str, table) -> str:
    """Each YERKON row's capital and running cost, line by line."""
    out = []
    for key, name in ROWS:
        if key not in published.keys:
            continue
        deployed, costing = costed(key, published.row(key).area_km2)
        corridor = deployed.serves_a_corridor
        per = costing.route_km if corridor else costing.service_area_km2
        unit = "/km" if corridor else "/km²"
        head = [
            _say(("Kalem", "Line"), language),
            _say(("Toplam", "Total"), language),
            _say(("{} başına", "Per {}"), language).format(unit.strip("/")),
        ]
        body = []
        for items, total, title in (
            (costing.capital, costing.capex_tl,
             ("Kurulum (CAPEX)", "Build (CAPEX)")),
            (costing.operating, costing.opex_tl_per_year,
             ("İşletme, yıllık (OPEX)", "Running, a year (OPEX)")),
        ):
            for item in items:
                body.append([
                    html.escape(_say(LINES.get(item.label, (item.label,) * 2),
                                     language)),
                    _tl(item.tl), _tl(item.tl / per),
                ])
            body.append([
                "<b>{}</b>".format(html.escape(_say(title, language))),
                "<b>{}</b>".format(_tl(total)),
                "<b>{}</b>".format(_tl(total / per)),
            ])
        counted = {}
        for anchor in deployed.scenario.deployment.anchors:
            counted[anchor.mounting.kind] = counted.get(anchor.mounting.kind, 0) + 1
        what = ", ".join(
            "{} {}".format(n, _say(STRUCTURES.get(kind, (kind, kind)), language))
            for kind, n in counted.items())
        out.append("<h3>{}</h3><p>{}</p><div class=\"scroll\" tabindex=\"0\">{}</div>".format(
            html.escape(_say(name, language)),
            html.escape(_say((
                "{} birim ({}), {} {} üzerinde.",
                "{} units ({}), over {} {}.",
            ), language).format(
                len(deployed.scenario.deployment.anchors), what,
                decimal_comma(per, 2), "km" if corridor else "km²")),
            table([head] + body, numeric_from=1),
        ))
    return "".join(out)


#: Products the model keeps but no row of the table uses: the plain
#: module without the FHSS and LBT certificate stays so a simulator run can
#: choose it, and is left off the price tables (ADR-0094).
UNSHOWN = {"sx1280-anchor"}


def summary(language: str, table) -> str:
    """Each product at one, a hundred and a thousand."""
    from yerkon.bom import read

    bill = read()
    head = [_say(pair, language) for pair in (
        ("Ürün", "Product"), ("1 adet", "One"),
        ("100 adette", "At a hundred"), ("1000 adette", "At a thousand"),
    )]
    body = [
        [html.escape(board.name(language)), _tl(board.one_tl),
         _tl(board.hundred_tl), "<b>{}</b>".format(_tl(board.thousand_tl))]
        for board in bill.boards.values() if board.key not in UNSHOWN
    ]
    return '<div class="scroll" tabindex="0">{}</div>'.format(
        table([head] + body, numeric_from=1))


def parts(language: str, table) -> str:
    """Every part of every product, with who sells it and for how much
    at one, a hundred and a thousand boards."""
    from yerkon.bom import read

    bill = read()
    out = []
    for board in bill.boards.values():
        if board.key in UNSHOWN:
            continue
        head = [_say(pair, language) for pair in (
            ("Parça", "Part"), ("Görevi", "What it does"),
            ("Satıcı", "Seller"), ("1 adet", "One"),
            ("100 adette", "At a hundred"), ("1000 adette", "At a thousand"),
        )]
        body = []
        for part, count in board.lines:
            name = part.name if count == 1 else "{} x {}".format(count, part.name)
            role = part.role(language)
            if part.note and language != "en":
                role = "{} ({})".format(role, part.note)
            body.append([
                html.escape(name), html.escape(role),
                '<a href="{}">{}</a>'.format(
                    html.escape(part.url, quote=True), html.escape(part.seller)),
            ] + [
                "{} USD".format(decimal_comma(count * part.at(count * tier), 2))
                for tier in (1, 100, 1000)
            ])
        body.append([
            "<b>{}</b>".format(html.escape(_say(("Toplam", "Total"), language))),
            "", "",
            "<b>{}</b>".format(_tl(board.one_tl)),
            "<b>{}</b>".format(_tl(board.hundred_tl)),
            "<b>{}</b>".format(_tl(board.thousand_tl)),
        ])
        out.append(_folded(
            board.name(language),
            '<div class="scroll" tabindex="0">{}</div>'.format(
                table([head] + body, numeric_from=3))))
    return "".join(out)


def _folded(title: str, inside: str) -> str:
    """A sub-heading that opens to what is under it, so a long list reads
    as its topics first."""
    return ('<details class="fold sub"><summary><h3>{}</h3></summary>{}'
            "</details>".format(html.escape(title), inside))


#: The bibliography entries behind each figure on the list, so a source
#: named in words is also a link a reader can open. A figure resting on
#: this project's own choice has none.
LINKS = {
    "operating.crew_day_tl": ("sepetli-ankara", "yevmiye-2026"),
    "operating.crew_size": ("yevmiye-2026",),
    "mounting.rooftop.crew_day_tl": ("yevmiye-2026",),
    "mounting.lighting_column.per_crew_day": ("dicle-surici",),
    "mounting.distribution_pole.per_crew_day": ("dicle-surici",),
    "mounting.tunnel_bracket.per_crew_day": ("dicle-surici",),
    "mounting.rooftop.per_crew_day": ("dicle-surici",),
    "mounting.tall_mast.per_crew_day": ("dicle-surici",),
    "mounting.lighting_column.site_cost_tl": ("sepetli-ankara", "yevmiye-2026"),
    "mounting.distribution_pole.site_cost_tl": ("sepetli-ankara", "yevmiye-2026"),
    "mounting.rooftop.site_cost_tl": ("yevmiye-2026",),
    "mounting.tunnel_bracket.site_cost_tl": ("sepetli-ankara", "yevmiye-2026"),
    "mounting.tall_mast.site_cost_tl": ("pana-direk",),
    "mounting.lighting_column.height_m": ("tedas-led-yol",),
    "mounting.distribution_pole.height_m": ("tedas-beton-direk", "ekaty"),
    "operating.anchor_kwh_per_year": ("semtech-sx1280-datasheet",),
    "operating.electricity_tl_per_kwh": ("genel-aydinlatma", "forelektrik-2026",
                                         "zam-nisan-2026"),
    "operating.off_grid_supply_tl": ("akakce-panel", "akakce-battery",
                                     "akakce-controller", "akakce-bracket",
                                     "akakce-box", "solar-kablo-2026"),
    "operating.extra_off_grid_visits_per_year": ("gib-amortisman",),
    "operating.per_diem_tl": ("harcirah-kanunu", "gvk-24",
                              "sbb-h-cetveli-2026"),
    "operating.per_diem_share": ("harcirah-kanunu",),
    "urban.crew_travels": ("harcirah-kanunu",),
    "mounting.distribution_pole.rent_tl_per_year": (
        "uab-gecis-hakki", "genel-aydinlatma", "direk-reklam",
        "ibb-tariff-2025"),
    "mounting.rooftop.rent_tl_per_year": ("ibb-tariff-2025", "tarim-orman-2025"),
    "operating.service_life_years": ("gib-amortisman",),
    "operating.battery_life_years": ("gib-amortisman",),
    "operating.central_operation_tl_per_anchor_year": (
        "yazilimci-maaslari-2026", "vds-2026"),
}


def _links(key: str, language: str) -> str:
    from yerkon.sources import read

    known = read().by_key
    return " · ".join(
        '<a href="{}">{}</a>'.format(html.escape(known[cited].url, quote=True),
                                     html.escape(known[cited].said(language)))
        for cited in LINKS.get(key, ()))


def assumptions(language: str, table) -> str:
    """Every figure a cost rests on, grouped and numbered, one by one:
    what it is, its value, what kind of figure it is, how it was worked
    out and where it came from."""
    from yerkon.settings import defaults_in

    settings = defaults_in(language)
    out = []
    number = 0
    for title, items in GROUPS:
        entries = []
        start = number + 1
        for key, name in items:
            number += 1
            sourced = settings.sourced(key)
            value = float(sourced.value)
            shown = decimal_comma(value, 2 if value != int(value) else 0)
            unit = _say(UNITS.get(sourced.unit, (sourced.unit, sourced.unit)),
                        language)
            if sourced.unit == "yes/no":
                shown = _say(("evet", "yes") if value else ("hayır", "no"),
                             language)
                unit = ""
            entries.append(
                "<li><p><b>{name}: {value}</b> <span class=\"kind\">"
                "({kind})</span></p><p>{note}</p><p class=\"source\">{said}: "
                "{source}</p>{links}</li>".format(
                    links=('<p class="source">{}</p>'.format(_links(key, language))
                           if key in LINKS else ""),
                    name=html.escape(_say(name, language)),
                    value=html.escape((shown + " " + unit).strip()),
                    kind=html.escape(_say(KINDS[sourced.provenance], language)),
                    note=html.escape(sourced.note),
                    said=html.escape(_say(("Kaynak", "Source"), language)),
                    source=html.escape(sourced.source)))
        out.append(_folded(
            _say(title, language),
            '<ol class="basis" start="{}">{}</ol>'.format(
                start, "".join(entries))))
    return "".join(out)


def structures(language: str, table) -> str:
    """The town's units on the structures it has, and on masts raised for them."""
    from yerkon.cost import AMPLIFIED_ANCHOR, DEFAULT_RATES
    from yerkon.world import LIGHTING_COLUMN, TALL_MAST

    unit = float(AMPLIFIED_ANCHOR.unit_price_tl.value)
    fitting = float(LIGHTING_COLUMN.site_cost_tl.value)
    mast = float(TALL_MAST.site_cost_tl.value)
    supply = float(DEFAULT_RATES.off_grid_supply_tl.value)
    on_column = unit + fitting
    on_mast = unit + mast + supply
    head = [_say(pair, language) for pair in (
        ("Bir birimin bedeli", "What one unit costs"),
        ("Mevcut yapıya", "On a structure that stands"),
        ("Dikilen direğe", "On a mast raised for it"),
    )]
    body = [
        [_say(("Yayın birimi", "The broadcast unit"), language),
         _tl(unit), _tl(unit)],
        [_say(("Yapı ve montaj", "Structure and fitting"), language),
         _tl(fitting), _tl(mast)],
        [_say(("Şebeke dışı besleme", "Standalone power"), language),
         _say(("yok", "none"), language), _tl(supply)],
        ["<b>{}</b>".format(_say(("Toplam", "Total"), language)),
         "<b>{}</b>".format(_tl(on_column)), "<b>{}</b>".format(_tl(on_mast))],
    ]
    times = round(on_mast / on_column)
    said = _say((
        "<p><b>Sermayede {} kat.</b> Aynı birim, aynı zemin; tek fark neye "
        "takıldığı.</p>",
        "<p><b>{} times, on capital.</b> The same unit on the same ground; "
        "the only difference is what it is fitted to.</p>",
    ), language).format(times)
    return '<div class="scroll" tabindex="0">{}</div>{}'.format(
        table([head] + body, numeric_from=1), said)


#: The structures a broadcast unit is shown on, in the order a reader
#: meets them: town, open country, roof, tunnel, a mast raised for it.
SHOWN_ON = ("lighting_column", "distribution_pole", "rooftop",
            "tunnel_bracket", "tall_mast")


def units(published, language: str, table) -> str:
    """One broadcast unit on each structure, and why a row's km² differs.

    Priced through `cost.price` one unit at a time, so every figure here
    is the one the rows are built from.
    """
    from yerkon.cost import (AMPLIFIED_ANCHOR, TUNNEL_ANCHOR, AnchorSite,
                             Inventory, price)
    from yerkon.world import MOUNTINGS

    columns = []
    for key in SHOWN_ON:
        mounting = MOUNTINGS[key]
        product = TUNNEL_ANCHOR if key == "tunnel_bracket" else AMPLIFIED_ANCHOR
        site = AnchorSite(
            product=product, structure=mounting.kind,
            site_cost_tl=mounting.site_cost_tl,
            per_crew_day=float(mounting.per_crew_day.value),
            crew_day_tl=mounting.crew_day_value,
            has_power=mounting.has_power, has_backhaul=mounting.has_backhaul,
            rent_tl_per_year=(float(mounting.rent_tl_per_year.value)
                              if mounting.rent_tl_per_year is not None
                              else 0.0))
        costing = price(Inventory(anchors=(site,)))
        lines = {i.label: i.tl for i in costing.capital + costing.operating}
        columns.append((mounting, lines, costing))

    head = [_say(("Bir birim", "One unit"), language)] + [
        html.escape(_say(STRUCTURES[m.kind], language)).capitalize()
        for m, _, _ in columns]
    shown = (
        ("anchor units", ("Yayın birimi (1000 adette)",
                          "Broadcast unit (at a thousand)")),
        ("structures and installation", ("Montaj", "Fitting")),
        ("standalone power", ("Güneş paneli ve akü", "Solar panel and battery")),
    )
    body = []
    for label, name in shown:
        body.append([html.escape(_say(name, language))]
                    + [_tl(lines[label]) for _, lines, _ in columns])
    body.append(["<b>{}</b>".format(_say(("Kurulum", "To build"), language))]
                + ["<b>{}</b>".format(_tl(c.capex_tl)) for _, _, c in columns])
    for label in ("energy", "structure rent", "maintenance", "replacement",
                  "central operation"):
        body.append([html.escape(_say(LINES[label], language))]
                    + [_tl(lines[label]) for _, lines, _ in columns])
    body.append(["<b>{}</b>".format(_say(("Yıllık işletme", "To run, a year"),
                                         language))]
                + ["<b>{}</b>".format(_tl(c.opex_tl_per_year))
                   for _, _, c in columns])

    said = [_say((
        "<p>Şehir içi ve kırsal satırlar aynı yayın birimini kullanıyor: yükselteçli "
        "SX1280 modülü E28-2G4M20S, dış ortam tipi 5 dBi çubuk anten, aynı "
        "mikrodenetleyici ve güvenlik yongası. Tünelde yayın birimi DWM3000 "
        "UWB modülünü taşıyor. Farkı birim değil, birimin takıldığı yapı "
        "yaratıyor: şehirde elektriği olan aydınlatma direği, kırsalda "
        "elektriği olmayan dağıtım direği ve güneş paneli, tünelde şerit "
        "kapatmaya bağlı bir askı.</p>",
        "<p>The town and open country rows use the same broadcast unit: the "
        "amplified SX1280 module E28-2G4M20S, an outdoor 5 dBi whip, the "
        "same microcontroller and secure element. In the tunnel the unit "
        "carries the DWM3000 UWB module. What differs is not the unit but "
        "the structure it goes on: a lighting column with mains in town, a "
        "distribution pole with no mains and a solar panel in open "
        "country, a bracket that waits on a lane closure in the tunnel.</p>",
    ), language)]
    column = dict((m.kind, c) for m, _, c in columns)
    said.append(_say((
        "<p><b>Dikilen direkte kurulum, aydınlatma direğindekinin {} katı.</b> "
        "Aynı birim, aynı zemin; tek fark neye takıldığı.</p>",
        "<p><b>On a raised mast the build costs {} times what it does on a "
        "lighting column.</b> The same unit on the same ground; the only "
        "difference is what it is fitted to.</p>",
    ), language).format(ratio_on_masts()))
    dense = []
    for key, name in ROWS:
        if published is None or key not in published.keys:
            continue
        deployed = __import__("yerkon.scenarios", fromlist=["CHOICES"]).CHOICES[key]
        if deployed.serves_a_corridor:
            continue
        count = len(deployed.scenario.deployment.anchors)
        area = published.row(key).area_km2
        dense.append((name, count, area))
    if len(dense) == 2:
        (n1, c1, a1), (n2, c2, a2) = dense
        said.append(_say((
            "<p>Tablonun kullandığı yapılar içinde bir birim şehirdeki "
            "aydınlatma direğinde en ucuza kuruluyor ve işletiliyor, ama "
            "şehir içi satır kilometrekare başına en pahalısı. Sebep "
            "yoğunluk: binalar sinyali kestiği için şehirde bir birim "
            "{a1} km²'ye, kırsalda {a2} km²'ye hizmet ediyor. {c1} birim "
            "{A1} km²'de kilometrekareye {d1} birim, {c2} birim {A2} km²'de "
            "{d2} birim ediyor. Kilometrekare başına maliyet, birim başına "
            "maliyetin bu yoğunlukla çarpımı.</p>",
            "<p>Of the structures the table uses, a unit is cheapest to "
            "build and run on a town lighting column, yet the town "
            "row is the dearest per square kilometre. The reason is "
            "density: buildings cut the signal, so a unit serves {a1} km² "
            "in town and {a2} km² in open country. {c1} units over {A1} km² "
            "are {d1} units a km²; {c2} units over {A2} km² are {d2}. The "
            "cost per square kilometre is the cost per unit times that "
            "density.</p>",
        ), language).format(
            a1=decimal_comma(a1 / c1, 2), a2=decimal_comma(a2 / c2, 2),
            c1=c1, A1=decimal_comma(a1, 2), d1=decimal_comma(c1 / a1, 2),
            c2=c2, A2=decimal_comma(a2, 2), d2=decimal_comma(c2 / a2, 2)))
    return '<div class="scroll" tabindex="0">{}</div>{}'.format(
        table([head] + body, numeric_from=1), "".join(said))


def ratio_on_masts() -> int:
    """How many times the mast costs the column, rounded as the page says."""
    from yerkon.cost import AMPLIFIED_ANCHOR, DEFAULT_RATES
    from yerkon.world import LIGHTING_COLUMN, TALL_MAST

    unit = float(AMPLIFIED_ANCHOR.unit_price_tl.value)
    return round(
        (unit + float(TALL_MAST.site_cost_tl.value)
         + float(DEFAULT_RATES.off_grid_supply_tl.value))
        / (unit + float(LIGHTING_COLUMN.site_cost_tl.value))
    )
