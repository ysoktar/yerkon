"""How a fetch asks a server for something, wherever it runs (ADR-0086).

`requests` where it is installed, and the standard library's `urllib`
where it is not, so a plain install fetches too (ADR-0087). In the
published site the simulator
runs as Python compiled to WebAssembly inside a browser worker
(ADR-0080), which has no sockets and no `requests`; there the browser's
own request does the asking. A worker may wait for an answer
synchronously, so a fetcher written as a plain loop of requests runs
unchanged in both places.

Only what the fetchers use is here: a status, the bytes, a few headers
and JSON. Everything else about `requests` stays where it was.
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass, field
from typing import Optional
from urllib.parse import urlencode

#: True inside the published site's worker.
IN_A_BROWSER = sys.platform == "emscripten"

DEFAULT_TIMEOUT_S = 30.0


class Failed(RuntimeError):
    """A request that did not come back, or came back refused."""


@dataclass
class Reply:
    """What came back, shaped like the parts of a `requests` response the
    fetchers read."""

    status_code: int
    content: bytes = b""
    headers: dict = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        return 200 <= self.status_code < 400

    def json(self):
        return json.loads(self.content.decode("utf-8"))

    def raise_for_status(self) -> None:
        if not self.ok:
            raise Failed("the server answered {}".format(self.status_code))


#: Sent where the transport lets a script name itself. Overpass and most
#: tile servers refuse an unnamed client.
USER_AGENT = "yerkon/1.0 (terrestrial positioning study)"


def can_ask() -> bool:
    """Whether this install can reach a server at all. Always, now that
    the standard library is the fallback; kept so callers read as they
    did."""
    return True


def get(url: str, params: Optional[dict] = None,
        timeout: float = DEFAULT_TIMEOUT_S,
        headers: Optional[dict] = None) -> Reply:
    if params:
        url = "{}{}{}".format(url, "&" if "?" in url else "?", urlencode(params))
    return _ask("GET", url, None, timeout, headers)


def head(url: str, timeout: float = DEFAULT_TIMEOUT_S) -> Reply:
    """The headers alone: a file's size, before reading parts of it."""
    return _ask("HEAD", url, None, timeout)


def post_form(url: str, data: dict, timeout: float = DEFAULT_TIMEOUT_S) -> Reply:
    return _ask("POST", url, data, timeout)


def header(reply: Reply, name: str) -> Optional[str]:
    """One header of a reply, whatever case the server wrote it in."""
    wanted = name.lower()
    for key, value in reply.headers.items():
        if key.lower() == wanted:
            return value
    return None


def _ask(method: str, url: str, form: Optional[dict], timeout: float,
         headers: Optional[dict] = None) -> Reply:
    if IN_A_BROWSER:
        return _in_the_browser(
            method, url, None if form is None else urlencode(form), timeout,
            headers)
    try:
        import requests
    except ImportError:
        return _with_urllib(method, url, form, timeout, headers)

    extra = {"headers": headers} if headers else {}
    try:
        if method == "POST":
            answer = requests.post(url, data=form, timeout=timeout, **extra)
        elif method == "HEAD":
            answer = requests.head(url, timeout=timeout, **extra)
        else:
            answer = requests.get(url, timeout=timeout, **extra)
    except Exception as error:  # noqa: BLE001 — every transport failure is one
        raise Failed(_cause(error)) from error
    return Reply(answer.status_code, answer.content, dict(answer.headers))


def _with_urllib(method: str, url: str, form: Optional[dict],
                 timeout: float, headers: Optional[dict] = None) -> Reply:
    """The standard library's request, for an install without `requests`."""
    import urllib.error
    import urllib.request

    body = None if form is None else urlencode(form).encode("utf-8")
    request = urllib.request.Request(
        url, data=body, method=method,
        headers=dict({"User-Agent": USER_AGENT}, **(headers or {})))
    try:
        with urllib.request.urlopen(request, timeout=timeout) as answer:
            return Reply(answer.status, answer.read(), dict(answer.headers))
    except urllib.error.HTTPError as refused:
        return Reply(refused.code, refused.read() or b"", dict(refused.headers))
    except Exception as error:  # noqa: BLE001 — every transport failure is one
        raise Failed(_cause(error)) from error


#: Seconds waited before each further try of a request the browser
#: dropped. A phone drops every open request when its owner switches to
#: another app and freezes the page until they come back; the request
#: then fails the moment the page wakes, and asked again it goes through.
BROWSER_RETRY_WAITS_S = (1.0, 3.0, 8.0)


def _in_the_browser(method: str, url: str, form: Optional[str],
                    timeout: float, headers: Optional[dict] = None) -> Reply:
    """The worker's own request, tried again while the browser drops it.

    Only a request that never came back is tried again: a server's own
    refusal is an answer, and the fetchers decide what to do with it.
    """
    import time

    for wait in BROWSER_RETRY_WAITS_S + (None,):
        try:
            reply = _once_in_the_browser(method, url, form, timeout, headers)
        except Failed:
            if wait is None:
                raise
        else:
            # Status 0 is the browser's word for no answer at all.
            if reply.status_code != 0 or wait is None:
                return reply
        # Counted out rather than slept: this runtime's sleep does not
        # reliably wait, and the worker has nothing else to do meanwhile.
        until = time.monotonic() + wait
        while time.monotonic() < until:
            pass
    raise AssertionError("unreachable")


def _once_in_the_browser(method: str, url: str, form: Optional[str],
                         timeout: float, headers: Optional[dict] = None) -> Reply:
    """The worker's own request, waited for.

    Synchronous, which a page may not do and a worker may. The browser
    sets its own User-Agent and refuses to let a script change it, so
    none is sent; the tile servers this reaches accept a browser as it
    is.
    """
    from js import XMLHttpRequest  # type: ignore[import-not-found]

    request = XMLHttpRequest.new()
    request.open(method, url, False)
    request.responseType = "arraybuffer"
    request.timeout = int(timeout * 1000)
    if form is not None:
        request.setRequestHeader(
            "Content-Type", "application/x-www-form-urlencoded")
    for name, value in (headers or {}).items():
        request.setRequestHeader(name, value)
    try:
        request.send(form)
    except Exception as error:  # noqa: BLE001 — a JavaScript NetworkError
        raise Failed(_cause(error)) from error
    body = request.response
    if body is None:
        content = b""
    elif hasattr(body, "to_bytes"):
        # An ArrayBuffer comes over as a buffer proxy that copies itself
        # out; older Pyodide only offers the memoryview.
        content = bytes(body.to_bytes())
    else:
        content = bytes(body.to_py())
    # Only the headers a page may read across origins come back, and
    # only these are wanted: when to try again, and how big a file is.
    kept = {}
    for name in ("Retry-After", "Content-Length", "Content-Range"):
        value = request.getResponseHeader(name)
        if value:
            kept[name] = str(value)
    return Reply(int(request.status), content, kept)


def _cause(error: Exception) -> str:
    """The reason, without the query a URL carried.

    `requests` puts the whole URL in its exceptions, and for an
    elevation service that is a hundred coordinates in front of the one
    word that matters.
    """
    text = str(error)
    marker = "(Caused by "
    if marker in text:
        text = text[text.index(marker) + len(marker):].rstrip(")")
    elif "url:" in text:
        text = text.split("url:")[0]
    text = " ".join(text.split())
    return text[:200] if text else type(error).__name__
