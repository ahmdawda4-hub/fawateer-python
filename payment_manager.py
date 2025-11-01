import os
import sqlite3
from datetime import datetime, date, timedelta
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                              QPushButton, QTableWidget, QTableWidgetItem,
                              QLineEdit, QGroupBox, QHeaderView, QMessageBox,
                              QDialog, QFormLayout, QTextEdit, QCheckBox, QDateEdit,
                              QInputDialog)
from PySide6.QtCore import Qt, QSize, QDate
from PySide6.QtGui import QPainter, QPixmap, QIcon, QKeyEvent, QColor

class PaymentManager(QWidget):
    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        self.selected_payment_ids = []  # ✅ تغيير من selected_payment_id إلى قائمة
        self.setup_database()
        self.load_exchange_rate()
        self.init_ui()
        self.load_payments_data()
        self.check_reminders()
        print("✅ تم تحميل صفحة الدفعات بنجاح")

    def setup_database(self):
        """إنشاء قاعدة البيانات والجداول"""
        self.conn = sqlite3.connect('payments_database.db', check_same_thread=False)
        self.cursor = self.conn.cursor()
        
        # جدول سعر الصرف
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS exchange_rates (
                id INTEGER PRIMARY KEY,
                usd_to_lbp_rate REAL,
                last_updated DATE
            )
        ''')
        
        # جدول الدفعات الخاصة - محدث مع جميع الأعمدة
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS special_payments (
                id INTEGER PRIMARY KEY,
                title TEXT,
                reason TEXT,
                total_amount REAL,
                total_currency TEXT,
                paid_amount REAL,
                paid_currency TEXT,
                remaining_amount REAL,
                installments_count INTEGER,
                installment_value REAL,
                details TEXT,
                created_date DATE,
                due_date DATE,
                has_reminder BOOLEAN,
                is_completed BOOLEAN DEFAULT FALSE,
                exchange_rate_used REAL DEFAULT 0
            )
        ''')
        
        # جدول دفعات الفواتير
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS payment_installments (
                id INTEGER PRIMARY KEY,
                payment_id INTEGER,
                installment_number INTEGER,
                amount REAL,
                currency TEXT,
                due_date DATE,
                is_paid BOOLEAN DEFAULT FALSE,
                FOREIGN KEY (payment_id) REFERENCES special_payments (id)
            )
        ''')
        
        # التحقق من وجود جميع الأعمدة وإضافتها إذا كانت مفقودة
        self.cursor.execute("PRAGMA table_info(special_payments)")
        existing_columns = [column[1] for column in self.cursor.fetchall()]
        
        required_columns = [
            'title', 'reason', 'total_amount', 'total_currency', 'paid_amount',
            'paid_currency', 'remaining_amount', 'installments_count', 
            'installment_value', 'details', 'created_date', 'due_date', 
            'has_reminder', 'is_completed', 'exchange_rate_used'
        ]
        
        for column in required_columns:
            if column not in existing_columns:
                if column == 'details':
                    self.cursor.execute(f"ALTER TABLE special_payments ADD COLUMN {column} TEXT")
                elif column in ['has_reminder', 'is_completed']:
                    self.cursor.execute(f"ALTER TABLE special_payments ADD COLUMN {column} BOOLEAN DEFAULT FALSE")
                elif column in ['installments_count']:
                    self.cursor.execute(f"ALTER TABLE special_payments ADD COLUMN {column} INTEGER DEFAULT 0")
                elif column in ['total_amount', 'paid_amount', 'remaining_amount', 'installment_value', 'exchange_rate_used']:
                    self.cursor.execute(f"ALTER TABLE special_payments ADD COLUMN {column} REAL DEFAULT 0")
                else:
                    self.cursor.execute(f"ALTER TABLE special_payments ADD COLUMN {column} TEXT")
                print(f"✅ تم إضافة العمود {column} إلى الجدول")
        
        # إدخال سعر صرف افتراضي إذا لم يكن موجوداً
        self.cursor.execute("SELECT COUNT(*) FROM exchange_rates")
        if self.cursor.fetchone()[0] == 0:
            self.cursor.execute('''
                INSERT INTO exchange_rates (usd_to_lbp_rate, last_updated)
                VALUES (?, ?)
            ''', (89500, datetime.now().strftime("%Y-%m-%d")))
        
        self.conn.commit()

    def load_exchange_rate(self):
        """تحميل سعر الصرف الحالي"""
        self.cursor.execute("SELECT usd_to_lbp_rate FROM exchange_rates ORDER BY last_updated DESC LIMIT 1")
        result = self.cursor.fetchone()
        self.exchange_rate = result[0] if result else 89500

    def init_ui(self):
        """تهيئة واجهة المستخدم"""
        layout = QVBoxLayout()
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)
        
        # شريط العنوان العلوي
        header_layout = QHBoxLayout()
        
        # زر الرجوع (يسار)
        back_btn = QPushButton()
        back_icon_path = "C:/Users/User/Desktop/chbib1/icons/back.png"
        if os.path.exists(back_icon_path):
            back_btn.setIcon(QIcon(back_icon_path))
            back_btn.setIconSize(QSize(32, 32))
        else:
            back_btn.setText("←")
        back_btn.setIconSize(QSize(120 , 100))
        back_btn.setFixedSize(40, 38)
        back_btn.setStyleSheet("""
            QPushButton {
                background: #3498db;
                color: white;
                border: none;
                border-radius: 5px;
                font-size: 18px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #2980b9;
            }
        """)
        back_btn.clicked.connect(self.controller.show_main_page)
        header_layout.addWidget(back_btn)
        
        # عنوان الصفحة (وسط)
        title = QLabel("💳 نظام إدارة الدفعات والديون")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: white;")
        title.setAlignment(Qt.AlignCenter)
        header_layout.addWidget(title)
        
        # شعار المؤسسة (يمين)
        self.logo_label = QLabel()
        logo_path = "C:/Users/User/Desktop/chbib1/icons/logo.png"
        self.update_logo(logo_path)
        self.logo_label.setFixedSize(235, 130)
        header_layout.addWidget(self.logo_label)
        
        layout.addLayout(header_layout)

        # شريط الأدوات
        toolbar_layout = QHBoxLayout()
        
        # حقل البحث مع أيقونة
        search_layout = QHBoxLayout()
        search_layout.setSpacing(5)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("ابحث في الدفعات...")
        self.search_input.setStyleSheet("""
            QLineEdit {
                font-size: 16px; 
                padding: 10px 12px 10px 35px;
                border: 2px solid #34495e;
                border-radius: 5px;
                background: white;
                color: black;
                min-width: 300px;
                font-weight: bold;
            }
        """)
        self.search_input.textChanged.connect(self.search_payments)
        search_layout.addWidget(self.search_input)
        
        # إضافة أيقونة البحث داخل الحقل
        search_icon = QLabel("🔍")
        search_icon.setStyleSheet("color: #7f8c8d; font-size: 16px; margin-left: 10px;")
        search_icon.setFixedSize(20, 20)
        search_layout.addWidget(search_icon)
        
        toolbar_layout.addLayout(search_layout)
        
        # زر إضافة دفعة
        add_btn = QPushButton("🆕 إضافة دفعة")
        add_btn.setStyleSheet("""
            QPushButton {
                background: #27ae60;
                color: white;
                font-size: 16px;
                padding: 12px 18px;
                border: none;
                border-radius: 5px;
                font-weight: bold;
                margin-left: 10px;
            }
            QPushButton:hover {
                background: #219a52;
            }
        """)
        add_btn.clicked.connect(self.open_add_payment_window)
        toolbar_layout.addWidget(add_btn)
        
        # زر تحديث سعر الصرف
        exchange_btn = QPushButton("💰 تحديث سعر الصرف")
        exchange_btn.setStyleSheet("""
            QPushButton {
                background: #f39c12;
                color: white;
                font-size: 16px;
                padding: 12px 18px;
                border: none;
                border-radius: 5px;
                font-weight: bold;
                margin-left: 10px;
            }
            QPushButton:hover {
                background: #e67e22;
            }
        """)
        exchange_btn.clicked.connect(self.open_exchange_rate_window)
        toolbar_layout.addWidget(exchange_btn)
        
        # زر تعديل
        self.edit_btn = QPushButton("✏️ تعديل")
        self.edit_btn.setStyleSheet("""
            QPushButton {
                background: #3498db;
                color: white;
                font-size: 16px;
                padding: 12px 18px;
                border: none;
                border-radius: 5px;
                font-weight: bold;
                margin-left: 10px;
            }
            QPushButton:hover {
                background: #2980b9;
            }
            QPushButton:disabled {
                background: #95a5a6;
            }
        """)
        self.edit_btn.clicked.connect(self.edit_selected_payment)
        self.edit_btn.setEnabled(False)
        toolbar_layout.addWidget(self.edit_btn)
        
        # زر حذف
        self.delete_btn = QPushButton("🗑️ حذف")
        self.delete_btn.setStyleSheet("""
            QPushButton {
                background: #e74c3c;
                color: white;
                font-size: 16px;
                padding: 12px 18px;
                border: none;
                border-radius: 5px;
                font-weight: bold;
                margin-left: 10px;
            }
            QPushButton:hover {
                background: #c0392b;
            }
            QPushButton:disabled {
                background: #95a5a6;
            }
        """)
        self.delete_btn.clicked.connect(self.delete_selected_payments)  # ✅ تغيير إلى الجمع
        self.delete_btn.setEnabled(False)
        toolbar_layout.addWidget(self.delete_btn)
        
        toolbar_layout.addStretch()
        layout.addLayout(toolbar_layout)
        
        # جدول الدفعات
        self.create_payments_table(layout)
        
        # إحصائيات إجمالي الدفعات
        self.create_total_payments_section(layout)
        
        self.setLayout(layout)

    def update_logo(self, logo_path):
        """تحديث شعار المؤسسة"""
        if os.path.exists(logo_path):
            pixmap = QPixmap(logo_path)
            scaled_pixmap = pixmap.scaled(250, 300, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.logo_label.setPixmap(scaled_pixmap)
        else:
            self.logo_label.setText("🏢")
            self.logo_label.setStyleSheet("font-size: 24px; color: white;")

    def create_payments_table(self, layout):
        """إنشاء جدول الدفعات"""
        payments_group = QGroupBox("📋 الدفعات المسجلة")
        payments_group.setStyleSheet("""
            QGroupBox {
                font-size: 18px;
                font-weight: bold;
                color: white;
                border: none;  /* ✅ حذف الخط الكحلي */
                border-radius: 8px;
                padding-top: 10px;
                margin-top: 10px;
            }
            QGroupBox::title {
                color: #3498db;
                subcontrol-origin: margin;
                padding: 0 10px;
            }
        """)
        payments_layout = QVBoxLayout()
        
        # إنشاء الجدول
        self.payments_table = QTableWidget()
        self.payments_table.setColumnCount(8)
        self.payments_table.setHorizontalHeaderLabels([
            "التاريخ", "العنوان", "السبب", "المبلغ الإجمالي", 
            "المدفوع", "المتبقي", "الحالة", "التذكير"
        ])
        
        # تحسين مظهر الجدول
        self.payments_table.setStyleSheet("""
            QTableWidget {
                background: white;
                font-size: 14px;
                font-weight: bold;
                border: 2px solid #bdc3c7;
                border-radius: 5px;
                gridline-color: #ecf0f1;
                alternate-background-color: #f8f9fa;
                outline: none;
                selection-background-color: #3498db;
                selection-color: white;
            }
            QTableWidget::item {
                padding: 12px;
                border-bottom: 2px solid #ecf0f1;
                border-right: 1px solid #ecf0f1;
            }
            QTableWidget::item:selected {
                background: #3498db;
                color: white;
                border: none;
                outline: none;
            }
            QHeaderView::section {
                background: #2c3e50;
                color: white;
                font-weight: bold;
                padding: 15px;
                border: none;
                font-size: 14px;
                border-right: 1px solid #34495e;
            }
            QTableWidget::item:focus {
                border: none;
                outline: none;
            }
        """)
        
        # تفعيل التناوب في الألوان
        self.payments_table.setAlternatingRowColors(True)
        
        # ✅ التعديل: منع فقدان التحديد عند النقر على الخلفية
        self.payments_table.setFocusPolicy(Qt.StrongFocus)
        self.payments_table.setEditTriggers(QTableWidget.NoEditTriggers)
        
        # تحجيم الأعمدة - تم التعديل لجعل الخانات متناسقة مع حجم الجدول
        header = self.payments_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # التاريخ
        header.setSectionResizeMode(1, QHeaderView.Stretch)  # العنوان
        header.setSectionResizeMode(2, QHeaderView.Stretch)  # السبب - تم تغييره لـ Stretch
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # المبلغ الإجمالي
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)  # المدفوع
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)  # المتبقي
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)  # الحالة
        header.setSectionResizeMode(7, QHeaderView.ResizeToContents)  # التذكير
        
        # تعيين ارتفاع الصفوف
        self.payments_table.verticalHeader().setDefaultSectionSize(50)
        self.payments_table.verticalHeader().setVisible(False)  # إخفاء الأرقام الجانبية
        
        # ✅ التعديل: تفعيل اختيار متعدد للصفوف مع Ctrl فقط
        self.payments_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.payments_table.setSelectionMode(QTableWidget.ExtendedSelection)  # ✅ تغيير إلى ExtendedSelection
        
        self.payments_table.itemSelectionChanged.connect(self.on_payment_selected)
        self.payments_table.doubleClicked.connect(self.on_payment_double_click)
        
        payments_layout.addWidget(self.payments_table)
        payments_group.setLayout(payments_layout)
        layout.addWidget(payments_group)

    def create_total_payments_section(self, layout):
        """إنشاء قسم إجمالي الدفعات"""
        # ✅ التعديل: حذف الخلفية الكبيرة واستخدام تخطيط بسيط
        self.total_container = QWidget()
        self.total_container.setStyleSheet("background: transparent;")  # ✅ خلفية شفافة
        
        self.total_layout = QVBoxLayout(self.total_container)
        self.total_layout.setSpacing(8)
        self.total_layout.setContentsMargins(0, 0, 0, 0)  # ✅ إزالة الهوامش
        
        # عنوان القسم مع زر العين - ✅ تعديل الخلفية
        title_layout = QHBoxLayout()
        title_label = QLabel("📊 إجمالي الدفعات")
        title_label.setStyleSheet("""
            font-size: 18px; 
            font-weight: bold; 
            color: #e3f2fd;
            background: qlineargradient(x1: 0, y1: 0, x2: 1, y1: 0,
                stop: 0 #3949ab, stop: 1 #5c6bc0);
            padding: 12px 20px;
            border-radius: 8px;
            border: 1px solid #7986cb;
            min-width: 200px;
        """)
        
        # ✅ التعديل: زر العين مباشرة بجانب العنوان بدون خطوط
        self.toggle_btn = QPushButton("👁️")
        self.toggle_btn.setCheckable(True)
        self.toggle_btn.setChecked(True)
        self.toggle_btn.setFixedSize(50, 45)
        self.toggle_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #42a5f5;
                border: none;  /* ✅ إزالة الخطوط */
                border-radius: 8px;
                font-size: 18px;
                font-weight: bold;
            }
            QPushButton:checked {
                background: rgba(66, 165, 245, 0.2);
                color: #1976d2;
                border: none;  /* ✅ إزالة الخطوط */
            }
            QPushButton:hover {
                background: rgba(66, 165, 245, 0.3);
                border: none;  /* ✅ إزالة الخطوط */
            }
        """)
        self.toggle_btn.toggled.connect(self.toggle_total_section)
        
        title_layout.addWidget(title_label)
        title_layout.addWidget(self.toggle_btn)  # ✅ نقل زر العين مباشرة بجانب العنوان
        title_layout.addStretch()
        self.total_layout.addLayout(title_layout)
        
        # ✅ التعديل: محتوى الإحصائيات في ويدجت منفصلة
        self.stats_content = QWidget()
        self.stats_content.setStyleSheet("background: transparent;")
        stats_layout = QVBoxLayout(self.stats_content)
        stats_layout.setSpacing(8)
        stats_layout.setContentsMargins(0, 0, 0, 0)
        
        # إحصائيات الدفعات المستحقة (باللون الأحمر)
        self.due_layout = QHBoxLayout()
        due_label = QLabel("🔴 الدفعات المستحقة:")
        due_label.setStyleSheet("""
            font-size: 15px; 
            color: #ffebee; 
            font-weight: bold;
            background: qlineargradient(x1: 0, y1: 0, x2: 1, y1: 0,
                stop: 0 #c62828, stop: 1 #d32f2f);
            padding: 10px 15px;
            border-radius: 6px;
            border: 1px solid #f44336;
            min-width: 150px;
        """)
        
        self.due_usd_value = QLabel("0 $")
        self.due_usd_value.setStyleSheet("""
            font-size: 15px; 
            color: #ffebee; 
            font-weight: bold; 
            background: qlineargradient(x1: 0, y1: 0, x2: 1, y1: 0,
                stop: 0 #b71c1c, stop: 1 #c62828);
            padding: 10px 15px; 
            border-radius: 6px;
            border: 1px solid #ef5350;
            min-width: 120px;
        """)
        
        self.due_lbp_value = QLabel("0 LBP")
        self.due_lbp_value.setStyleSheet("""
            font-size: 15px; 
            color: #ffebee; 
            font-weight: bold; 
            background: qlineargradient(x1: 0, y1: 0, x2: 1, y1: 0,
                stop: 0 #b71c1c, stop: 1 #c62828);
            padding: 10px 15px; 
            border-radius: 6px;
            border: 1px solid #ef5350;
            min-width: 120px;
        """)
        
        self.due_layout.addWidget(due_label)
        self.due_layout.addWidget(self.due_usd_value)
        self.due_layout.addWidget(self.due_lbp_value)
        self.due_layout.addStretch()
        stats_layout.addLayout(self.due_layout)
        
        # إحصائيات القيمة المدفوعة (باللون الأخضر)
        self.paid_layout = QHBoxLayout()
        paid_label = QLabel("🟢 القيمة المدفوعة:")
        paid_label.setStyleSheet("""
            font-size: 15px; 
            color: #e8f5e8; 
            font-weight: bold;
            background: qlineargradient(x1: 0, y1: 0, x2: 1, y1: 0,
                stop: 0 #2e7d32, stop: 1 #388e3c);
            padding: 10px 15px;
            border-radius: 6px;
            border: 1px solid #4caf50;
            min-width: 150px;
        """)
        
        self.paid_usd_value = QLabel("0 $")
        self.paid_usd_value.setStyleSheet("""
            font-size: 15px; 
            color: #e8f5e8; 
            font-weight: bold; 
            background: qlineargradient(x1: 0, y1: 0, x2: 1, y1: 0,
                stop: 0 #1b5e20, stop: 1 #2e7d32);
            padding: 10px 15px; 
            border-radius: 6px;
            border: 1px solid #66bb6a;
            min-width: 120px;
        """)
        
        self.paid_lbp_value = QLabel("0 LBP")
        self.paid_lbp_value.setStyleSheet("""
            font-size: 15px; 
            color: #e8f5e8; 
            font-weight: bold; 
            background: qlineargradient(x1: 0, y1: 0, x2: 1, y1: 0,
                stop: 0 #1b5e20, stop: 1 #2e7d32);
            padding: 10px 15px; 
            border-radius: 6px;
            border: 1px solid #66bb6a;
            min-width: 120px;
        """)
        
        self.paid_layout.addWidget(paid_label)
        self.paid_layout.addWidget(self.paid_usd_value)
        self.paid_layout.addWidget(self.paid_lbp_value)
        self.paid_layout.addStretch()
        stats_layout.addLayout(self.paid_layout)
        
        self.total_layout.addWidget(self.stats_content)
        layout.addWidget(self.total_container)

    def toggle_total_section(self, visible):
        """إظهار/إخفاء قسم الإجمالي بالكامل"""
        if visible:
            self.toggle_btn.setText("👁️")
            self.stats_content.show()  # ✅ إظهار المحتوى فقط
        else:
            self.toggle_btn.setText("👁️")
            self.stats_content.hide()  # ✅ إخفاء المحتوى فقط

    def load_payments_data(self):
        """تحميل بيانات الدفعات من قاعدة البيانات"""
        try:
            # استعلام البيانات
            self.cursor.execute('''
                SELECT id, title, reason, total_amount, total_currency, 
                       paid_amount, paid_currency, remaining_amount, 
                       installments_count, created_date, due_date, has_reminder
                FROM special_payments 
                ORDER BY created_date DESC
            ''')
            payments = self.cursor.fetchall()
            
            self.payments_table.setRowCount(len(payments))
            
            total_due_usd = 0
            total_due_lbp = 0
            total_paid_usd = 0
            total_paid_lbp = 0
            
            for row, payment in enumerate(payments):
                (payment_id, title, reason, total_amount, total_currency, 
                 paid_amount, paid_currency, remaining_amount, 
                 installments_count, created_date, due_date, has_reminder) = payment
                
                # تنسيق التاريخ
                date_obj = datetime.strptime(created_date, "%Y-%m-%d")
                formatted_date = date_obj.strftime("%d/%m/%Y")
                
                # تحديد الحالة
                if remaining_amount == 0:
                    status = "🟢 مدفوعة"
                    status_color = QColor("#27ae60")
                    # إضافة للمدفوعات
                    if total_currency == "USD":
                        total_paid_usd += total_amount
                    else:
                        total_paid_lbp += total_amount
                elif paid_amount == 0:
                    status = "🔴 غير مدفوعة"
                    status_color = QColor("#e74c3c")
                    # إضافة للمستحقات
                    if total_currency == "USD":
                        total_due_usd += total_amount
                    else:
                        total_due_lbp += total_amount
                else:
                    status = "🟡 جزئية"
                    status_color = QColor("#f39c12")
                    # إضافة الباقي للمستحقات والمدفوع للمدفوعات
                    if total_currency == "USD":
                        total_due_usd += remaining_amount
                        total_paid_usd += paid_amount
                    else:
                        total_due_lbp += remaining_amount
                        total_paid_lbp += paid_amount
                
                # حالة التذكير
                reminder_status = "🔔" if has_reminder else "🔕"
                if has_reminder and due_date:
                    due_date_obj = datetime.strptime(due_date, "%Y-%m-%d").date()
                    if due_date_obj < date.today():
                        reminder_status = "⚠️ متأخرة"
                
                # إضافة البيانات للجدول
                self.payments_table.setItem(row, 0, QTableWidgetItem(formatted_date))
                self.payments_table.setItem(row, 1, QTableWidgetItem(title))
                self.payments_table.setItem(row, 2, QTableWidgetItem(reason))
                
                # ✅ تحسين: عرض الأرقام بدقة بدون كسور عشرية غير ضرورية
                amount_text = self.format_amount(total_amount, total_currency)
                self.payments_table.setItem(row, 3, QTableWidgetItem(amount_text))
                
                paid_text = self.format_amount(paid_amount, paid_currency)
                self.payments_table.setItem(row, 4, QTableWidgetItem(paid_text))
                
                remaining_text = self.format_amount(remaining_amount, total_currency)
                self.payments_table.setItem(row, 5, QTableWidgetItem(remaining_text))
                
                status_item = QTableWidgetItem(status)
                status_item.setForeground(status_color)
                self.payments_table.setItem(row, 6, status_item)
                self.payments_table.setItem(row, 7, QTableWidgetItem(reminder_status))
                
                # تخزين ID الدفعة في الصف
                self.payments_table.item(row, 0).setData(Qt.UserRole, payment_id)
            
            # ✅ التعديل: تحديث الإحصائيات تلقائياً مع الحساب الصحيح للعملات
            self.update_total_statistics()
            
        except Exception as e:
            print(f"خطأ في تحميل البيانات: {e}")

    def format_amount(self, amount, currency):
        """✅ تنسيق المبلغ بدقة بدون كسور عشرية غير ضرورية"""
        try:
            if amount == 0:
                return f"0 {currency}"
            
            # إذا كان الرقم صحيحاً، عرضه بدون كسور عشرية
            if amount == int(amount):
                return f"{int(amount):,} {currency}"
            else:
                # إذا كان به كسور عشرية، عرضه مع منزلتين عشريتين فقط إذا لزم الأمر
                formatted = f"{amount:,.2f}"
                # إزالة الأصفار غير الضرورية بعد الفاصلة
                if formatted.endswith('.00'):
                    return f"{int(amount):,} {currency}"
                else:
                    # إزالة الأصفار الزائدة بعد الفاصلة
                    formatted = formatted.rstrip('0').rstrip('.') if '.' in formatted else formatted
                    return f"{formatted} {currency}"
        except:
            return f"0 {currency}"

    def on_payment_selected(self):
        """عند اختيار دفعة من الجدول"""
        selected_items = self.payments_table.selectedItems()
        if selected_items:
            # ✅ التعديل: جمع جميع IDs المحددة
            selected_rows = set()
            for item in selected_items:
                selected_rows.add(item.row())
            
            self.selected_payment_ids = []
            for row in selected_rows:
                payment_id = self.payments_table.item(row, 0).data(Qt.UserRole)
                if payment_id:
                    self.selected_payment_ids.append(payment_id)
            
            # ✅ التعديل: تفعيل الأزرار إذا كان هناك تحديد
            has_selection = len(self.selected_payment_ids) > 0
            self.edit_btn.setEnabled(has_selection and len(self.selected_payment_ids) == 1)  # التعديل لدفعة واحدة فقط
            self.delete_btn.setEnabled(has_selection)
            
            # ✅ إظهار عدد الدفعات المحددة
            if len(self.selected_payment_ids) > 1:
                self.delete_btn.setText(f"🗑️ حذف ({len(self.selected_payment_ids)})")
            else:
                self.delete_btn.setText("🗑️ حذف")
                
        else:
            self.selected_payment_ids = []
            self.edit_btn.setEnabled(False)
            self.delete_btn.setEnabled(False)
            self.delete_btn.setText("🗑️ حذف")

    def on_payment_double_click(self, index):
        """عند النقر المزدوج على دفعة"""
        row = index.row()
        payment_id = self.payments_table.item(row, 0).data(Qt.UserRole)
        if payment_id:
            self.open_edit_payment_window(payment_id)

    def keyPressEvent(self, event: QKeyEvent):
        """معالجة ضغطات المفاتيح"""
        if event.key() == Qt.Key_Delete and self.selected_payment_ids:
            self.delete_selected_payments()  # ✅ تغيير إلى الجمع
        elif event.key() == Qt.Key_Return and self.selected_payment_ids and len(self.selected_payment_ids) == 1:
            self.edit_selected_payment()
        else:
            super().keyPressEvent(event)

    def edit_selected_payment(self):
        """تعديل الدفعة المحددة"""
        if self.selected_payment_ids and len(self.selected_payment_ids) == 1:
            self.open_edit_payment_window(self.selected_payment_ids[0])

    def delete_selected_payments(self):
        """✅ التعديل: حذف الدفعات المحددة (واحدة أو متعددة)"""
        if not self.selected_payment_ids:
            return
            
        if len(self.selected_payment_ids) == 1:
            # حذف دفعة واحدة
            payment_id = self.selected_payment_ids[0]
            self.cursor.execute("SELECT title FROM special_payments WHERE id = ?", (payment_id,))
            payment_title = self.cursor.fetchone()[0]
            
            reply = QMessageBox.question(self, "تأكيد الحذف", 
                                       f"هل أنت متأكد من حذف الدفعة '{payment_title}'؟",
                                       QMessageBox.Yes | QMessageBox.No,
                                       QMessageBox.No)
        else:
            # حذف متعدد
            reply = QMessageBox.question(self, "تأكيد الحذف", 
                                       f"هل أنت متأكد من حذف {len(self.selected_payment_ids)} دفعة؟",
                                       QMessageBox.Yes | QMessageBox.No,
                                       QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            try:
                success_count = 0
                for payment_id in self.selected_payment_ids:
                    # حذف دفعات الفواتير المرتبطة أولاً
                    self.cursor.execute("DELETE FROM payment_installments WHERE payment_id = ?", (payment_id,))
                    # ثم حذف الدفعة الرئيسية
                    self.cursor.execute("DELETE FROM special_payments WHERE id = ?", (payment_id,))
                    success_count += 1
                
                self.conn.commit()
                self.load_payments_data()
                self.selected_payment_ids = []
                self.edit_btn.setEnabled(False)
                self.delete_btn.setEnabled(False)
                self.delete_btn.setText("🗑️ حذف")
                
                if success_count > 1:
                    QMessageBox.information(self, "تم الحذف", f"✅ تم حذف {success_count} دفعة بنجاح")
                else:
                    QMessageBox.information(self, "تم الحذف", "✅ تم حذف الدفعة بنجاح")
                    
            except Exception as e:
                QMessageBox.critical(self, "خطأ", f"❌ حدث خطأ أثناء الحذف: {e}")

    def search_payments(self):
        """بحث في الدفعات"""
        search_text = self.search_input.text().lower()
        
        for row in range(self.payments_table.rowCount()):
            should_show = False
            for col in range(self.payments_table.columnCount()):
                item = self.payments_table.item(row, col)
                if item and search_text in item.text().lower():
                    should_show = True
                    break
            
            self.payments_table.setRowHidden(row, not should_show)

    def open_add_payment_window(self):
        """فتح نافذة إضافة دفعة جديدة"""
        dialog = AddPaymentDialog(self, self.exchange_rate)
        if dialog.exec() == QDialog.Accepted:
            self.load_payments_data()
            # ✅ التعديل: تحديث الإحصائيات تلقائياً بعد حفظ دفعة جديدة
            self.update_total_statistics()

    def open_edit_payment_window(self, payment_id):
        """فتح نافذة تعديل دفعة"""
        dialog = EditPaymentDialog(self, payment_id, self.exchange_rate)
        if dialog.exec() == QDialog.Accepted:
            self.load_payments_data()
            # ✅ التعديل: تحديث الإحصائيات تلقائياً بعد تعديل دفعة
            self.update_total_statistics()

    def open_exchange_rate_window(self):
        """فتح نافذة تحديث سعر الصرف"""
        dialog = ExchangeRateDialog(self, self.exchange_rate)
        if dialog.exec() == QDialog.Accepted:
            self.load_exchange_rate()
            self.load_payments_data()
            # ✅ التعديل: تحديث الإحصائيات تلقائياً بعد تحديث سعر الصرف
            self.update_total_statistics()

    def update_total_statistics(self):
        """✅ التعديل: تحديث إحصائيات إجمالي الدفعات تلقائياً مع الحساب الصحيح للعملات"""
        try:
            total_due_usd = 0
            total_due_lbp = 0
            total_paid_usd = 0
            total_paid_lbp = 0
            
            # جلب جميع الدفعات
            self.cursor.execute('''
                SELECT total_amount, total_currency, paid_amount, paid_currency, remaining_amount
                FROM special_payments
            ''')
            payments = self.cursor.fetchall()
            
            for payment in payments:
                total_amount, total_currency, paid_amount, paid_currency, remaining_amount = payment
                
                # ✅ التعديل: حساب العملات بشكل منفصل بناءً على عملة كل دفعة
                if total_currency == "USD":
                    # إذا كانت العملة USD
                    if remaining_amount == 0:
                        # الدفعة مدفوعة بالكامل
                        total_paid_usd += total_amount
                    elif paid_amount == 0:
                        # الدفعة غير مدفوعة
                        total_due_usd += total_amount
                    else:
                        # الدفعة جزئية
                        total_due_usd += remaining_amount
                        total_paid_usd += paid_amount
                else:
                    # إذا كانت العملة LBP
                    if remaining_amount == 0:
                        # الدفعة مدفوعة بالكامل
                        total_paid_lbp += total_amount
                    elif paid_amount == 0:
                        # الدفعة غير مدفوعة
                        total_due_lbp += total_amount
                    else:
                        # الدفعة جزئية
                        total_due_lbp += remaining_amount
                        total_paid_lbp += paid_amount
            
            # ✅ التحديث: استخدام التنسيق الجديد مع الأرقام العشرية الدقيقة
            self.due_usd_value.setText(self.format_amount_with_decimals(total_due_usd, "USD"))
            self.due_lbp_value.setText(self.format_amount_with_decimals(total_due_lbp, "LBP"))
            self.paid_usd_value.setText(self.format_amount_with_decimals(total_paid_usd, "USD"))
            self.paid_lbp_value.setText(self.format_amount_with_decimals(total_paid_lbp, "LBP"))
            
        except Exception as e:
            print(f"خطأ في تحديث الإحصائيات: {e}")

    def format_amount_with_decimals(self, amount, currency):
        """✅ تنسيق المبلغ مع الأرقام العشرية الدقيقة"""
        try:
            if amount == 0:
                return f"0 {currency}"
            
            # إذا كان الرقم صحيحاً، عرضه بدون كسور عشرية
            if amount == int(amount):
                return f"{int(amount):,} {currency}"
            else:
                # عرض الرقم مع منزلتين عشريتين
                formatted = f"{amount:,.2f}"
                # إزالة الأصفار غير الضرورية بعد الفاصلة
                if formatted.endswith('.00'):
                    return f"{int(amount):,} {currency}"
                else:
                    # الحفاظ على منزلتين عشريتين مع إزالة الأصفار الزائدة فقط
                    formatted = formatted.rstrip('0').rstrip('.') if '.' in formatted else formatted
                    # إذا انتهى الرقم بنقطة، أضف منزلتين عشريتين
                    if formatted.endswith('.'):
                        formatted = f"{formatted}00"
                    # إذا كان به منزلة عشرية واحدة فقط، أضف صفراً
                    elif '.' in formatted and len(formatted.split('.')[1]) == 1:
                        formatted = f"{formatted}0"
                    return f"{formatted} {currency}"
        except:
            return f"0 {currency}"

    def check_reminders(self):
        """التحقق من التذكيرات المستحقة"""
        try:
            today = date.today().strftime("%Y-%m-%d")
            self.cursor.execute('''
                SELECT title, due_date FROM special_payments 
                WHERE has_reminder = TRUE AND due_date = ? AND is_completed = FALSE
            ''', (today,))
            
            reminders = self.cursor.fetchall()
            for title, due_date in reminders:
                QMessageBox.information(self, "تذكير بالدفعة", 
                                      f"🔔 تذكير: دفعة '{title}' مستحقة اليوم!\n\nتاريخ الاستحقاق: {due_date}")
                
        except Exception as e:
            print(f"خطأ في التحقق من التذكيرات: {e}")

    def refresh_logo(self):
        """تحديث الشعار"""
        logo_path = "C:/Users/User/Desktop/chbib1/icons/logo.png"
        self.update_logo(logo_path)

    def paintEvent(self, event):
        """رسم الخلفية"""
        painter = QPainter(self)
        bg = QPixmap("BG.JPG")
        if not bg.isNull():
            painter.drawPixmap(self.rect(), bg)
        super().paintEvent(event)


class AddPaymentDialog(QDialog):
    def __init__(self, parent, exchange_rate):
        super().__init__(parent)
        self.parent = parent
        self.exchange_rate = exchange_rate
        self.setWindowTitle("إضافة دفعة جديدة")
        self.setFixedSize(750, 850)  # ✅ زيادة العرض لتوفير مساحة أكبر للخانات
        self.setStyleSheet("""
            QDialog {
                background: #1e3a5f; 
                color: white;
                font-size: 16px;
                font-weight: bold;
            }
        """)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(12)  # تقليل المسافة بين العناصر
        
        # عنوان النافذة
        title = QLabel("🆕 إضافة دفعة جديدة")
        title.setStyleSheet("font-size: 22px; font-weight: bold; color: white; margin: 10px;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        form_layout = QFormLayout()
        form_layout.setLabelAlignment(Qt.AlignRight)
        form_layout.setSpacing(12)  # تقليل المسافة بين الصفوف
        form_layout.setContentsMargins(15, 15, 15, 15)  # زيادة الهوامش
        
        # ✅ حقل العنوان - تم تكبيره
        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("أدخل عنوان الدفعة")
        self.title_input.setStyleSheet("""
            font-size: 16px; 
            padding: 12px; 
            background: white; 
            color: black; 
            border-radius: 5px; 
            border: 2px solid #bdc3c7; 
            font-weight: bold;
            min-height: 45px;
        """)
        self.title_input.setMinimumHeight(45)  # ✅ زيادة الارتفاع
        form_layout.addRow("🏷️ العنوان:", self.title_input)
        
        # ✅ حقل السبب - تم تكبيره
        self.reason_input = QLineEdit()
        self.reason_input.setPlaceholderText("أدخل سبب الدفعة")
        self.reason_input.setStyleSheet("""
            font-size: 16px; 
            padding: 12px; 
            background: white; 
            color: black; 
            border-radius: 5px; 
            border: 2px solid #bdc3c7; 
            font-weight: bold;
            min-height: 45px;
        """)
        self.reason_input.setMinimumHeight(45)  # ✅ زيادة الارتفاع
        form_layout.addRow("📝 السبب:", self.reason_input)
        
        # المبلغ الإجمالي بالدولار
        total_usd_layout = QHBoxLayout()
        self.total_amount_usd_input = QLineEdit()
        self.total_amount_usd_input.setPlaceholderText("0")
        self.total_amount_usd_input.setStyleSheet("font-size: 14px; padding: 10px; background: white; color: black; border-radius: 5px; border: 2px solid #bdc3c7; font-weight: bold;")
        self.total_amount_usd_input.setMaximumHeight(40)
        self.total_amount_usd_input.textChanged.connect(self.on_total_usd_changed)
        
        total_usd_layout.addWidget(QLabel("المبلغ الإجمالي ($):"))
        total_usd_layout.addWidget(self.total_amount_usd_input)
        total_usd_layout.addStretch()
        form_layout.addRow(total_usd_layout)
        
        # المبلغ الإجمالي بالليرة اللبنانية
        total_lbp_layout = QHBoxLayout()
        self.total_amount_lbp_input = QLineEdit()
        self.total_amount_lbp_input.setPlaceholderText("0")
        self.total_amount_lbp_input.setStyleSheet("font-size: 14px; padding: 10px; background: white; color: black; border-radius: 5px; border: 2px solid #bdc3c7; font-weight: bold;")
        self.total_amount_lbp_input.setMaximumHeight(40)
        self.total_amount_lbp_input.textChanged.connect(self.on_total_lbp_changed)
        
        total_lbp_layout.addWidget(QLabel("المبلغ الإجمالي (LBP):"))
        total_lbp_layout.addWidget(self.total_amount_lbp_input)
        total_lbp_layout.addStretch()
        form_layout.addRow(total_lbp_layout)
        
        # المبلغ المدفوع بالدولار
        paid_usd_layout = QHBoxLayout()
        self.paid_amount_usd_input = QLineEdit()
        self.paid_amount_usd_input.setPlaceholderText("0")
        self.paid_amount_usd_input.setStyleSheet("font-size: 14px; padding: 10px; background: white; color: black; border-radius: 5px; border: 2px solid #bdc3c7; font-weight: bold;")
        self.paid_amount_usd_input.setMaximumHeight(40)
        self.paid_amount_usd_input.textChanged.connect(self.on_paid_usd_changed)
        
        paid_usd_layout.addWidget(QLabel("المبلغ المدفوع ($):"))
        paid_usd_layout.addWidget(self.paid_amount_usd_input)
        paid_usd_layout.addStretch()
        form_layout.addRow(paid_usd_layout)
        
        # المبلغ المدفوع بالليرة اللبنانية
        paid_lbp_layout = QHBoxLayout()
        self.paid_amount_lbp_input = QLineEdit()
        self.paid_amount_lbp_input.setPlaceholderText("0")
        self.paid_amount_lbp_input.setStyleSheet("font-size: 14px; padding: 10px; background: white; color: black; border-radius: 5px; border: 2px solid #bdc3c7; font-weight: bold;")
        self.paid_amount_lbp_input.setMaximumHeight(40)
        self.paid_amount_lbp_input.textChanged.connect(self.on_paid_lbp_changed)
        
        paid_lbp_layout.addWidget(QLabel("المبلغ المدفوع (LBP):"))
        paid_lbp_layout.addWidget(self.paid_amount_lbp_input)
        paid_lbp_layout.addStretch()
        form_layout.addRow(paid_lbp_layout)
        
        # عدد الدفعات
        self.installments_input = QLineEdit()
        self.installments_input.setPlaceholderText("0 (اختياري)")
        self.installments_input.setStyleSheet("font-size: 14px; padding: 10px; background: white; color: black; border-radius: 5px; border: 2px solid #bdc3c7; font-weight: bold;")
        self.installments_input.setMaximumHeight(40)
        self.installments_input.textChanged.connect(self.calculate_installment)
        form_layout.addRow("🔢 عدد الدفعات:", self.installments_input)
        
        # منطقة الحسابات التلقائية - بدون عنوان وشكل مستطيل
        calc_layout = QVBoxLayout()
        calc_layout.setSpacing(8)
        
        # المبلغ المتبقي - تم زيادة الارتفاع والتباعد
        remaining_layout = QHBoxLayout()
        remaining_label = QLabel("المبلغ المتبقي:")
        remaining_label.setStyleSheet("color: #e74c3c; font-weight: bold; font-size: 15px;")
        
        self.remaining_amount_usd_input = QLineEdit()
        self.remaining_amount_usd_input.setPlaceholderText("0 $")
        # تم زيادة الارتفاع والتباعد لضمان ظهور الأرقام كاملة
        self.remaining_amount_usd_input.setStyleSheet("""
            font-size: 15px; 
            padding: 12px 8px; 
            background: transparent; 
            color: #e74c3c; 
            border: none; 
            font-weight: bold;
            border-bottom: 2px solid #e74c3c;
            min-height: 25px;
        """)
        self.remaining_amount_usd_input.setReadOnly(True)
        self.remaining_amount_usd_input.setMinimumHeight(45)  # زيادة الارتفاع
        
        self.remaining_amount_lbp_input = QLineEdit()
        self.remaining_amount_lbp_input.setPlaceholderText("0 LBP")
        self.remaining_amount_lbp_input.setStyleSheet("""
            font-size: 15px; 
            padding: 12px 8px; 
            background: transparent; 
            color: #e74c3c; 
            border: none; 
            font-weight: bold;
            border-bottom: 2px solid #e74c3c;
            min-height: 25px;
        """)
        self.remaining_amount_lbp_input.setReadOnly(True)
        self.remaining_amount_lbp_input.setMinimumHeight(45)  # زيادة الارتفاع
        
        remaining_layout.addWidget(remaining_label)
        remaining_layout.addWidget(self.remaining_amount_usd_input)
        remaining_layout.addWidget(self.remaining_amount_lbp_input)
        calc_layout.addLayout(remaining_layout)
        
        # المبلغ للدفعة الواحدة - تم زيادة الارتفاع والتباعد
        installment_layout = QHBoxLayout()
        installment_label = QLabel("المبلغ للدفعة الواحدة:")
        installment_label.setStyleSheet("color: #f39c12; font-weight: bold; font-size: 15px;")
        
        self.installment_amount_usd_input = QLineEdit()
        self.installment_amount_usd_input.setPlaceholderText("0 $")
        self.installment_amount_usd_input.setStyleSheet("""
            font-size: 15px; 
            padding: 12px 8px; 
            background: transparent; 
            color: #f39c12; 
            border: none; 
            font-weight: bold;
            border-bottom: 2px solid #f39c12;
            min-height: 25px;
        """)
        self.installment_amount_usd_input.setMinimumHeight(45)  # زيادة الارتفاع
        self.installment_amount_usd_input.textChanged.connect(self.on_installment_usd_changed)
        
        self.installment_amount_lbp_input = QLineEdit()
        self.installment_amount_lbp_input.setPlaceholderText("0 LBP")
        self.installment_amount_lbp_input.setStyleSheet("""
            font-size: 15px; 
            padding: 12px 8px; 
            background: transparent; 
            color: #f39c12; 
            border: none; 
            font-weight: bold;
            border-bottom: 2px solid #f39c12;
            min-height: 25px;
        """)
        self.installment_amount_lbp_input.setMinimumHeight(45)  # زيادة الارتفاع
        self.installment_amount_lbp_input.textChanged.connect(self.on_installment_lbp_changed)
        
        installment_layout.addWidget(installment_label)
        installment_layout.addWidget(self.installment_amount_usd_input)
        installment_layout.addWidget(self.installment_amount_lbp_input)
        calc_layout.addLayout(installment_layout)
        
        # إضافة التخطيط مباشرة بدون QGroupBox
        form_layout.addRow(calc_layout)
        
        # خانة التفاصيل - تم تصغيرها
        self.details_input = QTextEdit()
        self.details_input.setPlaceholderText("أدخل تفاصيل إضافية عن الدفعة (اختياري)")
        self.details_input.setMaximumHeight(80)  # تصغير الارتفاع
        self.details_input.setStyleSheet("font-size: 14px; padding: 8px; background: white; color: black; border-radius: 5px; border: 2px solid #bdc3c7; font-weight: bold;")
        form_layout.addRow("📄 التفاصيل:", self.details_input)
        
        # تفعيل التذكير
        reminder_layout = QHBoxLayout()
        self.reminder_check = QCheckBox("تفعيل نظام التذكير")
        self.reminder_check.setStyleSheet("color: white; font-size: 14px; font-weight: bold;")
        self.reminder_check.toggled.connect(self.toggle_reminder_date)
        
        self.due_date_input = QDateEdit()
        self.due_date_input.setDate(QDate.currentDate().addDays(30))
        self.due_date_input.setCalendarPopup(True)
        self.due_date_input.setStyleSheet("font-size: 14px; padding: 8px; background: white; color: black; border-radius: 5px; border: 2px solid #bdc3c7; font-weight: bold;")
        self.due_date_input.setMaximumHeight(40)
        self.due_date_input.setEnabled(False)
        
        reminder_layout.addWidget(self.reminder_check)
        reminder_layout.addWidget(QLabel("تاريخ الاستحقاق:"))
        reminder_layout.addWidget(self.due_date_input)
        reminder_layout.addStretch()
        form_layout.addRow("🔔 التذكير:", reminder_layout)
        
        layout.addLayout(form_layout)
        
        # أزرار الحفظ والإلغاء
        button_layout = QHBoxLayout()
        
        save_btn = QPushButton("💾 حفظ الدفعة")
        save_btn.setStyleSheet("""
            QPushButton {
                background: #27ae60;
                color: white;
                font-size: 16px;
                padding: 12px 25px;
                border: none;
                border-radius: 8px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #219a52;
            }
        """)
        save_btn.clicked.connect(self.save_payment)
        
        cancel_btn = QPushButton("❌ إلغاء")
        cancel_btn.setStyleSheet("""
            QPushButton {
                background: #95a5a6;
                color: white;
                font-size: 16px;
                padding: 12px 25px;
                border: none;
                border-radius: 8px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #7f8c8d;
            }
        """)
        cancel_btn.clicked.connect(self.reject)
        
        button_layout.addWidget(save_btn)
        button_layout.addWidget(cancel_btn)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)

    def format_amount_display(self, amount):
        """✅ تنسيق المبلغ للعرض بدون كسور عشرية غير ضرورية"""
        try:
            if amount == 0:
                return "0"
            
            # إذا كان الرقم صحيحاً، عرضه بدون كسور عشرية
            if amount == int(amount):
                return f"{int(amount):,}"
            else:
                # إذا كان به كسور عشرية، عرضه مع منزلتين عشريتين فقط إذا لزم الأمر
                formatted = f"{amount:,.2f}"
                # إزالة الأصفار غير الضرورية بعد الفاصلة
                if formatted.endswith('.00'):
                    return f"{int(amount):,}"
                else:
                    # إزالة الأصفار الزائدة بعد الفاصلة
                    formatted = formatted.rstrip('0').rstrip('.') if '.' in formatted else formatted
                    return formatted
        except:
            return "0"

    def on_total_usd_changed(self):
        """عند تغيير المبلغ الإجمالي بالدولار"""
        try:
            text = self.total_amount_usd_input.text().strip()
            if text:
                amount = float(text)
                lbp_amount = amount * self.exchange_rate
                # ✅ تحديث الحقل المقابل مع منع التكرار واستخدام التنسيق الجديد
                self.total_amount_lbp_input.blockSignals(True)
                self.total_amount_lbp_input.setText(self.format_amount_display(lbp_amount))
                self.total_amount_lbp_input.blockSignals(False)
            else:
                self.total_amount_lbp_input.blockSignals(True)
                self.total_amount_lbp_input.clear()
                self.total_amount_lbp_input.blockSignals(False)
            
            self.calculate_remaining()
            self.calculate_installment()
        except ValueError:
            pass

    def on_total_lbp_changed(self):
        """عند تغيير المبلغ الإجمالي بالليرة اللبنانية"""
        try:
            text = self.total_amount_lbp_input.text().strip().replace(',', '')
            if text:
                amount = float(text)
                usd_amount = amount / self.exchange_rate
                # ✅ تحديث الحقل المقابل مع منع التكرار واستخدام التنسيق الجديد
                self.total_amount_usd_input.blockSignals(True)
                self.total_amount_usd_input.setText(self.format_amount_display(usd_amount))
                self.total_amount_usd_input.blockSignals(False)
            else:
                self.total_amount_usd_input.blockSignals(True)
                self.total_amount_usd_input.clear()
                self.total_amount_usd_input.blockSignals(False)
            
            self.calculate_remaining()
            self.calculate_installment()
        except ValueError:
            pass

    def on_paid_usd_changed(self):
        """عند تغيير المبلغ المدفوع بالدولار"""
        try:
            text = self.paid_amount_usd_input.text().strip()
            if text:
                amount = float(text)
                lbp_amount = amount * self.exchange_rate
                # ✅ تحديث الحقل المقابل مع منع التكرار واستخدام التنسيق الجديد
                self.paid_amount_lbp_input.blockSignals(True)
                self.paid_amount_lbp_input.setText(self.format_amount_display(lbp_amount))
                self.paid_amount_lbp_input.blockSignals(False)
            else:
                self.paid_amount_lbp_input.blockSignals(True)
                self.paid_amount_lbp_input.clear()
                self.paid_amount_lbp_input.blockSignals(False)
            
            self.calculate_remaining()
            self.calculate_installment()
        except ValueError:
            pass

    def on_paid_lbp_changed(self):
        """عند تغيير المبلغ المدفوع بالليرة اللبنانية"""
        try:
            text = self.paid_amount_lbp_input.text().strip().replace(',', '')
            if text:
                amount = float(text)
                usd_amount = amount / self.exchange_rate
                # ✅ تحديث الحقل المقابل مع منع التكرار واستخدام التنسيق الجديد
                self.paid_amount_usd_input.blockSignals(True)
                self.paid_amount_usd_input.setText(self.format_amount_display(usd_amount))
                self.paid_amount_usd_input.blockSignals(False)
            else:
                self.paid_amount_usd_input.blockSignals(True)
                self.paid_amount_usd_input.clear()
                self.paid_amount_usd_input.blockSignals(False)
            
            self.calculate_remaining()
            self.calculate_installment()
        except ValueError:
            pass

    def on_installment_usd_changed(self):
        """عند تغيير مبلغ الدفعة الواحدة بالدولار"""
        try:
            text = self.installment_amount_usd_input.text().strip()
            if text:
                amount = float(text)
                lbp_amount = amount * self.exchange_rate
                # ✅ تحديث الحقل المقابل مع منع التكرار واستخدام التنسيق الجديد
                self.installment_amount_lbp_input.blockSignals(True)
                self.installment_amount_lbp_input.setText(self.format_amount_display(lbp_amount))
                self.installment_amount_lbp_input.blockSignals(False)
        except ValueError:
            pass

    def on_installment_lbp_changed(self):
        """عند تغيير مبلغ الدفعة الواحدة بالليرة اللبنانية"""
        try:
            text = self.installment_amount_lbp_input.text().strip().replace(',', '')
            if text:
                amount = float(text)
                usd_amount = amount / self.exchange_rate
                # ✅ تحديث الحقل المقابل مع منع التكرار واستخدام التنسيق الجديد
                self.installment_amount_usd_input.blockSignals(True)
                self.installment_amount_usd_input.setText(self.format_amount_display(usd_amount))
                self.installment_amount_usd_input.blockSignals(False)
        except ValueError:
            pass

    def calculate_remaining(self):
        """✅ حساب المبلغ المتبقي بدقة"""
        try:
            total_usd_text = self.total_amount_usd_input.text().strip().replace(',', '')
            paid_usd_text = self.paid_amount_usd_input.text().strip().replace(',', '')
            
            total_amount = float(total_usd_text) if total_usd_text else 0
            paid_amount = float(paid_usd_text) if paid_usd_text else 0
            
            remaining_usd = total_amount - paid_amount
            remaining_lbp = remaining_usd * self.exchange_rate
            
            # ✅ تحديث حقول المبلغ المتبقي باستخدام التنسيق الجديد
            self.remaining_amount_usd_input.setText(f"{self.format_amount_display(remaining_usd)} $")
            self.remaining_amount_lbp_input.setText(f"{self.format_amount_display(remaining_lbp)} LBP")
            
        except ValueError:
            # في حالة الخطأ، ضع القيم الافتراضية
            self.remaining_amount_usd_input.setText("0 $")
            self.remaining_amount_lbp_input.setText("0 LBP")

    def calculate_installment(self):
        """✅ حساب قيمة كل دفعة بدقة"""
        try:
            total_usd_text = self.total_amount_usd_input.text().strip().replace(',', '')
            paid_usd_text = self.paid_amount_usd_input.text().strip().replace(',', '')
            installments_text = self.installments_input.text().strip()
            
            total_amount = float(total_usd_text) if total_usd_text else 0
            paid_amount = float(paid_usd_text) if paid_usd_text else 0
            installments = int(installments_text) if installments_text else 0
            
            remaining_usd = total_amount - paid_amount
            
            if installments > 0 and remaining_usd > 0:
                installment_usd = remaining_usd / installments
                installment_lbp = installment_usd * self.exchange_rate
                
                # ✅ تحديث حقول المبلغ للدفعة الواحدة باستخدام التنسيق الجديد
                self.installment_amount_usd_input.blockSignals(True)
                self.installment_amount_lbp_input.blockSignals(True)
                self.installment_amount_usd_input.setText(self.format_amount_display(installment_usd))
                self.installment_amount_lbp_input.setText(self.format_amount_display(installment_lbp))
                self.installment_amount_usd_input.blockSignals(False)
                self.installment_amount_lbp_input.blockSignals(False)
            else:
                # إذا لم يكن هناك دفعات، امسح الحقول
                self.installment_amount_usd_input.blockSignals(True)
                self.installment_amount_lbp_input.blockSignals(True)
                self.installment_amount_usd_input.clear()
                self.installment_amount_lbp_input.clear()
                self.installment_amount_usd_input.blockSignals(False)
                self.installment_amount_lbp_input.blockSignals(False)
                
        except ValueError:
            # في حالة الخطأ، امسح الحقول
            self.installment_amount_usd_input.blockSignals(True)
            self.installment_amount_lbp_input.blockSignals(True)
            self.installment_amount_usd_input.clear()
            self.installment_amount_lbp_input.clear()
            self.installment_amount_usd_input.blockSignals(False)
            self.installment_amount_lbp_input.blockSignals(False)

    def toggle_reminder_date(self, checked):
        """تفعيل/تعطيل حقل تاريخ الاستحقاق"""
        self.due_date_input.setEnabled(checked)

    def save_payment(self):
        """حفظ الدفعة في قاعدة البيانات"""
        try:
            title = self.title_input.text().strip()
            reason = self.reason_input.text().strip()
            details = self.details_input.toPlainText().strip()
            
            if not title:
                QMessageBox.warning(self, "تحذير", "⚠️ يرجى إدخال عنوان الدفعة")
                return
            
            total_usd_text = self.total_amount_usd_input.text().strip().replace(',', '')
            
            if not total_usd_text:
                QMessageBox.warning(self, "تحذير", "⚠️ يرجى إدخال المبلغ الإجمالي")
                return
            
            total_amount = float(total_usd_text)
            paid_amount = float(self.paid_amount_usd_input.text().strip().replace(',', '')) if self.paid_amount_usd_input.text().strip() else 0
            installments_count = int(self.installments_input.text().strip()) if self.installments_input.text().strip() else 0
            
            # حساب المبلغ المتبقي
            remaining_amount = total_amount - paid_amount
            
            # حساب قيمة الدفعة الواحدة
            installment_value = float(self.installment_amount_usd_input.text().strip().replace(',', '')) if self.installment_amount_usd_input.text().strip() else 0
            
            has_reminder = self.reminder_check.isChecked()
            due_date = self.due_date_input.date().toString("yyyy-MM-dd") if has_reminder else None
            
            # إدخال البيانات في قاعدة البيانات
            today = datetime.now().strftime("%Y-%m-%d")
            self.parent.cursor.execute('''
                INSERT INTO special_payments 
                (title, reason, total_amount, total_currency, paid_amount, paid_currency,
                 remaining_amount, installments_count, installment_value, details, 
                 created_date, due_date, has_reminder, exchange_rate_used)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (title, reason, total_amount, "USD", paid_amount, "USD",
                  remaining_amount, installments_count, installment_value, details, 
                  today, due_date, has_reminder, self.exchange_rate))
            
            payment_id = self.parent.cursor.lastrowid
            
            # إنشاء دفعات الفواتير إذا كان هناك أقساط
            if installments_count > 0 and remaining_amount > 0:
                self.create_payment_installments(payment_id, installments_count, installment_value, "USD", due_date)
            
            self.parent.conn.commit()
            QMessageBox.information(self, "نجاح", "✅ تم حفظ الدفعة بنجاح")
            self.accept()
            
        except ValueError as e:
            QMessageBox.warning(self, "تحذير", f"⚠️ يرجى إدخال أرقام صحيحة في الحقول الرقمية: {str(e)}")
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"❌ حدث خطأ أثناء الحفظ: {str(e)}")

    def create_payment_installments(self, payment_id, installments_count, installment_value, currency, due_date):
        """إنشاء دفعات الفواتير"""
        try:
            base_date = datetime.strptime(due_date, "%Y-%m-%d") if due_date else datetime.now()
            
            for i in range(installments_count):
                installment_date = (base_date + timedelta(days=30 * i)).strftime("%Y-%m-%d")
                self.parent.cursor.execute('''
                    INSERT INTO payment_installments 
                    (payment_id, installment_number, amount, currency, due_date)
                    VALUES (?, ?, ?, ?, ?)
                ''', (payment_id, i + 1, installment_value, currency, installment_date))
        except Exception as e:
            print(f"خطأ في إنشاء دفعات الفواتير: {e}")


class EditPaymentDialog(AddPaymentDialog):
    def __init__(self, parent, payment_id, exchange_rate):
        self.payment_id = payment_id
        self.original_exchange_rate = None
        super().__init__(parent, exchange_rate)
        self.setWindowTitle("✏️ تعديل الدفعة")
        self.load_payment_data()

    def load_payment_data(self):
        """تحميل بيانات الدفعة للتعديل"""
        try:
            self.parent.cursor.execute('''
                SELECT title, reason, total_amount, total_currency, paid_amount, paid_currency,
                       remaining_amount, installments_count, details, due_date, has_reminder, exchange_rate_used
                FROM special_payments WHERE id = ?
            ''', (self.payment_id,))
            
            payment = self.parent.cursor.fetchone()
            if payment:
                (title, reason, total_amount, total_currency, paid_amount, paid_currency,
                 remaining_amount, installments_count, details, due_date, has_reminder, exchange_rate_used) = payment
                
                self.title_input.setText(title)
                self.reason_input.setText(reason)
                
                # حفظ سعر الصرف الأصلي
                self.original_exchange_rate = exchange_rate_used if exchange_rate_used else self.exchange_rate
                
                # ✅ تعبئة الحقول باستخدام التنسيق الجديد
                self.total_amount_usd_input.setText(self.format_amount_display(total_amount))
                self.total_amount_lbp_input.setText(self.format_amount_display(total_amount * self.original_exchange_rate))
                
                self.paid_amount_usd_input.setText(self.format_amount_display(paid_amount))
                self.paid_amount_lbp_input.setText(self.format_amount_display(paid_amount * self.original_exchange_rate))
                
                self.installments_input.setText(str(installments_count))
                self.details_input.setPlainText(details if details else "")
                self.reminder_check.setChecked(has_reminder)
                
                if due_date:
                    due_date_obj = QDate.fromString(due_date, "yyyy-MM-dd")
                    self.due_date_input.setDate(due_date_obj)
                
                # تحديث الحقول المحسوبة تلقائياً
                self.calculate_remaining()
                self.calculate_installment()
                
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"❌ حدث خطأ في تحميل البيانات: {e}")

    def save_payment(self):
        """حفظ التعديلات على الدفعة"""
        try:
            title = self.title_input.text().strip()
            reason = self.reason_input.text().strip()
            details = self.details_input.toPlainText().strip()
            
            if not title:
                QMessageBox.warning(self, "تحذير", "⚠️ يرجى إدخال عنوان الدفعة")
                return
            
            total_usd_text = self.total_amount_usd_input.text().strip().replace(',', '')
            
            if not total_usd_text:
                QMessageBox.warning(self, "تحذير", "⚠️ يرجى إدخال المبلغ الإجمالي")
                return
            
            total_amount = float(total_usd_text)
            paid_amount = float(self.paid_amount_usd_input.text().strip().replace(',', '')) if self.paid_amount_usd_input.text().strip() else 0
            installments_count = int(self.installments_input.text().strip()) if self.installments_input.text().strip() else 0
            
            # حساب المبلغ المتبقي
            remaining_amount = total_amount - paid_amount
            
            # حساب قيمة الدفعة الواحدة
            installment_value = float(self.installment_amount_usd_input.text().strip().replace(',', '')) if self.installment_amount_usd_input.text().strip() else 0
            
            has_reminder = self.reminder_check.isChecked()
            due_date = self.due_date_input.date().toString("yyyy-MM-dd") if has_reminder else None
            
            # استخدام سعر الصرف الأصلي
            exchange_rate_to_use = self.original_exchange_rate
            
            # تحديث البيانات في قاعدة البيانات
            self.parent.cursor.execute('''
                UPDATE special_payments 
                SET title = ?, reason = ?, total_amount = ?, total_currency = ?, 
                    paid_amount = ?, paid_currency = ?, remaining_amount = ?,
                    installments_count = ?, installment_value = ?, details = ?, 
                    due_date = ?, has_reminder = ?, exchange_rate_used = ?
                WHERE id = ?
            ''', (title, reason, total_amount, "USD", paid_amount, "USD",
                  remaining_amount, installments_count, installment_value, details, 
                  due_date, has_reminder, exchange_rate_to_use, self.payment_id))
            
            self.parent.conn.commit()
            QMessageBox.information(self, "نجاح", "✅ تم تحديث الدفعة بنجاح")
            self.accept()
            
        except ValueError:
            QMessageBox.warning(self, "تحذير", "⚠️ يرجى إدخال أرقام صحيحة في الحقول الرقمية")
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"❌ حدث خطأ أثناء التحديث: {e}")


class ExchangeRateDialog(QDialog):
    def __init__(self, parent, current_rate):
        super().__init__(parent)
        self.parent = parent
        self.current_rate = current_rate
        self.setWindowTitle("تحديث سعر الصرف")
        self.setFixedSize(450, 250)
        self.setStyleSheet("""
            QDialog {
                background: #1e3a5f; 
                color: white;
                font-size: 16px;
                font-weight: bold;
            }
        """)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        
        title = QLabel("💰 تحديث سعر الصرف")
        title.setStyleSheet("font-size: 20px; font-weight: bold; margin: 15px;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        form_layout = QFormLayout()
        form_layout.setSpacing(15)
        
        current_rate_label = QLabel(f"السعر الحالي: 1 USD = {self.current_rate:,.0f} LBP")
        current_rate_label.setStyleSheet("font-size: 16px; color: #f39c12; font-weight: bold; padding: 10px; background: rgba(243, 156, 18, 0.1); border-radius: 5px;")
        form_layout.addRow("السعر الحالي:", current_rate_label)
        
        self.rate_input = QLineEdit()
        self.rate_input.setText(str(self.current_rate))
        self.rate_input.setPlaceholderText("أدخل السعر الجديد")
        self.rate_input.setStyleSheet("font-size: 16px; padding: 12px; background: white; color: black; border-radius: 5px; border: 2px solid #bdc3c7; font-weight: bold;")
        form_layout.addRow("💰 السعر الجديد (LBP):", self.rate_input)
        
        layout.addLayout(form_layout)
        
        button_layout = QHBoxLayout()
        
        update_btn = QPushButton("💾 تحديث السعر")
        update_btn.setStyleSheet("""
            QPushButton {
                background: #27ae60;
                color: white;
                font-size: 16px;
                padding: 12px 25px;
                border: none;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #219a52;
            }
        """)
        update_btn.clicked.connect(self.update_rate)
        
        cancel_btn = QPushButton("❌ إلغاء")
        cancel_btn.setStyleSheet("""
            QPushButton {
                background: #95a5a6;
                color: white;
                font-size: 16px;
                padding: 12px 25px;
                border: none;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #7f8c8d;
            }
        """)
        cancel_btn.clicked.connect(self.reject)
        
        button_layout.addWidget(update_btn)
        button_layout.addWidget(cancel_btn)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)

    def update_rate(self):
        """تحديث سعر الصرف"""
        try:
            rate_text = self.rate_input.text().strip()
            if not rate_text:
                QMessageBox.warning(self, "تحذير", "⚠️ يرجى إدخال سعر الصرف")
                return
                
            new_rate = float(rate_text)
            today = datetime.now().strftime("%Y-%m-%d")
            
            self.parent.cursor.execute('''
                INSERT INTO exchange_rates (usd_to_lbp_rate, last_updated)
                VALUES (?, ?)
            ''', (new_rate, today))
            
            self.parent.conn.commit()
            
            # تحديث السعر الحالي في البرنامج
            self.parent.exchange_rate = new_rate
            self.current_rate = new_rate
            
            QMessageBox.information(self, "نجاح", f"✅ تم تحديث سعر الصرف بنجاح\n\nالسعر الجديد: 1 USD = {new_rate:,.0f} LBP")
            self.accept()
            
        except ValueError:
            QMessageBox.warning(self, "تحذير", "⚠️ يرجى إدخال رقم صحيح لسعر الصرف")
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"❌ حدث خطأ أثناء التحديث: {e}")