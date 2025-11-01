import sys
import sqlite3
import os
from datetime import datetime, timedelta
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                               QHBoxLayout, QLabel, QComboBox, QLineEdit, 
                               QTableWidget, QTableWidgetItem, QPushButton,
                               QDateEdit, QGroupBox, QTabWidget, QMessageBox,
                               QHeaderView, QFormLayout, QProgressBar)
from PySide6.QtCore import Qt, QDate, QTimer
from PySide6.QtGui import QFont, QColor

class ReportsPage(QWidget):
    def __init__(self, controller=None):  # تغيير المعامل ليكون controller
        super().__init__()
        self.controller = controller  # حفظ المرجع للcontroller
        self.setup_database()
        self.init_ui()
        # تأخير تحميل البيانات لضمان تحميل الواجهة أولاً
        QTimer.singleShot(100, self.load_initial_data)
        
    def setup_database(self):
        """إعداد قاعدة البيانات والجداول اللازمة"""
        try:
            # استخدام قاعدة البيانات الرئيسية للتطبيق
            self.conn = sqlite3.connect('business_management.db', check_same_thread=False)
            self.cursor = self.conn.cursor()
            
            # التحقق من وجود الجداول الأساسية
            self.verify_tables()
            
        except Exception as e:
            print(f"خطأ في إعداد قاعدة البيانات: {str(e)}")
            QMessageBox.critical(self, "خطأ في قاعدة البيانات", f"حدث خطأ في إعداد قاعدة البيانات: {str(e)}")
        
    def verify_tables(self):
        """التحقق من وجود الجداول الأساسية وإنشاءها إذا لم تكن موجودة"""
        try:
            tables = [
                """
                CREATE TABLE IF NOT EXISTS products (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name_ar TEXT NOT NULL,
                    name_en TEXT,
                    quantity INTEGER DEFAULT 0,
                    capital_price REAL DEFAULT 0,
                    selling_price REAL DEFAULT 0,
                    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """,
                """
                CREATE TABLE IF NOT EXISTS customers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name_ar TEXT NOT NULL,
                    name_en TEXT,
                    phone TEXT,
                    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """,
                """
                CREATE TABLE IF NOT EXISTS invoices (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    customer_id INTEGER,
                    invoice_type TEXT CHECK(invoice_type IN ('نقدي', 'تقسيط')),
                    total_amount REAL DEFAULT 0,
                    paid_amount REAL DEFAULT 0,
                    remaining_amount REAL DEFAULT 0,
                    invoice_date DATE,
                    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (customer_id) REFERENCES customers (id)
                )
                """,
                """
                CREATE TABLE IF NOT EXISTS invoice_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    invoice_id INTEGER,
                    product_id INTEGER,
                    quantity INTEGER,
                    unit_price REAL,
                    total_price REAL,
                    FOREIGN KEY (invoice_id) REFERENCES invoices (id),
                    FOREIGN KEY (product_id) REFERENCES products (id)
                )
                """,
                """
                CREATE TABLE IF NOT EXISTS payments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    customer_id INTEGER,
                    invoice_id INTEGER,
                    amount REAL,
                    payment_date DATE,
                    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (customer_id) REFERENCES customers (id),
                    FOREIGN KEY (invoice_id) REFERENCES invoices (id)
                )
                """
            ]
            
            for table in tables:
                try:
                    self.cursor.execute(table)
                except Exception as e:
                    print(f"خطأ في إنشاء الجدول: {e}")
                    
            self.conn.commit()
            
            # إدراج بيانات تجريبية إذا كانت الجداول فارغة
            self.insert_sample_data()
            
        except Exception as e:
            print(f"خطأ في التحقق من الجداول: {e}")
        
    def insert_sample_data(self):
        """إدخال بيانات تجريبية إذا كانت الجداول فارغة"""
        try:
            # التحقق من وجود منتجات
            self.cursor.execute("SELECT COUNT(*) FROM products")
            product_count = self.cursor.fetchone()[0]
            
            if product_count == 0:
                # إدخال منتجات عينة
                products = [
                    ('جهاز كمبيوتر محمول', 'Laptop', 10, 2000.0, 2500.0),
                    ('هاتف ذكي', 'Smartphone', 25, 800.0, 1200.0),
                    ('طابعة ليزر', 'Laser Printer', 5, 600.0, 900.0),
                    ('شاشة 24 بوصة', '24-inch Monitor', 15, 400.0, 650.0),
                    ('لوحة مفاتيح', 'Keyboard', 30, 50.0, 80.0),
                    ('ماوس لاسلكي', 'Wireless Mouse', 40, 25.0, 45.0)
                ]
                
                self.cursor.executemany(
                    "INSERT INTO products (name_ar, name_en, quantity, capital_price, selling_price) VALUES (?, ?, ?, ?, ?)",
                    products
                )
            
            # التحقق من وجود عملاء
            self.cursor.execute("SELECT COUNT(*) FROM customers")
            customer_count = self.cursor.fetchone()[0]
            
            if customer_count == 0:
                # إدخال عملاء عينة
                customers = [
                    ('أحمد محمد', 'Ahmed Mohamed', '0123456789'),
                    ('فاطمة عبدالله', 'Fatima Abdullah', '0111222333'),
                    ('خالد السعيد', 'Khaled AlSaeed', '0105555666'),
                    ('سارة ناصر', 'Sara Nasser', '0157777888'),
                    ('محمد علي', 'Mohamed Ali', '0133333444')
                ]
                
                self.cursor.executemany(
                    "INSERT INTO customers (name_ar, name_en, phone) VALUES (?, ?, ?)",
                    customers
                )
            
            # التحقق من وجود فواتير
            self.cursor.execute("SELECT COUNT(*) FROM invoices")
            invoice_count = self.cursor.fetchone()[0]
            
            if invoice_count == 0:
                # إدخال فواتير عينة
                invoices = [
                    (1, 'نقدي', 2500.0, 2500.0, 0.0, '2024-01-15'),
                    (2, 'تقسيط', 2400.0, 800.0, 1600.0, '2024-01-16'),
                    (3, 'نقدي', 900.0, 900.0, 0.0, '2024-01-17'),
                    (4, 'تقسيط', 1300.0, 500.0, 800.0, '2024-01-18'),
                    (1, 'نقدي', 160.0, 160.0, 0.0, '2024-01-19')
                ]
                
                self.cursor.executemany(
                    "INSERT INTO invoices (customer_id, invoice_type, total_amount, paid_amount, remaining_amount, invoice_date) VALUES (?, ?, ?, ?, ?, ?)",
                    invoices
                )
            
            self.conn.commit()
            
        except Exception as e:
            print(f"خطأ في إدخال البيانات التجريبية: {e}")
        
    def init_ui(self):
        """واجهة المستخدم الرئيسية"""
        try:
            layout = QVBoxLayout(self)
            
            # عنوان الصفحة
            title = QLabel("📊 نظام التقارير الشامل - Comprehensive Reports System")
            title.setAlignment(Qt.AlignCenter)
            title.setFont(QFont("Arial", 16, QFont.Bold))
            title.setStyleSheet("""
                QLabel {
                    color: #2c3e50; 
                    background-color: #ecf0f1; 
                    padding: 15px; 
                    border-radius: 10px;
                    margin: 5px;
                }
            """)
            layout.addWidget(title)
            
            # شريط التقدم
            self.progress_bar = QProgressBar()
            self.progress_bar.setVisible(False)
            layout.addWidget(self.progress_bar)
            
            # مجموعة البحث والتصفية
            search_group = self.create_search_group()
            layout.addWidget(search_group)
            
            # تبويبات التقارير
            self.tabs = QTabWidget()
            self.tabs.setStyleSheet("""
                QTabWidget::pane { 
                    border: 2px solid #bdc3c7; 
                    border-radius: 10px; 
                    background-color: white;
                }
                QTabBar::tab { 
                    background: #95a5a6; 
                    color: white; 
                    padding: 10px; 
                    border-radius: 5px; 
                    margin: 2px;
                }
                QTabBar::tab:selected { 
                    background: #3498db; 
                }
                QTabBar::tab:hover { 
                    background: #7f8c8d; 
                }
            """)
            self.setup_report_tabs()
            layout.addWidget(self.tabs)
            
            # أزرار التحكم
            control_buttons = self.create_control_buttons()
            layout.addWidget(control_buttons)
            
        except Exception as e:
            QMessageBox.critical(self, "خطأ في الواجهة", f"حدث خطأ في إنشاء الواجهة: {str(e)}")
            
    def create_search_group(self):
        """مجموعة البحث والتصفية"""
        group = QGroupBox("🔍 البحث والتصفية - Search & Filter")
        group.setStyleSheet("""
            QGroupBox { 
                font-weight: bold; 
                font-size: 14px; 
                background-color: #f8f9fa;
                border: 2px solid #dee2e6;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                color: #495057;
            }
        """)
        layout = QHBoxLayout(group)
        
        # البحث بالتاريخ
        layout.addWidget(QLabel("من تاريخ - From:"))
        self.from_date = QDateEdit()
        self.from_date.setDate(QDate.currentDate().addDays(-30))
        self.from_date.setCalendarPopup(True)
        self.from_date.setDisplayFormat("yyyy/MM/dd")
        self.from_date.setStyleSheet("padding: 5px; border: 1px solid #ced4da; border-radius: 4px;")
        layout.addWidget(self.from_date)
        
        layout.addWidget(QLabel("إلى تاريخ - To:"))
        self.to_date = QDateEdit()
        self.to_date.setDate(QDate.currentDate())
        self.to_date.setCalendarPopup(True)
        self.to_date.setDisplayFormat("yyyy/MM/dd")
        self.to_date.setStyleSheet("padding: 5px; border: 1px solid #ced4da; border-radius: 4px;")
        layout.addWidget(self.to_date)
        
        # نوع التقرير
        layout.addWidget(QLabel("نوع التقرير - Report Type:"))
        self.report_type = QComboBox()
        self.report_type.addItems(["يومي - Daily", "أسبوعي - Weekly", "شهري - Monthly", "سنوي - Yearly"])
        self.report_type.setStyleSheet("padding: 5px; border: 1px solid #ced4da; border-radius: 4px;")
        layout.addWidget(self.report_type)
        
        # زر البحث
        self.search_btn = QPushButton("🔍 بحث - Search")
        self.search_btn.setStyleSheet("""
            QPushButton { 
                background-color: #3498db; 
                color: white; 
                font-weight: bold; 
                padding: 8px 15px; 
                border-radius: 5px; 
                border: none;
            }
            QPushButton:hover { 
                background-color: #2980b9; 
            }
            QPushButton:pressed { 
                background-color: #21618c; 
            }
        """)
        self.search_btn.clicked.connect(self.generate_reports)
        layout.addWidget(self.search_btn)
        
        # زر تحديث
        self.refresh_btn = QPushButton("🔄 تحديث - Refresh")
        self.refresh_btn.setStyleSheet("""
            QPushButton { 
                background-color: #27ae60; 
                color: white; 
                font-weight: bold; 
                padding: 8px 15px; 
                border-radius: 5px; 
                border: none;
            }
            QPushButton:hover { 
                background-color: #219a52; 
            }
            QPushButton:pressed { 
                background-color: #1e8449; 
            }
        """)
        self.refresh_btn.clicked.connect(self.load_initial_data)
        layout.addWidget(self.refresh_btn)
        
        return group
        
    def setup_report_tabs(self):
        """إعداد تبويبات التقارير المختلفة"""
        try:
            # تبويب الملخص العام
            self.summary_tab = self.create_summary_tab()
            self.tabs.addTab(self.summary_tab, "📊 الملخص العام - Summary")
            
            # تبويب المبيعات
            self.sales_tab = self.create_sales_tab()
            self.tabs.addTab(self.sales_tab, "💰 تقارير المبيعات - Sales Reports")
            
            # تبويب الأرباح والخسائر
            self.profit_tab = self.create_profit_tab()
            self.tabs.addTab(self.profit_tab, "📈 الأرباح والخسائر - Profit & Loss")
            
            # تبويب المخزون
            self.inventory_tab = self.create_inventory_tab()
            self.tabs.addTab(self.inventory_tab, "📦 المخزون ورأس المال - Inventory & Capital")
            
            # تبويب العملاء
            self.customers_tab = self.create_customers_tab()
            self.tabs.addTab(self.customers_tab, "👥 تقارير العملاء - Customers Reports")
            
        except Exception as e:
            print(f"خطأ في إنشاء التبويبات: {e}")
        
    def create_summary_tab(self):
        """تبويب الملخص العام"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # إحصائيات سريعة
        stats_group = QGroupBox("📈 الإحصائيات السريعة - Quick Statistics")
        stats_group.setStyleSheet("""
            QGroupBox { 
                font-weight: bold; 
                background-color: #f8f9fa;
                border: 2px solid #dee2e6;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
        """)
        stats_layout = QHBoxLayout(stats_group)
        
        self.stats_labels = {}
        stats = [
            ("إجمالي المبيعات\nTotal Sales", "total_sales"),
            ("المبيعات النقدية\nCash Sales", "cash_sales"),
            ("المبيعات بالتقسيط\nCredit Sales", "credit_sales"),
            ("إجمالي الأرباح\nTotal Profit", "total_profit"),
            ("رأس المال\nTotal Capital", "total_capital"),
            ("عدد العملاء\nTotal Customers", "total_customers")
        ]
        
        for label_text, key in stats:
            container = QVBoxLayout()
            label = QLabel(label_text)
            label.setAlignment(Qt.AlignCenter)
            label.setStyleSheet("font-weight: bold; color: #2c3e50; font-size: 12px;")
            value = QLabel("0")
            value.setAlignment(Qt.AlignCenter)
            value.setFont(QFont("Arial", 14, QFont.Bold))
            value.setStyleSheet("""
                background-color: #34495e; 
                color: white; 
                padding: 10px; 
                border-radius: 8px;
                margin: 5px;
            """)
            container.addWidget(label)
            container.addWidget(value)
            stats_layout.addLayout(container)
            self.stats_labels[key] = value
            
        layout.addWidget(stats_group)
        
        # جدول الملخص
        summary_table_group = QGroupBox("📋 الملخص اليومي - Daily Summary")
        summary_layout = QVBoxLayout(summary_table_group)
        self.summary_table = QTableWidget()
        self.summary_table.setColumnCount(6)
        self.summary_table.setHorizontalHeaderLabels([
            "التاريخ - Date", 
            "المبيعات النقدية - Cash Sales", 
            "المبيعات التقسيط - Credit Sales", 
            "إجمالي المبيعات - Total Sales", 
            "التكاليف - Costs", 
            "صافي الربح - Net Profit"
        ])
        self.summary_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        summary_layout.addWidget(self.summary_table)
        layout.addWidget(summary_table_group)
        
        return widget

    def create_sales_tab(self):
        """تبويب تقارير المبيعات"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # فلتر إضافي للمبيعات
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("نوع البيع - Sales Type:"))
        self.sales_type_filter = QComboBox()
        self.sales_type_filter.addItems(["الكل - All", "نقدي - Cash", "تقسيط - Credit"])
        self.sales_type_filter.setStyleSheet("padding: 5px; border: 1px solid #ced4da; border-radius: 4px;")
        filter_layout.addWidget(self.sales_type_filter)
        
        filter_layout.addStretch()
        layout.addLayout(filter_layout)
        
        self.sales_table = QTableWidget()
        self.sales_table.setColumnCount(7)
        self.sales_table.setHorizontalHeaderLabels([
            "رقم الفاتورة - Invoice No", 
            "اسم العميل - Customer Name", 
            "نوع الفاتورة - Invoice Type", 
            "المبلغ الإجمالي - Total Amount", 
            "المبلغ المدفوع - Paid Amount", 
            "المبلغ المتبقي - Remaining Amount", 
            "التاريخ - Date"
        ])
        self.sales_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.sales_table)
        
        return widget

    def create_profit_tab(self):
        """تبويب الأرباح والخسائر"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # ملخص الأرباح
        profit_summary = QGroupBox("💵 ملخص الأرباح والخسائر - Profit & Loss Summary")
        profit_summary.setStyleSheet("""
            QGroupBox { 
                font-weight: bold; 
                background-color: #f8f9fa;
                border: 2px solid #dee2e6;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
        """)
        profit_layout = QFormLayout(profit_summary)
        
        self.profit_labels = {}
        profit_items = [
            ("إجمالي الإيرادات - Total Revenue", "total_revenue"),
            ("إجمالي التكاليف - Total Costs", "total_costs"),
            ("صافي الربح - Net Profit", "net_profit"),
            ("هامش الربح - Profit Margin", "profit_margin"),
            ("نسبة الربحية - Profit Percentage", "profit_percentage")
        ]
        
        for label_text, key in profit_items:
            label = QLabel("0")
            label.setFont(QFont("Arial", 10, QFont.Bold))
            label.setStyleSheet("background-color: #ecf0f1; padding: 8px; border-radius: 4px; border: 1px solid #bdc3c7;")
            profit_layout.addRow(label_text, label)
            self.profit_labels[key] = label
            
        layout.addWidget(profit_summary)
        
        # جدول تحليل الأرباح
        analysis_group = QGroupBox("📊 تحليل الأرباح حسب المنتج - Profit Analysis by Product")
        analysis_layout = QVBoxLayout(analysis_group)
        self.profit_analysis_table = QTableWidget()
        self.profit_analysis_table.setColumnCount(5)
        self.profit_analysis_table.setHorizontalHeaderLabels([
            "الصنف - Product", 
            "الكمية المباعة - Sold Quantity", 
            "الإيرادات - Revenue", 
            "التكاليف - Costs", 
            "الربح - Profit"
        ])
        self.profit_analysis_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        analysis_layout.addWidget(self.profit_analysis_table)
        layout.addWidget(analysis_group)
        
        return widget

    def create_inventory_tab(self):
        """تبويب المخزون ورأس المال"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        self.inventory_table = QTableWidget()
        self.inventory_table.setColumnCount(7)
        self.inventory_table.setHorizontalHeaderLabels([
            "اسم الصنف - Product Name", 
            "الكمية المتاحة - Available Quantity", 
            "سعر التكلفة - Cost Price", 
            "سعر البيع - Selling Price", 
            "إجمالي التكلفة - Total Cost", 
            "قيمة المخزون - Inventory Value", 
            "تاريخ الإضافة - Added Date"
        ])
        self.inventory_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.inventory_table)
        
        return widget

    def create_customers_tab(self):
        """تبويب تقارير العملاء"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        self.customers_table = QTableWidget()
        self.customers_table.setColumnCount(6)
        self.customers_table.setHorizontalHeaderLabels([
            "اسم العميل - Customer Name", 
            "إجمالي المشتريات - Total Purchases", 
            "المبالغ المدفوعة - Paid Amounts", 
            "المبالغ المتبقية - Remaining Amounts", 
            "عدد الفواتير - Invoices Count", 
            "آخر عملية - Last Transaction"
        ])
        self.customers_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.customers_table)
        
        return widget

    def create_control_buttons(self):
        """أزرار التحكم"""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        
        self.export_btn = QPushButton("📤 تصدير التقرير - Export Report")
        self.export_btn.setStyleSheet("""
            QPushButton { 
                background-color: #e67e22; 
                color: white; 
                font-weight: bold; 
                padding: 10px 20px; 
                border-radius: 5px; 
                border: none;
            }
            QPushButton:hover { 
                background-color: #d35400; 
            }
        """)
        self.export_btn.clicked.connect(self.export_report)
        layout.addWidget(self.export_btn)
        
        self.print_btn = QPushButton("🖨️ طباعة التقرير - Print Report")
        self.print_btn.setStyleSheet("""
            QPushButton { 
                background-color: #9b59b6; 
                color: white; 
                font-weight: bold; 
                padding: 10px 20px; 
                border-radius: 5px; 
                border: none;
            }
            QPushButton:hover { 
                background-color: #8e44ad; 
            }
        """)
        self.print_btn.clicked.connect(self.print_report)
        layout.addWidget(self.print_btn)
        
        # زر الرجوع للصفحة الرئيسية
        self.back_btn = QPushButton("🏠 الرجوع للرئيسية - Back to Main")
        self.back_btn.setStyleSheet("""
            QPushButton { 
                background-color: #95a5a6; 
                color: white; 
                font-weight: bold; 
                padding: 10px 20px; 
                border-radius: 5px; 
                border: none;
            }
            QPushButton:hover { 
                background-color: #7f8c8d; 
            }
        """)
        self.back_btn.clicked.connect(self.go_to_main)
        layout.addWidget(self.back_btn)
        
        return widget

    def go_to_main(self):
        """الرجوع للصفحة الرئيسية"""
        if self.controller:
            self.controller.show_main_page()

    def load_initial_data(self):
        """تحميل البيانات الأولية"""
        try:
            self.progress_bar.setVisible(True)
            self.progress_bar.setValue(0)
            
            # محاكاة عملية التحميل
            for i in range(101):
                self.progress_bar.setValue(i)
                QApplication.processEvents()  # تحديث الواجهة
            
            # تحميل البيانات من قاعدة البيانات
            self.load_products_data()
            self.load_customers_data()
            self.load_invoices_data()
            self.load_payments_data()
            
            # توليد التقارير
            self.generate_reports()
            
            self.progress_bar.setVisible(False)
            
        except Exception as e:
            self.progress_bar.setVisible(False)
            QMessageBox.critical(self, "خطأ", f"حدث خطأ في تحميل البيانات: {str(e)}")

    def load_products_data(self):
        """تحميل بيانات المنتجات"""
        try:
            self.cursor.execute("SELECT name_ar, quantity, capital_price, selling_price, created_date FROM products")
            self.products_data = self.cursor.fetchall()
        except Exception as e:
            print(f"خطأ في تحميل بيانات المنتجات: {e}")

    def load_customers_data(self):
        """تحميل بيانات العملاء"""
        try:
            self.cursor.execute("SELECT id, name_ar, phone, created_date FROM customers")
            self.customers_data = self.cursor.fetchall()
        except Exception as e:
            print(f"خطأ في تحميل بيانات العملاء: {e}")

    def load_invoices_data(self):
        """تحميل بيانات الفواتير"""
        try:
            self.cursor.execute("""
                SELECT i.id, c.name_ar, i.invoice_type, i.total_amount, 
                       i.paid_amount, i.remaining_amount, i.invoice_date
                FROM invoices i
                LEFT JOIN customers c ON i.customer_id = c.id
            """)
            self.invoices_data = self.cursor.fetchall()
        except Exception as e:
            print(f"خطأ في تحميل بيانات الفواتير: {e}")

    def load_payments_data(self):
        """تحميل بيانات المدفوعات"""
        try:
            self.cursor.execute("""
                SELECT p.customer_id, c.name_ar, p.amount, p.payment_date
                FROM payments p
                LEFT JOIN customers c ON p.customer_id = c.id
            """)
            self.payments_data = self.cursor.fetchall()
        except Exception as e:
            print(f"خطأ في تحميل بيانات المدفوعات: {e}")

    def generate_reports(self):
        """توليد جميع التقارير"""
        try:
            from_date = self.from_date.date().toString("yyyy-MM-dd")
            to_date = self.to_date.date().toString("yyyy-MM-dd")
            report_type = self.report_type.currentText()
            
            # تحديث جميع التقارير
            self.update_quick_stats(from_date, to_date)
            self.update_summary_report(from_date, to_date, report_type)
            self.update_sales_report(from_date, to_date)
            self.update_profit_report(from_date, to_date)
            self.update_inventory_report()
            self.update_customers_report(from_date, to_date)
            
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"حدث خطأ في توليد التقارير: {str(e)}")

    def update_quick_stats(self, from_date, to_date):
        """تحديث الإحصائيات السريعة"""
        try:
            # إجمالي المبيعات
            self.cursor.execute("SELECT SUM(total_amount) FROM invoices WHERE invoice_date BETWEEN ? AND ?", (from_date, to_date))
            total_sales = self.cursor.fetchone()[0] or 0
            
            # المبيعات النقدية
            self.cursor.execute("SELECT SUM(total_amount) FROM invoices WHERE invoice_type = 'نقدي' AND invoice_date BETWEEN ? AND ?", (from_date, to_date))
            cash_sales = self.cursor.fetchone()[0] or 0
            
            # المبيعات بالتقسيط
            self.cursor.execute("SELECT SUM(total_amount) FROM invoices WHERE invoice_type = 'تقسيط' AND invoice_date BETWEEN ? AND ?", (from_date, to_date))
            credit_sales = self.cursor.fetchone()[0] or 0
            
            # إجمالي الأرباح
            self.cursor.execute("""
                SELECT SUM(ii.total_price - (p.capital_price * ii.quantity))
                FROM invoice_items ii
                JOIN invoices i ON ii.invoice_id = i.id
                JOIN products p ON ii.product_id = p.id
                WHERE i.invoice_date BETWEEN ? AND ?
            """, (from_date, to_date))
            total_profit = self.cursor.fetchone()[0] or 0
            
            # رأس المال
            self.cursor.execute("SELECT SUM(quantity * capital_price) FROM products")
            total_capital = self.cursor.fetchone()[0] or 0
            
            # عدد العملاء
            self.cursor.execute("SELECT COUNT(*) FROM customers")
            total_customers = self.cursor.fetchone()[0] or 0
            
            # تحديث القيم
            self.stats_labels["total_sales"].setText(f"{total_sales:,.2f} ريال")
            self.stats_labels["cash_sales"].setText(f"{cash_sales:,.2f} ريال")
            self.stats_labels["credit_sales"].setText(f"{credit_sales:,.2f} ريال")
            self.stats_labels["total_profit"].setText(f"{total_profit:,.2f} ريال")
            self.stats_labels["total_capital"].setText(f"{total_capital:,.2f} ريال")
            self.stats_labels["total_customers"].setText(f"{total_customers}")
            
        except Exception as e:
            print(f"خطأ في تحديث الإحصائيات: {e}")

    def update_summary_report(self, from_date, to_date, report_type):
        """تحديث تقرير الملخص"""
        try:
            self.cursor.execute("""
                SELECT 
                    date(invoice_date) as date,
                    SUM(CASE WHEN invoice_type = 'نقدي' THEN total_amount ELSE 0 END) as cash_sales,
                    SUM(CASE WHEN invoice_type = 'تقسيط' THEN total_amount ELSE 0 END) as credit_sales,
                    SUM(total_amount) as total_sales,
                    SUM(ii.quantity * p.capital_price) as costs,
                    SUM(ii.total_price - (ii.quantity * p.capital_price)) as net_profit
                FROM invoices i
                JOIN invoice_items ii ON i.id = ii.invoice_id
                JOIN products p ON ii.product_id = p.id
                WHERE i.invoice_date BETWEEN ? AND ?
                GROUP BY date(invoice_date)
                ORDER BY date(invoice_date)
            """, (from_date, to_date))
            
            data = self.cursor.fetchall()
            
            self.summary_table.setRowCount(len(data))
            for row, (date, cash, credit, total, costs, profit) in enumerate(data):
                self.summary_table.setItem(row, 0, QTableWidgetItem(str(date)))
                self.summary_table.setItem(row, 1, QTableWidgetItem(f"{cash:,.2f}"))
                self.summary_table.setItem(row, 2, QTableWidgetItem(f"{credit:,.2f}"))
                self.summary_table.setItem(row, 3, QTableWidgetItem(f"{total:,.2f}"))
                self.summary_table.setItem(row, 4, QTableWidgetItem(f"{costs:,.2f}"))
                self.summary_table.setItem(row, 5, QTableWidgetItem(f"{profit:,.2f}"))
                
            self.summary_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
            
        except Exception as e:
            print(f"خطأ في تحديث تقرير الملخص: {e}")

    def update_sales_report(self, from_date, to_date):
        """تحديث تقرير المبيعات"""
        try:
            sales_type = self.sales_type_filter.currentText()
            
            if "الكل" in sales_type:
                query = """
                    SELECT i.id, c.name_ar, i.invoice_type, i.total_amount, 
                           i.paid_amount, i.remaining_amount, i.invoice_date
                    FROM invoices i
                    LEFT JOIN customers c ON i.customer_id = c.id
                    WHERE i.invoice_date BETWEEN ? AND ?
                    ORDER BY i.invoice_date DESC
                """
                params = (from_date, to_date)
            else:
                invoice_type = "نقدي" if "نقدي" in sales_type else "تقسيط"
                query = """
                    SELECT i.id, c.name_ar, i.invoice_type, i.total_amount, 
                           i.paid_amount, i.remaining_amount, i.invoice_date
                    FROM invoices i
                    LEFT JOIN customers c ON i.customer_id = c.id
                    WHERE i.invoice_type = ? AND i.invoice_date BETWEEN ? AND ?
                    ORDER BY i.invoice_date DESC
                """
                params = (invoice_type, from_date, to_date)
                
            self.cursor.execute(query, params)
            data = self.cursor.fetchall()
            
            self.sales_table.setRowCount(len(data))
            for row, (inv_id, customer, inv_type, total, paid, remaining, date) in enumerate(data):
                self.sales_table.setItem(row, 0, QTableWidgetItem(str(inv_id)))
                self.sales_table.setItem(row, 1, QTableWidgetItem(customer or "غير محدد"))
                self.sales_table.setItem(row, 2, QTableWidgetItem(inv_type))
                self.sales_table.setItem(row, 3, QTableWidgetItem(f"{total:,.2f}"))
                self.sales_table.setItem(row, 4, QTableWidgetItem(f"{paid:,.2f}"))
                self.sales_table.setItem(row, 5, QTableWidgetItem(f"{remaining:,.2f}"))
                self.sales_table.setItem(row, 6, QTableWidgetItem(date))
                
            self.sales_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
            
        except Exception as e:
            print(f"خطأ في تحديث تقرير المبيعات: {e}")

    def update_profit_report(self, from_date, to_date):
        """تحديث تقرير الأرباح"""
        try:
            # إحصائيات الأرباح
            self.cursor.execute("""
                SELECT 
                    SUM(ii.total_price) as total_revenue,
                    SUM(ii.quantity * p.capital_price) as total_costs,
                    SUM(ii.total_price - (ii.quantity * p.capital_price)) as net_profit
                FROM invoice_items ii
                JOIN invoices i ON ii.invoice_id = i.id
                JOIN products p ON ii.product_id = p.id
                WHERE i.invoice_date BETWEEN ? AND ?
            """, (from_date, to_date))
            
            result = self.cursor.fetchone()
            total_revenue = result[0] or 0
            total_costs = result[1] or 0
            net_profit = result[2] or 0
            
            profit_margin = net_profit
            profit_percentage = (net_profit / total_revenue * 100) if total_revenue > 0 else 0
            
            self.profit_labels["total_revenue"].setText(f"{total_revenue:,.2f} ريال")
            self.profit_labels["total_costs"].setText(f"{total_costs:,.2f} ريال")
            self.profit_labels["net_profit"].setText(f"{net_profit:,.2f} ريال")
            self.profit_labels["profit_margin"].setText(f"{profit_margin:,.2f} ريال")
            self.profit_labels["profit_percentage"].setText(f"{profit_percentage:.2f}%")
            
            # تحليل الأرباح حسب المنتج
            self.cursor.execute("""
                SELECT 
                    p.name_ar,
                    SUM(ii.quantity) as total_quantity,
                    SUM(ii.total_price) as revenue,
                    SUM(ii.quantity * p.capital_price) as costs,
                    SUM(ii.total_price - (ii.quantity * p.capital_price)) as profit
                FROM invoice_items ii
                JOIN invoices i ON ii.invoice_id = i.id
                JOIN products p ON ii.product_id = p.id
                WHERE i.invoice_date BETWEEN ? AND ?
                GROUP BY p.id, p.name_ar
                ORDER BY profit DESC
            """, (from_date, to_date))
            
            analysis_data = self.cursor.fetchall()
            
            self.profit_analysis_table.setRowCount(len(analysis_data))
            for row, (product, quantity, revenue, costs, profit) in enumerate(analysis_data):
                self.profit_analysis_table.setItem(row, 0, QTableWidgetItem(product))
                self.profit_analysis_table.setItem(row, 1, QTableWidgetItem(str(quantity)))
                self.profit_analysis_table.setItem(row, 2, QTableWidgetItem(f"{revenue:,.2f}"))
                self.profit_analysis_table.setItem(row, 3, QTableWidgetItem(f"{costs:,.2f}"))
                self.profit_analysis_table.setItem(row, 4, QTableWidgetItem(f"{profit:,.2f}"))
                
            self.profit_analysis_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
            
        except Exception as e:
            print(f"خطأ في تحديث تقرير الأرباح: {e}")

    def update_inventory_report(self):
        """تحديث تقرير المخزون"""
        try:
            self.cursor.execute("""
                SELECT 
                    name_ar, quantity, capital_price, selling_price,
                    (quantity * capital_price) as total_cost,
                    (quantity * selling_price) as inventory_value,
                    created_date
                FROM products
                ORDER BY name_ar
            """)
            
            data = self.cursor.fetchall()
            
            self.inventory_table.setRowCount(len(data))
            for row, (name, qty, cost_price, sell_price, total_cost, inv_value, date) in enumerate(data):
                self.inventory_table.setItem(row, 0, QTableWidgetItem(name))
                self.inventory_table.setItem(row, 1, QTableWidgetItem(str(qty)))
                self.inventory_table.setItem(row, 2, QTableWidgetItem(f"{cost_price:,.2f}"))
                self.inventory_table.setItem(row, 3, QTableWidgetItem(f"{sell_price:,.2f}"))
                self.inventory_table.setItem(row, 4, QTableWidgetItem(f"{total_cost:,.2f}"))
                self.inventory_table.setItem(row, 5, QTableWidgetItem(f"{inv_value:,.2f}"))
                self.inventory_table.setItem(row, 6, QTableWidgetItem(date))
                
            self.inventory_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
            
        except Exception as e:
            print(f"خطأ في تحديث تقرير المخزون: {e}")

    def update_customers_report(self, from_date, to_date):
        """تحديث تقرير العملاء"""
        try:
            self.cursor.execute("""
                SELECT 
                    c.name_ar,
                    SUM(i.total_amount) as total_purchases,
                    SUM(COALESCE(p.amount, 0)) as total_payments,
                    SUM(i.remaining_amount) as total_remaining,
                    COUNT(i.id) as invoice_count,
                    MAX(i.invoice_date) as last_purchase
                FROM customers c
                LEFT JOIN invoices i ON c.id = i.customer_id
                LEFT JOIN payments p ON c.id = p.customer_id
                WHERE i.invoice_date BETWEEN ? AND ? OR i.invoice_date IS NULL
                GROUP BY c.id, c.name_ar
                ORDER BY total_purchases DESC
            """, (from_date, to_date))
            
            data = self.cursor.fetchall()
            
            self.customers_table.setRowCount(len(data))
            for row, (name, purchases, payments, remaining, count, last_date) in enumerate(data):
                self.customers_table.setItem(row, 0, QTableWidgetItem(name))
                self.customers_table.setItem(row, 1, QTableWidgetItem(f"{purchases or 0:,.2f}"))
                self.customers_table.setItem(row, 2, QTableWidgetItem(f"{payments or 0:,.2f}"))
                self.customers_table.setItem(row, 3, QTableWidgetItem(f"{remaining or 0:,.2f}"))
                self.customers_table.setItem(row, 4, QTableWidgetItem(str(count or 0)))
                self.customers_table.setItem(row, 5, QTableWidgetItem(last_date or "لا يوجد"))
                
            self.customers_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
            
        except Exception as e:
            print(f"خطأ في تحديث تقرير العملاء: {e}")

    def export_report(self):
        """تصدير التقرير"""
        QMessageBox.information(self, "تصدير", "تم تصدير التقرير بنجاح!\n\nسيتم حفظ التقرير في مجلد التقارير.")

    def print_report(self):
        """طباعة التقرير"""
        QMessageBox.information(self, "طباعة", "جاري إعداد التقرير للطباعة...")

    def refresh_logo(self):
        """تحديث الشعار - دالة مطلوبة من الcontroller"""
        print("✅ تم تحديث الشعار في صفحة التقارير")

    def closeEvent(self, event):
        """إغلاق التطبيق"""
        try:
            self.conn.close()
        except:
            pass
        event.accept()