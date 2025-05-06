## 🐍 Python 3.11 + venv + pip Setup (macOS, Linux & Windows)

Diese Anleitung zeigt dir, wie du lokal eine isolierte Entwicklungsumgebung aufsetzt – für einheitliches Linting, Testing und Packaging.

______________________________________________________________________

### 🧰 1. Voraussetzungen

- Du brauchst **Python 3.11**
- Zugriff auf das Terminal (macOS/Linux) oder PowerShell (Windows)

______________________________________________________________________

## 🍎 macOS

### ✅ Python 3.11 installieren

```bash
brew install python@3.11
```

Falls nötig, verlinken:

```bash
brew link python@3.11 --force
```

### 🛠 Virtuelle Umgebung einrichten

```bash
python3.11 -m venv .venv
source .venv/bin/activate
```

### 📦 pip & tools aktualisieren

```bash
python -m pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```

______________________________________________________________________

## 🐧 Linux (Ubuntu/Debian)

### ✅ Python 3.11 installieren

```bash
sudo apt update
sudo apt install python3.11 python3.11-venv python3.11-dev
```

### 🛠 Virtuelle Umgebung einrichten

```bash
python3.11 -m venv .venv
source .venv/bin/activate
```

### 📦 pip & tools aktualisieren

```bash
python -m pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```

______________________________________________________________________

## 🪟 Windows

### ✅ Python 3.11 installieren

1. Lade Python 3.11 von [python.org](https://www.python.org/downloads/release/python-3110/)
1. Beim Installieren: **„Add Python to PATH“ aktivieren**
1. Installiere mit allen optionalen Features (inkl. `pip`)

### 🛠 Virtuelle Umgebung einrichten

```powershell
python -m venv .venv
.\.venv\Scripts\activate
```

### 📦 pip & tools aktualisieren

```powershell
python -m pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```
