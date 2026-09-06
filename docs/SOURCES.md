# Sources

Every source used by this project is recorded in code with its evidence
type, scope, and (where applicable) verification status - see
`locbench3d/core/evidence.py` for the controlled vocabulary. This file
summarizes them; the workbook's `official_references`,
`sx1280_published_data`, `sx1280_calibration_notes`, and
`sx1280_software_refs` sheets carry the same records in tabular form.

## Network access during development

This project was built in an environment where outbound HTTPS to
manufacturer, distributor, and standards-body web pages was blocked
(`WebFetch` returned `EGRESS_BLOCKED` for every domain tried, including
`semtech.com`, `stuartsprojects.github.io`, `mouser.com`, and
`example.com`). A search-snippet tool remained available. As a result:

- Two facts were confirmed via search-engine snippets this session
  (`verified_this_session=True` in `references/official_sources.py`):
  1. The current Semtech SX1281 product page is titled "LoRa Connect
     Transceiver, SX1281, 2.4GHz Without Ranging", distinct from the
     shared SX1280/SX1281 datasheet's "with Ranging Capability" title.
  2. GPS.gov's GPS accuracy page distinguishes signal-in-space user range
     error (<=2.0 m, 95%, daily global average) from receiver/user
     position accuracy.
- Every other official source listed below was not freshly fetched this
  session. Each carries an explicit note to that effect in its
  `EvidenceRecord.source_scope` and must be independently verified before
  a specific numeric claim from it is used for an engineering decision.

## Official / primary sources

| Topic | URL | Verified this session |
| --- | --- | --- |
| Semtech SX1280 | https://www.semtech.com/products/wireless-rf/lora-connect/sx1280 | No |
| Semtech SX1281 | https://www.semtech.com/products/wireless-rf/lora-connect/sx1281 | Yes (title only) |
| Semtech ranging FAQ (P40) | https://www.semtech.com/design-support/faq/P40 | No |
| IEEE 802.15.4 | https://standards.ieee.org/ieee/802.15.4/11041/ | No |
| GPS performance | https://www.gps.gov/gps-performance | No |
| GPS accuracy | https://www.gps.gov/gps-accuracy | Yes (SIS vs. user accuracy distinction) |
| BeiDou | https://en.beidou.gov.cn/ | No |
| Galileo | https://www.gsc-europa.eu/ | No |
| QZSS | https://qzss.go.jp/en/ | No |
| NavIC | https://www.isro.gov.in/ | No |
| Android Wi-Fi RTT | https://developer.android.com/develop/connectivity/wifi/wifi-rtt | No |
| MATLAB UWB toolbox | https://www.mathworks.com/help/comm/uwb.html | No |

## MATLAB UWB waveform evidence

`matlab/uwb_waveform_ranging.m` implements a waveform-level UWB ranging
simulation (Gaussian RF pulse via `gauspuls`, synthetic multipath, AWGN,
matched-filter leading-edge detection) that produces `MATLAB_WAVEFORM`
evidence when its output CSV is imported via `--matlab-uwb-csv`. It uses
IEEE 802.15.4 UWB channel 5 nominal parameters (center frequency 6489.6
MHz, bandwidth 499.2 MHz) as its default pulse configuration - general
knowledge of the 802.15.4 UWB PHY channelization, not independently
re-verified against the standard text this session. This script has never
been executed (no MATLAB license was available); see `matlab/README.md`
and `docs/LIMITATIONS.md` before trusting any output from it.

## Stuart Robinson's published SX1280 field data

Primary source: https://stuartsprojects.github.io/2019/04/26/Semtech-SX1280-2-4Ghz-LoRa-ranging-tranceivers.html

Related (long-range calibration): the two balloon-tracker posts and the
fast-LoRa post linked from `hardware/sx1280_published.py`.

All of this is `PUBLISHED_EXPERIMENT` evidence: one individual's field
tests, not a manufacturer specification and not a measurement taken by
this project. Specifically:

- The six short-range points (0-250 m) are the only short-range data this
  source publishes; this project does not extrapolate them into a general
  accuracy curve.
- The ~40 km and ~85 km results come from one calibration path and one
  hardware configuration each; they are not a validated long-range
  accuracy model.
- The ~89.237 km figure is a *communication reception* event, not a
  ranging measurement, and is flagged `is_verified_ranging_result=False`.
- The ~4.4 km at 203 kbps figure is a communication throughput benchmark,
  also flagged `is_verified_ranging_result=False`, and kept out of the
  ranging error table.

Software references (`SOFTWARE_REFERENCE` evidence):
https://github.com/StuartsProjects/SX1280 and
https://github.com/StuartsProjects/SX12XX-LoRa.

Community reference (`COMMUNITY_REFERENCE`, lower authority than
manufacturer documentation or the published field tests):
https://github.com/StuartsProjects/SX12XX-LoRa/issues/34.

## Hardware profiles without a fetched datasheet

NiceRF LoRa1280 (and TCXO/F27/F27-TCXO variants) and Ebyte E28 profiles in
`hardware/profiles.py` carry `verified_radio_ic=None` and a scope note
explaining that the SX1280 IC inside them is the manufacturer's claim, not
independently verified in this session. The Ebyte E28 entry is
additionally marked with a provenance conflict flag because Ebyte sells
multiple E28 suffix/revision variants and this project could not check
which exact suffix maps to which specification without a fetched
datasheet or a physical unit.

## GNSS sample data

`examples/gnss_sample_log.csv` is synthetic, generated for this project to
exercise the CSV importer and workbook pipeline. It is labeled
`SIMULATED_MONTE_CARLO` and explicitly is not a real receiver capture.
