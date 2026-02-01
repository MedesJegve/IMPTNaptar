<div align="center">

# 🗓️ EseményLekérő
### WordPress REST API → Live GUI → Excel Export (Windows)

<a href="#"><img src="https://img.shields.io/badge/Python-3.12+-3776AB?style=for-the-badge&logo=python&logoColor=white" /></a>
<a href="#"><img src="https://img.shields.io/badge/GUI-PySide6%20(Qt)-41CD52?style=for-the-badge&logo=qt&logoColor=white" /></a>
<a href="#"><img src="https://img.shields.io/badge/Build-Nuitka-111827?style=for-the-badge&logo=windows&logoColor=white" /></a>
<a href="#"><img src="https://img.shields.io/badge/Export-Excel-217346?style=for-the-badge&logo=microsoft-excel&logoColor=white" /></a>

<br/>
<br/>

**Egy felhasználóbarát, asztali alkalmazás**, ami a WordPress REST API-ról eseményeket gyűjt, cache-el, szűrhető táblázatban megjelenít, majd Excelbe exportál.

</div>

---

## ✨ Demo / UX

- 🔄 Spinner + progress (pl. `32/125`) betöltés közben
- 📥 Oldalankénti betöltés: a táblázat folyamatosan töltődik
- 🧠 Cache: következő indításkor gyorsabb, akár offline is
- 🧾 Export: csak a szűrt találatok mennek Excelbe

---

## ✅ Fő funkciók

- WordPress REST API lapozott lekérés (`X-WP-TotalPages`)
- Kategóriák feloldása ID → név
- Lokális cache
- Háttérszálas letöltés (QThread)
- Dátum és kategória szerinti szűrés
- Excel export

---

## 🧰 Tech stack

- Python 3.12+
- PySide6 (Qt GUI)
- requests
- pandas
- openpyxl
- Nuitka (natív Windows exe)

---

## ▶️ Futtatás fejlesztői módban

```bash
pip install pyside6 requests pandas openpyxl
python app.py
```

---

## 🏗️ Windows EXE build (Nuitka)

```powershell
py -3.12 -m pip install -U pip nuitka pyside6 requests pandas openpyxl ordered-set zstandard
py -3.12 -m nuitka --onefile --windows-disable-console --enable-plugin=pyside6 --include-qt-plugins=sensible,platforms --include-package=pandas --include-package-data=pandas --include-package=pandas._libs --include-package=openpyxl --include-package-data=openpyxl --output-filename=EsemenyLekero.exe app.py
```

---

## 🗂️ Cache

A program futás közben létrehoz egy `cache/` mappát, és ide menti a letöltött adatokat.

## 👤 Szerző

Dániel Dávid
