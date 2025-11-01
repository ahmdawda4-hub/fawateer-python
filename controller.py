import os
import json
import sys
from PySide6.QtWidgets import QMainWindow, QStackedWidget
from PySide6.QtCore import Qt
from PySide6.QtGui import QPalette, QBrush, QPixmap

# إضافة المسار الحالي إلى sys.path لتجنب مشاكل الاستيراد
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

class MainController(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # ⚡ فوري: الإعدادات الأساسية
        self.setWindowTitle("CHBIB - نظام إدارة مواد البناء")
        self.setLayoutDirection(Qt.RightToLeft)
        
        # ⚡ إعدادات النافذة لتمكين التكبير والتصغير
        self.setWindowFlags(Qt.Window | Qt.WindowMinimizeButtonHint | Qt.WindowMaximizeButtonHint | Qt.WindowCloseButtonHint)
        
        # ⚡ تعيين حجم ابتدائي كبير
        self.resize(1200, 800)
        
        # ⚡ فوري: تحميل الخلفية من ملف
        self._load_background_from_file()
        
        # ⚡ المكونات الأساسية
        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)
        
        self.pages = {}
        self.settings_file = "app_settings.json"
        self.logo_settings = {}
        
        # ⚡ فوري: تحميل الصفحة الرئيسية
        self._load_main_page_instant()
        
        # ⚡ فوري: النافذة كاملة الشاشة بعد تحميل المحتوى
        self.showMaximized()

    def _load_background_from_file(self):
        """تحميل الخلفية من ملف الصورة"""
        bg_path = r"C:\Users\User\Desktop\chbib1\icons\bg.jpg"
        if os.path.exists(bg_path):
            # استخدام صورة الخلفية من الملف
            palette = QPalette()
            pixmap = QPixmap(bg_path)
            # تأجيل التحجيم الفعلي حتى تكون النافذة جاهزة
            self.background_pixmap = pixmap
            palette.setBrush(QPalette.Window, QBrush(pixmap))
            self.setPalette(palette)
        else:
            # استخدام CSS كخلفية احتياطية إذا لم توجد الصورة
            self.setStyleSheet("""
                QMainWindow, QWidget {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                                                stop:0 #0D1B2A, stop:0.5 #1B263B, stop:1 #415A77);
                }
                QStackedWidget {
                    background: transparent;
                }
            """)

    def resizeEvent(self, event):
        """إعادة رسم الخلفية عند تغيير حجم النافذة"""
        super().resizeEvent(event)
        # إعادة تحميل الخلفية لضبطها مع الحديد الجديد
        bg_path = r"C:\Users\User\Desktop\chbib1\icons\bg.jpg"
        if os.path.exists(bg_path):
            palette = QPalette()
            pixmap = QPixmap(bg_path)
            scaled_pixmap = pixmap.scaled(self.size(), Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
            palette.setBrush(QPalette.Window, QBrush(scaled_pixmap))
            self.setPalette(palette)

    def _load_main_page_instant(self):
        """تحميل فوري للصفحة الرئيسية"""
        try:
            # محاولة الاستيراد من مجلد pages
            from pages.main_page import MainPage
            self.pages["main"] = MainPage(self)
            self.stack.addWidget(self.pages["main"])
            self.stack.setCurrentWidget(self.pages["main"])
            print("✅ تم تحميل الصفحة الرئيسية بنجاح")
        except ImportError as e:
            print(f"❌ خطأ في استيراد الصفحة الرئيسية: {e}")
            # إنشاء صفحة بديلة في حالة الخطأ
            from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton
            class TempMainPage(QWidget):
                def __init__(self, controller):
                    super().__init__()
                    self.controller = controller
                    layout = QVBoxLayout()
                    title = QLabel("الصفحة الرئيسية - نسخة مؤقتة")
                    title.setStyleSheet("font-size: 24px; color: white;")
                    layout.addWidget(title)
                    
                    test_btn = QPushButton("اختبار تحميل الصفحات")
                    test_btn.clicked.connect(self.test_pages)
                    layout.addWidget(test_btn)
                    
                    self.setLayout(layout)
                
                def test_pages(self):
                    try:
                        from pages.invoices_page import InvoicesPage
                        print("✅ invoices_page يمكن استيراده")
                    except Exception as e:
                        print(f"❌ invoices_page: {e}")
                    
                    try:
                        from pages.customers_page import CustomersPage  
                        print("✅ customers_page يمكن استيراده")
                    except Exception as e:
                        print(f"❌ customers_page: {e}")
            
            self.pages["main"] = TempMainPage(self)
            self.stack.addWidget(self.pages["main"])
            self.stack.setCurrentWidget(self.pages["main"])

    def _load_settings_background(self):
        """تحميل الإعدادات في الخلفية بعد عرض الواجهة"""
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    self.logo_settings = json.load(f)
        except:
            self.logo_settings = {}

    def _load_page(self, page_name):
        """تحميل الصفحات الأخرى عند الطلب"""
        if page_name not in self.pages:
            try:
                if page_name == "admin":
                    from pages.admin_page import AdminPage
                    self.pages["admin"] = AdminPage(self)
                    self.stack.addWidget(self.pages["admin"])
                elif page_name == "invoices":
                    from pages.invoices_page import InvoicesPage
                    self.pages["invoices"] = InvoicesPage(self)
                    self.stack.addWidget(self.pages["invoices"])
                elif page_name == "customers":
                    from pages.customers_page import CustomersPage
                    self.pages["customers"] = CustomersPage(self)
                    self.stack.addWidget(self.pages["customers"])
                elif page_name == "reports":
                    from pages.reports_page import ReportsPage
                    self.pages["reports"] = ReportsPage(self)
                    self.stack.addWidget(self.pages["reports"])
                elif page_name == "settings":
                    from pages.settings_page import SettingsPage
                    self.pages["settings"] = SettingsPage(self)
                    self.stack.addWidget(self.pages["settings"])
                elif page_name == "logo_settings":
                    from pages.logo_settings_page import LogoSettingsPage
                    self.pages["logo_settings"] = LogoSettingsPage(self)
                    self.stack.addWidget(self.pages["logo_settings"])
                elif page_name == "payments":
                    from pages.payment_manager import PaymentManager
                    self.pages["payments"] = PaymentManager(self)
                    self.stack.addWidget(self.pages["payments"])
                    print("✅ تم تحميل صفحة الدفعات بنجاح")
                
                print(f"✅ تم تحميل صفحة {page_name} بنجاح")
                
            except Exception as e:
                print(f"❌ خطأ في تحميل صفحة {page_name}: {e}")
                # إنشاء صفحة بديلة
                from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton
                class TempPage(QWidget):
                    def __init__(self, controller, page_name):
                        super().__init__()
                        self.controller = controller
                        layout = QVBoxLayout()
                        title = QLabel(f"صفحة {page_name} - نسخة مؤقتة")
                        title.setStyleSheet("font-size: 24px; color: white;")
                        layout.addWidget(title)
                        
                        error_label = QLabel(f"الخطأ: {str(e)}")
                        error_label.setStyleSheet("color: red; font-size: 14px;")
                        layout.addWidget(error_label)
                        
                        back_btn = QPushButton("رجوع للصفحة الرئيسية")
                        back_btn.clicked.connect(self.controller.show_main_page)
                        layout.addWidget(back_btn)
                        
                        self.setLayout(layout)
                
                self.pages[page_name] = TempPage(self, page_name)
                self.stack.addWidget(self.pages[page_name])
        
        return self.pages[page_name]

    def _load_customer_invoices_page(self, customer_id, customer_name, customer_phone):
        """✅ تحميل صفحة فواتير الزبون مع بيانات محددة"""
        try:
            # ✅ إنشاء مفتاح فريد للصفحة بناءً على customer_id
            page_key = f"customer_{customer_id}"
            
            if page_key not in self.pages:
                from pages.customer_invoices_page import CustomerInvoicesPage
                self.pages[page_key] = CustomerInvoicesPage(self, customer_id, customer_name, customer_phone)
                self.stack.addWidget(self.pages[page_key])
                print(f"✅ تم تحميل صفحة الزبون: {customer_name} (ID: {customer_id})")
            
            return self.pages[page_key]
            
        except Exception as e:
            print(f"❌ خطأ في تحميل صفحة الزبون: {e}")
            # إنشاء صفحة بديلة في حالة الخطأ
            from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton
            class TempCustomerPage(QWidget):
                def __init__(self, controller, customer_name, customer_phone):
                    super().__init__()
                    self.controller = controller
                    layout = QVBoxLayout()
                    
                    title = QLabel(f"صفحة الزبون: {customer_name}")
                    title.setStyleSheet("font-size: 24px; color: white;")
                    layout.addWidget(title)
                    
                    phone_label = QLabel(f"رقم الهاتف: {customer_phone}")
                    phone_label.setStyleSheet("color: white; font-size: 16px;")
                    layout.addWidget(phone_label)
                    
                    error_label = QLabel(f"الخطأ: {str(e)}")
                    error_label.setStyleSheet("color: red; font-size: 14px;")
                    layout.addWidget(error_label)
                    
                    back_btn = QPushButton("رجوع لصفحة الزبائن")
                    back_btn.clicked.connect(self.controller.show_invoices_page)
                    layout.addWidget(back_btn)
                    
                    self.setLayout(layout)
            
            page_key = f"customer_temp_{customer_id}"
            self.pages[page_key] = TempCustomerPage(self, customer_name, customer_phone)
            self.stack.addWidget(self.pages[page_key])
            return self.pages[page_key]

    def _load_customer_reservations_page(self, customer_name):
        """✅ تحميل صفحة حجوزات الزبون مع الاسم فقط"""
        try:
            # ✅ إنشاء مفتاح فريد للصفحة بناءً على اسم الزبون
            page_key = f"reservations_{customer_name}"
            
            if page_key not in self.pages:
                print(f"🔍 محاولة تحميل صفحة الحجوزات للزبون: {customer_name}")
                
                # ✅ استخدام المسار المطلق للتأكد من وجود الملف
                project_root = r"C:\Users\User\Desktop\chbib1"
                file_path = os.path.join(project_root, "pages", "customer_reservations_page.py")
                
                if not os.path.exists(file_path):
                    raise ImportError(f"ملف الحجوزات غير موجود: {file_path}")
                
                print(f"✅ الملف موجود: {file_path}")
                
                # ✅ إضافة المسار إلى sys.path للاستيراد
                pages_dir = os.path.join(project_root, "pages")
                if pages_dir not in sys.path:
                    sys.path.append(pages_dir)
                    print(f"✅ تم إضافة المسار إلى sys.path: {pages_dir}")
                
                # ✅ استيراد CustomerReservationsPage
                try:
                    from customer_reservations_page import CustomerReservationsPage
                    print("✅ تم استيراد CustomerReservationsPage بنجاح")
                except ImportError as e:
                    print(f"❌ فشل الاستيراد المباشر: {e}")
                    # محاولة بديلة: استيراد من المسار الكامل
                    import importlib.util
                    spec = importlib.util.spec_from_file_location("customer_reservations_page", file_path)
                    customer_reservations_module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(customer_reservations_module)
                    CustomerReservationsPage = customer_reservations_module.CustomerReservationsPage
                    print("✅ تم استيراد CustomerReservationsPage باستخدام importlib")
                
                # ✅ إنشاء الصفحة
                self.pages[page_key] = CustomerReservationsPage(customer_name, self)
                self.stack.addWidget(self.pages[page_key])
                print(f"✅ تم تحميل صفحة حجوزات الزبون: {customer_name}")
            
            return self.pages[page_key]
            
        except Exception as e:
            print(f"❌ خطأ في تحميل صفحة حجوزات الزبون: {e}")
            import traceback
            traceback.print_exc()  # ✅ طباعة التفاصيل الكاملة للخطأ
            
            # إنشاء صفحة بديلة في حالة الخطأ
            from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QMessageBox
            class TempReservationsPage(QWidget):
                def __init__(self, controller, customer_name, error_msg):
                    super().__init__()
                    self.controller = controller
                    layout = QVBoxLayout()
                    
                    title = QLabel(f"صفحة حجوزات الزبون: {customer_name}")
                    title.setStyleSheet("font-size: 24px; color: white;")
                    layout.addWidget(title)
                    
                    error_label = QLabel(f"الخطأ: {error_msg}")
                    error_label.setStyleSheet("color: red; font-size: 14px;")
                    layout.addWidget(error_label)
                    
                    # زر لتفاصيل الخطأ
                    debug_btn = QPushButton("تفاصيل الخطأ")
                    debug_btn.clicked.connect(lambda: self.show_debug_info(error_msg))
                    layout.addWidget(debug_btn)
                    
                    # زر لفحص الملف
                    check_file_btn = QPushButton("فحص ملف الحجوزات")
                    check_file_btn.clicked.connect(self.check_reservations_file)
                    layout.addWidget(check_file_btn)
                    
                    back_btn = QPushButton("رجوع لصفحة الفواتير")
                    back_btn.clicked.connect(self.controller.show_invoices_page)
                    layout.addWidget(back_btn)
                    
                    self.setLayout(layout)
                    self.error_msg = error_msg
                
                def show_debug_info(self, error_msg):
                    QMessageBox.information(self, "تفاصيل الخطأ", f"الخطأ الكامل:\n{error_msg}")
                
                def check_reservations_file(self):
                    """فحص وجود وملاءمة ملف الحجوزات"""
                    project_root = r"C:\Users\User\Desktop\chbib1"
                    file_path = os.path.join(project_root, "pages", "customer_reservations_page.py")
                    if os.path.exists(file_path):
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                content = f.read()
                                lines = content.split('\n')
                                
                            if "class CustomerReservationsPage" in content:
                                # البحث عن سطر تعريف الكلاس
                                class_line = None
                                for i, line in enumerate(lines):
                                    if "class CustomerReservationsPage" in line:
                                        class_line = f"السطر {i+1}: {line.strip()}"
                                        break
                                
                                QMessageBox.information(self, "فحص الملف", 
                                    f"✅ الملف موجود ويحتوي على الكلاس المطلوب\n\n"
                                    f"المسار: {file_path}\n"
                                    f"{class_line}")
                            else:
                                QMessageBox.warning(self, "فحص الملف", 
                                    f"⚠️ الملف موجود لكن لا يحتوي على الكلاس المطلوب\n\nالمسار: {file_path}")
                        except Exception as e:
                            QMessageBox.critical(self, "فحص الملف", 
                                f"❌ خطأ في قراءة الملف: {e}")
                    else:
                        QMessageBox.critical(self, "فحص الملف", 
                            f"❌ الملف غير موجود في المسار: {file_path}")
            
            page_key = f"reservations_temp_{customer_name}"
            self.pages[page_key] = TempReservationsPage(self, customer_name, str(e))
            self.stack.addWidget(self.pages[page_key])
            return self.pages[page_key]

    def show_main_page(self):
        page = self._load_page("main")
        self.stack.setCurrentWidget(page)

    def show_admin_page(self):
        page = self._load_page("admin")
        self.stack.setCurrentWidget(page)

    def show_invoices_page(self):
        page = self._load_page("invoices")
        self.stack.setCurrentWidget(page)

    def show_customers_page(self):
        page = self._load_page("customers")
        self.stack.setCurrentWidget(page)

    def show_reports_page(self):
        page = self._load_page("reports")
        self.stack.setCurrentWidget(page)

    def show_settings_page(self):
        page = self._load_page("settings")
        self.stack.setCurrentWidget(page)

    def show_logo_settings_page(self):
        page = self._load_page("logo_settings")
        self.stack.setCurrentWidget(page)

    def show_payments_page(self):
        page = self._load_page("payments")
        self.stack.setCurrentWidget(page)

    def show_customer_page(self, customer_id, customer_name, customer_phone):
        """✅ الانتقال إلى صفحة الزبون المحدد"""
        page = self._load_customer_invoices_page(customer_id, customer_name, customer_phone)
        self.stack.setCurrentWidget(page)
        print(f"✅ تم الانتقال إلى صفحة الزبون: {customer_name}")

    def show_customer_invoices_page(self, customer_id, customer_name, customer_phone):
        """✅ الانتقال إلى صفحة فواتير الزبون - دالة مضافة للتوافق"""
        page = self._load_customer_invoices_page(customer_id, customer_name, customer_phone)
        self.stack.setCurrentWidget(page)
        print(f"✅ تم الانتقال إلى صفحة الزبون: {customer_name}")

    def show_customer_reservations_page(self, customer_name):
        """✅ الانتقال إلى صفحة حجوزات الزبون المحدد"""
        page = self._load_customer_reservations_page(customer_name)
        self.stack.setCurrentWidget(page)
        print(f"✅ تم الانتقال إلى صفحة حجوزات الزبون: {customer_name}")

    def _save_settings(self):
        """حفظ الإعدادات"""
        try:
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(self.logo_settings, f, ensure_ascii=False, indent=4)
        except:
            pass

    def refresh_logo(self, page_name):
        """تحديث الشعار"""
        if page_name in ["الرئيسية", "main"] and "main" in self.pages:
            self.pages["main"].refresh_logo()
        elif page_name in ["الإدارة", "admin"] and "admin" in self.pages:
            self.pages["admin"].refresh_logo()
        elif page_name in ["الفواتير", "invoices"] and "invoices" in self.pages:
            self.pages["invoices"].refresh_logo()
        elif page_name in ["الزبائن", "customers"] and "customers" in self.pages:
            self.pages["customers"].refresh_logo()
        elif page_name in ["التقارير", "reports"] and "reports" in self.pages:
            self.pages["reports"].refresh_logo()
        elif page_name in ["الإعدادات", "settings"] and "settings" in self.pages:
            self.pages["settings"].refresh_logo()
        elif page_name in ["الدفعات", "payments"] and "payments" in self.pages:
            self.pages["payments"].refresh_logo()

    def save_logo_settings(self):
        self._save_settings()

    def closeEvent(self, event):
        self._save_settings()
        event.accept()