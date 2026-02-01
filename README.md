<div align="center">

# 🗓️ EseményLekérő
### WordPress REST API → Live GUI → Excel Export (Windows)

<a href="#"><img src="https://img.shields.io/badge/Python-3.12+-3776AB?style=for-the-badge&logo=python&logoColor=white" /></a>
<a href="#"><img src="https://img.shields.io/badge/GUI-PySide6%20(Qt)-41CD52?style=for-the-badge&logo=qt&logoColor=white" /></a>
<a href="#"><img src="https://img.shields.io/badge/Build-Nuitka-111827?style=for-the-badge&logo=windows&logoColor=white" /></a>
<a href="#"><img src="https://img.shields.io/badge/Export-Excel-217346?style=for-the-badge&logo=microsoft-excel&logoColor=white" /></a>

<br/>

<a href="#"><img src="https://img.shields.io/badge/Status-Working%20✅-22c55e?style=for-the-badge" /></a>
<a href="#"><img src="https://img.shields.io/badge/Platform-Windows%2010%2F11-0ea5e9?style=for-the-badge&logo=windows&logoColor=white" /></a>

<br/>
<br/>

**Egy felhasználóbarát, asztali alkalmazás**, ami a **csodalatosmagyarorszag.hu** WordPress REST API-járól **összegyűjti az eseményeket**, **cache-eli**, **szűrhető táblázatban megjeleníti**, majd **Excelbe exportálja**.

</div>

---

## ✨ Demo / UX (miért “látszik”, hogy dolgozik?)
- 🔄 **Spinner + progress** (pl. `32/125`) betöltés közben  
- 📥 **Oldalankénti betöltés**: a táblázat **folyamatosan töltődik**, nem “áll” a program  
- 🧠 **Cache**: következő indításkor gyorsabb, akár offline is  
- 🧾 **Export**: **csak a szűrt** találatok mennek Excelbe  

---

## ✅ Fő funkciók
- 🌐 WordPress REST API lekérés **lapozással** (`X-WP-TotalPages`)
- 🏷️ Kategóriák feloldása **ID → név**
- ♻️ Lokális cache (JSON)
- 🧵 Háttérszálas letöltés (UI nem fagy)
- 🔎 Szűrés:
  - 📅 dátumtartomány
  - 🧩 kategória (multi-select)
  - 🔤 keresés (cím / helyszín)
- 📊 Excel export (openpyxl)

---

## 🧰 Tech stack
- **Python 3.12+**
- **PySide6 (Qt)** – GUI + QThread
- **requests** – HTTP
- **pandas** – adatfeldolgozás
- **openpyxl** – Excel írás
- **Nuitka** – Windows exe build

---

## 📦 Telepítés (fejlesztői futtatás)

```bash
pip install pyside6 requests pandas openpyxl
python app.py
