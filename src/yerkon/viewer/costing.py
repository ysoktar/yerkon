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
    "structure rent": ("Direk kirası", "Pole rent"),
    "replacement": ("Yenileme", "Replacement"),
    "maintenance": ("Bakım", "Maintenance"),
    "central operation": ("Merkezî işletme payı", "Share of central operation"),
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
}

#: The rows, in table order, with what each is called.
ROWS = (
    ("urban", ("Şehir içi", "Urban")),
    ("rural", ("Kırsal", "Rural")),
    ("tunnel", ("Tünel", "Tunnel")),
)

#: Every figure a cost rests on, in the order a reader meets them.
ASSUMED = (
    ("mounting.lighting_column.site_cost_tl",
     ("Aydınlatma direğine montaj", "Fitting to a lighting column")),
    ("mounting.tall_mast.site_cost_tl",
     ("25 m direk dikmek", "Raising a 25 m mast")),
    ("mounting.distribution_pole.height_m",
     ("Dağıtım direğinde yükseklik", "Height on a distribution pole")),
    ("mounting.distribution_pole.site_cost_tl",
     ("Dağıtım direğine montaj", "Fitting to a distribution pole")),
    ("mounting.distribution_pole.rent_tl_per_year",
     ("Dağıtım direği kirası, yıllık", "Distribution pole rent, a year")),
    ("mounting.tunnel_bracket.site_cost_tl",
     ("Tünel askısı", "Tunnel bracket")),
    ("operating.off_grid_supply_tl",
     ("Güneş paneli ve akü", "Solar panel and battery")),
    ("operating.electricity_tl_per_kwh",
     ("Elektrik birim fiyatı", "Electricity tariff")),
    ("operating.anchor_kwh_per_year",
     ("Bir birimin yıllık tüketimi", "One unit's yearly consumption")),
    ("operating.connectivity_tl_per_year",
     ("Bir veri paketi, yıllık", "One data plan, a year")),
    ("operating.anchors_per_data_plan",
     ("Bir paketi paylaşan birim", "Units sharing a plan")),
    ("urban.junction_every",
     ("Işıklı kavşak aralığı", "Signalised junction spacing")),
    ("operating.service_life_years",
     ("Birimin ömrü", "A unit's service life")),
    ("operating.maintenance_visits_per_year",
     ("Yıllık bakım ziyareti", "Maintenance visits a year")),
    ("operating.extra_off_grid_visits_per_year",
     ("Şebeke dışı ek ziyaret", "Extra off-grid visits")),
    ("operating.maintenance_tl_per_visit",
     ("Bir bakım ziyareti", "One maintenance visit")),
    ("operating.central_operation_tl_per_year",
     ("Merkezî sistem, yıllık", "Central system, a year")),
    ("operating.anchors_sharing_central_operation",
     ("Merkezî sistemi paylaşan birim", "Units sharing the centre")),
)

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
        out.append("<h3>{}</h3><p>{}</p><div class=\"scroll\">{}</div>".format(
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


def summary(language: str, table) -> str:
    """Each product at one, a hundred and a thousand, beside the report."""
    from yerkon.bom import read

    bill = read()
    head = [_say(pair, language) for pair in (
        ("Ürün", "Product"), ("Raporda 1", "Report, 1"),
        ("Raporda 100", "Report, 100"), ("Şimdi 1", "Now, 1"),
        ("Şimdi 100", "Now, 100"), ("Şimdi 1000", "Now, 1000"),
    )]
    body = [
        [html.escape(board.name(language)), _tl(board.report_one_tl),
         _tl(board.report_hundred_tl), _tl(board.one_tl),
         _tl(board.hundred_tl), "<b>{}</b>".format(_tl(board.thousand_tl))]
        for board in bill.boards.values()
    ]
    return '<div class="scroll">{}</div>'.format(
        table([head] + body, numeric_from=1))


def parts(language: str, table) -> str:
    """Every part of every product, with who sells it and for how much."""
    from yerkon.bom import read

    bill = read()
    out = []
    for board in bill.boards.values():
        replaced = {came.key: gone for gone, came in board.swapped}
        head = [_say(pair, language) for pair in (
            ("Parça", "Part"), ("Görevi", "What it does"),
            ("Satıcı", "Seller"), ("Yerine geçtiği", "Replaces"),
            ("1 adet", "One"),
        )]
        body = []
        for part in board.parts:
            gone = replaced.get(part.key)
            body.append([
                html.escape(part.name), html.escape(part.role(language)),
                '<a href="{}">{}</a>'.format(
                    html.escape(part.url, quote=True), html.escape(part.seller)),
                html.escape("{}, {}, {} USD".format(
                    gone.name, gone.seller, decimal_comma(gone.usd, 2)))
                if gone else "",
                "{} USD".format(decimal_comma(part.usd, 2)),
            ])
        body.append([
            html.escape(_say(("Diğer", "Other"), language)),
            html.escape(_say((
                "güç dönüşümü, koruma, bağlantı, kutu",
                "power conversion, protection, connectors, enclosure",
            ), language)),
            html.escape(_say(("raporun toplamından", "from the report's total"),
                             language)),
            "",
            "{} USD".format(decimal_comma(board.other_usd, 2)),
        ])
        out.append("<h3>{}</h3>{}".format(
            html.escape(board.name(language)),
            '<div class="scroll">{}</div>'.format(
                table([head] + body, numeric_from=4))))
    return "".join(out)


def assumptions(language: str, table) -> str:
    """Every figure a cost rests on, what it is and where it came from."""
    from yerkon.settings import defaults_in

    settings = defaults_in(language)
    head = [_say(pair, language) for pair in (
        ("Varsayım", "Figure"), ("Değer", "Value"),
        ("Dayanağı", "What it rests on"), ("Ne demek", "What it means"),
    )]
    body = []
    for key, name in ASSUMED:
        sourced = settings.sourced(key)
        value = float(sourced.value)
        shown = decimal_comma(value, 2 if value != int(value) else 0)
        body.append([
            html.escape(_say(name, language)),
            html.escape("{} {}".format(shown, sourced.unit)),
            html.escape("{}: {}".format(
                _say(KINDS[sourced.provenance], language), sourced.source)),
            html.escape(sourced.note),
        ])
    return '<div class="scroll">{}</div>'.format(
        table([head] + body, numeric_from=1))


def structures(language: str, table) -> str:
    """The town's units on the structures it has, and on masts raised for them."""
    from yerkon.cost import SX1280_ANCHOR, DEFAULT_RATES
    from yerkon.world import LIGHTING_COLUMN, TALL_MAST

    unit = float(SX1280_ANCHOR.unit_price_tl.value)
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
    return '<div class="scroll">{}</div>{}'.format(
        table([head] + body, numeric_from=1), said)


def ratio_on_masts() -> int:
    """How many times the mast costs the column, rounded as the page says."""
    from yerkon.cost import SX1280_ANCHOR, DEFAULT_RATES
    from yerkon.world import LIGHTING_COLUMN, TALL_MAST

    unit = float(SX1280_ANCHOR.unit_price_tl.value)
    return round(
        (unit + float(TALL_MAST.site_cost_tl.value)
         + float(DEFAULT_RATES.off_grid_supply_tl.value))
        / (unit + float(LIGHTING_COLUMN.site_cost_tl.value))
    )
