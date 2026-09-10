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

import json
import pathlib
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Optional

from yerkon.design import Design
from yerkon.proposal import propose
from yerkon.viewer.scene import design_of, figures, scene, simulate, sweep
from yerkon.viewer.state import (
    CASCADING,
    CASCADING_RUN,
    MODES,
    ViewState,
    from_scenario,
)

STATIC = pathlib.Path(__file__).parent / "static"


class Session:
    """The one state the page is looking at.

    A lock rather than a queue: the sweep takes seconds and a person can
    move a slider in that time, so two requests really do overlap. What
    they must not do is interleave a read of the state with a write to it.
    """

    def __init__(self, state: Optional[ViewState] = None) -> None:
        self.state = state or ViewState()
        self._lock = threading.Lock()

    def read(self) -> ViewState:
        with self._lock:
            return self.state

    def write(self, state: ViewState) -> ViewState:
        with self._lock:
            self.state = state
            return self.state


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
        name in CASCADING or name in ("runs", "overrides") for name in changes
    ):
        return None

    proposed = state.merged(changes)
    groups = []

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

    # Quiet: a page that redraws on every drag would otherwise bury the
    # terminal in request lines.
    def log_message(self, *args) -> None:
        return

    def do_GET(self) -> None:
        path = self.path.split("?")[0]
        if path in ("/", "/index.html"):
            return self._file("index.html", "text/html; charset=utf-8")
        if path in ("/app.js", "/draw.js"):
            return self._file(path.lstrip("/"), "text/javascript; charset=utf-8")
        if path == "/favicon.ico":
            self.send_response(204)
            self.end_headers()
            return
        if path == "/style.css":
            return self._file("style.css", "text/css; charset=utf-8")
        if path == "/api/figures":
            return self._json(lambda: figures(self.session.read()))
        if path == "/api/figures.toml":
            return self._toml(self.session.read())
        if path == "/api/scene":
            return self._json(lambda: scene(self.session.read()))
        if path == "/api/sweep":
            return self._json(lambda: sweep(self.session.read()))
        if path == "/api/simulate":
            return self._json(lambda: simulate(self.session.read()))
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
        if path == "/api/reset":
            return self._json(
                lambda: {"state": self.session.write(ViewState()).as_json()}
            )
        self.send_error(404)

    # -- the two things a POST can mean -----------------------------------

    def _propose(self, changes: dict) -> dict:
        state = self.session.read()
        # Validate before answering, so a bad field name comes back as a
        # message rather than as a panel describing nothing.
        state.merged(changes)
        found = cascades(state, changes)
        return {"cascades": found} if found else {"cascades": None}

    def _mode(self, name: str) -> dict:
        """Load one of the report's modes, discarding the current one.

        Not an edit, so it does not go through the panel: nothing is
        being changed into anything, the whole arrangement is replaced.
        """
        if name not in MODES:
            raise ValueError(
                "no mode called {!r}. Choose from: {}".format(
                    name, ", ".join(MODES)
                )
            )
        return {"state": self.session.write(from_scenario(name)).as_json()}

    def _apply(self, changes: dict) -> dict:
        state = self.session.read()
        updated = self.session.write(state.merged(changes))
        return {"state": updated.as_json()}

    # -- plumbing ----------------------------------------------------------

    def _toml(self, state: ViewState) -> None:
        """The figures as a file, so an afternoon's editing survives the tab.

        Served as a download rather than shown, because the useful thing
        to do with it is put it beside the project and pass it back with
        --assumptions.
        """
        payload = state.settings().to_toml().encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/toml; charset=utf-8")
        self.send_header(
            "Content-Disposition", 'attachment; filename="assumptions.toml"'
        )
        self.send_header("Content-Length", str(len(payload)))
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


def serve(
    host: str = "127.0.0.1",
    port: int = 8765,
    open_browser: bool = True,
    state: Optional[ViewState] = None,
) -> None:
    """Run until interrupted.

    Bound to the loopback address on purpose. This serves a live engine
    that will run a simulation for anybody who asks, and nothing about it
    is written to be exposed.
    """
    Handler.session = Session(state)
    server = ThreadingHTTPServer((host, port), Handler)
    address = "http://{}:{}/".format(host, port)
    print("YERKON viewer on {}".format(address))
    print("Ctrl-C to stop.")
    if open_browser:
        threading.Timer(0.5, webbrowser.open, args=(address,)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
    finally:
        server.server_close()
