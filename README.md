# Bible Commentary Comparison

Compare three public-domain Bible commentaries — Matthew Henry, Gill's Exposition, and
Calvin's Commentaries — side by side for any verse, with local AI Q&A grounded strictly
in the loaded commentary text.

Commentary text is fetched from [BibleHub.com](https://biblehub.com). Q&A uses
[Ollama](https://ollama.com) running locally — no cloud API, no keys.

## Run (development)

```bash
python3 proxy.py          # then open http://localhost:8765
# or, native desktop window (needs pywebview):
pip install -r requirements.txt
python3 main.py
```

Q&A requires Ollama:

```bash
ollama serve              # if not already running as a service
ollama pull llama3.2
```

The app works without Ollama — the Q&A panel shows install guidance and the
commentary comparison is unaffected.

## Build a desktop app

Install the build tools:

```bash
pip install -r requirements.txt pyinstaller
```

**Linux** (produces `dist/bible-commentaries`):

```bash
pyinstaller --onefile --windowed --name bible-commentaries \
    --add-data "index.html:." main.py
```

Target machines need WebKitGTK (standard on most desktop distros):
`sudo apt install python3-gi gir1.2-webkit2-4.1`

**Windows** (run on Windows; produces `dist\BibleCommentaries.exe`):

```cmd
pyinstaller --onefile --windowed --name BibleCommentaries ^
    --add-data "index.html;." main.py
```

Requires the WebView2 runtime (preinstalled on Windows 10/11).

PyInstaller cannot cross-compile — build each OS's binary on that OS
(or use a CI matrix with `ubuntu-latest` and `windows-latest`).

## Files

| File | Purpose |
|------|---------|
| `index.html` | The whole frontend — UI, BibleHub parsing, RAG context, Q&A panel |
| `proxy.py` | Local server: serves the page, proxies BibleHub, routes Q&A to Ollama |
| `main.py` | Desktop entry point: starts the server + opens a native window |
| `logs/queries.jsonl` | Q&A log (in dev mode; packaged app logs to the per-user data dir) |

Packaged-app log locations: `~/.local/share/bible-commentaries/logs/` (Linux),
`%LOCALAPPDATA%\bible-commentaries\logs\` (Windows).

## Configuration

Edit the constants at the top of `proxy.py`: `OLLAMA_MODEL` (default `llama3.2:latest`),
`OLLAMA_NUM_CTX`, `PORT`.
