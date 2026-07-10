# Bible Commentary Comparison

Compare three public-domain Bible commentaries — Matthew Henry, Gill's Exposition, and
Calvin's Commentaries — side by side for any verse, with local AI Q&A grounded strictly
in the loaded commentary text.

Commentary text is fetched from [BibleHub.com](https://biblehub.com). Q&A uses
[Ollama](https://ollama.com) running locally — no cloud API, no keys.

## How to run

There are three ways to run the app, from easiest to most hands-on.

### Option 1 — Download the app (Windows, no install)

1. Go to the [latest release](https://github.com/joshuaaraj/bible-commentaries/releases/latest)
   and download `BibleCommentaries.exe`.
2. Double-click it. Windows SmartScreen may warn about an unrecognized app the first
   time — click **More info → Run anyway** (the exe is unsigned, not malicious).
3. The app opens in its own window. Pick a book, chapter, and verse, then click
   **Compare**.

Requires Windows 10/11 (the WebView2 runtime it uses is preinstalled there).

### Option 2 — Run from source in your browser (Linux/Windows/macOS)

Needs only Python 3.8+ — no packages to install; the server uses the standard library.

```bash
git clone https://github.com/joshuaaraj/bible-commentaries.git
cd bible-commentaries
python3 proxy.py
```

You'll see:

```
Bible commentary proxy running.
Open http://localhost:8765 in your browser.
```

Open that address in any browser. Stop the server with `Ctrl+C`.

### Option 3 — Run from source in a native window

Same as Option 2 but opens a desktop window instead of a browser tab:

```bash
pip install -r requirements.txt     # installs pywebview
python3 main.py
```

On Linux this needs WebKitGTK, which most desktop distros already have. If the window
fails to open: `sudo apt install python3-gi gir1.2-webkit2-4.1`

### Enable the Q&A feature (optional, all options)

Comparing commentaries works out of the box. The **"Ask the Commentaries"** panel — which
answers questions strictly from the loaded commentary text using a local AI — additionally
needs [Ollama](https://ollama.com):

1. Install Ollama from [ollama.com/download](https://ollama.com/download)
   (Linux one-liner: `curl -fsSL https://ollama.com/install.sh | sh`)
2. Pull the model (~2 GB download, needs ~4 GB free RAM to run):
   ```bash
   ollama pull llama3.2
   ```
3. Make sure Ollama is running (`ollama serve` — usually it's already running as a
   service after install; if you see "address already in use", it is).
4. Reload the app. The Q&A panel detects Ollama automatically — no configuration needed.

Without Ollama the Q&A panel simply shows install instructions; everything else works.

### Using the app

1. Pick a **book**, **chapter**, and **verse** → click **Compare**. The three columns load
   Matthew Henry, Gill, and Calvin for that verse. Use **← Prev / Next →** to step
   through verses.
2. Ask a question in the panel below (e.g. *"What are the main points of Gill's
   commentary?"*, *"Simplify Calvin's commentary to modern English"*). Answers come only
   from the loaded text — the current verse is what's used as context, shown as
   `Context: <verse>` above the answer area.
3. Every question and answer is logged to `logs/queries.jsonl`.

### Troubleshooting

| Symptom | Fix |
|---------|-----|
| "Could not reach the proxy server" | Start it: `python3 proxy.py` (Options 2/3) |
| Q&A panel says Ollama is not installed | Install Ollama and pull the model (see above) |
| Q&A answers time out | The model needs ~4 GB free RAM — close other apps, or use a smaller model (`ollama pull llama3.2:1b` + set `OLLAMA_MODEL = "llama3.2:1b"` in `proxy.py`) |
| Port 8765 already in use | Change `PORT` at the top of `proxy.py` |
| A commentary column shows "No commentary found" | That commentator may not cover this verse (e.g. Calvin didn't write on Revelation) — the other columns still work |

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
