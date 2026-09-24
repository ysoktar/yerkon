"""How a fetch asks a server for something, wherever it runs (ADR-0086).

`requests` where it is installed. In the published site the simulator
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


def can_ask() -> bool:
    """Whether this install can reach a server at all."""
    if IN_A_BROWSER:
        return True
    try:
        import requests  # noqa: F401
    except ImportError:
        return False
    return True


def get(url: str, params: Optional[dict] = None,
        timeout: float = DEFAULT_TIMEOUT_S) -> Reply:
    if params:
        url = "{}{}{}".format(url, "&" if "?" in url else "?", urlencode(params))
    return _ask("GET", url, None, timeout)


def post_form(url: str, data: dict, timeout: float = DEFAULT_TIMEOUT_S) -> Reply:
    return _ask("POST", url, data, timeout)


def _ask(method: str, url: str, form: Optional[dict], timeout: float) -> Reply:
    if IN_A_BROWSER:
        return _in_the_browser(
            method, url, None if form is None else urlencode(form), timeout)
    import requests

    try:
        if method == "POST":
            answer = requests.post(url, data=form, timeout=timeout)
        else:
            answer = requests.get(url, timeout=timeout)
    except Exception as error:  # noqa: BLE001 — every transport failure is one
        raise Failed(_cause(error)) from error
    return Reply(answer.status_code, answer.content, dict(answer.headers))


def _in_the_browser(method: str, url: str, form: Optional[str],
                    timeout: float) -> Reply:
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
    headers = {}
    retry = request.getResponseHeader("Retry-After")
    if retry:
        headers["Retry-After"] = str(retry)
    return Reply(int(request.status), content, headers)


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
