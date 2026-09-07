"""Render the comparison table as a PNG.

The ten baseline rows are reference figures for other positioning systems,
transcribed from the comparison chart this output extends. They are not
computed here and are not claims this project makes. The four YERKON rows
below them are computed on every run, and are shaded differently so the
distinction survives a screenshot.

matplotlib is imported lazily so the rest of the pipeline runs without it.
"""
from __future__ import annotations

from typing import Sequence

HEADER_BG = "#4472C4"
HEADER_FG = "white"
ROW_BG_A = "#DCE6F5"
ROW_BG_B = "#EAF0FA"
YERKON_BG_A = "#FDE9D9"
YERKON_BG_B = "#FEF3E8"
BORDER = "#8EA9DB"

#: Column headings, with line breaks the CSV does not need.
IMAGE_COLUMNS = (
    "Sistem", "Teknoloji", "Ortam", "HPE\nP50 [m]", "HPE\nP95 [m]", "VPE\nP95 [m]",
    "Kullanılabilirlik", "Alan [km²]", "CAPEX\n[TL/km²]", "OPEX\n[TL/km²/yıl]",
)

#: Reference rows for other systems, transcribed from the source chart.
#: Not produced by this project; shown for context only.
BASELINE_ROWS = (
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
)

#: Long cell text is wrapped for the image's narrower columns. The CSV keeps
#: the single-line form.
_WRAP = {
    "YERKON (Şehir İçi - Kalibreli)¹": "YERKON (Şehir İçi -\nKalibreli)¹",
    "YERKON (Şehir İçi - Ham)²": "YERKON (Şehir İçi -\nHam)²",
    "YERKON (Kritik Bölge/Tünel)⁴": "YERKON (Kritik Bölge/\nTünel)⁴",
    "Karasal PNT (SX1280/LoRa TWR)": "Karasal PNT (SX1280/\nLoRa TWR)",
    "Karasal PNT (E28-SX1280 TWR)": "Karasal PNT (E28-\nSX1280 TWR)",
    "Karasal PNT (UWB/DWM3000 TWR)": "Karasal PNT (UWB/\nDWM3000 TWR)",
}


def wrap_for_image(rows: Sequence[tuple[str, ...]]) -> list[tuple[str, ...]]:
    return [tuple(_WRAP.get(cell, cell) for cell in row) for row in rows]


def render_table(yerkon_rows: Sequence[tuple[str, ...]], out_path: str) -> str:
    """Draw the baseline rows and the computed YERKON rows into one PNG."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    all_rows = list(BASELINE_ROWS) + wrap_for_image(yerkon_rows)
    n_rows = len(all_rows) + 1

    fig, ax = plt.subplots(figsize=(16, 0.62 * n_rows + 1.6))
    ax.axis("off")

    col_widths = [0.135, 0.145, 0.075, 0.075, 0.085, 0.085, 0.115, 0.10, 0.095, 0.09]
    table = ax.table(
        cellText=[list(IMAGE_COLUMNS)] + [list(r) for r in all_rows],
        colWidths=col_widths,
        cellLoc="center",
        loc="center",
    )
    table.auto_set_font_size(False)
    table.set_fontsize(10.5)
    table.scale(1, 2.35)

    first_yerkon_row = 1 + len(BASELINE_ROWS)
    for (row, col), cell in table.get_celld().items():
        cell.set_edgecolor(BORDER)
        cell.set_linewidth(1.0)
        if row == 0:
            cell.set_facecolor(HEADER_BG)
            cell.get_text().set_color(HEADER_FG)
            cell.get_text().set_fontweight("bold")
            cell.set_height(cell.get_height() * 1.5)
        elif row < first_yerkon_row:
            cell.set_facecolor(ROW_BG_A if row % 2 == 1 else ROW_BG_B)
        else:
            shade = (row - first_yerkon_row) % 2 == 0
            cell.set_facecolor(YERKON_BG_A if shade else YERKON_BG_B)
            if col == 0:
                cell.get_text().set_fontweight("bold")
        if col == 0:
            cell.get_text().set_ha("left")
            cell.PAD = 0.02

    plt.tight_layout()
    plt.savefig(out_path, dpi=200, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return out_path
