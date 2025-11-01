import os
import json
import sqlite3
import uuid
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
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
from PySide6.QtGui import QPixmap, QFont, QColor, QIntValidator, QDoubleValidator, QIcon, QPainter

DB_PATH = "chbib_materials.db"

class DateInput(QLineEdit):
    """✅ حقل إدخال التاريخ مع التحديث التلقائي والتحقق من الصحة"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        """إعداد واجهة حقل التاريخ"""
        self.setPlaceholderText("ابحث عن تاريخ")
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
        date_text = date_text.replace('/', '-')
        
        # ✅ التحقق من تنسيق التاريخ (dd-mm-yyyy)
        try:
            parts = date_text.split('-')
            if len(parts) != 3:
                self.setStyleSheet(self.styleSheet() + "border: 2px solid #e74c3c;")
                return False
            
            day, month, year = parts  # ✅ تغيير الترتيب ليكون يوم-شهر-سنة
            if len(day) not in [1, 2] or not day.isdigit():
                self.setStyleSheet(self.styleSheet() + "border: 2px solid #e74c3c;")
                return False
            
            if len(month) not in [1, 2] or not month.isdigit():
                self.setStyleSheet(self.styleSheet() + "border: 2px solid #e74c3c;")
                return False
            
            if len(year) != 4 or not year.isdigit():
                self.setStyleSheet(self.styleSheet() + "border: 2px solid #e74c3c;")
                return False
            
            day_int = int(day)
            month_int = int(month)
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
            return True
            
        except:
            self.setStyleSheet(self.styleSheet() + "border: 2px solid #e74c3c;")
            return False
    
    def get_date(self):
        """✅ الحصول على التاريخ كسلسلة نصية"""
        if self.validate_date():
            return self.text().strip()
        return None
    
    def get_date_for_search(self):
        """✅ الحصول على التاريخ بصيغة YYYY-MM-DD للبحث"""
        if self.validate_date():
            date_text = self.text().strip().replace('/', '-')
            parts = date_text.split('-')
            if len(parts) == 3:
                day, month, year = parts
                return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
        return None
    
    def set_date(self, date_str):
        """✅ تعيين تاريخ معين"""
        if date_str:
            # ✅ تحويل أي تنسيق إلى تنسيق يوم-شهر-سنة
            try:
                if '-' in date_str:
                    parts = date_str.split('-')
                    if len(parts) == 3:
                        if len(parts[0]) == 4:  # إذا كان التنسيق YYYY-MM-DD
                            year, month, day = parts
                            self.setText(f"{day}-{month}-{year}")
                        else:  # إذا كان التنسيق DD-MM-YYYY
                            self.setText(date_str)
            except:
                self.set_date_to_today()
        else:
            self.set_date_to_today()

class AddPaymentDialog(QDialog):
    """نافذة إضافة دفعة جديدة"""
    def __init__(self, parent, customer_id, customer_name, phone_number, exchange_rate):
        super().__init__(parent)
        self.customer_id = customer_id
        self.customer_name = customer_name
        self.phone_number = phone_number
        self.exchange_rate = exchange_rate
        self.invoices = self.load_customer_invoices()
        self.setup_ui()
        
    def load_customer_invoices(self):
        """✅ تحميل فواتير الزبون من قاعدة البيانات"""
        try:
            with open("data/customers.json", 'r', encoding='utf-8') as f:
                customers = json.load(f)
            
            for customer in customers:
                if (customer.get('name') == self.customer_name and 
                    customer.get('phone') == self.phone_number):
                    invoices = customer.get('invoices', [])
                    # ✅ إضافة UUID للفواتير القديمة التي لا تمتلكه
                    for invoice in invoices:
                        if 'invoice_uuid' not in invoice:
                            invoice['invoice_uuid'] = str(uuid.uuid4())
                    return invoices
            
            return []
        except Exception as e:
            print(f"❌ خطأ في تحميل فواتير الزبون: {e}")
            return []
    
    def setup_ui(self):
        self.setWindowTitle("إضافة دفعة جديدة")
        # ✅ تكبير النافذة إلى حجم متوسط
        self.setFixedSize(600, 500)
        
        # ✅ خلفية كحلية داكنة مع خطوط بيضاء وسميكة
        self.setStyleSheet("""
            QDialog {
                background-color: #1e2a3a;
            }
            QLabel {
                color: white;
                font-family: Arial;
                font-weight: bold;
                font-size: 16px;
            }
            QGroupBox {
                color: white;
                font-family: Arial;
                font-weight: bold;
                font-size: 16px;
            }
            QGroupBox::title {
                color: white;
                font-size: 16px;
                font-weight: bold;
            }
        """)
        
        layout = QVBoxLayout(self)
        
        # معلومات الزبون
        customer_group = QGroupBox("معلومات الزبون")
        customer_layout = QFormLayout()
        
        customer_name_label = QLabel(self.customer_name)
        customer_phone_label = QLabel(self.phone_number)
        
        customer_name_label.setStyleSheet("color: white; font-size: 16px; font-weight: bold;")
        customer_phone_label.setStyleSheet("color: white; font-size: 16px; font-weight: bold;")
        
        customer_layout.addRow("اسم الزبون:", customer_name_label)
        customer_layout.addRow("رقم الهاتف:", customer_phone_label)
        
        customer_group.setLayout(customer_layout)
        layout.addWidget(customer_group)
        
        # بيانات الدفعة
        form_layout = QFormLayout()
        
        # اختيار الفاتورة
        self.invoice_combo = QComboBox()
        self.invoice_combo.setStyleSheet("""
            QComboBox {
                background-color: white; 
                color: black; 
                padding: 12px; 
                border-radius: 5px;
                font-size: 16px;
                border: 1px solid #bdc3c7;
                font-family: Arial;
                font-weight: bold;
                min-height: 40px;
            }
            QComboBox:focus {
                border: 2px solid #3498db;
                background-color: #f8f9fa;
            }
            QComboBox QAbstractItemView {
                background-color: white;
                color: black;
                font-size: 16px;
                font-weight: bold;
                selection-background-color: #3498db;
                selection-color: white;
            }
        """)
        self.load_invoices_to_combo()
        self.invoice_combo.currentIndexChanged.connect(self.on_invoice_changed)
        
        # مبلغ الدفعة
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
                min-height: 40px;
            }
            QLineEdit:focus {
                border: 2px solid #3498db;
                background-color: #f8f9fa;
            }
        """)
        amount_validator = QDoubleValidator(0, 1000000, 2, self)
        self.payment_amount.setValidator(amount_validator)
        
        # تاريخ الدفعة
        self.payment_date = DateInput()
        
        form_layout.addRow("الفاتورة:", self.invoice_combo)
        form_layout.addRow("مبلغ الدفعة ($):", self.payment_amount)
        form_layout.addRow("تاريخ الدفعة:", self.payment_date)
        
        layout.addLayout(form_layout)
        
        # معلومات الفاتورة المحددة
        self.invoice_info_group = QGroupBox("معلومات الفاتورة المحددة")
        self.invoice_info_group.setStyleSheet("""
            QGroupBox {
                color: white;
                font-weight: bold;
                font-family: Arial;
                border: 1px solid #bdc3c7;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
                font-size: 16px;
            }
        """)
        self.invoice_info_layout = QVBoxLayout()
        
        self.invoice_number_label = QLabel("")
        self.total_amount_label = QLabel("")
        self.paid_amount_label = QLabel("")
        self.remaining_amount_label = QLabel("")
        
        # ✅ تكبير الخطوط في معلومات الفاتورة
        for label in [self.invoice_number_label, self.total_amount_label, 
                     self.paid_amount_label, self.remaining_amount_label]:
            label.setStyleSheet("color: white; font-size: 16px; font-weight: bold;")
        
        self.invoice_info_layout.addWidget(self.invoice_number_label)
        self.invoice_info_layout.addWidget(self.total_amount_label)
        self.invoice_info_layout.addWidget(self.paid_amount_label)
        self.invoice_info_layout.addWidget(self.remaining_amount_label)
        
        self.invoice_info_group.setLayout(self.invoice_info_layout)
        layout.addWidget(self.invoice_info_group)
        
        # تحديث معلومات الفاتورة الأولى
        if self.invoices:
            self.update_invoice_info(0)
        
        # أزرار
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.validate_and_accept)
        buttons.rejected.connect(self.reject)
        
        buttons.setStyleSheet("""
            QPushButton {
                padding: 12px 25px;
                border: none;
                border-radius: 5px;
                font-size: 16px;
                font-weight: bold;
                font-family: Arial;
                min-width: 100px;
                min-height: 40px;
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
    
    def load_invoices_to_combo(self):
        """✅ تحميل الفواتير في القائمة المنسدلة"""
        self.invoice_combo.clear()
        
        for invoice in self.invoices:
            if invoice.get('type') == 'تقسيط':  # فقط فواتير التقسيط
                # ✅ ✅ ✅ التصحيح: استخدام رقم العرض الحقيقي بدلاً من invoice_number
                display_number = self.get_invoice_display_number(invoice.get('invoice_uuid'))
                invoice_text = f"فاتورة #{display_number} - {invoice.get('total_usd', 0):.2f} $"
                self.invoice_combo.addItem(invoice_text, invoice)
        
        if self.invoice_combo.count() == 0:
            self.invoice_combo.addItem("لا توجد فواتير تقسيط", None)
    
    def get_invoice_display_number(self, invoice_uuid):
        """✅ الحصول على رقم العرض الحقيقي للفاتورة من خلال UUID"""
        try:
            with open("data/customers.json", 'r', encoding='utf-8') as f:
                customers = json.load(f)
        
            for customer in customers:
                if (customer.get('name') == self.customer_name and 
                    customer.get('phone') == self.phone_number):
                
                    invoices = customer.get('invoices', [])
                    for index, invoice in enumerate(invoices):
                        if invoice.get('invoice_uuid') == invoice_uuid:
                            # ✅ الرقم الحقيقي هو index + 1 (نفس آلية صفحة الفواتير)
                            return str(index + 1)
        
            return "غير معروف"
        except Exception as e:
            print(f"❌ خطأ في الحصول على رقم العرض: {e}")
            return "غير معروف"
    
    def on_invoice_changed(self, index):
        """✅ عند تغيير الفاتورة المحددة"""
        if index >= 0:
            self.update_invoice_info(index)
    
    def update_invoice_info(self, index):
        """✅ تحديث معلومات الفاتورة المحددة"""
        invoice_data = self.invoice_combo.itemData(index)
        if invoice_data:
            # ✅ ✅ ✅ التصحيح: استخدام رقم العرض الحقيقي
            display_number = self.get_invoice_display_number(invoice_data.get('invoice_uuid'))
            total_amount = invoice_data.get('total_usd', 0)
            paid_amount = invoice_data.get('paid_amount', 0)
            remaining_amount = invoice_data.get('remaining_amount', 0)
            
            self.invoice_number_label.setText(f"رقم الفاتورة: {display_number}")
            self.total_amount_label.setText(f"المبلغ الإجمالي: {total_amount:.2f} $")
            self.paid_amount_label.setText(f"المبلغ المدفوع: {paid_amount:.2f} $")
            self.remaining_amount_label.setText(f"المبلغ المتبقي: {remaining_amount:.2f} $")
            
            # ✅ تخزين المبلغ المتبقي للتحقق منه
            self.max_payment_amount = remaining_amount
        else:
            self.invoice_number_label.setText("")
            self.total_amount_label.setText("")
            self.paid_amount_label.setText("")
            self.remaining_amount_label.setText("")
            self.max_payment_amount = 0
    
    def validate_and_accept(self):
        """✅ التحقق من صحة البيانات قبل القبول"""
        try:
            # التحقق من اختيار فاتورة
            current_index = self.invoice_combo.currentIndex()
            if current_index < 0:
                self.show_message("تحذير", "يرجى اختيار فاتورة", "warning")
                return
            
            invoice_data = self.invoice_combo.itemData(current_index)
            if not invoice_data:
                self.show_message("تحذير", "يرجى اختيار فاتورة صحيحة", "warning")
                return
            
            # التحقق من مبلغ الدفعة
            amount_text = self.payment_amount.text().strip()
            if not amount_text:
                self.show_message("تحذير", "يرجى إدخال مبلغ الدفعة", "warning")
                return
            
            # ✅ ✅ ✅ التصحيح: استخدام Decimal للتعامل مع الأرقام العشرية بدقة
            try:
                amount = Decimal(amount_text)
                amount = amount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            except:
                self.show_message("تحذير", "يرجى إدخال مبلغ صحيح", "warning")
                return
            
            if amount <= 0:
                self.show_message("تحذير", "يرجى إدخال مبلغ صحيح", "warning")
                return
            
            # ✅ ✅ ✅ التصحيح: السماح بدفع المبلغ المتبقي بالضبط
            if amount > Decimal(str(self.max_payment_amount)):
                self.show_message("تحذير", f"لا يمكن دفع مبلغ أكبر من المبلغ المتبقي ({self.max_payment_amount:.2f} $)", "warning")
                return
            
            # التحقق من صحة التاريخ
            if not self.payment_date.validate_date():
                self.show_message("تحذير", "يرجى إدخال تاريخ صحيح (dd-mm-yyyy أو dd/mm/yyyy)", "warning")
                return
            
            self.accept()
            
        except ValueError:
            self.show_message("تحذير", "يرجى إدخال مبلغ صحيح", "warning")
    
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
    
    def get_payment_data(self):
        """✅ الحصول على بيانات الدفعة"""
        current_index = self.invoice_combo.currentIndex()
        invoice_data = self.invoice_combo.itemData(current_index)
        
        return {
            'invoice_data': invoice_data,
            'amount': float(self.payment_amount.text()),
            'date': self.payment_date.get_date(),
            'invoice_number': invoice_data.get('invoice_number', ''),
            'invoice_uuid': invoice_data.get('invoice_uuid', '')  # ✅ إضافة UUID
        }

class CustomerPaymentsPage(QWidget):
    def __init__(self, parent, customer_id, customer_name, phone_number):
        super().__init__()
        self.parent = parent
        self.customer_id = customer_id
        self.customer_name = customer_name
        self.phone_number = phone_number
        self.exchange_rate = self.load_exchange_rate()
        
        # ✅ إضافة متغيرات لتتبع حالة البحث
        self.is_searching = False
        self.current_search_date = ""
        self.current_search_invoice = ""
        
        # ✅ إضافة مؤقت للتحديث التلقائي (تم إيقافه أثناء البحث)
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self.load_payments_data)
        self.refresh_timer.start(3000)  # تحديث كل 3 ثواني
        
        # ✅ ضبط حجم النافذة
        screen = self.screen()
        screen_size = screen.availableSize()
        self.setMinimumSize(int(screen_size.width() * 0.5), int(screen_size.height() * 0.5))  # ✅ تصغير 50%
        self.resize(int(screen_size.width() * 0.7), int(screen_size.height() * 0.7))
        
        # ✅ تمكين أزرار الإغلاق والتصغير في الشريط العلوي
        self.setWindowFlags(Qt.Window | Qt.WindowMinimizeButtonHint | Qt.WindowMaximizeButtonHint | Qt.WindowCloseButtonHint)
        
        self.setup_ui()
        self.load_payments_data()
        
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
        """إنشاء واجهة صفحة دفعات الزبون"""
        self.setWindowTitle(f"دفعات الزبون - {self.customer_name}")
        
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

        # ✅ الهيدر
        header_layout = QHBoxLayout()
        
        # إضافة شعار المؤسسة
        logo_path = r"C:\Users\User\Desktop\chbib1\icons\logo_invoices.png"
        if os.path.exists(logo_path):
            logo_label = QLabel()
            pixmap = QPixmap(logo_path)
            scaled_pixmap = pixmap.scaled(120, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            logo_label.setPixmap(scaled_pixmap)
            logo_label.setStyleSheet("background-color: transparent;")
            header_layout.addWidget(logo_label)
        
        # عنوان الصفحة
        title = QLabel(f"دفعات الزبون: {self.customer_name}")
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
        
        header_layout.addStretch()
        
        header_layout.addWidget(title)
        
        # ❌ تم إزالة زر حفظ من أعلى الصفحة (سيتم وضعه في الأسفل)
        
        main_layout.addLayout(header_layout)

        # قسم محرك البحث
        search_group = QGroupBox("محرك البحث")
        search_group.setStyleSheet("""
            QGroupBox {
                color: white;
                font-size: 16px;
                font-weight: bold;
                border: 2px solid #3498db;
                border-radius: 8px;
                padding: 12px;
                margin-top: 10px;
                background-color: rgba(30, 42, 58, 0.9);
                font-family: Arial;
            }
        """)
        
        search_layout = QHBoxLayout()
        
        # بحث برقم الفاتورة
        self.invoice_search = QLineEdit()
        self.invoice_search.setPlaceholderText("ابحث عن فاتورة")
        self.invoice_search.setStyleSheet("""
            QLineEdit {
                padding: 12px;
                border: 2px solid #bdc3c7;
                border-radius: 5px;
                font-size: 16px;
                background-color: white;
                color: black;
                font-family: Arial;
                font-weight: bold;
                min-height: 40px;
            }
            QLineEdit:focus {
                border: 2px solid #3498db;
                background-color: #f8f9fa;
            }
        """)
        self.invoice_search.textChanged.connect(self.search_payments)
        
        # بحث بالتاريخ
        self.date_search = DateInput()
        self.date_search.textChanged.connect(self.search_payments)
        
        search_layout.addStretch()
        search_layout.addWidget(self.invoice_search)
        search_layout.addWidget(QLabel(""))
        search_layout.addWidget(self.date_search)
        search_layout.addWidget(QLabel("بحث بالتاريخ:"))
        
        search_group.setLayout(search_layout)
        main_layout.addWidget(search_group)

        # قسم الإحصائيات
        self.setup_stats_section()
        main_layout.addLayout(self.stats_layout)

        # جدول الدفعات
        self.setup_payments_table()
        main_layout.addWidget(self.payments_table)

        # ✅ أزرار التحكم - تم نقل زر حفظ إلى هنا بجانب زر الحذف
        buttons_layout = QHBoxLayout()
        
        self.delete_payment_btn = QPushButton("🗑️ حذف الدفعة المحددة")
        self.delete_payment_btn.setStyleSheet("""
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
        self.delete_payment_btn.clicked.connect(self.delete_selected_payment)
        
        # ✅ زر حفظ تم نقله إلى هنا بجانب زر الحذف
        self.save_word_btn = QPushButton("💾 حفظ ")
        self.save_word_btn.setStyleSheet("""
            QPushButton {
                background-color: #185abd;
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
                background-color: #164a9d;
            }
        """)
        self.save_word_btn.clicked.connect(self.export_to_word)
        
        buttons_layout.addWidget(self.delete_payment_btn)
        buttons_layout.addWidget(self.save_word_btn)
        buttons_layout.addStretch()
        
        main_layout.addLayout(buttons_layout)

    def setup_stats_section(self):
        """إنشاء قسم الإحصائيات"""
        self.stats_layout = QHBoxLayout()
        
        # ✅ عدد الدفعات - تم تعديل التنسيق ليكون من الجهة اليمنى
        self.payments_count_group = QGroupBox()
        self.payments_count_group.setStyleSheet("""
            QGroupBox {
                color: white;
                font-size: 16px;
                font-weight: bold;
                border: 2px solid #27ae60;
                border-radius: 8px;
                background-color: rgba(39, 174, 96, 0.3);
                padding: 10px;
                min-width: 200px;
                font-family: Arial;
            }
        """)
        
        count_layout = QHBoxLayout()
        
        self.payments_count_label = QLabel("0")
        self.payments_count_label.setStyleSheet("""
            QLabel {
                color: white; 
                font-weight: bold; 
                font-size: 18px; 
                background-color: transparent; 
                padding: 5px; 
                border-radius: 4px;
                font-family: Arial;
            }
        """)
        
        count_label = QLabel("عدد الدفعات:")
        count_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 18px;
                font-weight: bold;
                font-family: Arial;
                background-color: transparent;
            }
        """)
        
        # ✅ تعديل الترتيب: الكلمة أولاً ثم الرقم
        count_layout.addStretch()
        count_layout.addWidget(self.payments_count_label)
        count_layout.addWidget(count_label)
        
        self.payments_count_group.setLayout(count_layout)
        
        # ✅ إجمالي المدفوعات - تم تعديل التنسيق ليكون من الجهة اليمنى
        self.total_payments_group = QGroupBox()
        self.total_payments_group.setStyleSheet("""
            QGroupBox {
                color: white;
                font-size: 16px;
                font-weight: bold;
                border: 2px solid #3498db;
                border-radius: 8px;
                background-color: rgba(52, 152, 219, 0.3);
                padding: 10px;
                min-width: 300px;
                font-family: Arial;
            }
        """)
        
        total_layout = QHBoxLayout()
        
        self.total_lbp_label = QLabel("0 LBP")
        self.total_lbp_label.setStyleSheet("""
            QLabel {
                color: white; 
                font-weight: bold; 
                font-size: 18px; 
                background-color: transparent; 
                padding: 5px; 
                border-radius: 4px;
                font-family: Arial;
            }
        """)
        
        total_layout.addWidget(QLabel("|"))
        
        self.total_usd_label = QLabel("0 $")
        self.total_usd_label.setStyleSheet("""
            QLabel {
                color: white; 
                font-weight: bold; 
                font-size: 18px; 
                background-color: transparent; 
                padding: 5px; 
                border-radius: 4px;
                font-family: Arial;
            }
        """)
        
        total_label = QLabel("إجمالي المدفوعات:")
        total_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 18px;
                font-weight: bold;
                font-family: Arial;
                background-color: transparent;
            }
        """)
        
        # ✅ تعديل الترتيب: الكلمة أولاً ثم الأرقام
        total_layout.addStretch()
        total_layout.addWidget(self.total_lbp_label)
        total_layout.addWidget(QLabel("|"))
        total_layout.addWidget(self.total_usd_label)
        total_layout.addWidget(total_label)
        
        self.total_payments_group.setLayout(total_layout)
        
        # ✅ إضافة المجموعات مع ضبط المحاذاة لليمين
        self.stats_layout.addWidget(self.payments_count_group)
        self.stats_layout.addWidget(self.total_payments_group)
        self.stats_layout.addStretch()

    def setup_payments_table(self):
        """إنشاء جدول الدفعات"""
        self.payments_table = QTableWidget()
        self.payments_table.setColumnCount(5)  # ✅ تم تقليل الأعمدة من 6 إلى 5 بعد حذف خانة الوقت
        self.payments_table.setHorizontalHeaderLabels([
            "رقم", "رقم الفاتورة", "المبلغ ($)", "المبلغ (LBP)", "التاريخ"
        ])
        
        self.payments_table.setStyleSheet("""
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
        
        self.payments_table.setFocusPolicy(Qt.NoFocus)
        self.payments_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.payments_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.payments_table.setEditTriggers(QTableWidget.NoEditTriggers)
        
        # ✅ ضبط اتجاه الجدول من اليمين لليسار
        self.payments_table.setLayoutDirection(Qt.RightToLeft)

    def get_invoice_number_by_uuid(self, invoice_uuid):
        """✅ الحصول على رقم الفاتورة الحقيقي من خلال UUID"""
        try:
            with open("data/customers.json", 'r', encoding='utf-8') as f:
                customers = json.load(f)
            
            for customer in customers:
                if (customer.get('name') == self.customer_name and 
                    customer.get('phone') == self.phone_number):
                    
                    invoices = customer.get('invoices', [])
                    for invoice in invoices:
                        if invoice.get('invoice_uuid') == invoice_uuid:
                            return invoice.get('invoice_number', '')
            
            return "غير معروف"
        except Exception as e:
            print(f"❌ خطأ في الحصول على رقم الفاتورة: {e}")
            return "غير معروف"
            
    def get_invoice_display_number(self, invoice_uuid):
        """✅ الحصول على رقم العرض الحقيقي للفاتورة من خلال UUID"""
        try:
            with open("data/customers.json", 'r', encoding='utf-8') as f:
                customers = json.load(f)
        
            for customer in customers:
                if (customer.get('name') == self.customer_name and 
                    customer.get('phone') == self.phone_number):
                
                    invoices = customer.get('invoices', [])
                    for index, invoice in enumerate(invoices):
                        if invoice.get('invoice_uuid') == invoice_uuid:
                            # ✅ الرقم الحقيقي هو index + 1 (نفس آلية صفحة الفواتير)
                            return str(index + 1)
        
            return "غير معروف"
        except Exception as e:
            print(f"❌ خطأ في الحصول على رقم العرض: {e}")
            return "غير معروف"        

    def find_invoice_uuid(self, invoice_number):
        """✅ البحث عن UUID الفاتورة من ملف customers.json"""
        try:
            with open("data/customers.json", 'r', encoding='utf-8') as f:
                customers = json.load(f)
            
            for customer in customers:
                if (customer.get('name') == self.customer_name and 
                    customer.get('phone') == self.phone_number):
                    for invoice in customer.get('invoices', []):
                        if invoice.get('invoice_number') == invoice_number:
                            return invoice.get('invoice_uuid')
            return None
        except Exception as e:
            print(f"❌ خطأ في البحث عن UUID: {e}")
            return None

    def load_payments_data(self):
        """تحميل بيانات الدفعات"""
        # ✅ إذا كان البحث نشطاً، لا نقوم بالتحديث التلقائي
        if self.is_searching:
            return
            
        try:
            payments_file = "data/customer_payments.json"
            if not os.path.exists(payments_file):
                self.payments = []
                self.update_stats()
                return
            
            with open(payments_file, 'r', encoding='utf-8') as f:
                all_payments = json.load(f)
            
            # ✅ تصفية الدفعات الخاصة بالزبون الحالي فقط
            self.payments = [
                payment for payment in all_payments 
                if (payment.get('customer_id') == self.customer_id and
                    payment.get('customer_phone') == self.phone_number)
            ]

            # ✅ ✅ ✅ إضافة UUID للدفعات القديمة التي ما عندها UUID
            payments_updated = False
            for payment in self.payments:
                if 'invoice_uuid' not in payment:
                    invoice_uuid = self.find_invoice_uuid(payment.get('invoice_number'))
                    if invoice_uuid:
                        payment['invoice_uuid'] = invoice_uuid
                        payments_updated = True
                        print(f"✅ تم إضافة UUID للدفعة القديمة: {payment['invoice_number']}")

            # ✅ حفظ التعديلات إذا تم تحديث الدفعات
            if payments_updated:
                try:
                    # تحديث جميع الدفعات في الملف
                    for updated_payment in all_payments:
                        if 'invoice_uuid' not in updated_payment:
                            invoice_uuid = self.find_invoice_uuid(updated_payment.get('invoice_number'))
                            if invoice_uuid:
                                updated_payment['invoice_uuid'] = invoice_uuid
                    
                    with open(payments_file, 'w', encoding='utf-8') as f:
                        json.dump(all_payments, f, ensure_ascii=False, indent=2)
                    print("✅ تم حفظ التعديلات في customer_payments.json")
                except Exception as e:
                    print(f"❌ خطأ في حفظ التعديلات: {e}")

            self.load_payments_table()
            self.update_stats()
            
        except Exception as e:
            print(f"❌ خطأ في تحميل بيانات الدفعات: {e}")
            self.payments = []
            self.update_stats()

    def load_payments_table(self):
        """تحميل الدفعات في الجدول"""
        self.payments_table.setRowCount(len(self.payments))
        
        for row, payment in enumerate(self.payments):
            # ✅ رقم الدفعة (الترتيب التلقائي)
            number_item = QTableWidgetItem(str(row + 1))
            number_item.setBackground(QColor("white"))
            number_item.setTextAlignment(Qt.AlignCenter)
            self.payments_table.setItem(row, 0, number_item)
            
            # ✅ ✅ ✅ التصحيح: الحصول على رقم الفاتورة الحقيقي من خلال UUID
            # ✅ ✅ ✅ التصحيح النهائي: استخدام رقم العرض الحقيقي (نفس صفحة الفواتير)
            display_number = self.get_invoice_display_number(payment.get('invoice_uuid'))
            invoice_item = QTableWidgetItem(display_number)
            invoice_item.setBackground(QColor("white"))
            invoice_item.setTextAlignment(Qt.AlignCenter)
            self.payments_table.setItem(row, 1, invoice_item)
            
            # ✅ المبلغ بالدولار
            amount_usd = payment.get('amount', 0)
            usd_text = f"{int(amount_usd)} $" if amount_usd == int(amount_usd) else f"{amount_usd:.2f} $"
            usd_item = QTableWidgetItem(usd_text)
            usd_item.setBackground(QColor("white"))
            usd_item.setTextAlignment(Qt.AlignCenter)
            self.payments_table.setItem(row, 2, usd_item)
            
            # ✅ المبلغ بالليرة
            amount_lbp = payment.get('amount_lbp', 0)
            lbp_text = f"{int(amount_lbp):,} LBP"
            lbp_item = QTableWidgetItem(lbp_text)
            lbp_item.setBackground(QColor("white"))
            lbp_item.setTextAlignment(Qt.AlignCenter)
            self.payments_table.setItem(row, 3, lbp_item)
            
            # ✅ التاريخ فقط (تم حذف الوقت)
            date_item = QTableWidgetItem(payment.get('date', ''))
            date_item.setBackground(QColor("white"))
            date_item.setTextAlignment(Qt.AlignCenter)
            self.payments_table.setItem(row, 4, date_item)

    def update_stats(self):
        """تحديث الإحصائيات"""
        total_usd = sum(payment.get('amount', 0) for payment in self.payments)
        total_lbp = sum(payment.get('amount_lbp', 0) for payment in self.payments)
        payments_count = len(self.payments)
        
        # ✅ تنسيق الأرقام
        total_usd_text = f"{int(total_usd)} $" if total_usd == int(total_usd) else f"{total_usd:.2f} $"
        total_lbp_text = f"{int(total_lbp):,} LBP"
        
        self.total_usd_label.setText(total_usd_text)
        self.total_lbp_label.setText(total_lbp_text)
        self.payments_count_label.setText(str(payments_count))

    def search_payments(self):
        """بحث في الدفعات"""
        invoice_text = self.invoice_search.text().strip()
        date_text = self.date_search.text().strip()
        
        # ✅ تحديد حالة البحث
        self.is_searching = bool(invoice_text or date_text)
        self.current_search_invoice = invoice_text
        self.current_search_date = date_text
        
        # ✅ إذا لم يكن هناك بحث، عرض كل الدفعات
        if not self.is_searching:
            self.load_payments_table()
            self.update_stats()
            return
        
        # ✅ البحث بالتاريخ (بدون تحويل إلى YYYY-MM-DD)
        filtered_payments = []
        
        for payment in self.payments:
            match = True
            
            # ✅ البحث برقم الفاتورة الحقيقي من خلال UUID
            if invoice_text:
                display_number = self.get_invoice_display_number(payment.get('invoice_uuid'))
                if invoice_text not in str(display_number).lower():
                    match = False
            
            # ✅ البحث بالتاريخ (مقارنة مباشرة بالنص المدخل)
            if date_text and match:
                payment_date = payment.get('date', '')
                # ✅ البحث التدريجي: إذا كتب "12" يظهر كل التواريخ التي تحتوي على 12
                if date_text not in payment_date:
                    match = False
            
            if match:
                filtered_payments.append(payment)
        
        # ✅ تحميل الدفعات المفلترة في الجدول
        self.payments_table.setRowCount(len(filtered_payments))
        
        for row, payment in enumerate(filtered_payments):
            number_item = QTableWidgetItem(str(row + 1))
            number_item.setBackground(QColor("white"))
            number_item.setTextAlignment(Qt.AlignCenter)
            self.payments_table.setItem(row, 0, number_item)
            
            # ✅ ✅ ✅ استخدام رقم الفاتورة الحقيقي
            display_number = self.get_invoice_display_number(payment.get('invoice_uuid'))
            invoice_item = QTableWidgetItem(str(display_number))
            invoice_item.setBackground(QColor("white"))
            invoice_item.setTextAlignment(Qt.AlignCenter)
            self.payments_table.setItem(row, 1, invoice_item)
            
            amount_usd = payment.get('amount', 0)
            usd_text = f"{int(amount_usd)} $" if amount_usd == int(amount_usd) else f"{amount_usd:.2f} $"
            usd_item = QTableWidgetItem(usd_text)
            usd_item.setBackground(QColor("white"))
            usd_item.setTextAlignment(Qt.AlignCenter)
            self.payments_table.setItem(row, 2, usd_item)
            
            amount_lbp = payment.get('amount_lbp', 0)
            lbp_text = f"{int(amount_lbp):,} LBP"
            lbp_item = QTableWidgetItem(lbp_text)
            lbp_item.setBackground(QColor("white"))
            lbp_item.setTextAlignment(Qt.AlignCenter)
            self.payments_table.setItem(row, 3, lbp_item)
            
            date_item = QTableWidgetItem(payment.get('date', ''))
            date_item.setBackground(QColor("white"))
            date_item.setTextAlignment(Qt.AlignCenter)
            self.payments_table.setItem(row, 4, date_item)
        
        # ✅ تحديث الإحصائيات للنتائج المفلترة
        total_usd = sum(payment.get('amount', 0) for payment in filtered_payments)
        total_lbp = sum(payment.get('amount_lbp', 0) for payment in filtered_payments)
        payments_count = len(filtered_payments)
        
        total_usd_text = f"{int(total_usd)} $" if total_usd == int(total_usd) else f"{total_usd:.2f} $"
        total_lbp_text = f"{int(total_lbp):,} LBP"
        
        self.total_usd_label.setText(total_usd_text)
        self.total_lbp_label.setText(total_lbp_text)
        self.payments_count_label.setText(str(payments_count))

    def add_new_payment(self):
        """✅ إضافة دفعة جديدة"""
        try:
            payment_dialog = AddPaymentDialog(self, self.customer_id, self.customer_name, self.phone_number, self.exchange_rate)
            
            if payment_dialog.exec() == QDialog.Accepted:
                payment_data = payment_dialog.get_payment_data()
                self.save_payment(payment_data)
                
        except Exception as e:
            self.show_message("خطأ", f"حدث خطأ في إضافة الدفعة: {e}", "error")

    def save_payment(self, payment_data):
        """✅ حفظ الدفعة في قاعدة البيانات"""
        try:
            print(f"💾 بدء حفظ الدفعة للفاتورة: {payment_data['invoice_number']}")
            
            # 1. حفظ الدفعة في ملف customer_payments.json
            payments_file = "data/customer_payments.json"
            payments = []
            
            if os.path.exists(payments_file):
                with open(payments_file, 'r', encoding='utf-8') as f:
                    payments = json.load(f)
            
            # ✅ استخدام UUID بدلاً من رقم الفاتورة
            invoice_uuid = payment_data.get('invoice_uuid', '')
            payment_id = f"{self.customer_id}_{invoice_uuid}_{payment_data['date']}_{payment_data['amount']}"
            
            # ✅ التحقق من عدم تكرار الدفعة
            payment_exists = False
            for payment in payments:
                if (payment.get('customer_id') == self.customer_id and
                    payment.get('invoice_uuid') == invoice_uuid and
                    payment.get('amount') == payment_data['amount'] and
                    payment.get('date') == payment_data['date']):
                    payment_exists = True
                    break
            
            if payment_exists:
                print("⚠️ الدفعة موجودة مسبقاً")
                self.show_message("تحذير", "هذه الدفعة موجودة مسبقاً", "warning")
                return
            
            # ✅ إضافة الدفعة الجديدة
            new_payment = {
                'id': len(payments) + 1,
                'payment_id': payment_id,
                'customer_id': self.customer_id,
                'customer_name': self.customer_name,
                'customer_phone': self.phone_number,
                'invoice_number': payment_data['invoice_number'],
                'invoice_uuid': invoice_uuid,  # ✅ إضافة UUID للفاتورة
                'payment_uuid': str(uuid.uuid4()),  # ✅ إضافة UUID للدفعة
                'amount': payment_data['amount'],
                'date': payment_data['date'],
                'time': datetime.now().strftime('%H:%M:%S'),
                'timestamp': datetime.now().isoformat(),
                'exchange_rate': self.exchange_rate,
                'amount_lbp': payment_data['amount'] * self.exchange_rate,
                'type': 'دفعة فاتورة تقسيط'
            }
            
            payments.append(new_payment)
            
            with open(payments_file, 'w', encoding='utf-8') as f:
                json.dump(payments, f, ensure_ascii=False, indent=2)
            
            # 2. تحديث الفاتورة في ملف customers.json
            self.update_invoice_payment(payment_data)
            
            # ✅ إعادة تحميل البيانات
            self.load_payments_data()
            
            self.show_message("نجاح", "✅ تم حفظ الدفعة بنجاح", "info")
            
        except Exception as e:
            print(f"❌ خطأ في حفظ الدفعة: {e}")
            self.show_message("خطأ", f"حدث خطأ في حفظ الدفعة: {e}", "error")

    def update_invoice_payment(self, payment_data):
        """✅ تحديث الفاتورة بإضافة الدفعة"""
        try:
            with open("data/customers.json", 'r', encoding='utf-8') as f:
                customers = json.load(f)
            
            for customer in customers:
                if (customer.get('name') == self.customer_name and 
                    customer.get('phone') == self.phone_number):
                    
                    invoices = customer.get('invoices', [])
                    for invoice in invoices:
                        # ✅ البحث باستخدام UUID فقط
                        if invoice.get('invoice_uuid') == payment_data.get('invoice_uuid'):
                            # ✅ إضافة الدفعة للفاتورة
                            if 'payments' not in invoice:
                                invoice['payments'] = []
                            
                            # ✅ منع التكرار
                            payment_exists = False
                            for existing_payment in invoice['payments']:
                                if (existing_payment.get('amount') == payment_data['amount'] and
                                    existing_payment.get('date') == payment_data['date']):
                                    payment_exists = True
                                    break
                            
                            if not payment_exists:
                                invoice_payment = {
                                    'amount': payment_data['amount'],
                                    'date': payment_data['date'],
                                    'invoice_number': payment_data['invoice_number'],
                                    'invoice_uuid': payment_data['invoice_uuid']  # ✅ إضافة UUID
                                }
                                invoice['payments'].append(invoice_payment)
                                
                                # ✅ تحديث المبالغ المدفوعة والمتبقية
                                payment_amount = payment_data['amount']
                                invoice['paid_amount'] = invoice.get('paid_amount', 0) + payment_amount
                                invoice['remaining_amount'] = invoice.get('remaining_amount', 0) - payment_amount
                                
                                # ✅ ✅ ✅ التصحيح: التحقق من اكتمال الفاتورة
                                total_amount = invoice.get('total_usd', 0)
                                new_paid_amount = invoice.get('paid_amount', 0)
                                
                                # ✅ ✅ ✅ استخدام مقارنة دقيقة مع Decimal
                                if abs(new_paid_amount - total_amount) < 0.01 or new_paid_amount >= total_amount:
                                    invoice['remaining_amount'] = 0  # تأكيد ضبط المتبقي على صفر
                                    print(f"✅ الفاتورة اكتملت بعد الدفعة! المدفوع: {new_paid_amount}، الإجمالي: {total_amount}")
                                
                                # ✅ تحديث إحصائيات الزبون
                                customer['total_paid'] = customer.get('total_paid', 0) + payment_amount
                                customer['total_remaining'] = customer.get('total_remaining', 0) - payment_amount
                                
                                print(f"✅ تم تحديث الفاتورة في customers.json")
                            break
                    break
            
            with open("data/customers.json", 'w', encoding='utf-8') as f:
                json.dump(customers, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            print(f"❌ خطأ في تحديث الفاتورة: {e}")

    def delete_selected_payment(self):
        """✅ حذف الدفعة المحددة"""
        selected_row = self.payments_table.currentRow()
        if selected_row < 0:
            self.show_message("تحذير", "⚠️ يرجى اختيار دفعة للحذف", "warning")
            return
        
        try:
            if selected_row < len(self.payments):
                payment_to_delete = self.payments[selected_row]
                
                # ✅ ✅ ✅ التصحيح: استخدام رقم العرض الحقيقي في رسالة التأكيد
                display_number = self.get_invoice_display_number(payment_to_delete.get('invoice_uuid'))
                
                # ✅ تأكيد الحذف
                reply = self.show_message("تأكيد الحذف", 
                    f"هل أنت متأكد من حذف الدفعة رقم {selected_row + 1}؟\n\n"
                    f"الفاتورة: {display_number}\n"
                    f"المبلغ: {payment_to_delete.get('amount', 0):.2f} $\n"
                    f"التاريخ: {payment_to_delete.get('date', '')}",
                    "question", True)
                
                if reply == QMessageBox.Yes:
                    # ✅ حذف الدفعة من ملف customer_payments.json باستخدام UUID الفريد
                    self.delete_payment_from_file_by_uuid(payment_to_delete)
                    
                    # ✅ تحديث الفاتورة في ملف customers.json
                    self.remove_payment_from_invoice(payment_to_delete)
                    
                    # ✅ إعادة تحميل البيانات
                    self.load_payments_data()
                    
                    self.show_message("نجاح", "✅ تم حذف الدفعة بنجاح", "info")
            
        except Exception as e:
            self.show_message("خطأ", f"❌ حدث خطأ في حذف الدفعة: {e}", "error")

    def delete_payment_from_file_by_uuid(self, payment_to_delete):
        """✅ حذف الدفعة من ملف customer_payments.json باستخدام UUID الفريد"""
        try:
            payments_file = "data/customer_payments.json"
            if not os.path.exists(payments_file):
                return
            
            with open(payments_file, 'r', encoding='utf-8') as f:
                all_payments = json.load(f)
            
            # ✅ استخدام UUID الفريد للدفعة للبحث بدقة
            payment_uuid = payment_to_delete.get('payment_uuid')
            
            if payment_uuid:
                # ✅ البحث باستخدام UUID الفريد للدفعة
                updated_payments = [
                    payment for payment in all_payments 
                    if payment.get('payment_uuid') != payment_uuid
                ]
            else:
                # ✅ إذا لم يوجد UUID، نستخدم المعايير القديمة ولكن بدقة أكبر
                updated_payments = [
                    payment for payment in all_payments 
                    if not (payment.get('customer_id') == self.customer_id and
                           payment.get('invoice_uuid') == payment_to_delete.get('invoice_uuid') and
                           payment.get('amount') == payment_to_delete.get('amount') and
                           payment.get('date') == payment_to_delete.get('date') and
                           payment.get('time') == payment_to_delete.get('time'))
                ]
            
            with open(payments_file, 'w', encoding='utf-8') as f:
                json.dump(updated_payments, f, ensure_ascii=False, indent=2)
                
            print(f"✅ تم حذف الدفعة من customer_payments.json باستخدام UUID: {payment_uuid}")
                
        except Exception as e:
            print(f"❌ خطأ في حذف الدفعة من الملف: {e}")

    def remove_payment_from_invoice(self, payment_to_delete):
        """✅ إزالة الدفعة من الفاتورة في ملف customers.json"""
        try:
            with open("data/customers.json", 'r', encoding='utf-8') as f:
                customers = json.load(f)
            
            for customer in customers:
                if (customer.get('name') == self.customer_name and 
                    customer.get('phone') == self.phone_number):
                    
                    invoices = customer.get('invoices', [])
                    for invoice in invoices:
                        # ✅ البحث باستخدام UUID فقط
                        if invoice.get('invoice_uuid') == payment_to_delete.get('invoice_uuid'):
                            # ✅ إزالة الدفعة من قائمة دفعات الفاتورة باستخدام UUID الفريد
                            if 'payments' in invoice:
                                invoice['payments'] = [
                                    p for p in invoice['payments'] 
                                    if not (p.get('amount') == payment_to_delete.get('amount') and
                                           p.get('date') == payment_to_delete.get('date') and
                                           p.get('invoice_uuid') == payment_to_delete.get('invoice_uuid'))
                                ]
                            
                            # ✅ تحديث المبالغ المدفوعة والمتبقية
                            payment_amount = payment_to_delete.get('amount', 0)
                            invoice['paid_amount'] = max(0, invoice.get('paid_amount', 0) - payment_amount)
                            invoice['remaining_amount'] = invoice.get('remaining_amount', 0) + payment_amount
                            
                            # ✅ ✅ ✅ التصحيح: تحديث حالة الفاتورة بعد حذف الدفعة
                            total_amount = invoice.get('total_usd', 0)
                            new_paid_amount = invoice.get('paid_amount', 0)
                            
                            # ✅ ✅ ✅ استخدام مقارنة دقيقة مع Decimal
                            if abs(new_paid_amount - total_amount) < 0.01 or new_paid_amount >= total_amount:
                                invoice['remaining_amount'] = 0  # تأكيد ضبط المتبقي على صفر
                            else:
                                # إذا لم تكن الفاتورة مكتملة، تأكد من أن المتبقي صحيح
                                invoice['remaining_amount'] = total_amount - new_paid_amount
                            
                            # ✅ تحديث إحصائيات الزبون
                            customer['total_paid'] = max(0, customer.get('total_paid', 0) - payment_amount)
                            customer['total_remaining'] = customer.get('total_remaining', 0) + payment_amount
                            
                            print(f"✅ تم تحديث الفاتورة بعد حذف الدفعة")
                            break
                    break
            
            with open("data/customers.json", 'w', encoding='utf-8') as f:
                json.dump(customers, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            print(f"❌ خطأ في تحديث الفاتورة بعد الحذف: {e}")

    def delete_payments_by_invoice_uuid(self, invoice_uuid):
        """✅ ✅ ✅ وظيفة جديدة: حذف جميع الدفعات المرتبطة بفاتورة معينة"""
        try:
            payments_file = "data/customer_payments.json"
            if not os.path.exists(payments_file):
                return
            
            with open(payments_file, 'r', encoding='utf-8') as f:
                all_payments = json.load(f)
            
            # ✅ تصفية الدفعات المرتبطة بالفاتورة المحددة
            updated_payments = [
                payment for payment in all_payments 
                if not (payment.get('customer_id') == self.customer_id and
                       payment.get('invoice_uuid') == invoice_uuid)
            ]
            
            with open(payments_file, 'w', encoding='utf-8') as f:
                json.dump(updated_payments, f, ensure_ascii=False, indent=2)
                
            print(f"✅ تم حذف جميع الدفعات المرتبطة بالفاتورة UUID: {invoice_uuid}")
            
            # ✅ إعادة تحميل البيانات
            self.load_payments_data()
                
        except Exception as e:
            print(f"❌ خطأ في حذف دفعات الفاتورة: {e}")

    def delete_all_customer_payments(self):
        """✅ ✅ ✅ وظيفة جديدة: حذف جميع دفعات الزبون"""
        try:
            payments_file = "data/customer_payments.json"
            if not os.path.exists(payments_file):
                return
            
            with open(payments_file, 'r', encoding='utf-8') as f:
                all_payments = json.load(f)
            
            # ✅ تصفية جميع دفعات الزبون الحالي
            updated_payments = [
                payment for payment in all_payments 
                if not (payment.get('customer_id') == self.customer_id and
                       payment.get('customer_phone') == self.phone_number)
            ]
            
            with open(payments_file, 'w', encoding='utf-8') as f:
                json.dump(updated_payments, f, ensure_ascii=False, indent=2)
                
            print(f"✅ تم حذف جميع دفعات الزبون: {self.customer_name}")
            
            # ✅ إعادة تحميل البيانات
            self.load_payments_data()
                
        except Exception as e:
            print(f"❌ خطأ في حذف جميع دفعات الزبون: {e}")

    def export_to_word(self):
        """✅ ✅ ✅ وظيفة جديدة: تصدير إلى Microsoft Word باستخدام HTML"""
        try:
            if not self.payments:
                self.show_message("تحذير", "لا توجد دفعات لتصديرها", "warning")
                return
            
            # ✅ ✅ ✅ إنشاء نافذة خيارات التصدير مخصصة بدلاً من QInputDialog
            export_dialog = QDialog(self)
            export_dialog.setWindowTitle("خيارات التصدير")
            # ✅ تكبير حجم النافذة إلى حجم متوسط
            export_dialog.setFixedSize(500, 300)
            
            # ✅ ✅ ✅ تطبيق التنسيقات المطلوبة
            export_dialog.setStyleSheet("""
                QDialog {
                    background-color: #1e2a3a;
                }
                QLabel {
                    color: white;
                    font-size: 18px;
                    font-weight: bold;
                    font-family: Arial;
                    padding: 10px;
                }
                QComboBox {
                    background-color: white;
                    color: black;
                    font-size: 16px;
                    font-weight: bold;
                    padding: 12px;
                    border: 2px solid #3498db;
                    border-radius: 5px;
                    min-height: 40px;
                    font-family: Arial;
                }
                QComboBox QAbstractItemView {
                    background-color: white;
                    color: black;
                    font-size: 16px;
                    font-weight: bold;
                    selection-background-color: #3498db;
                    selection-color: white;
                    font-family: Arial;
                }
                QPushButton {
                    background-color: #185abd;
                    color: white;
                    font-size: 16px;
                    font-weight: bold;
                    padding: 15px 25px;
                    border: none;
                    border-radius: 6px;
                    min-height: 45px;
                    font-family: Arial;
                    min-width: 120px;
                }
                QPushButton:hover {
                    background-color: #164a9d;
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                                stop:0 #1e6fd9, stop:1 #185abd);
                }
                QPushButton#okButton {
                    background-color: #27ae60;
                    color: white;
                }
                QPushButton#okButton:hover {
                    background-color: #229954;
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                                stop:0 #2ecc71, stop:1 #27ae60);
                }
                QPushButton#cancelButton {
                    background-color: #95a5a6;
                    color: white;
                }
                QPushButton#cancelButton:hover {
                    background-color: #7f8c8d;
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                                stop:0 #bdc3c7, stop:1 #95a5a6);
                }
            """)
            
            layout = QVBoxLayout(export_dialog)
            
            # ✅ عنوان النافذة
            title_label = QLabel("اختر طريقة التصدير:")
            title_label.setAlignment(Qt.AlignCenter)
            layout.addWidget(title_label)
            
            # ✅ القائمة المنسدلة
            self.export_combo = QComboBox()
            self.export_combo.addItems(["تصدير كامل الصفحة", "تصدير دفعات محددة"])
            layout.addWidget(self.export_combo)
            
            layout.addStretch()
            
            # ✅ أزرار الموافقة والإلغاء
            button_layout = QHBoxLayout()
            
            ok_btn = QPushButton("موافق")
            ok_btn.setObjectName("okButton")
            ok_btn.clicked.connect(export_dialog.accept)
            
            cancel_btn = QPushButton("إلغاء")
            cancel_btn.setObjectName("cancelButton")
            cancel_btn.clicked.connect(export_dialog.reject)
            
            button_layout.addWidget(ok_btn)
            button_layout.addWidget(cancel_btn)
            
            layout.addLayout(button_layout)
            
            # ✅ عرض النافذة والحصول على النتيجة
            if export_dialog.exec() == QDialog.Accepted:
                choice = self.export_combo.currentText()
                
                if choice == "تصدير دفعات محددة":
                    # ✅ الحصول على الصفوف المحددة
                    selected_rows = self.payments_table.selectionModel().selectedRows()
                    if not selected_rows:
                        self.show_message("تحذير", "⚠️ يرجى اختيار دفعات محددة للتصدير", "warning")
                        return
                    
                    # ✅ جمع الدفعات المحددة
                    selected_payments = []
                    for model_index in selected_rows:
                        row = model_index.row()
                        if row < len(self.payments):
                            selected_payments.append(self.payments[row])
                    
                    payments_to_export = selected_payments
                    export_type = "محددة"
                else:
                    payments_to_export = self.payments
                    export_type = "كاملة"
                
                # ✅ اختيار مكان الحفظ
                default_filename = f"دفعات_{self.customer_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
                filename, _ = QFileDialog.getSaveFileName(
                    self, 
                    "حفظ الدفعات كـ Microsoft Word", 
                    os.path.expanduser(f"~/Desktop/{default_filename}"),
                    "Word Documents (*.html *.docx)"
                )
                
                if not filename:
                    return
                
                # ✅ إضافة امتداد .html إذا لم يكن موجوداً
                if not filename.lower().endswith(('.html', '.docx')):
                    filename += '.html'
                
                # ✅ إنشاء محتوى HTML يمكن فتحه في Word
                self.create_html_document(filename, payments_to_export, export_type)
                
                self.show_message("نجاح", f"✅ تم حفظ الدفعات كـ Microsoft Word بنجاح\n{filename}", "info")
            
        except Exception as e:
            self.show_message("خطأ", f"❌ حدث خطأ في التصدير إلى Word: {str(e)}", "error")

    def create_html_document(self, filename, payments, export_type):
        """✅ ✅ ✅ إنشاء مستند HTML يمكن فتحه في Microsoft Word"""
        try:
            total_usd = sum(payment.get('amount', 0) for payment in payments)
            total_lbp = sum(payment.get('amount_lbp', 0) for payment in payments)
            
            # ✅ الحصول على صورة الشعار كـ base64
            logo_base64 = ""
            logo_path = r"C:\Users\User\Desktop\chbib1\icons\logosave.png"
            if os.path.exists(logo_path):
                import base64
                with open(logo_path, "rb") as logo_file:
                    logo_base64 = base64.b64encode(logo_file.read()).decode()
            
            # ✅ إنشاء محتوى HTML
            html_content = f"""
            <!DOCTYPE html>
            <html dir="rtl" lang="ar">
            <head>
                <meta charset="UTF-8">
                <title>دفعات الزبون - {self.customer_name}</title>
                <style>
                    body {{
                        font-family: 'Arial', sans-serif;
                        margin: 20px;
                        line-height: 1.6;
                        direction: rtl;
                    }}
                    .header {{
                        text-align: center;
                        margin-bottom: 30px;
                        border-bottom: 2px solid #333;
                        padding-bottom: 20px;
                    }}
                    .logo {{
                        float: left;
                        margin-right: 20px;
                    }}
                    .customer-info {{
                        text-align: right;
                        margin-bottom: 20px;
                        background-color: #f8f9fa;
                        padding: 15px;
                        border-radius: 5px;
                        font-size: 20px;  /* ✅ أضف هذا السطر لتكبير الخط */
                        font-weight: bold; /* ✅ اختياري: لجعل الخط أكثر سماكة */
                    }}
                    .stats {{
                        background-color: #e9ecef;
                        padding: 15px;
                        border-radius: 5px;
                        margin-bottom: 20px;
                        text-align: right;
                    }}
                    table {{
                        width: 100%;
                        border-collapse: collapse;
                        margin: 20px 0;
                        font-size: 18px;
                    }}
                    th, td {{
                        border: 1px solid #ddd;
                        padding: 12px;
                        text-align: center;
                    }}
                    th {{
                        background-color: #2c3e50;
                        color: white;
                        font-weight: bold;
                    }}
                    tr:nth-child(even) {{
                        background-color: #f2f2f2;
                    }}
                    .total-section {{
                        background-color: #d4edda;
                        padding: 15px;
                        border-radius: 5px;
                        margin-top: 20px;
                        text-align: right;
                    }}
                    .footer {{
                        text-align: center;
                        margin-top: 30px;
                        font-size: 12px;
                        color: #666;
                    }}
                </style>
            </head>
            <body>
                <!-- ✅ الشعار في أعلى الصفحة -->
                <div class="header">
                    <div class="logo">
                        <img src="data:image/png;base64,{logo_base64}" width="180" height="105" alt="شعار المؤسسة">
                    </div>

                <!-- ✅ معلومات الزبون -->
                <div class="customer-info">
                    <p><strong>اسم الزبون:</strong> {self.customer_name}</p>
                    <p><strong>رقم الهاتف:</strong> {self.phone_number}</p>
                    <p><strong>سعر الصرف:</strong> {self.exchange_rate:,.0f}</p>


                <!-- ✅ الجدول في منتصف الصفحة -->
                <table>
                    <thead>
                        <tr>
                            <th>الرقم</th>
                            <th>رقم الفاتورة</th>
                            <th>المبلغ ($)</th>
                            <th>المبلغ (LBP)</th>
                            <th>التاريخ</th>
                        </tr>
                    </thead>
                    <tbody>
            """
            
            # ✅ إضافة بيانات الدفعات إلى الجدول
            for i, payment in enumerate(payments):
                display_number = self.get_invoice_display_number(payment.get('invoice_uuid'))
                html_content += f"""
                        <tr>
                            <td>{i + 1}</td>
                            <td>{display_number}</td>
                            <td>{payment.get('amount', 0):.2f} $</td>
                            <td>{payment.get('amount_lbp', 0):,.0f} LBP</td>
                            <td>{payment.get('date', '')}</td>
                        </tr>
                """
            
            html_content += f"""
                    </tbody>
                </table>

                <!-- ✅ الملخص -->
                <div class="total-section">
                   
                    <p><strong> عدد الدفعات:</strong> {len(payments)} دفعة</p>
                    <p><strong> المبلغ بالدولار:</strong> {total_usd:.2f} $</p>
                    <p><strong> المبلغ بالليرة اللبنانية:</strong> {total_lbp:,.0f} </p>
                </div>

            </body>
            </html>
            """
            
            # ✅ حفظ الملف
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            print(f"✅تم الحفظ بنجاح ")
            
        except Exception as e:
            print(f"❌ خطأ في إنشاء ملف HTML: {e}")
            self.show_message("خطأ", f"❌ حدث خطأ في إنشاء ملف Word: {str(e)}", "error")

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
        
    def closeEvent(self, event):
        """✅ إغلاق النافذة"""
        try:
            # ✅ إيقاف المؤقت قبل الإغلاق
            self.refresh_timer.stop()
            event.accept()
        except Exception as e:
            print(f"❌ خطأ في إغلاق النافذة: {e}")
            event.accept()