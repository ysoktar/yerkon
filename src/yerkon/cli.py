"""Command line entry points.

``fetch`` is the only thing that touches the network; it writes a cache,
and everything else reads that cache and runs offline. ADR-0008 is why
they are separate.

``table`` runs the three scenarios and prints the four rows of the
report's comparison table.

``view`` starts a local web app: the same engine, drawn in three
dimensions, with every setting live.

``defaults`` lists every figure the model needs that nobody supplied,
what it affects, and what replacing it would move.

``budget`` takes each scenario's error apart, one source at a time, and
says which one is worth spending money on.

``calibrate`` reads what a MATLAB run measured and says what to put in
the defaults file.

``site`` searches for the cheapest deployment that meets a target.

``design`` shows what a set of settings implies, and asks once before
changing them. The panel it prints is built in ``proposal`` and rendered
unchanged by the application too, so both front ends ask the same
question in the same words. See ADR-0001 and ADR-0009.
"""

from __future__ import annotations

import argparse
import sys

from yerkon.site.cache import SiteCache
from yerkon.site.fetch import (
    CopernicusElevation,
    GeoTiffElevation,
    OpenStreetMapBuildings,
    ServiceElevation,
    Unreachable,
    build_site,
)
from yerkon.design import (
    ANTENNA_CHOICES,
    Design,
    MOUNTING_CHOICES,
    RADIO_CHOICES,
    REGION_CHOICES,
    chosen,
    derive,
)
from yerkon.numbers import decimal_comma, readable
from yerkon.report import as_breakdown, as_markdown, as_text, build, footnotes
from yerkon.scenarios import ALL as ALL_SCENARIOS, CHOICES as SCENARIO_CHOICES
from yerkon.proposal import OUTCOME_LABELS, confirm, show_outcome
from yerkon.terms import NAMES as SOURCE_NAMES
from yerkon.site.model import BoundingBox


def fetch(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="yerkon fetch",
        description=(
            "Download ground and buildings for an area into a cache. This is "
            "the only command that uses the network; runs read the cache."
        ),
    )
    parser.add_argument("--south", type=float, required=True)
    parser.add_argument("--west", type=float, required=True)
    parser.add_argument("--north", type=float, required=True)
    parser.add_argument("--east", type=float, required=True)
    parser.add_argument(
        "--into", required=True,
        help="cache directory to write, for example sites/ankara-o20",
    )
    parser.add_argument(
        "--spacing", type=float, default=30.0,
        help="grid spacing in metres (default: %(default)s)",
    )
    parser.add_argument(
        "--geotiff",
        help=(
            "a downloaded elevation raster to prefer over the online "
            "service. Faster, higher resolution, and it needs no network."
        ),
    )
    parser.add_argument(
        "--no-buildings", action="store_true",
        help="skip OpenStreetMap; the site records that nobody looked",
    )
    parser.add_argument(
        "--no-copernicus", action="store_true",
        help="skip the Copernicus tiles, leaving only the query service",
    )
    parser.add_argument(
        "--tile-cache", default="sites/_tiles",
        help="where Copernicus tiles are kept (default: %(default)s)",
    )
    args = parser.parse_args(argv)

    bounds = BoundingBox(
        south=args.south, west=args.west, north=args.north, east=args.east
    )

    sources = []
    if args.geotiff:
        sources.append(GeoTiffElevation(args.geotiff))
    if not args.no_copernicus:
        sources.append(CopernicusElevation(cache_directory=args.tile_cache))
    sources.append(ServiceElevation())

    print("Fetching {:.4f},{:.4f} to {:.4f},{:.4f} at {:.0f} m".format(
        bounds.south, bounds.west, bounds.north, bounds.east, args.spacing
    ))
    print("  ground: {} (each tried in turn until one answers)".format(
        ", then ".join(source.name for source in sources)
    ))
    if not args.no_buildings:
        print("  features: OpenStreetMap")

    # What the query service would cost, and only when it is the source
    # that will actually be asked. A GeoTIFF or a Copernicus tile answers
    # first and makes no calls at all, so quoting a rate limit ahead of
    # them describes a fetch that is not going to happen.
    if isinstance(sources[0], ServiceElevation):
        service = sources[0]
        points = service.points_required(bounds, args.spacing)
        calls = (points + service.batch - 1) // service.batch
        minutes = calls * service.seconds_between_requests / 60.0
        print("  {:,} points, {:,} calls, about {:.0f} minutes at the "
              "service's rate limit".format(points, calls, minutes))

    try:
        site = build_site(
            bounds,
            spacing_m=args.spacing,
            elevation_sources=tuple(sources),
            buildings_source=None if args.no_buildings else OpenStreetMapBuildings(),
        )
    except Unreachable as error:
        print("\nNothing answered.\n  {}".format(error), file=sys.stderr)
        print(
            "\nEither pass --geotiff with a downloaded raster, or run this "
            "from a machine that can reach the elevation service.",
            file=sys.stderr,
        )
        return 1

    SiteCache(args.into).save(site)

    print("\nWrote {}".format(args.into))
    print("  {}".format(site.manifest.describe()))
    print("  {:.0f} x {:.0f} m, relief {:.0f} m, roughness {:.2f} m".format(
        site.width_m, site.height_m, site.relief_m, site.roughness_m()
    ))
    for note in site.manifest.notes:
        print("  note: {}".format(note))
    return 0


EDITS = {
    "region": (REGION_CHOICES, "region"),
    "radio": (RADIO_CHOICES, "radio"),
    "mounting": (MOUNTING_CHOICES, "mounting"),
    "antenna": (ANTENNA_CHOICES, "antenna"),
}

#: Which Design field each command line option sets.
EDIT_FIELDS = {
    "region": "region",
    "radio": "anchor_radio",
    "mounting": "mounting",
    "antenna": "antenna",
    "receiver_height": "receiver_height_m",
    "roughness": "surface_roughness_m",
    "tolerance": "target_ranging_sigma_m",
}


def design(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="yerkon design",
        description=(
            "Show what a set of settings implies. Given an edit, show "
            "everything it would change and ask once before applying it."
        ),
    )
    for option, (catalogue, what) in EDITS.items():
        parser.add_argument(
            "--{}".format(option),
            help="{}: {}".format(what, ", ".join(sorted(catalogue))),
        )
    parser.add_argument("--receiver-height", type=float, help="metres above ground")
    parser.add_argument(
        "--roughness", type=float,
        help="root-mean-square height of the reflecting ground, in metres",
    )
    parser.add_argument(
        "--tolerance", type=float,
        help="ranging error a link may have and still count as usable, in metres",
    )
    parser.add_argument(
        "--yes", action="store_true",
        help="answer the confirmation yes without asking",
    )
    args = parser.parse_args(argv)

    current = Design()
    edits = {}
    for option, field in EDIT_FIELDS.items():
        value = getattr(args, option.replace("-", "_"))
        if value is None:
            continue
        if option in EDITS:
            catalogue, what = EDITS[option]
            try:
                value = chosen(catalogue, value, what)
            except ValueError as error:
                print(error, file=sys.stderr)
                return 2
        edits[field] = value

    if not edits:
        print(describe_outcome(current))
        return 0

    def ask(panel: str) -> bool:
        print(panel)
        if args.yes:
            print("\nApplying (--yes).")
            return True
        answer = input("\nApply all of that? [y/N] ").strip().lower()
        return answer in {"y", "yes"}

    try:
        updated, applied = confirm(current, ask, **edits)
    except ValueError as error:
        print(error, file=sys.stderr)
        return 2

    if not applied:
        print("\nNothing changed.")
        return 0

    print()
    print(describe_outcome(updated))
    return 0


def describe_outcome(design_: Design) -> str:
    """The settings and what they imply, in the panel's own words."""
    outcome = derive(design_)
    lines = ["Settings:"]
    lines.append("  region             {}".format(design_.region.region))
    lines.append("  anchor radio       {}".format(design_.anchor_radio.part))
    lines.append("  antenna            {}".format(design_.antenna.part))
    lines.append("  mounting           {}".format(design_.mounting.kind))
    lines.append("  receiver height    {} m".format(
        decimal_comma(design_.receiver_height_m, 2)))
    lines.append("  ground roughness   {} m".format(
        decimal_comma(design_.surface_roughness_m, 2)))
    lines.append("  ranging tolerance  {} m".format(
        decimal_comma(design_.target_ranging_sigma_m, 2)))
    lines.append("")
    lines.append("Which gives:")
    width = max(len(label) for label in OUTCOME_LABELS.values())
    for field, label in OUTCOME_LABELS.items():
        lines.append("  {:<{width}}  {}".format(
            label, show_outcome(field, getattr(outcome, field)), width=width
        ))
    return "\n".join(lines)


def _add_defaults_flag(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--defaults", metavar="FILE",
        help=(
            "a settings file of the figures nobody supplied. Everything "
            "is rebuilt from it: mounting costs and heights, the "
            "unpublished radio figures, the clocks, and the operating "
            "rates. See `yerkon defaults`."
        ),
    )


def _settings_from(args):
    from yerkon.settings import load

    return load(args.defaults) if args.defaults else None


def table(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="yerkon table",
        description=(
            "Run the three scenarios and print the four YERKON rows of the "
            "comparison table, with what they rest on."
        ),
    )
    parser.add_argument(
        "--markdown", action="store_true",
        help="print the table as markdown rather than aligned text",
    )
    parser.add_argument(
        "--only", action="append", choices=sorted(SCENARIO_CHOICES),
        help="run only these scenarios; repeat the flag for several",
    )
    parser.add_argument(
        "--no-notes", action="store_true",
        help="print the table alone, without what it rests on",
    )
    _add_defaults_flag(parser)
    parser.add_argument(
        "--weight", action="append", metavar="NAME=SHARE",
        help=(
            "journey mix for the weighted row, for example --weight "
            "urban=0.6 --weight rural=0.3 --weight tunnel=0.1. Nobody "
            "supplied one, so the default is a starting point rather "
            "than a finding."
        ),
    )
    args = parser.parse_args(argv)

    try:
        settings = _settings_from(args)
    except (FileNotFoundError, ValueError) as error:
        print(error, file=sys.stderr)
        return 2

    from yerkon.scenarios import catalogue

    available = catalogue(settings) if settings else SCENARIO_CHOICES
    chosen = (
        tuple(available[name] for name in args.only)
        if args.only else tuple(available.values())
    )

    print("Running {} scenario{}{}. This takes a minute.".format(
        len(chosen), "" if len(chosen) == 1 else "s",
        " against {}".format(settings.path) if settings else "",
    ), file=sys.stderr)

    try:
        weights = _weights(args.weight)
        results, rows = build(chosen, weights=weights, settings=settings)
    except ValueError as error:
        print(error, file=sys.stderr)
        return 2
    print(as_markdown(rows) if args.markdown else as_text(rows))
    if not args.no_notes:
        print()
        print(footnotes(results, rows))
    return 0


def _weights(pairs: list[str] | None) -> dict[str, float] | None:
    """Parse --weight NAME=SHARE, saying what went wrong rather than raising."""
    if not pairs:
        return None
    weights = {}
    for pair in pairs:
        name, _, share = pair.partition("=")
        if not share:
            raise ValueError(
                "--weight wants NAME=SHARE, for example urban=0.5; got {!r}".format(
                    pair
                )
            )
        try:
            weights[name.strip().lower()] = float(share)
        except ValueError:
            raise ValueError("{!r} is not a share".format(share)) from None
    return weights


def view(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="yerkon view",
        description=(
            "Open the live 3D viewer in a browser. Everything is "
            "configurable and every number comes from the same engine "
            "that builds the table."
        ),
    )
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument(
        "--no-browser", action="store_true",
        help="print the address instead of opening it",
    )
    _add_defaults_flag(parser)
    args = parser.parse_args(argv)

    try:
        settings = _settings_from(args)
    except (FileNotFoundError, ValueError) as error:
        print(error, file=sys.stderr)
        return 2
    if settings is not None:
        print("Reading figures from {}.".format(settings.path))

    from yerkon.viewer import serve

    try:
        serve(host=args.host, port=args.port, open_browser=not args.no_browser)
    except OSError as error:
        print(
            "Could not listen on {}:{} ({}). Another viewer may already be "
            "running; try --port 8766.".format(args.host, args.port, error),
            file=sys.stderr,
        )
        return 1
    return 0


def site(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="yerkon site",
        description=(
            "Find the least expensive way to meet an accuracy target over "
            "a corridor, using the structures that already stand beside it "
            "and building only where none does."
        ),
    )
    parser.add_argument("--corridor", type=float, default=12_000.0,
                        help="length in metres (default: %(default)s)")
    parser.add_argument("--tolerance", type=float, default=5.0,
                        help="ranging error a link may have, in metres")
    parser.add_argument("--covered", type=float, default=0.95,
                        help="share of the corridor that must have a position")
    parser.add_argument("--relief", type=float, default=40.0,
                        help="height of the rolling ground, in metres")
    parser.add_argument("--radio", default="e28",
                        help="anchor module: {}".format(
                            ", ".join(sorted(RADIO_CHOICES))))
    parser.add_argument("--region", default="TR")
    parser.add_argument("--all", action="store_true",
                        help="list every candidate, not only those that meet")
    _add_defaults_flag(parser)
    args = parser.parse_args(argv)

    from yerkon.evaluate import Journey, Receiver
    from yerkon.hardware import DWM3000, SX1280
    from yerkon.siting import Requirement, cheapest
    from yerkon.world import Road, graded_alignment, rolling_terrain, flat_terrain

    from yerkon.cost import operating_rates
    from yerkon.hardware import radios as radio_catalogue
    from yerkon.world import mountings

    try:
        settings = _settings_from(args)
        catalogue_of_radios = (
            radio_catalogue(settings) if settings else RADIO_CHOICES
        )
        radio = chosen(catalogue_of_radios, args.radio, "radio")
        region = chosen(REGION_CHOICES, args.region, "region")
        requirement = Requirement(
            target_sigma_m=args.tolerance, corridor_covered=args.covered
        )
    except (FileNotFoundError, ValueError) as error:
        print(error, file=sys.stderr)
        return 2

    terrain = (
        flat_terrain() if args.relief <= 0.0
        else rolling_terrain(amplitude_m=args.relief, wavelength_m=3000.0,
                             micro_roughness_m=0.2)
    )
    centreline = [
        (float(x), 0.0)
        for x in range(0, int(args.corridor) + 1, 500)
    ]
    road = Road(centreline_m=centreline, terrain=terrain,
                surface_m=graded_alignment(centreline, terrain))
    units = (
        Receiver("araç", Journey(road=road, speed_m_s=27.8, duration_s=300.0),
                 radios=(SX1280, DWM3000)),
    )

    print("Searching {:.1f} km at a {:.1f} m tolerance, {:.0f}% covered."
          .format(args.corridor / 1000.0, args.tolerance, args.covered * 100),
          file=sys.stderr)

    from yerkon.siting import Availability, TYPICAL_ROADSIDE

    if settings:
        # Rebuild what stands beside the road from the same file, so a
        # run against real site costs searches over real structures.
        rebuilt = mountings(settings)
        by_kind = {option.kind: option for option in rebuilt.values()}
        available = tuple(
            Availability(
                by_kind.get(entry.mounting.kind, entry.mounting),
                entry.every_m, entry.from_m, entry.to_m,
            )
            for entry in TYPICAL_ROADSIDE
        )
        rates = operating_rates(settings)
    else:
        available = TYPICAL_ROADSIDE
        rates = None

    winner, everything = cheapest(
        terrain, args.corridor, units, radio=radio,
        requirement=requirement, region=region,
        available=available,
        **({"rates": rates} if rates else {}),
    )

    shown = everything if args.all else tuple(c for c in everything if c.meets)
    print("{:<34}{:>8}{:>15}{:>10}".format(
        "candidate", "anchors", "CAPEX [TL]", "covered"))
    print("-" * 67)
    for candidate in shown:
        print("{:<34}{:>8}{:>15}{:>10}  {}".format(
            candidate.label,
            len(candidate.anchors),
            decimal_comma(candidate.costing.capex_tl, 0),
            "%" + decimal_comma(100.0 * candidate.corridor_covered, 1),
            "" if candidate.meets else "(short)",
        ))

    if winner is None:
        print("\nNothing on offer meets that. Loosen the tolerance, accept "
              "less of the corridor, or allow taller structures.",
              file=sys.stderr)
        return 1

    counted: dict = {}
    for anchor in winner.anchors:
        counted[anchor.mounting.kind] = counted.get(anchor.mounting.kind, 0) + 1

    print("\nCheapest that meets it: {}".format(winner.label))
    for kind, count in sorted(counted.items()):
        print("  {} x {}".format(count, kind))
    print("  {} TL to build, {} TL a year to run".format(
        decimal_comma(winner.costing.capex_tl, 0),
        decimal_comma(winner.costing.opex_tl_per_year, 0)))
    print("  {} km² served, {} TL per km², {} TL per route kilometre".format(
        decimal_comma(winner.served_km2, 2),
        decimal_comma(winner.costing.capex_tl_per_km2, 0),
        decimal_comma(winner.costing.capex_tl_per_route_km, 0)))
    print("  {} of that rests on rates nobody supplied.".format(
        "%" + decimal_comma(100.0 * winner.costing.assumed_share, 0)))
    return 0


def defaults(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="yerkon defaults",
        description=(
            "Every figure this project needs that the report did not "
            "supply, in one list, with what each affects. Replacing one "
            "is an edit to defaults.toml, not a change to the code."
        ),
    )
    parser.add_argument(
        "--file", help="a settings file to read instead of the shipped one"
    )
    parser.add_argument(
        "--sourced", action="store_true",
        help="list the figures that have been sourced instead",
    )
    parser.add_argument(
        "--full", action="store_true",
        help="print each figure's note and sensitivity too",
    )
    args = parser.parse_args(argv)

    from yerkon.settings import DEFAULT_FILE, load

    try:
        settings = load(args.file)
    except (FileNotFoundError, ValueError) as error:
        print(error, file=sys.stderr)
        return 2

    listed = settings.sourced_entries if args.sourced else settings.assumed
    heading = "Sourced" if args.sourced else "Still assumed"

    print("{} in {}".format(heading, settings.path))
    print("{} of {} figures are still assumptions ({}).".format(
        len(settings.assumed), len(settings.entries),
        "%" + decimal_comma(100.0 * settings.assumed_share, 0),
    ))
    print()

    if not listed:
        print("  none.")
        return 0

    width = max(len(entry.key) for entry in listed)
    for entry in listed:
        print("{key:<{width}}  {value:>12} {unit}".format(
            key=entry.key, width=width,
            value=readable(float(entry.sourced.value)),
            unit=entry.sourced.unit,
        ))
        print("{:<{width}}  affects: {}".format("", entry.affects, width=width))
        if args.full:
            print("{:<{width}}  {}".format("", entry.sourced.note, width=width))
            if entry.sensitivity:
                print("{:<{width}}  sensitivity: {}".format(
                    "", entry.sensitivity, width=width))
        print()

    if not args.sourced:
        print("To replace one: copy {}, edit the value and the source, and "
              "change provenance from ASSUMPTION.".format(DEFAULT_FILE))
        print("Then pass --defaults with your copy to any other command.")
    return 0


def budget(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="yerkon budget",
        description=(
            "Take each scenario's position error apart, one source at a "
            "time, and say which source is worth removing. Every line is "
            "the same simulation the table uses, re-run with one error "
            "silenced, so this is slow: a couple of minutes per scenario."
        ),
    )
    parser.add_argument(
        "--only", action="append", choices=sorted(SCENARIO_CHOICES),
        help="dissect only these scenarios; repeat the flag for several",
    )
    parser.add_argument(
        "--source", action="append", choices=list(SOURCE_NAMES),
        help=(
            "dissect only these error sources; repeat the flag for "
            "several. The default is all of them."
        ),
    )
    _add_defaults_flag(parser)
    args = parser.parse_args(argv)

    try:
        settings = _settings_from(args)
    except (FileNotFoundError, ValueError) as error:
        print(error, file=sys.stderr)
        return 2

    from yerkon.budget import dissect_all
    from yerkon.scenarios import catalogue

    available = catalogue(settings) if settings else SCENARIO_CHOICES
    chosen = (
        tuple(available[name] for name in args.only)
        if args.only else tuple(available.values())
    )
    sources = tuple(args.source) if args.source else SOURCE_NAMES

    runs = len(chosen) * (2 * len(sources) + 2)
    print(
        "Running {} simulations: {} scenario{} against {} error "
        "source{}. This takes a few minutes.".format(
            runs, len(chosen), "" if len(chosen) == 1 else "s",
            len(sources), "" if len(sources) == 1 else "s",
        ),
        file=sys.stderr,
    )

    print(as_breakdown(dissect_all(chosen, sources)))
    return 0


def calibrate(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="yerkon calibrate",
        description=(
            "Read a measurement from the MATLAB scripts and print the "
            "defaults.toml entry that replaces the figure it stands in "
            "for. Nothing is written; the entry is printed to be pasted."
        ),
    )
    parser.add_argument("files", nargs="+", metavar="CSV",
                        help="what a MATLAB script wrote")
    args = parser.parse_args(argv)

    from yerkon.calibrate import read
    from yerkon.settings import DEFAULTS

    measured = []
    for path in args.files:
        try:
            measured.append(read(path))
        except (FileNotFoundError, ValueError) as error:
            print(error, file=sys.stderr)
            return 2

    for one in measured:
        try:
            was = DEFAULTS.number(one.key)
        except KeyError:
            was = None
        print("# {}".format(one.key))
        if was is not None:
            print("#   default {} {} -> measured {} {}".format(
                readable(was), one.unit, readable(one.value), one.unit))
            if was != 0.0:
                print("#   a factor of {} {}".format(
                    readable(max(was, one.value) / min(was, one.value)),
                    "better" if one.value < was else "worse",
                ))
        print(one.as_toml())
        print()

    print("# Paste these over the matching entries in defaults.toml,")
    print("# then re-run anything with --defaults pointing at it.")
    return 0


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or argv[0] in {"-h", "--help"}:
        print(__doc__.strip())
        print("\nUsage:")
        print("  yerkon fetch  --south .. --west .. --north .. --east .. --into DIR")
        print("  yerkon design [--region TR] [--mounting mast] [--tolerance 5]")
        print("  yerkon table  [--markdown] [--only rural]")
        print("  yerkon view   [--port 8765]")
        print("  yerkon site   [--corridor 12000] [--tolerance 5]")
        print("  yerkon budget [--only tunnel] [--source survey]")
        print("  yerkon defaults [--full]")
        print("  yerkon calibrate out/clock_residual.csv")
        return 0
    verb, rest = argv[0], argv[1:]
    if verb == "fetch":
        return fetch(rest)
    if verb == "design":
        return design(rest)
    if verb == "table":
        return table(rest)
    if verb == "view":
        return view(rest)
    if verb == "site":
        return site(rest)
    if verb == "budget":
        return budget(rest)
    if verb == "defaults":
        return defaults(rest)
    if verb == "calibrate":
        return calibrate(rest)
    print("Unknown command: {}".format(verb), file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
