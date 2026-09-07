"""Render the PNT/GNSS-backup comparison table (10 baseline systems, as
transcribed from the source comparison chart, plus 4 YERKON rows computed
by ``simulate_yerkon.py``) as a PNG image, in the same visual style as the
original chart.

The 10 baseline rows are reference figures transcribed from the comparison
table this was built to extend - they are not computed by this project.
The 4 YERKON rows ARE computed, live, by simulate_yerkon.run_all() every
time this script runs, so the numbers in the image always match what the
simulation actually produces.

Requires matplotlib (not a locbench3d dependency - install separately):

    pip install matplotlib
    python examples/yerkon_comparison/render_comparison_table.py

Writes yerkon_comparison_table.png next to this script.
"""
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from format_rows import build_yerkon_rows
from simulate_yerkon import run_all

HEADER_BG = "#4472C4"
HEADER_FG = "white"
ROW_BG_A = "#DCE6F5"
ROW_BG_B = "#EAF0FA"
YERKON_BG_A = "#FDE9D9"
YERKON_BG_B = "#FEF3E8"
BORDER = "#8EA9DB"

# Same columns as format_rows.COLUMNS, with line breaks for the image's
# narrower header cells.
COLUMNS = [
    "Sistem", "Teknoloji", "Ortam", "HPE\nP50 [m]", "HPE\nP95 [m]", "VPE\nP95 [m]",
    "Kullanılabilirlik", "Alan [km²]", "CAPEX\n[TL/km²]", "OPEX\n[TL/km²/yıl]",
]

# Baseline rows transcribed from the source comparison chart (not computed
# by this project).
BASELINE_ROWS = [
    ("GPS", "GNSS", "Dış", "-", "≤ 8", "≤ 13", "≥ %99 / ≥ %90", "510.064.472", "≈ 683,80", "≈ 37,99"),
    ("Galileo OS", "GNSS", "Dış", "-", "≤ 7,5", "≤ 15", "≥ %90", "510.064.472", "≈ 615,90", "≈ 65,12"),
    ("GLONASS", "GNSS", "Dış", "-", "≤ 5 / ≤ 12", "≤ 9 / ≤ 25", "≥ %99 / ≥ %90", "510.064.472", "-", "≈ 17,84"),
    ("BeiDou BDS", "GNSS", "Dış", "-", "≤ 10 / ≤ 5", "≤ 10 / ≤ 5", "> %95", "510.064.472", "≥ ≈ 792,51", "-"),
    ("QZSS SLAS", "GNSS desteği", "Dış", "-", "R1 ≤ 1 / R2 ≤ 2", "R1 ≤ 2 / R2 ≤ 3", "100%", "-", "-", "≤ ≈ 10.904,49"),
    ("NavIC SPS", "Bölgesel GNSS", "Dış", "-", "-", "-", "-", "≈ 33.243.459", "≈ 218,99", "-"),
    ("TerraPoiNT", "Karasal PNT", "İç + dış", "≤ 3", "≤ 8", "2", "%99,96", "≈ 900", "-", "-"),
    ("Locata", "Pseudolite PNT", "İç + dış", "-", "0,017", "0,024", "999999%", "≈ 6.475", "-", "-"),
    ("Pozyx", "UWB RTLS", "İç + dış", "0,114", "0,181", "-", "≥ 0,035", "-", "-", "-"),
    ("eLoran", "Karasal PNT", "Dış", "-", "15,72", "-", "-", "≤ 8.482,30", "-", "-"),
]


# format_rows.build_yerkon_rows() returns single-line cell text (it also
# backs the CSV output, where line breaks would be wrong). For the image's
# narrower columns, re-wrap just the long Sistem/Teknoloji cells.
_IMAGE_WRAP = {
    "YERKON (Şehir İçi - Kalibreli)¹": "YERKON (Şehir İçi -\nKalibreli)¹",
    "YERKON (Şehir İçi - Ham)⁵": "YERKON (Şehir İçi -\nHam)⁵",
    "YERKON (Kritik Bölge/Tünel)⁴": "YERKON (Kritik Bölge/\nTünel)⁴",
    "Karasal PNT (SX1280/LoRa TWR)": "Karasal PNT (SX1280/\nLoRa TWR)",
    "Karasal PNT (E28-SX1280 TWR)": "Karasal PNT (E28-\nSX1280 TWR)",
    "Karasal PNT (UWB/DWM3000 TWR)": "Karasal PNT (UWB/\nDWM3000 TWR)",
}


def wrap_for_image(rows):
    return [tuple(_IMAGE_WRAP.get(cell, cell) for cell in row) for row in rows]


def render(all_rows, out_path):
    n_rows = len(all_rows) + 1
    fig_h = 0.62 * n_rows + 1.6
    fig, ax = plt.subplots(figsize=(16, fig_h))
    ax.axis("off")

    col_widths = [0.135, 0.145, 0.075, 0.075, 0.085, 0.085, 0.115, 0.10, 0.095, 0.09]
    assert abs(sum(col_widths) - 1.0) < 1e-6, sum(col_widths)

    table = ax.table(
        cellText=[COLUMNS] + [list(r) for r in all_rows],
        colWidths=col_widths,
        cellLoc="center",
        loc="center",
    )
    table.auto_set_font_size(False)
    table.set_fontsize(10.5)
    table.scale(1, 2.35)

    n_baseline = 1 + len(BASELINE_ROWS)
    for (row, col), cell in table.get_celld().items():
        cell.set_edgecolor(BORDER)
        cell.set_linewidth(1.0)
        if row == 0:
            cell.set_facecolor(HEADER_BG)
            cell.get_text().set_color(HEADER_FG)
            cell.get_text().set_fontweight("bold")
            cell.set_height(cell.get_height() * 1.5)
        elif row < n_baseline:
            cell.set_facecolor(ROW_BG_A if row % 2 == 1 else ROW_BG_B)
        else:
            cell.set_facecolor(YERKON_BG_A if (row - n_baseline) % 2 == 0 else YERKON_BG_B)
            if col == 0:
                cell.get_text().set_fontweight("bold")
        if col == 0:
            cell.get_text().set_ha("left")
            cell.PAD = 0.02

    plt.tight_layout()
    plt.savefig(out_path, dpi=200, bbox_inches="tight", facecolor="white")


if __name__ == "__main__":
    results = run_all()
    all_rows = BASELINE_ROWS + wrap_for_image(build_yerkon_rows(results))
    out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "yerkon_comparison_table.png")
    render(all_rows, out_path)
    print(f"Saved {out_path}")
