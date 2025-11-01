# admin_page.py
import os
import re
import sqlite3
import json
from datetime import datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QLineEdit,
    QComboBox, QDialog, QFormLayout, QMessageBox, QTableWidget,
    QTableWidgetItem, QHeaderView, QInputDialog, QDialogButtonBox, QListWidget,
    QCheckBox, QScrollArea, QGroupBox
)
from PySide6.QtGui import QFont, QIcon, QPixmap, QColor
from PySide6.QtCore import Qt, QSize, QTimer, QEvent

DB_PATH = "chbib_materials.db"
DEFAULT_USD_TO_LBP = 89000

def to_decimal_from_text(s: str) -> Decimal:
    if s is None:
        raise InvalidOperation
    t = str(s).strip()
    if t == "":
        raise InvalidOperation
    m = re.search(r'[-+]?\d+(?:[.,]\d+)?', t)
    if not m:
        raise InvalidOperation
    num = m.group(0).replace(",", ".")
    return Decimal(num)

def fmt_lbp(value):
    try:
        dec = Decimal(value)
    except Exception:
        dec = Decimal(0)
    dec = dec.quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    return f"{int(dec):,} ل.ل"

def fmt_usd(value):
    try:
        dec = Decimal(value)
    except Exception:
        dec = Decimal(0)
    if dec == dec.quantize(Decimal("1")):
        return f"{int(dec):,} $"
    dec2 = dec.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP).normalize()
    s = format(dec2, 'f')
    if "." in s:
        intp, frac = s.split(".")
        intp = f"{int(intp):,}"
        return f"{intp}.{frac} $"
    else:
        return f"{int(s):,} $"

def fmt_qty(value):
    try:
        dec = Decimal(value)
    except Exception:
        return str(value)
    if dec == dec.quantize(Decimal("1")):
        return f"{int(dec):,}"
    s = dec.normalize()
    return format(s, 'f')

class AdminPage(QWidget):
    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        self.db_path = DB_PATH
        self.usd_to_lbp = self.load_exchange_rate()
        self.capital_hidden = False

        self._ensure_db()
        self._load_units_cache()
        self._build_ui()
        
        # ✅ إعداد نظام المراقبة
        self.setup_data_monitoring()

        self.load_items()
        self.update_total_capital()

    def load_exchange_rate(self):
        """✅ تحميل سعر الصرف من ملف الإعدادات"""
        try:
            settings_file = "data/exchange_rate.json"
            if os.path.exists(settings_file):
                with open(settings_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return int(data.get('exchange_rate', DEFAULT_USD_TO_LBP))
        except Exception as e:
            print(f"❌ خطأ في تحميل سعر الصرف: {e}")
        return DEFAULT_USD_TO_LBP

    def save_exchange_rate_to_file(self, rate):
        """✅ حفظ سعر الصرف في ملف"""
        try:
            os.makedirs("data", exist_ok=True)
            settings_file = "data/exchange_rate.json"
            data = {
                "exchange_rate": rate, 
                "last_updated": datetime.now().isoformat()
            }
            
            with open(settings_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                
            print(f"✅ [سعر الصرف] تم الحفظ في الملف: {rate}")
        except Exception as e:
            print(f"❌ [سعر الصرف] خطأ في حفظ الملف: {e}")

    def _ensure_db(self):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        c.execute("""
            CREATE TABLE IF NOT EXISTS Items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                buy_unit TEXT,
                sell_unit TEXT,
                buy_price REAL,
                sell_price REAL,
                quantity REAL,
                currency TEXT,
                capital_value_lbp REAL
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS Units (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                unit TEXT,
                kind TEXT
            )
        """)
        
        # ✅ جدول جديد لوحدات المبيع لكل صنف
        c.execute("""
            CREATE TABLE IF NOT EXISTS ItemSellUnits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_id INTEGER,
                sell_unit TEXT,
                FOREIGN KEY (item_id) REFERENCES Items (id) ON DELETE CASCADE
            )
        """)
        
        default_buy = ["طن", "شوال 25كغ", "شوال 50كغ", "كيلو", "متر", "بالحبة/العدد"]
        default_sell = ["طن", "شوال", "كيلو", "شحنة", "متر", "بالحبة/العدد"]
        for u in default_buy:
            c.execute("INSERT INTO Units(unit, kind) SELECT ?, 'buy' WHERE NOT EXISTS (SELECT 1 FROM Units WHERE unit=? AND kind='buy')", (u, u))
        for u in default_sell:
            c.execute("INSERT INTO Units(unit, kind) SELECT ?, 'sell' WHERE NOT EXISTS (SELECT 1 FROM Units WHERE unit=? AND kind='sell')", (u, u))

        conn.commit()
        conn.close()

    def _load_units_cache(self):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("SELECT unit FROM Units WHERE kind='buy' ORDER BY unit")
        self.units_buy = [r[0] for r in c.fetchall()]
        c.execute("SELECT unit FROM Units WHERE kind='sell' ORDER BY unit")
        self.units_sell = [r[0] for r in c.fetchall()]
        conn.close()

    def _build_ui(self):
        # ✅ تحسين الخطوط وجعلها أكبر وأكثر سماكة
        self.setStyleSheet("""
            QWidget { 
                background-color: #0D1B2A; 
                color: white; 
                font-family: Arial; 
                font-weight: bold;
                font-size: 16px;
            }
            QLineEdit, QComboBox { 
                background-color: #F6F6F6; 
                color: black; 
                border-radius: 8px; 
                padding: 12px;
                font-size: 16px;
                font-weight: bold;
                border: 2px solid #415A77;
                min-height: 25px;
            }
            QPushButton { 
                background-color: #1B263B; 
                color: white; 
                border-radius: 10px; 
                padding: 15px;
                font-size: 18px;
                font-weight: bold;
                border: 2px solid #415A77;
                min-height: 30px;
            }
            QPushButton:hover { 
                background-color: #2E4057; 
                border: 2px solid #778DA9;
            }
            QTableWidget {
                font-size: 15px;
                font-weight: bold;
            }
            QHeaderView::section {
                font-size: 15px;
                font-weight: bold;
                padding: 12px;
            }
            QLabel {
                font-weight: bold;
                font-size: 16px;
            }
            QListWidget {
                font-size: 15px;
                font-weight: bold;
            }
        """)
        main = QVBoxLayout(self)
        main.setContentsMargins(15, 5, 15, 15)  # ✅ تقليل المسافة العلوية
        main.setSpacing(10)  # ✅ تقليل المسافة بين العناصر

        # ✅ رأس الصفحة - تصميم جديد لجعل "الإدارة" في أعلى منتصف الشاشة
        header_widget = QWidget()
        header_widget.setStyleSheet("background-color: transparent;")
        header_layout = QVBoxLayout(header_widget)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(0)  # ✅ إزالة المسافة بين الصفوف تماماً

        # ✅ الصف العلوي: زر الرجوع واللوجو فقط
        top_row = QHBoxLayout()
        top_row.setContentsMargins(0, 0, 0, 0)
        
        self.back_btn = QPushButton()
        if os.path.exists("icons/back.png"):
            self.back_btn.setIcon(QIcon("icons/back.png"))
        else:
            self.back_btn.setText("←")
        self.back_btn.setIconSize(QSize(120, 100))
        self.back_btn.setFixedSize(50, 50)
        self.back_btn.setStyleSheet("background: transparent; border: none; font-size: 40px;")
        
        if hasattr(self.controller, "init_main_page"):
            self.back_btn.clicked.connect(self.controller.init_main_page)
        elif hasattr(self.controller, "show_main_page"):
            self.back_btn.clicked.connect(self.controller.show_main_page)

        self.logo_label = QLabel()
        logo_path = "icons/logo.png"
        if os.path.exists(logo_path):
            pix = QPixmap(logo_path)
            self.logo_label.setPixmap(pix.scaled(150, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        self.logo_label.setAlignment(Qt.AlignRight)
        self.logo_label.setStyleSheet("background-color: transparent;")

        top_row.addWidget(self.back_btn, alignment=Qt.AlignLeft)
        top_row.addStretch()
        top_row.addWidget(self.logo_label, alignment=Qt.AlignRight)

        # ✅ الصف الأوسط: عنوان "الإدارة" كبير وفي المنتصف تماماً - تم رفعه للأعلى
        title_row = QHBoxLayout()
        title_row.setContentsMargins(0, -250, 0, -100)  # ✅ رفع كبير جداً
        title_row.setAlignment(Qt.AlignTop)  # ✅ محاذاة للأعلى
        
        title = QLabel("الإدارة")
        title.setFont(QFont("Arial", 56, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("""
            background-color: transparent;
            font-size: 28px; 
            color: white; 
            padding: 0; 
            margin: 0;
            border: none;
            font-weight: bold;
        """)
        
        title_row.addStretch()
        title_row.addWidget(title, alignment=Qt.AlignCenter)
        title_row.addStretch()

        # ✅ إضافة الصفوف إلى التخطيط الرئيسي للرأس
        header_layout.addLayout(top_row)
        header_layout.addLayout(title_row)
        
        # ✅ إضافة الرأس إلى التخطيط الرئيسي
        main.addWidget(header_widget)

        # أزرار الإدارة - حجم أكبر
        btns_layout = QHBoxLayout()
        self.add_btn = QPushButton("➕ إضافة صنف")
        self.edit_btn = QPushButton("✏️ تعديل صنف")
        self.delete_btn = QPushButton("🗑 حذف صنف")
        self.units_btn = QPushButton("⚙️ وحدات القياس")
        self.rate_btn = QPushButton("💱 سعر الصرف")

        for b in (self.add_btn, self.edit_btn, self.delete_btn, self.units_btn, self.rate_btn):
            b.setFixedHeight(65)  # ✅ زيادة ارتفاع الأزرار
            b.setMinimumWidth(180)  # ✅ زيادة عرض الأزرار
            b.setFont(QFont("Arial", 16, QFont.Bold))  # ✅ زيادة حجم خط الأزرار
            btns_layout.addWidget(b)

        main.addLayout(btns_layout)

        # ربط الأزرار
        self.add_btn.clicked.connect(self.open_add_dialog)
        self.edit_btn.clicked.connect(self.open_edit_dialog)
        self.delete_btn.clicked.connect(self.delete_selected_item)
        self.units_btn.clicked.connect(self.open_manage_units_dialog)
        self.rate_btn.clicked.connect(self.change_exchange_rate_dialog)

        # شريط البحث - حجم أكبر
        search_row = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 ابحث باسم الصنف...")
        self.search_input.setFixedHeight(55)  # ✅ زيادة ارتفاع شريط البحث
        self.search_input.setFont(QFont("Arial", 16, QFont.Bold))  # ✅ زيادة حجم خط البحث
        self.search_input.textChanged.connect(self._on_search_text_changed)
        search_row.addWidget(self.search_input)
        main.addLayout(search_row)

        # جدول الأصناف
        self.table = QTableWidget(0, 11)
        self.table.setHorizontalHeaderLabels([
            "ID", "الاسم", "وحدة الشراء", "وحدة المبيع",
            "سعر الشراء (ل.ل)", "سعر الشراء ($)",
            "سعر المبيع مفرق (ل.ل)", "سعر المبيع مفرق ($)",
            "الكمية", "رأس المال (ل.ل)", "رأس المال ($)"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setColumnHidden(0, True)
        
        # ✅ تحسين التحديد في الجدول - إزالة النقاط واستخدام اللون الأزرق
        self.table.setStyleSheet("""
            QTableWidget { 
                background-color: #FFFFFF; 
                color: black; 
                gridline-color: #dcdcdc;
                font-size: 14px;
                font-weight: bold;
                selection-background-color: #2196F3;
                selection-color: white;
                outline: none;
            }
            QHeaderView::section { 
                background-color: #1B263B; 
                color: white; 
                padding: 12px;
                font-size: 14px;
                font-weight: bold;
            }
            QTableWidget::item {
                padding: 10px;
                font-weight: bold;
                font-size: 14px;
            }
            QTableWidget::item:selected {
                background-color: #2196F3;
                color: white;
            }
        """)
        
        main.addWidget(self.table)

        self.table.itemDoubleClicked.connect(self._on_table_double_click)
        
        # ✅ إضافة حدث النقر على الخلفية لإزالة التحديد
        self.table.viewport().installEventFilter(self)

        # إجمالي رأس المال - حجم أكبر
        total_row = QHBoxLayout()
        total_row.addStretch()
        self.total_label = QLabel("إجمالي رأس المال:")
        self.total_label.setFont(QFont("Arial", 20, QFont.Bold))
        self.total_label.setStyleSheet("color: white; font-weight: bold;")
        self.total_value = QLabel("")
        self.total_value.setFont(QFont("Arial", 20, QFont.Bold))
        self.total_value.setStyleSheet("color: lightgreen; font-weight: bold;")

        self.eye_btn = QPushButton()
        if os.path.exists("icons/eye.png"):
            self.eye_btn.setIcon(QIcon("icons/eye.png"))
        else:
            self.eye_btn.setText("👁")
        self.eye_btn.setIconSize(QSize(35, 35))
        self.eye_btn.setFixedSize(50, 50)
        self.eye_btn.setStyleSheet("background-color: transparent; border: none; font-size: 25px;")
        self.eye_btn.clicked.connect(self.toggle_capital_visibility)

        total_row.addWidget(self.total_label)
        total_row.addWidget(self.total_value)
        total_row.addWidget(self.eye_btn)
        total_row.addStretch()
        main.addLayout(total_row)

    def eventFilter(self, source, event):
        """✅ إزالة التحديد عند النقر على الخلفية - الإصدار المصحح"""
        if (source is self.table.viewport() and 
            event.type() == QEvent.Type.MouseButtonPress and 
            not self.table.indexAt(event.pos()).isValid()):
            self.table.clearSelection()
            return True
        return super().eventFilter(source, event)

    def load_items(self):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("PRAGMA table_info(Items)")
        cols = [r[1] for r in c.fetchall()]

        c.execute("SELECT * FROM Items ORDER BY name")
        rows = c.fetchall()
        col_indices = {name: idx for idx, name in enumerate(cols)}

        self.all_rows = []
        self.table.setRowCount(0)

        for r in rows:
            rowd = {}
            for i, colname in enumerate(cols):
                rowd[colname] = r[i]

            item_id = rowd.get("id")
            name = rowd.get("name") or ""
            buy_unit = rowd.get("buy_unit") or ""
            sell_unit = rowd.get("sell_unit") or ""
            
            if "buy_price" in rowd and rowd.get("buy_price") is not None:
                buy_price_raw = Decimal(rowd.get("buy_price") or 0)
            elif "buy_price_lbp" in rowd and rowd.get("buy_price_lbp") is not None:
                buy_price_raw = Decimal(rowd.get("buy_price_lbp") or 0)
            else:
                buy_price_raw = Decimal(0)

            if "sell_price" in rowd and rowd.get("sell_price") is not None:
                sell_price_raw = Decimal(rowd.get("sell_price") or 0)
            elif "sell_price_lbp" in rowd and rowd.get("sell_price_lbp") is not None:
                sell_price_raw = Decimal(rowd.get("sell_price_lbp") or 0)
            else:
                sell_price_raw = Decimal(0)

            qty = Decimal(rowd.get("quantity") or 0)
            currency = (rowd.get("currency") or "LBP").upper()
            
            cap_lbp = None
            if "capital_value_lbp" in rowd and rowd.get("capital_value_lbp") is not None:
                cap_lbp = Decimal(rowd.get("capital_value_lbp") or 0)
            else:
                if currency in ("USD", "US$"):
                    cap_lbp = (buy_price_raw * qty * Decimal(self.usd_to_lbp)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                else:
                    cap_lbp = (buy_price_raw * qty).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

            if currency in ("USD", "US$"):
                buy_usd = buy_price_raw
                buy_lbp = (buy_price_raw * Decimal(self.usd_to_lbp)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                sell_usd = sell_price_raw
                sell_lbp = (sell_price_raw * Decimal(self.usd_to_lbp)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            else:
                buy_lbp = buy_price_raw
                buy_usd = (buy_price_raw / Decimal(self.usd_to_lbp)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                sell_lbp = sell_price_raw
                sell_usd = (sell_price_raw / Decimal(self.usd_to_lbp)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

            cap_usd = (cap_lbp / Decimal(self.usd_to_lbp)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

            self.all_rows.append((item_id, name, buy_unit, sell_unit, buy_lbp, buy_usd, sell_lbp, sell_usd, qty, cap_lbp, cap_usd))

        conn.close()
        self._populate_table(self.all_rows)

    def _populate_table(self, rows):
        self.table.setRowCount(0)
        for r in rows:
            item_id, name, buy_u, sell_u, buy_lbp, buy_usd, sell_lbp, sell_usd, qty, cap_lbp, cap_usd = r
            row = self.table.rowCount()
            self.table.insertRow(row)

            id_item = QTableWidgetItem(str(item_id))
            id_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 0, id_item)

            def qitem(text):
                it = QTableWidgetItem(text)
                it.setTextAlignment(Qt.AlignCenter)
                it.setForeground(QColor("black"))
                font = QFont("Arial", 13, QFont.Bold)
                it.setFont(font)
                return it

            self.table.setItem(row, 1, qitem(str(name)))
            self.table.setItem(row, 2, qitem(str(buy_u)))
            self.table.setItem(row, 3, qitem(str(sell_u)))
            self.table.setItem(row, 4, qitem(fmt_lbp(buy_lbp)))
            self.table.setItem(row, 5, qitem(fmt_usd(buy_usd)))
            self.table.setItem(row, 6, qitem(fmt_lbp(sell_lbp)))
            self.table.setItem(row, 7, qitem(fmt_usd(sell_usd)))
            self.table.setItem(row, 8, qitem(fmt_qty(qty)))
            self.table.setItem(row, 9, qitem(fmt_lbp(cap_lbp)))
            self.table.setItem(row, 10, qitem(fmt_usd(cap_usd)))

    def _on_search_text_changed(self):
        q = self.search_input.text().strip().lower()
        if not q:
            rows = self.all_rows
        else:
            rows = [r for r in self.all_rows if q in str(r[1]).lower()]
        self._populate_table(rows)

    def update_total_capital(self):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        try:
            c.execute("SELECT SUM(capital_value_lbp) FROM Items")
            total_lbp = Decimal(c.fetchone()[0] or 0)
        except sqlite3.OperationalError:
            c.execute("SELECT buy_price, quantity, currency FROM Items")
            total_lbp = Decimal(0)
            for bprice, qty, currency in c.fetchall():
                try:
                    b = Decimal(bprice or 0)
                    q = Decimal(qty or 0)
                except Exception:
                    continue
                if (currency or "LBP").upper() in ("USD", "US$"):
                    total_lbp += (b * q * Decimal(self.usd_to_lbp))
                else:
                    total_lbp += (b * q)
        conn.close()

        total_usd = (total_lbp / Decimal(self.usd_to_lbp)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        if self.capital_hidden:
            self.total_value.setText("******")
        else:
            self.total_value.setText(f"{fmt_lbp(total_lbp)}  —  {fmt_usd(total_usd)}")

    def toggle_capital_visibility(self):
        self.capital_hidden = not self.capital_hidden
        if self.capital_hidden:
            if os.path.exists("icons/eye_off.png"):
                self.eye_btn.setIcon(QIcon("icons/eye_off.png"))
            else:
                self.eye_btn.setText("👁️‍🗨️")
        else:
            if os.path.exists("icons/eye.png"):
                self.eye_btn.setIcon(QIcon("icons/eye.png"))
            else:
                self.eye_btn.setText("👁")
        self.update_total_capital()

    def open_add_dialog(self):
        dlg = ItemDialog(self.units_buy, self.units_sell, parent=self)
        if dlg.exec():
            data = dlg.get_data()
            try:
                buy_price = to_decimal_from_text(data["buy_price"])
                sell_price = to_decimal_from_text(data["sell_price"]) if data["sell_price"].strip() != "" else Decimal(0)
                qty = to_decimal_from_text(data["quantity"])
            except Exception:
                QMessageBox.warning(self, "خطأ", "الرجاء إدخال أرقام صحيحة للسعر والكمية.")
                return

            currency = data["currency"]
            if currency.upper() in ("USD", "US$"):
                cap_lbp = (buy_price * qty * Decimal(self.usd_to_lbp)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            else:
                cap_lbp = (buy_price * qty).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            c.execute("""
                INSERT INTO Items (name, buy_unit, sell_unit, buy_price, sell_price, quantity, currency, capital_value_lbp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (data["name"], data["buy_unit"], data["sell_unit"], float(buy_price), float(sell_price), float(qty), currency.upper(), float(cap_lbp)))
            
            item_id = c.lastrowid
            
            # ✅ حفظ وحدات المبيع المتعددة للصنف
            if "sell_units" in data:
                for unit in data["sell_units"]:
                    c.execute("INSERT INTO ItemSellUnits (item_id, sell_unit) VALUES (?, ?)", (item_id, unit))
            
            conn.commit()
            conn.close()
            self._load_units_cache()
            self.load_items()
            self.update_total_capital()
            
            # ✅ إرسال البيانات إلى صفحة التقارير
            self.send_to_reports_page("add", item_id, data["name"])

    def open_edit_dialog(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "تحذير", "يرجى اختيار صنف أولاً")
            return
        try:
            item_id = int(self.table.item(row, 0).text())
        except Exception:
            QMessageBox.warning(self, "خطأ", "لا يمكن الحصول على هوية الصنف.")
            return

        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("SELECT id, name, buy_unit, sell_unit, buy_price, sell_price, quantity, currency FROM Items WHERE id=?", (item_id,))
        rec = c.fetchone()
        
        # ✅ جلب وحدات المبيع الخاصة بالصنف
        c.execute("SELECT sell_unit FROM ItemSellUnits WHERE item_id=?", (item_id,))
        item_sell_units = [row[0] for row in c.fetchall()]
        
        conn.close()
        if not rec:
            QMessageBox.warning(self, "خطأ", "الصنف غير موجود.")
            return

        preset = {
            "id": rec[0],
            "name": rec[1],
            "buy_unit": rec[2] or "",
            "sell_unit": rec[3] or "",
            "buy_price": str(rec[4]) if rec[4] is not None else "0",
            "sell_price": str(rec[5]) if rec[5] is not None else "0",
            "quantity": str(rec[6]) if rec[6] is not None else "0",
            "currency": (rec[7] or "LBP").upper(),
            "sell_units": item_sell_units
        }

        dlg = ItemDialog(self.units_buy, self.units_sell, parent=self, preset=preset)
        if dlg.exec():
            data = dlg.get_data()
            try:
                buy_price = to_decimal_from_text(data["buy_price"])
                sell_price = to_decimal_from_text(data["sell_price"]) if data["sell_price"].strip() != "" else Decimal(0)
                qty = to_decimal_from_text(data["quantity"])
            except Exception:
                QMessageBox.warning(self, "خطأ", "الرجاء إدخال أرقام صحيحة.")
                return

            currency = data["currency"]
            if currency.upper() in ("USD", "US$"):
                cap_lbp = (buy_price * qty * Decimal(self.usd_to_lbp)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            else:
                cap_lbp = (buy_price * qty).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            c.execute("""
                UPDATE Items SET name=?, buy_unit=?, sell_unit=?, buy_price=?, sell_price=?, quantity=?, currency=?, capital_value_lbp=?
                WHERE id=?
            """, (data["name"], data["buy_unit"], data["sell_unit"], float(buy_price), float(sell_price), float(qty), currency.upper(), float(cap_lbp), item_id))
            
            # ✅ تحديث وحدات المبيع المتعددة للصنف
            c.execute("DELETE FROM ItemSellUnits WHERE item_id=?", (item_id,))
            if "sell_units" in data:
                for unit in data["sell_units"]:
                    c.execute("INSERT INTO ItemSellUnits (item_id, sell_unit) VALUES (?, ?)", (item_id, unit))
            
            conn.commit()
            conn.close()
            self._load_units_cache()
            self.load_items()
            self.update_total_capital()
            
            # ✅ إرسال البيانات إلى صفحة التقارير
            self.send_to_reports_page("edit", item_id, data["name"])

    def delete_selected_item(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "تحذير", "اختر صنفًا للحذف.")
            return
        try:
            item_id = int(self.table.item(row, 0).text())
            name = self.table.item(row, 1).text()
        except Exception:
            QMessageBox.warning(self, "خطأ", "حدث خطأ في تحديد الصنف.")
            return

        r = QMessageBox.question(self, "تأكيد الحذف", f"هل تريد حذف الصنف '{name}'؟", QMessageBox.Yes | QMessageBox.No)
        if r != QMessageBox.Yes:
            return
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("DELETE FROM Items WHERE id=?", (item_id,))
        c.execute("DELETE FROM ItemSellUnits WHERE item_id=?", (item_id,))
        conn.commit()
        conn.close()
        self.load_items()
        self.update_total_capital()
        
        # ✅ إرسال البيانات إلى صفحة التقارير
        self.send_to_reports_page("delete", item_id, name)

    def open_manage_units_dialog(self):
        dlg = ManageUnitsDialog(self.units_buy, self.units_sell, parent=self)
        if dlg.exec():
            self._load_units_cache()

    def change_exchange_rate_dialog(self):
        """✅ تحديث سعر الصرف مع التطبيق الفوري"""
        text, ok = QInputDialog.getText(self, "تعديل سعر الصرف", "1 دولار = كم ليرة لبنانية؟", text=str(self.usd_to_lbp))
        if ok and text:
            try:
                v = to_decimal_from_text(text)
                new_rate = int(v)
                
                # ✅ تحديث سعر الصرف فوراً
                success = self.update_exchange_rate_globally(new_rate)
                
                if success:
                    QMessageBox.information(self, "تم", f"✅ تم تحديث سعر الصرف إلى: 1$ = {new_rate} ل.ل\n\nتم التحديث في:\n• صفحة الإدارة\n• ملف الإعدادات\n• صفحة الفواتير")
                else:
                    QMessageBox.warning(self, "تحذير", "تم تحديث سعر الصرف محلياً ولكن قد يكون هناك مشكلة في التحديث العالمي")
                    
            except Exception:
                QMessageBox.warning(self, "خطأ", "أدخل قيمة صحيحة لسعر الصرف.")

    def update_exchange_rate_globally(self, new_rate):
        """✅ تحديث سعر الصرف عالمياً وفي جميع الصفحات"""
        try:
            print(f"🔄 [سعر الصرف] بدء التحديث العالمي إلى: {new_rate}")
            
            # تحديث السعر محلياً
            self.usd_to_lbp = new_rate
            
            # ✅ حفظ في ملف الإعدادات
            self.save_exchange_rate_to_file(new_rate)
            
            # ✅ تحديث صفحة الفواتير إذا كانت مفتوحة
            self.update_invoice_page_exchange_rate(new_rate)
            
            # ✅ تحديث الأسعار والمخزون
            self.update_lbp_prices_and_capital()
            
            print(f"✅ [سعر الصرف] تم التحديث العالمي بنجاح: {new_rate}")
            return True
            
        except Exception as e:
            print(f"❌ [سعر الصرف] خطأ في التحديث العالمي: {e}")
            return False

    def update_invoice_page_exchange_rate(self, new_rate):
        """✅ تحديث سعر الصرف في صفحة الفواتير مباشرة"""
        try:
            print(f"🔍 [سعر الصرف] محاولة تحديث صفحة الفواتير إلى: {new_rate}")
            
            # الطريقة 1: عبر الـ controller مباشرة
            if hasattr(self.controller, 'invoices_page') and self.controller.invoices_page is not None:
                if hasattr(self.controller.invoices_page, 'update_exchange_rate'):
                    self.controller.invoices_page.update_exchange_rate(new_rate)
                    print(f"✅ [سعر الصرف] تم التحديث المباشر عبر controller: {new_rate}")
                else:
                    self.controller.invoices_page.exchange_rate = new_rate
                    print(f"✅ [سعر الصرف] تم تحديث السعر مباشرة: {new_rate}")
            
            # الطريقة 2: عبر ملف مشترك (مضمونة)
            self.save_exchange_rate_to_file(new_rate)
            print(f"✅ [سعر الصرف] تم حفظ السعر في الملف: {new_rate}")
            
            return True
            
        except Exception as e:
            print(f"❌ [سعر الصرف] خطأ في تحديث صفحة الفواتير: {e}")
            return False

    def update_lbp_prices_and_capital(self):
        """✅ تحديث الأسعار بالليرة اللبنانية ورأس المال"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # تحديث رأس المال بالليرة اللبنانية لكل صنف
        c.execute("SELECT id, buy_price, quantity, currency FROM Items")
        items = c.fetchall()
        
        for item_id, buy_price, quantity, currency in items:
            try:
                buy_price_dec = Decimal(str(buy_price)) if buy_price else Decimal(0)
                quantity_dec = Decimal(str(quantity)) if quantity else Decimal(0)
                
                if (currency or "LBP").upper() in ("USD", "US$"):
                    capital_value_lbp = (buy_price_dec * quantity_dec * Decimal(self.usd_to_lbp)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                else:
                    capital_value_lbp = (buy_price_dec * quantity_dec).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                
                c.execute("UPDATE Items SET capital_value_lbp = ? WHERE id = ?", (float(capital_value_lbp), item_id))
                
            except Exception as e:
                print(f"خطأ في تحديث رأس المال للصنف {item_id}: {e}")
        
        conn.commit()
        conn.close()
        
        # إعادة تحميل العناصر لتحديث العرض
        self.load_items()
        self.update_total_capital()
        print("✅ [رأس المال] تم تحديث الأسعار ورأس المال")

    def update_item_quantity(self, item_name, quantity_change, operation_type="subtract"):
        """✅ تحديث كمية الصنف تلقائياً - فعالة ومباشرة"""
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            
            # البحث عن الصنف بالاسم
            c.execute("SELECT id, quantity, name FROM Items WHERE name=?", (item_name,))
            item = c.fetchone()
            
            if item:
                item_id, current_quantity, item_name = item
                current_qty_dec = Decimal(str(current_quantity))
                change_qty_dec = Decimal(str(quantity_change))
                
                if operation_type == "subtract":
                    new_quantity = current_qty_dec - change_qty_dec
                else:  # add
                    new_quantity = current_qty_dec + change_qty_dec
                
                # التأكد من أن الكمية لا تصبح سالبة
                if new_quantity < Decimal(0):
                    print(f"⚠️ [المخزون] الكمية غير كافية للصنف {item_name}")
                    conn.close()
                    return False
                
                # تحديث الكمية في قاعدة البيانات
                c.execute("UPDATE Items SET quantity=? WHERE id=?", (float(new_quantity), item_id))
                print(f"✅ [المخزون] تم تحديث {item_name}: {current_quantity} → {new_quantity} ({operation_type} {quantity_change})")
                
                # إعادة حساب رأس المال
                c.execute("SELECT buy_price, currency FROM Items WHERE id=?", (item_id,))
                buy_price, currency = c.fetchone()
                buy_price_dec = Decimal(str(buy_price)) if buy_price else Decimal(0)
                
                if (currency or "LBP").upper() in ("USD", "US$"):
                    capital_value_lbp = (buy_price_dec * new_quantity * Decimal(self.usd_to_lbp)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                else:
                    capital_value_lbp = (buy_price_dec * new_quantity).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                
                c.execute("UPDATE Items SET capital_value_lbp=? WHERE id=?", (float(capital_value_lbp), item_id))
                
                conn.commit()
                conn.close()
                
                # ✅ تحديث العرض مباشرة
                self.load_items()
                self.update_total_capital()
                
                print(f"✅ [المخزون] تم التحديث بنجاح للصنف {item_name}")
                return True
            else:
                print(f"❌ [المخزون] لم يتم العثور على الصنف {item_name}")
                conn.close()
                return False
                
        except Exception as e:
            print(f"❌ [المخزون] خطأ في تحديث كمية الصنف: {e}")
            return False

    def restore_item_quantity(self, item_name, quantity_to_restore):
        """✅ استعادة كمية الصنف عند حذف فاتورة أو تعديلها"""
        return self.update_item_quantity(item_name, quantity_to_restore, "add")

    def refresh_data_immediately(self):
        """✅ تحديث البيانات فورياً دون إعادة فتح الصفحة"""
        try:
            print("🔄 [التحديث الفوري] بدء تحديث بيانات الإدارة...")
            
            # تحميل العناصر من قاعدة البيانات
            self.load_items()
            
            # تحديث رأس المال
            self.update_total_capital()
            
            # تحديث وحدات القياس إذا لزم الأمر
            self._load_units_cache()
            
            print("✅ [التحديث الفوري] تم تحديث بيانات الإدارة بنجاح")
            
        except Exception as e:
            print(f"❌ [التحديث الفوري] خطأ في تحديث البيانات: {e}")

    def setup_data_monitoring(self):
        """✅ إعداد نظام مراقبة التغييرات في البيانات"""
        try:
            # مؤقت للمراقبة الدورية (اختياري)
            self.monitor_timer = QTimer()
            self.monitor_timer.timeout.connect(self.check_for_data_changes)
            self.monitor_timer.start(5000)  # التحقق كل 5 ثواني
            
            print("✅ [المراقبة] تم إعداد نظام مراقبة التغييرات")
        except Exception as e:
            print(f"❌ [المراقبة] خطأ في إعداد النظام: {e}")

    def check_for_data_changes(self):
        """✅ التحقق من التغييرات في البيانات إذا كانت الصفحة مرئية"""
        if self.isVisible():
            try:
                # يمكن إضافة منطق للتحقق من آخر وقت تحديث
                # للتأكد من أن البيانات محدثة
                pass
            except Exception as e:
                print(f"❌ [المراقبة] خطأ في التحقق من التغييرات: {e}")

    def showEvent(self, event):
        """✅ عند إظهار الصفحة، تأكد من تحديث البيانات"""
        super().showEvent(event)
        print("🔄 [عرض الصفحة] تحديث بيانات الإدارة...")
        self.load_items()
        self.update_total_capital()

    def _on_table_double_click(self, item):
        row = item.row()
        self.table.setCurrentCell(row, 1)
        self.open_edit_dialog()

    def keyPressEvent(self, event):
        focus = self.focusWidget()
        if (focus is self.table) or self.table.hasFocus() or self.table.viewport().hasFocus():
            k = event.key()
            if k == Qt.Key_Delete:
                self.delete_selected_item()
                return
            if k in (Qt.Key_Return, Qt.Key_Enter):
                self.open_edit_dialog()
                return
        super().keyPressEvent(event)

    def get_units(self):
        self._load_units_cache()
        return self.units_buy, self.units_sell

    def back_to_main(self):
        if hasattr(self.controller, "init_main_page"):
            self.controller.init_main_page()
        elif hasattr(self.controller, "show_main_page"):
            self.controller.show_main_page()

    def get_item_sell_units(self, item_id):
        """✅ جلب وحدات المبيع الخاصة بصنف معين"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("SELECT sell_unit FROM ItemSellUnits WHERE item_id=? ORDER BY sell_unit", (item_id,))
        units = [row[0] for row in c.fetchall()]
        conn.close()
        return units

    def send_to_reports_page(self, action, item_id, item_name):
        """✅ إرسال البيانات إلى صفحة التقارير"""
        try:
            if hasattr(self.controller, 'reports_page') and self.controller.reports_page is not None:
                # ✅ إرسال بيانات التعديل إلى صفحة التقارير
                report_data = {
                    'action': action,
                    'item_id': item_id,
                    'item_name': item_name,
                    'timestamp': datetime.now(),
                    'page': 'admin_page'
                }
                
                if hasattr(self.controller.reports_page, 'receive_admin_data'):
                    self.controller.reports_page.receive_admin_data(report_data)
                    print(f"✅ [التقارير] تم إرسال بيانات {action} للصنف {item_name} إلى صفحة التقارير")
                else:
                    print(f"⚠️ [التقارير] صفحة التقارير لا تحتوي على دالة receive_admin_data")
            else:
                print(f"⚠️ [التقارير] صفحة التقارير غير متاحة للإرسال")
        except Exception as e:
            print(f"❌ [التقارير] خطأ في إرسال البيانات إلى صفحة التقارير: {e}")


class ManageUnitsDialog(QDialog):
    def __init__(self, units_buy, units_sell, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.db_path = DB_PATH
        self.setWindowTitle("إدارة وحدات القياس")
        self.setMinimumWidth(600)
        
        layout = QFormLayout(self)

        unit_input = QLineEdit()
        unit_input.setFont(QFont("Arial", 16, QFont.Bold))
        add_btn = QPushButton("💾 إضافة وحدة")
        add_btn.setFont(QFont("Arial", 16, QFont.Bold))
        del_btn = QPushButton("🗑 حذف الوحدة المحددة")
        del_btn.setFont(QFont("Arial", 16, QFont.Bold))
        
        self.units_list = QListWidget()
        self.units_list.setFont(QFont("Arial", 14, QFont.Bold))

        def refresh():
            self.units_list.clear()
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            try:
                c.execute("SELECT DISTINCT unit FROM Units ORDER BY unit")
                for (unit,) in c.fetchall():
                    self.units_list.addItem(unit)
            except Exception:
                pass
            conn.close()

        def add_unit():
            name_str = unit_input.text().strip()
            if not name_str:
                QMessageBox.warning(self, "خطأ", "أدخل اسم وحدة صالح.")
                return
            
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            
            c.execute("INSERT INTO Units(unit, kind) SELECT ?, 'buy' WHERE NOT EXISTS (SELECT 1 FROM Units WHERE unit=? AND kind='buy')", 
                     (name_str, name_str))
            
            c.execute("INSERT INTO Units(unit, kind) SELECT ?, 'sell' WHERE NOT EXISTS (SELECT 1 FROM Units WHERE unit=? AND kind='sell')", 
                     (name_str, name_str))
            
            conn.commit()
            conn.close()
            
            refresh()
            unit_input.clear()
            
            if self.parent:
                self.parent._load_units_cache()
            
            QMessageBox.information(self, "تم", f"تمت إضافة الوحدة '{name_str}' بنجاح")

        def delete_unit():
            current_item = self.units_list.currentItem()
            if not current_item:
                QMessageBox.information(self, "ملاحظة", "اختر وحدة للحذف.")
                return
            
            unit_name = current_item.text()
            
            r = QMessageBox.question(self, "تأكيد", f"هل تريد حذف الوحدة '{unit_name}'؟", QMessageBox.Yes | QMessageBox.No)
            if r != QMessageBox.Yes:
                return
            
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            c.execute("DELETE FROM Units WHERE unit=?", (unit_name,))
            conn.commit()
            conn.close()
            
            refresh()
            
            if self.parent:
                self.parent._load_units_cache()

        add_btn.clicked.connect(add_unit)
        del_btn.clicked.connect(delete_unit)

        layout.addRow("اسم الوحدة:", unit_input)
        layout.addRow(add_btn)
        layout.addRow(del_btn)
        layout.addRow("الوحدات الحالية:", self.units_list)

        refresh()


class ItemDialog(QDialog):
    def __init__(self, units_buy, units_sell, parent=None, preset: dict = None):
        super().__init__(parent)
        self.setWindowTitle("إضافة / تعديل صنف")
        self.setMinimumWidth(700)
        self.units_buy = units_buy or []
        self.units_sell = units_sell or []
        self.preset = preset or {}

        main_layout = QVBoxLayout(self)
        
        self.setStyleSheet("""
            QDialog {
                font-weight: bold;
                font-size: 16px;
            }
            QLabel {
                font-size: 16px;
                font-weight: bold;
                color: white;
            }
            QLineEdit, QComboBox {
                font-size: 16px;
                font-weight: bold;
                padding: 12px;
                min-height: 25px;
            }
            QCheckBox {
                font-size: 14px;
                font-weight: bold;
                color: white;
            }
            QGroupBox {
                font-size: 18px;
                font-weight: bold;
                color: white;
                border: 2px solid #415A77;
                border-radius: 10px;
                margin-top: 12px;
                padding-top: 12px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 8px 0 8px;
            }
            QPushButton {
                font-size: 16px;
                font-weight: bold;
                padding: 12px;
            }
            QFormLayout QLabel {
                text-align: right;
                min-width: 150px;
            }
            QFormLayout QLineEdit, QFormLayout QComboBox, QFormLayout QGroupBox {
                min-width: 300px;
            }
        """)
        
        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignRight)  # ✅ محاذاة التسميات لليمين
        form.setFormAlignment(Qt.AlignRight)   # ✅ محاذاة النموذج لليمين
        
        font = QFont("Arial", 16, QFont.Bold)

        self.name_edit = QLineEdit()
        self.name_edit.setFont(font)
        form.addRow("اسم الصنف:", self.name_edit)

        self.buy_unit_combo = QComboBox()
        self.buy_unit_combo.setFont(QFont("Arial", 16, QFont.Bold))
        self.buy_unit_combo.addItems(self.units_buy)
        form.addRow("وحدة الشراء:", self.buy_unit_combo)

        # ✅ قسم وحدات المبيع المتعددة مع تحسين التصميم
        units_group = QGroupBox("وحدات المبيع المفرق")
        units_group.setFont(QFont("Arial", 18, QFont.Bold))
        
        units_layout = QVBoxLayout(units_group)
        
        self.sell_units_widget = QWidget()
        self.sell_units_layout = QVBoxLayout(self.sell_units_widget)
        self.sell_units_layout.setContentsMargins(12, 8, 12, 8)
        
        # ✅ صناديق اختيار لوحدات المبيع
        self.sell_units_checkboxes = []
        for unit in self.units_sell:
            cb = QCheckBox(unit)
            cb.setFont(QFont("Arial", 14, QFont.Bold))
            cb.setStyleSheet("QCheckBox { color: white; font-weight: bold; }")
            self.sell_units_layout.addWidget(cb)
            self.sell_units_checkboxes.append(cb)
        
        scroll_area = QScrollArea()
        scroll_area.setWidget(self.sell_units_widget)
        scroll_area.setMaximumHeight(160)
        scroll_area.setStyleSheet("QScrollArea { background-color: #1B263B; border-radius: 8px; }")
        
        units_layout.addWidget(scroll_area)
        form.addRow(units_group)

        self.buy_price_edit = QLineEdit()
        self.buy_price_edit.setFont(font)
        self.buy_price_edit.setPlaceholderText("مثال: 100000 أو 100 (دولار)")
        form.addRow("سعر الشراء:", self.buy_price_edit)

        self.sell_price_edit = QLineEdit()
        self.sell_price_edit.setFont(font)
        self.sell_price_edit.setPlaceholderText("سعر المبيع المفرق (اختياري)")
        form.addRow("سعر المبيع المفرق:", self.sell_price_edit)

        self.qty_edit = QLineEdit()
        self.qty_edit.setFont(font)
        self.qty_edit.setPlaceholderText("مثال: 0.5 أو 10")
        form.addRow("الكمية:", self.qty_edit)

        self.currency_combo = QComboBox()
        self.currency_combo.setFont(QFont("Arial", 16, QFont.Bold))
        self.currency_combo.addItems(["LBP", "USD"])
        form.addRow("العملة:", self.currency_combo)

        main_layout.addLayout(form)

        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.Save).setText("💾 حفظ")
        buttons.button(QDialogButtonBox.Cancel).setText("❌ إلغاء")
        buttons.button(QDialogButtonBox.Save).setFont(QFont("Arial", 16, QFont.Bold))
        buttons.button(QDialogButtonBox.Cancel).setFont(QFont("Arial", 16, QFont.Bold))
        main_layout.addWidget(buttons)

        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)

        # ✅ تحميل البيانات إذا كانت موجودة
        if self.preset:
            self.name_edit.setText(self.preset.get("name", ""))
            buy_u = self.preset.get("buy_unit", "")
            if buy_u and buy_u in self.units_buy:
                self.buy_unit_combo.setCurrentText(buy_u)
            self.buy_price_edit.setText(str(self.preset.get("buy_price", "")))
            self.sell_price_edit.setText(str(self.preset.get("sell_price", "")))
            self.qty_edit.setText(str(self.preset.get("quantity", "")))
            cur = self.preset.get("currency", "LBP").upper()
            if cur in ("LBP", "USD"):
                self.currency_combo.setCurrentText(cur)
            
            # ✅ تحميل وحدات المبيع الخاصة بالصنف
            preset_sell_units = self.preset.get("sell_units", [])
            for cb in self.sell_units_checkboxes:
                if cb.text() in preset_sell_units:
                    cb.setChecked(True)

        buttons.button(QDialogButtonBox.Save).setAutoDefault(True)
        buttons.button(QDialogButtonBox.Save).setDefault(True)

    def _on_accept(self):
        if not self.name_edit.text().strip():
            QMessageBox.warning(self, "خطأ", "أدخل اسم الصنف.")
            return
        try:
            _ = to_decimal_from_text(self.buy_price_edit.text())
            _ = to_decimal_from_text(self.qty_edit.text())
        except Exception:
            QMessageBox.warning(self, "خطأ", "الرجاء إدخال قيم رقمية صحيحة (مثال: 0.5 أو 100).")
            return
        self.accept()

    def get_data(self):
        # ✅ جمع وحدات المبيع المختارة
        selected_sell_units = []
        for cb in self.sell_units_checkboxes:
            if cb.isChecked():
                selected_sell_units.append(cb.text())
        
        # ✅ إذا لم يتم اختيار أي وحدة، نستخدم الوحدة الافتراضية
        if not selected_sell_units:
            selected_sell_units = [self.units_sell[0] if self.units_sell else "قطعة"]

        return {
            "name": self.name_edit.text().strip(),
            "buy_unit": self.buy_unit_combo.currentText(),
            "sell_unit": selected_sell_units[0],
            "buy_price": self.buy_price_edit.text().strip(),
            "sell_price": self.sell_price_edit.text().strip(),
            "quantity": self.qty_edit.text().strip(),
            "currency": self.currency_combo.currentText(),
            "sell_units": selected_sell_units
        }