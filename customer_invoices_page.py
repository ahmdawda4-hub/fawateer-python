import os
import json
import sqlite3
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
import uuid
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QLineEdit, QComboBox, QDialog,
    QMessageBox, QGroupBox, QFrame, QFormLayout,
    QDateEdit, QDoubleSpinBox, QDialogButtonBox,
    QSpinBox, QTextEdit, QScrollArea, QSplitter,
    QProgressBar, QFileDialog, QInputDialog
)
from PySide6.QtCore import Qt, QSize, QDate, QTimer
from PySide6.QtGui import QPixmap, QFont, QColor, QIntValidator, QDoubleValidator, QIcon, QPainter, QShortcut, QKeySequence
from pages.customer_payments_page import CustomerPaymentsPage 

DB_PATH = "chbib_materials.db"

# ✅ استيراد الصفحات من مجلد pages
print("✅ تحميل صفحة فواتير الزبون...")
# ✅ استيراد صفحة الدفعات
try:
    from customer_payments_page import CustomerPaymentsPage
    print("✅ تم تحميل صفحة الدفعات بنجاح")
except ImportError as e:
    print(f"❌ خطأ في تحميل صفحة الدفعات: {e}")

# ✅ استيراد صفحة الحجوزات
try:
    from pages.customer_reservations_page import CustomerReservationsPage
    print("✅ تم تحميل صفحة الحجوزات بنجاح")
except ImportError as e:
    print(f"❌ خطأ في تحميل صفحة الحجوزات: {e}")

class InvoiceTypeDialog(QDialog):
    """نافذة اختيار نوع الفاتورة"""
    def __init__(self, parent, customer_id, customer_name, phone_number):
        super().__init__(parent)
        self.parent = parent
        self.controller = parent  # ✅ هذا السطر الجديد - أضفته هنا
        self.customer_id = customer_id
        self.customer_name = customer_name
        self.phone_number = phone_number
        self.setup_ui()
        
    def setup_ui(self):
        self.setWindowTitle("اختر نوع الفاتورة")
        self.setFixedSize(500, 400)  # ✅ تكبير الحجم
        
        # ✅ خلفية كحلية داكنة
        self.setStyleSheet("""
            QDialog {
                background-color: #1e2a3a;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)
        
        # ✅ كلمة "اختر نوع الفاتورة" - إصلاح كامل للعربية
        title = QLabel("اختر نوع الفاتورة")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("""
            QLabel {
                color: #ffffff;
                font-size: 26px;
                font-weight: bold;
                font-family: 'Arial', 'Segoe UI';
                background-color: #2c3e50;
                padding: 20px;
                border: 3px solid #3498db;
                border-radius: 10px;
                margin-bottom: 20px;
            }
        """)
        title.setMinimumHeight(80)
        title.setWordWrap(True)
        layout.addWidget(title)
        
        # ✅ زر الفاتورة النقدية - إصلاح كامل للعربية
        cash_btn = QPushButton("نقدي")
        cash_btn.setMinimumHeight(80)
        cash_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: #ffffff;
                font-size: 26px;
                font-weight: bold;
                font-family: 'Arial', 'Segoe UI';
                border: 3px solid #2ecc71;
                border-radius: 10px;
                margin: 5px;
            }
            QPushButton:hover {
                background-color: #229954;
                border: 3px solid #27ae60;
            }
            QPushButton:pressed {
                background-color: #1e8449;
            }
        """)
        cash_btn.clicked.connect(lambda: self.select_type("نقدي"))
        layout.addWidget(cash_btn)
        
        # ✅ زر فاتورة التقسيط - إصلاح كامل للعربية
        installment_btn = QPushButton("تقسيط")
        installment_btn.setMinimumHeight(80)
        installment_btn.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: #ffffff;
                font-size: 26px;
                font-weight: bold;
                font-family: 'Arial', 'Segoe UI';
                border: 3px solid #ec7063;
                border-radius: 10px;
                margin: 5px;
            }
            QPushButton:hover {
                background-color: #c0392b;
                border: 3px solid #e74c3c;
            }
            QPushButton:pressed {
                background-color: #a93226;
            }
        """)
        installment_btn.clicked.connect(lambda: self.select_type("تقسيط"))
        layout.addWidget(installment_btn)
        
        # ✅ زر الإلغاء - إصلاح كامل للعربية
        cancel_btn = QPushButton("إلغاء")
        cancel_btn.setMinimumHeight(70)
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #95a5a6;
                color: #ffffff;
                font-size: 22px;
                font-weight: bold;
                font-family: 'Arial', 'Segoe UI';
                border: 2px solid #bdc3c7;
                border-radius: 8px;
                margin: 5px;
                margin-top: 20px;
            }
            QPushButton:hover {
                background-color: #7f8c8d;
                border: 2px solid #95a5a6;
            }
            QPushButton:pressed {
                background-color: #616a6b;
            }
        """)
        cancel_btn.clicked.connect(self.reject)
        layout.addWidget(cancel_btn)
        
        # ✅ إضافة مساحة مرنة لتحسين التخطيط
        layout.addStretch()
    
    def select_type(self, invoice_type):
        self.selected_type = invoice_type
        self.accept()
    
    def get_selected_type(self):
        return getattr(self, 'selected_type', None)

# ✅ ✅ ✅ إضافة كلاس نافذة الحجز الجديد
class ReservationDialog(QDialog):
    """نافذة إنشاء حجز جديد"""
    def __init__(self, parent, exchange_rate, reservation_number):
        super().__init__(parent)
        self.exchange_rate = exchange_rate
        self.reservation_number = reservation_number
        self.items = []
        self.products = self.load_products_from_database()
        self.setup_ui()
        self.setup_enter_shortcut()
    
    def setup_enter_shortcut(self):
        """✅ تعطيل زر Enter لإضافة الأصناف"""
        enter_shortcut = QShortcut(QKeySequence("Return"), self)
        enter_shortcut.setEnabled(False)
        enter_shortcut = QShortcut(QKeySequence("Enter"), self)
        enter_shortcut.setEnabled(False)
        
        self.disable_enter_on_lineedits()
    
    def disable_enter_on_lineedits(self):
        """✅ تعطيل زر Enter على جميع الحقول النصية"""
        for child in self.findChildren(QLineEdit):
            enter_shortcut = QShortcut(QKeySequence("Return"), child)
            enter_shortcut.setEnabled(False)
            enter_shortcut = QShortcut(QKeySequence("Enter"), child)
            enter_shortcut.setEnabled(False)
            
        for child in self.findChildren(QComboBox):
            enter_shortcut = QShortcut(QKeySequence("Return"), child)
            enter_shortcut.setEnabled(False)
            enter_shortcut = QShortcut(QKeySequence("Enter"), child)
            enter_shortcut.setEnabled(False)
            
        for child in self.findChildren(DateInput):
            enter_shortcut = QShortcut(QKeySequence("Return"), child)
            enter_shortcut.setEnabled(False)
            enter_shortcut = QShortcut(QKeySequence("Enter"), child)
            enter_shortcut.setEnabled(False)

    def load_products_from_database(self):
        """✅ تحميل الأصناف من قاعدة البيانات"""
        try:
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            
            c.execute("""
                SELECT 
                    id, name, buy_unit, sell_unit, buy_price, sell_price, 
                    quantity, currency 
                FROM Items 
                ORDER BY name
            """)
            
            products = []
            for row in c.fetchall():
                product = {
                    'id': row[0],
                    'name': row[1],
                    'buy_unit': row[2],
                    'sell_unit': row[3],
                    'buy_price': float(row[4]),
                    'sell_price': float(row[5]),
                    'stock': float(row[6]),
                    'currency': row[7]
                }
                
                # ✅ تحويل الأسعار بناءً على العملة وسعر الصرف الحالي
                if product['currency'].upper() == 'LBP':
                    product['buy_price_usd'] = product['buy_price'] / self.exchange_rate
                    product['sell_price_usd'] = product['sell_price'] / self.exchange_rate
                else:
                    product['buy_price_usd'] = product['buy_price']
                    product['sell_price_usd'] = product['sell_price']
                
                products.append(product)
            
            conn.close()
            return products
            
        except Exception as e:
            print(f"❌ خطأ في تحميل الأصناف من قاعدة البيانات: {e}")
            return []

    def get_item_sell_units(self, item_id):
        """✅ جلب وحدات المبيع الخاصة بصنف معين من قاعدة البيانات"""
        try:
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute("SELECT sell_unit FROM ItemSellUnits WHERE item_id=? ORDER BY sell_unit", (item_id,))
            units = [row[0] for row in c.fetchall()]
            conn.close()
            
            if not units:
                c.execute("SELECT sell_unit FROM Items WHERE id=?", (item_id,))
                default_unit = c.fetchone()
                if default_unit and default_unit[0]:
                    units = [default_unit[0]]
            
            return units if units else ["قطعة"]
            
        except Exception as e:
            print(f"❌ خطأ في جلب وحدات المبيع للصنف {item_id}: {e}")
            return ["قطعة"]

    def setup_ui(self):
        self.setWindowTitle(f"إضافة حجز - رقم: {self.reservation_number}")
        
        # ✅ خلفية كحلية داكنة
        self.setStyleSheet("""
            QDialog {
                background-color: #1e2a3a;
                border: 2px solid #34495e;
                border-radius: 10px;
            }
            QGroupBox {
                color: white;
                font-size: 16px;
                font-weight: bold;
                font-family: Arial;
                border: 2px solid #34495e;
                border-radius: 8px;
                background-color: rgba(30, 42, 58, 0.9);
                margin-top: 8px;
                padding: 10px;
            }
            QLabel {
                color: white;
                font-size: 16px;
                font-weight: bold;
                font-family: Arial;
            }
        """)
        
        layout = QVBoxLayout(self)
        
        # ✅ الهيدر مع العنوان والشعار
        header_layout = QHBoxLayout()
        
        title_label = QLabel(f"إضافة حجز - رقم: {self.reservation_number}")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 28px;
                font-weight: bold;
                background-color: transparent;
                padding: 15px;
                font-family: Arial;
            }
        """)
        
        logo_label = QLabel()
        logo_pixmap = QPixmap(r"C:\Users\User\Desktop\chbib1\icons\logo.png")
        if not logo_pixmap.isNull():
            logo_label.setPixmap(logo_pixmap.scaled(80, 80, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        logo_label.setAlignment(Qt.AlignRight)
        
        header_layout.addStretch()
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(logo_label)
        
        layout.addLayout(header_layout)
        
        # ✅ حقل التاريخ - ✅ استخدام DateInput الجديد
        date_group = QGroupBox("")
        date_layout = QHBoxLayout()
        
        date_label = QLabel("تاريخ الحجز:")
        date_label.setStyleSheet("color: white; font-size: 16px; font-weight: bold; font-family: Arial;")
        
        self.date_input = DateInput()
        self.date_input.setPlaceholderText("ابحث عن تاريخ")
        
        date_layout.addStretch()
        date_layout.addWidget(self.date_input)
        date_layout.addWidget(date_label)
        
        date_group.setLayout(date_layout)
        layout.addWidget(date_group)
        
        # معلومات العميل
        customer_group = QGroupBox("")
        customer_layout = QFormLayout()
        
        self.customer_name = QLineEdit()
        self.customer_name.setPlaceholderText("(اختياري) العميل اسم")
        self.customer_name.setStyleSheet("""
            QLineEdit {
                background-color: white; 
                color: black; 
                padding: 12px; 
                border-radius: 5px;
                font-size: 16px;
                border: 1px solid #bdc3c7;
                font-family: Arial;
                font-weight: bold;
                min-height: 35px;
            }
            QLineEdit:focus {
                border: 2px solid #3498db;
                background-color: #f8f9fa;
            }
        """)
        
        self.customer_phone = QLineEdit()
        self.customer_phone.setPlaceholderText("(اختياري) الهاتف رقم")
        self.customer_phone.setStyleSheet("""
            QLineEdit {
                background-color: white; 
                color: black; 
                padding: 12px; 
                border-radius: 5px;
                font-size: 16px;
                border: 1px solid #bdc3c7;
                font-family: Arial;
                font-weight: bold;
                min-height: 35px;
            }
            QLineEdit:focus {
                border: 2px solid #3498db;
                background-color: #f8f9fa;
            }
        """)
        phone_validator = QIntValidator(0, 999999999, self)
        self.customer_phone.setValidator(phone_validator)
        
        # ✅ تعديل المحاذاة: الحقول أولاً ثم النقطتين
        name_layout = QHBoxLayout()
        name_layout.addStretch()
        name_layout.addWidget(self.customer_name)
        name_layout.addWidget(QLabel("الاسم:"))
        
        phone_layout = QHBoxLayout()
        phone_layout.addStretch()
        phone_layout.addWidget(self.customer_phone)
        phone_layout.addWidget(QLabel("الهاتف:"))
        
        customer_layout.addRow(name_layout)
        customer_layout.addRow(phone_layout)
        customer_group.setLayout(customer_layout)
        layout.addWidget(customer_group)
        
        # إضافة الأصناف
        items_group = QGroupBox("")
        items_layout = QVBoxLayout()
        
        # عناصر التحكم
        control_layout = QHBoxLayout()
        
        self.product_combo = QComboBox()
        self.product_combo.setStyleSheet("""
            QComboBox {
                background-color: white; 
                color: black; 
                padding: 12px; 
                border-radius: 5px;
                font-size: 16px;
                border: 1px solid #bdc3c7;
                min-width: 200px;
                font-family: Arial;
                font-weight: bold;
                min-height: 35px;
            }
            QComboBox:focus {
                border: 2px solid #3498db;
                background-color: #f8f9fa;
            }
            QComboBox QAbstractItemView {
                background-color: white;
                color: black;
                selection-background-color: #3498db;
                selection-color: white;
                border: 1px solid #bdc3c7;
                font-family: Arial;
                font-weight: bold;
                font-size: 14px;
            }
        """)
        if self.products:
            self.product_combo.addItems([p['name'] for p in self.products])
        else:
            self.product_combo.addItems(["لا توجد أصناف - الرجاء إضافة أصناف من صفحة الإدارة"])
        self.product_combo.currentIndexChanged.connect(self.on_product_changed)
        
        # ✅ حقل وحدات المبيع
        self.unit_combo = QComboBox()
        self.unit_combo.setStyleSheet("""
            QComboBox {
                background-color: white; 
                color: black; 
                padding: 12px; 
                border-radius: 5px;
                font-size: 16px;
                border: 1px solid #bdc3c7;
                min-width: 140px;
                font-family: Arial;
                font-weight: bold;
                min-height: 35px;
            }
            QComboBox:focus {
                border: 2px solid #3498db;
                background-color: #f8f9fa;
            }
            QComboBox QAbstractItemView {
                background-color: white;
                color: black;
                selection-background-color: #3498db;
                selection-color: white;
                border: 1px solid #bdc3c7;
                font-family: Arial;
                font-weight: bold;
                font-size: 14px;
            }
        """)
        
        self.quantity_input = QLineEdit()
        self.quantity_input.setPlaceholderText("الكمية أدخل")
        self.quantity_input.setText("1")
        self.quantity_input.setStyleSheet("""
            QLineEdit {
                background-color: white; 
                color: black; 
                padding: 12px; 
                border-radius: 5px;
                font-size: 16px;
                border: 1px solid #bdc3c7;
                min-width: 120px;
                font-family: Arial;
                font-weight: bold;
                min-height: 35px;
            }
            QLineEdit:focus {
                border: 2px solid #3498db;
                background-color: #f8f9fa;
            }
        """)
        quantity_validator = QDoubleValidator(0.001, 10000, 3, self)
        self.quantity_input.setValidator(quantity_validator)
        self.quantity_input.textChanged.connect(self.on_quantity_changed)
        
        add_btn = QPushButton(" اضافة صنف ")
        add_btn.setStyleSheet("""
            QPushButton {
                background-color: white;
                color: #2c3e50;
                padding: 12px 25px;
                border: 2px solid #2c3e50;
                border-radius: 5px;
                font-size: 16px;
                font-weight: bold;
                font-family: Arial;
                min-height: 35px;
            }
            QPushButton:hover {
                background-color: #f8f9fa;
                border: 2px solid #34495e;
            }
        """)
        add_btn.clicked.connect(self.add_item)
        
        # ✅ تعديل المحاذاة: الحقول أولاً ثم التسميات
        control_layout.addStretch()
        control_layout.addWidget(self.product_combo)
        control_layout.addWidget(QLabel("الصنف:"))
        control_layout.addWidget(self.unit_combo)
        control_layout.addWidget(QLabel("المبيع وحدة:"))
        control_layout.addWidget(self.quantity_input)
        control_layout.addWidget(QLabel("الكمية:"))
        control_layout.addWidget(add_btn)
        
        items_layout.addLayout(control_layout)
        
        # جدول الأصناف
        table_layout = QVBoxLayout()
        
        self.items_table = QTableWidget()
        self.items_table.setColumnCount(7)
        self.items_table.setHorizontalHeaderLabels([
            "LBP المجموع", "$ المجموع", "LBP الوحدة سعر", "$ الوحدة سعر", "الكمية", "المبيع وحدة", "الصنف"
        ])
        
        self.items_table.setStyleSheet("""
            QTableWidget {
                background-color: white;
                border: 2px solid #2c3e50;
                border-radius: 8px;
                font-size: 14px;
                gridline-color: #bdc3c7;
                selection-background-color: #3498db;
                selection-color: black;
                font-family: Arial;
                font-weight: bold;
            }
            QHeaderView::section {
                background-color: #2c3e50;
                color: white;
                padding: 15px;
                border: none;
                font-weight: bold;
                font-size: 14px;
                font-family: Arial;
            }
            QTableWidget::item {
                padding: 12px;
                border-bottom: 1px solid #ecf0f1;
                font-size: 14px;
                color: #2c3e50;
                background-color: white;
                selection-background-color: #e3f2fd;
                selection-color: black;
                min-height: 45px;
                font-family: Arial;
                font-weight: bold;
            }
            QTableWidget::item:selected {
                background-color: #e3f2fd;
                color: black;
                border: 1px solid #3498db;
            }
            QTableWidget::item:focus {
                background-color: #e3f2fd;
                border: 1px solid #3498db;
                color: black;
            }
        """)
        
        self.items_table.setFocusPolicy(Qt.NoFocus)
        
        header = self.items_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)
        
        self.items_table.verticalHeader().setDefaultSectionSize(50)
        self.items_table.cellChanged.connect(self.on_cell_changed)
        
        # أزرار التحكم
        buttons_layout = QHBoxLayout()
        
        delete_item_btn = QPushButton("المحدد الصنف حذف 🗑️")
        delete_item_btn.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                padding: 12px 25px;
                border: none;
                border-radius: 5px;
                font-size: 16px;
                font-weight: bold;
                font-family: Arial;
                min-height: 35px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        delete_item_btn.clicked.connect(self.delete_selected_item)
        
        buttons_layout.addWidget(delete_item_btn)
        buttons_layout.addStretch()
        
        table_layout.addWidget(self.items_table)
        table_layout.addLayout(buttons_layout)
        
        items_layout.addLayout(table_layout)
        items_group.setLayout(items_layout)
        layout.addWidget(items_group)
        
        # المجاميع
        totals_layout = QHBoxLayout()
        
        self.total_usd = QLabel("0 $")
        self.total_usd.setStyleSheet("font-size: 20px; font-weight: bold; color: white; font-family: Arial;")
        
        self.total_lbp = QLabel("0 LBP")
        self.total_lbp.setStyleSheet("font-size: 20px; font-weight: bold; color: white; font-family: Arial;")
        
        totals_layout.addStretch()
        totals_layout.addWidget(QLabel("المجموع بالدولار:"))
        totals_layout.addWidget(self.total_usd)
        totals_layout.addWidget(QLabel("المجموع بالليرة:"))
        totals_layout.addWidget(self.total_lbp)
        
        layout.addLayout(totals_layout)
        
        # أزرار الحفظ والإلغاء
        button_layout = QHBoxLayout()
        
        save_btn = QPushButton("حفظ الحجز 💾")
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                padding: 15px 30px;
                border: none;
                border-radius: 6px;
                font-size: 18px;
                font-weight: bold;
                font-family: Arial;
                min-height: 40px;
                margin-top: 10px;
            }
            QPushButton:hover {
                background-color: #229954;
            }
        """)
        save_btn.clicked.connect(self.save_reservation)
        
        cancel_btn = QPushButton("❌ إلغاء")
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #95a5a6;
                color: white;
                padding: 15px 30px;
                border: none;
                border-radius: 6px;
                font-size: 18px;
                font-family: Arial;
                font-weight: bold;
                min-height: 40px;
                margin-top: 10px;
            }
            QPushButton:hover {
                background-color: #7f8c8d;
            }
        """)
        cancel_btn.clicked.connect(self.reject)
        
        button_layout.addWidget(save_btn)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
        
        # ✅ تحميل وحدات المبيع للصنف الأول عند فتح النافذة
        if self.products:
            self.load_sell_units_for_product(self.products[0]['id'])

    def on_product_changed(self):
        """✅ عند تغيير المنتج المحدد - تحميل وحدات المبيع الخاصة به"""
        product_index = self.product_combo.currentIndex()
        if product_index >= 0 and product_index < len(self.products):
            product = self.products[product_index]
            self.load_sell_units_for_product(product['id'])
        
        self.update_unit_price()

    def load_sell_units_for_product(self, product_id):
        """✅ تحميل وحدات المبيع الخاصة بصنف معين"""
        try:
            units = self.get_item_sell_units(product_id)
            
            self.unit_combo.clear()
            if units:
                self.unit_combo.addItems(units)
            else:
                self.unit_combo.addItems(["قطعة"])
            
        except Exception as e:
            print(f"❌ خطأ في تحميل وحدات الصنف {product_id}: {e}")
            self.unit_combo.clear()
            self.unit_combo.addItems(["قطعة"])

    def on_quantity_changed(self):
        """عند تغيير الكمية - تحديث الأسعار تلقائياً"""
        self.update_unit_price()

    def update_unit_price(self):
        """✅ تحديث سعر الوحدة بناءً على المنتج والكمية وسعر الصرف"""
        product_index = self.product_combo.currentIndex()
        if product_index >= 0 and product_index < len(self.products):
            product = self.products[product_index]
            quantity_text = self.quantity_input.text().strip()
            
            if quantity_text and quantity_text != '.':
                try:
                    quantity = float(quantity_text)
                    unit_price_usd_single = product['sell_price_usd'] * quantity
                    unit_price_lbp_single = unit_price_usd_single * self.exchange_rate
                except ValueError:
                    pass

    def on_cell_changed(self, row, column):
        """✅ تحديث تلقائي عند تعديل خلية في الجدول"""
        if row < 0 or row >= len(self.items):
            return
            
        if column == 2:  # عمود الكمية
            try:
                quantity_item = self.items_table.item(row, column)
                if quantity_item:
                    new_quantity_text = quantity_item.text().strip()
                    if not new_quantity_text:
                        return
                        
                    new_quantity = float(new_quantity_text)
                    old_quantity = self.items[row]['quantity']
                    
                    self.items[row]['quantity'] = new_quantity
                    
                    product = self.get_product_by_name(self.items[row]['product_name'])
                    if product:
                        unit_price_usd_single = product['sell_price_usd']
                        unit_price_lbp_single = unit_price_usd_single * self.exchange_rate
                        
                        total_usd = unit_price_usd_single * new_quantity
                        total_lbp = unit_price_lbp_single * new_quantity
                        
                        self.items[row]['unit_price_usd'] = unit_price_usd_single
                        self.items[row]['unit_price_lbp'] = unit_price_lbp_single
                        self.items[row]['total_usd'] = total_usd
                        self.items[row]['total_lbp'] = total_lbp
                        
                        self.update_table_row(row)
                        self.calculate_totals()
                        
            except ValueError:
                self.items_table.blockSignals(True)
                self.items_table.item(row, column).setText(str(self.items[row]['quantity']))
                self.items_table.blockSignals(False)
        
        elif column == 3:  # ✅ عمود سعر الوحدة $ - التعديل اليدوي
            try:
                price_item = self.items_table.item(row, column)
                if price_item:
                    new_price_text = price_item.text().replace('$', '').strip()
                    if not new_price_text:
                        return
                        
                    new_price = float(new_price_text)
                    old_price = self.items[row]['unit_price_usd']
                    
                    self.items[row]['unit_price_usd'] = new_price
                    self.items[row]['unit_price_lbp'] = new_price * self.exchange_rate
                    
                    quantity = self.items[row]['quantity']
                    self.items[row]['total_usd'] = new_price * quantity
                    self.items[row]['total_lbp'] = (new_price * self.exchange_rate) * quantity
                    
                    self.update_table_row(row)
                    self.calculate_totals()
                    
            except ValueError:
                self.items_table.blockSignals(True)
                self.items_table.item(row, column).setText(f"{self.items[row]['unit_price_usd']:.3f} $")
                self.items_table.blockSignals(False)

    def get_product_by_name(self, product_name):
        """الحصول على بيانات المنتج بالاسم"""
        for product in self.products:
            if product['name'] == product_name:
                return product
        return None

    def check_stock_availability(self, product_name, quantity):
        """التحقق من توفر المخزون"""
        for product in self.products:
            if product['name'] == product_name:
                if quantity > product['stock']:
                    reply = self.show_message("المخزون تحذير", 
                        f"المتاح المخزون ({product['stock']}) {product_name} لأصناف ({quantity}) المطلوبة الكمية تتجاوز",
                        "warning", True)
                    return reply == QMessageBox.Yes
                return True
        return False

    def add_item(self):
        """✅ ✅ ✅ إضافة صنف إلى الحجز مع وحدة المبيع المحددة"""
        try:
            product_index = self.product_combo.currentIndex()
            if product_index < 0 or product_index >= len(self.products):
                self.show_message("تحذير", "صحيح صنف اختيار يرجى", "warning")
                return
            
            product = self.products[product_index]
            unit = self.unit_combo.currentText()
            quantity_text = self.quantity_input.text().strip()
            
            if not quantity_text:
                self.show_message("تحذير", "كمية إدخال يرجى", "warning")
                return
            
            try:
                quantity = float(quantity_text)
            except ValueError:
                self.show_message("تحذير", "صحيحة كمية إدخال يرجى", "warning")
                return
            
            if quantity <= 0:
                self.show_message("تحذير", "صحيحة كمية إدخال يرجى", "warning")
                return
            
            if not self.check_stock_availability(product['name'], quantity):
                return
            
            unit_price_usd_single = product['sell_price_usd']
            unit_price_lbp_single = unit_price_usd_single * self.exchange_rate
            
            total_usd = unit_price_usd_single * quantity
            total_lbp = unit_price_lbp_single * quantity
            
            item = {
                'product_name': product['name'],
                'unit': unit,
                'quantity': quantity,
                'unit_price_usd': unit_price_usd_single,
                'unit_price_lbp': unit_price_lbp_single,
                'total_usd': total_usd,
                'total_lbp': total_lbp,
                'product_id': product['id']
            }
            
            self.items.append(item)
            self.update_items_table()
            self.calculate_totals()
            
            self.quantity_input.setText("1")
            
        except Exception as e:
            self.show_message("خطأ", f"خطأ حدث: {e}", "error")

    def delete_selected_item(self):
        """✅ حذف الصنف المحدد من الجدول"""
        selected_row = self.items_table.currentRow()
        if selected_row == -1:
            self.show_message("تحذير", "للحذف صنف تحديد يرجى", "warning")
            return
            
        if selected_row >= 0 and selected_row < len(self.items):
            self.items.pop(selected_row)
            self.update_items_table()
            self.calculate_totals()
            self.show_message("نجاح", "✅ بنجاح الصنف حذف تم", "info")
    
    def update_items_table(self):
        """✅ ✅ ✅ تحديث جدول الأصناف مع عرض وحدة المبيع"""
        self.items_table.blockSignals(True)
        
        self.items_table.setRowCount(len(self.items))
        
        for row, item in enumerate(self.items):
            quantity_text = f"{int(item['quantity'])}" if item['quantity'] == int(item['quantity']) else f"{item['quantity']:.3f}"
            unit_price_usd_text = f"{int(item['unit_price_usd'])}" if item['unit_price_usd'] == int(item['unit_price_usd']) else f"{item['unit_price_usd']:.3f}"
            unit_price_lbp_text = f"{int(item['unit_price_lbp'])}" if item['unit_price_lbp'] == int(item['unit_price_lbp']) else f"{item['unit_price_lbp']:.0f}"
            total_usd_text = f"{int(item['total_usd'])}" if item['total_usd'] == int(item['total_usd']) else f"{item['total_usd']:.2f}"
            total_lbp_text = f"{int(item['total_lbp'])}" if item['total_lbp'] == int(item['total_lbp']) else f"{item['total_lbp']:.0f}"
            
            product_item = QTableWidgetItem(item['product_name'])
            product_item.setBackground(QColor("white"))
            self.items_table.setItem(row, 6, product_item)
            
            unit_item = QTableWidgetItem(item['unit'])
            unit_item.setFlags(unit_item.flags() & ~Qt.ItemIsEditable)
            unit_item.setBackground(QColor("white"))
            self.items_table.setItem(row, 5, unit_item)
            
            quantity_item = QTableWidgetItem(quantity_text)
            quantity_item.setForeground(QColor("#2c3e50"))
            quantity_item.setBackground(QColor("white"))
            quantity_item.setFont(QFont("Arial", 12, QFont.Bold))
            self.items_table.setItem(row, 4, quantity_item)
            
            unit_price_usd_item = QTableWidgetItem(f"{unit_price_usd_text} $")
            unit_price_usd_item.setForeground(QColor("#2c3e50"))
            unit_price_usd_item.setBackground(QColor("white"))
            unit_price_usd_item.setFont(QFont("Arial", 12, QFont.Bold))
            self.items_table.setItem(row, 3, unit_price_usd_item)
            
            unit_price_lbp_item = QTableWidgetItem(f"{unit_price_lbp_text} LBP")
            unit_price_lbp_item.setFlags(unit_price_lbp_item.flags() & ~Qt.ItemIsEditable)
            unit_price_lbp_item.setBackground(QColor("white"))
            self.items_table.setItem(row, 2, unit_price_lbp_item)
            
            total_usd_item = QTableWidgetItem(f"{total_usd_text} $")
            total_usd_item.setFlags(total_usd_item.flags() & ~Qt.ItemIsEditable)
            total_usd_item.setBackground(QColor("white"))
            self.items_table.setItem(row, 1, total_usd_item)
            
            total_lbp_item = QTableWidgetItem(f"{total_lbp_text} LBP")
            total_lbp_item.setFlags(total_lbp_item.flags() & ~Qt.ItemIsEditable)
            total_lbp_item.setBackground(QColor("white"))
            self.items_table.setItem(row, 0, total_lbp_item)
        
        self.items_table.blockSignals(False)
    
    def update_table_row(self, row):
        """تحديث صف معين في الجدول"""
        if row < 0 or row >= len(self.items):
            return
            
        item = self.items[row]
        
        quantity_text = f"{int(item['quantity'])}" if item['quantity'] == int(item['quantity']) else f"{item['quantity']:.3f}"
        unit_price_usd_text = f"{int(item['unit_price_usd'])}" if item['unit_price_usd'] == int(item['unit_price_usd']) else f"{item['unit_price_usd']:.3f}"
        unit_price_lbp_text = f"{int(item['unit_price_lbp'])}" if item['unit_price_lbp'] == int(item['unit_price_lbp']) else f"{item['unit_price_lbp']:.0f}"
        total_usd_text = f"{int(item['total_usd'])}" if item['total_usd'] == int(item['total_usd']) else f"{item['total_usd']:.2f}"
        total_lbp_text = f"{int(item['total_lbp'])}" if item['total_lbp'] == int(item['total_lbp']) else f"{item['total_lbp']:.0f}"
        
        self.items_table.item(row, 4).setText(quantity_text)
        self.items_table.item(row, 3).setText(f"{unit_price_usd_text} $")
        self.items_table.item(row, 2).setText(f"{unit_price_lbp_text} LBP")
        self.items_table.item(row, 1).setText(f"{total_usd_text} $")
        self.items_table.item(row, 0).setText(f"{total_lbp_text} LBP")
    
    def calculate_totals(self):
        """حساب المجاميع تلقائياً"""
        total_usd = sum(item['total_usd'] for item in self.items)
        total_lbp = sum(item['total_lbp'] for item in self.items)
        
        usd_text = f"{int(total_usd)} $" if total_usd == int(total_usd) else f"{total_usd:.2f} $"
        lbp_text = f"{int(total_lbp)} LBP" if total_lbp == int(total_lbp) else f"{total_lbp:.0f} LBP"
        
        self.total_usd.setText(usd_text)
        self.total_lbp.setText(lbp_text)
    
    def save_reservation(self):
        """✅ حفظ الحجز في صفحة الحجوزات"""
        if not self.items:
            self.show_message("تحذير", "الحجز لأصناف إضافة يرجى", "warning")
            return
        
        try:
            # ✅ التحقق من صحة التاريخ
            if not self.date_input.validate_date():
                self.show_message("تحذير", "صحيح تاريخ إدخال يرجى (yyyy-mm-dd أو yyyy/mm/dd)", "warning")
                return
            
            total_usd = sum(item['total_usd'] for item in self.items)
            total_lbp = sum(item['total_lbp'] for item in self.items)
            
            reservation_data = {
                'reservation_number': self.reservation_number,
                'customer_name': self.customer_name.text().strip() or 'محدد غير',
                'customer_phone': self.customer_phone.text().strip() or 'محدد غير',
                'type': 'حجز',
                'items': self.items,
                'total_usd': total_usd,
                'total_lbp': total_lbp,
                'exchange_rate': self.exchange_rate,
                'date': self.date_input.get_date(),
                'reservation_uuid': str(uuid.uuid4())
            }
            
            # ✅ حفظ الحجز في صفحة الحجوزات
            self.save_reservation_to_reservations_page(reservation_data)
            
            self.show_message("نجاح", "✅ تم حفظ الحجز بنجاح", "info")
            self.accept()
            
        except Exception as e:
            self.show_message("خطأ", f"في الحفظ خطأ حدث: {e}", "error")
    
    def save_reservation_to_reservations_page(self, reservation_data):
        """✅ حفظ الحجز في صفحة الحجوزات"""
        try:
            reservations_file = "data/customer_reservations.json"
            
            # ✅ التأكد من وجود المجلد والملف
            os.makedirs(os.path.dirname(reservations_file), exist_ok=True)
            
            reservations = []
            if os.path.exists(reservations_file):
                try:
                    with open(reservations_file, 'r', encoding='utf-8') as f:
                        reservations = json.load(f)
                except:
                    reservations = []
            
            # ✅ إضافة الحجز الجديد
            reservations.append(reservation_data)
            
            # ✅ حفظ الملف
            with open(reservations_file, 'w', encoding='utf-8') as f:
                json.dump(reservations, f, ensure_ascii=False, indent=2)
                
            print(f"✅ تم حفظ الحجز في customer_reservations.json:")
            print(f"   - رقم الحجز: {reservation_data['reservation_number']}")
            print(f"   - الزبون: {reservation_data['customer_name']}")
            print(f"   - عدد الأصناف: {len(reservation_data['items'])}")
            print(f"   - الإجمالي: {reservation_data['total_usd']} $")
                
        except Exception as e:
            print(f"❌ خطأ في حفظ الحجز في صفحة الحجوزات: {e}")
            raise
    
    def show_message(self, title, message, type="info", show_buttons=False):
        """✅ عرض رسائل للمستخدم"""
        msg = QMessageBox(self)
        msg.setWindowTitle(title)
        msg.setText(message)
        
        msg.setStyleSheet("""
            QMessageBox {
                background-color: #1e2a3a;
            }
            QMessageBox QLabel {
                color: white;
                font-size: 16px;
                font-weight: bold;
                font-family: Arial;
            }
            QMessageBox QPushButton {
                background-color: #3498db;
                color: white;
                padding: 10px 20px;
                border: none;
                border-radius: 5px;
                font-size: 16px;
                font-weight: bold;
                font-family: Arial;
                min-width: 100px;
            }
            QMessageBox QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        
        if type == "warning":
            msg.setIcon(QMessageBox.Warning)
        elif type == "error":
            msg.setIcon(QMessageBox.Critical)
        elif type == "question":
            msg.setIcon(QMessageBox.Question)
            msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
            msg.setDefaultButton(QMessageBox.No)
        else:
            msg.setIcon(QMessageBox.Information)
            
        if show_buttons and type == "question":
            return msg.exec()
        else:
            msg.exec()
            return None

# ✅ ✅ ✅ إضافة كلاس نافذة السحب الجديد
class WithdrawalDialog(QDialog):
    """نافذة سحب أصناف من الحجوزات"""
    def __init__(self, parent, exchange_rate, invoice_number, customer_name, customer_phone):
        super().__init__(parent)
        self.exchange_rate = exchange_rate
        self.invoice_number = invoice_number
        self.customer_name = customer_name
        self.customer_phone = customer_phone
        self.reserved_items = self.load_customer_reservations()
        self.withdrawal_items = []
        self.setup_ui()
    
    def load_customer_reservations(self):
        """✅ تحميل حجوزات الزبون"""
        try:
            reservations_file = "data/customer_reservations.json"
            if not os.path.exists(reservations_file):
                return []
            
            with open(reservations_file, 'r', encoding='utf-8') as f:
                reservations = json.load(f)
            
            customer_reservations = []
            for reservation in reservations:
                if (reservation.get('customer_name') == self.customer_name and 
                    reservation.get('customer_phone') == self.customer_phone):
                    
                    for item in reservation.get('items', []):
                        # ✅ إضافة معلومات الحجز إلى كل صنف
                        item_with_reservation = item.copy()
                        item_with_reservation['reservation_number'] = reservation.get('reservation_number')
                        item_with_reservation['reservation_date'] = reservation.get('date')
                        item_with_reservation['reservation_uuid'] = reservation.get('reservation_uuid')
                        item_with_reservation['available_quantity'] = item['quantity']  # الكمية المتاحة للسحب
                        
                        customer_reservations.append(item_with_reservation)
            
            return customer_reservations
            
        except Exception as e:
            print(f"❌ خطأ في تحميل حجوزات الزبون: {e}")
            return []
    
    def setup_ui(self):
        self.setWindowTitle(f"سحب من الحجوزات - فاتورة: {self.invoice_number}")
        
        # ✅ خلفية كحلية داكنة
        self.setStyleSheet("""
            QDialog {
                background-color: #1e2a3a;
                border: 2px solid #34495e;
                border-radius: 10px;
            }
            QGroupBox {
                color: white;
                font-size: 16px;
                font-weight: bold;
                font-family: Arial;
                border: 2px solid #34495e;
                border-radius: 8px;
                background-color: rgba(30, 42, 58, 0.9);
                margin-top: 8px;
                padding: 10px;
            }
            QLabel {
                color: white;
                font-size: 16px;
                font-weight: bold;
                font-family: Arial;
            }
        """)
        
        layout = QVBoxLayout(self)
        
        # ✅ الهيدر مع العنوان
        header_layout = QHBoxLayout()
        
        title_label = QLabel(f"سحب من الحجوزات - فاتورة: {self.invoice_number}")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 24px;
                font-weight: bold;
                background-color: transparent;
                padding: 15px;
                font-family: Arial;
            }
        """)
        
        header_layout.addWidget(title_label)
        layout.addLayout(header_layout)
        
        if not self.reserved_items:
            # ✅ إذا لم يكن هناك حجوزات
            no_reservations_label = QLabel("⚠️ لا توجد حجوزات لهذا الزبون")
            no_reservations_label.setStyleSheet("""
                QLabel {
                    color: #e74c3c;
                    font-size: 18px;
                    font-weight: bold;
                    background-color: transparent;
                    padding: 20px;
                    font-family: Arial;
                    text-align: center;
                }
            """)
            layout.addWidget(no_reservations_label)
            
            # زر الإغلاق
            close_btn = QPushButton("إغلاق")
            close_btn.setStyleSheet("""
                QPushButton {
                    background-color: #95a5a6;
                    color: white;
                    padding: 15px 30px;
                    border: none;
                    border-radius: 6px;
                    font-size: 18px;
                    font-family: Arial;
                    font-weight: bold;
                    min-height: 40px;
                }
                QPushButton:hover {
                    background-color: #7f8c8d;
                }
            """)
            close_btn.clicked.connect(self.reject)
            layout.addWidget(close_btn)
            
            return
        
        # ✅ عرض الأصناف المحجوزة
        reservations_group = QGroupBox("الأصناف المحجوزة المتاحة للسحب")
        reservations_layout = QVBoxLayout()
        
        self.reservations_table = QTableWidget()
        self.reservations_table.setColumnCount(6)
        self.reservations_table.setHorizontalHeaderLabels([
            "الكمية المتاحة", "LBP الوحدة سعر", "$ الوحدة سعر", "المبيع وحدة", "الصنف", "رقم الحجز"
        ])
        
        self.reservations_table.setStyleSheet("""
            QTableWidget {
                background-color: white;
                border: 2px solid #2c3e50;
                border-radius: 8px;
                font-size: 14px;
                gridline-color: #bdc3c7;
                selection-background-color: #3498db;
                selection-color: black;
                font-family: Arial;
                font-weight: bold;
            }
            QHeaderView::section {
                background-color: #2c3e50;
                color: white;
                padding: 12px;
                border: none;
                font-weight: bold;
                font-size: 14px;
                font-family: Arial;
            }
            QTableWidget::item {
                padding: 10px;
                border-bottom: 1px solid #ecf0f1;
                font-size: 14px;
                color: #2c3e50;
                background-color: white;
                selection-background-color: #e3f2fd;
                selection-color: black;
                min-height: 40px;
                font-family: Arial;
                font-weight: bold;
            }
        """)
        
        self.reservations_table.setRowCount(len(self.reserved_items))
        
        for row, item in enumerate(self.reserved_items):
            # رقم الحجز
            reservation_item = QTableWidgetItem(str(item.get('reservation_number', '')))
            reservation_item.setBackground(QColor("white"))
            self.reservations_table.setItem(row, 5, reservation_item)
            
            # الصنف
            product_item = QTableWidgetItem(item['product_name'])
            product_item.setBackground(QColor("white"))
            self.reservations_table.setItem(row, 4, product_item)
            
            # وحدة المبيع
            unit_item = QTableWidgetItem(item['unit'])
            unit_item.setBackground(QColor("white"))
            self.reservations_table.setItem(row, 3, unit_item)
            
            # سعر الوحدة $
            unit_price_usd_text = f"{int(item['unit_price_usd'])}" if item['unit_price_usd'] == int(item['unit_price_usd']) else f"{item['unit_price_usd']:.3f}"
            unit_price_usd_item = QTableWidgetItem(f"{unit_price_usd_text} $")
            unit_price_usd_item.setBackground(QColor("white"))
            self.reservations_table.setItem(row, 2, unit_price_usd_item)
            
            # سعر الوحدة LBP
            unit_price_lbp_text = f"{int(item['unit_price_lbp'])}" if item['unit_price_lbp'] == int(item['unit_price_lbp']) else f"{item['unit_price_lbp']:.0f}"
            unit_price_lbp_item = QTableWidgetItem(f"{unit_price_lbp_text} LBP")
            unit_price_lbp_item.setBackground(QColor("white"))
            self.reservations_table.setItem(row, 1, unit_price_lbp_item)
            
            # الكمية المتاحة
            available_qty_text = f"{int(item['available_quantity'])}" if item['available_quantity'] == int(item['available_quantity']) else f"{item['available_quantity']:.3f}"
            available_qty_item = QTableWidgetItem(available_qty_text)
            available_qty_item.setBackground(QColor("white"))
            self.reservations_table.setItem(row, 0, available_qty_item)
        
        self.reservations_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.reservations_table.setSelectionBehavior(QTableWidget.SelectRows)
        
        reservations_layout.addWidget(self.reservations_table)
        reservations_group.setLayout(reservations_layout)
        layout.addWidget(reservations_group)
        
        # ✅ عناصر التحكم للسحب
        control_group = QGroupBox("إعدادات السحب")
        control_layout = QHBoxLayout()
        
        self.withdrawal_quantity = QLineEdit()
        self.withdrawal_quantity.setPlaceholderText("الكمية المسحوبة")
        self.withdrawal_quantity.setStyleSheet("""
            QLineEdit {
                background-color: white; 
                color: black; 
                padding: 12px; 
                border-radius: 5px;
                font-size: 16px;
                border: 1px solid #bdc3c7;
                min-width: 120px;
                font-family: Arial;
                font-weight: bold;
                min-height: 35px;
            }
            QLineEdit:focus {
                border: 2px solid #3498db;
                background-color: #f8f9fa;
            }
        """)
        quantity_validator = QDoubleValidator(0.001, 10000, 3, self)
        self.withdrawal_quantity.setValidator(quantity_validator)
        
        add_withdrawal_btn = QPushButton("إضافة للسحب")
        add_withdrawal_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                padding: 12px 25px;
                border: none;
                border-radius: 5px;
                font-size: 16px;
                font-weight: bold;
                font-family: Arial;
                min-height: 35px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        add_withdrawal_btn.clicked.connect(self.add_to_withdrawal)
        
        control_layout.addWidget(QLabel("الكمية المسحوبة:"))
        control_layout.addWidget(self.withdrawal_quantity)
        control_layout.addWidget(add_withdrawal_btn)
        control_layout.addStretch()
        
        control_group.setLayout(control_layout)
        layout.addWidget(control_group)
        
        # ✅ جدول الأصناف المسحوبة
        withdrawal_group = QGroupBox("الأصناف المسحوبة")
        withdrawal_layout = QVBoxLayout()
        
        self.withdrawal_table = QTableWidget()
        self.withdrawal_table.setColumnCount(6)
        self.withdrawal_table.setHorizontalHeaderLabels([
            "LBP المجموع", "$ المجموع", "الكمية المسحوبة", "الصنف", "رقم الحجز", "إجراء"
        ])
        
        self.withdrawal_table.setStyleSheet("""
            QTableWidget {
                background-color: white;
                border: 2px solid #2c3e50;
                border-radius: 8px;
                font-size: 14px;
                gridline-color: #bdc3c7;
                font-family: Arial;
                font-weight: bold;
            }
            QHeaderView::section {
                background-color: #2c3e50;
                color: white;
                padding: 12px;
                border: none;
                font-weight: bold;
                font-size: 14px;
                font-family: Arial;
            }
            QTableWidget::item {
                padding: 10px;
                border-bottom: 1px solid #ecf0f1;
                font-size: 14px;
                color: #2c3e50;
                background-color: white;
                min-height: 40px;
                font-family: Arial;
                font-weight: bold;
            }
        """)
        
        withdrawal_layout.addWidget(self.withdrawal_table)
        withdrawal_group.setLayout(withdrawal_layout)
        layout.addWidget(withdrawal_group)
        
        # ✅ المجاميع
        totals_layout = QHBoxLayout()
        
        self.withdrawal_total_usd = QLabel("0 $")
        self.withdrawal_total_usd.setStyleSheet("font-size: 18px; font-weight: bold; color: white; font-family: Arial;")
        
        self.withdrawal_total_lbp = QLabel("0 LBP")
        self.withdrawal_total_lbp.setStyleSheet("font-size: 18px; font-weight: bold; color: white; font-family: Arial;")
        
        totals_layout.addStretch()
        totals_layout.addWidget(QLabel("المجموع بالدولار:"))
        totals_layout.addWidget(self.withdrawal_total_usd)
        totals_layout.addWidget(QLabel("المجموع بالليرة:"))
        totals_layout.addWidget(self.withdrawal_total_lbp)
        
        layout.addLayout(totals_layout)
        
        # ✅ أزرار الحفظ والإلغاء
        button_layout = QHBoxLayout()
        
        save_btn = QPushButton("حفظ السحب 💾")
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                padding: 15px 30px;
                border: none;
                border-radius: 6px;
                font-size: 18px;
                font-weight: bold;
                font-family: Arial;
                min-height: 40px;
            }
            QPushButton:hover {
                background-color: #229954;
            }
        """)
        save_btn.clicked.connect(self.save_withdrawal)
        
        cancel_btn = QPushButton("❌ إلغاء")
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #95a5a6;
                color: white;
                padding: 15px 30px;
                border: none;
                border-radius: 6px;
                font-size: 18px;
                font-family: Arial;
                font-weight: bold;
                min-height: 40px;
            }
            QPushButton:hover {
                background-color: #7f8c8d;
            }
        """)
        cancel_btn.clicked.connect(self.reject)
        
        button_layout.addWidget(save_btn)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
    
    def add_to_withdrawal(self):
        """✅ إضافة صنف إلى قائمة السحب"""
        selected_row = self.reservations_table.currentRow()
        if selected_row < 0:
            self.show_message("تحذير", "⚠️ يرجى اختيار صنف من الحجوزات", "warning")
            return
        
        quantity_text = self.withdrawal_quantity.text().strip()
        if not quantity_text:
            self.show_message("تحذير", "⚠️ يرجى إدخال الكمية المسحوبة", "warning")
            return
        
        try:
            withdrawal_quantity = float(quantity_text)
            if withdrawal_quantity <= 0:
                self.show_message("تحذير", "⚠️ يرجى إدخال كمية صحيحة", "warning")
                return
            
            selected_item = self.reserved_items[selected_row]
            available_quantity = selected_item['available_quantity']
            
            if withdrawal_quantity > available_quantity:
                self.show_message("تحذير", f"⚠️ الكمية المسحوبة ({withdrawal_quantity}) تتجاوز الكمية المتاحة ({available_quantity})", "warning")
                return
            
            # ✅ إنشاء عنصر السحب
            withdrawal_item = {
                'product_name': selected_item['product_name'],
                'unit': selected_item['unit'],
                'quantity': withdrawal_quantity,
                'unit_price_usd': selected_item['unit_price_usd'],
                'unit_price_lbp': selected_item['unit_price_lbp'],
                'total_usd': selected_item['unit_price_usd'] * withdrawal_quantity,
                'total_lbp': selected_item['unit_price_lbp'] * withdrawal_quantity,
                'product_id': selected_item['product_id'],
                'reservation_number': selected_item['reservation_number'],
                'reservation_uuid': selected_item['reservation_uuid'],
                'original_quantity': selected_item['quantity']  # الكمية الأصلية في الحجز
            }
            
            # ✅ إضافة إلى قائمة السحب
            self.withdrawal_items.append(withdrawal_item)
            
            # ✅ تحديث الكمية المتاحة في القائمة
            self.reserved_items[selected_row]['available_quantity'] -= withdrawal_quantity
            
            # ✅ إذا أصبحت الكمية المتاحة صفر، إزالة الصنف من القائمة
            if self.reserved_items[selected_row]['available_quantity'] <= 0:
                self.reserved_items.pop(selected_row)
            
            # ✅ تحديث الواجهة
            self.update_reservations_table()
            self.update_withdrawal_table()
            self.calculate_totals()
            
            self.withdrawal_quantity.clear()
            
        except ValueError:
            self.show_message("تحذير", "⚠️ يرجى إدخال كمية صحيحة", "warning")
    
    def update_reservations_table(self):
        """✅ تحديث جدول الحجوزات"""
        self.reservations_table.setRowCount(len(self.reserved_items))
        
        for row, item in enumerate(self.reserved_items):
            # رقم الحجز
            reservation_item = QTableWidgetItem(str(item.get('reservation_number', '')))
            reservation_item.setBackground(QColor("white"))
            self.reservations_table.setItem(row, 5, reservation_item)
            
            # الصنف
            product_item = QTableWidgetItem(item['product_name'])
            product_item.setBackground(QColor("white"))
            self.reservations_table.setItem(row, 4, product_item)
            
            # وحدة المبيع
            unit_item = QTableWidgetItem(item['unit'])
            unit_item.setBackground(QColor("white"))
            self.reservations_table.setItem(row, 3, unit_item)
            
            # سعر الوحدة $
            unit_price_usd_text = f"{int(item['unit_price_usd'])}" if item['unit_price_usd'] == int(item['unit_price_usd']) else f"{item['unit_price_usd']:.3f}"
            unit_price_usd_item = QTableWidgetItem(f"{unit_price_usd_text} $")
            unit_price_usd_item.setBackground(QColor("white"))
            self.reservations_table.setItem(row, 2, unit_price_usd_item)
            
            # سعر الوحدة LBP
            unit_price_lbp_text = f"{int(item['unit_price_lbp'])}" if item['unit_price_lbp'] == int(item['unit_price_lbp']) else f"{item['unit_price_lbp']:.0f}"
            unit_price_lbp_item = QTableWidgetItem(f"{unit_price_lbp_text} LBP")
            unit_price_lbp_item.setBackground(QColor("white"))
            self.reservations_table.setItem(row, 1, unit_price_lbp_item)
            
            # الكمية المتاحة
            available_qty_text = f"{int(item['available_quantity'])}" if item['available_quantity'] == int(item['available_quantity']) else f"{item['available_quantity']:.3f}"
            available_qty_item = QTableWidgetItem(available_qty_text)
            available_qty_item.setBackground(QColor("white"))
            self.reservations_table.setItem(row, 0, available_qty_item)
    
    def update_withdrawal_table(self):
        """✅ تحديث جدول السحب"""
        self.withdrawal_table.setRowCount(len(self.withdrawal_items))
        
        for row, item in enumerate(self.withdrawal_items):
            # رقم الحجز
            reservation_item = QTableWidgetItem(str(item.get('reservation_number', '')))
            reservation_item.setBackground(QColor("white"))
            self.withdrawal_table.setItem(row, 4, reservation_item)
            
            # الصنف
            product_item = QTableWidgetItem(item['product_name'])
            product_item.setBackground(QColor("white"))
            self.withdrawal_table.setItem(row, 3, product_item)
            
            # الكمية المسحوبة
            quantity_text = f"{int(item['quantity'])}" if item['quantity'] == int(item['quantity']) else f"{item['quantity']:.3f}"
            quantity_item = QTableWidgetItem(quantity_text)
            quantity_item.setBackground(QColor("white"))
            self.withdrawal_table.setItem(row, 2, quantity_item)
            
            # المجموع $
            total_usd_text = f"{int(item['total_usd'])}" if item['total_usd'] == int(item['total_usd']) else f"{item['total_usd']:.2f}"
            total_usd_item = QTableWidgetItem(f"{total_usd_text} $")
            total_usd_item.setBackground(QColor("white"))
            self.withdrawal_table.setItem(row, 1, total_usd_item)
            
            # المجموع LBP
            total_lbp_text = f"{int(item['total_lbp'])}" if item['total_lbp'] == int(item['total_lbp']) else f"{item['total_lbp']:.0f}"
            total_lbp_item = QTableWidgetItem(f"{total_lbp_text} LBP")
            total_lbp_item.setBackground(QColor("white"))
            self.withdrawal_table.setItem(row, 0, total_lbp_item)
            
            # زر حذف
            delete_btn = QPushButton("🗑️")
            delete_btn.setStyleSheet("""
                QPushButton {
                    background-color: #e74c3c;
                    color: white;
                    padding: 5px;
                    border: none;
                    border-radius: 3px;
                    font-size: 12px;
                }
                QPushButton:hover {
                    background-color: #c0392b;
                }
            """)
            delete_btn.clicked.connect(lambda checked, r=row: self.remove_from_withdrawal(r))
            
            # إضافة الزر إلى الخلية
            self.withdrawal_table.setCellWidget(row, 5, delete_btn)
    
    def remove_from_withdrawal(self, row):
        """✅ إزالة صنف من قائمة السحب"""
        if row < 0 or row >= len(self.withdrawal_items):
            return
        
        item_to_remove = self.withdrawal_items[row]
        
        # ✅ استعادة الكمية إلى الحجوزات
        for reserved_item in self.reserved_items:
            if (reserved_item['product_name'] == item_to_remove['product_name'] and 
                reserved_item['reservation_number'] == item_to_remove['reservation_number']):
                reserved_item['available_quantity'] += item_to_remove['quantity']
                break
        else:
            # ✅ إذا لم يكن الصنف موجوداً في القائمة، نعيد إضافته
            self.reserved_items.append({
                'product_name': item_to_remove['product_name'],
                'unit': item_to_remove['unit'],
                'unit_price_usd': item_to_remove['unit_price_usd'],
                'unit_price_lbp': item_to_remove['unit_price_lbp'],
                'product_id': item_to_remove['product_id'],
                'reservation_number': item_to_remove['reservation_number'],
                'reservation_uuid': item_to_remove['reservation_uuid'],
                'available_quantity': item_to_remove['quantity'],
                'quantity': item_to_remove['original_quantity']
            })
        
        # ✅ إزالة من قائمة السحب
        self.withdrawal_items.pop(row)
        
        # ✅ تحديث الواجهة
        self.update_reservations_table()
        self.update_withdrawal_table()
        self.calculate_totals()
    
    def calculate_totals(self):
        """✅ حساب مجاميع السحب"""
        total_usd = sum(item['total_usd'] for item in self.withdrawal_items)
        total_lbp = sum(item['total_lbp'] for item in self.withdrawal_items)
        
        usd_text = f"{int(total_usd)} $" if total_usd == int(total_usd) else f"{total_usd:.2f} $"
        lbp_text = f"{int(total_lbp)} LBP" if total_lbp == int(total_lbp) else f"{total_lbp:.0f} LBP"
        
        self.withdrawal_total_usd.setText(usd_text)
        self.withdrawal_total_lbp.setText(lbp_text)
    
    def save_withdrawal(self):
        """✅ حفظ عملية السحب"""
        if not self.withdrawal_items:
            self.show_message("تحذير", "⚠️ لم تقم بإضافة أي أصناف للسحب", "warning")
            return
        
        try:
            # ✅ تحديث الحجوزات في الملف
            self.update_reservations_file()
            
            # ✅ إرجاع بيانات السحب
            self.withdrawal_data = {
                'items': self.withdrawal_items,
                'total_usd': sum(item['total_usd'] for item in self.withdrawal_items),
                'total_lbp': sum(item['total_lbp'] for item in self.withdrawal_items)
            }
            
            self.show_message("نجاح", "✅ تم حفظ عملية السحب بنجاح", "info")
            self.accept()
            
        except Exception as e:
            self.show_message("خطأ", f"❌ حدث خطأ في حفظ السحب: {e}", "error")
    
    def update_reservations_file(self):
        """✅ تحديث ملف الحجوزات بعد السحب"""
        try:
            reservations_file = "data/customer_reservations.json"
            if not os.path.exists(reservations_file):
                return
            
            with open(reservations_file, 'r', encoding='utf-8') as f:
                reservations = json.load(f)
            
            # ✅ تحديث كل حجز بناءً على عمليات السحب
            for withdrawal_item in self.withdrawal_items:
                for reservation in reservations:
                    if reservation.get('reservation_uuid') == withdrawal_item['reservation_uuid']:
                        for item in reservation.get('items', []):
                            if (item['product_name'] == withdrawal_item['product_name'] and 
                                item['unit'] == withdrawal_item['unit']):
                                # ✅ خصم الكمية المسحوبة
                                item['quantity'] -= withdrawal_item['quantity']
                                break
                        break
            
            # ✅ إزالة الحجوزات التي أصبحت كمية جميع أصنافها صفر
            updated_reservations = []
            for reservation in reservations:
                # ✅ التحقق إذا كانت هناك أصناف بكمية أكبر من الصفر
                has_items = any(item['quantity'] > 0 for item in reservation.get('items', []))
                if has_items:
                    # ✅ إزالة الأصناف التي كميتها صفر
                    reservation['items'] = [item for item in reservation.get('items', []) if item['quantity'] > 0]
                    updated_reservations.append(reservation)
            
            # ✅ حفظ الملف المحدث
            with open(reservations_file, 'w', encoding='utf-8') as f:
                json.dump(updated_reservations, f, ensure_ascii=False, indent=2)
            
            print(f"✅ تم تحديث الحجوزات بعد السحب - بقي {len(updated_reservations)} حجز")
                
        except Exception as e:
            print(f"❌ خطأ في تحديث ملف الحجوزات: {e}")
            raise
    
    def show_message(self, title, message, type="info"):
        """✅ عرض رسائل للمستخدم"""
        msg = QMessageBox(self)
        msg.setWindowTitle(title)
        msg.setText(message)
        
        msg.setStyleSheet("""
            QMessageBox {
                background-color: #1e2a3a;
            }
            QMessageBox QLabel {
                color: white;
                font-size: 16px;
                font-weight: bold;
                font-family: Arial;
            }
            QMessageBox QPushButton {
                background-color: #3498db;
                color: white;
                padding: 10px 20px;
                border: none;
                border-radius: 5px;
                font-size: 16px;
                font-weight: bold;
                font-family: Arial;
                min-width: 100px;
            }
            QMessageBox QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        
        if type == "warning":
            msg.setIcon(QMessageBox.Warning)
        elif type == "error":
            msg.setIcon(QMessageBox.Critical)
        else:
            msg.setIcon(QMessageBox.Information)
            
        msg.exec()
    
    def get_withdrawal_data(self):
        return getattr(self, 'withdrawal_data', None)

class DateInput(QLineEdit):
    """✅ حقل إدخال التاريخ مع التحديث التلقائي والتحقق من الصحة"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        """إعداد واجهة حقل التاريخ"""
        self.setPlaceholderText("yyyy-mm-dd أو yyyy/mm/dd")
        self.setStyleSheet("""
            QLineEdit {
                background-color: white; 
                color: black; 
                padding: 10px; 
                border-radius: 5px;
                font-size: 16px;
                border: 1px solid #bdc3c7;
                font-family: Arial;
                font-weight: bold;
                min-width: 150px;
                min-height: 35px;
            }
            QLineEdit:focus {
                border: 2px solid #3498db;
                background-color: #f8f9fa;
            }
            QLineEdit:invalid {
                border: 2px solid #e74c3c;
                background-color: #ffeaea;
            }
        """)
        
        # ✅ تعيين التاريخ الحالي تلقائياً
        self.set_date_to_today()
        
        # ✅ إضافة validator للتحقق من صحة التنسيق
        self.textChanged.connect(self.validate_date)
    
    def set_date_to_today(self):
        """✅ تعيين التاريخ الحالي تلقائياً"""
        today = datetime.now()
        self.setText(today.strftime("%d-%m-%Y"))
    
    def validate_date(self):
        """✅ التحقق من صحة تاريخ الإدخال مع دعم - و /"""
        date_text = self.text().strip()
        
        if not date_text:
            self.setStyleSheet(self.styleSheet() + "border: 2px solid #e74c3c;")
            return False
        
        # ✅ دعم كلا التنسيقين: - و /
        date_text = date_text.replace('/', '-').replace('\\', '-')
        
        # ✅ التحقق من تنسيق التاريخ (yyyy-mm-dd)
        try:
            parts = date_text.split('-')
            if len(parts) != 3:
                self.setStyleSheet(self.styleSheet() + "border: 2px solid #e74c3c;")
                return False
            
            day, month, year = parts
            if len(year) != 4 or not year.isdigit():
                self.setStyleSheet(self.styleSheet() + "border: 2px solid #e74c3c;")
                return False
            
            if len(month) not in [1, 2] or not month.isdigit():
                self.setStyleSheet(self.styleSheet() + "border: 2px solid #e74c3c;")
                return False
            
            if len(day) not in [1, 2] or not day.isdigit():
                self.setStyleSheet(self.styleSheet() + "border: 2px solid #e74c3c;")
                return False
            
            month_int = int(month)
            day_int = int(day)
            year_int = int(year)
            
            # ✅ التحقق من صحة التاريخ
            if month_int < 1 or month_int > 12:
                self.setStyleSheet(self.styleSheet() + "border: 2px solid #e74c3c;")
                return False
            
            if day_int < 1 or day_int > 31:
                self.setStyleSheet(self.styleSheet() + "border: 2px solid #e74c3c;")
                return False
            
            # ✅ التحقق من الأشهر التي تحتوي على 30 يوم
            if month_int in [4, 6, 9, 11] and day_int > 30:
                self.setStyleSheet(self.styleSheet() + "border: 2px solid #e74c3c;")
                return False
            
            # ✅ التحقق من شهر فبراير
            if month_int == 2:
                if (year_int % 4 == 0 and year_int % 100 != 0) or (year_int % 400 == 0):
                    if day_int > 29:
                        self.setStyleSheet(self.styleSheet() + "border: 2px solid #e74c3c;")
                        return False
                else:
                    if day_int > 28:
                        self.setStyleSheet(self.styleSheet() + "border: 2px solid #e74c3c;")
                        return False
            
            # ✅ إذا كان التاريخ صحيحاً
            self.setStyleSheet("""
                QLineEdit {
                    background-color: white; 
                    color: black; 
                    padding: 10px; 
                    border-radius: 5px;
                    font-size: 16px;
                    border: 2px solid #27ae60;
                    font-family: Arial;
                    font-weight: bold;
                    min-width: 150px;
                    min-height: 35px;
                }
            """)
            self.setText(f"{day}-{month}-{year}")
            return True
            
        except:
            self.setStyleSheet(self.styleSheet() + "border: 2px solid #e74c3c;")
            return False
    
    def get_date(self):
        """✅ الحصول على التاريخ كسلسلة نصية"""
        if self.validate_date():
            return self.text().strip()
            
        return None
    
    def set_date(self, date_str):
        """✅ تعيين تاريخ معين"""
        if date_str:
            # ✅ تحويل أي تنسيق إلى تنسيق موحد
            date_str = date_str.replace('/', '-')
            self.setText(date_str)
        else:
            self.set_date_to_today()

class PaymentDialog(QDialog):
    def __init__(self, parent, invoice_data, exchange_rate):
        super().__init__(parent)
        self.invoice_data = invoice_data
        self.exchange_rate = exchange_rate
        self.setup_ui()
        
    def setup_ui(self):
        self.setWindowTitle("إضافة دفعة جديدة")
        self.setFixedSize(500, 400)  # ✅ تكبير النافذة لاستيعاب التعديلات
        
        # ✅ خلفية كحلية داكنة
        self.setStyleSheet("""
            QDialog {
                background-color: #1e2a3a;
            }
            QLabel {
                color: white;
                font-family: Arial;
                font-weight: bold;
            }
            QGroupBox {
                color: white;
                font-family: Arial;
                font-weight: bold;
            }
        """)
        
        layout = QVBoxLayout(self)
        
        # ✅ ✅ ✅ التعديل: تحسين عرض رقم الفاتورة والمبلغ المتبقي
        info_group = QGroupBox("معلومات الفاتورة")
        info_group.setStyleSheet("""
            QGroupBox {
                color: white;
                font-weight: bold;
                font-family: Arial;
                border: 2px solid #3498db;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 15px;
                font-size: 16px;
            }
        """)
        info_layout = QVBoxLayout()
        
        # ✅ ✅ ✅ التعديل: تحسين عرض رقم الفاتورة - من اليسار مع خلفية شفافة
        invoice_layout = QHBoxLayout()
        invoice_label = QLabel("رقم الفاتورة:")
        invoice_label.setStyleSheet("color: white; font-size: 18px; font-weight: bold; font-family: Arial;")
        display_number = self.get_invoice_display_number(self.invoice_data.get('invoice_uuid'))
        invoice_number = QLabel(str(display_number))
        invoice_number.setStyleSheet("color: #3498db; font-size: 22px; font-weight: bold; font-family: Arial; background-color: transparent; padding: 10px; border-radius: 5px;")
        invoice_layout.addStretch()  # ✅ إضافة مساحة أولاً
        invoice_layout.addWidget(invoice_number)   # الرقم
        invoice_layout.addWidget(invoice_label)    # ثم الكلمة

        
        # ✅ ✅ ✅ التعديل: تحسين عرض المبلغ المتبقي - من اليسار مع خلفية شفافة
        remaining_layout = QHBoxLayout()
        remaining_label = QLabel("المبلغ المتبقي:")
        remaining_label.setStyleSheet("color: white; font-size: 18px; font-weight: bold; font-family: Arial;")
        
        # ✅ ✅ ✅ التعديل الهام: حساب المبلغ المتبقي الحقيقي من قاعدة البيانات
        remaining_amount = self.calculate_real_remaining_amount()
        remaining_value = QLabel(f"{remaining_amount:.2f} $")
        remaining_value.setStyleSheet("color: #e74c3c; font-size: 22px; font-weight: bold; font-family: Arial; background-color: transparent; padding: 10px; border-radius: 5px;")
        remaining_layout.addStretch()  # ✅ إضافة مساحة أولاً
        remaining_layout.addWidget(remaining_value)   # الرقم
        remaining_layout.addWidget(remaining_label) 
        
        info_layout.addLayout(invoice_layout)
        info_layout.addLayout(remaining_layout)
        info_group.setLayout(info_layout)
        
        layout.addWidget(info_group)
        # إنشاء الحقول والتسميات أولاً
        payment_amount_label = QLabel("مبلغ الدفعة:")
        payment_amount_label.setStyleSheet("color: white; font-size: 18px; font-weight: bold; font-family: Arial;")

        self.payment_amount = QLineEdit()
        self.payment_amount.setPlaceholderText("أدخل مبلغ الدفعة")
        self.payment_amount.setStyleSheet("""
            QLineEdit {
            padding: 12px;
            border: 2px solid #bdc3c7;
            border-radius: 5px;
            font-size: 16px;
            background-color: white;
            color: black;
            font-family: Arial;
            font-weight: bold;
            min-width: 200px;
            }
            QLineEdit:focus {
            border: 2px solid #3498db;
            background-color: #f8f9fa;
            }
            """)

        payment_date_label = QLabel("تاريخ الدفعة:")
        payment_date_label.setStyleSheet("color: white; font-size: 18px; font-weight: bold; font-family: Arial;")

        self.payment_date = DateInput()
        self.payment_date.setStyleSheet("""
            QLineEdit {
            padding: 12px;
            border: 2px solid #bdc3c7;
            border-radius: 5px;
            font-size: 16px;
            background-color: white;
            color: black;
            font-family: Arial;
            font-weight: bold;
            min-width: 200px;
            }
            """)

        # الآن نضيفهم بالترتيب المطلوب - بدون FormLayout

        # صف مبلغ الدفعة
        payment_layout = QHBoxLayout()
        payment_layout.addStretch()  # لدفع المحتوى لليمين
        payment_layout.addWidget(self.payment_amount)
        payment_layout.addWidget(payment_amount_label)
        layout.addLayout(payment_layout)

        # صف تاريخ الدفعة
        date_layout = QHBoxLayout()
        date_layout.addStretch()  # لدفع المحتوى لليمين
        date_layout.addWidget(self.payment_date)
        date_layout.addWidget(payment_date_label)
        layout.addLayout(date_layout)
        
        # ✅ تخزين المبلغ المتبقي للتحقق منه
        self.max_payment_amount = remaining_amount
        
        # أزرار
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.validate_and_accept)
        buttons.rejected.connect(self.reject)
        
        # ✅ تنسيق الأزرار
        buttons.setStyleSheet("""
            QPushButton {
                padding: 12px 25px;
                border: none;
                border-radius: 5px;
                font-size: 16px;
                font-weight: bold;
                font-family: Arial;
                min-width: 100px;
            }
            QPushButton[text="OK"] {
                background-color: #27ae60;
                color: white;
            }
            QPushButton[text="OK"]:hover {
                background-color: #229954;
            }
            QPushButton[text="Cancel"] {
                background-color: #95a5a6;
                color: white;
            }
            QPushButton[text="Cancel"]:hover {
                background-color: #7f8c8d;
            }
        """)
        
        layout.addWidget(buttons)

    def calculate_real_remaining_amount(self):
        """✅ ✅ ✅ التعديل الهام: حساب المبلغ المتبقي الحقيقي من قاعدة البيانات"""
        try:
            # ✅ الحصول على بيانات الفاتورة الحقيقية من ملف customers.json
            with open("data/customers.json", 'r', encoding='utf-8') as f:
                customers = json.load(f)
            
            invoice_uuid = self.invoice_data.get('invoice_uuid')
            if not invoice_uuid:
                return self.invoice_data.get('remaining_amount', 0)
            
            for customer in customers:
                invoices = customer.get('invoices', [])
                for invoice in invoices:
                    if invoice.get('invoice_uuid') == invoice_uuid:
                        # ✅ حساب المبلغ المتبقي الحقيقي
                        total_usd = invoice.get('total_usd', 0)
                        paid_amount = invoice.get('paid_amount', 0)
                        real_remaining = total_usd - paid_amount
                        
                        print(f"💰 حساب المبلغ المتبقي الحقيقي:")
                        print(f"   - الإجمالي: {total_usd:.2f} $")
                        print(f"   - المدفوع: {paid_amount:.2f} $")
                        print(f"   - المتبقي: {real_remaining:.2f} $")
                        
                        return max(0, real_remaining)
            
            # ✅ إذا لم نجد الفاتورة، نستخدم القيمة المخزنة
            return self.invoice_data.get('remaining_amount', 0)
            
        except Exception as e:
            print(f"❌ خطأ في حساب المبلغ المتبقي الحقيقي: {e}")
            return self.invoice_data.get('remaining_amount', 0)
    
    def get_invoice_display_number(self, invoice_uuid):
        """✅ الحصول على رقم العرض الحقيقي للفاتورة من خلال UUID"""
        try:
            # ✅ الوصول إلى parent (CustomerInvoicesPage) الذي يحتوي على البيانات
            parent = self.parent()
            if hasattr(parent, 'customer_name') and hasattr(parent, 'phone_number'):
                with open("data/customers.json", 'r', encoding='utf-8') as f:
                    customers = json.load(f)
            
                for customer in customers:
                    if (customer.get('name') == parent.customer_name and 
                        customer.get('phone') == parent.phone_number):
                    
                        invoices = customer.get('invoices', [])
                        for index, invoice in enumerate(invoices):
                            if invoice.get('invoice_uuid') == invoice_uuid:
                            # ✅ الرقم الحقيقي هو index + 1 (نفس آلية صفحة الفواتير)
                                return str(index + 1)
        
            return self.invoice_data.get('invoice_number', '')
        except Exception as e:
            print(f"❌ خطأ في الحصول على رقم العرض: {e}")
            return self.invoice_data.get('invoice_number', '')    
    
    def validate_and_accept(self):
        """✅ التحقق من صحة البيانات قبل القبول"""
        try:
            amount_text = self.payment_amount.text().strip()
            if not amount_text:
                self.show_message("تحذير", "يرجى إدخال مبلغ الدفعة", "warning")
                return
            
            # ✅ ✅ ✅ التعديل: السماح بالقيم الصغيرة حتى 0.01
            amount = float(amount_text)
            if amount <= 0:
                self.show_message("تحذير", "يرجى إدخال مبلغ صحيح أكبر من الصفر", "warning")
                return
            
            # ✅ ✅ ✅ التعديل: السماح بدفع المبلغ المتبقي بالكامل حتى لو كان 0.01
            if amount > self.max_payment_amount + 0.01:  # ✅ إضافة هامش بسيط للتقريب
                self.show_message("تحذير", f"لا يمكن دفع مبلغ أكبر من المبلغ المتبقي ({self.max_payment_amount:.2f} $)", "warning")
                return
            
            # ✅ التحقق من صحة التاريخ
            if not self.payment_date.validate_date():
                self.show_message("تحذير", "يرجى إذخال تاريخ صحيح (yyyy-mm-dd أو yyyy/mm/dd)", "warning")
                return
            
            # ✅ ✅ ✅ التصحيح: استخدام self.accept() مباشرة - هذا هو الحل للمشكلة
            self.accept()
            
        except ValueError:
            self.show_message("تحذير", "يرجى إدخال مبلغ صحيح", "warning")
    
    def show_message(self, title, message, type="info"):
        """✅ عرض رسائل للمستخدم"""
        msg = QMessageBox(self)
        msg.setWindowTitle(title)
        msg.setText(message)
        
        # ✅ تنسيق الرسائل بخلفية كحلية داكنة
        msg.setStyleSheet("""
            QMessageBox {
                background-color: #1e2a3a;
            }
            QMessageBox QLabel {
                color: white;
                font-size: 16px;
                font-weight: bold;
                font-family: Arial;
            }
            QMessageBox QPushButton {
                background-color: #3498db;
                color: white;
                padding: 10px 20px;
                border: none;
                border-radius: 5px;
                font-size: 16px;
                font-weight: bold;
                font-family: Arial;
                min-width: 100px;
            }
            QMessageBox QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        
        if type == "warning":
            msg.setIcon(QMessageBox.Warning)
        elif type == "error":
            msg.setIcon(QMessageBox.Critical)
        else:
            msg.setIcon(QMessageBox.Information)
            
        msg.exec()
    
    def get_payment_data(self):
        return {
            'amount': float(self.payment_amount.text()),
            'date': self.payment_date.get_date(),
            'invoice_number': self.invoice_data.get('invoice_number', ''),
            'invoice_uuid': self.invoice_data.get('invoice_uuid', '')  # ✅ إضافة UUID
        }

# ✅ ✅ ✅ إضافة كلاس فاتورة التقسيط الجديد
class InstallmentInvoiceDialog(QDialog):
    """نافذة إنشاء فاتورة تقسيط جديدة"""
    def __init__(self, parent, exchange_rate, invoice_number, invoice_data=None):
        super().__init__(parent)
        self.exchange_rate = exchange_rate
        self.invoice_number = invoice_number
        self.items = []
        self.products = self.load_products_from_database()
        self.is_editing = invoice_data is not None
        self.original_invoice_data = invoice_data
        self.parent = parent  # ✅ حفظ المرجع للوصول إلى دالة حفظ الدفعات
        
        # ✅ ضبط حجم النافذة
        screen = self.screen()
        screen_size = screen.availableSize()
        min_width = int(screen_size.width() * 0.9)
        min_height = int(screen_size.height() * 0.8)
        
        self.setMinimumSize(min_width, min_height)
        
        self.setup_ui()
        self.setup_enter_shortcut()
        
        # ✅ إذا كنا في وضع التعديل، نقوم بتحميل بيانات الفاتورة
        if self.is_editing:
            self.load_invoice_data()
    
    def load_invoice_data(self):
        """✅ تحميل بيانات الفاتورة للتعديل"""
        if self.original_invoice_data:
            # تحميل التاريخ
            if 'date' in self.original_invoice_data:
                date_str = self.original_invoice_data['date'].split(' ')[0]  # أخذ الجزء الخاص بالتاريخ فقط
                try:
                    # ✅ استخدام DateInput الجديد
                    self.date_input.set_date(date_str)
                except:
                    pass
            
            # تحميل بيانات العميل
            self.customer_name.setText(self.original_invoice_data.get('customer_name', ''))
            self.customer_phone.setText(self.original_invoice_data.get('customer_phone', ''))
            
            # ✅ تحميل العنوان
            self.address_input.setText(self.original_invoice_data.get('address', ''))
            
            # تحميل المبلغ المدفوع
            paid_amount = self.original_invoice_data.get('paid_amount', 0)
            self.paid_amount_input.setText(str(paid_amount))  # ✅ التعديل: استخدام setText بدلاً من setValue
            
            # تحميل الأصناف
            self.items = self.original_invoice_data.get('items', [])
            self.update_items_table()
            self.calculate_totals()
            self.calculate_remaining()
    
    def setup_enter_shortcut(self):
        """✅ ✅ ✅ التعديل: تعطيل زر Enter لإضافة الأصناف وتفعيله فقط للحفظ"""
        # تعطيل Enter لإضافة الأصناف
        enter_shortcut = QShortcut(QKeySequence("Return"), self)
        enter_shortcut.setEnabled(False)
        enter_shortcut = QShortcut(QKeySequence("Enter"), self)
        enter_shortcut.setEnabled(False)
        
        # تفعيل Enter فقط لحفظ الفاتورة
        self.save_shortcut = QShortcut(QKeySequence("Return"), self)
        self.save_shortcut.activated.connect(self.save_invoice)
        self.save_shortcut = QShortcut(QKeySequence("Enter"), self)
        self.save_shortcut.activated.connect(self.save_invoice)
        
        self.disable_enter_on_lineedits()
    
    def disable_enter_on_lineedits(self):
        """✅ تعطيل زر Enter على جميع الحقول النصية"""
        for child in self.findChildren(QLineEdit):
            enter_shortcut = QShortcut(QKeySequence("Return"), child)
            enter_shortcut.setEnabled(False)
            enter_shortcut = QShortcut(QKeySequence("Enter"), child)
            enter_shortcut.setEnabled(False)
            
        for child in self.findChildren(QComboBox):
            enter_shortcut = QShortcut(QKeySequence("Return"), child)
            enter_shortcut.setEnabled(False)
            enter_shortcut = QShortcut(QKeySequence("Enter"), child)
            enter_shortcut.setEnabled(False)
            
        for child in self.findChildren(DateInput):
            enter_shortcut = QShortcut(QKeySequence("Return"), child)
            enter_shortcut.setEnabled(False)
            enter_shortcut = QShortcut(QKeySequence("Enter"), child)
            enter_shortcut.setEnabled(False)

    def load_products_from_database(self):
        """✅ تحميل الأصناف من قاعدة البيانات مع تحديث الأسعار بناءً على سعر الصرف"""
        try:
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            
            c.execute("""
                SELECT 
                    id, name, buy_unit, sell_unit, buy_price, sell_price, 
                    quantity, currency 
                FROM Items 
                ORDER BY name
            """)
            
            products = []
            for row in c.fetchall():
                product = {
                    'id': row[0],
                    'name': row[1],
                    'buy_unit': row[2],
                    'sell_unit': row[3],
                    'buy_price': float(row[4]),
                    'sell_price': float(row[5]),
                    'stock': float(row[6]),
                    'currency': row[7]
                }
                
                # ✅ تحويل الأسعار بناءً على العملة وسعر الصرف الحالي
                if product['currency'].upper() == 'LBP':
                    product['buy_price_usd'] = product['buy_price'] / self.exchange_rate
                    product['sell_price_usd'] = product['sell_price'] / self.exchange_rate
                else:
                    product['buy_price_usd'] = product['buy_price']
                    product['sell_price_usd'] = product['sell_price']
                
                products.append(product)
            
            conn.close()
            return products
            
        except Exception as e:
            print(f"❌ خطأ في تحميل الأصناف من قاعدة البيانات: {e}")
            return []

    def get_item_sell_units(self, item_id):
        """✅ جلب وحدات المبيع الخاصة بصنف معين من قاعدة البيانات"""
        try:
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute("SELECT sell_unit FROM ItemSellUnits WHERE item_id=? ORDER BY sell_unit", (item_id,))
            units = [row[0] for row in c.fetchall()]
            conn.close()
            
            if not units:
                c.execute("SELECT sell_unit FROM Items WHERE id=?", (item_id,))
                default_unit = c.fetchone()
                if default_unit and default_unit[0]:
                    units = [default_unit[0]]
            
            return units if units else ["قطعة"]
            
        except Exception as e:
            print(f"❌ خطأ في جلب وحدات المبيع للصنف {item_id}: {e}")
            return ["قطعة"]

    def setup_ui(self):
        title = f"فاتورة تقسيط - رقم: {self.invoice_number}"
        if self.is_editing:
            title = f"فاتورة تقسيط  تعديل - رقم: {self.invoice_number}"
        
        self.setWindowTitle(title)
        
        # ✅ خلفية كحلية داكنة
        self.setStyleSheet("""
            QDialog {
                background-color: #1e2a3a;
                border: 2px solid #34495e;
                border-radius: 10px;
            }
            QGroupBox {
                color: white;
                font-size: 16px;
                font-weight: bold;
                font-family: Arial;
                border: 2px solid #34495e;
                border-radius: 8px;
                background-color: rgba(30, 42, 58, 0.9);
                margin-top: 8px;
                padding: 10px;
            }
            QLabel {
                color: white;
                font-size: 16px;
                font-weight: bold;
                font-family: Arial;
            }
        """)
        
        layout = QVBoxLayout(self)
        
        # ✅ الهيدر مع العنوان والشعار
        header_layout = QHBoxLayout()
        
        title_label = QLabel(title)
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 28px;
                font-weight: bold;
                background-color: transparent;
                padding: 15px;
                font-family: Arial;
            }
        """)
        
        logo_label = QLabel()
        logo_pixmap = QPixmap(r"C:\Users\User\Desktop\chbib1\icons\logo.png")
        if not logo_pixmap.isNull():
            logo_label.setPixmap(logo_pixmap.scaled(80, 80, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        logo_label.setAlignment(Qt.AlignRight)
        
        header_layout.addStretch()
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(logo_label)
        
        layout.addLayout(header_layout)
        
        # ✅ حقل التاريخ - ✅ استخدام DateInput الجديد مع تعديل المحاذاة
        date_group = QGroupBox("")
        date_layout = QHBoxLayout()
        
        # ✅ تعديل المحاذاة: النقطتين فوق بعض ثم الحقل
        date_label = QLabel("تاريخ الفاتورة:")
        date_label.setStyleSheet("color: white; font-size: 16px; font-weight: bold; font-family: Arial;")
        
        self.date_input = DateInput()
        self.date_input.setPlaceholderText("ابحث عن تاريخ")
        
        date_layout.addStretch()
        date_layout.addWidget(self.date_input)
        date_layout.addWidget(date_label)
        
        date_group.setLayout(date_layout)
        layout.addWidget(date_group)
        
        # معلومات العميل - ✅ تعديل المحاذاة
        customer_group = QGroupBox("")
        customer_layout = QFormLayout()
        
        self.customer_name = QLineEdit()
        self.customer_name.setPlaceholderText("(اختياري) العميل اسم")
        self.customer_name.setStyleSheet("""
            QLineEdit {
                background-color: white; 
                color: black; 
                padding: 12px; 
                border-radius: 5px;
                font-size: 16px;
                border: 1px solid #bdc3c7;
                font-family: Arial;
                font-weight: bold;
                min-height: 35px;
            }
            QLineEdit:focus {
                border: 2px solid #3498db;
                background-color: #f8f9fa;
            }
        """)
        
        self.customer_phone = QLineEdit()
        self.customer_phone.setPlaceholderText("(اختياري) الهاتف رقم")
        self.customer_phone.setStyleSheet("""
            QLineEdit {
                background-color: white; 
                color: black; 
                padding: 12px; 
                border-radius: 5px;
                font-size: 16px;
                border: 1px solid #bdc3c7;
                font-family: Arial;
                font-weight: bold;
                min-height: 35px;
            }
            QLineEdit:focus {
                border: 2px solid #3498db;
                background-color: #f8f9fa;
            }
        """)
        phone_validator = QIntValidator(0, 999999999, self)
        self.customer_phone.setValidator(phone_validator)
        
        # ✅ ✅ ✅ إضافة حقل العنوان الجديد
        self.address_input = QLineEdit()
        self.address_input.setPlaceholderText("(اختياري) مكان الورشة")
        self.address_input.setStyleSheet("""
            QLineEdit {
                background-color: white; 
                color: black; 
                padding: 12px; 
                border-radius: 5px;
                font-size: 16px;
                border: 1px solid #bdc3c7;
                font-family: Arial;
                font-weight: bold;
                min-height: 35px;
            }
            QLineEdit:focus {
                border: 2px solid #3498db;
                background-color: #f8f9fa;
            }
        """)
        
        # ✅ تعديل المحاذاة: الحقول أولاً ثم النقطتين
        name_layout = QHBoxLayout()
        name_layout.addStretch()
        name_layout.addWidget(self.customer_name)
        name_layout.addWidget(QLabel("الاسم:"))
        
        phone_layout = QHBoxLayout()
        phone_layout.addStretch()
        phone_layout.addWidget(self.customer_phone)
        phone_layout.addWidget(QLabel("الهاتف:"))
        
        # ✅ ✅ ✅ إضافة صف العنوان
        address_layout = QHBoxLayout()
        address_layout.addStretch()
        address_layout.addWidget(self.address_input)
        address_layout.addWidget(QLabel("مكان الورشة:"))
        
        customer_layout.addRow(name_layout)
        customer_layout.addRow(phone_layout)
        customer_layout.addRow(address_layout)  # ✅ إضافة صف العنوان
        customer_group.setLayout(customer_layout)
        layout.addWidget(customer_group)
        
        # إضافة الأصناف
        items_group = QGroupBox("")
        items_layout = QVBoxLayout()
        
        # عناصر التحكم
        control_layout = QHBoxLayout()
        
        self.product_combo = QComboBox()
        self.product_combo.setStyleSheet("""
            QComboBox {
                background-color: white; 
                color: black; 
                padding: 12px; 
                border-radius: 5px;
                font-size: 16px;
                border: 1px solid #bdc3c7;
                min-width: 200px;
                font-family: Arial;
                font-weight: bold;
                min-height: 35px;
            }
            QComboBox:focus {
                border: 2px solid #3498db;
                background-color: #f8f9fa;
            }
            QComboBox QAbstractItemView {
                background-color: white;
                color: black;
                selection-background-color: #3498db;
                selection-color: white;
                border: 1px solid #bdc3c7;
                font-family: Arial;
                font-weight: bold;
                font-size: 14px;
            }
        """)
        if self.products:
            self.product_combo.addItems([p['name'] for p in self.products])
        else:
            self.product_combo.addItems(["لا توجد أصناف - الرجاء إضافة أصناف من صفحة الإدارة"])
        self.product_combo.currentIndexChanged.connect(self.on_product_changed)
        
        # ✅ حقل وحدات المبيع
        self.unit_combo = QComboBox()
        self.unit_combo.setStyleSheet("""
            QComboBox {
                background-color: white; 
                color: black; 
                padding: 12px; 
                border-radius: 5px;
                font-size: 16px;
                border: 1px solid #bdc3c7;
                min-width: 140px;
                font-family: Arial;
                font-weight: bold;
                min-height: 35px;
            }
            QComboBox:focus {
                border: 2px solid #3498db;
                background-color: #f8f9fa;
            }
            QComboBox QAbstractItemView {
                background-color: white;
                color: black;
                selection-background-color: #3498db;
                selection-color: white;
                border: 1px solid #bdc3c7;
                font-family: Arial;
                font-weight: bold;
                font-size: 14px;
            }
        """)
        
        self.quantity_input = QLineEdit()
        self.quantity_input.setPlaceholderText("الكمية أدخل")
        self.quantity_input.setText("1")
        self.quantity_input.setStyleSheet("""
            QLineEdit {
                background-color: white; 
                color: black; 
                padding: 12px; 
                border-radius: 5px;
                font-size: 16px;
                border: 1px solid #bdc3c7;
                min-width: 120px;
                font-family: Arial;
                font-weight: bold;
                min-height: 35px;
            }
            QLineEdit:focus {
                border: 2px solid #3498db;
                background-color: #f8f9fa;
            }
        """)
        quantity_validator = QDoubleValidator(0.001, 10000, 3, self)
        self.quantity_input.setValidator(quantity_validator)
        self.quantity_input.textChanged.connect(self.on_quantity_changed)
        
        add_btn = QPushButton(" اضافة صنف ")
        add_btn.setStyleSheet("""
            QPushButton {
                background-color: white;
                color: #2c3e50;
                padding: 12px 25px;
                border: 2px solid #2c3e50;
                border-radius: 5px;
                font-size: 16px;
                font-weight: bold;
                font-family: Arial;
                min-height: 35px;
            }
            QPushButton:hover {
                background-color: #f8f9fa;
                border: 2px solid #34495e;
            }
        """)
        add_btn.clicked.connect(self.add_item)
        
        # ✅ تعديل المحاذاة: الحقول أولاً ثم التسميات
        control_layout.addStretch()
        control_layout.addWidget(self.product_combo)
        control_layout.addWidget(QLabel("الصنف:"))
        control_layout.addWidget(self.unit_combo)
        control_layout.addWidget(QLabel("المبيع وحدة:"))
        control_layout.addWidget(self.quantity_input)
        control_layout.addWidget(QLabel("الكمية:"))
        control_layout.addWidget(add_btn)
        
        items_layout.addLayout(control_layout)
        
        # جدول الأصناف
        table_layout = QVBoxLayout()
        
        self.items_table = QTableWidget()
        self.items_table.setColumnCount(7)
        self.items_table.setHorizontalHeaderLabels([
            "LBP المجموع", "$ المجموع", "LBP الوحدة سعر", "$ الوحدة سعر", "الكمية", "المبيع وحدة", "الصنف"
        ])
        
        self.items_table.setStyleSheet("""
            QTableWidget {
                background-color: white;
                border: 2px solid #2c3e50;
                border-radius: 8px;
                font-size: 14px;
                gridline-color: #bdc3c7;
                selection-background-color: #3498db;
                selection-color: black;
                font-family: Arial;
                font-weight: bold;
            }
            QHeaderView::section {
                background-color: #2c3e50;
                color: white;
                padding: 15px;
                border: none;
                font-weight: bold;
                font-size: 14px;
                font-family: Arial;
            }
            QTableWidget::item {
                padding: 12px;
                border-bottom: 1px solid #ecf0f1;
                font-size: 0.5px;
                color: #2c3e50;
                background-color: white;
                selection-background-color: #e3f2fd;
                selection-color: black;
                min-height: 45px;
                font-family: Arial;
                font-weight: bold;
            }
            QTableWidget::item:selected {
                background-color: #e3f2fd;
                color: black;
                border: 1px solid #3498db;
            }
            QTableWidget::item:focus {
                background-color: #e3f2fd;
                border: 1px solid #3498db;
                color: black;
            }
        """)
        
        self.items_table.setFocusPolicy(Qt.NoFocus)
        
        header = self.items_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)
        
        self.items_table.verticalHeader().setDefaultSectionSize(50)
        self.items_table.cellChanged.connect(self.on_cell_changed)
        
        # أزرار التحكم
        buttons_layout = QHBoxLayout()
        
        delete_item_btn = QPushButton("المحدد الصنف حذف 🗑️")
        delete_item_btn.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                padding: 12px 25px;
                border: none;
                border-radius: 5px;
                font-size: 16px;
                font-weight: bold;
                font-family: Arial;
                min-height: 35px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        delete_item_btn.clicked.connect(self.delete_selected_item)
        
        # ✅ ✅ ✅ التعديل: تغيير زر PDF إلى حفظ HTML
        save_btn = QPushButton("حفظ 💾")
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                padding: 12px 25px;
                border: none;
                border-radius: 5px;
                font-size: 16px;
                font-weight: bold;
                font-family: Arial;
                min-height: 35px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        save_btn.clicked.connect(self.export_invoice_html)  # ✅ تغيير الدالة المستدعاة
        
        buttons_layout.addWidget(delete_item_btn)
        buttons_layout.addStretch()
        buttons_layout.addWidget(save_btn)  # ✅ تغيير اسم الزر
        
        table_layout.addWidget(self.items_table)
        table_layout.addLayout(buttons_layout)
        
        items_layout.addLayout(table_layout)
        items_group.setLayout(items_layout)
        layout.addWidget(items_group)
        
        # المجاميع
        totals_layout = QHBoxLayout()
        
        self.total_usd = QLabel("0 $")
        self.total_usd.setStyleSheet("font-size: 20px; font-weight: bold; color: white; font-family: Arial;")
        
        self.total_lbp = QLabel("0 LBP")
        self.total_lbp.setStyleSheet("font-size: 20px; font-weight: bold; color: white; font-family: Arial;")
        
        totals_layout.addStretch()
        totals_layout.addWidget(QLabel("المجموع بالدولار  :"))
        totals_layout.addWidget(self.total_usd)
        totals_layout.addWidget(QLabel("المجموع بالليرة  :"))
        totals_layout.addWidget(self.total_lbp)
        
        layout.addLayout(totals_layout)
        
        # ✅ ✅ ✅ نقل قسم المدفوعات والمتبقي إلى أسفل الصفحة مع تعديل المحاذاة
        payment_group = QGroupBox("")
        payment_layout = QFormLayout()
        
        # ✅ ✅ ✅ التعديل: استبدال QDoubleSpinBox بـ QLineEdit لحذف السهمين
        self.paid_amount_input = QLineEdit()
        self.paid_amount_input.setPlaceholderText("0.00 $")
        self.paid_amount_input.setText("0.00")
        self.paid_amount_input.setStyleSheet("""
            QLineEdit {
                background-color: white; 
                color: black; 
                padding: 8px; 
                border-radius: 5px;
                font-size: 14px;
                border: 1px solid #bdc3c7;
                font-family: Arial;
                font-weight: bold;
                min-height: 30px;
                max-width: 120px;
            }
            QLineEdit:focus {
                border: 2px solid #3498db;
                background-color: #f8f9fa;
            }
        """)
        paid_validator = QDoubleValidator(0, 1000000, 2, self)
        self.paid_amount_input.setValidator(paid_validator)
        self.paid_amount_input.textChanged.connect(self.calculate_remaining)
        
        self.remaining_amount_label = QLabel("0 $")
        self.remaining_amount_label.setStyleSheet("""
            QLabel {
                color: #e74c3c;
                font-size: 16px;
                font-weight: bold;
                font-family: Arial;
                padding: 8px;
                background-color: white;
                border-radius: 5px;
                border: 1px solid #e74c3c;
                max-width: 120px;
            }
        """)
        
        # ✅ تعديل المحاذاة: الحقول أولاً ثم النقطتين
        paid_layout = QHBoxLayout()
        paid_layout.addStretch()
        paid_layout.addWidget(self.paid_amount_input)
        paid_layout.addWidget(QLabel("($) المبلغ المدفوع:"))
        
        remaining_layout = QHBoxLayout()
        remaining_layout.addStretch()
        remaining_layout.addWidget(self.remaining_amount_label)
        remaining_layout.addWidget(QLabel("المتبقي:"))
        
        payment_layout.addRow(paid_layout)
        payment_layout.addRow(remaining_layout)
        
        payment_group.setLayout(payment_layout)
        layout.addWidget(payment_group)
        
        # أزرار الحفظ والإلغاء - ✅ رفع الأزرار للأعلى
        button_layout = QHBoxLayout()
        
        save_text = " حفظ الفاتورة💾" if not self.is_editing else "التعديلات حفظ 💾"
        save_btn = QPushButton(save_text)
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                padding: 15px 30px;
                border: none;
                border-radius: 6px;
                font-size: 18px;
                font-weight: bold;
                font-family: Arial;
                min-height: 40px;
                margin-top: 10px;
            }
            QPushButton:hover {
                background-color: #229954;
            }
        """)
        save_btn.clicked.connect(self.save_invoice)
        
        cancel_btn = QPushButton("❌ إلغاء")
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #95a5a6;
                color: white;
                padding: 15px 30px;
                border: none;
                border-radius: 6px;
                font-size: 18px;
                font-family: Arial;
                font-weight: bold;
                min-height: 40px;
                margin-top: 10px;
            }
            QPushButton:hover {
                background-color: #7f8c8d;
            }
        """)
        cancel_btn.clicked.connect(self.reject)
        
        button_layout.addWidget(save_btn)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
        
        # ✅ تحميل وحدات المبيع للصنف الأول عند فتح النافذة
        if self.products:
            self.load_sell_units_for_product(self.products[0]['id'])

    def on_product_changed(self):
        """✅ عند تغيير المنتج المحدد - تحميل وحدات المبيع الخاصة به"""
        product_index = self.product_combo.currentIndex()
        if product_index >= 0 and product_index < len(self.products):
            product = self.products[product_index]
            self.load_sell_units_for_product(product['id'])
        
        self.update_unit_price()

    def load_sell_units_for_product(self, product_id):
        """✅ تحميل وحدات المبيع الخاصة بصنف معين"""
        try:
            units = self.get_item_sell_units(product_id)
            
            self.unit_combo.clear()
            if units:
                self.unit_combo.addItems(units)
            else:
                self.unit_combo.addItems(["قطعة"])
            
        except Exception as e:
            print(f"❌ خطأ في تحميل وحدات الصنف {product_id}: {e}")
            self.unit_combo.clear()
            self.unit_combo.addItems(["قطعة"])

    def on_quantity_changed(self):
        """عند تغيير الكمية - تحديث الأسعار تلقائياً"""
        self.update_unit_price()

    def update_unit_price(self):
        """✅ تحديث سعر الوحدة بناءً على المنتج والكمية وسعر الصرف"""
        product_index = self.product_combo.currentIndex()
        if product_index >= 0 and product_index < len(self.products):
            product = self.products[product_index]
            quantity_text = self.quantity_input.text().strip()
            
            if quantity_text and quantity_text != '.':
                try:
                    quantity = float(quantity_text)
                    unit_price_usd_single = product['sell_price_usd'] * quantity
                    unit_price_lbp_single = unit_price_usd_single * self.exchange_rate
                except ValueError:
                    pass

    def calculate_remaining(self):
        """✅ حساب المبلغ المتبقي تلقائياً"""
        total_usd = sum(item['total_usd'] for item in self.items)
        try:
            paid_amount = float(self.paid_amount_input.text() or 0)
        except ValueError:
            paid_amount = 0
        remaining = total_usd - paid_amount
        
        remaining_text = f"{remaining:.2f} $" if remaining >= 0 else "0 $"
        self.remaining_amount_label.setText(remaining_text)
        
        # ✅ تغيير لون المتبقي إذا كان سالباً
        if remaining < 0:
            self.remaining_amount_label.setStyleSheet("""
                QLabel {
                    color: #e74c3c;
                    font-size: 16px;
                    font-weight: bold;
                    font-family: Arial;
                    padding: 8px;
                    background-color: #ffebee;
                    border-radius: 5px;
                    border: 1px solid #e74c3c;
                    max-width: 120px;
                }
            """)
        else:
            self.remaining_amount_label.setStyleSheet("""
                QLabel {
                    color: #27ae60;
                    font-size: 16px;
                    font-weight: bold;
                    font-family: Arial;
                    padding: 8px;
                    background-color: white;
                    border-radius: 5px;
                    border: 1px solid #27ae60;
                    max-width: 120px;
                }
            """)

    def on_cell_changed(self, row, column):
        """✅ تحديث تلقائي عند تعديل خلية في الجدول"""
        if row < 0 or row >= len(self.items):
            return
            
        if column == 2:  # عمود الكمية
            try:
                quantity_item = self.items_table.item(row, column)
                if quantity_item:
                    new_quantity_text = quantity_item.text().strip()
                    if not new_quantity_text:
                        return
                        
                    new_quantity = float(new_quantity_text)
                    old_quantity = self.items[row]['quantity']
                    
                    self.items[row]['quantity'] = new_quantity
                    
                    product = self.get_product_by_name(self.items[row]['product_name'])
                    if product:
                        unit_price_usd_single = product['sell_price_usd']
                        unit_price_lbp_single = unit_price_usd_single * self.exchange_rate
                        
                        total_usd = unit_price_usd_single * new_quantity
                        total_lbp = unit_price_lbp_single * new_quantity
                        
                        self.items[row]['unit_price_usd'] = unit_price_usd_single
                        self.items[row]['unit_price_lbp'] = unit_price_lbp_single
                        self.items[row]['total_usd'] = total_usd
                        self.items[row]['total_lbp'] = total_lbp
                        
                        self.update_table_row(row)
                        self.calculate_totals()
                        self.calculate_remaining()
                        
            except ValueError:
                self.items_table.blockSignals(True)
                self.items_table.item(row, column).setText(str(self.items[row]['quantity']))
                self.items_table.blockSignals(False)
        
        elif column == 3:  # ✅ عمود سعر الوحدة $ - التعديل اليدوي
            try:
                price_item = self.items_table.item(row, column)
                if price_item:
                    new_price_text = price_item.text().replace('$', '').strip()
                    if not new_price_text:
                        return
                        
                    new_price = float(new_price_text)
                    old_price = self.items[row]['unit_price_usd']
                    
                    self.items[row]['unit_price_usd'] = new_price
                    self.items[row]['unit_price_lbp'] = new_price * self.exchange_rate
                    
                    quantity = self.items[row]['quantity']
                    self.items[row]['total_usd'] = new_price * quantity
                    self.items[row]['total_lbp'] = (new_price * self.exchange_rate) * quantity
                    
                    self.update_table_row(row)
                    self.calculate_totals()
                    self.calculate_remaining()
                    
            except ValueError:
                self.items_table.blockSignals(True)
                self.items_table.item(row, column).setText(f"{self.items[row]['unit_price_usd']:.3f} $")
                self.items_table.blockSignals(False)

    def update_stock_quantity_single(self, product_id, quantity, operation):
        """✅ تحديث كمية مخزون صنف واحد - فوري"""
        try:
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            
            if operation == "subtract":
                c.execute("UPDATE Items SET quantity = quantity - ? WHERE id = ?", (quantity, product_id))
            elif operation == "add":
                c.execute("UPDATE Items SET quantity = quantity + ? WHERE id = ?", (quantity, product_id))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            print(f"❌ خطأ في تحديث المخزون: {e}")

    def get_product_by_name(self, product_name):
        """الحصول على بيانات المنتج بالاسم"""
        for product in self.products:
            if product['name'] == product_name:
                return product
        return None

    def check_stock_availability(self, product_name, quantity):
        """التحقق من توفر المخزون"""
        for product in self.products:
            if product['name'] == product_name:
                if quantity > product['stock']:
                    reply = self.show_message("المخزون تحذير", 
                        f"المتاح المخزون ({product['stock']}) {product_name} لأصناف ({quantity}) المطلوبة الكمية تتجاوز",
                        "warning", True)
                    return reply == QMessageBox.Yes
                return True
        return False

    def add_item(self):
        """✅ ✅ ✅ إضافة صنف إلى الفاتورة مع وحدة المبيع المحددة"""
        try:
            product_index = self.product_combo.currentIndex()
            if product_index < 0 or product_index >= len(self.products):
                self.show_message("تحذير", "صحيح صنف اختيار يرجى", "warning")
                return
            
            product = self.products[product_index]
            unit = self.unit_combo.currentText()
            quantity_text = self.quantity_input.text().strip()
            
            if not quantity_text:
                self.show_message("تحذير", "كمية إدخال يرجى", "warning")
                return
            
            try:
                quantity = float(quantity_text)
            except ValueError:
                self.show_message("تحذير", "صحيحة كمية إدخال يرجى", "warning")
                return
            
            if quantity <= 0:
                self.show_message("تحذير", "صحيحة كمية إدخال يرجى", "warning")
                return
            
            if not self.check_stock_availability(product['name'], quantity):
                return
            
            unit_price_usd_single = product['sell_price_usd']
            unit_price_lbp_single = unit_price_usd_single * self.exchange_rate
            
            total_usd = unit_price_usd_single * quantity
            total_lbp = unit_price_lbp_single * quantity
            
            item = {
                'product_name': product['name'],
                'unit': unit,
                'quantity': quantity,
                'unit_price_usd': unit_price_usd_single,
                'unit_price_lbp': unit_price_lbp_single,
                'total_usd': total_usd,
                'total_lbp': total_lbp,
                'purchase_price': product['buy_price_usd'] * quantity,
                'product_id': product['id']
            }
            
            self.items.append(item)
            self.update_items_table()
            self.calculate_totals()
            self.calculate_remaining()
            
            self.quantity_input.setText("1")
            
        except Exception as e:
            self.show_message("خطأ", f"خطأ حدث: {e}", "error")

    def delete_selected_item(self):
        """✅ حذف الصنف المحدد من الجدول"""
        selected_row = self.items_table.currentRow()
        if selected_row == -1:
            self.show_message("تحذير", "للحذف صنف تحديد يرجى", "warning")
            return
            
        if selected_row >= 0 and selected_row < len(self.items):
            item_to_delete = self.items[selected_row]
            reply = self.show_message("الحذف تأكيد", 
                f"'{item_to_delete['product_name']}' الصنف حذف تريد هل؟\n\n"
                f"{item_to_delete['quantity']} :الكمية\n\n"
                f"المخزون إلى الكمية استعادة سيتم ✓ نعم\n"
                f"الكمية استعادة دون فقط الصنف حذف سيتم ✗ لا", 
                "question", True)
            
            if reply == QMessageBox.Yes:
                self.update_stock_quantity_single(item_to_delete['product_id'], item_to_delete['quantity'], "add")
                self.items.pop(selected_row)
                self.update_items_table()
                self.calculate_totals()
                self.calculate_remaining()
                self.show_message("نجاح", "✅ بنجاح الصنف حذف و المخزون إلى الكمية استعادة تم", "info")
                
            elif reply == QMessageBox.No:
                self.items.pop(selected_row)
                self.update_items_table()
                self.calculate_totals()
                self.calculate_remaining()
                self.show_message("نجاح", "✅ بنجاح الصنف حذف تم", "info")
    
    def update_items_table(self):
        """✅ ✅ ✅ تحديث جدول الأصناف مع عرض وحدة المبيع"""
        self.items_table.blockSignals(True)
        
        self.items_table.setRowCount(len(self.items))
        
        for row, item in enumerate(self.items):
            quantity_text = f"{int(item['quantity'])}" if item['quantity'] == int(item['quantity']) else f"{item['quantity']:.3f}"
            unit_price_usd_text = f"{int(item['unit_price_usd'])}" if item['unit_price_usd'] == int(item['unit_price_usd']) else f"{item['unit_price_usd']:.3f}"
            unit_price_lbp_text = f"{int(item['unit_price_lbp'])}" if item['unit_price_lbp'] == int(item['unit_price_lbp']) else f"{item['unit_price_lbp']:.0f}"
            total_usd_text = f"{int(item['total_usd'])}" if item['total_usd'] == int(item['total_usd']) else f"{item['total_usd']:.2f}"
            total_lbp_text = f"{int(item['total_lbp'])}" if item['total_lbp'] == int(item['total_lbp']) else f"{item['total_lbp']:.0f}"
            
            product_item = QTableWidgetItem(item['product_name'])
            product_item.setBackground(QColor("white"))
            self.items_table.setItem(row, 6, product_item)
            
            unit_item = QTableWidgetItem(item['unit'])
            unit_item.setFlags(unit_item.flags() & ~Qt.ItemIsEditable)
            unit_item.setBackground(QColor("white"))
            self.items_table.setItem(row, 5, unit_item)
            
            quantity_item = QTableWidgetItem(quantity_text)
            quantity_item.setForeground(QColor("#2c3e50"))
            quantity_item.setBackground(QColor("white"))
            quantity_item.setFont(QFont("Arial", 12, QFont.Bold))
            self.items_table.setItem(row, 4, quantity_item)
            
            unit_price_usd_item = QTableWidgetItem(f"{unit_price_usd_text} $")
            unit_price_usd_item.setForeground(QColor("#2c3e50"))
            unit_price_usd_item.setBackground(QColor("white"))
            unit_price_usd_item.setFont(QFont("Arial", 12, QFont.Bold))
            self.items_table.setItem(row, 3, unit_price_usd_item)
            
            unit_price_lbp_item = QTableWidgetItem(f"{unit_price_lbp_text} LBP")
            unit_price_lbp_item.setFlags(unit_price_lbp_item.flags() & ~Qt.ItemIsEditable)
            unit_price_lbp_item.setBackground(QColor("white"))
            self.items_table.setItem(row, 2, unit_price_lbp_item)
            
            total_usd_item = QTableWidgetItem(f"{total_usd_text} $")
            total_usd_item.setFlags(total_usd_item.flags() & ~Qt.ItemIsEditable)
            total_usd_item.setBackground(QColor("white"))
            self.items_table.setItem(row, 1, total_usd_item)
            
            total_lbp_item = QTableWidgetItem(f"{total_lbp_text} LBP")
            total_lbp_item.setFlags(total_lbp_item.flags() & ~Qt.ItemIsEditable)
            total_lbp_item.setBackground(QColor("white"))
            self.items_table.setItem(row, 0, total_lbp_item)
        
        self.items_table.blockSignals(False)
    
    def update_table_row(self, row):
        """تحديث صف معين في الجدول"""
        if row < 0 or row >= len(self.items):
            return
            
        item = self.items[row]
        
        quantity_text = f"{int(item['quantity'])}" if item['quantity'] == int(item['quantity']) else f"{item['quantity']:.3f}"
        unit_price_usd_text = f"{int(item['unit_price_usd'])}" if item['unit_price_usd'] == int(item['unit_price_usd']) else f"{item['unit_price_usd']:.3f}"
        unit_price_lbp_text = f"{int(item['unit_price_lbp'])}" if item['unit_price_lbp'] == int(item['unit_price_lbp']) else f"{item['unit_price_lbp']:.0f}"
        total_usd_text = f"{int(item['total_usd'])}" if item['total_usd'] == int(item['total_usd']) else f"{item['total_usd']:.2f}"
        total_lbp_text = f"{int(item['total_lbp'])}" if item['total_lbp'] == int(item['total_lbp']) else f"{item['total_lbp']:.0f}"
        
        self.items_table.item(row, 4).setText(quantity_text)
        self.items_table.item(row, 3).setText(f"{unit_price_usd_text} $")
        self.items_table.item(row, 2).setText(f"{unit_price_lbp_text} LBP")
        self.items_table.item(row, 1).setText(f"{total_usd_text} $")
        self.items_table.item(row, 0).setText(f"{total_lbp_text} LBP")
    
    def calculate_totals(self):
        """حساب المجاميع تلقائياً"""
        total_usd = sum(item['total_usd'] for item in self.items)
        total_lbp = sum(item['total_lbp'] for item in self.items)
        
        usd_text = f"{int(total_usd)} $" if total_usd == int(total_usd) else f"{total_usd:.2f} $"
        lbp_text = f"{int(total_lbp)} LBP" if total_lbp == int(total_lbp) else f"{total_lbp:.0f} LBP"
        
        self.total_usd.setText(usd_text)
        self.total_lbp.setText(lbp_text)

    def validate_customer_info(self):
        """التحقق من صحة معلومات الزبون"""
        return True  # التقسيط لا يتطلب معلومات إجبارية
    
    def save_invoice(self):
        """✅ حفظ الفاتورة مع تحديث المخزون فورياً وإرسال الدفعة تلقائياً"""
        if not self.items:
            self.show_message("تحذير", "الفاتورة لأصناف إضافة يرجى", "warning")
            return
        
        try:
            # ✅ التحقق من صحة التاريخ
            if not self.date_input.validate_date():
                self.show_message("تحذير", "صحيح تاريخ إدخال يرجى (yyyy-mm-dd أو yyyy/mm/dd)", "warning")
                return
            
            total_usd = sum(item['total_usd'] for item in self.items)
            total_lbp = sum(item['total_lbp'] for item in self.items)
            try:
                paid_amount = float(self.paid_amount_input.text() or 0)
            except ValueError:
                paid_amount = 0
            remaining_amount = total_usd - paid_amount
            
            if remaining_amount < 0:
                self.show_message("تحذير", "الكلي المجموع من أكبر يكون أن يمكن لا المبلغ المدفوع", "warning")
                return
            
            invoice_data = {
                'invoice_number': self.invoice_number,
                'customer_name': self.customer_name.text().strip() or 'محدد غير',
                'customer_phone': self.customer_phone.text().strip() or 'محدد غير',
                'address': self.address_input.text().strip() or '',  # ✅ إضافة العنوان
                'type': 'تقسيط',
                'items': self.items,
                'total_usd': total_usd,
                'total_lbp': total_lbp,
                'paid_amount': paid_amount,
                'remaining_amount': remaining_amount,
                'exchange_rate': self.exchange_rate,
                'logo_path': r"C:\Users\User\Desktop\chbib1\icons\logo.png",
                'date': self.date_input.get_date(),  # ✅ استخدام DateInput الجديد
                'payments': self.original_invoice_data.get('payments', []) if self.is_editing else []
            }
            
            # ✅ ✅ ✅ التعديل: إضافة UUID فريد للفاتورة
            if 'invoice_uuid' not in invoice_data:
                invoice_data['invoice_uuid'] = str(uuid.uuid4())
            
            # ✅ ✅ ✅ التعديل: إذا كان هناك مبلغ مدفوع، أضفه كدفعة أولية وإرساله إلى صفحة الدفعات
            if paid_amount > 0:
                initial_payment = {
                    'amount': paid_amount,
                    'date': datetime.now().strftime("%d-%m-%Y"),
                    'invoice_number': self.invoice_number,
                    'invoice_uuid': invoice_data['invoice_uuid']  # ✅ إضافة UUID
                }
                invoice_data['payments'].append(initial_payment)
                print(f"✅ تم إضافة دفعة أولية: {paid_amount} $")
                
                # ✅ ✅ ✅ التعديل الجديد: إرسال الدفعة تلقائياً إلى صفحة الدفعات
                self.send_payment_to_payments_page(invoice_data, initial_payment)
            
            self.invoice_data = invoice_data
            self.accept()
            
        except Exception as e:
            self.show_message("خطأ", f"في الحفظ خطأ حدث: {e}", "error")
    
    def send_payment_to_payments_page(self, invoice_data, payment_data):
        """✅ ✅ ✅ إرسال الدفعة تلقائياً إلى صفحة الدفعات عند حفظ فاتورة التقسيط"""
        try:
            # ✅ الحصول على بيانات الزبون من الـ parent
            if hasattr(self.parent, 'customer_id') and hasattr(self.parent, 'customer_name') and hasattr(self.parent, 'phone_number'):
                customer_id = self.parent.customer_id
                customer_name = self.parent.customer_name
                phone_number = self.parent.phone_number
                
                payments_file = "data/customer_payments.json"
                
                # ✅ التأكد من وجود المجلد والملف
                os.makedirs(os.path.dirname(payments_file), exist_ok=True)
                
                payments = []
                if os.path.exists(payments_file):
                    try:
                        with open(payments_file, 'r', encoding='utf-8') as f:
                            payments = json.load(f)
                    except:
                        payments = []
                
                # ✅ إنشاء معرف فريد للدفعة
                payment_id = f"{customer_id}_{invoice_data.get('invoice_uuid', '')}_{payment_data['date']}_{payment_data['amount']}"
                
                # ✅ التحقق من عدم تكرار الدفعة
                payment_exists = False
                for payment in payments:
                    if (payment.get('customer_id') == customer_id and
                        payment.get('invoice_uuid') == invoice_data.get('invoice_uuid') and
                        payment.get('amount') == payment_data['amount'] and
                        payment.get('date') == payment_data['date']):
                        payment_exists = True
                        break
                
                if not payment_exists:
                    # ✅ إضافة الدفعة الجديدة
                    new_payment = {
                        'id': len(payments) + 1,
                        'payment_id': payment_id,
                        'customer_id': customer_id,
                        'customer_name': customer_name,
                        'customer_phone': phone_number,
                        'invoice_number': invoice_data.get('invoice_number', ''),
                        'invoice_uuid': invoice_data.get('invoice_uuid', ''),  # ✅ إضافة UUID للفاتورة
                        'amount': payment_data['amount'],
                        'date': payment_data['date'],
                        'time': datetime.now().strftime('%H:%M:%S'),
                        'timestamp': datetime.now().isoformat(),
                        'exchange_rate': self.exchange_rate,
                        'amount_lbp': payment_data['amount'] * self.exchange_rate,
                        'type': 'دفعة أولى - فاتورة تقسيط'
                    }
                    
                    payments.append(new_payment)
                    
                    # ✅ حفظ الملف
                    with open(payments_file, 'w', encoding='utf-8') as f:
                        json.dump(payments, f, ensure_ascii=False, indent=2)
                        
                    print(f"✅ تم إرسال الدفعة تلقائياً إلى صفحة الدفعات:")
                    print(f"   - الزبون: {customer_name}")
                    print(f"   - الفاتورة: {invoice_data.get('invoice_number', '')}")
                    print(f"   - المبلغ: {payment_data['amount']} $")
                    print(f"   - التاريخ: {payment_data['date']}")
                    
                    # ✅ إرسال إشعار بتحديث المدفوعات
                    if hasattr(self.parent, 'send_payment_added_notification'):
                        self.parent.send_payment_added_notification({
                            'customer_name': customer_name,
                            'customer_phone': phone_number,
                            'invoice_number': invoice_data.get('invoice_number', ''),
                            'amount': payment_data['amount'],
                            'date': payment_data['date']
                        })
                else:
                    print(f"⚠️ الدفعة موجودة مسبقاً في customer_payments.json")
                    
            else:
                print("❌ لم يتم العثور على بيانات الزبون في الـ parent")
                
        except Exception as e:
            print(f"❌ خطأ في إرسال الدفعة تلقائياً إلى صفحة الدفعات: {e}")

    def export_invoice_html(self):
        """✅ ✅ ✅ التعديل: حفظ الفاتورة بصيغة HTML بدلاً من PDF"""
        try:
            if not self.items:
                self.show_message("تحذير", "لتصديرها أصناف توجد لا", "warning")
                return
            
            default_filename = f"تقسيط_فاتورة_{self.invoice_number}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
            filename, _ = QFileDialog.getSaveFileName(
                self, 
                "HTML كـ حفظ الفاتورة", 
                os.path.expanduser(f"~/Desktop/{default_filename}"),
                "HTML Files (*.html)"
            )
            
            if not filename:
                return
            
            if not filename.lower().endswith('.html'):
                filename += '.html'
            
            # ✅ ✅ ✅ التعديل: حفظ محتوى HTML في ملف
            content = self.generate_invoice_html_content()
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(content)
            
            self.show_message("نجاح", f"بنجاح HTML كـ حفظ الفاتورة تم\n{filename}", "info")
            
        except Exception as e:
            self.show_message("تحذير", f"في التصدير خطأ حدث: {str(e)}", "warning")
    
    def generate_invoice_html_content(self):
        """✅ ✅ ✅ إصلاح محتوى HTML لعرض جميع الأصناف والتفاصيل"""
        total_usd = sum(item['total_usd'] for item in self.items)
        total_lbp = sum(item['total_lbp'] for item in self.items)
        try:
            paid_amount = float(self.paid_amount_input.text() or 0)
        except ValueError:
            paid_amount = 0
        remaining_amount = total_usd - paid_amount
        
        logo_path = r"C:\Users\User\Desktop\chbib1\icons\logo_invoices.png"
        logo_base64 = ""
        if os.path.exists(logo_path):
            import base64
            with open(logo_path, "rb") as logo_file:
                logo_base64 = base64.b64encode(logo_file.read()).decode()
        
        # ✅ ✅ ✅ تكبير حجم الشعار إلى 120x120
        logo_html = f'<img src="data:image/png;base64,{logo_base64}" width="250" height="120" style="display: block; margin: 0 auto 20px auto;">' if logo_base64 else ""
        
        # ✅ ✅ ✅ إصلاح عرض الأصناف - التأكد من ظهور جميع الأصناف
        items_html = ""
        if self.items:
            for i, item in enumerate(self.items):
                quantity_text = f"{int(item['quantity'])}" if item['quantity'] == int(item['quantity']) else f"{item['quantity']:.3f}"
                unit_price_usd_text = f"{int(item['unit_price_usd'])}" if item['unit_price_usd'] == int(item['unit_price_usd']) else f"{item['unit_price_usd']:.3f}"
                total_usd_text = f"{int(item['total_usd'])}" if item['total_usd'] == int(item['total_usd']) else f"{item['total_usd']:.2f}"
                
                items_html += f"""
                <tr>
                    <td style="padding: 1px; border: 1px solid #ddd; font-size: 18px; font-weight: bold; text-align: right;">{item['product_name']}</td>
                    <td style="padding: 1px; border: 1px solid #ddd; font-size: 18px; text-align: right; font-weight: bold;">{item['unit']}</td>
                    <td style="padding: 1px; border: 1px solid #ddd; font-size: 18px; text-align: right; font-weight: bold;">{quantity_text}</td>
                    <td style="padding: 1px; border: 1px solid #ddd; font-size: 18px; text-align: right; font-weight: bold;">{unit_price_usd_text} $</td>
                    <td style="padding: 1px; border: 1px solid #ddd; font-size: 18px; text-align: right; font-weight: bold;">{total_usd_text} $</td>
                </tr>
                """
        else:
            items_html = """
            <tr>
                <td colspan="5" style="padding: 60px; border: 1px solid #ddd; font-size: 200px; text-align: center; font-weight: bold; color: #e74c3c;">
                    لا توجد أصناف في الفاتورة
                </td>
            </tr>
            """
        
        total_usd_text = f"{int(total_usd)} $" if total_usd == int(total_usd) else f"{total_usd:.2f} $"
        total_lbp_text = f"{int(total_lbp)} LBP" if total_lbp == int(total_lbp) else f"{total_lbp:.0f} LBP"
        paid_text = f"{int(paid_amount)} $" if paid_amount == int(paid_amount) else f"{paid_amount:.2f} $"
        remaining_text = f"{int(remaining_amount)} $" if remaining_amount == int(remaining_amount) else f"{remaining_amount:.2f} $"
        
        # ✅ ✅ ✅ إضافة معلومات إضافية عن الفاتورة
        content = f"""
        <html>
        <head>
        <meta charset="UTF-8">
        <style>
        body {{ 
            font-family: 'Arial', sans-serif; 
            margin: 60px; 
            direction: rtl; 
            line-height: 1.6;
            text-align: right
        }}
        .header {{ 
            text-align: center; 
            margin-bottom: 25px; 
            border-bottom: 3px solid #2c3e50;
            padding-bottom: 20px;
            margin-top: 0;  /* ✅ ✅ ✅ إزالة أي هامش علوي */
            padding-top: 0; /* ✅ ✅ ✅ إزالة أي حشوة علوية */
        }}
        
        h1 {{ 
            color: #2c3e50; 
            text-align: center; 
            margin: 12px 0; 
            font-size: 18px;
            font-weight: bold;
        }}
        .info {{ 
            margin: 20px 0; 
            background-color: transparent;
            padding: 20px; 
            border-radius: 8px; 
            border-right: 5px solid #3498db;
        }}
        .info p {{ 
            margin: 10px 0; 
            font-size: 18px;
            font-weight: bold;
        }}
        .payment-info {{
            margin: 20px 0;
            background-color: transparent;
            padding: 20px;
            border-radius: 8px;
            border-right: 5px solid #27ae60;
        }}
        .payment-info p {{
            margin: 8px 0;
            font-size: 18px;
            font-weight: bold;
        }}
        table {{ 
            width: 200%; 
            border-collapse: collapse; 
            margin-top: 100px; 
            font-size: 18px;
            border: 5px solid #2c3e50;
        }}
        th {{ 
            background-color: #2c3e50; 
            color: white; 
            padding: 12px;
            border: 2px solid #ddd;
            font-weight: bold;
            font-size: 18px;
            text-align: center;
        }}
        td {{
            padding: 10px;
            border: 2px solid #ddd;
            text-align: right;
            font-size: 18px;
        }}
        .total {{ 
            font-weight: bold; 
            color: #27ae60; 
            font-size: 18px; 
            background-color: #f8f9fa;
        }}
        .footer {{ 
            margin-top: 30px; 
            text-align: center; 
            font-size: 18px; 
            color: #7f8c8d; 
            border-top: 2px solid #ddd;
            padding-top: 20px;
        }}
        .invoice-details {{
            margin: 15px 0;
            padding: 15px;
            background-color: #fff3cd;
            border-radius: 8px;
            border-right: 5px solid #ffc107;
        }}
        .invoice-details p {{
            margin: 5px 0;
            font-size: px;
            font-weight: bold;
        }}
        </style>
        </head>
        <body>
        <div class="header">
            {logo_html}
            <h1>فاتورة تقسيط - رقم: {self.invoice_number}</h1>
        </div>
        
        <div class="info">
            <p><strong>الزبون اسم:</strong> {self.customer_name.text() or 'محدد غير'}</p>
            <p><strong>الهاتف رقم:</strong> {self.customer_phone.text() or 'محدد غير'}</p>
            <p><strong>العنوان:</strong> {self.address_input.text() or 'غير محدد'}</p>
            <p><strong>التاريخ:</strong> {self.date_input.get_date()}</p>
            
        
        <div class="payment-info">
            <p><strong>الإجمالي المبلغ:</strong> {total_usd_text}</p>
            <p><strong>المبلغ المدفوع:</strong> {paid_text}</p>
            <p><strong>المتبقي المبلغ:</strong> {remaining_text}</p>
        </div>
        
        <div class="invoice-details">
            <p><strong>عدد الأصناف:</strong> {len(self.items)} صنف</p>
           
        
        <table>
            <tr>
                <th>الصنف</th>
                <th>المبيع وحدة</th>
                <th>الكمية</th>
                <th>($) الوحدة سعر</th>
                <th>($) المجموع</th>
            </tr>
            {items_html}
            <tr class="total">
                <td colspan="4" style="text-align: left; font-size: 200px;">price $ </td>
                <td style="text-align: center; font-size: 200px;">{total_usd_text}</td>
            </tr>
            <tr class="total">
                <td colspan="4" style="text-align: left; font-size: 200px;"> LBP </td>
                <td style="text-align: center; font-size: 200px;">{total_lbp_text}</td>
            </tr>
        </table>

            
        </div>
        </body>
        </html>
        """
        
        return content
    
    def show_message(self, title, message, type="info", show_buttons=False):
        """✅ عرض رسائل للمستخدم بخلفية كحلية داكنة"""
        msg = QMessageBox(self)
        msg.setWindowTitle(title)
        msg.setText(message)
        
        # ✅ تنسيق الرسائل بخلفية كحلية داكنة
        msg.setStyleSheet("""
            QMessageBox {
                background-color: #1e2a3a;
            }
            QMessageBox QLabel {
                color: white;
                font-size: 16px;
                font-weight: bold;
                font-family: Arial;
            }
            QMessageBox QPushButton {
                background-color: #3498db;
                color: white;
                padding: 10px 20px;
                border: none;
                border-radius: 5px;
                font-size: 16px;
                font-weight: bold;
                font-family: Arial;
                min-width: 100px;
            }
            QMessageBox QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        
        if type == "warning":
            msg.setIcon(QMessageBox.Warning)
        elif type == "error":
            msg.setIcon(QMessageBox.Critical)
        elif type == "question":
            msg.setIcon(QMessageBox.Question)
            msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
            msg.setDefaultButton(QMessageBox.No)
        else:
            msg.setIcon(QMessageBox.Information)
            
        if show_buttons and type == "question":
            return msg.exec()
        else:
            msg.exec()
            return None
    
    def get_invoice_data(self):
        return self.invoice_data

# ✅ ✅ ✅ إضافة كلاس فاتورة النقدي الجديد
class CashInvoiceDialog(QDialog):
    """نافذة إنشاء فاتورة نقدي جديدة"""
    def __init__(self, parent, exchange_rate, invoice_number, invoice_data=None):
        super().__init__(parent)
        self.exchange_rate = exchange_rate
        self.invoice_number = invoice_number
        self.items = []
        self.products = self.load_products_from_database()
        self.is_editing = invoice_data is not None
        self.original_invoice_data = invoice_data
        
        # ✅ ضبط حجم النافذة
        screen = self.screen()
        screen_size = screen.availableSize()
        min_width = int(screen_size.width() * 0.9)
        min_height = int(screen_size.height() * 0.8)
        
        self.setMinimumSize(min_width, min_height)
        
        self.setup_ui()
        self.setup_enter_shortcut()
        
        # ✅ إذا كنا في وضع التعديل، نقوم بتحميل بيانات الفاتورة
        if self.is_editing:
            self.load_invoice_data()
    
    def load_invoice_data(self):
        """✅ تحميل بيانات الفاتورة للتعديل"""
        if self.original_invoice_data:
            # تحميل التاريخ
            if 'date' in self.original_invoice_data:
                date_str = self.original_invoice_data['date'].split(' ')[0]  # أخذ الجزء الخاص بالتاريخ فقط
                try:
                    # ✅ استخدام DateInput الجديد
                    self.date_input.set_date(date_str)
                except:
                    pass
            
            # تحميل بيانات العميل
            self.customer_name.setText(self.original_invoice_data.get('customer_name', ''))
            self.customer_phone.setText(self.original_invoice_data.get('customer_phone', ''))
            
            # ✅ تحميل العنوان
            self.address_input.setText(self.original_invoice_data.get('address', ''))
            
            # تحميل الأصناف
            self.items = self.original_invoice_data.get('items', [])
            self.update_items_table()
            self.calculate_totals()
    
    def setup_enter_shortcut(self):
        """✅ ✅ ✅ التعديل: تعطيل زر Enter لإضافة الأصناف وتفعيله فقط للحفظ"""
        # تعطيل Enter لإضافة الأصناف
        enter_shortcut = QShortcut(QKeySequence("Return"), self)
        enter_shortcut.setEnabled(False)
        enter_shortcut = QShortcut(QKeySequence("Enter"), self)
        enter_shortcut.setEnabled(False)
        
        # تفعيل Enter فقط لحفظ الفاتورة
        self.save_shortcut = QShortcut(QKeySequence("Return"), self)
        self.save_shortcut.activated.connect(self.save_invoice)
        self.save_shortcut = QShortcut(QKeySequence("Enter"), self)
        self.save_shortcut.activated.connect(self.save_invoice)
        
        self.disable_enter_on_lineedits()
    
    def disable_enter_on_lineedits(self):
        """✅ تعطيل زر Enter على جميع الحقول النصية"""
        for child in self.findChildren(QLineEdit):
            enter_shortcut = QShortcut(QKeySequence("Return"), child)
            enter_shortcut.setEnabled(False)
            enter_shortcut = QShortcut(QKeySequence("Enter"), child)
            enter_shortcut.setEnabled(False)
            
        for child in self.findChildren(QComboBox):
            enter_shortcut = QShortcut(QKeySequence("Return"), child)
            enter_shortcut.setEnabled(False)
            enter_shortcut = QShortcut(QKeySequence("Enter"), child)
            enter_shortcut.setEnabled(False)
            
        for child in self.findChildren(DateInput):
            enter_shortcut = QShortcut(QKeySequence("Return"), child)
            enter_shortcut.setEnabled(False)
            enter_shortcut = QShortcut(QKeySequence("Enter"), child)
            enter_shortcut.setEnabled(False)

    def load_products_from_database(self):
        """✅ تحميل الأصناف من قاعدة البيانات مع تحديث الأسعار بناءً على سعر الصرف"""
        try:
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            
            c.execute("""
                SELECT 
                    id, name, buy_unit, sell_unit, buy_price, sell_price, 
                    quantity, currency 
                FROM Items 
                ORDER BY name
            """)
            
            products = []
            for row in c.fetchall():
                product = {
                    'id': row[0],
                    'name': row[1],
                    'buy_unit': row[2],
                    'sell_unit': row[3],
                    'buy_price': float(row[4]),
                    'sell_price': float(row[5]),
                    'stock': float(row[6]),
                    'currency': row[7]
                }
                
                # ✅ تحويل الأسعار بناءً على العملة وسعر الصرف الحالي
                if product['currency'].upper() == 'LBP':
                    product['buy_price_usd'] = product['buy_price'] / self.exchange_rate
                    product['sell_price_usd'] = product['sell_price'] / self.exchange_rate
                else:
                    product['buy_price_usd'] = product['buy_price']
                    product['sell_price_usd'] = product['sell_price']
                
                products.append(product)
            
            conn.close()
            return products
            
        except Exception as e:
            print(f"❌ خطأ في تحميل الأصناف من قاعدة البيانات: {e}")
            return []

    def get_item_sell_units(self, item_id):
        """✅ جلب وحدات المبيع الخاصة بصنف معين من قاعدة البيانات"""
        try:
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute("SELECT sell_unit FROM ItemSellUnits WHERE item_id=? ORDER BY sell_unit", (item_id,))
            units = [row[0] for row in c.fetchall()]
            conn.close()
            
            if not units:
                c.execute("SELECT sell_unit FROM Items WHERE id=?", (item_id,))
                default_unit = c.fetchone()
                if default_unit and default_unit[0]:
                    units = [default_unit[0]]
            
            return units if units else ["قطعة"]
            
        except Exception as e:
            print(f"❌ خطأ في جلب وحدات المبيع للصنف {item_id}: {e}")
            return ["قطعة"]

    def setup_ui(self):
        title = f"فاتورة نقدي - رقم: {self.invoice_number}"
        if self.is_editing:
            title = f"تعديل فاتورة نقدي - رقم: {self.invoice_number}"
        
        self.setWindowTitle(title)
        
        # ✅ خلفية كحلية داكنة
        self.setStyleSheet("""
            QDialog {
                background-color: #1e2a3a;
                border: 2px solid #34495e;
                border-radius: 10px;
            }
            QGroupBox {
                color: white;
                font-size: 16px;
                font-weight: bold;
                font-family: Arial;
                border: 2px solid #34495e;
                border-radius: 8px;
                background-color: rgba(30, 42, 58, 0.9);
                margin-top: 8px;
                padding: 10px;
            }
            QLabel {
                color: white;
                font-size: 16px;
                font-weight: bold;
                font-family: Arial;
            }
        """)
        
        layout = QVBoxLayout(self)
        
        # ✅ الهيدر مع العنوان والشعار
        header_layout = QHBoxLayout()
        
        title_label = QLabel(title)
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 28px;
                font-weight: bold;
                background-color: transparent;
                padding: 15px;
                font-family: Arial;
            }
        """)
        
        logo_label = QLabel()
        logo_pixmap = QPixmap(r"C:\Users\User\Desktop\chbib1\icons\logo.png")
        if not logo_pixmap.isNull():
            logo_label.setPixmap(logo_pixmap.scaled(80, 80, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        logo_label.setAlignment(Qt.AlignRight)
        
        header_layout.addStretch()
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(logo_label)
        
        layout.addLayout(header_layout)
        
        # ✅ حقل التاريخ - ✅ استخدام DateInput الجديد مع تعديل المحاذاة
        date_group = QGroupBox("")
        date_layout = QHBoxLayout()
        
        # ✅ تعديل المحاذاة: النقطتين فوق بعض ثم الحقل
        date_label = QLabel("تاريخ الفاتورة:")
        date_label.setStyleSheet("color: white; font-size: 16px; font-weight: bold; font-family: Arial;")
        
        self.date_input = DateInput()
        self.date_input.setPlaceholderText("ابحث عن تاريخ")
        
        date_layout.addStretch()
        date_layout.addWidget(self.date_input)
        date_layout.addWidget(date_label)
        
        date_group.setLayout(date_layout)
        layout.addWidget(date_group)
        
        # معلومات العميل - ✅ تعديل المحاذاة
        customer_group = QGroupBox("")
        customer_layout = QFormLayout()
        
        self.customer_name = QLineEdit()
        self.customer_name.setPlaceholderText("(اختياري) العميل اسم")
        self.customer_name.setStyleSheet("""
            QLineEdit {
                background-color: white; 
                color: black; 
                padding: 12px; 
                border-radius: 5px;
                font-size: 16px;
                border: 1px solid #bdc3c7;
                font-family: Arial;
                font-weight: bold;
                min-height: 35px;
            }
            QLineEdit:focus {
                border: 2px solid #3498db;
                background-color: #f8f9fa;
            }
        """)
        
        self.customer_phone = QLineEdit()
        self.customer_phone.setPlaceholderText("(اختياري) الهاتف رقم")
        self.customer_phone.setStyleSheet("""
            QLineEdit {
                background-color: white; 
                color: black; 
                padding: 12px; 
                border-radius: 5px;
                font-size: 16px;
                border: 1px solid #bdc3c7;
                font-family: Arial;
                font-weight: bold;
                min-height: 35px;
            }
            QLineEdit:focus {
                border: 2px solid #3498db;
                background-color: #f8f9fa;
            }
        """)
        phone_validator = QIntValidator(0, 999999999, self)
        self.customer_phone.setValidator(phone_validator)
        
        # ✅ ✅ ✅ إضافة حقل العنوان الجديد
        self.address_input = QLineEdit()
        self.address_input.setPlaceholderText("(اختياري) مكان الورشة")
        self.address_input.setStyleSheet("""
            QLineEdit {
                background-color: white; 
                color: black; 
                padding: 12px; 
                border-radius: 5px;
                font-size: 16px;
                border: 1px solid #bdc3c7;
                font-family: Arial;
                font-weight: bold;
                min-height: 35px;
            }
            QLineEdit:focus {
                border: 2px solid #3498db;
                background-color: #f8f9fa;
            }
        """)
        
        # ✅ تعديل المحاذاة: الحقول أولاً ثم النقطتين
        name_layout = QHBoxLayout()
        name_layout.addStretch()
        name_layout.addWidget(self.customer_name)
        name_layout.addWidget(QLabel("الاسم:"))
        
        phone_layout = QHBoxLayout()
        phone_layout.addStretch()
        phone_layout.addWidget(self.customer_phone)
        phone_layout.addWidget(QLabel("الهاتف:"))
        
        # ✅ ✅ ✅ إضافة صف العنوان
        address_layout = QHBoxLayout()
        address_layout.addStretch()
        address_layout.addWidget(self.address_input)
        address_layout.addWidget(QLabel("مكان الورشة:"))
        
        customer_layout.addRow(name_layout)
        customer_layout.addRow(phone_layout)
        customer_layout.addRow(address_layout)  # ✅ إضافة صف العنوان
        customer_group.setLayout(customer_layout)
        layout.addWidget(customer_group)
        
        # إضافة الأصناف
        items_group = QGroupBox("")
        items_layout = QVBoxLayout()
        
        # عناصر التحكم
        control_layout = QHBoxLayout()
        
        self.product_combo = QComboBox()
        self.product_combo.setStyleSheet("""
            QComboBox {
                background-color: white; 
                color: black; 
                padding: 12px; 
                border-radius: 5px;
                font-size: 16px;
                border: 1px solid #bdc3c7;
                min-width: 200px;
                font-family: Arial;
                font-weight: bold;
                min-height: 35px;
            }
            QComboBox:focus {
                border: 2px solid #3498db;
                background-color: #f8f9fa;
            }
            QComboBox QAbstractItemView {
                background-color: white;
                color: black;
                selection-background-color: #3498db;
                selection-color: white;
                border: 1px solid #bdc3c7;
                font-family: Arial;
                font-weight: bold;
                font-size: 14px;
            }
        """)
        if self.products:
            self.product_combo.addItems([p['name'] for p in self.products])
        else:
            self.product_combo.addItems(["لا توجد أصناف - الرجاء إضافة أصناف من صفحة الإدارة"])
        self.product_combo.currentIndexChanged.connect(self.on_product_changed)
        
        # ✅ حقل وحدات المبيع
        self.unit_combo = QComboBox()
        self.unit_combo.setStyleSheet("""
            QComboBox {
                background-color: white; 
                color: black; 
                padding: 12px; 
                border-radius: 5px;
                font-size: 16px;
                border: 1px solid #bdc3c7;
                min-width: 140px;
                font-family: Arial;
                font-weight: bold;
                min-height: 35px;
            }
            QComboBox:focus {
                border: 2px solid #3498db;
                background-color: #f8f9fa;
            }
            QComboBox QAbstractItemView {
                background-color: white;
                color: black;
                selection-background-color: #3498db;
                selection-color: white;
                border: 1px solid #bdc3c7;
                font-family: Arial;
                font-weight: bold;
                font-size: 14px;
            }
        """)
        
        self.quantity_input = QLineEdit()
        self.quantity_input.setPlaceholderText("الكمية أدخل")
        self.quantity_input.setText("1")
        self.quantity_input.setStyleSheet("""
            QLineEdit {
                background-color: white; 
                color: black; 
                padding: 12px; 
                border-radius: 5px;
                font-size: 16px;
                border: 1px solid #bdc3c7;
                min-width: 120px;
                font-family: Arial;
                font-weight: bold;
                min-height: 35px;
            }
            QLineEdit:focus {
                border: 2px solid #3498db;
                background-color: #f8f9fa;
            }
        """)
        quantity_validator = QDoubleValidator(0.001, 10000, 3, self)
        self.quantity_input.setValidator(quantity_validator)
        self.quantity_input.textChanged.connect(self.on_quantity_changed)
        
        add_btn = QPushButton("إضافة صنف ")
        add_btn.setStyleSheet("""
            QPushButton {
                background-color: white;
                color: #2c3e50;
                padding: 12px 25px;
                border: 2px solid #2c3e50;
                border-radius: 5px;
                font-size: 16px;
                font-weight: bold;
                font-family: Arial;
                min-height: 35px;
            }
            QPushButton:hover {
                background-color: #f8f9fa;
                border: 2px solid #34495e;
            }
        """)
        add_btn.clicked.connect(self.add_item)
        
        # ✅ تعديل المحاذاة: الحقول أولاً ثم التسميات
        control_layout.addStretch()
        control_layout.addWidget(self.product_combo)
        control_layout.addWidget(QLabel("الصنف:"))
        control_layout.addWidget(self.unit_combo)
        control_layout.addWidget(QLabel("المبيع وحدة:"))
        control_layout.addWidget(self.quantity_input)
        control_layout.addWidget(QLabel("الكمية:"))
        control_layout.addWidget(add_btn)
        
        items_layout.addLayout(control_layout)
        
        # جدول الأصناف
        table_layout = QVBoxLayout()
        
        self.items_table = QTableWidget()
        self.items_table.setColumnCount(7)
        self.items_table.setHorizontalHeaderLabels([
            "LBP المجموع", "$ المجموع", "LBP الوحدة سعر", "$ الوحدة سعر", "الكمية", "المبيع وحدة", "الصنف"
        ])
        
        self.items_table.setStyleSheet("""
            QTableWidget {
                background-color: white;
                border: 2px solid #2c3e50;
                border-radius: 8px;
                font-size: 14px;
                gridline-color: #bdc3c7;
                selection-background-color: #3498db;
                selection-color: black;
                font-family: Arial;
                font-weight: bold;
            }
            QHeaderView::section {
                background-color: #2c3e50;
                color: white;
                padding: 15px;
                border: none;
                font-weight: bold;
                font-size: 14px;
                font-family: Arial;
            }
            QTableWidget::item {
                padding: 12px;
                border-bottom: 1px solid #ecf0f1;
                font-size: 14px;
                color: #2c3e50;
                background-color: white;
                selection-background-color: #e3f2fd;
                selection-color: black;
                min-height: 45px;
                font-family: Arial;
                font-weight: bold;
            }
            QTableWidget::item:selected {
                background-color: #e3f2fd;
                color: black;
                border: 1px solid #3498db;
            }
            QTableWidget::item:focus {
                background-color: #e3f2fd;
                border: 1px solid #3498db;
                color: black;
            }
        """)
        
        self.items_table.setFocusPolicy(Qt.NoFocus)
        
        header = self.items_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)
        
        self.items_table.verticalHeader().setDefaultSectionSize(50)
        self.items_table.cellChanged.connect(self.on_cell_changed)
        
        # أزرار التحكم
        buttons_layout = QHBoxLayout()
        
        delete_item_btn = QPushButton("المحدد الصنف حذف 🗑️")
        delete_item_btn.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                padding: 12px 25px;
                border: none;
                border-radius: 5px;
                font-size: 16px;
                font-weight: bold;
                font-family: Arial;
                min-height: 35px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        delete_item_btn.clicked.connect(self.delete_selected_item)
        
        # ✅ ✅ ✅ التعديل: تغيير زر PDF إلى حفظ HTML
        save_btn = QPushButton("حفظ 💾")
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                padding: 12px 25px;
                border: none;
                border-radius: 5px;
                font-size: 16px;
                font-weight: bold;
                font-family: Arial;
                min-height: 35px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        save_btn.clicked.connect(self.export_invoice_html)  # ✅ تغيير الدالة المستدعاة
        
        buttons_layout.addWidget(delete_item_btn)
        buttons_layout.addStretch()
        buttons_layout.addWidget(save_btn)  # ✅ تغيير اسم الزر
        
        table_layout.addWidget(self.items_table)
        table_layout.addLayout(buttons_layout)
        
        items_layout.addLayout(table_layout)
        items_group.setLayout(items_layout)
        layout.addWidget(items_group)
        
        # المجاميع
        totals_layout = QHBoxLayout()
        
        self.total_usd = QLabel("0 $")
        self.total_usd.setStyleSheet("font-size: 20px; font-weight: bold; color: white; font-family: Arial;")
        
        self.total_lbp = QLabel("0 LBP")
        self.total_lbp.setStyleSheet("font-size: 20px; font-weight: bold; color: white; font-family: Arial;")
        
        totals_layout.addStretch()
        totals_layout.addWidget(QLabel(" المجموع بالدولار:"))
        totals_layout.addWidget(self.total_usd)
        totals_layout.addWidget(QLabel(" المجموع بالليرة:"))
        totals_layout.addWidget(self.total_lbp)
        
        layout.addLayout(totals_layout)
        
        # أزرار الحفظ والإلغاء - ✅ رفع الأزرار للأعلى
        button_layout = QHBoxLayout()
        
        save_text = "حفظ الفاتورة 💾" if not self.is_editing else "التعديلات حفظ 💾"
        save_btn = QPushButton(save_text)
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                padding: 15px 30px;
                border: none;
                border-radius: 6px;
                font-size: 18px;
                font-weight: bold;
                font-family: Arial;
                min-height: 40px;
                margin-top: 10px;
            }
            QPushButton:hover {
                background-color: #229954;
            }
        """)
        save_btn.clicked.connect(self.save_invoice)
        
        cancel_btn = QPushButton("❌ إلغاء")
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #95a5a6;
                color: white;
                padding: 15px 30px;
                border: none;
                border-radius: 6px;
                font-size: 18px;
                font-family: Arial;
                font-weight: bold;
                min-height: 40px;
                margin-top: 10px;
            }
            QPushButton:hover {
                background-color: #7f8c8d;
            }
        """)
        cancel_btn.clicked.connect(self.reject)
        
        button_layout.addWidget(save_btn)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
        
        # ✅ تحميل وحدات المبيع للصنف الأول عند فتح النافذة
        if self.products:
            self.load_sell_units_for_product(self.products[0]['id'])

    def on_product_changed(self):
        """✅ عند تغيير المنتج المحدد - تحميل وحدات المبيع الخاصة به"""
        product_index = self.product_combo.currentIndex()
        if product_index >= 0 and product_index < len(self.products):
            product = self.products[product_index]
            self.load_sell_units_for_product(product['id'])
        
        self.update_unit_price()

    def load_sell_units_for_product(self, product_id):
        """✅ تحميل وحدات المبيع الخاصة بصنف معين"""
        try:
            units = self.get_item_sell_units(product_id)
            
            self.unit_combo.clear()
            if units:
                self.unit_combo.addItems(units)
            else:
                self.unit_combo.addItems(["قطعة"])
            
        except Exception as e:
            print(f"❌ خطأ في تحميل وحدات الصنف {product_id}: {e}")
            self.unit_combo.clear()
            self.unit_combo.addItems(["قطعة"])

    def on_quantity_changed(self):
        """عند تغيير الكمية - تحديث الأسعار تلقائياً"""
        self.update_unit_price()

    def update_unit_price(self):
        """✅ تحديث سعر الوحدة بناءً على المنتج والكمية وسعر الصرف"""
        product_index = self.product_combo.currentIndex()
        if product_index >= 0 and product_index < len(self.products):
            product = self.products[product_index]
            quantity_text = self.quantity_input.text().strip()
            
            if quantity_text and quantity_text != '.':
                try:
                    quantity = float(quantity_text)
                    unit_price_usd_single = product['sell_price_usd'] * quantity
                    unit_price_lbp_single = unit_price_usd_single * self.exchange_rate
                except ValueError:
                    pass

    def on_cell_changed(self, row, column):
        """✅ تحديث تلقائي عند تعديل خلية في الجدول"""
        if row < 0 or row >= len(self.items):
            return
            
        if column == 2:  # عمود الكمية
            try:
                quantity_item = self.items_table.item(row, column)
                if quantity_item:
                    new_quantity_text = quantity_item.text().strip()
                    if not new_quantity_text:
                        return
                        
                    new_quantity = float(new_quantity_text)
                    old_quantity = self.items[row]['quantity']
                    
                    self.items[row]['quantity'] = new_quantity
                    
                    product = self.get_product_by_name(self.items[row]['product_name'])
                    if product:
                        unit_price_usd_single = product['sell_price_usd']
                        unit_price_lbp_single = unit_price_usd_single * self.exchange_rate
                        
                        total_usd = unit_price_usd_single * new_quantity
                        total_lbp = unit_price_lbp_single * new_quantity
                        
                        self.items[row]['unit_price_usd'] = unit_price_usd_single
                        self.items[row]['unit_price_lbp'] = unit_price_lbp_single
                        self.items[row]['total_usd'] = total_usd
                        self.items[row]['total_lbp'] = total_lbp
                        
                        self.update_table_row(row)
                        self.calculate_totals()
                        
            except ValueError:
                self.items_table.blockSignals(True)
                self.items_table.item(row, column).setText(str(self.items[row]['quantity']))
                self.items_table.blockSignals(False)
        
        elif column == 3:  # ✅ عمود سعر الوحدة $ - التعديل اليدوي
            try:
                price_item = self.items_table.item(row, column)
                if price_item:
                    new_price_text = price_item.text().replace('$', '').strip()
                    if not new_price_text:
                        return
                        
                    new_price = float(new_price_text)
                    old_price = self.items[row]['unit_price_usd']
                    
                    self.items[row]['unit_price_usd'] = new_price
                    self.items[row]['unit_price_lbp'] = new_price * self.exchange_rate
                    
                    quantity = self.items[row]['quantity']
                    self.items[row]['total_usd'] = new_price * quantity
                    self.items[row]['total_lbp'] = (new_price * self.exchange_rate) * quantity
                    
                    self.update_table_row(row)
                    self.calculate_totals()
                    
            except ValueError:
                self.items_table.blockSignals(True)
                self.items_table.item(row, column).setText(f"{self.items[row]['unit_price_usd']:.3f} $")
                self.items_table.blockSignals(False)

    def update_stock_quantity_single(self, product_id, quantity, operation):
        """✅ تحديث كمية مخزون صنف واحد - فوري"""
        try:
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            
            if operation == "subtract":
                c.execute("UPDATE Items SET quantity = quantity - ? WHERE id = ?", (quantity, product_id))
            elif operation == "add":
                c.execute("UPDATE Items SET quantity = quantity + ? WHERE id = ?", (quantity, product_id))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            print(f"❌ خطأ في تحديث المخزون: {e}")

    def get_product_by_name(self, product_name):
        """الحصول على بيانات المنتج بالاسم"""
        for product in self.products:
            if product['name'] == product_name:
                return product
        return None

    def check_stock_availability(self, product_name, quantity):
        """التحقق من توفر المخزون"""
        for product in self.products:
            if product['name'] == product_name:
                if quantity > product['stock']:
                    reply = self.show_message("المخزون تحذير", 
                        f"المتاح المخزون ({product['stock']}) {product_name} لأصناف ({quantity}) المطلوبة الكمية تتجاوز",
                        "warning", True)
                    return reply == QMessageBox.Yes
                return True
        return False

    def add_item(self):
        """✅ ✅ ✅ إضافة صنف إلى الفاتورة مع وحدة المبيع المحددة"""
        try:
            product_index = self.product_combo.currentIndex()
            if product_index < 0 or product_index >= len(self.products):
                self.show_message("تحذير", "صحيح صنف اختيار يرجى", "warning")
                return
            
            product = self.products[product_index]
            unit = self.unit_combo.currentText()
            quantity_text = self.quantity_input.text().strip()
            
            if not quantity_text:
                self.show_message("تحذير", "كمية إدخال يرجى", "warning")
                return
            
            try:
                quantity = float(quantity_text)
            except ValueError:
                self.show_message("تحذير", "صحيحة كمية إدخال يرجى", "warning")
                return
            
            if quantity <= 0:
                self.show_message("تحذير", "صحيحة كمية إدخال يرجى", "warning")
                return
            
            if not self.check_stock_availability(product['name'], quantity):
                return
            
            unit_price_usd_single = product['sell_price_usd']
            unit_price_lbp_single = unit_price_usd_single * self.exchange_rate
            
            total_usd = unit_price_usd_single * quantity
            total_lbp = unit_price_lbp_single * quantity
            
            item = {
                'product_name': product['name'],
                'unit': unit,
                'quantity': quantity,
                'unit_price_usd': unit_price_usd_single,
                'unit_price_lbp': unit_price_lbp_single,
                'total_usd': total_usd,
                'total_lbp': total_lbp,
                'purchase_price': product['buy_price_usd'] * quantity,
                'product_id': product['id']
            }
            
            self.items.append(item)
            self.update_items_table()
            self.calculate_totals()
            
            self.quantity_input.setText("1")
            
        except Exception as e:
            self.show_message("خطأ", f"خطأ حدث: {e}", "error")

    def delete_selected_item(self):
        """✅ حذف الصنف المحدد من الجدول"""
        selected_row = self.items_table.currentRow()
        if selected_row == -1:
            self.show_message("تحذير", "للحذف صنف تحديد يرجى", "warning")
            return
            
        if selected_row >= 0 and selected_row < len(self.items):
            item_to_delete = self.items[selected_row]
            reply = self.show_message("الحذف تأكيد", 
                f"'{item_to_delete['product_name']}' الصنف حذف تريد هل؟\n\n"
                f"{item_to_delete['quantity']} :الكمية\n\n"
                f"المخزون إلى الكمية استعادة سيتم ✓ نعم\n"
                f"الكمية استعادة دون فقط الصنف حذف سيتم ✗ لا", 
                "question", True)
            
            if reply == QMessageBox.Yes:
                self.update_stock_quantity_single(item_to_delete['product_id'], item_to_delete['quantity'], "add")
                self.items.pop(selected_row)
                self.update_items_table()
                self.calculate_totals()
                self.show_message("نجاح", "✅ بنجاح الصنف حذف و المخزون إلى الكمية استعادة تم", "info")
                
            elif reply == QMessageBox.No:
                self.items.pop(selected_row)
                self.update_items_table()
                self.calculate_totals()
                self.show_message("نجاح", "✅ بنجاح الصنف حذف تم", "info")
    
    def update_items_table(self):
        """✅ ✅ ✅ تحديث جدول الأصناف مع عرض وحدة المبيع"""
        self.items_table.blockSignals(True)
        
        self.items_table.setRowCount(len(self.items))
        
        for row, item in enumerate(self.items):
            quantity_text = f"{int(item['quantity'])}" if item['quantity'] == int(item['quantity']) else f"{item['quantity']:.3f}"
            unit_price_usd_text = f"{int(item['unit_price_usd'])}" if item['unit_price_usd'] == int(item['unit_price_usd']) else f"{item['unit_price_usd']:.3f}"
            unit_price_lbp_text = f"{int(item['unit_price_lbp'])}" if item['unit_price_lbp'] == int(item['unit_price_lbp']) else f"{item['unit_price_lbp']:.0f}"
            total_usd_text = f"{int(item['total_usd'])}" if item['total_usd'] == int(item['total_usd']) else f"{item['total_usd']:.2f}"
            total_lbp_text = f"{int(item['total_lbp'])}" if item['total_lbp'] == int(item['total_lbp']) else f"{item['total_lbp']:.0f}"
            
            product_item = QTableWidgetItem(item['product_name'])
            product_item.setBackground(QColor("white"))
            self.items_table.setItem(row, 6, product_item)
            
            unit_item = QTableWidgetItem(item['unit'])
            unit_item.setFlags(unit_item.flags() & ~Qt.ItemIsEditable)
            unit_item.setBackground(QColor("white"))
            self.items_table.setItem(row, 5, unit_item)
            
            quantity_item = QTableWidgetItem(quantity_text)
            quantity_item.setForeground(QColor("#2c3e50"))
            quantity_item.setBackground(QColor("white"))
            quantity_item.setFont(QFont("Arial", 12, QFont.Bold))
            self.items_table.setItem(row, 4, quantity_item)
            
            unit_price_usd_item = QTableWidgetItem(f"{unit_price_usd_text} $")
            unit_price_usd_item.setForeground(QColor("#2c3e50"))
            unit_price_usd_item.setBackground(QColor("white"))
            unit_price_usd_item.setFont(QFont("Arial", 12, QFont.Bold))
            self.items_table.setItem(row, 3, unit_price_usd_item)
            
            unit_price_lbp_item = QTableWidgetItem(f"{unit_price_lbp_text} LBP")
            unit_price_lbp_item.setFlags(unit_price_lbp_item.flags() & ~Qt.ItemIsEditable)
            unit_price_lbp_item.setBackground(QColor("white"))
            self.items_table.setItem(row, 2, unit_price_lbp_item)
            
            total_usd_item = QTableWidgetItem(f"{total_usd_text} $")
            total_usd_item.setFlags(total_usd_item.flags() & ~Qt.ItemIsEditable)
            total_usd_item.setBackground(QColor("white"))
            self.items_table.setItem(row, 1, total_usd_item)
            
            total_lbp_item = QTableWidgetItem(f"{total_lbp_text} LBP")
            total_lbp_item.setFlags(total_lbp_item.flags() & ~Qt.ItemIsEditable)
            total_lbp_item.setBackground(QColor("white"))
            self.items_table.setItem(row, 0, total_lbp_item)
        
        self.items_table.blockSignals(False)
    
    def update_table_row(self, row):
        """تحديث صف معين في الجدول"""
        if row < 0 or row >= len(self.items):
            return
            
        item = self.items[row]
        
        quantity_text = f"{int(item['quantity'])}" if item['quantity'] == int(item['quantity']) else f"{item['quantity']:.3f}"
        unit_price_usd_text = f"{int(item['unit_price_usd'])}" if item['unit_price_usd'] == int(item['unit_price_usd']) else f"{item['unit_price_usd']:.3f}"
        unit_price_lbp_text = f"{int(item['unit_price_lbp'])}" if item['unit_price_lbp'] == int(item['unit_price_lbp']) else f"{item['unit_price_lbp']:.0f}"
        total_usd_text = f"{int(item['total_usd'])}" if item['total_usd'] == int(item['total_usd']) else f"{item['total_usd']:.2f}"
        total_lbp_text = f"{int(item['total_lbp'])}" if item['total_lbp'] == int(item['total_lbp']) else f"{item['total_lbp']:.0f}"
        
        self.items_table.item(row, 4).setText(quantity_text)
        self.items_table.item(row, 3).setText(f"{unit_price_usd_text} $")
        self.items_table.item(row, 2).setText(f"{unit_price_lbp_text} LBP")
        self.items_table.item(row, 1).setText(f"{total_usd_text} $")
        self.items_table.item(row, 0).setText(f"{total_lbp_text} LBP")
    
    def calculate_totals(self):
        """حساب المجاميع تلقائياً"""
        total_usd = sum(item['total_usd'] for item in self.items)
        total_lbp = sum(item['total_lbp'] for item in self.items)
        
        usd_text = f"{int(total_usd)} $" if total_usd == int(total_usd) else f"{total_usd:.2f} $"
        lbp_text = f"{int(total_lbp)} LBP" if total_lbp == int(total_lbp) else f"{total_lbp:.0f} LBP"
        
        self.total_usd.setText(usd_text)
        self.total_lbp.setText(lbp_text)
    
    def validate_customer_info(self):
        """التحقق من صحة معلومات الزبون"""
        return True  # النقدي لا يتطلب معلومات إجبارية
    
    def save_invoice(self):
        """✅ حفظ الفاتورة مع تحديث المخزون فورياً"""
        if not self.items:
            self.show_message("تحذير", "الفاتورة لأصناف إضافة يرجى", "warning")
            return
        
        try:
            # ✅ التحقق من صحة التاريخ
            if not self.date_input.validate_date():
                self.show_message("تحذير", "صحيح تاريخ إدخال يرجى (yyyy-mm-dd أو yyyy/mm/dd)", "warning")
                return
            
            total_usd = sum(item['total_usd'] for item in self.items)
            total_lbp = sum(item['total_lbp'] for item in self.items)
            
            invoice_data = {
                'invoice_number': self.invoice_number,
                'customer_name': self.customer_name.text().strip() or 'محدد غير',
                'customer_phone': self.customer_phone.text().strip() or 'محدد غير',
                'address': self.address_input.text().strip() or '',  # ✅ إضافة العنوان
                'type': 'نقدي',
                'items': self.items,
                'total_usd': total_usd,
                'total_lbp': total_lbp,
                'paid_amount': total_usd,  # ✅ النقدي المدفوع يساوي الإجمالي
                'remaining_amount': 0,     # ✅ النقدي لا يوجد متبقي
                'exchange_rate': self.exchange_rate,
                'logo_path': r"C:\Users\User\Desktop\chbib1\icons\logo.png",
                'date': self.date_input.get_date()  # ✅ استخدام DateInput الجديد
            }
            
            # ✅ ✅ ✅ التعديل: إضافة UUID فريد للفاتورة
            if 'invoice_uuid' not in invoice_data:
                invoice_data['invoice_uuid'] = str(uuid.uuid4())
            
            self.invoice_data = invoice_data
            self.accept()
            
        except Exception as e:
            self.show_message("خطأ", f"في الحفظ خطأ حدث: {e}", "error")
    
    def export_invoice_html(self):
        """✅ ✅ ✅ التعديل: حفظ الفاتورة بصيغة HTML بدلاً من PDF"""
        try:
            if not self.items:
                self.show_message("تحذير", "لتصديرها أصناف توجد لا", "warning")
                return
            
            default_filename = f"فاتورة_{self.invoice_number}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
            filename, _ = QFileDialog.getSaveFileName(
                self, 
                "HTML كـ حفظ الفاتورة", 
                os.path.expanduser(f"~/Desktop/{default_filename}"),
                "HTML Files (*.html)"
            )
            
            if not filename:
                return
            
            if not filename.lower().endswith('.html'):
                filename += '.html'
            
            # ✅ ✅ ✅ التعديل: حفظ محتوى HTML في ملف
            content = self.generate_invoice_html_content()
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(content)
            
            self.show_message("نجاح", f"بنجاح HTML كـ حفظ الفاتورة تم\n{filename}", "info")
            
        except Exception as e:
            self.show_message("تحذير", f"في التصدير خطأ حدث: {str(e)}", "warning")
    
    def generate_invoice_html_content(self):
        """✅ ✅ ✅ إصلاح محتوى HTML لعرض جميع الأصناف والتفاصيل"""
        total_usd = sum(item['total_usd'] for item in self.items)
        total_lbp = sum(item['total_lbp'] for item in self.items)
        
        logo_path = r"C:\Users\User\Desktop\chbib1\icons\logo.png"
        logo_base64 = ""
        if os.path.exists(logo_path):
            import base64
            with open(logo_path, "rb") as logo_file:
                logo_base64 = base64.b64encode(logo_file.read()).decode()
        
        # ✅ ✅ ✅ تكبير حجم الشعار إلى 120x120
        logo_html = f'<img src="data:image/png;base64,{logo_base64}" width="120" height="120" style="display: block; margin: 0 auto;">' if logo_base64 else ""
        
        # ✅ ✅ ✅ إصلاح عرض الأصناف - التأكد من ظهور جميع الأصناف
        items_html = ""
        if self.items:
            for i, item in enumerate(self.items):
                quantity_text = f"{int(item['quantity'])}" if item['quantity'] == int(item['quantity']) else f"{item['quantity']:.3f}"
                unit_price_usd_text = f"{int(item['unit_price_usd'])}" if item['unit_price_usd'] == int(item['unit_price_usd']) else f"{item['unit_price_usd']:.3f}"
                total_usd_text = f"{int(item['total_usd'])}" if item['total_usd'] == int(item['total_usd']) else f"{item['total_usd']:.2f}"
                
                items_html += f"""
                <tr>
                    <td style="padding: 10px; border: 1px solid #ddd; font-size: 200px; font-weight: bold; text-align: right;">{item['product_name']}</td>
                    <td style="padding: 10px; border: 1px solid #ddd; font-size: 200px; text-align: center; font-weight: bold;">{item['unit']}</td>
                    <td style="padding: 10px; border: 1px solid #ddd; font-size: 200px; text-align: center; font-weight: bold;">{quantity_text}</td>
                    <td style="padding: 10px; border: 1px solid #ddd; font-size: 200px; text-align: center; font-weight: bold;">{unit_price_usd_text} $</td>
                    <td style="padding: 10px; border: 1px solid #ddd; font-size: 200px; text-align: center; font-weight: bold;">{total_usd_text} $</td>
                </tr>
                """
        else:
            items_html = """
            <tr>
                <td colspan="5" style="padding: 20px; border: 1px solid #ddd; font-size: 300px; text-align: center; font-weight: bold; color: #e74c3c;">
                    لا توجد أصناف في الفاتورة
                </td>
            </tr>
            """
        
        total_usd_text = f"{int(total_usd)} $" if total_usd == int(total_usd) else f"{total_usd:.2f} $"
        total_lbp_text = f"{int(total_lbp)} LBP" if total_lbp == int(total_lbp) else f"{total_lbp:.0f} LBP"
        
        # ✅ ✅ ✅ إضافة معلومات إضافية عن الفاتورة
        content = f"""
        <html>
        <head>
        <meta charset="UTF-8">
        <style>
        body {{ 
            font-family: 'Arial', sans-serif; 
            margin: 20px; 
            direction: rtl; 
            line-height: 1.6;
        }}
        .header {{ 
            text-align: center; 
            margin-bottom: 25px; 
            border-bottom: 15px solid #2c3e50;
            padding-bottom: 20px;
        }}
        h1 {{ 
            color: #2c3e50; 
            text-align: center; 
            margin: 12px 0; 
            font-size: 24px;
            font-weight: bold;
        }}
        .info {{ 
            margin: 20px 0; 
            background-color: #f8f9fa; 
            padding: 20px; 
            border-radius: 8px; 
            border-right: 5px solid #3498db;
        }}
        .info p {{ 
            margin: 10px 0; 
            font-size: 14px;
            font-weight: bold;
        }}
        .payment-info {{
            margin: 20px 0;
            background-color: #e8f5e8;
            padding: 20px;
            border-radius: 8px;
            border-right: 5px solid #27ae60;
        }}
        .payment-info p {{
            margin: 8px 0;
            font-size: 14px;
            font-weight: bold;
        }}
        table {{ 
            width: 130%; 
            border-collapse: collapse; 
            margin-top: 20px; 
            font-size: 14px;
            border: 3px solid #2c3e50;
        }}
        th {{ 
            background-color: #2c3e50; 
            color: white; 
            padding: 12px;
            border: 2px solid #ddd;
            font-weight: bold;
            font-size: 14px;
            text-align: center;
        }}
        td {{
            padding: 10px;
            border: 2px solid #ddd;
            text-align: right;
            font-size: 14px;
        }}
        .total {{ 
            font-weight: bold; 
            color: #27ae60; 
            font-size: 14px; 
            background-color: #f8f9fa;
        }}
        .footer {{ 
            margin-top: 30px; 
            text-align: center; 
            font-size: 12px; 
            color: #7f8c8d; 
            border-top: 2px solid #ddd;
            padding-top: 20px;
        }}
        .invoice-details {{
            margin: 15px 0;
            padding: 15px;
            background-color: #fff3cd;
            border-radius: 8px;
            border-right: 5px solid #ffc107;
        }}
        .invoice-details p {{
            margin: 5px 0;
            font-size: 12px;
            font-weight: bold;
        }}
        </style>
        </head>
        <body>
        <div class="header">
            {logo_html}
            <h1>فاتورة نقدي - رقم: {self.invoice_number}</h1>
        </div>
        
        <div class="info">
            <p><strong>الزبون اسم:</strong> {self.customer_name.text() or 'محدد غير'}</p>
            <p><strong>الهاتف رقم:</strong> {self.customer_phone.text() or 'محدد غير'}</p>
            <p><strong>العنوان:</strong> {self.address_input.text() or 'غير محدد'}</p>
            <p><strong>التاريخ:</strong> {self.date_input.get_date()}</p>
            <p><strong>الفاتورة نوع:</strong> نقدي</p>
            <p><strong>الصرف سعر:</strong> {self.exchange_rate:,.0f} LBP/$</p>
        </div>
        
        <div class="payment-info">
            <p><strong>الإجمالي المبلغ:</strong> {total_usd_text}</p>
            <p><strong>المبلغ المدفوع:</strong> {total_usd_text}</p>
            <p><strong>المتبقي المبلغ:</strong> 0 $</p>
        </div>
        
        <div class="invoice-details">
            <p><strong>عدد الأصناف:</strong> {len(self.items)} صنف</p>
            <p><strong>حالة الفاتورة:</strong> مكتملة</p>
        </div>
        
        <table>
            <tr>
                <th>الصنف</th>
                <th>المبيع وحدة</th>
                <th>الكمية</th>
                <th>($) الوحدة سعر</th>
                <th>($) المجموع</th>
            </tr>
            {items_html}
            <tr class="total">
                <td colspan="4" style="text-align: left; font-size: 14px;">الدولار بالإجمالي</td>
                <td style="text-align: center; font-size: 14px;">{total_usd_text}</td>
            </tr>
            <tr class="total">
                <td colspan="4" style="text-align: left; font-size: 14px;">اللبنانية الليرة بالإجمالي</td>
                <td style="text-align: center; font-size: 14px;">{total_lbp_text}</td>
            </tr>
        </table>
        
        <div class="footer">
            <p>معنا لتعاملكم شكراً - electronically هذه الفاتورة إنشاء تم</p>
            <p>التصدير تاريخ: {datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
        </div>
        </body>
        </html>
        """
        
        return content
    
    def show_message(self, title, message, type="info", show_buttons=False):
        """✅ عرض رسائل للمستخدم بخلفية كحلية داكنة"""
        msg = QMessageBox(self)
        msg.setWindowTitle(title)
        msg.setText(message)
        
        # ✅ تنسيق الرسائل بخلفية كحلية داكنة
        msg.setStyleSheet("""
            QMessageBox {
                background-color: #1e2a3a;
            }
            QMessageBox QLabel {
                color: white;
                font-size: 16px;
                font-weight: bold;
                font-family: Arial;
            }
            QMessageBox QPushButton {
                background-color: #3498db;
                color: white;
                padding: 10px 20px;
                border: none;
                border-radius: 5px;
                font-size: 16px;
                font-weight: bold;
                font-family: Arial;
                min-width: 100px;
            }
            QMessageBox QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        
        if type == "warning":
            msg.setIcon(QMessageBox.Warning)
        elif type == "error":
            msg.setIcon(QMessageBox.Critical)
        elif type == "question":
            msg.setIcon(QMessageBox.Question)
            msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
            msg.setDefaultButton(QMessageBox.No)
        else:
            msg.setIcon(QMessageBox.Information)
            
        if show_buttons and type == "question":
            return msg.exec()
        else:
            msg.exec()
            return None
    
    def get_invoice_data(self):
        return self.invoice_data

class CustomerInvoicesPage(QWidget):
    def __init__(self, parent, customer_id, customer_name, phone_number):
        super().__init__()
        self.parent = parent
        self.customer_id = customer_id
        self.customer_name = customer_name
        self.phone_number = phone_number
        self.exchange_rate = self.load_exchange_rate()
        self.all_invoices = []  # ✅ تخزين جميع الفواتير للبحث
        self.filtered_invoices = []  # ✅ تخزين الفواتير المصفاة للبحث
        self.refresh_timer = QTimer()  # ✅ إضافة مؤقت للتحديث التلقائي
        self.setup_refresh_timer()  # ✅ إعداد المؤقت
        
        # ✅ ضبط حجم النافذة ليكون بحجم الشاشة مع إمكانية التصغير
        screen = self.screen()
        screen_size = screen.availableSize()
        self.setMinimumSize(int(screen_size.width() * 0.5), int(screen_size.height() * 0.5))  # ✅ تصغير إلى 50%
        self.resize(screen_size.width(), screen_size.height())  # ✅ فتح بحجم الشاشة الكامل
        
        self.setWindowFlags(Qt.Window | Qt.WindowMinimizeButtonHint | Qt.WindowMaximizeButtonHint)  # ✅ إزالة زر الإغلاق من النافذة
        
        self.setup_ui()
        self.load_customer_data()
        self.setup_keyboard_shortcuts()  # ✅ ✅ ✅ إضافة اختصارات الكيبورد
        
    def setup_keyboard_shortcuts(self):
        """✅ ✅ ✅ إعداد اختصارات الكيبورد"""
        # تفعيل زر Delete لحذف الفاتورة المحددة
        self.delete_shortcut = QShortcut(QKeySequence("Delete"), self)
        self.delete_shortcut.activated.connect(self.delete_selected_invoice)
        
        # تفعيل زر Enter للموافقة على الحذف
        self.enter_shortcut = QShortcut(QKeySequence("Return"), self)
        self.enter_shortcut.activated.connect(self.confirm_delete)
        self.enter_shortcut = QShortcut(QKeySequence("Enter"), self)
        self.enter_shortcut.activated.connect(self.confirm_delete)
    
    def confirm_delete(self):
        """✅ ✅ ✅ الموافقة على الحذف عند الضغط على Enter"""
        # إذا كانت هناك رسالة تأكيد حذف معروضة، ننفذ الحذف
        if hasattr(self, 'delete_message_box') and self.delete_message_box.isVisible():
            self.delete_message_box.accept()
    
    def setup_refresh_timer(self):
        """✅ إعداد المؤقت للتحديث التلقائي"""
        self.refresh_timer.timeout.connect(self.auto_refresh_data)
        self.refresh_timer.start(2000)  # ✅ تحديث كل 2 ثانية
    
    def auto_refresh_data(self):
        """✅ التحديث التلقائي للبيانات"""
        try:
            # ✅ التحقق من وجود تغييرات في ملف customers.json
            current_stats = self.get_current_customer_stats()
            if hasattr(self, 'last_known_stats'):
                if current_stats != self.last_known_stats:
                    print("🔄 اكتشاف تغييرات في البيانات - إعادة التحميل...")
                    self.load_customer_data()
            
            self.last_known_stats = current_stats
        except Exception as e:
            print(f"⚠️ خطأ في التحديث التلقائي: {e}")
    
    def get_current_customer_stats(self):
        """✅ الحصول على الإحصائيات الحالية للزبون"""
        try:
            with open("data/customers.json", 'r', encoding='utf-8') as f:
                customers = json.load(f)
            
            for customer in customers:
                if (customer.get('name') == self.customer_name and 
                    customer.get('phone') == self.phone_number):
                    return {
                        'total_paid': customer.get('total_paid', 0),
                        'total_remaining': customer.get('total_remaining', 0),
                        'invoices_count': len(customer.get('invoices', []))
                    }
            return {}
        except:
            return {}
    
    def load_exchange_rate(self):
        """تحميل سعر الصرف"""
        try:
            exchange_file = "data/exchange_rate.json"
            if os.path.exists(exchange_file):
                with open(exchange_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data.get('exchange_rate', 89000)
            return 89000
        except:
            return 89000

    def setup_ui(self):
        """إنشاء واجهة صفحة الزبون"""
        self.setWindowTitle(f"فواتير الزبون - {self.customer_name}")
        
        # ✅ خلفية كحلية داكنة
        self.setStyleSheet("""
            QWidget {
                background-color: #1e2a3a;
            }
            QLabel {
                color: white;
                font-family: Arial;
                font-weight: bold;
                background-color: transparent;
            }
        """)
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(15)

        # ✅ الهيدر المعدل - إضافة زر الحجوزات بجانب زر الدفعات
        header_layout = QHBoxLayout()
        
        # زر الرجوع إلى صفحة الفواتير - ✅ إضافة صورة back.png فقط بدون خلفية حمراء
        back_btn = QPushButton()
        back_icon_path = r"C:\Users\User\Desktop\chbib1\icons\back.png"
        if os.path.exists(back_icon_path):
            back_icon = QIcon(back_icon_path)
            back_btn.setIcon(back_icon)
            back_btn.setIconSize(QSize(120 , 100))
            back_btn.setFixedSize(40,38)
        back_btn.setText("")  # ✅ إزالة النص
        back_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: rgba(0,0,0,0.);
                border-radius: 3px;
            }
        """)
        back_btn.clicked.connect(self.go_back_to_invoices)
        
        # عنوان الصفحة - معدل بحجم خط أكبر
        title = QLabel(f"فواتير الزبون: {self.customer_name}")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 28px;
                font-weight: bold;
                padding: 15px;
                background-color: transparent;
                font-family: Arial;
                border: none;
            }
        """)
        
        # ✅ زر الانتقال إلى صفحة الحجوزات - جديد
        reservations_btn = QPushButton("📋 الحجوزات")
        reservations_btn.setStyleSheet("""
            QPushButton {
                background-color: #8e44ad;
                color: white;
                padding: 12px 25px;
                border: none;
                border-radius: 6px;
                font-size: 16px;
                font-weight: bold;
                font-family: Arial;
                min-height: 35px;
            }
            QPushButton:hover {
                background-color: #7d3c98;
            }
        """)
        reservations_btn.clicked.connect(self.open_reservations_page)
        
        # ✅ زر الانتقال إلى صفحة الدفعات
        payments_btn = QPushButton("💰 الدفعات")
        payments_btn.setStyleSheet("""
            QPushButton {
                background-color: #2980b9;
                color: white;
                padding: 12px 25px;
                border: none;
                border-radius: 6px;
                font-size: 16px;
                font-weight: bold;
                font-family: Arial;
                min-height: 35px;
            }
            QPushButton:hover {
                background-color: #2471a3;
            }
        """)
        payments_btn.clicked.connect(self.open_payments_page)
        
        header_layout.addWidget(back_btn)
        header_layout.addStretch()
        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(reservations_btn)  # ✅ إضافة زر الحجوزات
        header_layout.addWidget(payments_btn)  # ✅ زر الدفعات
        
        main_layout.addLayout(header_layout)

        # ✅ ✅ ✅ إضافة قسم محركات البحث الجديد
        self.setup_search_section()
        main_layout.addLayout(self.search_layout)

        # قسم الإحصائيات - معدل بحجم خط أكبر
        self.setup_stats_section()
        main_layout.addLayout(self.stats_layout)

        # جدول الفواتير - معدل
        self.setup_invoices_table()
        main_layout.addWidget(self.invoices_table)

        # أزرار التحكم - معدلة بحجم أكبر وإضافة زر إضافة حجز
        buttons_layout = QHBoxLayout()
        
        self.add_invoice_btn = QPushButton("➕ إضافة فاتورة جديدة")
        self.add_invoice_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                padding: 15px 30px;
                border: none;
                border-radius: 6px;
                font-size: 18px;
                font-weight: bold;
                font-family: Arial;
                min-height: 45px;
            }
            QPushButton:hover {
                background-color: #229954;
            }
        """)
        self.add_invoice_btn.clicked.connect(self.add_new_invoice)
        
        # ✅ ✅ ✅ زر إضافة حجز جديد - بخلفية صفراء لامعة
        self.add_reservation_btn = QPushButton("➕ إضافة حجز")
        self.add_reservation_btn.setStyleSheet("""
            QPushButton {
                background-color: #ffff00;
                color: #2c3e50;
                padding: 15px 30px;
                border: none;
                border-radius: 6px;
                font-size: 18px;
                font-weight: bold;
                font-family: Arial;
                min-height: 45px;
            }
            QPushButton:hover {
                background-color: #f1c40f;
            }
        """)
        self.add_reservation_btn.clicked.connect(self.add_new_reservation)
        
        self.add_payment_btn = QPushButton("💰 إضافة دفعة جديدة")
        self.add_payment_btn.setStyleSheet("""
            QPushButton {
                background-color: #21618C;
                color: white;
                padding: 15px 30px;
                border: none;
                border-radius: 6px;
                font-size: 18px;
                font-weight: bold;
                font-family: Arial;
                min-height: 45px;
            }
            QPushButton:hover {
                background-color: #1B4F72;
            }
        """)
        self.add_payment_btn.clicked.connect(self.add_new_payment)
        
        # ✅ زر حذف الفاتورة المحددة
        self.delete_invoice_btn = QPushButton("🗑️ حذف الفاتورة المحددة")
        self.delete_invoice_btn.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                padding: 15px 30px;
                border: none;
                border-radius: 6px;
                font-size: 18px;
                font-weight: bold;
                font-family: Arial;
                min-height: 45px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        self.delete_invoice_btn.clicked.connect(self.delete_selected_invoice)
        
        buttons_layout.addWidget(self.add_invoice_btn)
        buttons_layout.addWidget(self.add_reservation_btn)  # ✅ إضافة زر الحجز
        buttons_layout.addWidget(self.add_payment_btn)
        buttons_layout.addWidget(self.delete_invoice_btn)
        buttons_layout.addStretch()
        
        main_layout.addLayout(buttons_layout)

    def setup_search_section(self):
        """✅ ✅ ✅ إعداد قسم محركات البحث الجديد"""
        self.search_layout = QHBoxLayout()
        
        # ✅ محرك البحث السريع - بحث في الأصناف والعنوان
        self.quick_search_input = QLineEdit()
        self.quick_search_input.setPlaceholderText("ابحث عن عنوان، صنف...")
        self.quick_search_input.setStyleSheet("""
            QLineEdit {
                background-color: white;
                color: black;
                padding: 12px;
                border-radius: 6px;
                font-size: 16px;
                border: 2px solid #3498db;
                font-family: Arial;
                font-weight: bold;
                min-width: 300px;
            }
            QLineEdit:focus {
                border: 2px solid #2980b9;
                background-color: #f8f9fa;
            }
        """)
        self.quick_search_input.textChanged.connect(self.search_invoices)
        
        # ✅ محرك البحث بالتاريخ
        self.date_search_input = QLineEdit()
        self.date_search_input.setPlaceholderText("ابحث عن تاريخ")
        self.date_search_input.setStyleSheet("""
            QLineEdit {
                background-color: white;
                color: black;
                padding: 12px;
                border-radius: 6px;
                font-size: 16px;
                border: 2px solid #e74c3c;
                font-family: Arial;
                font-weight: bold;
                min-width: 250px;
            }
            QLineEdit:focus {
                border: 2px solid #c0392b;
                background-color: #f8f9fa;
            }
        """)
        self.date_search_input.textChanged.connect(self.search_invoices)
        
        self.search_layout.addWidget(self.quick_search_input)
        self.search_layout.addWidget(self.date_search_input)
        self.search_layout.addStretch()

    def setup_stats_section(self):
        """إنشاء قسم الإحصائيات - معدل بحجم خط أكبر"""
        self.stats_layout = QHBoxLayout()
        
        # زر إظهار/إخفاء العين
        self.toggle_stats_btn = QPushButton("👁")
        self.toggle_stats_btn.setFixedSize(40, 40)
        self.toggle_stats_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: white;
                border: none;
                border-radius: 5px;
                font-size: 18px;
                font-weight: bold;
                font-family: Arial;
            }
            QPushButton:hover {
                background-color: rgba(255,255,255,0.1);
            }
        """)
        self.toggle_stats_btn.clicked.connect(self.toggle_stats_display)
        
        # ✅ ✅ ✅ التعديل: تكبير كلمة "المدفوع" إلى خط 22
        self.paid_group = QGroupBox()
        self.paid_group.setStyleSheet("""
            QGroupBox {
                color: white;
                font-size: 22px;  /* ✅ تكبير كلمة المدفوع إلى خط 22 */
                font-weight: bold;
                border: 2px solid #27ae60;
                border-radius: 8px;
                background-color: rgba(39, 174, 96, 0.3);
                padding: 10px;
                min-width: 300px;
                font-family: Arial;
            }
        """)
        
        paid_layout = QHBoxLayout()
        
        paid_label = QLabel("المدفوع:")
        paid_label.setStyleSheet("color: white; font-size: 22px; font-weight: bold; font-family: Arial;")
        paid_layout.addWidget(paid_label)
        
        self.paid_usd_label = QLabel("0 $")
        self.paid_usd_label.setStyleSheet("""
            QLabel {
                color: white; 
                font-weight: bold; 
                font-size: 21px; 
                background-color: transparent; 
                padding: 5px; 
                border-radius: 4px;
                font-family: Arial;
            }
        """)
        paid_layout.addWidget(self.paid_usd_label)
        
        paid_layout.addWidget(QLabel("|"))
        
        self.paid_lbp_label = QLabel("0 LBP")
        self.paid_lbp_label.setStyleSheet("""
            QLabel {
                color: white; 
                font-weight: bold; 
                font-size: 21px; 
                background-color: transparent; 
                padding: 5px; 
                border-radius: 4px;
                font-family: Arial;
            }
        """)
        paid_layout.addWidget(self.paid_lbp_label)
        
        paid_layout.addStretch()
        self.paid_group.setLayout(paid_layout)
        
        # ✅ ✅ ✅ التعديل: تكبير كلمة "المتبقي" إلى خط 22
        self.remaining_group = QGroupBox()
        self.remaining_group.setStyleSheet("""
            QGroupBox {
                color: white;
                font-size: 22px;  /* ✅ تكبير كلمة المتبقي إلى خط 22 */
                font-weight: bold;
                border: 2px solid #e74c3c;
                border-radius: 8px;
                background-color: rgba(231, 76, 60, 0.3);
                padding: 10px;
                min-width: 300px;
                font-family: Arial;
            }
        """)
        
        remaining_layout = QHBoxLayout()
        
        remaining_label = QLabel("المتبقي:")
        remaining_label.setStyleSheet("color: white; font-size: 22px; font-weight: bold; font-family: Arial;")
        remaining_layout.addWidget(remaining_label)
        
        self.remaining_usd_label = QLabel("0 $")
        self.remaining_usd_label.setStyleSheet("""
            QLabel {
                color: white; 
                font-weight: bold; 
                font-size: 21px; 
                background-color: transparent; 
                padding: 5px; 
                border-radius: 4px;
                font-family: Arial;
            }
        """)
        remaining_layout.addWidget(self.remaining_usd_label)
        
        remaining_layout.addWidget(QLabel("|"))
        
        self.remaining_lbp_label = QLabel("0 LBP")
        self.remaining_lbp_label.setStyleSheet("""
            QLabel {
                color: white; 
                font-weight: bold; 
                font-size: 21px; 
                background-color: transparent; 
                padding: 5px; 
                border-radius: 4px;
                font-family: Arial;
            }
        """)
        remaining_layout.addWidget(self.remaining_lbp_label)
        
        remaining_layout.addStretch()
        self.remaining_group.setLayout(remaining_layout)
        
        self.stats_layout.addWidget(self.toggle_stats_btn)
        self.stats_layout.addWidget(self.paid_group)
        self.stats_layout.addWidget(self.remaining_group)
        self.stats_layout.addStretch()

    def setup_invoices_table(self):
        """إنشاء جدول الفواتير - معدل"""
        self.invoices_table = QTableWidget()
        self.invoices_table.setColumnCount(6)  # ✅ إضافة عمود جديد للدفعات
        self.invoices_table.setHorizontalHeaderLabels([
    "رقم", "التاريخ", "النوع", "المبلغ ($)", "الحالة", "الدفعات"
        ])

        # ✅ محاذاة رأس عمود التاريخ لليمين (يسار الموظف)
        header = self.invoices_table.horizontalHeader()
        header.setDefaultAlignment(Qt.AlignRight)  # ✅ جميع العناوين تبدأ من اليمين
        
        self.invoices_table.setStyleSheet("""
            QTableWidget {
                background-color: white;
                border: 2px solid #2c3e50;
                border-radius: 8px;
                font-size: 16px;
                gridline-color: #bdc3c7;
                font-weight: bold;
                font-family: Arial;
                selection-background-color: #3498db;
                selection-color: white;
            }
            QHeaderView::section {
                background-color: #2c3e50;
                color: white;
                padding: 15px;
                border: none;
                font-weight: bold;
                font-size: 16px;
                font-family: Arial;
            }
            QTableWidget::item {
                padding: 12px;
                border-bottom: 1px solid #ecf0f1;
                font-size: 14px;
                font-weight: bold;
                font-family: Arial;
                background-color: white;
            }
            QTableWidget::item:selected {
                background-color: #3498db;
                color: white;
            }
        """)
        
        # ✅ إزالة المستطيل عند التحديد
        self.invoices_table.setFocusPolicy(Qt.NoFocus)
        
        self.invoices_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.invoices_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.invoices_table.setEditTriggers(QTableWidget.NoEditTriggers)
        
        # ✅ تعديل: الضغط المزدوج على أي مكان في الصف لفتح الفاتورة
        self.invoices_table.doubleClicked.connect(self.open_invoice_details)

    def open_invoice_details(self, index):
        """✅ ✅ ✅ إصلاح: فتح تفاصيل الفاتورة الصحيحة بعد البحث"""
        selected_row = self.invoices_table.currentRow()
        if selected_row >= 0:
            try:
                # ✅ ✅ ✅ التعديل: إلغاء التحديد المخفي بعد فتح التفاصيل
                self.clear_selection_after_operation()
                
                # ✅ استخدام الفواتير المصفاة إذا كان هناك بحث، وإلا استخدام جميع الفواتير
                if hasattr(self, 'filtered_invoices') and self.filtered_invoices:
                    invoices_to_use = self.filtered_invoices
                else:
                    invoices_to_use = self.all_invoices
                
                if selected_row < len(invoices_to_use):
                    invoice = invoices_to_use[selected_row]
                    
                    # ✅ فتح نافذة تعديل الفاتورة مع إمكانية التعديل
                    if invoice.get('type') == 'نقدي':
                        self.edit_cash_invoice(invoice)
                    else:
                        self.edit_installment_invoice(invoice)
                    
            except Exception as e:
                self.show_message("خطأ", f"حدث خطأ في فتح الفاتورة: {e}", "error")

    def edit_cash_invoice(self, invoice_data):
        """✅ تعديل الفاتورة النقدية المحددة"""
        try:
            # ✅ فتح نافذة تعديل الفاتورة النقدية
            invoice_dialog = CashInvoiceDialog(self, self.exchange_rate, invoice_data['invoice_number'], invoice_data)
            
            # ✅ ضبط حجم نافذة الفاتورة ليكون بحجم الشاشة مع إمكانية تصغيرها 50%
            screen = self.screen()
            screen_size = screen.availableSize()
            invoice_dialog.setMinimumSize(int(screen_size.width() * 0.5), int(screen_size.height() * 0.5))
            invoice_dialog.resize(screen_size.width(), screen_size.height())
            
            if invoice_dialog.exec() == QDialog.Accepted:
                new_invoice_data = invoice_dialog.get_invoice_data()
                self.update_customer_invoice(invoice_data, new_invoice_data)
                
        except Exception as e:
            self.show_message("خطأ", f"حدث خطأ في تعديل الفاتورة: {e}", "error")

    def edit_installment_invoice(self, invoice_data):
        """✅ تعديل الفاتورة التقسيط المحددة"""
        try:
            # ✅ فتح نافذة تعديل الفاتورة التقسيط
            invoice_dialog = InstallmentInvoiceDialog(self, self.exchange_rate, invoice_data['invoice_number'], invoice_data)
            
            # ✅ ضبط حجم نافذة الفاتورة ليكون بحجم الشاشة مع إمكانية تصغيرها 50%
            screen = self.screen()
            screen_size = screen.availableSize()
            invoice_dialog.setMinimumSize(int(screen_size.width() * 0.5), int(screen_size.height() * 0.5))
            invoice_dialog.resize(screen_size.width(), screen_size.height())
            
            if invoice_dialog.exec() == QDialog.Accepted:
                new_invoice_data = invoice_dialog.get_invoice_data()
                self.update_customer_invoice(invoice_data, new_invoice_data)
                
        except Exception as e:
            self.show_message("خطأ", f"حدث خطأ في تعديل الفاتورة: {e}", "error")

    def update_customer_invoice(self, old_invoice_data, new_invoice_data):
        """✅ تحديث الفاتورة بعد التعديل"""
        try:
            with open("data/customers.json", 'r', encoding='utf-8') as f:
                customers = json.load(f)
            
            for customer in customers:
                if (customer.get('name') == self.customer_name and 
                    customer.get('phone') == self.phone_number):
                    
                    invoices = customer.get('invoices', [])
                    for i, invoice in enumerate(invoices):
                        if invoice.get('invoice_uuid') == old_invoice_data.get('invoice_uuid'):
                            # ✅ استعادة المخزون من الفاتورة القديمة
                            self.update_stock_quantity(old_invoice_data.get('items', []), "add")
                            
                            # ✅ تحديث الفاتورة بالبيانات الجديدة
                            invoices[i] = new_invoice_data
                            
                            # ✅ خصم المخزون للفاتورة الجديدة
                            self.update_stock_quantity(new_invoice_data.get('items', []), "subtract")
                            
                            # ✅ تحديث إحصائيات الزبون
                            self.update_customer_stats(customer, old_invoice_data, new_invoice_data)
                            break
                    
                    break
            
            with open("data/customers.json", 'w', encoding='utf-8') as f:
                json.dump(customers, f, ensure_ascii=False, indent=2)
            
            # ✅ ✅ ✅ التعديل: إلغاء التحديد المخفي بعد التعديل
            self.clear_selection_after_operation()
            
            # ✅ إعادة تحميل البيانات
            self.load_customer_data()
            
            self.show_message("نجاح", "✅ تم تعديل الفاتورة بنجاح", "info")
            
        except Exception as e:
            self.show_message("خطأ", f"حدث خطأ في تعديل الفاتورة: {e}", "error")

    def update_customer_stats(self, customer, old_invoice, new_invoice):
        """✅ تحديث إحصائيات الزبون بعد التعديل"""
        try:
            old_total = old_invoice.get('total_usd', 0)
            new_total = new_invoice.get('total_usd', 0)
            old_paid = old_invoice.get('paid_amount', 0)
            new_paid = new_invoice.get('paid_amount', 0)
            
            difference_total = new_total - old_total
            difference_paid = new_paid - old_paid
            difference_remaining = (new_total - new_paid) - (old_total - old_paid)
            
            # ✅ تحديث الإجمالي
            customer['total_amount'] = customer.get('total_amount', 0) + difference_total
            customer['total_paid'] = customer.get('total_paid', 0) + difference_paid
            customer['total_remaining'] = customer.get('total_remaining', 0) + difference_remaining
            
        except Exception as e:
            print(f"❌ خطأ في تحديث إحصائيات الزبون: {e}")

    def show_invoice_with_payments(self, invoice_data):
        """✅ عرض الفاتورة مع إمكانية إضافة الدفعات"""
        dialog = QDialog(self)
        dialog.setWindowTitle(f"فاتورة #{invoice_data.get('invoice_number', '')}")
        dialog.setFixedSize(800, 600)
        
        # ✅ خلفية كحلية داكنة
        dialog.setStyleSheet("""
            QDialog {
                background-color: #1e2a3a;
            }
            QLabel {
                color: white;
                font-family: Arial;
                font-weight: bold;
            }
        """)
        
        layout = QVBoxLayout(dialog)
        
        # معلومات الفاتورة
        info_group = QGroupBox("معلومات الفاتورة")
        info_layout = QFormLayout()
        
        invoice_number = QLabel(str(invoice_data.get('invoice_number', '')))
        invoice_date = QLabel(invoice_data.get('date', ''))
        invoice_type = QLabel(invoice_data.get('type', 'نقدي'))
        total_amount = QLabel(f"{invoice_data.get('total_usd', 0):.2f} $")
        paid_amount = QLabel(f"{invoice_data.get('paid_amount', 0):.2f} $")
        remaining_amount = QLabel(f"{invoice_data.get('remaining_amount', 0):.2f} $")
        
        info_layout.addRow("رقم الفاتورة:", invoice_number)
        info_layout.addRow("التاريخ:", invoice_date)
        info_layout.addRow("النوع:", invoice_type)
        info_layout.addRow("المبلغ الإجمالي:", total_amount)
        info_layout.addRow("المبلغ المدفوع:", paid_amount)
        info_layout.addRow("المبلغ المتبقي:", remaining_amount)
        
        info_group.setLayout(info_layout)
        layout.addWidget(info_group)
        
        # جدول الدفعات إذا كانت فاتورة تقسيط
        if invoice_data.get('type') == 'تقسيط':
            payments_group = QGroupBox("الدفعات")
            payments_layout = QVBoxLayout()
            
            payments_table = QTableWidget()
            payments_table.setColumnCount(2)  # ✅ إزالة عمود الوقت
            payments_table.setHorizontalHeaderLabels(["المبلغ", "التاريخ"])
            
            payments = invoice_data.get('payments', [])
            payments_table.setRowCount(len(payments))
            
            for row, payment in enumerate(payments):
                payments_table.setItem(row, 0, QTableWidgetItem(f"{payment.get('amount', 0):.2f} $"))
                payments_table.setItem(row, 1, QTableWidgetItem(payment.get('date', '')))
            
            payments_layout.addWidget(payments_table)
            
            # زر إضافة دفعة جديدة
            add_payment_btn = QPushButton("➕ إضافة دفعة جديدة")
            add_payment_btn.clicked.connect(lambda: self.add_payment_to_invoice(invoice_data, dialog))
            payments_layout.addWidget(add_payment_btn)
            
            payments_group.setLayout(payments_layout)
            layout.addWidget(payments_group)
        
        # أزرار الإغلاق
        buttons = QDialogButtonBox(QDialogButtonBox.Close)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        
        dialog.exec()

    def add_payment_to_invoice(self, invoice_data, parent_dialog):
        """✅ إضافة دفعة إلى الفاتورة"""
        payment_dialog = PaymentDialog(self, invoice_data, self.exchange_rate)
        
        if payment_dialog.exec() == QDialog.Accepted:
            payment_data = payment_dialog.get_payment_data()
            self.save_payment(invoice_data, payment_data)
            # ✅ التصحيح: استخدام parent_dialog.accept() بدلاً من self.accept()
            parent_dialog.accept()  
            self.load_customer_data()

    def save_payment(self, invoice_data, payment_data):
        """✅ ✅ ✅ التعديل الهام: حفظ الدفعة مع السماح بإضافة دفعات بنفس المبلغ"""
        try:
            print(f"💾 بدء حفظ الدفعة للفاتورة: {invoice_data.get('invoice_number', '')}")
            
            # 1. حفظ الدفعة في ملف customers.json
            with open("data/customers.json", 'r', encoding='utf-8') as f:
                customers = json.load(f)
            
            payment_saved = False
            invoice_updated = False
            
            for customer in customers:
                if (customer.get('name') == self.customer_name and 
                    customer.get('phone') == self.phone_number):
                    
                    invoices = customer.get('invoices', [])
                    for invoice in invoices:
                        if invoice.get('invoice_uuid') == invoice_data.get('invoice_uuid'):
                            # ✅ إضافة الدفعة للفاتورة
                            if 'payments' not in invoice:
                                invoice['payments'] = []
                            
                            # ✅ ✅ ✅ التعديل: السماح بإضافة دفعات بنفس المبلغ
                            # ✅ استخدام UUID فريد لكل دفعة بدلاً من التحقق من التكرار
                            payment_data['payment_uuid'] = str(uuid.uuid4())
                            payment_data['invoice_uuid'] = invoice_data.get('invoice_uuid')
                            payment_data['timestamp'] = datetime.now().isoformat()  # ✅ إضافة الطابع الزمني

                            invoice['payments'].append(payment_data)
                            
                            # ✅ ✅ ✅ التعديل الهام: حساب المبلغ المتبقي الحقيقي
                            total_amount = invoice.get('total_usd', 0)
                            current_paid = invoice.get('paid_amount', 0)
                            payment_amount = payment_data['amount']
                            
                            # ✅ حساب المبلغ المدفوع الجديد
                            new_paid_amount = current_paid + payment_amount
                            invoice['paid_amount'] = new_paid_amount
                            
                            # ✅ ✅ ✅ التعديل الهام: حساب المبلغ المتبقي مع التقريب الصحيح
                            real_remaining = total_amount - new_paid_amount
                            
                            # ✅ ✅ ✅ التعديل: استخدام تقريب صحيح لتجنب -0.00
                            if abs(real_remaining) < 0.009:  # إذا كان أقل من 0.01
                                invoice['remaining_amount'] = 0.0  # ضبط على 0.00 بالضبط
                            else:
                                invoice['remaining_amount'] = round(real_remaining, 2)  # تقريب لرقمين عشريين
                            
                            print(f"💰 تحديث المبالغ بعد الدفعة:")
                            print(f"   - الإجمالي: {total_amount:.2f} $")
                            print(f"   - المدفوع السابق: {current_paid:.2f} $")
                            print(f"   - الدفعة الجديدة: {payment_amount:.2f} $")
                            print(f"   - المدفوع الجديد: {new_paid_amount:.2f} $")
                            print(f"   - المتبقي الحقيقي: {real_remaining:.2f} $")
                            print(f"   - المتبقي بعد التقريب: {invoice['remaining_amount']:.2f} $")
                            
                            # ✅ ✅ ✅ التعديل: التحقق مما إذا كانت الفاتورة اكتملت بعد هذه الدفعة
                            if invoice['remaining_amount'] <= 0.009:
                                invoice['remaining_amount'] = 0.0  # تأكيد ضبط المتبقي على صفر
                                invoice_updated = True
                                print(f"✅ الفاتورة اكتملت بعد الدفعة! المدفوع: {new_paid_amount}، الإجمالي: {total_amount}")
                            
                            # ✅ تحديث إحصائيات الزبون
                            customer['total_paid'] = customer.get('total_paid', 0) + payment_amount
                            customer['total_remaining'] = max(0, customer.get('total_remaining', 0) - payment_amount)
                            
                            payment_saved = True
                            print(f"✅ تم تحديث الفاتورة في customers.json")
                            break
                    break
            
            with open("data/customers.json", 'w', encoding='utf-8') as f:
                json.dump(customers, f, ensure_ascii=False, indent=2)
            
            # 2. حفظ الدفعة في صفحة المدفوعات
            if payment_saved:
                success = self.save_payment_to_payments_page(invoice_data, payment_data)
                if success:
                    print(f"✅ تم حفظ الدفعة في customer_payments.json")
                    
                    # ✅ إرسال إشعار بتحديث المدفوعات
                    self.send_payment_added_notification({
                        'customer_name': self.customer_name,
                        'customer_phone': self.phone_number,
                        'invoice_number': invoice_data.get('invoice_number', ''),
                        'amount': payment_data['amount'],
                        'date': payment_data['date'],
                        'invoice_completed': invoice_updated  # ✅ إضافة علامة اكتمال الفاتورة
                    })
                else:
                    print("❌ فشل حفظ الدفعة في customer_payments.json")
            else:
                print("⚠️ لم يتم العثور على الفاتورة لحفظ الدفعة")
            
            # ✅ ✅ ✅ التعديل: إلغاء التحديد المخفي بعد إضافة الدفعة
            self.clear_selection_after_operation()
            
            # ✅ إعادة تحميل البيانات لتحديث الواجهة
            self.load_customer_data()
            
            # ✅ ✅ ✅ التعديل: إظهار رسالة خاصة إذا اكتملت الفاتورة
            if invoice_updated:
                self.show_message("اكتمال الفاتورة", "🎉 تم دفع المبلغ بالكامل! الفاتورة اكتملت بنجاح", "info")
            
            print("🎉 تم حفظ الدفعة بنجاح في كلا الملفين")
            return payment_saved
            
        except Exception as e:
            print(f"❌ حدث خطأ في حفظ الدفعة: {e}")
            return False
            
    def save_payment_to_payments_page(self, invoice_data, payment_data):
        """✅ ✅ ✅ حفظ الدفعة في صفحة المدفوعات - السماح بالدفعات المتكررة"""
        try:
            payments_file = "data/customer_payments.json"
            
            # ✅ التأكد من وجود المجلد والملف
            os.makedirs(os.path.dirname(payments_file), exist_ok=True)
            
            payments = []
            if os.path.exists(payments_file):
                try:
                    with open(payments_file, 'r', encoding='utf-8') as f:
                        payments = json.load(f)
                except:
                    payments = []
            
            # ✅ ✅ ✅ التعديل: استخدام UUID فريد لكل دفعة بدلاً من التحقق من التكرار
            payment_id = f"{self.customer_id}_{invoice_data.get('invoice_uuid', '')}_{payment_data['date']}_{payment_data['amount']}_{datetime.now().strftime('%H%M%S')}"
            
            # ✅ إضافة الدفعة الجديدة
            new_payment = {
                'id': len(payments) + 1,
                'payment_id': payment_id,
                'customer_id': self.customer_id,
                'customer_name': self.customer_name,
                'customer_phone': self.phone_number,
                'invoice_number': invoice_data.get('invoice_number', ''),
                'invoice_uuid': invoice_data.get('invoice_uuid', ''),  # ✅ إضافة UUID للفاتورة
                'amount': payment_data['amount'],
                'date': payment_data['date'],
                'time': datetime.now().strftime('%H:%M:%S'),
                'timestamp': datetime.now().isoformat(),
                'exchange_rate': self.exchange_rate,
                'amount_lbp': payment_data['amount'] * self.exchange_rate,
                'type': 'دفعة فاتورة تقسيط'
            }
            
            payments.append(new_payment)
            
            # ✅ حفظ الملف
            with open(payments_file, 'w', encoding='utf-8') as f:
                json.dump(payments, f, ensure_ascii=False, indent=2)
                
            print(f"✅ تم حفظ الدفعة في customer_payments.json:")
            print(f"   - الزبون: {self.customer_name}")
            print(f"   - الفاتورة: {invoice_data.get('invoice_number', '')}")
            print(f"   - المبلغ: {payment_data['amount']} $")
            print(f"   - التاريخ: {payment_data['date']}")
            print(f"   - customer_id: {self.customer_id}")
            
            return True
                
        except Exception as e:
            print(f"❌ خطأ في حفظ الدفعة في صفحة المدفوعات: {e}")
            return False

    def load_customer_data(self):
        """تحميل بيانات الزبون"""
        try:
            # تنظيف الدفعات المحذوفة أولاً
            self.cleanup_deleted_customer_payments()
            
            # تحميل بيانات الزبون من ملف الزبائن
            with open("data/customers.json", 'r', encoding='utf-8') as f:
                customers = json.load(f)
            
            customer_data = None
            for customer in customers:
                if (customer.get('name') == self.customer_name and 
                    customer.get('phone') == self.phone_number):
                    customer_data = customer
                    break
            
            if customer_data:
                # تحديث الإحصائيات
                total_paid = customer_data.get('total_paid', 0)
                total_remaining = customer_data.get('total_remaining', 0)
                
                # ✅ تنسيق الأرقام بدون كسور عشرية
                paid_usd_text = f"{int(total_paid)} $" if total_paid == int(total_paid) else f"{total_paid:.2f} $"
                paid_lbp_text = f"{int(total_paid * self.exchange_rate):,} LBP"
                
                remaining_usd_text = f"{int(total_remaining)} $" if total_remaining == int(total_remaining) else f"{total_remaining:.2f} $"
                remaining_lbp_text = f"{int(total_remaining * self.exchange_rate):,} LBP"
                
                self.paid_usd_label.setText(paid_usd_text)
                self.paid_lbp_label.setText(paid_lbp_text)
                
                self.remaining_usd_label.setText(remaining_usd_text)
                self.remaining_lbp_label.setText(remaining_lbp_text)
                
                # تحميل الفواتير
                self.all_invoices = customer_data.get('invoices', [])  
                invoices_updated = False
                for invoice in self.all_invoices:
                    if 'invoice_uuid' not in invoice:
                        invoice['invoice_uuid'] = str(uuid.uuid4())
                        print(f"✅ تم إضافة UUID للفاتورة القديمة: {invoice['invoice_number']}")
                        invoices_updated = True
    
                 # ✅ حفظ التعديلات إذا تم تحديث الفواتير
                if invoices_updated:
                    try:
                        with open("data/customers.json", 'w', encoding='utf-8') as f:
                            json.dump(customers, f, ensure_ascii=False, indent=2)
                        print("✅ تم حفظ التعديلات في customers.json")
                    except Exception as e:
                        print(f"❌ خطأ في حفظ التعديلات: {e}")
                self.filtered_invoices = self.all_invoices.copy()  # ✅ تهيئة الفواتير المصفاة
                self.load_invoices_table(self.all_invoices)
                
        except Exception as e:
            print(f"❌ خطأ في تحميل بيانات الزبون: {e}")

    def update_parent_invoice_counters(self):
        """✅ ✅ ✅ تحديث عدادات الفواتير في الصفحة الرئيسية"""
        try:
            # حاول الوصول إلى parent وتحديث العدادات
            if hasattr(self, 'parent') and self.parent:
                if hasattr(self.parent, 'update_invoice_counters'):
                    self.parent.update_invoice_counters()
                    print("✅ تم تحديث عدادات الفواتير في الصفحة الرئيسية")
                elif hasattr(self.parent, 'parent') and self.parent.parent:
                    if hasattr(self.parent.parent, 'update_invoice_counters'):
                        self.parent.parent.update_invoice_counters()
                        print("✅ تم تحديث عدادات الفواتير في الصفحة الرئيسية")
        except Exception as e:
            print(f"❌ خطأ في تحديث عدادات الفواتير: {e}")

    def load_invoices_table(self, invoices):
        """تحميل الفواتير في الجدول"""
        self.invoices_table.setRowCount(len(invoices))
        
        for row, invoice in enumerate(invoices):
            # ✅ رقم الفاتورة (الترتيب التلقائي) - يبدأ من 1 لكل زبون
            number_item = QTableWidgetItem(str(row + 1))
            number_item.setBackground(QColor("white"))
            self.invoices_table.setItem(row, 0, number_item)
            
            # ✅ التاريخ - ✅ استخدام DateInput الجديد
            # ✅ التاريخ - عرضه كما هو لكن بمحاذاة لليمين
            # ✅ التاريخ - تحويل التنسيق إذا كان yyyy-mm-dd إلى dd-mm-yyyy
            date_str = invoice.get('date', '')
            if date_str and '-' in date_str and len(date_str) == 10:
                parts = date_str.split('-')
                if len(parts[0]) == 4:  # إذا السنة أولاً
                    date_str = f"{parts[2]}-{parts[1]}-{parts[0]}"  # تحويل إلى dd-mm-yyyy
            date_item = QTableWidgetItem(date_str)
            date_item.setBackground(QColor("white"))
            date_item.setForeground(QColor("#2c3e50"))
            date_item.setFont(QFont("Arial", 12, QFont.Bold))
            date_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.invoices_table.setItem(row, 1, date_item)
            
            # النوع
            invoice_type = invoice.get('type', 'نقدي')
            type_item = QTableWidgetItem(invoice_type)
            type_item.setBackground(QColor("white"))
            if invoice_type == 'تقسيط':
                type_item.setForeground(QColor('#e74c3c'))
            else:
                type_item.setForeground(QColor('#27ae60'))
            self.invoices_table.setItem(row, 2, type_item)
            
            # المبلغ بالدولار
            total_usd = invoice.get('total_usd', 0)
            usd_text = f"{int(total_usd)} $" if total_usd == int(total_usd) else f"{total_usd:.2f} $"
            usd_item = QTableWidgetItem(usd_text)
            usd_item.setBackground(QColor("white"))
            self.invoices_table.setItem(row, 3, usd_item)
            
            # ✅ ✅ ✅ التعديل الهام: الحالة - حساب الحالة بناءً على المبلغ المتبقي الحقيقي
            if invoice_type == 'نقدي':
                status = "مكتمل"
            else:
                # ✅ ✅ ✅ التعديل: حساب الحالة بناءً على المبلغ المتبقي الحقيقي
                total_amount = invoice.get('total_usd', 0)
                paid_amount = invoice.get('paid_amount', 0)
                remaining_amount = total_amount - paid_amount
                
                # ✅ ✅ ✅ التعديل الهام: استخدام عتبة 0.009 بدلاً من 0.01 لتجنب مشاكل التقريب
                if abs(remaining_amount) < 0.009:  # إذا كان المتبقي أقل من 0.01 (مع هامش تقريب)
                    status = "مكتمل"
                else:
                    status = "معلق"
            
            status_item = QTableWidgetItem(status)
            status_item.setBackground(QColor("white"))
            if status == "معلق":
                status_item.setForeground(QColor('#e74c3c'))
            else:
                status_item.setForeground(QColor('#27ae60'))
            self.invoices_table.setItem(row, 4, status_item)
            
            # ✅ عمود الدفعات
            if invoice_type == 'تقسيط':
                payments_count = len(invoice.get('payments', []))
                payments_text = f"{payments_count} دفعة" if payments_count > 0 else "لا توجد دفعات"
            else:
                payments_text = "---"
            
            payments_item = QTableWidgetItem(payments_text)
            payments_item.setBackground(QColor("white"))
            self.invoices_table.setItem(row, 5, payments_item)

    def search_invoices(self):
        try:
            quick_search_text = self.quick_search_input.text().strip()
            date_search_text = self.date_search_input.text().strip()
            
            # ✅ إذا كانت جميع حقول البحث فارغة، عرض جميع الفواتير
            if not quick_search_text and not date_search_text:
                self.filtered_invoices = self.all_invoices.copy()
                self.load_invoices_table(self.all_invoices)
                return
            
            filtered_invoices = []
            
            for invoice in self.all_invoices:
                match_quick_search = False
                match_date_search = False
                
                # ✅ البحث السريع في الأصناف والعنوان
                if quick_search_text:
                    search_text_lower = quick_search_text.lower()
                    
                    # البحث في العنوان
                    address = invoice.get('address', '').lower()
                    if search_text_lower in address:
                        match_quick_search = True
                    
                    # البحث في الأصناف
                    if not match_quick_search:
                        for item in invoice.get('items', []):
                            product_name = item.get('product_name', '').lower()
                            if search_text_lower in product_name:
                                match_quick_search = True
                                break
                else:
                    match_quick_search = True  # إذا كان البحث السريع فارغاً
                
                # ✅ البحث بالتاريخ - إصلاح المقارنة
                if date_search_text:
                    # ✅ إصلاح: البحث البسيط في سلسلة التاريخ
                    invoice_date = invoice.get('date', '').lower()
                    search_date = date_search_text.lower()
                    
                    # ✅ البحث بأي جزء من التاريخ
                    if search_date in invoice_date:
                        match_date_search = True
                else:
                    match_date_search = True  # إذا كان البحث بالتاريخ فارغاً
                
                # ✅ إذا تطابقت جميع شروط البحث، أضف الفاتورة إلى النتائج
                if match_quick_search and match_date_search:
                    filtered_invoices.append(invoice)
            
            # ✅ حفظ الفواتير المصفاة واستخدامها للعرض
            self.filtered_invoices = filtered_invoices
            
            # ✅ عرض الفواتير المصفاة
            self.load_invoices_table(filtered_invoices)
            
        except Exception as e:
            print(f"❌ خطأ في البحث: {e}")
            # في حالة الخطأ، عرض جميع الفواتير
            self.filtered_invoices = self.all_invoices.copy()
            self.load_invoices_table(self.all_invoices)

    def normalize_date_for_search(self, date_str):
        """✅ ✅ ✅ إصلاح: تحويل التاريخ إلى تنسيق موحد للمقارنة (dd-mm-yyyy)"""
        if not date_str:
            return ""
        
        # إزالة المسافات الزائدة
        date_str = date_str.strip()
        
        # استبدال المحددات المختلفة بشرطة
        date_str = date_str.replace('/', '-').replace('\\', '-').replace('.', '-')
        
        try:
            # تقسيم التاريخ إلى أجزاء
            parts = date_str.split('-')
            
            if len(parts) == 3:
                day, month, year = parts
                
                # تنظيف الأجزاء من المسافات
                day = day.strip()
                month = month.strip()
                year = year.strip()
                
                # تأكد من أن اليوم والشهر مكونة من رقمين والسنة من 4 أرقام
                day = day.zfill(2)
                month = month.zfill(2)
                
                if len(year) == 2:
                    year = '20' + year  # افتراض القرن 21 للسنوات المكونة من رقمين
                elif len(year) == 4:
                    pass  # السنة صحيحة
                else:
                    return ""  # إذا كانت السنة غير صحيحة، ارجع سلسلة فارغة
                
                return f"{day}-{month}-{year}"
            
        except Exception as e:
            print(f"⚠️ خطأ في تحويل التاريخ '{date_str}': {e}")
        
        return ""

    def toggle_stats_display(self):
        """إظهار/إخفاء قسم الإحصائيات"""
        self.paid_group.setVisible(not self.paid_group.isVisible())
        self.remaining_group.setVisible(not self.remaining_group.isVisible())

    def add_new_invoice(self):
        """✅ إضافة فاتورة جديدة مع اختيار النوع"""
        try:
            # ✅ فتح نافذة اختيار نوع الفاتورة
            type_dialog = InvoiceTypeDialog(self, self.customer_id, self.customer_name, self.phone_number)
            
            if type_dialog.exec() == QDialog.Accepted:
                invoice_type = type_dialog.get_selected_type()
                
                if invoice_type == 'نقدي':
                    self.add_cash_invoice()
                elif invoice_type == 'تقسيط':
                    self.add_installment_invoice()
                
        except Exception as e:
            self.show_message("خطأ", f"حدث خطأ في إنشاء الفاتورة: {e}", "error")

    def add_cash_invoice(self):
        """✅ إضافة فاتورة نقدي جديدة"""
        try:
            # ✅ فتح نافذة الفاتورة النقدية الجديدة
            invoice_dialog = CashInvoiceDialog(self, self.exchange_rate, self.get_next_invoice_number())
            
            # ✅ ضبط حجم نافذة الفاتورة ليكون بحجم الشاشة مع إمكانية تصغيرها 50%
            screen = self.screen()
            screen_size = screen.availableSize()
            invoice_dialog.setMinimumSize(int(screen_size.width() * 0.5), int(screen_size.height() * 0.5))
            invoice_dialog.resize(screen_size.width(), screen_size.height())
            
            # ✅ تعبئة بيانات الزبون تلقائياً
            invoice_dialog.customer_name.setText(self.customer_name)
            invoice_dialog.customer_phone.setText(self.phone_number)
            
            if invoice_dialog.exec() == QDialog.Accepted:
                invoice_data = invoice_dialog.get_invoice_data()
                self.save_customer_invoice(invoice_data)
                
        except Exception as e:
            self.show_message("خطأ", f"حدث خطأ في إنشاء الفاتورة النقدية: {e}", "error")

    def add_installment_invoice(self):
        """✅ إضافة فاتورة التقسيط جديدة"""
        try:
            # ✅ فتح نافذة الفاتورة التقسيط الجديدة
            invoice_dialog = InstallmentInvoiceDialog(self, self.exchange_rate, self.get_next_invoice_number())
            
            # ✅ ضبط حجم نافذة الفاتورة ليكون بحجم الشاشة مع إمكانية تصغيرها 50%
            screen = self.screen()
            screen_size = screen.availableSize()
            invoice_dialog.setMinimumSize(int(screen_size.width() * 0.5), int(screen_size.height() * 0.5))
            invoice_dialog.resize(screen_size.width(), screen_size.height())
            
            # ✅ تعبئة بيانات الزبون تلقائياً
            invoice_dialog.customer_name.setText(self.customer_name)
            invoice_dialog.customer_phone.setText(self.phone_number)
            
            if invoice_dialog.exec() == QDialog.Accepted:
                invoice_data = invoice_dialog.get_invoice_data()
                self.save_customer_invoice(invoice_data)
                
        except Exception as e:
            self.show_message("خطأ", f"حدث خطأ في إنشاء الفاتورة التقسيط: {e}", "error")

    # ✅ ✅ ✅ إضافة دالة إضافة حجز جديدة
    def add_new_reservation(self):
        """✅ إضافة حجز جديد"""
        try:
            # ✅ فتح نافذة الحجز الجديدة
            reservation_dialog = ReservationDialog(self, self.exchange_rate, self.get_next_reservation_number())
            
            # ✅ ضبط حجم نافذة الحجز ليكون بحجم الشاشة مع إمكانية تصغيرها 50%
            screen = self.screen()
            screen_size = screen.availableSize()
            reservation_dialog.setMinimumSize(int(screen_size.width() * 0.5), int(screen_size.height() * 0.5))
            reservation_dialog.resize(screen_size.width(), screen_size.height())
            
            # ✅ تعبئة بيانات الزبون تلقائياً
            reservation_dialog.customer_name.setText(self.customer_name)
            reservation_dialog.customer_phone.setText(self.phone_number)
            
            if reservation_dialog.exec() == QDialog.Accepted:
                self.show_message("نجاح", "✅ تم حفظ الحجز بنجاح في صفحة الحجوزات", "info")
                
        except Exception as e:
            self.show_message("خطأ", f"حدث خطأ في إنشاء الحجز: {e}", "error")

    def get_next_reservation_number(self):
        """✅ الحصول على رقم الحجز التالي"""
        try:
            reservations_file = "data/customer_reservations.json"
            if not os.path.exists(reservations_file):
                return 1
            
            with open(reservations_file, 'r', encoding='utf-8') as f:
                reservations = json.load(f)
            
            max_number = 0
            for reservation in reservations:
                reservation_number = reservation.get('reservation_number', 0)
                if reservation_number > max_number:
                    max_number = reservation_number
            
            return max_number + 1
            
        except:
            return 1

    def get_next_invoice_number(self):
        """✅ الحصول على رقم الفاتورة التالي - يبدأ من 1 لكل زبون"""
        try:
            # تحميل آخر رقم فاتورة من ملف الزبائن لهذا الزبون المحدد
            with open("data/customers.json", 'r', encoding='utf-8') as f:
                customers = json.load(f)
            
            max_number = 0
            for customer in customers:
                if (customer.get('name') == self.customer_name and 
                    customer.get('phone') == self.phone_number):
                    
                    invoices = customer.get('invoices', [])
                    for invoice in invoices:
                        # ✅ استخدام customer_invoice_id بدلاً من invoice_number العام
                        customer_invoice_id = invoice.get('customer_invoice_id', 0)
                        if customer_invoice_id > max_number:
                            max_number = customer_invoice_id
                    break
            
            return max_number + 1
            
        except:
            return 1

    def save_customer_invoice(self, invoice_data):
        """✅ حفظ فاتورة الزبون"""
        try:
            with open("data/customers.json", 'r', encoding='utf-8') as f:
                customers = json.load(f)
            
            for customer in customers:
                if (customer.get('name') == self.customer_name and 
                    customer.get('phone') == self.phone_number):
                    
                    # ✅ ✅ ✅ التعديل: إضافة UUID فريد للفاتورة
                    if 'invoice_uuid' not in invoice_data:
                        invoice_data['invoice_uuid'] = str(uuid.uuid4())
                    
                    # ✅ تحديث إحصائيات الزبون
                    customer['total_invoices'] = customer.get('total_invoices', 0) + 1
                    customer['total_amount'] = customer.get('total_amount', 0) + invoice_data['total_usd']
                    
                    # ✅ تحديث المدفوعات والمتبقي بناءً على نوع الفاتورة
                    if invoice_data['type'] == 'نقدي':
                        customer['total_paid'] = customer.get('total_paid', 0) + invoice_data['total_usd']
                    else:  # تقسيط
                        customer['total_paid'] = customer.get('total_paid', 0) + invoice_data['paid_amount']
                        customer['total_remaining'] = customer.get('total_remaining', 0) + invoice_data['remaining_amount']
                    
                    customer['last_invoice_date'] = invoice_data['date']
                    
                    # ✅ إضافة الفاتورة إلى قائمة فواتير الزبون
                    if 'invoices' not in customer:
                        customer['invoices'] = []
                    
                    # ✅ ✅ ✅ التعديل: استخدام رقم فاتورة يبدأ من 1 لكل زبون
                    invoice_data['customer_invoice_id'] = len(customer['invoices']) + 1
                    
                    customer['invoices'].append(invoice_data)
                    
                    break
            
            with open("data/customers.json", 'w', encoding='utf-8') as f:
                json.dump(customers, f, ensure_ascii=False, indent=2)
            
            # ✅ تحديث المخزون في قاعدة البيانات
            self.update_stock_quantity(invoice_data['items'], "subtract")
            
            # ✅ ✅ ✅ إرسال الفاتورة إلى صفحة الفواتير
            self.send_invoice_to_invoices_page(invoice_data)
            self.update_parent_invoice_counters()
            
            # ✅ ✅ إرسال إشعار بإضافة فاتورة جديدة - إضافة جديدة
            self.send_invoice_added_notification(invoice_data)
            
            # ✅ ✅ ✅ التعديل: إلغاء التحديد المخفي بعد الإضافة
            self.clear_selection_after_operation()
            
            # ✅ إعادة تحميل البيانات
            self.load_customer_data()
            
            # ✅ عرض رسالة نجاح واحدة فقط
            self.show_message("نجاح", "✅ تم حفظ الفاتورة بنجاح", "info")
        except Exception as e:
            self.show_message("خطأ", f"حدث خطأ في حفظ الفاتورة: {e}", "error")

    def send_invoice_to_invoices_page(self, invoice_data):
        """✅ ✅ ✅ إرسال الفاتورة إلى صفحة الفواتير - الإصدار المصحح"""
        try:
            invoices_file = "data/invoices.json"
            invoices = []
            
            if os.path.exists(invoices_file):
                with open(invoices_file, 'r', encoding='utf-8') as f:
                    invoices = json.load(f)
            
            # ✅ التصحيح: استخدام type مباشرة من invoice_data
            invoice_type = invoice_data.get('type', 'نقدي')
            
            print(f"🔍 [تصحيح] نوع الفاتورة المرسلة: {invoice_type}")
            
            # ✅ إضافة الفاتورة الجديدة
            new_invoice = {
                'invoice_number': invoice_data['invoice_number'],
                'customer_name': invoice_data['customer_name'],
                'customer_phone': invoice_data['customer_phone'],
                'address': invoice_data.get('address', ''),  # ✅ إضافة العنوان
                'type': invoice_type,  # ✅ استخدام النوع مباشرة
                'total_usd': invoice_data['total_usd'],
                'total_lbp': invoice_data['total_lbp'],
                'paid_amount': invoice_data['paid_amount'],
                'remaining_amount': invoice_data['remaining_amount'],
                'date': invoice_data['date'],
                'items': invoice_data['items'],
                'exchange_rate': invoice_data['exchange_rate'],
                'invoice_uuid': invoice_data.get('invoice_uuid', '')  # ✅ إضافة UUID
            }
            
            invoices.append(new_invoice)
            
            with open(invoices_file, 'w', encoding='utf-8') as f:
                json.dump(invoices, f, ensure_ascii=False, indent=2)
                
            print(f"✅ تم إرسال الفاتورة {invoice_data['invoice_number']} ({invoice_type}) إلى صفحة الفواتير")
                
        except Exception as e:
            print(f"❌ خطأ في إرسال الفاتورة إلى صفحة الفواتير: {e}")

    def send_invoice_added_notification(self, invoice_data):
        """✅ إرسال إشعار بإضافة فاتورة جديدة لجميع الصفحات"""
        try:
            # محاولة الوصول لمدير الأحداث من خلال الـ parent
            if hasattr(self, 'parent') and hasattr(self.parent, 'event_manager'):
                event_manager = self.parent.event_manager
                event_manager.publish("invoice_added", invoice_data)
                print(f"✅ تم إرسال إشعار بفاتورة جديدة: {invoice_data['invoice_number']}")
            
            # محاولة أخرى من خلال الـ controller
            elif hasattr(self, 'controller') and hasattr(self.controller, 'event_manager'):
                event_manager = self.controller.event_manager
                event_manager.publish("invoice_added", invoice_data)
                print(f"✅ تم إرسال إشعار بفاتورة جديدة: {invoice_data['invoice_number']}")
            
            else:
                print("⚠️ لم يتم العثور على مدير الأحداث لإرسال الإشعار")
                
        except Exception as e:
            print(f"❌ خطأ في إرسال إشعار الفاتورة: {e}")

    def send_invoice_deleted_notification(self, invoice_data):
        """✅ إرسال إشعار بحذف فاتورة لجميع الصفحات"""
        try:
            # محاولة الوصول لمدير الأحداث من خلال الـ parent
            if hasattr(self, 'parent') and hasattr(self.parent, 'event_manager'):
                event_manager = self.parent.event_manager
                event_manager.publish("data_updated", {"action": "delete", "invoice": invoice_data})
                print(f"✅ تم إرسال إشعار بحذف فاتورة: {invoice_data['invoice_number']}")
            
            # محاولة أخرى من خلال الـ controller
            elif hasattr(self, 'controller') and hasattr(self.controller, 'event_manager'):
                event_manager = self.controller.event_manager
                event_manager.publish("data_updated", {"action": "delete", "invoice": invoice_data})
                print(f"✅ تم إرسال إشعار بحذف فاتورة: {invoice_data['invoice_number']}")
            
            else:
                print("⚠️ لم يتم العثور على مدير الأحداث لإرسال إشعار الحذف")
                
        except Exception as e:
            print(f"❌ خطأ في إرسال إشعار حذف الفاتورة: {e}")

    def send_payment_added_notification(self, payment_data):
        """✅ إرسال إشعار بإضافة دفعة جديدة لجميع الصفحات"""
        try:
            # محاولة الوصول لمدير الأحداث من خلال الـ parent
            if hasattr(self, 'parent') and hasattr(self.parent, 'event_manager'):
                event_manager = self.parent.event_manager
                event_manager.publish("payment_added", payment_data)
                print(f"✅ تم إرسال إشعار بدفعة جديدة: {payment_data['amount']} $")
            
            # محاولة أخرى من خلال الـ controller
            elif hasattr(self, 'controller') and hasattr(self.controller, 'event_manager'):
                event_manager = self.controller.event_manager
                event_manager.publish("payment_added", payment_data)
                print(f"✅ تم إرسال إشعار بدفعة جديدة: {payment_data['amount']} $")
            
            else:
                print("⚠️ لم يتم العثور على مدير الأحداث لإرسال إشعار الدفعة")
                
        except Exception as e:
            print(f"❌ خطأ في إرسال إشعار الدفعة: {e}")

    def update_stock_quantity(self, items, operation):
        """✅ تحديث كمية المخزون في قاعدة البيانات - فوري ومباشر"""
        try:
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            
            for item in items:
                product_id = item['product_id']
                quantity = item['quantity']
                
                if operation == "subtract":
                    c.execute("UPDATE Items SET quantity = quantity - ? WHERE id = ?", (quantity, product_id))
                elif operation == "add":
                    c.execute("UPDATE Items SET quantity = quantity + ? WHERE id = ?", (quantity, product_id))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            print(f"❌ خطأ في تحديث المخزون: {e}")

    def add_new_payment(self):
        """✅ ✅ ✅ التعديل: إضافة تحقق من حالة الفاتورة قبل إضافة دفعة جديدة"""
        selected_row = self.invoices_table.currentRow()
        if selected_row < 0:
            self.show_message("تحذير", "⚠️ يرجى اختيار فاتورة أولاً", "warning")
            return
            
        try:
            with open("data/customers.json", 'r', encoding='utf-8') as f:
                customers = json.load(f)
            
            for customer in customers:
                if (customer.get('name') == self.customer_name and 
                    customer.get('phone') == self.phone_number):
                    
                    invoices = customer.get('invoices', [])
                    if selected_row < len(invoices):
                        invoice_data = invoices[selected_row]
                        
                        if invoice_data.get('type') != 'تقسيط':
                            self.show_message("تحذير", "⚠️ يمكن إضافة دفعات فقط للفواتير التقسيط", "warning")
                            return
                        
                        # ✅ ✅ ✅ التعديل الجديد: التحقق من حالة الفاتورة
                        total_usd = invoice_data.get('total_usd', 0)
                        paid_amount = invoice_data.get('paid_amount', 0)
                        
                        # إذا كانت الفاتورة مكتملة (المبلغ المدفوع يساوي أو يزيد عن الإجمالي)
                        if paid_amount >= total_usd:
                            self.show_message(
                                "فاتورة مكتملة", 
                                "⚠️ هذه الفاتورة حسابها مكتمل ولا يمكن إضافة دفعة إليها\n\n"
                                "💡 يمكنك إضافة دفعة فقط إذا تم إضافة أصناف لاحقاً للفاتورة",
                                "warning"
                            )
                            return
                            
                        # ✅ ✅ ✅ التصحيح: إنشاء PaymentDialog ومعالجته بشكل صحيح
                        payment_dialog = PaymentDialog(self, invoice_data, self.exchange_rate)
                        
                        if payment_dialog.exec() == QDialog.Accepted:
                            payment_data = payment_dialog.get_payment_data()
                            self.save_payment(invoice_data, payment_data)
                            self.load_customer_data()
                        return
            
        except Exception as e:
            self.show_message("خطأ", f"❌ حدث خطأ في إضافة الدفعة: {e}", "error")

    # ✅ ✅ ✅ إضافة دالة فتح صفحة الحجوزات
    def open_reservations_page(self):
        """فتح صفحة حجوزات الزبون في نافذة مستقلة"""
        try:
            # ✅ استيراد من مجلد pages
            from pages.customer_reservations_page import CustomerReservationsPage
        
            self.reservations_page = CustomerReservationsPage(
                self.customer_name,  # اسم الزبون
                self  # الـ controller
            )
            self.reservations_page.show()
            print(f"✅ تم فتح صفحة الحجوزات للزبون: {self.customer_name}")
        except Exception as e:
            print(f"❌ خطأ في فتح صفحة الحجوزات: {e}")
            self.show_message("خطأ", f"حدث خطأ في فتح صفحة الحجوزات: {str(e)}", "error")
    def delete_selected_invoice(self):
        """✅ ✅ ✅ التعديل: حذف الفاتورة المحددة مع إصلاح مشكلة التحديد المخفي"""
        selected_row = self.invoices_table.currentRow()
        if selected_row < 0:
            self.show_message("تحذير", "⚠️ يرجى اختيار فاتورة للحذف", "warning")
            return
        
        try:
            with open("data/customers.json", 'r', encoding='utf-8') as f:
                customers = json.load(f)
            
            invoice_to_delete = None
            for customer in customers:
                if (customer.get('name') == self.customer_name and 
                    customer.get('phone') == self.phone_number):
                    
                    invoices = customer.get('invoices', [])
                    if selected_row < len(invoices):
                        invoice_to_delete = invoices[selected_row]
                        
                        # ✅ ✅ ✅ التعديل: الحصول على رقم الفاتورة الصحيح من الجدول
                        display_number = self.invoices_table.item(selected_row, 0).text()
                        
                        # ✅ ✅ ✅ التعديل: حفظ صف التحديد قبل الحذف
                        self.last_selected_row = selected_row
                        
                        # ✅ تأكيد الحذف مع عرض الرقم الصحيح
                        reply = self.show_message("تأكيد الحذف", 
                            f"هل أنت متأكد من حذف الفاتورة رقم {display_number}؟\n\nهذا الإجراء لا يمكن التراجع عنه!",
                            "question", True)
                        
                        if reply == QMessageBox.Yes:
                            # ✅ استعادة المخزون أولاً
                            self.update_stock_quantity(invoice_to_delete.get('items', []), "add")
                            
                            # ✅ حذف الفاتورة من القائمة
                            invoices.pop(selected_row)
                            
                            # ✅ تحديث إحصائيات الزبون
                            self.update_customer_stats_after_deletion(customer, invoice_to_delete)
                            
                            # ✅ ✅ ✅ حذف الفاتورة من صفحة الفواتير
                            self.delete_invoice_from_invoices_page(invoice_to_delete)
                            self.update_parent_invoice_counters()
                            
                            # ✅ ✅ ✅ حذف جميع الدفعات المرتبطة بهذه الفاتورة من صفحة المدفوعات
                            self.delete_invoice_payments_from_payments_page(invoice_to_delete)
                            
                            # ✅ ✅ إرسال إشعار بحذف فاتورة - إضافة جديدة
                            self.send_invoice_deleted_notification(invoice_to_delete)
                            
                            # ✅ حفظ التغييرات
                            with open("data/customers.json", 'w', encoding='utf-8') as f:
                                json.dump(customers, f, ensure_ascii=False, indent=2)
                            
                            # ✅ ✅ ✅ التعديل: إلغاء التحديد المخفي بعد الحذف
                            self.clear_selection_after_operation()
                            
                            # ✅ إعادة تحميل البيانات
                            self.load_customer_data()
                            
                            self.show_message("نجاح", "✅ تم حذف الفاتورة بنجاح", "info")
                        break
                    break
            
        except Exception as e:
            self.show_message("خطأ", f"❌ حدث خطأ في حذف الفاتورة: {e}", "error")

    def clear_selection_after_operation(self):
        """✅ ✅ ✅ إصلاح مشكلة التحديد المخفي بعد العمليات"""
        try:
            # إلغاء تحديد أي صف في الجدول
            self.invoices_table.clearSelection()
            self.invoices_table.setCurrentItem(None)
            
            # إلغاء أي تحديد مخفي
            if hasattr(self, 'last_selected_row'):
                delattr(self, 'last_selected_row')
                
        except Exception as e:
            print(f"⚠️ خطأ في إلغاء التحديد: {e}")

    def delete_invoice_from_invoices_page(self, invoice_data):
        """✅ ✅ ✅ حذف الفاتورة من صفحة الفواتير"""
        try:
            invoices_file = "data/invoices.json"
            if not os.path.exists(invoices_file):
                return
            
            with open(invoices_file, 'r', encoding='utf-8') as f:
                invoices = json.load(f)
            
            # ✅ البحث عن الفاتورة وحذفها باستخدام UUID
            updated_invoices = []
            for invoice in invoices:
                if invoice.get('invoice_uuid') != invoice_data.get('invoice_uuid'):
                    updated_invoices.append(invoice)
            
            with open(invoices_file, 'w', encoding='utf-8') as f:
                json.dump(updated_invoices, f, ensure_ascii=False, indent=2)
                
            print(f"✅ تم حذف الفاتورة {invoice_data['invoice_number']} من صفحة الفواتير")
                
        except Exception as e:
            print(f"❌ خطأ في حذف الفاتورة من صفحة الفواتير: {e}")

    def delete_invoice_payments_from_payments_page(self, invoice_data):
        """✅ ✅ ✅ حذف جميع الدفعات المرتبطة بالفاتورة من صفحة المدفوعات"""
        try:
            payments_file = "data/customer_payments.json"
            if not os.path.exists(payments_file):
                return
            
            with open(payments_file, 'r', encoding='utf-8') as f:
                payments = json.load(f)
            
            # ✅ البحث عن جميع الدفعات المرتبطة بالفاتورة وحذفها باستخدام UUID
            updated_payments = []
            for payment in payments:
                if payment.get('invoice_uuid') != invoice_data.get('invoice_uuid'):
                    updated_payments.append(payment)
                else:
                    print(f"🗑️ حذف دفعة مرتبطة بالفاتورة: {payment.get('amount')} $")
            
            with open(payments_file, 'w', encoding='utf-8') as f:
                json.dump(updated_payments, f, ensure_ascii=False, indent=2)
                
            print(f"✅ تم حذف جميع الدفعات المرتبطة بالفاتورة {invoice_data['invoice_number']} من صفحة المدفوعات")
                
        except Exception as e:
            print(f"❌ خطأ في حذف دفعات الفاتورة من صفحة المدفوعات: {e}")

    def update_customer_stats_after_deletion(self, customer, deleted_invoice):
        """✅ تحديث إحصائيات الزبون بعد حذف الفاتورة"""
        try:
            invoice_total = deleted_invoice.get('total_usd', 0)
            invoice_paid = deleted_invoice.get('paid_amount', 0)
            invoice_type = deleted_invoice.get('type', 'نقدي')
            
            # ✅ تحديث الإجمالي
            customer['total_amount'] = max(0, customer.get('total_amount', 0) - invoice_total)
            customer['total_invoices'] = max(0, customer.get('total_invoices', 0) - 1)
            
            # ✅ تحديث المدفوعات والمتبقي بناءً على نوع الفاتورة
            if invoice_type == 'نقدي':
                customer['total_paid'] = max(0, customer.get('total_paid', 0) - invoice_total)
            else:  # تقسيط
                customer['total_paid'] = max(0, customer.get('total_paid', 0) - invoice_paid)
                customer['total_remaining'] = max(0, customer.get('total_remaining', 0) - (invoice_total - invoice_paid))
                
        except Exception as e:
            print(f"❌ خطأ في تحديث إحصائيات الزبون بعد الحذف: {e}")

    def go_back_to_invoices(self):
        """✅ الرجوع إلى صفحة الفواتير - الحل النهائي"""
        try:
            print("🔄 العودة إلى صفحة الفواتير...")
            
            # ✅ الحل: استخدام الـ controller للعودة إلى صفحة الفواتير
            if hasattr(self, 'controller') and self.controller:
                print("✅ استخدام controller للعودة")
                self.controller.show_invoices_page()
            elif hasattr(self, 'parent') and self.parent:
                print("✅ استخدام parent للعودة")
                self.parent.show_invoices_page()
            else:
                print("⚠️ لم يتم العثور على controller أو parent")
            
            self.close()
            print("✅ تم العودة إلى صفحة الفواتير بنجاح")
            
        except Exception as e:
            print(f"❌ خطأ في العودة: {e}")
            # في حالة الخطأ، نغلق النافذة على أي حال
            self.close()

    def open_payments_page(self):
        """فتح صفحة دفعات الزبون في نافذة مستقلة"""
        try:
            self.payments_page = CustomerPaymentsPage(
                self, 
                self.customer_id, 
                self.customer_name, 
                self.phone_number
            )
            self.payments_page.show()
            print(f"✅ تم فتح صفحة الدفعات للزبون: {self.customer_name}")
        except Exception as e:
            print(f"❌ خطأ في فتح صفحة الدفعات: {e}")
            QMessageBox.critical(self, "خطأ", f"حدث خطأ في فتح صفحة الدفعات: {str(e)}")

    def show_message(self, title, message, type="info", show_buttons=False):
        """✅ ✅ ✅ التعديل: عرض رسائل للمستخدم مع إصلاح مشكلة التحديد المخفي"""
        # ✅ إلغاء التحديد المخفي قبل عرض الرسالة
        self.clear_selection_after_operation()
        
        msg = QMessageBox(self)
        msg.setWindowTitle(title)
        msg.setText(message)
        
        # ✅ تنسيق الرسائل بخلفية كحلية داكنة
        msg.setStyleSheet("""
            QMessageBox {
                background-color: #1e2a3a;
            }
            QMessageBox QLabel {
                color: white;
                font-size: 16px;
                font-weight: bold;
                font-family: Arial;
            }
            QMessageBox QPushButton {
                background-color: #3498db;
                color: white;
                padding: 10px 20px;
                border: none;
                border-radius: 5px;
                font-size: 16px;
                font-weight: bold;
                font-family: Arial;
                min-width: 100px;
            }
            QMessageBox QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        
        if type == "warning":
            msg.setIcon(QMessageBox.Warning)
        elif type == "error":
            msg.setIcon(QMessageBox.Critical)
        elif type == "question":
            msg.setIcon(QMessageBox.Question)
            msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
            msg.setDefaultButton(QMessageBox.No)
            # ✅ ✅ ✅ حفظ المرجع للرسالة لتأكيد الحذف
            self.delete_message_box = msg
        else:
            msg.setIcon(QMessageBox.Information)
            
        if show_buttons and type == "question":
            return msg.exec()
        else:
            msg.exec()
            return None

    def cleanup_deleted_customer_payments(self):
        """✅ تنظيف الدفعات الخاصة بالزبائن المحذوفين"""
        try:
            payments_file = "data/customer_payments.json"
            customers_file = "data/customers.json"
            
            if not os.path.exists(payments_file):
                return
            
            with open(payments_file, 'r', encoding='utf-8') as f:
                payments = json.load(f)
            
            with open(customers_file, 'r', encoding='utf-8') as f:
                customers = json.load(f)
            
            # ✅ جمع أرقام هواتف الزبائن الموجودين
            existing_phones = set()
            for customer in customers:
                phone = customer.get('phone')
                if phone:
                    existing_phones.add(phone)
            
            # ✅ تصفية الدفعات - إبقاء فقط دفعات الزبائن الموجودين
            filtered_payments = []
            for payment in payments:
                if payment.get('customer_phone') in existing_phones:
                    filtered_payments.append(payment)
                else:
                    print(f"🗑️ حذف دفعة لزبون محذوف: {payment.get('customer_name')}")
            
            # ✅ حفظ الملف المصفى
            with open(payments_file, 'w', encoding='utf-8') as f:
                json.dump(filtered_payments, f, ensure_ascii=False, indent=2)
            
            print(f"✅ تم تنظيف دفعات الزبائن المحذوفين - بقي {len(filtered_payments)} دفعة")
            
        except Exception as e:
            print(f"❌ خطأ في تنظيف الدفعات: {e}")

    def closeEvent(self, event):
        """✅ إغلاق النافذة والرجوع إلى صفحة الفواتير"""
        try:
            # ✅ إيقاف المؤقت قبل الإغلاق
            if hasattr(self, 'refresh_timer'):
                self.refresh_timer.stop()
                
            self.hide()
            event.accept()
        except Exception as e:
            print(f"❌ خطأ في إغلاق النافذة: {e}")
            event.accept()