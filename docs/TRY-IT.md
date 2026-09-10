# Trying the recent work

Everything below landed on `claude/3d-localization-benchmark-bm3unn` in
twelve commits on 10 September 2026. It is ordered so each step shows one
thing, and the slow ones say how slow.

```bash
git pull
pip install -e ".[dev]"
```

Nothing here needs the network. The ground the table stands on is
committed inside the package.

---

## Start here: the app

```bash
yerkon view
```

**The GUI is the main way in** — everything the command line does, the
page does too, against the settings the page is showing rather than the
shipped defaults.

### Moving around (this was broken)

The camera could only orbit a fixed point, and every edit re-centred it,
so panning was pointless.

- **Drag** turns.
- **Right-drag**, middle-drag or **Shift+drag** slides the ground. The
  point you grab stays under the cursor.
- **Wheel** zooms *towards the cursor*, scaled by how far the wheel
  actually turned — a trackpad creeps, a mouse notch steps.
- **W A S D** / arrows walk the way the camera faces. Shift goes faster.
- **Q** / **E** spin. **+** / **−** zoom. **F** frames everything.
- Drag an anchor: it now follows the terrain, not one flat plane.

Set a view, change any slider, and check the camera *stays put*. That is
the fix.

### The ground

**Zemin** picks what the deployment stands on. Four real Ankara places
ship with the package:

| site | what it is |
|---|---|
| `kizilay` | the town — 91 m of relief across 3 km |
| `polatli` | the steppe the intercity roads run through — 486 m over 20 km |
| `golbasi` | hills — 907 m over 20 km |
| `kizilcahamam` | the mountain the tunnel bores through |

There is **no flat option**, on the selector or the relief slider.
Nowhere is flat, and a level plane is the most favourable ground this
model can draw rather than the neutral one.

**Yeni bir yer getir** fetches anywhere else: a bounding box, a grid
spacing, and whether to ask OpenStreetMap for buildings. It writes into
the package's site folder, so it appears in the selector at once — and a
report row can then stand on it (see `rural.site` below). *This is the
one part I could not verify: the sandbox I work in blocks OpenStreetMap.
The elevation half is the same path the four Ankara sites came through.*

### Modes and shape

Four modes. **En** (width) decides whether the site is a line or an area:
at zero, anchors line a road and units drive straight; above zero they
spread over a staggered grid and units drive a circuit. Urban and rural
open as areas; the tunnel and the mixed corridor as lines.

### Every number, live

The **Varsayılan değerler** panel now holds *sixteen deployment figures*
that used to be literals in the code — anchor spacing, site extent,
stagger, anchors polled per round, ranging tolerance, bore width — plus
the ground-patch controls. They were sent to the page for a whole release
with no heading to draw them under, so they were present, correct and
invisible. Now they are there.

`<row>.site` renders as a picker of the sites actually fetched.

### Running things (Çalıştır)

| button | what it does | how long |
|---|---|---|
| **Tablo** | the report rows | ~70 s for all three |
| **Hata dağılımı** | the error dissection, drawn as bars | ~4 min for all three |
| **Markdown olarak yaz** | writes the whole study to files | table only: ~70 s |

Pick one row in **Hangi satırlar** to make them quicker. They report a
line at a time while they run.

### The solver (Çözücü)

Set a target — leave a box empty and it is not a condition — and it
searches for the **cheapest arrangement that meets it**, not the best.
Under **Sayı ekle** you choose *which* figures to search and what values
to try; the short list per scenario is a starting point, not a menu.

Worth trying, because it found something nobody had:

- Scenario `tunnel`, HPE P50 ≤ 1,0, availability ≥ 0,99
- It finds 120 m bracket spacing: **1,77 m → 0,48 m** for about 23000 TL.

Give it a name under **Kaydedilecek ad** and it saves as an option the
list then offers.

---

## From a terminal

```bash
yerkon table                  # the four rows            ~70 s
yerkon budget                 # the error dissection     ~4 min
yerkon budget --only tunnel   #                          ~45 s
yerkon options                # the named deployments
yerkon options rural-dense    # one of them in full
yerkon table --option rural-hard-ground     # the same rural row on hills
yerkon solve --scenario tunnel --hpe-p50 1.0 --availability 0.99
yerkon deliver --into docs/teslim --no-budget   # the study as Markdown
yerkon defaults --full        # every figure and what it rests on
```

Everything runs on as many cores as the machine spares — one less than it
has, so the viewer stays usable. `yerkon table` was four minutes before
that and is seventy seconds now.

---

## What to look for, and what it cost

### The table

| | HPE P50 | HPE P95 | Availability |
|---|---|---|---|
| Şehir içi | 1,62 m | 4,52 m | %99,41 |
| Kırsal | 2,69 m | 10,89 m | %89,50 |
| Tünel | 1,77 m | 2,99 m | %100,00 |
| Ağırlıklı | 1,93 m | 7,22 m | %93,44 |

### Five findings worth checking yourself

**The tunnel is the least accurate row despite the best hardware.** Run
`yerkon budget --only tunnel`. It ranges twenty-nine times better than the
town and positions no better, because a bore multiplies one range's error
eighteenfold and what it multiplies hardest is the anchor survey error —
the one term that never averages out. Surveying the brackets properly
takes that row from 1,77 m to 0,17 m. A better radio buys nothing.

**Rural availability is a round-size problem, not a mast problem.** Not
one rural link fails for distance — every failure is ground in the way.
Polling twelve anchors a round instead of eight is worth 5,5 points and
costs no capital. Nineteen extra masts buy less.

**Both rural options are now poor value, and their notes say so.** They
were written when the default sat at 82,26 %; the round-size fix took it
to 89,50 % for nothing, and most of what they bought went with it.
`rural-dense` is 1,9 points for 3,4 million lira.

**A slope was being counted as roughness, by a factor of forty.** On a
12 % grade the model reported 2,8 m of roughness where the ground is
smooth to 7 cm. Correcting it — and correcting the tilt term that has to
come with it — moved the table by less than seed noise, because the old
model was reaching the same place by the wrong route.

**One shipped option did nothing at all.** `rural-hard-ground` produced
the default's numbers to every digit. Try `yerkon table --option
rural-hard-ground` now and the rural row should collapse; before, it
changed a figure nothing reads.

---

## Where to argue with it

- `docs/adr/` — twenty-seven decisions, each with what it cost. The
  recent ones are 0020 to 0027.
- `src/yerkon/defaults.toml` — sixty-nine figures. Thirty-five are still
  placeholders; the mast cost at 85000 TL is the one that decides whether
  masts or existing roadside furniture win.
- `yerkon defaults --full` prints all of it with what each affects.

Two things I could not do from here, both written down rather than
assumed: OpenStreetMap is unreachable from my sandbox, so no site carries
buildings or road geometry — which makes the urban obstruction a clutter
figure per kilometre and every rural journey a rectangle over the ground
rather than a road following it. Both make the numbers conservative.
