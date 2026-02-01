#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
GUI-s eseménygyűjtő Csodálatos Magyarországról (WordPress REST API).
- Háttérszálon tölt (nem fagy a UI)
- Oldalanként frissíti a táblát (laikusnak is látszik, hogy dolgozik)
- Felül pötty animáció + page/total (pl. 32/125)
- Lokális cache (categories + posts)
- Szűrés: dátumtartomány + kategória (multi) + kereső (cím/helyszín)
- Export: csak a szűrt táblát menti Excelbe

Futtatás:
    pip install pyside6 requests pandas openpyxl
    python app.py

EXE (Windows):
    pip install pyinstaller
    pyinstaller --noconfirm --onefile --windowed app.py
"""

import sys
import json
import time
from pathlib import Path
from datetime import datetime

import requests
import pandas as pd

from PySide6.QtCore import (
    Qt, QDate, QObject, Signal, QThread, QTimer
)
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QLineEdit, QListWidget, QListWidgetItem,
    QTableWidget, QTableWidgetItem, QFileDialog, QDateEdit, QMessageBox,
    QCheckBox
)

# REST API endpoints
API_POSTS = "https://csodalatosmagyarorszag.hu/wp-json/wp/v2/posts"
API_CATS  = "https://csodalatosmagyarorszag.hu/wp-json/wp/v2/categories"

PER_PAGE = 100
HEADERS  = {"User-Agent": "Mozilla/5.0"}

CACHE_DIR   = Path("./cache")
CACHE_CATS  = CACHE_DIR / "cache_categories.json"
CACHE_POSTS = CACHE_DIR / "cache_posts.json"


# --------------------------
# Helpers / Data fetching
# --------------------------

def safe_get(url, params, timeout=30, retries=3, sleep_s=2.0):
    """
    Timeout esetén retry-ol, egyéb HTTP hibára raise_for_status dob.
    """
    last_err = None
    for attempt in range(1, retries + 1):
        try:
            r = requests.get(url, params=params, headers=HEADERS, timeout=timeout)
            r.raise_for_status()
            return r
        except requests.exceptions.ReadTimeout as e:
            last_err = e
            if attempt == retries:
                raise
            time.sleep(sleep_s)
    raise last_err


def fetch_category_map():
    """
    Lekéri az összes kategóriát, id->név map.
    """
    cat_map = {}
    page = 1
    while True:
        r = safe_get(API_CATS, {"per_page": PER_PAGE, "page": page})
        data = r.json()
        if not data:
            break
        for c in data:
            cid = c.get("id")
            name = c.get("name")
            if cid is not None and name is not None:
                cat_map[int(cid)] = str(name)
        page += 1
    return cat_map


def parse_event(post, cat_map):
    """
    Kiveszi az esemény mezőket és kategória-neveket a poszt objektumból.
    """
    title = (post.get("title") or {}).get("rendered", "") or ""
    title = title.strip()
    link  = post.get("link", "") or ""

    acf = post.get("acf") or post.get("meta") or {}

    def to_iso(d):
        try:
            return datetime.strptime(d, "%Y%m%d").date().isoformat()
        except Exception:
            return None

    start = to_iso(acf.get("esemeny_kezdete"))
    end   = to_iso(acf.get("esemeny_vege"))

    place = acf.get("helyszin_rovid_neve") or (acf.get("esemeny_terkep") or {}).get("city") or "–"

    cat_ids = post.get("categories", []) or []
    cat_names = [cat_map.get(int(cid), str(cid)) for cid in cat_ids]
    cats = ", ".join(cat_names) if cat_names else "–"

    return {
        "Esemény neve": title,
        "Kezdete":      start,
        "Vége":         end,
        "Helyszín":     place,
        "Kategória":    cats,
        "Aloldal":      link
    }


def save_cache(cat_map, posts):
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    CACHE_CATS.write_text(json.dumps(cat_map, ensure_ascii=False), encoding="utf-8")
    CACHE_POSTS.write_text(json.dumps({
        "fetched_at": datetime.utcnow().isoformat() + "Z",
        "posts": posts
    }, ensure_ascii=False), encoding="utf-8")


def load_cache():
    if not (CACHE_CATS.exists() and CACHE_POSTS.exists()):
        return None, None, None
    try:
        cat_map_raw = json.loads(CACHE_CATS.read_text(encoding="utf-8"))
        # jsonból string kulcsok is jöhetnek -> normalizáljuk int-re
        cat_map = {}
        for k, v in cat_map_raw.items():
            try:
                cat_map[int(k)] = str(v)
            except Exception:
                pass

        post_obj = json.loads(CACHE_POSTS.read_text(encoding="utf-8"))
        posts = post_obj.get("posts", [])
        fetched_at = post_obj.get("fetched_at", None)
        return cat_map, posts, fetched_at
    except Exception:
        return None, None, None


# --------------------------
# Background Worker
# --------------------------

class FetchWorker(QObject):
    """
    Háttérben:
      - kategóriák
      - posztok oldalanként (X-WP-TotalPages alapján)
    Oldalanként küld "page_events" jelet, hogy a UI folyamatosan tudjon tölteni.
    """
    progress = Signal(int, int)      # current_page, total_pages
    status = Signal(str)
    page_events = Signal(list)       # list[dict] (parse_event output)
    finished = Signal(dict, list, str)  # cat_map, posts, fetched_at
    failed = Signal(str)

    def run(self):
        try:
            self.status.emit("Kategóriák letöltése…")
            cat_map = fetch_category_map()

            # 1. oldal: total_pages meghatározás
            self.status.emit("Posztok letöltése (1. oldal)…")
            r = safe_get(API_POSTS, {"per_page": PER_PAGE, "page": 1})
            posts = r.json()
            total_pages = int(r.headers.get("X-WP-TotalPages", 1))

            # 1. oldal feldolgozása
            ev = [parse_event(p, cat_map) for p in posts]
            self.progress.emit(1, total_pages)
            self.page_events.emit(ev)

            for page in range(2, total_pages + 1):
                self.status.emit(f"Posztok letöltése ({page}. oldal)…")
                r2 = safe_get(API_POSTS, {"per_page": PER_PAGE, "page": page})
                data = r2.json()
                posts.extend(data)

                ev2 = [parse_event(p, cat_map) for p in data]
                self.progress.emit(page, total_pages)
                self.page_events.emit(ev2)

            fetched_at = datetime.utcnow().isoformat() + "Z"
            save_cache(cat_map, posts)

            self.finished.emit(cat_map, posts, fetched_at)

        except Exception as e:
            self.failed.emit(str(e))


# --------------------------
# GUI App
# --------------------------

COLS = ["Esemény neve", "Kezdete", "Vége", "Helyszín", "Kategória", "Aloldal"]


class App(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Csodálatos Magyarország – Események")
        self.resize(1200, 720)

        self.df_all = pd.DataFrame(columns=COLS)
        self.df_view = pd.DataFrame(columns=COLS)

        # --- UI ---
        root = QVBoxLayout(self)

        # Top bar
        top = QHBoxLayout()
        self.btn_refresh = QPushButton("Frissítés (API)")
        self.btn_export  = QPushButton("Export (szűrt → Excel)")
        self.btn_open_cache = QPushButton("Cache megnyitása")
        self.btn_clear_cache = QPushButton("Cache törlése")

        self.lbl_spinner = QLabel("○○○")
        self.lbl_progress = QLabel("0/0")
        self.lbl_status  = QLabel("Kész.")

        top.addWidget(self.btn_refresh)
        top.addWidget(self.btn_export)
        top.addWidget(self.btn_open_cache)
        top.addWidget(self.btn_clear_cache)
        top.addStretch(1)
        top.addWidget(self.lbl_spinner)
        top.addWidget(self.lbl_progress)
        top.addWidget(self.lbl_status)

        root.addLayout(top)

        # Filters row
        filters = QHBoxLayout()

        self.date_from = QDateEdit()
        self.date_from.setCalendarPopup(True)
        self.date_from.setDisplayFormat("yyyy-MM-dd")
        self.date_from.setDate(QDate.currentDate())

        self.date_to = QDateEdit()
        self.date_to.setCalendarPopup(True)
        self.date_to.setDisplayFormat("yyyy-MM-dd")
        self.date_to.setDate(QDate.currentDate().addYears(1))

        filters.addWidget(QLabel("Kezdete tól:"))
        filters.addWidget(self.date_from)
        filters.addWidget(QLabel("ig:"))
        filters.addWidget(self.date_to)

        self.txt_search = QLineEdit()
        self.txt_search.setPlaceholderText("Keresés címben / helyszínben…")
        filters.addWidget(self.txt_search, stretch=1)

        self.chk_live_filter = QCheckBox("Szűrés betöltés közben is")
        self.chk_live_filter.setChecked(False)
        filters.addWidget(self.chk_live_filter)

        root.addLayout(filters)

        # Middle: categories + table
        mid = QHBoxLayout()

        left = QVBoxLayout()
        left.addWidget(QLabel("Kategóriák (multi-select):"))
        self.list_cats = QListWidget()
        self.list_cats.setSelectionMode(QListWidget.MultiSelection)
        left.addWidget(self.list_cats)
        mid.addLayout(left, stretch=1)

        right = QVBoxLayout()
        self.table = QTableWidget(0, len(COLS))
        self.table.setHorizontalHeaderLabels(COLS)
        self.table.setSortingEnabled(False)  # betöltés közben gyorsabb így
        self.table.horizontalHeader().setStretchLastSection(True)
        right.addWidget(self.table)

        self.lbl_count = QLabel("0 találat")
        right.addWidget(self.lbl_count)

        mid.addLayout(right, stretch=3)
        root.addLayout(mid)

        # Spinner timer
        self._spinner_frames = ["●○○", "○●○", "○○●"]
        self._spinner_idx = 0
        self._spinner_timer = QTimer(self)
        self._spinner_timer.setInterval(250)
        self._spinner_timer.timeout.connect(self._tick_spinner)
        self._spinner_timer.stop()

        # Signals
        self.btn_refresh.clicked.connect(self.refresh_from_api)
        self.btn_export.clicked.connect(self.export_filtered)
        self.btn_open_cache.clicked.connect(self.open_cache_folder)
        self.btn_clear_cache.clicked.connect(self.clear_cache)

        self.txt_search.textChanged.connect(self.apply_filters)
        self.date_from.dateChanged.connect(self.apply_filters)
        self.date_to.dateChanged.connect(self.apply_filters)
        self.list_cats.itemSelectionChanged.connect(self.apply_filters)

        # State
        self._loading = False
        self._loading_total_pages = 0
        self._loading_current_page = 0

        # Load cache on start
        self.load_initial()

    # ---------- UI helpers ----------
    def _tick_spinner(self):
        self._spinner_idx = (self._spinner_idx + 1) % len(self._spinner_frames)
        self.lbl_spinner.setText(self._spinner_frames[self._spinner_idx])

    def set_controls_enabled(self, enabled: bool):
        self.btn_refresh.setEnabled(enabled)
        self.btn_export.setEnabled(enabled and not self.df_view.empty)
        self.btn_open_cache.setEnabled(True)
        self.btn_clear_cache.setEnabled(True)
        self.date_from.setEnabled(enabled)
        self.date_to.setEnabled(enabled)
        self.txt_search.setEnabled(enabled)
        self.list_cats.setEnabled(enabled)
        self.chk_live_filter.setEnabled(True)

    # ---------- Cache actions ----------
    def open_cache_folder(self):
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        QDesktopServices.openUrl(CACHE_DIR.resolve().as_uri())

    def clear_cache(self):
        try:
            if CACHE_CATS.exists():
                CACHE_CATS.unlink()
            if CACHE_POSTS.exists():
                CACHE_POSTS.unlink()
            QMessageBox.information(self, "Cache törölve", "A cache fájlok törölve lettek.")
            self.lbl_status.setText("Cache törölve.")
        except Exception as e:
            QMessageBox.critical(self, "Hiba", f"Nem sikerült törölni:\n{e}")

    # ---------- Data / rendering ----------
    def load_initial(self):
        cat_map, posts, fetched_at = load_cache()
        if cat_map and posts:
            self.lbl_status.setText(f"Cache betöltve. Utolsó frissítés: {fetched_at or 'ismeretlen'}")
            # építs df-et egyszerre
            events = [parse_event(p, cat_map) for p in posts]
            df = pd.DataFrame(events)
            df = df[df["Kezdete"].notna() & (df["Kezdete"] != "")]
            self.df_all = df.reset_index(drop=True)
            self.populate_categories_from_df(self.df_all)
            self.apply_filters()  # ez a táblát is kirajzolja
        else:
            self.lbl_status.setText("Nincs cache. Nyomj Frissítést (API).")
            self.apply_filters()

    def populate_categories_from_df(self, df: pd.DataFrame):
        self.list_cats.blockSignals(True)
        self.list_cats.clear()
        if not df.empty:
            all_cat_names = sorted({
                c.strip()
                for x in df["Kategória"].dropna().tolist()
                for c in str(x).split(",")
                if c.strip()
            })
            for name in all_cat_names:
                self.list_cats.addItem(QListWidgetItem(name))
        self.list_cats.blockSignals(False)

    def reset_table(self):
        self.table.setRowCount(0)
        self.table.setSortingEnabled(False)

    def append_rows_to_table(self, df_chunk: pd.DataFrame):
        if df_chunk.empty:
            return
        start_row = self.table.rowCount()
        self.table.setRowCount(start_row + len(df_chunk))

        for r, (_, row) in enumerate(df_chunk.iterrows(), start=start_row):
            for c, col in enumerate(COLS):
                text = "" if pd.isna(row.get(col, "")) else str(row.get(col, ""))
                item = QTableWidgetItem(text)
                item.setFlags(item.flags() ^ Qt.ItemIsEditable)
                self.table.setItem(r, c, item)

        # UI: gyorsabb legyen scrollnál is
        self.table.scrollToBottom()

    def set_table_from_df(self, df: pd.DataFrame):
        self.reset_table()
        if df.empty:
            self.lbl_count.setText("0 találat")
            return

        self.table.setRowCount(len(df))
        for r, (_, row) in enumerate(df.iterrows()):
            for c, col in enumerate(COLS):
                text = "" if pd.isna(row.get(col, "")) else str(row.get(col, ""))
                item = QTableWidgetItem(text)
                item.setFlags(item.flags() ^ Qt.ItemIsEditable)
                self.table.setItem(r, c, item)

        self.lbl_count.setText(f"{len(df)} találat")

    # ---------- Filters ----------
    def apply_filters(self):
        # Ha töltés közben vagyunk és nincs "live filter", akkor csak a betöltést mutatjuk
        if self._loading and (not self.chk_live_filter.isChecked()):
            # közben a táblát nem rendereljük újra, mert a worker amúgy is append-el
            # de a gomb státuszát frissítjük
            self.df_view = pd.DataFrame(columns=COLS)
            self.btn_export.setEnabled(False)
            return

        df = self.df_all.copy()
        if df.empty:
            self.df_view = df
            if not self._loading:
                self.set_table_from_df(df)
            self.btn_export.setEnabled(False)
            return

        # Date range
        d_from = self.date_from.date().toPython()
        d_to   = self.date_to.date().toPython()

        def to_date(s):
            try:
                return datetime.fromisoformat(str(s)).date()
            except Exception:
                return None

        dates = df["Kezdete"].map(to_date)
        df = df[dates.notna()]
        if not df.empty:
            dates = df["Kezdete"].map(to_date)
            df = df[(dates >= d_from) & (dates <= d_to)]

        # Categories
        selected = [i.text() for i in self.list_cats.selectedItems()]
        if selected and not df.empty:
            def has_any(cat_str):
                parts = [p.strip() for p in str(cat_str).split(",")]
                return any(s in parts for s in selected)
            df = df[df["Kategória"].map(has_any)]

        # Search
        q = self.txt_search.text().strip().lower()
        if q and not df.empty:
            df = df[
                df["Esemény neve"].astype(str).str.lower().str.contains(q, na=False) |
                df["Helyszín"].astype(str).str.lower().str.contains(q, na=False)
            ]

        # Sort
        if not df.empty:
            df = df.sort_values(by=["Kezdete", "Esemény neve"], ascending=[True, True])

        self.df_view = df.reset_index(drop=True)

        # Render table (ha nincs loading, vagy live-filter módban vagyunk)
        if not self._loading:
            self.set_table_from_df(self.df_view)
        else:
            # live-filter közben a teljes táblát újrarendereljük (lassabb, de ezt kérte a checkbox)
            self.set_table_from_df(self.df_view)

        self.btn_export.setEnabled(not self.df_view.empty and (not self._loading))

    # ---------- Download / Worker hooks ----------
    def refresh_from_api(self):
        if self._loading:
            return

        self._loading = True
        self._loading_total_pages = 0
        self._loading_current_page = 0

        # UI reset
        self.df_all = pd.DataFrame(columns=COLS)
        self.df_view = pd.DataFrame(columns=COLS)
        self.reset_table()
        self.list_cats.clear()
        self.lbl_count.setText("0 betöltött esemény (folyamatban…)")

        self.set_controls_enabled(False)
        self.lbl_progress.setText("0/0")
        self.lbl_status.setText("Indítás…")

        # Spinner start
        self._spinner_idx = 0
        self.lbl_spinner.setText(self._spinner_frames[self._spinner_idx])
        self._spinner_timer.start()

        # Worker thread
        self.thread = QThread(self)
        self.worker = FetchWorker()
        self.worker.moveToThread(self.thread)

        self.thread.started.connect(self.worker.run)
        self.worker.progress.connect(self.on_progress)
        self.worker.status.connect(self.lbl_status.setText)
        self.worker.page_events.connect(self.on_page_events)
        self.worker.finished.connect(self.on_finished)
        self.worker.failed.connect(self.on_failed)

        self.worker.finished.connect(self.thread.quit)
        self.worker.failed.connect(self.thread.quit)
        self.thread.finished.connect(self.thread.deleteLater)

        self.thread.start()

    def on_progress(self, page, total):
        self._loading_current_page = page
        self._loading_total_pages = total
        self.lbl_progress.setText(f"{page}/{total}")

    def on_page_events(self, events_list):
        if not events_list:
            return

        df_new = pd.DataFrame(events_list)
        df_new = df_new[df_new["Kezdete"].notna() & (df_new["Kezdete"] != "")]
        if df_new.empty:
            return

        # bővítés
        self.df_all = pd.concat([self.df_all, df_new], ignore_index=True)

        # kategória lista “folyamatosan”
        existing = set()
        for i in range(self.list_cats.count()):
            existing.add(self.list_cats.item(i).text())

        new_cats = sorted({
            c.strip()
            for x in df_new["Kategória"].dropna().tolist()
            for c in str(x).split(",")
            if c.strip() and c.strip() not in existing
        })
        if new_cats:
            self.list_cats.blockSignals(True)
            for name in new_cats:
                self.list_cats.addItem(QListWidgetItem(name))
            self.list_cats.blockSignals(False)

        # táblázat: ha nincs live-filter, akkor “append” mód a leggyorsabb
        if not self.chk_live_filter.isChecked():
            self.append_rows_to_table(df_new)
            self.lbl_count.setText(f"{len(self.df_all)} betöltött esemény (folyamatban…)")
        else:
            # live-filter esetén azonnal szűrünk (lassabb, de látványos)
            self.apply_filters()
            self.lbl_count.setText(f"{len(self.df_view)} találat (betöltés közben)")

    def on_finished(self, cat_map, posts, fetched_at):
        self._loading = False
        self._spinner_timer.stop()
        self.lbl_spinner.setText("✓")

        # Betöltés végén: most már rendes szűrés + rendes render
        self.lbl_status.setText(f"Kész. Cache mentve. Utolsó frissítés: {fetched_at}")
        self.lbl_progress.setText(f"{self._loading_total_pages}/{self._loading_total_pages}" if self._loading_total_pages else "Kész")

        self.set_controls_enabled(True)

        # Betöltés közben appendeltünk; most rendezzünk és alkalmazzuk a szűrést normál módon
        # (akkor is, ha live-filter nem volt)
        self.apply_filters()
        if self.df_view.empty:
            self.btn_export.setEnabled(False)
        else:
            self.btn_export.setEnabled(True)

        # betöltés után engedhetjük a sortingot
        self.table.setSortingEnabled(True)

    def on_failed(self, msg):
        self._loading = False
        self._spinner_timer.stop()
        self.lbl_spinner.setText("✗")

        self.set_controls_enabled(True)
        self.btn_export.setEnabled(False)

        QMessageBox.critical(self, "Hiba", f"Nem sikerült frissíteni:\n{msg}")
        self.lbl_status.setText("Hiba történt.")

    # ---------- Export ----------
    def export_filtered(self):
        if self._loading:
            QMessageBox.information(self, "Folyamatban", "Betöltés közben nem exportálunk. Várd meg a végét.")
            return

        if self.df_view.empty:
            QMessageBox.information(self, "Nincs adat", "A szűrés eredménye üres, nincs mit exportálni.")
            return

        fn, _ = QFileDialog.getSaveFileName(
            self, "Mentés Excelbe", "esemenyek_szurt.xlsx", "Excel (*.xlsx)"
        )
        if not fn:
            return

        try:
            self.df_view.to_excel(fn, index=False)
            QMessageBox.information(self, "Kész", f"Mentve:\n{fn}")
        except Exception as e:
            QMessageBox.critical(self, "Hiba", f"Nem sikerült menteni:\n{e}")


def main():
    app = QApplication(sys.argv)
    w = App()
    w.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
