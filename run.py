#!/usr/bin/env python3
"""Produce the four YERKON comparison-table rows.

    python run.py                  # writes the CSV
    python run.py --image          # also renders the PNG (needs matplotlib)
    python run.py --details        # also writes the full metrics as JSON
    python run.py --repeats 1000   # more Monte Carlo repeats, same seed

Output goes to output/ next to this file. The default run writes only the
four rows; everything else is opt-in.
"""
from __future__ import annotations

import argparse
import json
import os
import sys

from yerkon.scenarios import N_REPEATS, SEED, run_all
from yerkon.table import build_rows, detail_records, write_csv

HERE = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(HERE, "output")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--image", action="store_true",
        help="also render the comparison table as a PNG (requires matplotlib)",
    )
    parser.add_argument(
        "--details", action="store_true",
        help="also write full per-scenario metrics as JSON",
    )
    parser.add_argument(
        "--repeats", type=int, default=N_REPEATS,
        help="Monte Carlo repeats per path sample (default: %(default)s)",
    )
    parser.add_argument(
        "--seed", type=int, default=SEED,
        help="random seed; the same seed always gives the same numbers "
             "(default: %(default)s)",
    )
    parser.add_argument(
        "--out", default=OUTPUT_DIR,
        help="output directory (default: ./output)",
    )
    args = parser.parse_args(argv)

    os.makedirs(args.out, exist_ok=True)
    results = run_all(n_repeats=args.repeats, seed=args.seed)
    rows = build_rows(results)

    csv_path = os.path.join(args.out, "yerkon_rows.csv")
    try:
        write_csv(rows, csv_path)
    except PermissionError:
        print(
            "ERROR: could not write {}. It is probably open in Excel; "
            "Windows locks open files. Close it and run again.".format(csv_path),
            file=sys.stderr,
        )
        return 1
    print("Wrote {}".format(csv_path))

    for row in rows:
        print("  " + " | ".join(row))

    if args.details:
        json_path = os.path.join(args.out, "yerkon_details.json")
        with open(json_path, "w", encoding="utf-8") as handle:
            json.dump(detail_records(results), handle, indent=2, ensure_ascii=False)
        print("Wrote {}".format(json_path))

    if args.image:
        try:
            from yerkon.render import render_table
        except ImportError:
            print(
                "ERROR: --image needs matplotlib. Install it with "
                "'pip install matplotlib' and run again.",
                file=sys.stderr,
            )
            return 1
        png_path = os.path.join(args.out, "yerkon_comparison_table.png")
        render_table(rows, png_path)
        print("Wrote {}".format(png_path))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
