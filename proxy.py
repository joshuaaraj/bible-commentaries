#!/usr/bin/env python3
"""
Local proxy server for the Bible Commentary Comparison page.
Run:  python3 proxy.py
Then: open http://localhost:8765 in your browser

Requires Ollama running locally for the Q&A feature:
  ollama serve
  ollama pull llama3.2
"""
import os
import sys
import json
import datetime
import pathlib
import urllib.request
import urllib.parse
import urllib.error
from http.server import HTTPServer, BaseHTTPRequestHandler

PORT         = 8765
ALLOWED_HOST = "biblehub.com"
OLLAMA_BASE  = "http://localhost:11434"
OLLAMA_URL   = OLLAMA_BASE + "/api/chat"
OLLAMA_MODEL = "llama3.2:latest"  # change to any model you have pulled in Ollama
OLLAMA_NUM_CTX = 8192      # context window; Ollama's default of 2048 silently drops text
MAX_CONTEXT_CHARS = 24000  # safety cap so the prompt always fits in OLLAMA_NUM_CTX


def resource_path(name):
    """Bundled read-only files (index.html). PyInstaller unpacks to sys._MEIPASS."""
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, name)


def data_dir():
    """Writable per-user data dir when frozen; script directory in dev mode."""
    if not getattr(sys, "frozen", False):
        return pathlib.Path(__file__).parent
    if sys.platform == "win32":
        root = os.environ.get("LOCALAPPDATA", os.path.expanduser("~"))
    else:
        root = os.environ.get("XDG_DATA_HOME", os.path.expanduser("~/.local/share"))
    d = pathlib.Path(root) / "bible-commentaries"
    d.mkdir(parents=True, exist_ok=True)
    return d


LOG_DIR  = data_dir() / "logs"
LOG_FILE = LOG_DIR / "queries.jsonl"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "identity",
    "Referer": "https://biblehub.com/",
}

SYSTEM_PROMPT = "You are a Bible commentary assistant. You answer questions using only the commentary text given to you."


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass  # suppress per-request logs

    # ── GET ──────────────────────────────────────────────────────────────────

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)

        if parsed.path in ("/", "/index.html"):
            self._serve_file("index.html", "text/html; charset=utf-8")

        elif parsed.path == "/status":
            self._status()

        elif parsed.path == "/fetch":
            params = urllib.parse.parse_qs(parsed.query)
            url = params.get("url", [""])[0]
            host = urllib.parse.urlparse(url).hostname or ""
            if not (url.startswith("https://") and host.endswith(ALLOWED_HOST)):
                self._error(403, "Forbidden")
                return
            self._proxy(url)

        else:
            self._error(404, "Not found")

    # ── POST ─────────────────────────────────────────────────────────────────

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length) if length else b"{}"
        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            self._error(400, "Invalid JSON")
            return

        if parsed.path == "/ask":
            self._ask(data)
        elif parsed.path == "/log":
            self._log_query(data)
            self._json(204, None)
        else:
            self._error(404, "Not found")

    # ── Handlers ─────────────────────────────────────────────────────────────

    def _serve_file(self, path, content_type):
        full = resource_path(path)
        try:
            with open(full, "rb") as f:
                data = f.read()
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
        except FileNotFoundError:
            self._error(404, f"{path} not found")

    def _status(self):
        """Report whether Ollama is reachable and which models it has."""
        try:
            with urllib.request.urlopen(OLLAMA_BASE + "/api/tags", timeout=2) as resp:
                tags = json.loads(resp.read())
            models = [m.get("name", "") for m in tags.get("models", [])]
            self._json(200, {"ollama": True, "models": models, "model": OLLAMA_MODEL})
        except Exception:
            self._json(200, {"ollama": False, "models": [], "model": OLLAMA_MODEL})

    def _proxy(self, url):
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = resp.read()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(data)
        except urllib.error.HTTPError as e:
            self._error(e.code, str(e))
        except Exception as e:
            self._error(502, str(e))

    def _ask(self, data):
        question = (data.get("question") or "").strip()
        context  = (data.get("context")  or "").strip()

        if not question:
            self._json(400, {"error": "Question is required."})
            return
        if not context:
            self._json(400, {"error": "No commentary context provided. Load a verse first."})
            return

        if len(context) > MAX_CONTEXT_CHARS:
            context = context[:MAX_CONTEXT_CHARS] + "\n[Commentary text truncated to fit the model's context window.]"

        user_message = (
            "The following is the ONLY source you may use. "
            "Do not add any information from outside this text.\n\n"
            "--- COMMENTARY START ---\n"
            f"{context}\n"
            "--- COMMENTARY END ---\n\n"
            "Rules:\n"
            "1. Use ONLY the text between the markers above. "
            "Do not add external theology, history, or personal knowledge.\n"
            "2. When asked for 'main points' or a summary: list every key theme and argument "
            "from the named commentary. Be thorough — do not skip any major idea in the text.\n"
            "3. When asked to 'simplify', 'translate', or 'rewrite': paraphrase the named "
            "commentary in clear, modern English. Keep every idea from the original — "
            "do not add or remove content.\n"
            "4. When the question names a specific commentator (Matthew Henry, Gill, or Calvin), "
            "focus only on that commentator's section and ignore the others.\n"
            "5. If the named commentator's section does not appear between the markers, "
            "reply that this commentary is not loaded for this verse. Do not answer from "
            "a different commentator instead.\n"
            "6. If the question cannot be answered from the text above, respond with exactly: "
            "\"This is not covered in the loaded commentary.\"\n\n"
            f"Question: {question}"
        )
        payload = {
            "model": OLLAMA_MODEL,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user",   "content": user_message},
            ],
            "stream": False,
            "options": {"num_ctx": OLLAMA_NUM_CTX},
        }

        try:
            req = urllib.request.Request(
                OLLAMA_URL,
                data=json.dumps(payload).encode(),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=120) as resp:
                result = json.loads(resp.read())
            answer = result["message"]["content"]
            self._json(200, {"answer": answer})
        except urllib.error.HTTPError as e:
            try:
                err_body = json.loads(e.read())
                msg = err_body.get("error", str(e))
            except Exception:
                msg = str(e)
            self._json(502, {"error": f"Ollama error: {msg}"})
        except urllib.error.URLError:
            self._json(502, {
                "error": "Ollama is not running. Start it with: ollama serve"
            })
        except KeyError:
            self._json(502, {"error": "Unexpected response format from Ollama."})
        except Exception as e:
            self._json(500, {"error": str(e)})

    def _log_query(self, data):
        try:
            record = {
                "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
                "verses":    data.get("verses", []),
                "question":  data.get("question", ""),
                "answer":    data.get("answer", ""),
                "model":     OLLAMA_MODEL,
                "context_chars": data.get("context_chars", None),
            }
            with open(LOG_FILE, "a", encoding="utf-8") as f:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
        except Exception:
            pass  # logging failures must never break the main flow

    # ── Helpers ──────────────────────────────────────────────────────────────

    def _json(self, code, obj):
        if obj is None:
            self.send_response(code)
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Content-Length", "0")
            self.end_headers()
            return
        body = json.dumps(obj, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def _error(self, code, msg):
        body = msg.encode()
        self.send_response(code)
        self.send_header("Content-Type", "text/plain")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def start_server(port=0):
    """Create the HTTP server. port=0 lets the OS pick a free port.
    Returns (server, actual_port)."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    server = HTTPServer(("127.0.0.1", port), Handler)
    return server, server.server_address[1]


if __name__ == "__main__":
    server, port = start_server(PORT)
    print(f"Bible commentary proxy running.")
    print(f"Open http://localhost:{port} in your browser.")
    print(f"Ollama model: {OLLAMA_MODEL}  (change OLLAMA_MODEL in proxy.py to switch)")
    print(f"Query log:    {LOG_FILE}")
    print("Press Ctrl+C to stop.\n")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
