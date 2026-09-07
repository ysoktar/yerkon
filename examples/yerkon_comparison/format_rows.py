"""Shared formatting for the 4 YERKON comparison-table rows, used by both
simulate_yerkon.py (CSV output) and render_comparison_table.py (PNG image),
so the two never drift apart."""

COLUMNS = [
    "Sistem", "Teknoloji", "Ortam", "HPE P50 [m]", "HPE P95 [m]", "VPE P95 [m]",
    "Kullanılabilirlik", "Alan [km²]", "CAPEX [TL/km²]", "OPEX [TL/km²/yıl]",
]


def fmt_m(value_m, decimals=2):
    if value_m >= 100:
        return f"≈ {value_m:,.0f}".replace(",", ".")
    return f"{value_m:.{decimals}f}".replace(".", ",")


def fmt_pct(fraction):
    return f"≈ %{fraction * 100:.1f}".replace(".", ",")


def fmt_tl_per_km2(value_tl):
    return f"≈ {value_tl:,.0f}".replace(",", ".")


def build_yerkon_rows(results):
    """Return the 4 YERKON rows, formatted, as a list of tuples matching
    COLUMNS."""
    urban = results["urban"]
    urban_raw = results["urban_uncalibrated"]
    rural = results["rural"]
    tunnel = results["tunnel"]

    return [
        (
            "YERKON (Şehir İçi - Kalibreli)¹", "Karasal PNT (SX1280/LoRa TWR)", "Dış",
            fmt_m(urban["hpe_p50_m"]), fmt_m(urban["hpe_p95_m"]), fmt_m(urban["vpe_p95_m"]),
            fmt_pct(urban["valid_fix_rate"]), fmt_m(urban["area_km2"]),
            fmt_tl_per_km2(urban["capex_per_km2_tl"]), "-",
        ),
        (
            "YERKON (Şehir İçi - Ham)⁵", "Karasal PNT (SX1280/LoRa TWR)", "Dış",
            fmt_m(urban_raw["hpe_p50_m"]), fmt_m(urban_raw["hpe_p95_m"]), fmt_m(urban_raw["vpe_p95_m"]),
            fmt_pct(urban_raw["valid_fix_rate"]), fmt_m(urban_raw["area_km2"]),
            fmt_tl_per_km2(urban_raw["capex_per_km2_tl"]), "-",
        ),
        (
            "YERKON (Kırsal)²", "Karasal PNT (E28-SX1280 TWR)", "Dış",
            fmt_m(rural["hpe_p50_m"]), fmt_m(rural["hpe_p95_m"]), fmt_m(rural["vpe_p95_m"]) + "³",
            fmt_pct(rural["valid_fix_rate"]), fmt_m(rural["area_km2"]),
            fmt_tl_per_km2(rural["capex_per_km2_tl"]), "-",
        ),
        (
            "YERKON (Kritik Bölge/Tünel)⁴", "Karasal PNT (UWB/DWM3000 TWR)", "İç + dış",
            fmt_m(tunnel["hpe_p50_m"]), fmt_m(tunnel["hpe_p95_m"]), fmt_m(tunnel["vpe_p95_m"]),
            fmt_pct(tunnel["valid_fix_rate"]), fmt_m(tunnel["area_km2"]),
            fmt_tl_per_km2(tunnel["capex_per_km2_tl"]), "-",
        ),
    ]
