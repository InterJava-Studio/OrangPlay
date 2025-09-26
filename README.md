# OrangPlay • Orange Music Player

A lightweight, cross-platform music player written in Python. OrangPlay aims to be simple, fast, and friendly-no bloat, just your music.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](#license)
[![Built with Python](https://img.shields.io/badge/python-3.10%2B-informational)](#-requirements)
[![Release](https://img.shields.io/github/v/release/InterJava-Studio/OrangPlay)](https://github.com/InterJava-Studio/OrangPlay/releases)

> Latest release: **v1.0** (2025-09-24). See **Releases** for downloads.  
> License: **MIT**.

---

## ✨ Features

- Local audio playback using a proven media backend (VLC) for broad codec support;  
- Minimal, responsive UI;  
- Basic playlist / queue management;  
- Keyboard shortcuts for quick control;  
- Cross-platform: Windows, Linux, macOS.


---

## 🖼️ Screens & Branding

<img alt="OrangPlay icon" src="./orange.png" width="96" />


---

## 🧩 Tech Stack

- **Python** (app logic)  
- **Qt** UI (via PyQt5 / PySide6)  
- **VLC** backend (via `python-vlc`)  
- **CSS** for styling (`style.css`)

> If you’re using PySide6 instead of PyQt5, adjust the install commands below.

---

## 🔧 Requirements

- Python **3.10+**
- VLC runtime installed (so the `libvlc` library is available on your system)
- The following Python packages:
  - `python-vlc`
  - `PyQt5` *(or `PySide6`, depending on your code)*
  - *(Optional)* `mutagen` for metadata, if used

---

## 🚀 Quick Start (from source)

```bash
# 1) Clone
git clone https://github.com/InterJava-Studio/OrangPlay.git
cd OrangPlay

# 2) Create & activate a virtual environment
python -m venv .venv
# Windows
. .venv/Scripts/activate
# macOS/Linux
source .venv/bin/activate

# 3) Install deps
pip install python-vlc PyQt5  # or PySide6 if the code uses it
# (Add other deps you use, e.g. mutagen)

# 4) Run
python orangplayer.py
````

If VLC is not found:

* **Windows**: install VLC and ensure it’s in PATH, or copy `libvlc.dll` near the app.
* **macOS**: install VLC (`brew install --cask vlc`).
* **Linux**: `sudo apt install vlc` (Debian/Ubuntu) or your distro equivalent.

---

## 📦 Download a Release

Grab the latest binaries (if provided) from **Releases**:
[https://github.com/InterJava-Studio/OrangPlay/releases](https://github.com/InterJava-Studio/OrangPlay/releases)

---

## 🗂️ Project Structure

```
OrangPlay/
├─ orangplayer.py      # Main application
├─ style.css           # UI styling
├─ media/              # App assets/screenshots (optional)
├─ orange.png          # App icon
├─ ICON.ico            # Windows icon
├─ LICENSE             # MIT
└─ README.md
```

---

## 🛠️ Development

**Linting & formatting (optional):**

```bash
pip install ruff black
ruff check .
black .
```

**Packaging (optional):**
If you want a single-file executable:

* **Windows:** `pip install pyinstaller && pyinstaller --noconsole --onefile orangplayer.py`
* **macOS/Linux:** similar `pyinstaller` command; you may need to bundle VLC or document that users must install it.

---

## 🤝 Contributing

1. Fork the repo and create a feature branch: `git checkout -b feat/my-feature`
2. Commit changes with clear messages
3. Open a Pull Request with a short description & screenshots if UI changes

---

## 📜 License

This project is licensed under the **MIT License**. See [LICENSE](./LICENSE) for details.

