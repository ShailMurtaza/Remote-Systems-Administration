# Remote Systems Administration

**Remote Systems Administration** is a Python learning project for studying how remote administration works over a network. It is built around sockets and demonstrates client–server communication, multi-client handling, message framing, encrypted traffic, and a small web control panel on top of it all.

> **Educational use only.** Run this only on machines and networks you own or have explicit permission to administer. Unauthorized access to systems is illegal.

Created by **Shail Murtaza**. Current version: **Remote Systems Administration GUI 5.2**.

---

## Project layout

Everything lives at the repository root — one web-based build, encrypted end to end:

```
main.py        # Bottle web app: socket listener, protocol, routes, payload generator
views/         # Bottle templates (home, clients, shell, file manager, screen share, ...)
static/        # CSS, JS, images, generated screen-share page
files/         # Runtime resources: server address, Fernet key, client template
clients/       # Output folder for generated client scripts
```

- **`files/server.txt`** — `host:port` the control panel binds to (e.g. `:80`)
- **`files/ENCRYPTION.KEY`** — Fernet key, auto-generated on first run
- **`files/client.py`** — template used when generating a client for a chosen host/port
- **`clients/zcreate_exe.py`** — optional helper that wraps a generated script with PyInstaller

---

## Core ideas

- **Python sockets** for reverse connections from client to server
- **Fernet encryption** on every message in transit (key stored in `files/ENCRYPTION.KEY`)
- **`recvall()` / `sendall()`** helpers so transfers are not limited by a single `recv()` call — a 10-byte length header frames each message, so large payloads (screenshots, zips) work
- **Multi-client management** — list, select (`use`), and disconnect clients by index
- **Client generation** — create a client script aimed at a chosen host and port, optionally self-encrypted

---

## Features

### Connection & session control

- Start a listener on a host/port
- List connected clients and select one by index
- Disconnect a client
- Generate client scripts (self-encrypted with their own Fernet key)

### Remote shell

- Interactive command execution on the selected client (cross-platform reverse shell)
- `server` prefix runs a command locally on the control panel instead

### File transfer & file manager

- Upload / download individual files
- Upload / download directories (zipped)
- Browser file manager with drive listing, directory changes, and browse/upload/download

### Screen & capture

- Take screenshots from the client
- Live screen share (screenshot stream written to `static/screen.html` and refreshed in the browser)

### System utilities (“Extra”)

- Shutdown / restart / log off (with optional delay)
- Task list and process kill
- Run as administrator (Windows)
- Dump saved Wi‑Fi credentials (Windows, for learning how local credential storage works)
- Attach client to Windows Startup (persistence demo)

---

## GUI modules (browser)

When a client is selected, the web UI exposes:

| Module | Purpose |
| --- | --- |
| **Home** | Start listener / generate client |
| **Clients** | View and manage connections |
| **CMD** | Remote shell |
| **Screenshot** | Capture and view screenshots |
| **Attach Startup** | Windows Startup persistence demo |
| **File Manager** | Browse, upload, and download files |
| **Screen Share** | Live screen view |
| **Extra** | Power controls, tasks, Wi‑Fi dump, elevation |

---

## Getting started

```bash
pip install bottle cryptography waitress win10toast pyautogui
python main.py
```

Then open the URL printed in the console (`http://host:port`, from `files/server.txt`).

> The control panel uses a few Windows-only conveniences (`title`, `shutdown`, `netsh`, toast notifications), so the full feature set is Windows-targeted; the socket protocol itself is cross-platform.

---

## Tech stack

### Language & runtime

| Technology | Role |
| --- | --- |
| **Python** | Main language for server, client, protocol, and GUI backend |
| **Python `socket`** | TCP client–server transport (reverse connections) |
| **`threading`** | Background listener thread so the web UI stays responsive while accepting clients |
| **`subprocess`** | Runs shell commands on the remote client |
| **`shutil`** | Directory zip/archive for folder upload/download; file copy for startup attach |
| **`marshal`** | Serialize/compile client payload code; used for the file-manager directory listing |
| **`ctypes`** | Windows API helpers (e.g. elevation / admin-related demos) |
| **`os` / `sys` / `time` / `datetime`** | Paths, process control, delays, and timestamps |

### Third-party Python libraries

| Library | Role |
| --- | --- |
| **[Bottle](https://bottlepy.org/)** | Lightweight WSGI web framework for the control panel (routes, templates, forms, static files) |
| **[cryptography](https://cryptography.io/)** (`Fernet`) | Symmetric encryption for traffic in transit and for self-encrypted generated clients |
| **[waitress](https://docs.pylons.org/waitress/)** | Production WSGI server hosting the Bottle app |
| **[PyAutoGUI](https://pyautogui.readthedocs.io/)** | Client-side screenshots (`screenshot`) used for capture and screen share |
| **[win10toast](https://github.com/jithurjacob/Windows-10-Toast-Notifications)** | Windows desktop toast notifications when a client connects |
| **[PyInstaller](https://www.pyinstaller.org/)** | Optional packaging of generated scripts into a standalone `.exe` (`clients/zcreate_exe.py`) |

### GUI front end

| Technology | Role |
| --- | --- |
| **HTML** | Bottle templates for Home, Clients, Shell, File Manager, Screenshot, Screen Share, Extra |
| **CSS** | Custom styles (`main.css`, `navbar.css`, `tooltip.css`) plus **W3.CSS** for layout/components |
| **JavaScript** | Small UI helpers (e.g. message dismiss, table toggles, delete checks) |

### Architecture summary

```
Browser (HTML/CSS/JS)
        │  HTTP
        ▼
Bottle web app (main.py)
        │  Python sockets + Fernet (length-prefixed frames)
        ▼
Generated client (socket + PyAutoGUI + subprocess + OS APIs)
```

---

## Learning goals

This repo is useful for practicing:

1. Socket programming and framing (headers + streaming)
2. Multi-client reverse-connection architecture
3. Building a small web front end over a socket backend
4. Encrypting traffic in transit with Fernet, and why plaintext protocols are easier to study
5. How remote-admin features map to OS APIs (shell, files, screen, power)

---


