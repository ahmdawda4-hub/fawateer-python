import os
import json
import sqlite3
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QLineEdit, QComboBox, QDialog,
    QDialogButtonBox, QFormLayout, QSpinBox,
    QDoubleSpinBox, QMessageBox, QGroupBox,
    QScrollArea, QFrame, QCheckBox, QTextEdit,
    QDateEdit, QTabWidget, QSplitter, QProgressBar,
    QFileDialog, QInputDialog
)
from PySide6.QtCore import Qt, QSize, QDate, QTimer
from PySide6.QtGui import QPixmap, QFont, QIcon, QPainter, QColor, QKeySequence, QShortcut, QIntValidator, QDoubleValidator

DB_PATH = "chbib_materials.db"

# ✅ استيراد الصفحة الجديدة
try:
    from pages.customer_invoices_page import CustomerInvoicesPage
    print("✅ تم تحميل صفحة الزبائن بنجاح")
except ImportError as e:
    print(f"❌ خطأ في تحميل صفحة الزبائن: {e}")

class InvoicesPage(QWidget):
    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        self.setup_event_listeners()
        self.data_file = "data/invoices.json"
        self.customers_file = "data/customers.json"
        self.reports_file = "data/reports.json"
        self.sales_stats_file = "data/sales_stats.json"  # ✅ ملف جديد للإحصائيات
        self.exchange_rate = self.load_exchange_rate()
        self.current_invoice_items = []
        self.invoice_counter = self.load_invoice_counter()
        
        # ✅ تهيئة إحصائيات المبيعات
        self.total_cash_sales = 0.0
        self.total_installment_sales = 0.0
        
        self.ensure_data_files()
        self.load_sales_stats()  # ✅ تحميل الإحصائيات المحفوظة
        self.setup_ui()
        self.load_customers()
        self.setShortcut()

    def load_sales_stats(self):
        """✅ تحميل إحصائيات المبيعات من ملف"""
        try:
            if os.path.exists(self.sales_stats_file):
                with open(self.sales_stats_file, 'r', encoding='utf-8') as f:
                    stats = json.load(f)
                    self.total_cash_sales = stats.get('total_cash_sales', 0.0)
                    self.total_installment_sales = stats.get('total_installment_sales', 0.0)
            else:
                # ✅ إذا لم يوجد الملف، نحسب الإحصائيات من الفواتير الحالية
                self.calculate_initial_sales_stats()
        except Exception as e:
            print(f"❌ خطأ في تحميل إحصائيات المبيعات: {e}")
            self.calculate_initial_sales_stats()

    def calculate_initial_sales_stats(self):
        """✅ حساب الإحصائيات الأولية من الفواتير الحالية"""
        try:
            if not os.path.exists(self.data_file):
                self.total_cash_sales = 0.0
                self.total_installment_sales = 0.0
                return

            with open(self.data_file, 'r', encoding='utf-8') as f:
                invoices = json.load(f)

            self.total_cash_sales = 0.0
            self.total_installment_sales = 0.0

            for invoice in invoices:
                payment_type = invoice.get('payment_type', 'نقدي')
                total_amount = float(invoice.get('total_amount', 0))
                
                if payment_type == 'نقدي':
                    self.total_cash_sales += total_amount
                elif payment_type == 'تقسيط':
                    self.total_installment_sales += total_amount

            self.save_sales_stats()
            print(f"✅ تم حساب الإحصائيات الأولية: نقدي={self.total_cash_sales}, تقسيط={self.total_installment_sales}")

        except Exception as e:
            print(f"❌ خطأ في حساب الإحصائيات الأولية: {e}")

    def save_sales_stats(self):
        """✅ حفظ إحصائيات المبيعات في ملف"""
        try:
            os.makedirs("data", exist_ok=True)
            stats = {
                'total_cash_sales': self.total_cash_sales,
                'total_installment_sales': self.total_installment_sales,
                'last_updated': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            with open(self.sales_stats_file, 'w', encoding='utf-8') as f:
                json.dump(stats, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"❌ خطأ في حفظ إحصائيات المبيعات: {e}")

    def update_sales_stats(self, invoice_data):
        """✅ تحديث إحصائيات المبيعات عند إضافة فاتورة جديدة"""
        try:
            payment_type = invoice_data.get('payment_type', 'نقدي')
            total_amount = float(invoice_data.get('total_amount', 0))
            
            if payment_type == 'نقدي':
                self.total_cash_sales += total_amount
            elif payment_type == 'تقسيط':
                self.total_installment_sales += total_amount
            
            self.save_sales_stats()
            
            print(f"✅ تم تحديث الإحصائيات: نقدي={self.total_cash_sales}, تقسيط={self.total_installment_sales}")
            
        except Exception as e:
            print(f"❌ خطأ في تحديث إحصائيات المبيعات: {e}")

    def convert_installment_to_cash(self, invoice_data):
        """✅ تحويل فاتورة تقسيط إلى نقدي عند السداد"""
        try:
            total_amount = float(invoice_data.get('total_amount', 0))
            
            # ✅ خصم من التقسيط وإضافة للنقدي
            self.total_installment_sales -= total_amount
            self.total_cash_sales += total_amount
            
            # ✅ التأكد من أن الأرقام لا تكون سالبة
            if self.total_installment_sales < 0:
                self.total_installment_sales = 0
                
            self.save_sales_stats()
            
            print(f"✅ تم التحويل: {total_amount} من التقسيط إلى النقدي")
            
        except Exception as e:
            print(f"❌ خطأ في تحويل التقسيط إلى نقدي: {e}")

    def reset_monthly_sales(self):
        """✅ تصفير إحصائيات المبيعات الشهرية"""
        try:
            reply = QMessageBox.question(
                self,
                "تصفير الإحصائيات الشهرية",
                "هل تريد تصفير إحصائيات المبيعات للشهر الجديد؟\n\nسيتم الاحتفاظ بالأرشيف في صفحة التقارير.",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                # ✅ حفظ البيانات الحالية للتقرير (سيتم استخدامها في reports_page.py)
                monthly_report = self.prepare_monthly_report()
                
                # ✅ تصفير الإحصائيات
                self.total_cash_sales = 0.0
                self.total_installment_sales = 0.0
                self.save_sales_stats()
                
                # ✅ رسالة نجاح
                self.show_auto_close_success_message("✅ تم تصفير الإحصائيات الشهرية بنجاح")
                
                print(f"✅ تم تصفير الإحصائيات الشهرية: {monthly_report}")
                
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"حدث خطأ في تصفير الإحصائيات: {e}")

    def prepare_monthly_report(self):
        """✅ تحضير تقرير شهري لصفحة التقارير المستقبلية"""
        return {
            'month': datetime.now().month,
            'year': datetime.now().year,
            'final_cash_sales': self.total_cash_sales,
            'final_installment_sales': self.total_installment_sales,
            'total_sales': self.total_cash_sales + self.total_installment_sales,
            'reset_date': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

    def load_invoice_counter(self):
        """✅ تحميل عداد الفواتير من ملف"""
        try:
            counter_file = "data/invoice_counter.json"
            if os.path.exists(counter_file):
                with open(counter_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data.get('counter', 1)
            return 1
        except:
            return 1

    def update_invoice_counters(self):
        """✅ تحديث عدادات الفواتير تلقائياً"""
        try:
            cash_count = 0
            installment_count = 0
            cash_total = 0.0
            installment_total = 0.0
            
            invoices_file = "data/invoices.json"
            if os.path.exists(invoices_file):
                with open(invoices_file, 'r', encoding='utf-8') as f:
                    invoices = json.load(f)
                
                for invoice in invoices:
                    invoice_type = invoice.get('type', 'نقدي')
                    total_usd = invoice.get('total_usd', 0)
                    
                    if invoice_type == 'نقدي':
                        cash_count += 1
                        cash_total += total_usd
                    elif invoice_type == 'تقسيط':
                        installment_count += 1
                        installment_total += total_usd
            
            print(f"✅ [تحديث العدادات] نقدي: {cash_count}, تقسيط: {installment_count}")
            
        except Exception as e:
            print(f"❌ خطأ في تحديث العدادات: {e}")

    def save_invoice_counter(self):
        """✅ حفظ عداد الفواتير في ملف"""
        try:
            counter_file = "data/invoice_counter.json"
            os.makedirs("data", exist_ok=True)
            with open(counter_file, 'w', encoding='utf-8') as f:
                json.dump({'counter': self.invoice_counter}, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"❌ خطأ في حفظ عداد الفواتير: {e}")

    def get_next_invoice_number(self):
        """✅ الحصول على رقم الفاتورة التالي"""
        number = self.invoice_counter
        self.invoice_counter += 1
        self.save_invoice_counter()
        return number

    def load_exchange_rate(self):
        """✅ تحميل سعر الصرف من ملف الإعدادات - محدث"""
        try:
            # الأولوية: ملف سعر الصرف الجديد
            exchange_file = "data/exchange_rate.json"
            if os.path.exists(exchange_file):
                with open(exchange_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    rate = data.get('exchange_rate')
                    if rate:
                        print(f"✅ [سعر الصرف] تم تحميل السعر من الملف: {rate:,.0f} LBP/USD")
                        return float(rate)
            
            # الاحتياطي: ملف الإعدادات القديم
            admin_file = "data/admin_settings.json"
            if os.path.exists(admin_file):
                with open(admin_file, 'r', encoding='utf-8') as f:
                    admin_data = json.load(f)
                    if admin_data and 'exchange_rate' in admin_data:
                        rate = float(admin_data['exchange_rate'])
                        print(f"✅ [سعر الصرف] تم تحميل السعر من الإدارة: {rate:,.0f} LBP/USD")
                        return rate

            # الاحتياطي: الإعدادات القديمة
            settings_file = "data/settings.json"
            if os.path.exists(settings_file):
                with open(settings_file, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                    if settings and 'exchange_rate' in settings[0]:
                        rate = float(settings[0]['exchange_rate'])
                        print(f"✅ [سعر الصرف] تم تحميل السعر من الإعدادات: {rate:,.0f} LBP/USD")
                        return rate
        except Exception as e:
            print(f"❌ خطأ في تحميل سعر الصرف: {e}")
        
        print("⚠️ [سعر الصرف] استخدام السعر الافتراضي: 89,000 LBP/USD")
        return 89000.0

    def update_exchange_rate(self, new_rate):
        """✅ تحديث سعر الصرف تلقائياً من صفحة الإدارة"""
        try:
            old_rate = self.exchange_rate
            self.exchange_rate = new_rate
            print(f"✅ [سعر الصرف] تم التحديث التلقائي: {old_rate:,.0f} → {new_rate:,.0f} LBP/USD")
            
            # تحديث المبيعات الإجمالية
            self.load_customers()
            
        except Exception as e:
            print(f"❌ [سعر الصرف] خطأ في التحديث التلقائي: {e}")

    def ensure_data_files(self):
        """تأكد من وجود ملفات البيانات"""
        os.makedirs("data", exist_ok=True)
        for file in [self.data_file, self.customers_file, self.reports_file, self.sales_stats_file]:
            if not os.path.exists(file):
                with open(file, 'w', encoding='utf-8') as f:
                    json.dump([], f, ensure_ascii=False, indent=2)

    def load_products_from_database(self):
        """✅ تحميل الأصناف من قاعدة البيانات مع تحديث سعر الصرف"""
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
                    'buy_price': float(row[4]),  # السعر الأصلي
                    'sell_price': float(row[5]), # السعر الأصلي
                    'stock': float(row[6]),
                    'currency': row[7]
                }
                
                # ✅ تحويل الأسعار بناءً على العملة وسعر الصرف الحالي
                if product['currency'].upper() == 'LBP':
                    # تحويل من LBP إلى USD باستخدام سعر الصرف الحالي
                    product['buy_price_usd'] = product['buy_price'] / self.exchange_rate
                    product['sell_price_usd'] = product['sell_price'] / self.exchange_rate
                    print(f"✅ [تحويل الأسعار] {product['name']}: {product['sell_price']} LBP → {product['sell_price_usd']:.4f} USD")
                else:
                    # إذا كانت العملة USD، استخدام الأسعار كما هي
                    product['buy_price_usd'] = product['buy_price']
                    product['sell_price_usd'] = product['sell_price']
                    print(f"✅ [تحويل الأسعار] منتج {product['name']}: {product['sell_price_usd']:.4f} USD")
                
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
            
            # ✅ إذا لم توجد وحدات مخصصة، نستخدم الوحدة الافتراضية من الجدول الرئيسي
            if not units:
                c.execute("SELECT sell_unit FROM Items WHERE id=?", (item_id,))
                default_unit = c.fetchone()
                if default_unit and default_unit[0]:
                    units = [default_unit[0]]
            
            return units if units else ["قطعة"]  # ✅ قيمة افتراضية إذا لم توجد وحدات
            
        except Exception as e:
            print(f"❌ خطأ في جلب وحدات المبيع للصنف {item_id}: {e}")
            return ["قطعة"]

    def setup_ui(self):
        """إنشاء واجهة صفحة الفواتير"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # الهيدر - زر الرجوع في اليسار والشعار في اليمين
        header_layout = QHBoxLayout()
        
        # زر الرجوع
        back_btn = QPushButton()
        back_btn.setIcon(QIcon(r"C:\Users\User\Desktop\chbib1\icons\back.png"))
        back_btn.setIconSize(QSize(120, 100))
        back_btn.setFixedSize(40,38)
        back_btn.setStyleSheet("""
            QPushButton {
                background-color: #2c3e50;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #34495e;
            }
        """)
        back_btn.clicked.connect(self.controller.show_main_page)
        
        # الشعار في اليمين بحجم أكبر
        logo_label = QLabel()
        logo_pixmap = QPixmap(r"C:\Users\User\Desktop\chbib1\icons\logo.png")
        if not logo_pixmap.isNull():
            logo_label.setPixmap(logo_pixmap.scaled(150, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        logo_label.setAlignment(Qt.AlignCenter)
        
        header_layout.addWidget(back_btn)
        header_layout.addStretch()
        header_layout.addWidget(logo_label)
        
        main_layout.addLayout(header_layout)

        title = QLabel("إدارة الزبائن")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("""
            QLabel {
                font-size: 30px;
                font-weight: bold;
                color: white;
                padding: 5px;
                background-color: transparent;
                border-radius: 3px;
                font-family: Arial;
            }
        """)
        main_layout.addWidget(title)

        control_layout = QHBoxLayout()
        
        search_layout = QHBoxLayout()
        search_label = QLabel("بحث سريع:")
        search_label.setStyleSheet("color: white; font-size: 18px; font-weight: bold; font-family: Arial;")
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("ابحث بالاسم، الهاتف، أو العنوان...")
        self.search_input.setStyleSheet("""
            QLineEdit {
                padding: 12px;
                border: 2px solid #3498db;
                border-radius: 5px;
                font-size: 18px;
                background-color: white;
                font-weight: bold;
                font-family: Arial;
                min-height: 30px;
            }
        """)
        self.search_input.textChanged.connect(self.search_customers)
        
        search_layout.addWidget(search_label)
        search_layout.addWidget(self.search_input)
        
        buttons_layout = QHBoxLayout()
        
        # ✅ زر إضافة زبون - مع محاذاة لليسار
        self.add_customer_btn = QPushButton("إضافة زبون")
        self.add_customer_btn.setStyleSheet("""
            QPushButton {
                background-color: #2c3e50;
                color: white;
                padding: 15px 25px;
                border: none;
                border-radius: 6px;
                font-size: 16px;
                font-weight: bold;
                font-family: Arial;
                min-height: 30px;
            }
            QPushButton:hover {
                background-color: #34495e;
            }
        """)
        self.add_customer_btn.clicked.connect(self.show_add_customer_dialog)
        
        # ✅ زر تعديل زبون - مع محاذاة لليسار
        self.edit_customer_btn = QPushButton("تعديل زبون")
        self.edit_customer_btn.setStyleSheet("""
            QPushButton {
                background-color: #2c3e50;
                color: white;
                padding: 15px 25px;
                border: none;
                border-radius: 6px;
                font-size: 16px;
                font-weight: bold;
                font-family: Arial;
                min-height: 30px;
            }
            QPushButton:hover {
                background-color: #34495e;
            }
        """)
        self.edit_customer_btn.clicked.connect(self.edit_selected_customer)
        
        # ✅ زر حذف زبون
        self.delete_customer_btn = QPushButton("حذف زبون")
        self.delete_customer_btn.setStyleSheet("""
            QPushButton {
                background-color: #2c3e50;
                color: white;
                padding: 15px 25px;
                border: none;
                border-radius: 6px;
                font-size: 16px;
                font-weight: bold;
                font-family: Arial;
                min-height: 30px;
            }
            QPushButton:hover {
                background-color: #34495e;
            }
        """)
        self.delete_customer_btn.clicked.connect(self.delete_selected_customer)
        
        buttons_layout.addWidget(self.add_customer_btn)
        buttons_layout.addWidget(self.edit_customer_btn)
        buttons_layout.addWidget(self.delete_customer_btn)
        
        control_layout.addLayout(search_layout)
        control_layout.addStretch()
        control_layout.addLayout(buttons_layout)
        
        main_layout.addLayout(control_layout)

        self.setup_customers_table()
        main_layout.addWidget(self.customers_table)

        # ✅ إضافة خانات الإحصائيات في أسفل الصفحة (فقط خانة الزبائن)
        self.setup_stats_widgets()
        main_layout.addWidget(self.stats_widget)

        self.setShortcut()

    def setup_stats_widgets(self):
        """✅ إنشاء خانات الإحصائيات في أسفل الصفحة (فقط خانة الزبائن)"""
        self.stats_widget = QWidget()
        stats_layout = QHBoxLayout(self.stats_widget)
        stats_layout.setContentsMargins(5, 5, 5, 5)
        stats_layout.setSpacing(10)

        # ✅ خانة الزبائن (الزرقاء) فقط
        self.setup_customer_counter()
        stats_layout.addWidget(self.customer_counter_widget)

        stats_layout.addStretch()

    def setup_customer_counter(self):
        """✅ إنشاء خانة عدد الزبائن في أسفل الصفحة"""
        self.customer_counter_widget = QWidget()
        self.customer_counter_widget.setFixedHeight(120)
        self.customer_counter_widget.setFixedWidth(170)
    
        self.customer_counter_widget.setStyleSheet("""
        QWidget {
            background-color: #1a237e;
            border: 2px solid #283593;
            border-radius: 10px;
            margin: 5px;
        }
    """)
    
        counter_layout = QVBoxLayout(self.customer_counter_widget)
        counter_layout.setContentsMargins(20, 10, 20, 10)
    
        # ✅ نص "الزبائن" في الأعلى
        customers_label = QLabel("الزبائن")
        customers_label.setStyleSheet("""
        QLabel {
            background-color: transparent;
            color: white;
            font-size: 28px;
            font-weight: bold;
            font-family: Arial;
            padding: 5px 15px;
        }
    """)
        customers_label.setAlignment(Qt.AlignCenter)
    
        # ✅ العداد في الأسفل
        self.customer_count_label = QLabel("0")
        self.customer_count_label.setStyleSheet("""
        QLabel {
            background-color: transparent;
            color: white;
            font-size: 32px;
            font-weight: bold;
            font-family: Arial;
            padding: 5px 15px;
        }
    """)
        self.customer_count_label.setAlignment(Qt.AlignCenter)
    
        counter_layout.addWidget(customers_label)
        counter_layout.addWidget(self.customer_count_label)
    
        # ✅ تحديث العداد أول مرة
        self.update_customer_counter()

    def setShortcut(self):
        """تعيين اختصار الحذف"""
        self.delete_shortcut = QShortcut(QKeySequence("Delete"), self)
        self.delete_shortcut.activated.connect(self.delete_selected_customer)

    def setup_customers_table(self):
        """إنشاء جدول الزبائن مع إمكانية التحديد الفردي"""
        self.customers_table = QTableWidget()
        self.customers_table.setColumnCount(5)  # ✅ زيادة عمود للترقيم
        self.customers_table.setHorizontalHeaderLabels([
            "", "اسم الزبون", "رقم الهاتف", "العنوان", "تاريخ الإضافة"  # ✅ إضافة عمود "م" للترقيم
        ])
        
        self.customers_table.setStyleSheet("""
        QTableWidget {
            background-color: white;
            border: 2px solid #2c3e50;
            border-radius: 8px;
            font-size: 18px;
            gridline-color: #bdc3c7;
            selection-background-color: #3498db;
            selection-color: white;
            font-weight: bold;
            font-family: Arial;
        }
        QHeaderView::section {
            background-color: #2c3e50;
            color: white;
            padding: 15px;
            border: none;
            font-weight: bold;
            font-size: 18px;
            font-family: Arial;
        }
        QTableWidget::item {
            padding: 15px;
            border-bottom: 1px solid #ecf0f1;
            font-weight: bold;
            font-size: 18px;
            font-family: Arial;
            background-color: white;
        }
        QTableWidget::item:selected {
            background-color: #3498db;
            color: white;
        }
        QTableWidget::item:focus {
            border: none;
            outline: none;
            background-color: #3498db;
        }
    """)
        
        # ✅ ✅ ✅ السماح بالتحديد الفردي فقط
        self.customers_table.setSelectionMode(QTableWidget.SingleSelection)
        self.customers_table.setSelectionBehavior(QTableWidget.SelectRows)
        
        # ✅ إزالة المستطيل عند التحديد
        self.customers_table.setFocusPolicy(Qt.NoFocus)
        
       # ✅ ضبط عرض الأعمدة بشكل منفصل
        self.customers_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)
        self.customers_table.setColumnWidth(0, 30)  # عرض 30 بكسل لعمود الترقيم

        # جعل باقي الأعمدة تتمدد
        self.customers_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.customers_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.customers_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        self.customers_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch)
        
        # ✅ فتح صفحة الزبون عند الضغط مرتين على اسم الزبون
        self.customers_table.doubleClicked.connect(self.on_table_double_click)
        
        # ✅ إزالة التحديد عند النقر على الخلفية
        self.customers_table.viewport().installEventFilter(self)

    def eventFilter(self, source, event):
        """✅ إزالة التحديد عند النقر على الخلفية"""
        if (source is self.customers_table.viewport() and 
            event.type() == event.Type.MouseButtonPress):
            # الحصول على العنصر الذي تم النقر عليه
            item = self.customers_table.itemAt(event.pos())
            if item is None:
                # إذا لم يتم النقر على عنصر، إزالة التحديد
                self.customers_table.clearSelection()
                return True
        return super().eventFilter(source, event)

    def on_table_double_click(self, index):
        """✅ فتح صفحة الزبون عند الضغط مرتين على اسم الزبون في الجدول"""
        selected_row = self.customers_table.currentRow()
        if selected_row >= 0:
            # الحصول على بيانات الزبون من الجدول
            customer_name_item = self.customers_table.item(selected_row, 1)  # ✅ تغيير العمود إلى 1 (اسم الزبون)
            customer_phone_item = self.customers_table.item(selected_row, 2)  # ✅ تغيير العمود إلى 2 (رقم الهاتف)
            
            if customer_name_item and customer_phone_item:
                customer_name = customer_name_item.text()
                customer_phone = customer_phone_item.text()
                
                if customer_name and customer_name != 'غير محدد':
                    # ✅ إزالة التحديد قبل فتح الصفحة
                    self.customers_table.clearSelection()
                    
                    self.open_customer_page(customer_name, customer_phone)

    def open_customer_page(self, customer_name, customer_phone):
        """✅ الانتقال إلى صفحة الزبون الخاصة به"""
        try:
            # البحث عن customer_id للزبون
            customer_id = self.find_customer_id(customer_name, customer_phone)
            
            if customer_id:
                # ✅ حل مشكلة عدد المعطيات - تمرير 3 معطيات فقط
                self.controller.show_customer_page(customer_id, customer_name, customer_phone)
                print(f"✅ تم الانتقال إلى صفحة الزبون: {customer_name}")
            else:
                print(f"⚠️ لم يتم العثور على customer_id للزبون: {customer_name}")
                QMessageBox.information(self, "معلومات", f"لم يتم العثور على صفحة زبون للزبون: {customer_name}")
                
        except Exception as e:
            print(f"❌ خطأ في فتح صفحة الزبون: {e}")
            QMessageBox.warning(self, "تحذير", f"خطأ في فتح صفحة الزبون: {e}")

    def load_customers(self):
        """تحميل الزبائن وعرضهم في الجدول"""
        try:
            with open(self.customers_file, 'r', encoding='utf-8') as f:
                customers = json.load(f)
        except:
            customers = []
        
        self.customers_table.setRowCount(len(customers))
        
        for row, customer in enumerate(customers):
            # ✅ إضافة الترقيم في العمود الأول
            number_item = QTableWidgetItem(str(row + 1))  # ✅ الترقيم يبدأ من 1
            number_item.setBackground(QColor("white"))
            number_item.setForeground(QColor("black"))
            number_item.setTextAlignment(Qt.AlignCenter)  # ✅ محاذاة الترقيم في المنتصف
            self.customers_table.setItem(row, 0, number_item)
            
            # ✅ إضافة بيانات الزبون إلى الجدول - بأرقام كبيرة وواضحة
            customer_name_item = QTableWidgetItem(customer.get('name', 'غير محدد'))
            customer_name_item.setBackground(QColor("white"))
            customer_name_item.setForeground(QColor("black"))
            self.customers_table.setItem(row, 1, customer_name_item)
            
            customer_phone_item = QTableWidgetItem(customer.get('phone', 'غير محدد'))
            customer_phone_item.setBackground(QColor("white"))
            customer_phone_item.setForeground(QColor("black"))
            self.customers_table.setItem(row, 2, customer_phone_item)
            
            customer_address_item = QTableWidgetItem(customer.get('address', 'غير محدد'))
            customer_address_item.setBackground(QColor("white"))
            customer_address_item.setForeground(QColor("black"))
            self.customers_table.setItem(row, 3, customer_address_item)
            
            # تنسيق التاريخ - d/m/y فقط بدون وقت
            date_str = customer.get('date_added', '')
            date_item = QTableWidgetItem()
            date_item.setBackground(QColor("white"))
            date_item.setForeground(QColor("black"))
            if date_str:
                try:
                    dt = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
                    formatted_date = f"{dt.strftime('%d/%m/%Y')}"  # d/m/y فقط
                    date_item.setText(formatted_date)
                except:
                    date_item.setText(date_str)
            self.customers_table.setItem(row, 4, date_item)
        
        # ✅ تحديث عداد الزبائن بعد التحميل
        self.update_customer_counter()

    def search_customers(self):
        """بحث في الزبائن"""
        search_text = self.search_input.text().lower()
        
        for row in range(self.customers_table.rowCount()):
            match = False
            for col in range(1, 4):  # ✅ البحث في الأعمدة من 1 إلى 3 (الاسم، الهاتف، العنوان) - تخطي عمود الترقيم
                item = self.customers_table.item(row, col)
                if item and search_text in item.text().lower():
                    match = True
                    break
            
            self.customers_table.setRowHidden(row, not match)

    def show_add_customer_dialog(self):
        """✅ عرض نافذة إضافة زبون جديد"""
        dialog = AddCustomerDialog(self)
        if dialog.exec() == QDialog.Accepted:
            customer_data = dialog.get_customer_data()
            self.save_customer(customer_data)

    def edit_selected_customer(self):
        """✅ تعديل الزبون المحدد"""
        selected_items = self.customers_table.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "تحذير", "يرجى اختيار زبون للتعديل")
            return
        
        # ✅ ✅ ✅ الحصول على الصف المحدد الأول فقط
        selected_row = self.customers_table.row(selected_items[0])
        self.edit_customer(selected_row)

    def edit_customer(self, row):
        """✅ تعديل بيانات الزبون"""
        try:
            with open(self.customers_file, 'r', encoding='utf-8') as f:
                customers = json.load(f)
            
            if row < len(customers):
                customer_to_edit = customers[row]
                
                # ✅ فتح نافذة التعديل
                dialog = EditCustomerDialog(self, customer_to_edit)
                if dialog.exec() == QDialog.Accepted:
                    updated_data = dialog.get_updated_data()
                    
                    # ✅ تحديث بيانات الزبون
                    customers[row].update(updated_data)
                    
                    with open(self.customers_file, 'w', encoding='utf-8') as f:
                        json.dump(customers, f, ensure_ascii=False, indent=2)
                    
                    # ✅ رسالة نجاح
                    self.show_auto_close_success_message("✅ تم تعديل الزبون بنجاح")
                    
                    # ✅ تحديث الجدول والعداد
                    self.load_customers()
                    
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"حدث خطأ في التعديل: {e}")

    def save_customer(self, customer_data):
        """✅ حفظ الزبون الجديد"""
        try:
            with open(self.customers_file, 'r', encoding='utf-8') as f:
                customers = json.load(f)
            
            # ✅ التحقق من عدم وجود زبون بنفس الاسم والهاتف
            for customer in customers:
                if (customer.get('name') == customer_data['name'] and 
                    customer.get('phone') == customer_data['phone']):
                    QMessageBox.warning(self, "تحذير", "يوجد زبون مسجل بنفس الاسم ورقم الهاتف")
                    return
            
            # ✅ إضافة الزبون الجديد
            customer_data['id'] = len(customers) + 1
            customer_data['date_added'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            customers.append(customer_data)
            
            with open(self.customers_file, 'w', encoding='utf-8') as f:
                json.dump(customers, f, ensure_ascii=False, indent=2)
            
            # ✅ رسالة نجاح
            self.show_auto_close_success_message("✅ تم إضافة الزبون بنجاح")
            
            # ✅ تحديث الجدول والعداد
            self.load_customers()
            
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"حدث خطأ في حفظ الزبون: {e}")

    def show_auto_close_success_message(self, message):
        """✅ عرض رسالة نجاح تختفي تلقائياً"""
        success_msg = QMessageBox(self)
        success_msg.setIcon(QMessageBox.Information)
        success_msg.setWindowTitle("نجاح")
        success_msg.setText(message)
        success_msg.setStandardButtons(QMessageBox.Ok)
        
        success_msg.setStyleSheet("""
        QMessageBox {
            background-color: #1e2a3a;
            border: 2px solid #27ae60;
            border-radius: 10px;
            min-width: 400px;
            min-height: 150px;
        }
        QMessageBox QLabel {
            color: white;
            font-size: 18px;
            font-weight: bold;
            font-family: Arial;
        }
        QMessageBox QPushButton {
            background-color: #27ae60;
            color: white;
            padding: 12px 25px;
            border: none;
            border-radius: 5px;
            font-size: 16px;
            font-weight: bold;
            font-family: Arial;
            min-width: 100px;
            min-height: 35px;
        }
        QMessageBox QPushButton:hover {
            background-color: #229954;
        }
    """)
        
        success_msg.exec()
        success_msg.close()

    def delete_selected_customer(self):
        """✅ حذف الزبون المحدد مع جميع فواتيره ودفعاته"""
        selected_items = self.customers_table.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "تحذير", "يرجى اختيار زبون للحذف")
            return
        
        # ✅ ✅ ✅ الحصول على الصف المحدد الأول فقط
        selected_row = self.customers_table.row(selected_items[0])
        
        try:
            with open(self.customers_file, 'r', encoding='utf-8') as f:
                customers = json.load(f)
            
            if selected_row < len(customers):
                customer_to_delete = customers[selected_row]
                customer_name = customer_to_delete.get('name', '')
                customer_phone = customer_to_delete.get('phone', '')
                
                # ✅ سؤال تأكيد الحذف
                reply = QMessageBox.question(
                    self, 
                    "تأكيد الحذف",
                    f"هل تريد حذف الزبون '{customer_name}'؟\n\n"
                    f"سيتم حذف:\n"
                    f"• جميع فواتير الزبون\n"
                    f"• جميع دفعات الزبون\n"
                    f"• جميع سجلات الزبون في النظام\n\n"
                    f"هذا الإجراء لا يمكن التراجع عنه!",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )
                
                if reply == QMessageBox.Yes:
                    # ✅ حذف جميع البيانات المرتبطة بالزبون
                    self.delete_all_customer_data(customer_name, customer_phone)
                    
                    # ✅ حذف الزبون من القائمة
                    customers.pop(selected_row)
                    
                    with open(self.customers_file, 'w', encoding='utf-8') as f:
                        json.dump(customers, f, ensure_ascii=False, indent=2)
                    
                    # ✅ رسالة نجاح
                    self.show_auto_close_success_message(f"✅ تم حذف الزبون '{customer_name}' وجميع بياناته بنجاح")
                    
                    # ✅ تحديث الجدول والعداد
                    self.load_customers()
                    
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"حدث خطأ في الحذف: {e}")

    def delete_all_customer_data(self, customer_name, customer_phone):
        """✅ حذف جميع البيانات المرتبطة بالزبون"""
        try:
            print(f"🔍 بدء حذف جميع بيانات الزبون: {customer_name} - {customer_phone}")
            
            # 1. ✅ حذف فواتير الزبون من invoices.json
            self.delete_customer_invoices(customer_name, customer_phone)
            
            # 2. ✅ حذف دفعات الزبون من payments.json
            self.delete_customer_payments(customer_name, customer_phone)
            
            # 3. ✅ حذف فواتير الزبون من customer_invoices.json
            self.delete_customer_invoices_from_customer_page(customer_name, customer_phone)
            
            # 4. ✅ حذف دفعات الزبون من customer_payments.json
            self.delete_customer_payments_from_customer_page(customer_name, customer_phone)
            
            print(f"✅ تم حذف جميع بيانات الزبون: {customer_name}")
            
        except Exception as e:
            print(f"❌ خطأ في حذف بيانات الزبون: {e}")

    def delete_customer_invoices(self, customer_name, customer_phone):
        """✅ حذف فواتير الزبون من ملف invoices.json"""
        try:
            invoices_file = "data/invoices.json"
            if not os.path.exists(invoices_file):
                print("⚠️ ملف invoices.json غير موجود")
                return
                
            with open(invoices_file, 'r', encoding='utf-8') as f:
                invoices = json.load(f)
            
            # ✅ تصفية الفواتير وإزالة فواتير الزبون
            updated_invoices = []
            invoices_deleted = 0
            
            for invoice in invoices:
                if (invoice.get('customer_name') != customer_name or 
                    invoice.get('customer_phone') != customer_phone):
                    updated_invoices.append(invoice)
                else:
                    invoices_deleted += 1
            
            with open(invoices_file, 'w', encoding='utf-8') as f:
                json.dump(updated_invoices, f, ensure_ascii=False, indent=2)
                
            print(f"✅ تم حذف {invoices_deleted} فاتورة للزبون: {customer_name}")
            
        except Exception as e:
            print(f"❌ خطأ في حذف فواتير الزبون: {e}")

    def delete_customer_payments(self, customer_name, customer_phone):
        """✅ حذف دفعات الزبون من ملف payments.json"""
        try:
            payments_file = "data/payments.json"
            if not os.path.exists(payments_file):
                print("⚠️ ملف payments.json غير موجود")
                return
                
            with open(payments_file, 'r', encoding='utf-8') as f:
                payments = json.load(f)
            
            # ✅ تصفية الدفعات وإزالة دفعات الزبون
            updated_payments = []
            payments_deleted = 0
            
            for payment in payments:
                if (payment.get('customer_name') != customer_name or 
                    payment.get('customer_phone') != customer_phone):
                    updated_payments.append(payment)
                else:
                    payments_deleted += 1
            
            with open(payments_file, 'w', encoding='utf-8') as f:
                json.dump(updated_payments, f, ensure_ascii=False, indent=2)
                
            print(f"✅ تم حذف {payments_deleted} دفعة للزبون: {customer_name}")
            
        except Exception as e:
            print(f"❌ خطأ في حذف دفعات الزبون: {e}")

    def delete_customer_invoices_from_customer_page(self, customer_name, customer_phone):
        """✅ حذف فواتير الزبون من صفحة customer_invoices_page"""
        try:
            # ملف الفواتير الخاص بصفحة الزبائن
            customer_invoices_file = "data/customer_invoices.json"
            if not os.path.exists(customer_invoices_file):
                print("⚠️ ملف customer_invoices.json غير موجود")
                return
                
            with open(customer_invoices_file, 'r', encoding='utf-8') as f:
                customer_invoices = json.load(f)
            
            # ✅ تصفية الفواتير وإزالة فواتير الزبون
            updated_customer_invoices = []
            customer_invoices_deleted = 0
            
            for invoice in customer_invoices:
                if (invoice.get('customer_name') != customer_name or 
                    invoice.get('customer_phone') != customer_phone):
                    updated_customer_invoices.append(invoice)
                else:
                    customer_invoices_deleted += 1
            
            with open(customer_invoices_file, 'w', encoding='utf-8') as f:
                json.dump(updated_customer_invoices, f, ensure_ascii=False, indent=2)
                
            print(f"✅ تم حذف {customer_invoices_deleted} فاتورة من صفحة الزبون: {customer_name}")
            
        except Exception as e:
            print(f"❌ خطأ في حذف فواتير الزبون من صفحة الزبائن: {e}")

    def delete_customer_payments_from_customer_page(self, customer_name, customer_phone):
        """✅ حذف دفعات الزبون من صفحة customer_payments_page"""
        try:
            # ملف الدفعات الخاص بصفحة الزبائن
            customer_payments_file = "data/customer_payments.json"
            if not os.path.exists(customer_payments_file):
                print("⚠️ ملف customer_payments.json غير موجود")
                return
                
            with open(customer_payments_file, 'r', encoding='utf-8') as f:
                customer_payments = json.load(f)
            
            # ✅ تصفية الدفعات وإزالة دفعات الزبون
            updated_customer_payments = []
            customer_payments_deleted = 0
            
            for payment in customer_payments:
                if (payment.get('customer_name') != customer_name or 
                    payment.get('customer_phone') != customer_phone):
                    updated_customer_payments.append(payment)
                else:
                    customer_payments_deleted += 1
            
            with open(customer_payments_file, 'w', encoding='utf-8') as f:
                json.dump(updated_customer_payments, f, ensure_ascii=False, indent=2)
                
            print(f"✅ تم حذف {customer_payments_deleted} دفعة من صفحة الزبون: {customer_name}")
            
        except Exception as e:
            print(f"❌ خطأ في حذف دفعات الزبون من صفحة الزبائن: {e}")

    def refresh_logo(self):
        """تحديث الشعار"""
        pass

    def paintEvent(self, event):
        """رسم الخلفية"""
        painter = QPainter(self)
        bg = QPixmap(r"C:\Users\User\Desktop\chbib1\icons\bg.jpg")
        if not bg.isNull():
            painter.drawPixmap(self.rect(), bg)
        super().paintEvent(event)

    def find_customer_id(self, customer_name, customer_phone):
        """✅ البحث عن customer_id للزبون"""
        try:
            with open(self.customers_file, 'r', encoding='utf-8') as f:
                customers = json.load(f)
            
            for i, customer in enumerate(customers):
                if (customer.get('name') == customer_name and 
                    customer.get('phone') == customer_phone):
                    return i + 1  # استخدام الفهرس كـ ID
            
            return None
            
        except Exception as e:
            print(f"❌ خطأ في البحث عن customer_id: {e}")
            return None

    def showEvent(self, event):
        """✅ إزالة التحديد عند العودة إلى الصفحة"""
        super().showEvent(event)
        self.customers_table.clearSelection()

    # ======== ✅ نظام الإشعارات - إضافة جديدة ========
    def setup_event_listeners(self):
        """✅ الاشتراك في الأحداث المهمة"""
        try:
            # الوصول لمدير الأحداث من خلال الكونترولر
            if hasattr(self.controller, 'event_manager'):
                event_manager = self.controller.event_manager
                
                # الاشتراك في حدث إضافة فاتورة
                event_manager.subscribe("invoice_added", self.on_invoice_added)
                
                # الاشتراك في حدث تحديث البيانات
                event_manager.subscribe("data_updated", self.on_data_updated)
                
                # الاشتراك في حدث تحديث المبيعات
                event_manager.subscribe("sales_updated", self.on_sales_updated)
                
                print("✅ تم الاشتراك في أحداث invoices_page بنجاح")
        except Exception as e:
            print(f"❌ خطأ في إعداد مستمعي الأحداث: {e}")

    def on_invoice_added(self, invoice_data):
        """✅ معالجة حدث إضافة فاتورة جديدة"""
        try:
            print(f"✅ تم استقبال إشعار بفاتورة جديدة: {invoice_data.get('invoice_number', '')}")
            
            # تحديث كل شيء تلقائياً
            self.load_customers()  # إعادة تحميل الزبائن
            self.update_customer_counter()  # تحديث عداد الزبائن
            
            # تحديث إحصائيات المبيعات إذا كانت البيانات متوفرة
            if invoice_data:
                self.update_sales_stats_from_invoice(invoice_data)
            
            print("✅ تم تحديث invoices_page تلقائياً بعد إضافة فاتورة")
            
        except Exception as e:
            print(f"❌ خطأ في معالجة حدث إضافة فاتورة: {e}")

    def on_data_updated(self, data=None):
        """✅ معالجة حدث تحديث البيانات - الإصدار المحسن"""
        try:
            print("✅ تم استقبال إشعار بتحديث البيانات")
            
            # إذا كان البيانات تحتوي على إجراء حذف
            if data and isinstance(data, dict) and data.get('action') == 'delete':
                invoice_data = data.get('invoice', {})
                if invoice_data:
                    # نستدعي الدالة الجديدة لتحديث المبيعات بعد الحذف
                    self.update_sales_stats_after_deletion(invoice_data)
                    print(f"✅ تم معالجة حذف الفاتورة: {invoice_data.get('invoice_number', '')}")
            
            # إعادة تحميل كل شيء في جميع الأحوال
            self.load_customers()
            self.update_customer_counter()
            self.calculate_initial_sales_stats()
            
            print("✅ تم تحديث invoices_page تلقائياً بعد حدث البيانات")
            
        except Exception as e:
            print(f"❌ خطأ في معالجة حدث تحديث البيانات: {e}")

    def on_sales_updated(self, data=None):
        """✅ معالجة حدث تحديث المبيعات"""
        try:
            print("✅ تم استقبال إشعار بتحديث المبيعات")
            self.calculate_initial_sales_stats()  # إعادة حساب المبيعات
            print("✅ تم تحديث إحصائيات المبيعات تلقائياً")
        except Exception as e:
            print(f"❌ خطأ في معالجة حدث تحديث المبيعات: {e}")

    def update_sales_stats_from_invoice(self, invoice_data):
        """✅ تحديث إحصائيات المبيعات من بيانات الفاتورة"""
        try:
            invoice_type = invoice_data.get('type', 'نقدي')
            total_amount = float(invoice_data.get('total_usd', 0))
            
            if invoice_type == 'نقدي':
                self.total_cash_sales += total_amount
            elif invoice_type == 'تقسيط':
                self.total_installment_sales += total_amount
            
            # حفظ الإحصائيات المحدثة
            self.save_sales_stats()
            
            print(f"✅ تم تحديث المبيعات: نقدي (+{total_amount})" if invoice_type == 'نقدي' else f"✅ تم تحديث المبيعات: تقسيط (+{total_amount})")
            
        except Exception as e:
            print(f"❌ خطأ في تحديث إحصائيات المبيعات: {e}")

    def update_sales_stats_after_deletion(self, invoice_data):
        """✅ تحديث إحصائيات المبيعات بعد حذف فاتورة"""
        try:
            # 1. جلب نوع الفاتورة (نقدي أو تقسيط)
            invoice_type = invoice_data.get('type', 'نقدي')
            
            # 2. جلب المبلغ الإجمالي للفاتورة
            total_amount = float(invoice_data.get('total_usd', 0))
            
            # 3. حسب نوع الفاتورة، نخصم المبلغ من الخانة المناسبة
            if invoice_type == 'نقدي':
                # إذا كانت نقدي: نخصم من total_cash_sales
                self.total_cash_sales = max(0, self.total_cash_sales - total_amount)
            elif invoice_type == 'تقسيط':
                # إذا كانت تقسيط: نخصم من total_installment_sales
                self.total_installment_sales = max(0, self.total_installment_sales - total_amount)
            
            # 4. نحفظ الإحصائيات الجديدة في الملف
            self.save_sales_stats()
            
            # 6. نطبع رسالة تأكيد
            print(f"✅ تم تحديث المبيعات بعد الحذف: {invoice_type} (-{total_amount})")
            
        except Exception as e:
            print(f"❌ خطأ في تحديث إحصائيات المبيعات بعد الحذف: {e}")

    def update_customer_counter(self):
        """✅ تحديث عدد الزبائن تلقائياً"""
        try:
            with open(self.customers_file, 'r', encoding='utf-8') as f:
                customers = json.load(f)
            
            customer_count = len(customers)
            self.customer_count_label.setText(str(customer_count))
            
        except Exception as e:
            print(f"❌ خطأ في تحديث عداد الزبائن: {e}")
            self.customer_count_label.setText("0")
    # ======== ✅ نهاية نظام الإشعارات ========

class AddCustomerDialog(QDialog):
    """نافذة إضافة زبون جديد"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.customer_data = None
        self.setup_ui()
    
    def setup_ui(self):
        self.setWindowTitle("إضافة زبون جديد")
        self.setFixedSize(500, 400)
        self.setStyleSheet("""
        QDialog {
            background-color: #1e2a3a;
            border: 2px solid #34495e;
            border-radius: 10px;
        }
        QLabel {
            color: white;
            font-size: 18px;
            font-weight: bold;
            font-family: Arial;
        }
        QLineEdit, QTextEdit {
            background-color: white;
            color: black;
            padding: 12px;
            border-radius: 5px;
            font-size: 18px;
            border: 1px solid #bdc3c7;
            font-family: Arial;
            font-weight: bold;
            min-height: 40px;
        }
        QLineEdit:focus, QTextEdit:focus {
            border: 2px solid #3498db;
            background-color: #f8f9fa;
        }
    """)
        
        layout = QVBoxLayout(self)
        
        # العنوان
        title = QLabel("إضافة زبون جديد")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("""
        QLabel {
            color: white;
            font-size: 24px;
            font-weight: bold;
            padding: 15px;
            background-color: transparent;
            font-family: Arial;
        }
    """)
        layout.addWidget(title)
        
        # نموذج إدخال البيانات - محاذاة لليسار للكلمات العربية
        form_layout = QFormLayout()
        form_layout.setFormAlignment(Qt.AlignRight | Qt.AlignTop)  # ✅ محاذاة لليمين للكلمات العربية
        
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("اسم الزبون (إجباري)")
        form_layout.addRow("الاسم:", self.name_input)
        
        self.phone_input = QLineEdit()
        self.phone_input.setPlaceholderText("رقم الهاتف (إجباري)")
        # منع إدخال الأحرف في رقم الهاتف
        phone_validator = QIntValidator(0, 999999999, self)
        self.phone_input.setValidator(phone_validator)
        form_layout.addRow("الهاتف:", self.phone_input)
        
        self.address_input = QTextEdit()
        self.address_input.setPlaceholderText("العنوان (اختياري)")
        self.address_input.setMaximumHeight(80)
        form_layout.addRow("العنوان:", self.address_input)
        
        layout.addLayout(form_layout)
        layout.addStretch()
        
        # أزرار الحفظ والإلغاء
        button_layout = QHBoxLayout()
        
        save_btn = QPushButton("💾 حفظ الزبون")
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
        save_btn.clicked.connect(self.save_customer)
        
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
    
    def save_customer(self):
        """حفظ بيانات الزبون"""
        name = self.name_input.text().strip()
        phone = self.phone_input.text().strip()
        address = self.address_input.toPlainText().strip()
        
        # ✅ التحقق من الحقول الإجبارية
        if not name:
            QMessageBox.warning(self, "تحذير", "يرجى إدخال اسم الزبون")
            return
        
        if not phone:
            QMessageBox.warning(self, "تحذير", "يرجى إدخال رقم الهاتف")
            return
        
        if len(phone) < 4:
            QMessageBox.warning(self, "تحذير", "يرجى إدخال رقم هاتف صحيح (4 أرقام على الأقل)")
            return
        
        self.customer_data = {
            'name': name,
            'phone': phone,
            'address': address or 'غير محدد'
        }
        
        self.accept()
    
    def get_customer_data(self):
        return self.customer_data


class EditCustomerDialog(QDialog):
    """✅ نافذة تعديل بيانات الزبون"""
    def __init__(self, parent=None, customer_data=None):
        super().__init__(parent)
        self.customer_data = customer_data
        self.updated_data = {}
        self.setup_ui()
    
    def setup_ui(self):
        self.setWindowTitle("تعديل بيانات الزبون")
        self.setFixedSize(500, 450)
        self.setStyleSheet("""
        QDialog {
            background-color: #1e2a3a;
            border: 2px solid #34495e;
            border-radius: 10px;
        }
        QLabel {
            color: white;
            font-size: 18px;
            font-weight: bold;
            font-family: Arial;
        }
        QLineEdit, QTextEdit, QDateEdit {
            background-color: white;
            color: black;
            padding: 12px;
            border-radius: 5px;
            font-size: 18px;
            border: 1px solid #bdc3c7;
            font-family: Arial;
            font-weight: bold;
            min-height: 40px;
        }
        QLineEdit:focus, QTextEdit:focus, QDateEdit:focus {
            border: 2px solid #3498db;
            background-color: #f8f9fa;
        }
    """)
        
        layout = QVBoxLayout(self)
        
        # العنوان
        title = QLabel("تعديل بيانات الزبون")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("""
        QLabel {
            color: white;
            font-size: 24px;
            font-weight: bold;
            padding: 15px;
            background-color: transparent;
            font-family: Arial;
        }
    """)
        layout.addWidget(title)
        
        # نموذج إدخال البيانات - محاذاة لليسار للكلمات العربية
        form_layout = QFormLayout()
        form_layout.setFormAlignment(Qt.AlignRight | Qt.AlignTop)  # ✅ محاذاة لليمين للكلمات العربية
        
        # ✅ اسم الزبون
        self.name_input = QLineEdit()
        self.name_input.setText(self.customer_data.get('name', ''))
        self.name_input.setPlaceholderText("اسم الزبون (إجباري)")
        form_layout.addRow("الاسم:", self.name_input)
        
        # ✅ رقم الهاتف
        self.phone_input = QLineEdit()
        self.phone_input.setText(self.customer_data.get('phone', ''))
        self.phone_input.setPlaceholderText("رقم الهاتف (إجباري)")
        phone_validator = QIntValidator(0, 999999999, self)
        self.phone_input.setValidator(phone_validator)
        form_layout.addRow("الهاتف:", self.phone_input)
        
        # ✅ العنوان
        self.address_input = QTextEdit()
        self.address_input.setText(self.customer_data.get('address', ''))
        self.address_input.setPlaceholderText("العنوان (اختياري)")
        self.address_input.setMaximumHeight(80)
        form_layout.addRow("العنوان:", self.address_input)
        
        # ✅ تاريخ الإضافة - QLineEdit يدعم التنسيقات المختلفة
        self.date_input = QLineEdit()
        current_date_str = self.customer_data.get('date_added', '')
        if current_date_str:
            try:
                dt = datetime.strptime(current_date_str, "%Y-%m-%d %H:%M:%S")
                formatted_date = f"{dt.strftime('%d/%m/%Y')}"  # d/m/y فقط
                self.date_input.setText(formatted_date)
            except:
                self.date_input.setText(current_date_str)
        else:
            current_date = datetime.now().strftime("%d/%m/%Y")
            self.date_input.setText(current_date)
        
        self.date_input.setPlaceholderText("dd/mm/yyyy أو dd-mm-yyyy")
        form_layout.addRow("تاريخ الإضافة:", self.date_input)
        
        layout.addLayout(form_layout)
        layout.addStretch()
        
        # أزرار الحفظ والإلغاء
        button_layout = QHBoxLayout()
        
        save_btn = QPushButton("💾 حفظ التعديلات")
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
        save_btn.clicked.connect(self.save_changes)
        
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
    
    def save_changes(self):
        """✅ حفظ التعديلات"""
        name = self.name_input.text().strip()
        phone = self.phone_input.text().strip()
        address = self.address_input.toPlainText().strip()
        date_input = self.date_input.text().strip()
        
        # ✅ التحقق من الحقول الإجبارية
        if not name:
            QMessageBox.warning(self, "تحذير", "يرجى إدخال اسم الزبون")
            return
        
        if not phone:
            QMessageBox.warning(self, "تحذير", "يرجى إدخال رقم الهاتف")
            return
        
        if len(phone) < 4:
            QMessageBox.warning(self, "تحذير", "يرجى إدخال رقم هاتف صحيح (4 أرقام على الأقل)")
            return
        
        # ✅ معالجة تاريخ الإضافة يدوياً
        if date_input:
            try:
                # دعم التنسيقات المختلفة: dd/mm/yyyy أو dd-mm-yyyy
                if '/' in date_input:
                    day, month, year = date_input.split('/')
                elif '-' in date_input:
                    day, month, year = date_input.split('-')
                else:
                    raise ValueError("تنسيق تاريخ غير مدعوم")
                
                # تحويل إلى تنسيق Y-m-d للحفظ
                formatted_date = f"{year.strip()}-{month.strip().zfill(2)}-{day.strip().zfill(2)} 00:00:00"
                
                # التحقق من صحة التاريخ
                datetime.strptime(formatted_date, "%Y-%m-%d %H:%M:%S")
                
            except Exception as e:
                QMessageBox.warning(self, "تحذير", "يرجى إدخال تاريخ صحيح (dd/mm/yyyy أو dd-mm-yyyy)")
                return
        else:
            # إذا لم يتم إدخال تاريخ، استخدام التاريخ الحالي
            formatted_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # ✅ تجميع البيانات المحدثة
        self.updated_data = {
            'name': name,
            'phone': phone,
            'address': address or 'غير محدد',
            'date_added': formatted_date
        }
        
        self.accept()
    
    def get_updated_data(self):
        return self.updated_data