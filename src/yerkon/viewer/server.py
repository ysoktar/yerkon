"""A local web app over the same engine the table uses.

Started with ``yerkon view``. Serves one page and a handful of JSON
endpoints from the standard library, so there is nothing to install and
it behaves the same on Windows as anywhere else.

The page holds no physics. Every number it shows was computed here, by
the modules the report is built from, which is what stops the picture and
the table drifting apart (ADR-0001).

One rule about editing, and it is ADR-0009. A change that forces other
settings to change — the region, the mounting, the radio, the tolerance —
goes through the confirmation panel and waits for a yes. Dragging an
anchor or moving a terrain slider forces nothing, so it applies at once
and the scene recomputes.
"""

from __future__ import annotations

import io
import json
import pathlib
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Optional
from urllib.parse import parse_qs, urlparse

from yerkon.design import Design
from yerkon.proposal import propose
from yerkon.viewer.jobs import Jobs
from yerkon.options import read as read_option
from yerkon.viewer.scene import (
    MAP_TILES,
    design_of,
    figures,
    ground,
    pool,
    scene,
    simulate,
    sweep,
)
from yerkon.viewer.tasks import (
    budget as budget_task,
    deliver as deliver_task,
    fetch as fetch_task,
    listed,
    solve as solve_task,
    place as place_task,
    table as table_task,
    target_from,
)
from yerkon.language import chosen as language_chosen, say
from yerkon.presets import Preset, PresetStore, UnknownPreset, offered
from yerkon.scenarios import SITES
from yerkon.site.cache import AERIAL_NAME
from yerkon.published import read as published_read
from yerkon.viewer.pages import SIMULATOR, page_at, render
from yerkon.viewer.state import (
    CASCADING,
    MODES,
    ViewState,
    from_scenario,
)

STATIC = pathlib.Path(__file__).parent / "static"

#: Where saved arrangements are kept, as a one-item list so `--presets`
#: can replace it without two copies of the answer (ADR-0043). The
#: working directory by default, beside `defaults.toml`: it is the thing
#: a person keeps with the study rather than inside the installation.
PRESETS = [PresetStore("presets")]


def _preset_label(preset, language: str) -> str:
    """What to call it in the picker.

    The two shipped ones are keys and get a translated label; a saved one
    is called whatever the person called it, in whatever they called it.
    """
    if preset.source == "shipped":
        return say("preset.{}".format(preset.name), language)
    return preset.name


def _find_preset(name: str, state) -> "Preset":
    for preset in offered(state.scenario, PRESETS[0], from_scenario):
        if preset.name == name:
            return preset
    raise UnknownPreset(say(
        "preset.unknown", state.language, name=name,
        known=", ".join(p.name for p in offered(
            state.scenario, PRESETS[0], from_scenario)),
        directory=str(PRESETS[0].directory)))


class Session:
    """Three prepared deployments, and which one the page is showing.

    One per row of the table, held at once. A dropdown that replaced the
    arrangement on every switch meant an afternoon spent on the rural row
    was gone the moment somebody looked at the tunnel, so nothing could
    be prepared and compared. Tabs keep all three, and a run takes either
    the one showing or all of them
    (ADR-0028).

    A lock rather than a queue: the sweep takes seconds and a person can
    move a slider in that time, so two requests really do overlap. What
    they must not do is interleave a read with a write.
    """

    def __init__(self, showing: str = "urban") -> None:
        self.states = {name: from_scenario(name) for name in MODES}
        self.showing = showing if showing in MODES else MODES[0]
        self._lock = threading.Lock()

    def read(self, name: Optional[str] = None) -> ViewState:
        with self._lock:
            return self.states[name or self.showing]

    def write(self, state: ViewState, name: Optional[str] = None) -> ViewState:
        with self._lock:
            self.states[name or self.showing] = state
            return state

    def show(self, name: str) -> ViewState:
        if name not in MODES:
            raise ValueError(
                "no row called {!r}. There are: {}".format(
                    name, ", ".join(MODES)
                )
            )
        with self._lock:
            self.showing = name
            return self.states[name]

    def prepared(self, only=None) -> tuple:
        """The rows a run should cover, as (name, state), in table order."""
        with self._lock:
            wanted = list(only) if only else list(MODES)
            unknown = [name for name in wanted if name not in self.states]
            if unknown:
                raise ValueError(
                    "no row called {}".format(", ".join(unknown))
                )
            return tuple((name, self.states[name]) for name in wanted)

    def speak(self, language: Optional[str]) -> ViewState:
        """Put every row into one language, and return the one showing."""
        wanted = language_chosen(language)
        with self._lock:
            self.states = {
                name: state.merged({"language": wanted})
                for name, state in self.states.items()
            }
            return self.states[self.showing]

    def reset(self, name: Optional[str] = None) -> ViewState:
        """Put one row back as it ships, keeping the language on screen."""
        with self._lock:
            which = name or self.showing
            language = self.states[which].language
            self.states[which] = from_scenario(which).merged(
                {"language": language}
            )
            return self.states[which]


def cascades(state: ViewState, changes: dict) -> Optional[dict]:
    """What a change would drag with it, or nothing if it drags nothing.

    Only settings the link budget reads can cascade. A terrain slider
    changes the world rather than the radio, and the panel would have
    nothing to say about it.

    A corridor carries more than one kind of anchor, so a change to one
    run is proposed against that run alone and the panel says which. A
    change to a setting the whole deployment shares — the region, the
    tolerance, the ground roughness — is proposed against every run,
    because it moves all of them and a person should see all of it.
    """
    if not any(
        name in CASCADING or name in ("runs", "overrides") or name in CAN_SHRINK
        for name in changes
    ):
        return None

    proposed = state.merged(changes)
    groups = list(_shortened(state, proposed, changes))

    shared = {
        name: value for name, value in changes.items()
        if name in CASCADING or name == "overrides"
    }
    for index, run in enumerate(state.runs):
        after_run = proposed.runs[index] if index < len(proposed.runs) else run
        edits = {}
        if shared or after_run != run:
            before = design_of(state, run)
            after = design_of(proposed, after_run)
            edits = {
                field: getattr(after, field)
                for field in Design.__dataclass_fields__
                if getattr(after, field) != getattr(before, field)
            }
        if not edits:
            continue
        proposal = propose(design_of(state, run), **edits)
        if proposal.follows:
            groups.append({
                "run": run.identifier,
                "asked": [_change(c) for c in proposal.asked],
                "follows": [_change(c) for c in proposal.follows],
                "panel": proposal.describe(),
            })

    if not groups:
        return None
    return {
        "groups": groups,
        "panel": "\n\n".join(
            "[{}]\n{}".format(group["run"], group["panel"]) for group in groups
        ),
    }


#: Edits that can pull the study in, and so go through the panel.
#:
#: The length and the width because a person moved them; the ground
#: because a smaller fetch cannot hold a larger site (ADR-0037). An edit
#: to a run's own ends is not here: that is a person being explicit about
#: that run.
CAN_SHRINK = ("corridor_m", "width_m", "site")


def _shortened(state: ViewState, proposed: ViewState, changes: dict):
    """What shrinking the site does to the anchor runs standing on it.

    The site's width already shapes the anchors — a grid runs from the
    road out to it — and its length did not, because a run carries its
    own start and end. Making the length behave the same way moves
    anchors somebody placed, which is exactly the kind of change ADR-0009
    exists for: it is proposed with every figure it moves and waits for a
    yes.

    Choosing ground is the same kind of change arriving from the other
    side: a site is no larger than the grid fetched for it, so picking a
    smaller place pulls the length and the width in with it.
    """
    if not any(name in CAN_SHRINK for name in changes):
        return
    # Naming new ground can make the site bigger as well as smaller, and
    # the panel is where both are said before either happens (ADR-0054).
    settled = proposed.on_new_ground(state).within_site()
    key = next(name for name in CAN_SHRINK if name in changes)
    asked = {
        "key": key,
        "label": say({"corridor_m": "panel.site_length",
                      "width_m": "panel.site_width",
                      "site": "panel.ground"}[key], state.language),
        "before": getattr(state, key),
        "after": getattr(proposed, key),
        "because": "",
    }
    # What the measured ground did to the site itself, before anything
    # standing on it moved.
    bounds = [
        {
            "key": field,
            "label": field,
            "before": getattr(proposed, field),
            "after": getattr(settled, field),
            # Two different things happen here and they are not the same
            # sentence: a site can be brought in because the ground under
            # it stops, or opened out because it was the whole of its
            # ground and the new ground is bigger.
            "because": say(
                "panel.filled_the_ground"
                if getattr(settled, field) > getattr(proposed, field)
                else "panel.past_the_measurement",
                state.language),
        }
        for field in ("corridor_m", "width_m")
        if getattr(proposed, field) != getattr(settled, field)
    ]
    if bounds:
        yield {
            "run": "",
            "asked": [asked],
            "follows": bounds,
            "panel": "{} {}; {}".format(
                asked["label"], _said(asked["before"], asked["after"]),
                ", ".join("{} {}".format(one["key"],
                                         _said(one["before"], one["after"]))
                          for one in bounds),
            ),
        }
    for before, after in zip(proposed.runs, settled.runs):
        follows = [
            {
                "key": field,
                "label": field,
                "before": getattr(before, field),
                "after": getattr(after, field),
                "because": say("panel.past_the_site", state.language),
            }
            for field in ("from_m", "to_m")
            if getattr(before, field) != getattr(after, field)
        ]
        if not follows:
            continue
        yield {
            "run": before.identifier,
            "asked": [asked],
            "follows": follows,
            "panel": "{} {}; {} run {}".format(
                asked["label"], _said(asked["before"], asked["after"]),
                before.identifier,
                ", ".join(
                    "{} {:.0f} -> {:.0f}".format(
                        change["key"], change["before"], change["after"])
                    for change in follows
                ),
            ),
        }


def _said(before, after) -> str:
    """`3000 -> 2940 m`, or `kizilay -> golbasi` when it is a name."""
    if isinstance(before, (int, float)) and isinstance(after, (int, float)):
        return "{:.0f} -> {:.0f} m".format(before, after)
    return "{} -> {}".format(before or "modelled", after or "modelled")


def _change(change) -> dict:
    return {
        "key": change.key,
        "label": change.label,
        "before": change.before,
        "after": change.after,
        "because": change.because,
    }


class Handler(BaseHTTPRequestHandler):
    session: Session = Session()
    #: Work that takes minutes: the table, the dissection, a search.
    #:
    #: Started here and polled, rather than answered inside one request,
    #: because a browser gives up long before a twelve minute dissection
    #: finishes and because a person should be able to watch it (ADR-0024).
    jobs: Jobs = Jobs()

    # Quiet: a page that redraws on every drag would otherwise bury the
    # terminal in request lines.
    def log_message(self, *args) -> None:
        return

    def do_GET(self) -> None:
        path = self.path.split("?")[0]
        # The simulator is one page of a site rather than the whole of
        # it: somebody who has not been told what YERKON is has no use
        # for a slider on the noise figure (ADR-0064).
        if path in (SIMULATOR, SIMULATOR + "/"):
            return self._file("simulator.html", "text/html; charset=utf-8")
        if path in ("/app.js", "/draw.js", "/words.js", "/map.js",
                    "/theme.js"):
            return self._file(path.lstrip("/"), "text/javascript; charset=utf-8")
        if path == "/favicon.ico":
            self.send_response(204)
            self.end_headers()
            return
        if path in ("/style.css", "/site.css"):
            return self._file(path.lstrip("/"), "text/css; charset=utf-8")
        if path in ("/road.png", "/gnss.png", "/architecture.png",
                    "/simulator.png"):
            return self._file(path.lstrip("/"), "image/png")
        if path == "/api/figures":
            return self._json(lambda: figures(self.session.read()))
        if path == "/api/figures.toml":
            return self._toml(self.session.read())
        if path == "/api/scene":
            return self._json(lambda: scene(self.session.read()))
        if path == "/api/ground":
            return self._json(lambda: self._ground())
        if path == "/api/sweep":
            return self._json(lambda: sweep(self.session.read()))
        if path == "/api/simulate":
            return self._json(lambda: simulate(self.session.read()))
        # The same arrangement over every draw of the shadows. Asked for
        # after the first one is on screen, because it costs about twice
        # as long again and the page should not be blank for it.
        if path == "/api/simulate/pooled":
            return self._json(lambda: pool(self.session.read()))
        if path == "/api/options":
            return self._json(
                lambda: listed(self.session.read().settings())
            )
        if path == "/api/aerial.png":
            return self._aerial()
        if path == "/api/presets":
            return self._json(self._presets)
        if path == "/api/job":
            return self._json(self._job)
        page = page_at(path) if not path.startswith("/api/") else None
        if page is not None:
            return self._page(page)
        self.send_error(404)

    def do_POST(self) -> None:
        path = self.path.split("?")[0]
        length = int(self.headers.get("Content-Length", 0))
        try:
            body = json.loads(self.rfile.read(length) or b"{}")
        except ValueError:
            return self._fail("that was not JSON")

        if path == "/api/propose":
            return self._json(
                lambda: self._propose(body.get("changes", {}))
            )
        if path == "/api/apply":
            return self._json(lambda: self._apply(body.get("changes", {})))
        if path == "/api/mode":
            return self._json(lambda: self._mode(body.get("mode", "rural")))
        if path == "/api/language":
            return self._json(lambda: self._language(body.get("language")))
        if path == "/api/preset/load":
            return self._json(lambda: self._load_preset(body.get("name", "")))
        if path == "/api/preset/save":
            return self._json(lambda: self._save_preset(body.get("name", "")))
        if path == "/api/preset/delete":
            return self._json(lambda: self._drop_preset(body.get("name", "")))
        if path == "/api/reset":
            return self._json(
                lambda: {"state": self.session.reset().as_json()}
            )
        if path == "/api/option":
            return self._json(lambda: self._option(body.get("name", "")))
        if path == "/api/run":
            return self._json(lambda: self._run(body))
        self.send_error(404)

    def _ground(self) -> dict:
        """A finer mesh over the window the page says it is looking at."""
        from urllib.parse import parse_qs, urlsplit

        asked = parse_qs(urlsplit(self.path).query)

        def edge(name: str) -> float:
            try:
                return float(asked[name][0])
            except (KeyError, IndexError, ValueError):
                raise ValueError("ground needs west, east, south and north")

        west, east = edge("west"), edge("east")
        south, north = edge("south"), edge("north")
        if east <= west or north <= south:
            raise ValueError("that window has no ground in it")
        return ground(self.session.read(), west, east, south, north)

    # -- the two things a POST can mean -----------------------------------

    def _propose(self, changes: dict) -> dict:
        state = self.session.read()
        # Validate before answering, so a bad field name comes back as a
        # message rather than as a panel describing nothing.
        state.merged(changes)
        found = cascades(state, changes)
        return {"cascades": found} if found else {"cascades": None}

    def _language(self, language) -> dict:
        """Say the whole study in the other language.

        Every row at once rather than the one showing, because a language
        is a property of the person reading rather than of a row, and a
        page half in each is the thing this exists to avoid (ADR-0035).
        """
        return {"state": self.session.speak(language).as_json()}

    def _mode(self, name: str) -> dict:
        """Show one of the three rows, keeping what the others hold.

        Not an edit, so it does not go through the panel: nothing is
        changed into anything, the page just looks somewhere else
        (ADR-0028).
        """
        return {"state": self.session.show(name).as_json(), "showing": name}

    def _option(self, name: str) -> dict:
        """Apply a named deployment option to what the page is showing.

        An option is a short list of edits to the settings, so it lands
        in the same overrides a person edits by hand: it composes with
        their work rather than replacing it, and it can be undone the
        same way.
        """
        option = read_option(name)
        state = self.session.read()
        overrides = dict(state.overrides)
        for key, value in option.values.items():
            overrides[key] = {
                "value": float(value),
                "source": "option: {}".format(option.name),
            }
        updated = self.session.write(state.merged({"overrides": overrides}))
        return {"state": updated.as_json(), "applied": option.name}

    def _run(self, body: dict) -> dict:
        """Start a long task and hand back something to poll.

        The page holds no physics, so it cannot run any of these itself;
        what it gets is an identifier and a stream of lines.
        """
        kind = body.get("kind", "")
        state = self.session.read()
        only = body.get("only") or None
        # A run covers the rows as they have been prepared in their tabs,
        # not the shipped catalogue: what you set up is what you run.
        rows = self.session.prepared(only)

        if kind == "table":
            work = table_task(rows)
        elif kind == "budget":
            work = budget_task(rows, body.get("sources") or None)
        elif kind == "deliver":
            work = deliver_task(
                rows, body.get("into", ""),
                with_budget=bool(body.get("with_budget", True)),
            )
        elif kind == "fetch":
            work = fetch_task(state, body.get("where", {}))
        elif kind == "solve":
            work = solve_task(
                state,
                body.get("scenario", "rural"),
                target_from(body.get("target", {})),
                body.get("vary") or None,
                (body.get("save") or "").strip() or None,
            )
        elif kind == "place":
            work = place_task(state, body.get("aim", "better"))
        else:
            raise ValueError(
                "no such task: {!r}. There is: table, budget, solve, "
                "place, deliver, fetch".format(kind)
            )
        return {"job": self.jobs.start(kind, work).as_json()}

    def _job(self) -> dict:
        """How a running task is getting on."""
        from urllib.parse import parse_qs, urlparse

        wanted = parse_qs(urlparse(self.path).query).get("id", [""])[0]
        job = self.jobs.read(wanted)
        if job is None:
            raise ValueError("no task called {!r} is running".format(wanted))
        return {"job": job.as_json()}

    def _apply(self, changes: dict) -> dict:
        state = self.session.read()
        settled = state.merged(changes).on_new_ground(state)
        if any(name in CAN_SHRINK for name in changes):
            # Whatever the panel just showed and got a yes for. A run's
            # own ends are not in that list: typing one is a person being
            # explicit about that run.
            settled = settled.within_site()
        return {"state": self.session.write(settled).as_json()}

    # -- plumbing ----------------------------------------------------------

    def _toml(self, state: ViewState) -> None:
        """The figures as a file, so an afternoon's editing survives the tab.

        Served as a download rather than shown, because the useful thing
        to do with it is put it beside the project and pass it back with
        --defaults.
        """
        payload = state.settings().to_toml().encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/toml; charset=utf-8")
        self.send_header(
            "Content-Disposition", 'attachment; filename="defaults.toml"'
        )
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    # -- named arrangements (ADR-0043) -------------------------------------

    def _presets(self) -> dict:
        """What this tab can be loaded from, and what it is showing."""
        state = self.session.read()
        return {
            "showing": self.session.showing,
            "presets": [
                {
                    "name": preset.name,
                    "label": _preset_label(preset, state.language),
                    "mode": preset.mode,
                    "shipped": preset.source == "shipped",
                    "digest": preset.digest,
                }
                for preset in offered(state.scenario, PRESETS[0], from_scenario)
            ],
        }

    def _load_preset(self, name: str) -> dict:
        """Put a saved arrangement into this tab, and nothing into the others.

        `scenario` and `language` are not taken from the file. The row a
        tab runs as is decided by the tab, and the language by the
        session — an arrangement saved on the rural row and loaded into
        the urban one is somebody looking at it there on purpose, and it
        should not silently turn the urban tab into a rural row.
        """
        preset = _find_preset(name, self.session.read())
        carried = {
            key: value for key, value in (preset.state or {}).items()
            if key not in ("scenario", "language")
        }
        state = self.session.read().merged(carried)
        # `on_measured_ground` and not `within_site`.
        #
        # The first is a correctness rule: a site cannot be larger than
        # the ground somebody measured, or anchors stand on a number
        # nobody took (ADR-0037). The second clips each run to the site,
        # and this project has already decided a run's own typed end is
        # the person being explicit about that run (`_apply` says so).
        # Clipping here and not there would make one arrangement mean two
        # different things depending on whether it came from a file —
        # which is how an arrangement saved with twelve anchors came back
        # with nine.
        self.session.write(state.on_measured_ground())
        return {"state": self.session.read().as_json(), "loaded": preset.name}

    def _save_preset(self, name: str) -> dict:
        """Save this tab under a name, which may be one already in use.

        Overwriting is allowed on purpose: "save as" over the name you
        just loaded is how somebody iterates, and refusing it would send
        them to the file manager to delete a file first.
        """
        state = self.session.read()
        preset = Preset(name=str(name).strip(), mode=state.scenario,
                        state=state.as_json())
        path = PRESETS[0].write(preset)
        return {"saved": preset.name, "path": str(path),
                "digest": preset.digest}

    def _drop_preset(self, name: str) -> dict:
        PRESETS[0].remove(str(name).strip())
        return {"removed": str(name).strip()}

    def _aerial(self) -> None:
        """The site's photograph, straight off the disk the fetch wrote it to.

        Named by the caller rather than read from the session, so that
        the browser can cache it: a picture whose address is the same for
        every site is a picture the browser hands back for the wrong one.
        The name is a single path segment or nothing doing — it arrives
        from a query string, and a query string is somewhere a person can
        type `../../etc/passwd`.
        """
        asked = parse_qs(urlparse(self.path).query).get("site", [""])[0]
        if not asked or asked != pathlib.Path(asked).name or asked.startswith("."):
            return self.send_error(404)
        picture = SITES / asked / AERIAL_NAME
        if not picture.exists():
            return self.send_error(404)
        payload = picture.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", "image/png")
        self.send_header("Content-Length", str(len(payload)))
        # A fetch rewrites the file, and the address does not change with
        # it, so the browser is told to ask again rather than to trust
        # what it has.
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        self.wfile.write(payload)

    def _page(self, page) -> None:
        """One page of the site, in the language the session is set to.

        A language is switched with a link rather than with a script,
        because these pages carry no script: ``?dil=en`` says it, and it
        moves the simulator with it, the same way the simulator's own
        TR/EN moves these (ADR-0035).
        """
        asked = parse_qs(urlparse(self.path).query).get("dil", [None])[0]
        if asked in ("tr", "en"):
            self.session.speak(asked)
        language = self.session.read().language
        try:
            record = published_read()
        except (OSError, ValueError, KeyError):
            # A site that will not open because nobody has published a
            # run yet is worse than a site that says so on one page.
            record = None
        payload = render(page, language, record).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        # The published table changes under a running server when
        # somebody publishes a run, and the address does not change with
        # it.
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        self.wfile.write(payload)

    def _file(self, name: str, content_type: str) -> None:
        path = STATIC / name
        if not path.exists():
            return self.send_error(404)
        payload = path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def _json(self, produce) -> None:
        try:
            payload = json.dumps(produce()).encode("utf-8")
        except ValueError as error:
            return self._fail(str(error))
        except Exception as error:  # noqa: BLE001
            # A viewer that dies on one bad slider is worse than one that
            # says what went wrong and keeps the page alive.
            return self._fail("{}: {}".format(type(error).__name__, error))
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def _fail(self, message: str) -> None:
        payload = json.dumps({"error": message}).encode("utf-8")
        self.send_response(400)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)


# --- The same engine without a socket -------------------------------------
#
# The published site is a folder of files, and a folder cannot run a
# link budget. So the visitor's browser runs this package itself, in
# Python compiled to WebAssembly, and asks it questions through the
# function below instead of over HTTP (ADR-0080). It is the handler
# above, word for word: only where the bytes go is different, so the
# simulator on the site and the one on a laptop cannot answer the same
# question two ways.


class _Captured(Handler):
    """The request handler, writing its answer into memory."""

    def __init__(self, path: str, body: bytes) -> None:  # noqa: D107
        # No socket and no server, so none of the base class's setup.
        self.path = path
        self.headers = {"Content-Length": str(len(body))}
        self.rfile = io.BytesIO(body)
        self.wfile = io.BytesIO()
        self.status = 200
        self.sent: dict = {}

    def send_response(self, code, message=None) -> None:
        self.status = int(code)

    def send_header(self, keyword, value) -> None:
        self.sent[keyword] = value

    def end_headers(self) -> None:
        return

    def send_error(self, code, message=None, explain=None) -> None:
        self.status = int(code)
        self.sent["Content-Type"] = "application/json; charset=utf-8"
        self.wfile.write(json.dumps(
            {"error": message or "nothing at {}".format(self.path)}
        ).encode("utf-8"))


def answer(method: str, path: str, body: str = "") -> str:
    """One request, answered as the server would, as a JSON triple.

    ``[status, content type, text]``. Text rather than bytes because
    everything the simulator asks for is JSON or TOML, and a string
    crosses from Python to JavaScript without a copy anybody has to
    manage. The one binary answer, the aerial photograph, is not shipped
    to the browser, and asking for it is an ordinary 404.
    """
    handler = _Captured(path, body.encode("utf-8"))
    if method.upper() == "POST":
        handler.do_POST()
    else:
        handler.do_GET()
    payload = handler.wfile.getvalue()
    kind = handler.sent.get("Content-Type", "application/octet-stream")
    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError:
        return json.dumps([404, "application/json; charset=utf-8",
                           json.dumps({"error": "binary answer"})])
    return json.dumps([handler.status, kind, text])


def serve(
    host: str = "127.0.0.1",
    port: int = 8765,
    open_browser: bool = True,
    state: Optional[ViewState] = None,
    map_tiles: Optional[str] = None,
    presets: Optional[str] = None,
) -> None:
    """Run until interrupted.

    Bound to the loopback address on purpose. This serves a live engine
    that will run a simulation for anybody who asks, and nothing about it
    is written to be exposed.
    """
    Handler.session = Session(state)
    # None means "whatever the engine ships with"; an empty string is a
    # deliberate no map, which is a different thing and has to survive.
    if map_tiles is not None:
        MAP_TILES[0] = map_tiles
    if presets is not None:
        PRESETS[0] = PresetStore(presets)
    server = ThreadingHTTPServer((host, port), Handler)
    address = "http://{}:{}/".format(host, port)
    print("YERKON on {}".format(address))
    print("The simulator is at {}{}".format(address.rstrip("/"), SIMULATOR))
    print("Ctrl-C to stop.")
    if open_browser:
        threading.Timer(0.5, webbrowser.open, args=(address,)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
    finally:
        server.server_close()
