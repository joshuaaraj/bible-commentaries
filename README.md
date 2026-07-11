# Bible Commentary Comparison

Compare three public-domain Bible commentaries — Matthew Henry, Gill's Exposition, and
Calvin's Commentaries — side by side for any verse, with local AI Q&A grounded strictly
in the loaded commentary text.

Commentary text is fetched from [BibleHub.com](https://biblehub.com). Q&A uses
[Ollama](https://ollama.com) running locally — no cloud API, no keys.

## Features

**Commentary comparison**
- Three commentaries side by side for any verse: Matthew Henry (1706–1714),
  Gill's Exposition (1746–1766), Calvin's Commentaries (1540s–1560s)
- All 66 books — pick a book, chapter, and verse, or step through with **← Prev / Next →**
- Handles each source's quirks automatically: verse groupings (e.g. Matthew Henry on
  Genesis 1:6–13), and Calvin's chapter-level commentary sliced to the section covering
  your verse
- Direct link to the verse on BibleHub for the full page

**Ask the Commentaries (AI Q&A)**
- Ask questions in plain English about the verse on screen — e.g. *"What are the main
  points of Gill's commentary?"*, *"Simplify Calvin's commentary to modern English"*,
  *"What does Matthew Henry say about creation?"*
- Answers come **only** from the loaded commentary text — the model cites which
  commentator says what, and replies *"This is not covered in the loaded commentary"*
  rather than inventing an answer
- Summarize, simplify, translate to modern English, or ask direct questions —
  scoped to a single named commentator or all three
- The context is always the currently displayed verse (shown as `Context: <verse>`);
  switching verses adds a separator in the chat history
- Runs entirely on your machine via Ollama — questions never leave your computer
- Every question and answer is logged to `logs/queries.jsonl` for later review

**App**
- Runs three ways: standalone desktop app (Windows/Linux, no install), native window
  from source, or plain browser tab — same features in all three
- No accounts, no API keys, no cloud services
- Works without Ollama: comparison is fully functional, and the Q&A panel shows
  setup instructions until Ollama is detected (checked automatically)

## How to run

There are three ways to run the app, from easiest to most hands-on.

### Option 1 — Download the app (no install)

Go to the [latest release](https://github.com/joshuaaraj/bible-commentaries/releases/latest) and download the file for your OS:

**Windows** — `BibleCommentaries.exe`
1. Double-click it. Windows SmartScreen may warn about an unrecognized app the first
   time — click **More info → Run anyway** (the exe is unsigned, not malicious).
2. Requires Windows 10/11 (the WebView2 runtime it uses is preinstalled there).

**Linux** — `bible-commentaries-linux`
```bash
chmod +x bible-commentaries-linux
./bible-commentaries-linux
```
Needs WebKitGTK, which most desktop distros already have
(`sudo apt install python3-gi gir1.2-webkit2-4.1` if not).

The app opens in its own window. Pick a book, chapter, and verse, then click **Compare**.

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
needs [Ollama](https://ollama.com), a free tool that runs AI models on your own machine.

#### Install Ollama on Windows

1. Download the installer from
   [ollama.com/download/windows](https://ollama.com/download/windows)
   (direct link: [OllamaSetup.exe](https://ollama.com/download/OllamaSetup.exe)).
2. Run `OllamaSetup.exe` and click through the installer — no options to configure.
3. Ollama starts automatically after install and on every boot (look for the llama icon
   in the system tray).
4. Open **Command Prompt** (press `Win+R`, type `cmd`, press Enter) and pull the model
   (~2 GB download, needs ~4 GB free RAM to run):
   ```cmd
   ollama pull llama3.2
   ```

#### Install Ollama on Linux

1. Run the official install script:
   ```bash
   curl -fsSL https://ollama.com/install.sh | sh
   ```
   (On most distros this also registers Ollama as a systemd service that starts on boot.)
2. Check it's running:
   ```bash
   ollama --version        # should print a version, not an error
   ```
   If it isn't running, start it with `ollama serve` (an "address already in use" error
   here actually means it *is* already running — you're done).
3. Pull the model (~2 GB download, needs ~4 GB free RAM to run):
   ```bash
   ollama pull llama3.2
   ```

#### Connect it to the app

Nothing to configure — reload the app and the Q&A panel detects Ollama automatically.
Until then, the panel just shows these install instructions; commentary comparison
works fine without it.

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
