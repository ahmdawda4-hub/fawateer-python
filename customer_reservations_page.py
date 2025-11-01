import sys
import os
import sqlite3
import json
from datetime import datetime
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                               QTableWidget, QTableWidgetItem, QHeaderView, QPushButton, 
                               QLineEdit, QLabel, QMessageBox, QDialog, QDialogButtonBox,
                               QFormLayout, QSpinBox, QDoubleSpinBox, QDateEdit, QTextEdit,
                               QFrame, QScrollArea, QComboBox)
from PySide6.QtCore import Qt, QDate, QTimer
from PySide6.QtGui import QPixmap, QPalette, QBrush, QFont, QColor  # ⬅️ تم إضافة QColor هنا

class EditReservationDialog(QDialog):
    def __init__(self, reservation_data, parent=None):
        super().__init__(parent)
        self.reservation_data = reservation_data
        self.setup_ui()
        self.load_reservation_data()
        
    def setup_ui(self):
        self.setWindowTitle("تعديل الحجز")
        self.setFixedSize(500, 600)
        
        layout = QVBoxLayout()
        
        # نموذج التعديل
        form_layout = QFormLayout()
        
        self.customer_name = QLineEdit()
        self.customer_name.setReadOnly(True)  # لا يمكن تعديل اسم الزبون
        form_layout.addRow("اسم الزبون:", self.customer_name)
        
        self.items_edit = QTextEdit()
        self.items_edit.setPlaceholderText("أدخل الأصناف بصيغة JSON: [{\"name\": \"صنف1\", \"quantity\": 2}, ...]")
        form_layout.addRow("الأصناف:", self.items_edit)
        
        self.quantity = QSpinBox()
        self.quantity.setMinimum(1)
        self.quantity.setMaximum(100000)
        form_layout.addRow("الكمية:", self.quantity)
        
        self.unit_price_usd = QDoubleSpinBox()
        self.unit_price_usd.setMinimum(0.01)
        self.unit_price_usd.setMaximum(1000000)
        self.unit_price_usd.setDecimals(2)
        self.unit_price_usd.setPrefix("$ ")
        form_layout.addRow("سعر الوحدة (USD):", self.unit_price_usd)
        
        self.exchange_rate = QDoubleSpinBox()
        self.exchange_rate.setMinimum(1)
        self.exchange_rate.setMaximum(100000)
        self.exchange_rate.setDecimals(2)
        form_layout.addRow("سعر الصرف (LBP/USD):", self.exchange_rate)
        
        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDisplayFormat("dd\\MM\\yyyy")
        form_layout.addRow("التاريخ:", self.date_edit)
        
        layout.addLayout(form_layout)
        
        # الأزرار
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.validate_and_accept)
        button_box.rejected.connect(self.reject)
        
        layout.addWidget(button_box)
        self.setLayout(layout)
    
    def load_reservation_data(self):
        """تحميل بيانات الحجز الحالية"""
        if self.reservation_data:
            self.customer_name.setText(self.reservation_data.get('customer_name', ''))
            self.items_edit.setPlainText(self.reservation_data.get('items_json', ''))
            self.quantity.setValue(self.reservation_data.get('total_quantity', 1))
            self.unit_price_usd.setValue(self.reservation_data.get('unit_price_usd', 0.01))
            self.exchange_rate.setValue(self.reservation_data.get('exchange_rate', 89000))
            
            date_str = self.reservation_data.get('date', '')
            if date_str:
                try:
                    date = QDate.fromString(date_str, "dd\\MM\\yyyy")
                    if date.isValid():
                        self.date_edit.setDate(date)
                except:
                    self.date_edit.setDate(QDate.currentDate())
    
    def validate_and_accept(self):
        """التحقق من البيانات وقبولها"""
        try:
            items_json = self.items_edit.toPlainText()
            if items_json:
                json.loads(items_json)
        except:
            QMessageBox.warning(self, "خطأ", "صيغة JSON للأصناف غير صحيحة")
            return
            
        self.accept()
    
    def get_updated_data(self):
        """الحصول على البيانات المحدثة"""
        total_amount_usd = self.quantity.value() * self.unit_price_usd.value()
        total_amount_lbp = total_amount_usd * self.exchange_rate.value()
        
        return {
            'customer_name': self.customer_name.text().strip(),
            'items_json': self.items_edit.toPlainText(),
            'total_quantity': self.quantity.value(),
            'unit_price_usd': self.unit_price_usd.value(),
            'total_amount_usd': total_amount_usd,
            'total_amount_lbp': total_amount_lbp,
            'date': self.date_edit.date().toString("dd\\MM\\yyyy"),
            'exchange_rate': self.exchange_rate.value(),
            'remaining_quantity': self.quantity.value(),
            'remaining_amount_usd': total_amount_usd
        }

class AddWithdrawalDialog(QDialog):
    def __init__(self, customer_name, available_reservations, parent=None):
        super().__init__(parent)
        self.customer_name = customer_name
        self.available_reservations = available_reservations
        self.setup_ui()
        
    def setup_ui(self):
        self.setWindowTitle("إضافة فاتورة سحب")
        self.setFixedSize(500, 400)
        
        layout = QVBoxLayout()
        
        # نموذج السحب
        form_layout = QFormLayout()
        
        self.customer_label = QLabel(self.customer_name)
        form_layout.addRow("اسم الزبون:", self.customer_label)
        
        self.reservation_combo = QComboBox()
        for reservation in self.available_reservations:
            res_id, items, rem_qty, rem_amount = reservation
            self.reservation_combo.addItem(f"حجز #{res_id} - متبقي: {rem_qty} - ${rem_amount:.2f}", res_id)
        form_layout.addRow("الحجز المستهدف:", self.reservation_combo)
        
        self.items_edit = QTextEdit()
        self.items_edit.setPlaceholderText("أدخل الأصناف المسحوبة بصيغة JSON")
        form_layout.addRow("الأصناف المسحوبة:", self.items_edit)
        
        self.quantity = QSpinBox()
        self.quantity.setMinimum(1)
        self.quantity.setMaximum(100000)
        form_layout.addRow("الكمية المسحوبة:", self.quantity)
        
        self.amount_usd = QDoubleSpinBox()
        self.amount_usd.setMinimum(0.01)
        self.amount_usd.setMaximum(1000000)
        self.amount_usd.setDecimals(2)
        self.amount_usd.setPrefix("$ ")
        form_layout.addRow("المبلغ المسحوب (USD):", self.amount_usd)
        
        self.exchange_rate = QDoubleSpinBox()
        self.exchange_rate.setMinimum(1)
        self.exchange_rate.setMaximum(100000)
        self.exchange_rate.setDecimals(2)
        form_layout.addRow("سعر الصرف (LBP/USD):", self.exchange_rate)
        
        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDisplayFormat("dd\\MM\\yyyy")
        self.date_edit.setDate(QDate.currentDate())
        form_layout.addRow("تاريخ السحب:", self.date_edit)
        
        layout.addLayout(form_layout)
        
        # الأزرار
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.validate_and_accept)
        button_box.rejected.connect(self.reject)
        
        layout.addWidget(button_box)
        self.setLayout(layout)
    
    def validate_and_accept(self):
        """التحقق من البيانات وقبولها"""
        if not self.items_edit.toPlainText().strip():
            QMessageBox.warning(self, "خطأ", "يرجى إدخال الأصناف المسحوبة")
            return
            
        try:
            items_json = self.items_edit.toPlainText()
            json.loads(items_json)
        except:
            QMessageBox.warning(self, "خطأ", "صيغة JSON للأصناف غير صحيحة")
            return
            
        # التحقق من أن الكمية المسحوبة لا تتجاوز الكمية المتبقية
        selected_reservation = self.available_reservations[self.reservation_combo.currentIndex()]
        max_quantity = selected_reservation[2]  # remaining_quantity
        if self.quantity.value() > max_quantity:
            QMessageBox.warning(self, "خطأ", f"الكمية المسحوبة تتجاوز الكمية المتبقية ({max_quantity})")
            return
            
        self.accept()
    
    def get_withdrawal_data(self):
        """الحصول على بيانات السحب"""
        amount_lbp = self.amount_usd.value() * self.exchange_rate.value()
        
        return {
            'reservation_id': self.reservation_combo.currentData(),
            'customer_name': self.customer_name,
            'items_json': self.items_edit.toPlainText(),
            'quantity': self.quantity.value(),
            'amount_usd': self.amount_usd.value(),
            'amount_lbp': amount_lbp,
            'date': self.date_edit.date().toString("dd\\MM\\yyyy"),
            'exchange_rate': self.exchange_rate.value()
        }

class CustomerReservationsPage(QMainWindow):
    def __init__(self, customer_name, controller=None):  # ⬅️ تم إضافة controller كمعامل اختياري
        super().__init__()
        self.customer_name = customer_name
        self.controller = controller  # ⬅️ حفظ الـ controller للاستخدام
        self.setWindowTitle(f"حجوزات الزبون - {customer_name}")
        self.setGeometry(100, 100, 1400, 800)
        
        # إعداد قاعدة البيانات
        self.setup_database()
        
        # إعداد الواجهة
        self.setup_ui()
        
        # تحميل البيانات
        self.load_reservations()
        
        # حساب الرصيد المتبقي
        self.calculate_remaining_balance()
        
        # مؤقت للتحديث التلقائي
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.calculate_remaining_balance)
        self.update_timer.start(5000)  # تحديث كل 5 ثواني
    
    def setup_database(self):
        """إعداد قاعدة البيانات"""
        conn = sqlite3.connect('customer_reservations.db')
        cursor = conn.cursor()
        
        # جدول الحجوزات
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS reservations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_name TEXT NOT NULL,
                items_json TEXT NOT NULL,
                total_quantity INTEGER NOT NULL,
                unit_price_usd REAL NOT NULL,
                total_amount_usd REAL NOT NULL,
                total_amount_lbp REAL NOT NULL,
                date TEXT NOT NULL,
                remaining_quantity INTEGER NOT NULL,
                remaining_amount_usd REAL NOT NULL,
                exchange_rate REAL NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # جدول السحوبات
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS withdrawals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                reservation_id INTEGER,
                customer_name TEXT NOT NULL,
                items_json TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                amount_usd REAL NOT NULL,
                amount_lbp REAL NOT NULL,
                date TEXT NOT NULL,
                exchange_rate REAL NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (reservation_id) REFERENCES reservations (id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def setup_ui(self):
        """إعداد واجهة المستخدم"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # تعيين الخلفية باللون الداكن
        self.set_background_dark()
        
        # زر الرجوع في الأعلى من جهة اليمين (أقصى اليمين)
        top_back_button = QPushButton(" رجوع ")
        top_back_button.setStyleSheet("""
            QPushButton {
                background-color: #FF6B6B;
                color: white;
                font-weight: bold;
                padding: 8px 16px;
                border-radius: 5px;
                margin: 5px;
            }
            QPushButton:hover {
                background-color: #FF5252;
            }
        """)
        top_back_button.clicked.connect(self.go_back)
        top_back_button.setFixedSize(100, 40)
        
        # إضافة زر الرجوع في تخطيط منفصل في الأعلى
        top_layout = QHBoxLayout()
        top_layout.addStretch()  # دفع الزر إلى أقصى اليمين
        top_layout.addWidget(top_back_button)
        layout.addLayout(top_layout)
        
        # إطار العنوان مع خلفية شفافة تماماً
        title_frame = QFrame()
        title_frame.setStyleSheet("""
            QFrame {
                background-color: transparent;
                border-radius: 10px;
                padding: 10px;
            }
            QLabel {
                color: white;
                font-weight: bold;
                background-color: transparent;
            }
        """)
        title_layout = QHBoxLayout(title_frame)
        
        title_label = QLabel(f"حجوزات الزبون - {self.customer_name}")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setFont(QFont("Arial", 18, QFont.Bold))
        title_layout.addWidget(title_label)
        
        layout.addWidget(title_frame)
        
        # إطار الرصيد المتبقي مع خلفية شفافة تماماً
        self.balance_frame = QFrame()
        self.balance_frame.setStyleSheet("""
            QFrame {
                background-color: transparent;
                border: 2px solid #32CD32;
                border-radius: 8px;
                padding: 10px;
            }
            QLabel {
                color: #32CD32;
                font-weight: bold;
                background-color: transparent;
                font-size: 14px;
            }
        """)
        balance_layout = QHBoxLayout(self.balance_frame)
        
        balance_layout.addStretch()
        
        self.balance_lbp_label = QLabel("0 LBP")
        self.balance_lbp_label.setFont(QFont("Arial", 14, QFont.Bold))
        balance_layout.addWidget(self.balance_lbp_label)
        
        self.balance_usd_label = QLabel("0$")
        self.balance_usd_label.setFont(QFont("Arial", 14, QFont.Bold))
        balance_layout.addWidget(self.balance_usd_label)
        
        balance_title = QLabel("المتبقي للزبون:")
        balance_title.setFont(QFont("Arial", 14, QFont.Bold))
        balance_layout.addWidget(balance_title)
        
        layout.addWidget(self.balance_frame)
        
        # إطار البحث مع خلفية شفافة تماماً
        search_frame = QFrame()
        search_frame.setStyleSheet("""
            QFrame {
                background-color: transparent;
                border: 1px solid #ccc;
                border-radius: 5px;
                padding: 8px;
            }
            QLineEdit {
                background-color: rgba(255, 255, 255, 0.9);
                border: 1px solid #aaa;
                border-radius: 3px;
                padding: 8px;
                font-size: 14px;
            }
            QLabel {
                background-color: transparent;
                font-size: 14px;
                color: white;
            }
        """)
        search_layout = QHBoxLayout(search_frame)
        
        search_layout.addStretch()
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("ابحث بالتاريخ (dd\\mm\\yyyy) أو باسم الصنف...")
        self.search_input.textChanged.connect(self.search_reservations)
        self.search_input.setFixedWidth(350)
        self.search_input.setMinimumHeight(35)
        search_layout.addWidget(self.search_input)
        
        search_label = QLabel("بحث:")
        search_label.setFont(QFont("Arial", 12))
        search_layout.addWidget(search_label)
        
        layout.addWidget(search_frame)
        
        # الجدول مع خلفية شفافة
        self.setup_table()
        layout.addWidget(self.table)
        
        # إطار الأزرار مع خلفية شفافة تماماً
        button_frame = QFrame()
        button_frame.setStyleSheet("""
            QFrame {
                background-color: transparent;
                border-radius: 5px;
                padding: 5px;
            }
        """)
        button_layout = QHBoxLayout(button_frame)
        
        button_layout.addStretch()
        
        # تم حذف زر إضافة سحب
        
        # زر حذف
        self.delete_button = QPushButton("حذف الحجز")
        self.delete_button.setStyleSheet("""
            QPushButton {
                background-color: #DC3545;
                color: white;
                font-weight: bold;
                padding: 12px 24px;
                border-radius: 5px;
                font-size: 14px;
                min-height: 20px;
            }
            QPushButton:hover {
                background-color: #C82333;
            }
        """)
        self.delete_button.clicked.connect(self.delete_reservation)
        self.delete_button.setMinimumHeight(45)
        button_layout.addWidget(self.delete_button)
        
        # زر تعديل
        self.edit_button = QPushButton("تعديل الحجز")
        self.edit_button.setStyleSheet("""
            QPushButton {
                background-color: #28A745;
                color: white;
                font-weight: bold;
                padding: 12px 24px;
                border-radius: 5px;
                font-size: 14px;
                min-height: 20px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)
        self.edit_button.clicked.connect(self.edit_reservation)
        self.edit_button.setMinimumHeight(45)
        button_layout.addWidget(self.edit_button)
        
        layout.addWidget(button_frame)
    
    def set_background_dark(self):
        """تعيين خلفية النافذة باللون الداكن"""
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(53, 53, 53))  # لون داكن
        self.setPalette(palette)
    
    def load_icon(self, icon_name):
        """تحميل الأيقونة"""
        icon_path = os.path.join(r"C:\Users\User\Desktop\chbib1\icons", icon_name)
        if os.path.exists(icon_path):
            return QPixmap(icon_path)
        return QPixmap()
    
    def setup_table(self):
        """إعداد الجدول بخلفية شفافة وعناوين كحلية داكنة"""
        self.table = QTableWidget()
        self.table.setColumnCount(10)
        headers = [
            "رقم", "الزبون", "الأصناف", "الكمية", "سعر الوحدة", 
            "المبلغ USD", "المبلغ LBP", "التاريخ", "الكمية المتبقية", "المبلغ المتبقي USD"
        ]
        self.table.setHorizontalHeaderLabels(headers)
        
        # إعداد خصائص الجدول
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setAlternatingRowColors(True)
        
        # تكبير حجم الصفوف والخطوط
        self.table.setFont(QFont("Arial", 12))
        self.table.verticalHeader().setDefaultSectionSize(50)  # زيادة ارتفاع الصفوف
        
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: rgba(255, 255, 255, 0.8);  /* شفافية 80% */
                alternate-background-color: rgba(240, 240, 240, 0.8);  /* شفافية 80% */
                gridline-color: #ddd;
                font-size: 14px;
            }
            QHeaderView::section {
                background-color: #1a237e;  /* كحلي داكن */
                color: white;
                font-weight: bold;
                padding: 12px;
                border: none;
                font-size: 14px;
                min-height: 50px;
            }
            QTableWidget::item {
                background-color: transparent;
                padding: 8px;
            }
            QTableCornerButton::section {
                background-color: #1a237e;
            }
        """)
    
    def load_reservations(self):
        """تحميل حجوزات الزبون المحدد فقط"""
        conn = sqlite3.connect('customer_reservations.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, customer_name, items_json, total_quantity, unit_price_usd, 
                   total_amount_usd, total_amount_lbp, date, remaining_quantity, remaining_amount_usd
            FROM reservations
            WHERE customer_name = ?
            ORDER BY date DESC
        ''', (self.customer_name,))
        
        reservations = cursor.fetchall()
        conn.close()
        
        self.table.setRowCount(len(reservations))
        
        for row_idx, row_data in enumerate(reservations):
            for col_idx, col_data in enumerate(row_data):
                if col_idx == 2:  # عمود الأصناف
                    try:
                        items = json.loads(col_data)
                        items_str = ", ".join([f"{item['name']}({item['quantity']})" for item in items])
                        item = QTableWidgetItem(items_str)
                    except:
                        item = QTableWidgetItem(str(col_data))
                elif col_idx in [4, 5, 9]:  # الأسعار (USD)
                    item = QTableWidgetItem(f"${col_data:.2f}")
                elif col_idx == 6:  # المبلغ LBP
                    item = QTableWidgetItem(f"{col_data:,.0f} LBP")
                elif col_idx in [3, 8]:  # الكميات
                    item = QTableWidgetItem(f"{col_data:.0f}")
                else:
                    item = QTableWidgetItem(str(col_data))
                
                item.setTextAlignment(Qt.AlignCenter)
                item.setFont(QFont("Arial", 11))
                self.table.setItem(row_idx, col_idx, item)
    
    def search_reservations(self):
        """بحث في حجوزات الزبون المحدد"""
        search_text = self.search_input.text().strip()
        if not search_text:
            self.load_reservations()
            return
        
        conn = sqlite3.connect('customer_reservations.db')
        cursor = conn.cursor()
        
        # البحث بالتاريخ أو باسم الصنف للزبون المحدد فقط
        cursor.execute('''
            SELECT id, customer_name, items_json, total_quantity, unit_price_usd, 
                   total_amount_usd, total_amount_lbp, date, remaining_quantity, remaining_amount_usd
            FROM reservations
            WHERE customer_name = ? AND (date LIKE ? OR items_json LIKE ?)
            ORDER BY date DESC
        ''', (self.customer_name, f'%{search_text}%', f'%{search_text}%'))
        
        reservations = cursor.fetchall()
        conn.close()
        
        self.table.setRowCount(len(reservations))
        
        for row_idx, row_data in enumerate(reservations):
            for col_idx, col_data in enumerate(row_data):
                if col_idx == 2:  # عمود الأصناف
                    try:
                        items = json.loads(col_data)
                        items_str = ", ".join([f"{item['name']}({item['quantity']})" for item in items])
                        item = QTableWidgetItem(items_str)
                    except:
                        item = QTableWidgetItem(str(col_data))
                elif col_idx in [4, 5, 9]:  # الأسعار (USD)
                    item = QTableWidgetItem(f"${col_data:.2f}")
                elif col_idx == 6:  # المبلغ LBP
                    item = QTableWidgetItem(f"{col_data:,.0f} LBP")
                elif col_idx in [3, 8]:  # الكميات
                    item = QTableWidgetItem(f"{col_data:.0f}")
                else:
                    item = QTableWidgetItem(str(col_data))
                
                item.setTextAlignment(Qt.AlignCenter)
                item.setFont(QFont("Arial", 11))
                self.table.setItem(row_idx, col_idx, item)
    
    def calculate_remaining_balance(self):
        """حساب الرصيد المتبقي للزبون المحدد فقط"""
        conn = sqlite3.connect('customer_reservations.db')
        cursor = conn.cursor()
        
        # مجموع المبالغ المتبقية من حجوزات الزبون المحدد
        cursor.execute('''
            SELECT COALESCE(SUM(remaining_amount_usd), 0), 
                   COALESCE(SUM(remaining_amount_usd * exchange_rate), 0)
            FROM reservations
            WHERE customer_name = ?
        ''', (self.customer_name,))
        
        total_usd, total_lbp = cursor.fetchone()
        conn.close()
        
        # تحديث التسميات
        self.balance_usd_label.setText(f"{total_usd:.2f}$")
        self.balance_lbp_label.setText(f"{total_lbp:,.0f} LBP")
    
    def edit_reservation(self):
        """تعديل الحجز المحدد"""
        current_row = self.table.currentRow()
        if current_row == -1:
            QMessageBox.warning(self, "تحذير", "يرجى اختيار حجز للتعديل")
            return
        
        reservation_id = int(self.table.item(current_row, 0).text())
        
        # جلب بيانات الحجز الحالية
        conn = sqlite3.connect('customer_reservations.db')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM reservations WHERE id = ? AND customer_name = ?', 
                      (reservation_id, self.customer_name))
        reservation_data = cursor.fetchone()
        conn.close()
        
        if not reservation_data:
            QMessageBox.warning(self, "خطأ", "لم يتم العثور على الحجز")
            return
        
        # تحويل البيانات إلى قاموس
        columns = ['id', 'customer_name', 'items_json', 'total_quantity', 'unit_price_usd', 
                  'total_amount_usd', 'total_amount_lbp', 'date', 'remaining_quantity', 
                  'remaining_amount_usd', 'exchange_rate', 'created_at']
        reservation_dict = dict(zip(columns, reservation_data))
        
        # فتح نافذة التعديل
        dialog = EditReservationDialog(reservation_dict, self)
        if dialog.exec() == QDialog.Accepted:
            updated_data = dialog.get_updated_data()
            
            # تحديث البيانات في قاعدة البيانات
            conn = sqlite3.connect('customer_reservations.db')
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE reservations 
                SET items_json = ?, total_quantity = ?, unit_price_usd = ?,
                    total_amount_usd = ?, total_amount_lbp = ?, date = ?, exchange_rate = ?,
                    remaining_quantity = ?, remaining_amount_usd = ?
                WHERE id = ? AND customer_name = ?
            ''', (
                updated_data['items_json'], 
                updated_data['total_quantity'], updated_data['unit_price_usd'],
                updated_data['total_amount_usd'], updated_data['total_amount_lbp'],
                updated_data['date'], updated_data['exchange_rate'],
                updated_data['remaining_quantity'], updated_data['remaining_amount_usd'],
                reservation_id, self.customer_name
            ))
            
            conn.commit()
            conn.close()
            
            QMessageBox.information(self, "نجاح", "تم تعديل الحجز بنجاح")
            self.load_reservations()
            self.calculate_remaining_balance()
    
    def delete_reservation(self):
        """حذف الحجز المحدد"""
        current_row = self.table.currentRow()
        if current_row == -1:
            QMessageBox.warning(self, "تحذير", "يرجى اختيار حجز للحذف")
            return
        
        reservation_id = int(self.table.item(current_row, 0).text())
        
        reply = QMessageBox.question(
            self, "تأكيد الحذف", 
            "هل أنت متأكد من حذف هذا الحجز؟",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            conn = sqlite3.connect('customer_reservations.db')
            cursor = conn.cursor()
            
            # حذف السحوبات المرتبطة أولاً
            cursor.execute('DELETE FROM withdrawals WHERE reservation_id = ?', (reservation_id,))
            
            # حذف الحجز
            cursor.execute('DELETE FROM reservations WHERE id = ? AND customer_name = ?', 
                          (reservation_id, self.customer_name))
            
            conn.commit()
            conn.close()
            
            QMessageBox.information(self, "نجاح", "تم حذف الحجز بنجاح")
            self.load_reservations()
            self.calculate_remaining_balance()
    
    def go_back(self):
        """العودة إلى صفحة الفواتير"""
        if self.controller:
            # إذا كان هناك controller، استخدمه للعودة
            self.controller.show_invoices_page()
        else:
            # إذا لم يكن هناك controller، أغلق النافذة فقط
            self.close()
    
    def add_reservation_from_invoice(self, invoice_data):
        """إضافة حجز جديد من صفحة الفواتير (للاستخدام من الصفحات الأخرى)"""
        if invoice_data['customer_name'] != self.customer_name:
            return  # لا تضيف إذا كان اسم الزبون لا يتطابق
        
        conn = sqlite3.connect('customer_reservations.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO reservations 
            (customer_name, items_json, total_quantity, unit_price_usd, total_amount_usd, 
             total_amount_lbp, date, remaining_quantity, remaining_amount_usd, exchange_rate)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            invoice_data['customer_name'],
            invoice_data['items_json'],
            invoice_data['total_quantity'],
            invoice_data['unit_price_usd'],
            invoice_data['total_amount_usd'],
            invoice_data['total_amount_lbp'],
            invoice_data['date'],
            invoice_data['total_quantity'],
            invoice_data['total_amount_usd'],
            invoice_data['exchange_rate']
        ))
        
        conn.commit()
        conn.close()
        
        self.load_reservations()
        self.calculate_remaining_balance()

def main():
    app = QApplication(sys.argv)
    
    # للاختبار - يمكنك تمرير اسم الزبون كمعامل
    customer_name = "زبون تجريبي"  # سيتم استبدال هذا من صفحة الفواتير
    window = CustomerReservationsPage(customer_name)
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()