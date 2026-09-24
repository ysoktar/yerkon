/* The simulator's engine, running in the visitor's browser (ADR-0080).
 *
 * The published site is a folder of files, and a folder cannot run a
 * link budget. So this worker loads Python compiled to WebAssembly
 * (Pyodide), numpy, and this project's own package, and answers the
 * page's questions with the same handler the local server uses. Nothing
 * leaves the browser; nothing runs anywhere else.
 *
 * A worker rather than the page, because a run takes seconds and the
 * page has to keep drawing while it does. A module worker, because this
 * Pyodide refuses to start in a classic one.
 */

const PYODIDE = "https://cdn.jsdelivr.net/pyodide/v314.0.7/full/";

function stage(name, detail) {
  postMessage({ stage: name, detail: detail || "" });
}

const ready = (async () => {
  stage("python");
  const { loadPyodide } = await import(PYODIDE + "pyodide.mjs");
  const pyodide = await loadPyodide({ indexURL: PYODIDE });
  stage("numpy");
  await pyodide.loadPackage("numpy");
  // A package that fails to load is logged rather than thrown, and the
  // failure would otherwise surface later as an import error that says
  // nothing about the network.
  if (!pyodide.loadedPackages.numpy) throw new Error("numpy could not be loaded");
  stage("package");
  const response = await fetch("yerkon.zip");
  if (!response.ok) throw new Error("yerkon.zip: " + response.status);
  pyodide.unpackArchive(await response.arrayBuffer(), "zip",
                        { extractDir: "/home/pyodide/lib" });
  pyodide.runPython("import sys; sys.path.insert(0, '/home/pyodide/lib')");
  const answer = pyodide.runPython(
    "from yerkon.viewer.server import answer; answer");
  stage("ready");
  return { answer, pyodide };
})();

/* Pillow, loaded the first time somebody fetches ground (ADR-0086).
 *
 * A fetch decodes terrain tiles and photographs, and nothing else here
 * needs an image library, so a visitor who never fetches never waits
 * for it.
 */
let pillow = null;
function withPillow() {
  if (!pillow) pillow = ready.then(({ pyodide }) => pyodide.loadPackage("pillow"));
  return pillow;
}

function isAFetch(path, body) {
  if (!path.startsWith("/api/run")) return false;
  try { return JSON.parse(body || "{}").kind === "fetch"; } catch { return false; }
}

ready.catch(error => stage("failed", String(error && error.message || error)));

// Set before anything is awaited, so a question the page asks while
// Python is still loading waits for it instead of being lost.
onmessage = async event => {
  const { id, method, path, body } = event.data;
  let status = 500;
  let type = "application/json; charset=utf-8";
  let text;
  let encoding = "";
  try {
    const { answer } = await ready;
    if (isAFetch(path, body)) await withPillow();
    [status, type, text, encoding = ""] = JSON.parse(answer(method, path, body || ""));
  } catch (error) {
    text = JSON.stringify({ error: String(error && error.message || error) });
  }
  postMessage({ id, status, type, text, encoding });
};
