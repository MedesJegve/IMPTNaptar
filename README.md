# 🗓️ EseményLekérő
## Python WordPress REST API Desktop GUI Example with PySide6 and Excel Export

A real-world Python desktop application that fetches event data from a WordPress REST API, displays it in a live Qt GUI, allows filtering, and exports the results to Excel — all built into a native Windows executable.

---

## 🚀 What this project demonstrates

This repository is not a toy script. It is a complete desktop software pipeline:

- Python WordPress REST API integration
- Handling paginated API responses (`X-WP-TotalPages`)
- Background thread loading in a Qt GUI using QThread
- Live table updates during network operations
- Local JSON cache strategy for offline usage
- Data processing with pandas
- Excel export with openpyxl
- Building a native Windows executable from Python using Nuitka

---

## 🔍 Keywords people search for

This project intentionally covers topics people often search for:

- python wordpress rest api example
- pyside6 tableview background thread
- python desktop gui rest api
- export api data to excel python
- qt python progress bar loading data
- pandas filter table before excel export
- nuitka build windows exe python

If you searched for any of these — you are in the right place.

---

## ✨ Features

- 🔄 Spinner + progress indicator while loading (`32/125 pages`)
- 📥 Table fills continuously while data is downloading
- 🧠 Smart local cache (fast startup, works offline)
- 🔎 Filter by date and category
- 📊 Export only filtered results to Excel
- 🪟 Native Windows EXE build

---

## 🧰 Tech Stack

| Technology | Purpose |
|------------|---------|
| Python 3.12+ | Core language |
| PySide6 (Qt) | Desktop GUI |
| requests | REST API communication |
| pandas | Data processing |
| openpyxl | Excel export |
| Nuitka | Native Windows executable build |

---

## ▶️ Run in development mode

```bash
pip install pyside6 requests pandas openpyxl
python app.py
```

---

## 🏗️ Build Windows EXE with Nuitka

```powershell
py -3.12 -m pip install -U pip nuitka pyside6 requests pandas openpyxl ordered-set zstandard
py -3.12 -m nuitka --onefile --windows-disable-console --enable-plugin=pyside6 --include-qt-plugins=sensible,platforms --include-package=pandas --include-package-data=pandas --include-package=pandas._libs --include-package=openpyxl --include-package-data=openpyxl --output-filename=EsemenyLekero.exe app.py
```

---

## 🗂️ Cache

The application creates a `cache/` folder during runtime to store downloaded data locally for faster subsequent startup and offline use.

---

## 📁 Recommended .gitignore

```
cache/
cache/*.json
*.xlsx
build/
dist/
*.exe
__pycache__/
venv/
.vscode/
.idea/
```

---

## 🧠 Why this is portfolio-worthy

This project shows practical knowledge of:

- REST API consumption
- Qt GUI development
- Multithreading in desktop applications
- Data processing pipelines
- Packaging Python applications as native software

---

## 🪪 License

This project is licensed under the **Mozilla Public License 2.0**.  
See the `LICENSE` file for details.

---

## 👤 Author

**Dániel Dávid**
