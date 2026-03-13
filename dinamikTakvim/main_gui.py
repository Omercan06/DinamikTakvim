

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import tkinter.font as tkFont
from datetime import datetime, timedelta, date
from database import Database
from excel_parser import ExcelParser
from sinav_algoritma import SinavProgramiOlusturucu, OturmaDuzeniOlusturucu
from raporlama import RaporOlusturucu
import os


class ModernButton(tk.Button):
    """Modern görünümlü buton"""
    def __init__(self, parent, **kwargs):
        super().__init__(
            parent,
            relief=tk.FLAT,
            borderwidth=0,
            padx=20,
            pady=10,
            cursor='hand2',
            **kwargs
        )
        
        self.bind('<Enter>', self.on_enter)
        self.bind('<Leave>', self.on_leave)
        
        self.default_bg = kwargs.get('bg', '#3498db')
        self.hover_bg = self._darken_color(self.default_bg)
    
    def _darken_color(self, color):
        """Rengi koyulaştır"""
        # Basit hex renk koyulaştırma
        if color.startswith('#'):
            r = int(color[1:3], 16)
            g = int(color[3:5], 16)
            b = int(color[5:7], 16)
            
            r = max(0, r - 30)
            g = max(0, g - 30)
            b = max(0, b - 30)
            
            return f'#{r:02x}{g:02x}{b:02x}'
        return color
    
    def on_enter(self, e):
        self['background'] = self.hover_bg
    
    def on_leave(self, e):
        self['background'] = self.default_bg


class SinavTakvimiApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Dinamik Sınav Takvimi Oluşturma Sistemi - KOÜ")
        self.root.geometry("1200x700")
        self.root.configure(bg='#ecf0f1')
        
        # Veritabanı bağlantısı
        self.db = Database()
        self.current_user = None
        self.current_bolum_id = None
        
        # Giriş ekranını göster
        self.show_login_screen()
    
    def clear_window(self):
        """Penceredeki tüm widget'ları temizle"""
        for widget in self.root.winfo_children():
            widget.destroy()
    
    def show_login_screen(self):
        """Giriş ekranını göster"""
        self.clear_window()
        
        # Ana frame
        main_frame = tk.Frame(self.root, bg='#ecf0f1')
        main_frame.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
        
        # Başlık
        title_font = tkFont.Font(family="Arial", size=24, weight="bold")
        title = tk.Label(
            main_frame,
            text="Dinamik Sınav Takvimi\nOluşturma Sistemi",
            font=title_font,
            bg='#ecf0f1',
            fg='#2c3e50'
        )
        title.pack(pady=20)
        
        subtitle = tk.Label(
            main_frame,
            text="Kocaeli Üniversitesi",
            font=("Arial", 12),
            bg='#ecf0f1',
            fg='#7f8c8d'
        )
        subtitle.pack(pady=5)
        
        # Giriş formu frame
        login_frame = tk.Frame(main_frame, bg='white', padx=40, pady=40)
        login_frame.pack(pady=30)
        
        # E-posta
        tk.Label(
            login_frame,
            text="E-posta:",
            font=("Arial", 11),
            bg='white'
        ).grid(row=0, column=0, sticky='w', pady=10)
        
        self.email_entry = tk.Entry(
            login_frame,
            font=("Arial", 11),
            width=30
        )
        self.email_entry.grid(row=0, column=1, pady=10, padx=10)
        
        # Şifre
        tk.Label(
            login_frame,
            text="Şifre:",
            font=("Arial", 11),
            bg='white'
        ).grid(row=1, column=0, sticky='w', pady=10)
        
        self.password_entry = tk.Entry(
            login_frame,
            font=("Arial", 11),
            width=30,
            show='*'
        )
        self.password_entry.grid(row=1, column=1, pady=10, padx=10)
        
        # Giriş butonu
        login_btn = ModernButton(
            login_frame,
            text="Giriş Yap",
            font=("Arial", 12, "bold"),
            bg='#3498db',
            fg='white',
            command=self.login
        )
        login_btn.grid(row=2, column=0, columnspan=2, pady=20)
        
        # Enter tuşu ile giriş
        self.password_entry.bind('<Return>', lambda e: self.login())
        
        # Bilgi notu
        info = tk.Label(
            main_frame,
            text="Varsayılan Admin: admin@kocaeli.edu.tr / admin123",
            font=("Arial", 9, "italic"),
            bg='#ecf0f1',
            fg='#95a5a6'
        )
        info.pack(pady=10)
    
    def login(self):
        """Kullanıcı girişini kontrol et"""
        email = self.email_entry.get().strip()
        password = self.password_entry.get().strip()
        
        if not email or not password:
            messagebox.showerror("Hata", "Lütfen tüm alanları doldurun!")
            return
        
        user = self.db.giris_yap(email, password)
        
        if user:
            self.current_user = {
                'id': user[0],
                'email': user[1],
                'rol': user[2],
                'bolum_id': user[3],
                'bolum_adi': user[4]
            }
            
            messagebox.showinfo("Başarılı", f"Hoş geldiniz, {user[2]}!")
            self.show_main_screen()
        else:
            messagebox.showerror("Hata", "E-posta veya şifre hatalı!")
    
    def show_main_screen(self):
        """Ana ekranı göster"""
        self.clear_window()
        
        # Üst bar
        top_bar = tk.Frame(self.root, bg='#2c3e50', height=60)
        top_bar.pack(fill=tk.X)
        
        tk.Label(
            top_bar,
            text=f"Hoş Geldiniz: {self.current_user['email']} ({self.current_user['rol']})",
            font=("Arial", 12),
            bg='#2c3e50',
            fg='white'
        ).pack(side=tk.LEFT, padx=20, pady=15)
        
        if self.current_user['bolum_adi']:
            tk.Label(
                top_bar,
                text=f"Bölüm: {self.current_user['bolum_adi']}",
                font=("Arial", 11),
                bg='#2c3e50',
                fg='#ecf0f1'
            ).pack(side=tk.LEFT, padx=20)
        
        logout_btn = ModernButton(
            top_bar,
            text="Çıkış",
            font=("Arial", 10),
            bg='#e74c3c',
            fg='white',
            command=self.logout
        )
        logout_btn.pack(side=tk.RIGHT, padx=20, pady=10)
        
        # Sol menü
        left_menu = tk.Frame(self.root, bg='#34495e', width=250)
        left_menu.pack(side=tk.LEFT, fill=tk.Y)
        
        tk.Label(
            left_menu,
            text="MENÜ",
            font=("Arial", 14, "bold"),
            bg='#34495e',
            fg='white'
        ).pack(pady=20)
        
        # Menü butonları
        menu_buttons = []
        
        if self.current_user['rol'] == 'Admin':
            menu_buttons = [
                ("👤 Kullanıcı Yönetimi", self.show_user_management),
                ("🏫 Bölüm Seçimi", self.show_department_selection),
            ]
        
        if self.current_user['rol'] == 'Bölüm Koordinatörü' or self.current_user['rol'] == 'Admin':
            menu_buttons.extend([
                ("🏢 Derslik Yönetimi", self.show_classroom_management),
                ("📚 Ders Listesi Yükle", self.show_course_upload),
                ("👨‍🎓 Öğrenci Listesi Yükle", self.show_student_upload),
                ("📋 Öğrenci Listesi", self.show_student_list),
                ("📖 Ders Listesi", self.show_course_list),
                ("📅 Sınav Programı Oluştur", self.show_exam_schedule),
                ("💺 Oturma Düzeni", self.show_seating_arrangement),
            ])
        
        for text, command in menu_buttons:
            btn = tk.Button(
                left_menu,
                text=text,
                font=("Arial", 11),
                bg='#34495e',
                fg='white',
                bd=0,
                padx=20,
                pady=15,
                anchor='w',
                cursor='hand2',
                command=command
            )
            btn.pack(fill=tk.X, padx=10, pady=5)
            
            # Hover efekti
            btn.bind('<Enter>', lambda e, b=btn: b.config(bg='#4a5f7f'))
            btn.bind('<Leave>', lambda e, b=btn: b.config(bg='#34495e'))
        
        # Ana içerik alanı
        self.content_frame = tk.Frame(self.root, bg='#ecf0f1')
        self.content_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Hoş geldiniz mesajı
        welcome_label = tk.Label(
            self.content_frame,
            text="Lütfen sol menüden bir işlem seçin",
            font=("Arial", 16),
            bg='#ecf0f1',
            fg='#7f8c8d'
        )
        welcome_label.pack(expand=True)
    
    def clear_content(self):
        """İçerik alanını temizle"""
        for widget in self.content_frame.winfo_children():
            widget.destroy()
    
    def logout(self):
        """Çıkış yap"""
        self.current_user = None
        self.current_bolum_id = None
        self.show_login_screen()
    
    # Kullanıcı Yönetimi
    def show_user_management(self):
        """Kullanıcı yönetimi ekranı"""
        self.clear_content()
        
        tk.Label(
            self.content_frame,
            text="Kullanıcı Yönetimi",
            font=("Arial", 18, "bold"),
            bg='#ecf0f1'
        ).pack(pady=20)
        
        # Yeni kullanıcı ekleme formu
        form_frame = tk.Frame(self.content_frame, bg='white', padx=30, pady=30)
        form_frame.pack(pady=20)
        
        tk.Label(form_frame, text="Yeni Kullanıcı Ekle", font=("Arial", 14, "bold"), bg='white').grid(
            row=0, column=0, columnspan=2, pady=10
        )
        
        tk.Label(form_frame, text="E-posta:", bg='white').grid(row=1, column=0, sticky='w', pady=5)
        email_entry = tk.Entry(form_frame, width=30)
        email_entry.grid(row=1, column=1, pady=5, padx=10)
        
        tk.Label(form_frame, text="Şifre:", bg='white').grid(row=2, column=0, sticky='w', pady=5)
        password_entry = tk.Entry(form_frame, width=30, show='*')
        password_entry.grid(row=2, column=1, pady=5, padx=10)
        
        tk.Label(form_frame, text="Rol:", bg='white').grid(row=3, column=0, sticky='w', pady=5)
        rol_var = tk.StringVar(value="Bölüm Koordinatörü")
        rol_combo = ttk.Combobox(form_frame, textvariable=rol_var, width=28, state='readonly')
        rol_combo['values'] = ('Admin', 'Bölüm Koordinatörü')
        rol_combo.grid(row=3, column=1, pady=5, padx=10)
        
        tk.Label(form_frame, text="Bölüm:", bg='white').grid(row=4, column=0, sticky='w', pady=5)
        bolumler = self.db.get_bolumler()
        bolum_dict = {b[1]: b[0] for b in bolumler}
        bolum_var = tk.StringVar()
        bolum_combo = ttk.Combobox(form_frame, textvariable=bolum_var, width=28, state='readonly')
        bolum_combo['values'] = list(bolum_dict.keys())
        bolum_combo.grid(row=4, column=1, pady=5, padx=10)
        
        def add_user():
            email = email_entry.get().strip()
            password = password_entry.get().strip()
            rol = rol_var.get()
            bolum_adi = bolum_var.get()
            
            if not email or not password:
                messagebox.showerror("Hata", "Lütfen tüm alanları doldurun!")
                return
            
            bolum_id = bolum_dict.get(bolum_adi) if bolum_adi else None
            
            basari, mesaj = self.db.kullanici_ekle(email, password, rol, bolum_id)
            
            if basari:
                messagebox.showinfo("Başarılı", mesaj)
                email_entry.delete(0, tk.END)
                password_entry.delete(0, tk.END)
            else:
                messagebox.showerror("Hata", mesaj)
        
        ModernButton(
            form_frame,
            text="Kullanıcı Ekle",
            bg='#27ae60',
            fg='white',
            command=add_user
        ).grid(row=5, column=0, columnspan=2, pady=20)
    
    # Bölüm Seçimi (Admin için)
    def show_department_selection(self):
        """Bölüm seçimi ekranı"""
        self.clear_content()
        
        tk.Label(
            self.content_frame,
            text="Bölüm Seçimi",
            font=("Arial", 18, "bold"),
            bg='#ecf0f1'
        ).pack(pady=20)
        
        tk.Label(
            self.content_frame,
            text="Yönetmek istediğiniz bölümü seçin:",
            font=("Arial", 12),
            bg='#ecf0f1'
        ).pack(pady=10)
        
        bolumler = self.db.get_bolumler()
        
        for bolum in bolumler:
            btn = ModernButton(
                self.content_frame,
                text=f"{bolum[1]} ({bolum[2]})",
                font=("Arial", 12),
                bg='#3498db',
                fg='white',
                width=30,
                command=lambda b=bolum: self.select_department(b)
            )
            btn.pack(pady=10)
    
    def select_department(self, bolum):
        """Bölüm seç"""
        self.current_user['bolum_id'] = bolum[0]
        self.current_user['bolum_adi'] = bolum[1]
        messagebox.showinfo("Başarılı", f"{bolum[1]} seçildi")
        self.show_main_screen()
    
    # Derslik Yönetimi
    def show_classroom_management(self):
        """Derslik yönetimi ekranı"""
        if not self.current_user.get('bolum_id'):
            messagebox.showerror("Hata", "Lütfen önce bir bölüm seçin!")
            return
        
        self.clear_content()
        
        tk.Label(
            self.content_frame,
            text="Derslik Yönetimi",
            font=("Arial", 18, "bold"),
            bg='#ecf0f1'
        ).pack(pady=20)
        
        # Derslik ekleme formu
        form_frame = tk.Frame(self.content_frame, bg='white', padx=30, pady=30)
        form_frame.pack(pady=20)
        
        entries = {}
        fields = [
            ('Derslik Kodu:', 'kod'),
            ('Derslik Adı:', 'adi'),
            ('Kapasite:', 'kapasite'),
            ('Enine Sıra Sayısı:', 'enine'),
            ('Boyuna Sıra Sayısı:', 'boyuna'),
            ('Sıra Yapısı (2 veya 3):', 'yapisi')
        ]
        
        for i, (label, key) in enumerate(fields):
            tk.Label(form_frame, text=label, bg='white').grid(row=i, column=0, sticky='w', pady=5)
            entry = tk.Entry(form_frame, width=30)
            entry.grid(row=i, column=1, pady=5, padx=10)
            entries[key] = entry
        
        def add_classroom():
            try:
                kod = entries['kod'].get().strip()
                adi = entries['adi'].get().strip()
                kapasite = int(entries['kapasite'].get())
                enine = int(entries['enine'].get())
                boyuna = int(entries['boyuna'].get())
                yapisi = int(entries['yapisi'].get())
                
                if yapisi not in [2, 3]:
                    messagebox.showerror("Hata", "Sıra yapısı 2 veya 3 olmalıdır!")
                    return
                
                basari, mesaj = self.db.derslik_ekle(
                    self.current_user['bolum_id'],
                    kod, adi, kapasite, enine, boyuna, yapisi
                )
                
                if basari:
                    messagebox.showinfo("Başarılı", mesaj)
                    for entry in entries.values():
                        entry.delete(0, tk.END)
                    self.show_classroom_list()
                else:
                    messagebox.showerror("Hata", mesaj)
            except ValueError:
                messagebox.showerror("Hata", "Lütfen sayısal değerleri doğru girin!")
        
        ModernButton(
            form_frame,
            text="Derslik Ekle",
            bg='#27ae60',
            fg='white',
            command=add_classroom
        ).grid(row=len(fields), column=0, columnspan=2, pady=20)
        
        # Derslik listesi
        self.show_classroom_list()
    
    def show_classroom_list(self):
        """Derslik listesini göster"""
        # Liste frame'i oluştur veya güncelle
        for widget in self.content_frame.winfo_children():
            if isinstance(widget, tk.Frame) and widget != self.content_frame.winfo_children()[0]:
                if len(widget.winfo_children()) > 0:
                    if isinstance(widget.winfo_children()[0], ttk.Treeview):
                        widget.destroy()
        
        list_frame = tk.Frame(self.content_frame, bg='white', padx=20, pady=20)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=20)
        
        tk.Label(
            list_frame,
            text="Mevcut Derslikler",
            font=("Arial", 14, "bold"),
            bg='white'
        ).pack(pady=10)
        
        # Treeview
        columns = ('Kod', 'Ad', 'Kapasite', 'Enine', 'Boyuna', 'Yapı')
        tree = ttk.Treeview(list_frame, columns=columns, show='headings', height=10)
        
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=100)
        
        # Derslikleri yükle
        derslikler = self.db.get_derslikler(self.current_user['bolum_id'])
        for derslik in derslikler:
            tree.insert('', tk.END, values=(
                derslik[2],  # derslik_kodu
                derslik[3],  # derslik_adi
                derslik[4],  # kapasite
                derslik[5],  # enine_sira
                derslik[6],  # boyuna_sira
                derslik[7]   # sira_yapisi
            ))
        
        tree.pack(fill=tk.BOTH, expand=True)
    
    # Ders Listesi Yükleme
    def show_course_upload(self):
        """Ders listesi yükleme ekranı"""
        if not self.current_user.get('bolum_id'):
            messagebox.showerror("Hata", "Lütfen önce bir bölüm seçin!")
            return
        
        self.clear_content()
        
        tk.Label(
            self.content_frame,
            text="Ders Listesi Yükle",
            font=("Arial", 18, "bold"),
            bg='#ecf0f1'
        ).pack(pady=20)
        
        info_frame = tk.Frame(self.content_frame, bg='white', padx=40, pady=40)
        info_frame.pack(pady=30)
        
        tk.Label(
            info_frame,
            text="Excel dosyası seçin ve yükleyin",
            font=("Arial", 12),
            bg='white'
        ).pack(pady=20)
        
        def upload_courses():
            file_path = filedialog.askopenfilename(
                title="Ders Listesi Excel Dosyası Seçin",
                filetypes=[("Excel files", "*.xlsx *.xls")]
            )
            
            if file_path:
                parser = ExcelParser(self.db)
                basari, mesaj, hatalar = parser.ders_listesi_yukle(
                    file_path,
                    self.current_user['bolum_id']
                )
                
                if basari:
                    messagebox.showinfo("Başarılı", mesaj)
                    if hatalar:
                        hata_mesaji = "\n".join(hatalar[:10])
                        messagebox.showwarning("Uyarılar", f"Bazı hatalar oluştu:\n{hata_mesaji}")
                else:
                    messagebox.showerror("Hata", mesaj)
        
        ModernButton(
            info_frame,
            text="Excel Dosyası Seç ve Yükle",
            bg='#3498db',
            fg='white',
            command=upload_courses
        ).pack(pady=10)
    
    # Öğrenci Listesi Yükleme
    def show_student_upload(self):
        """Öğrenci listesi yükleme ekranı"""
        if not self.current_user.get('bolum_id'):
            messagebox.showerror("Hata", "Lütfen önce bir bölüm seçin!")
            return
        
        self.clear_content()
        
        tk.Label(
            self.content_frame,
            text="Öğrenci Listesi Yükle",
            font=("Arial", 18, "bold"),
            bg='#ecf0f1'
        ).pack(pady=20)
        
        info_frame = tk.Frame(self.content_frame, bg='white', padx=40, pady=40)
        info_frame.pack(pady=30)
        
        tk.Label(
            info_frame,
            text="Excel dosyası seçin ve yükleyin",
            font=("Arial", 12),
            bg='white'
        ).pack(pady=20)
        
        def upload_students():
            file_path = filedialog.askopenfilename(
                title="Öğrenci Listesi Excel Dosyası Seçin",
                filetypes=[("Excel files", "*.xlsx *.xls")]
            )
            
            if file_path:
                parser = ExcelParser(self.db)
                basari, mesaj, hatalar = parser.ogrenci_listesi_yukle(
                    file_path,
                    self.current_user['bolum_id']
                )
                
                if basari:
                    messagebox.showinfo("Başarılı", mesaj)
                    if hatalar:
                        hata_mesaji = "\n".join(hatalar[:10])
                        messagebox.showwarning("Uyarılar", f"Bazı hatalar oluştu:\n{hata_mesaji}")
                else:
                    messagebox.showerror("Hata", mesaj)
        
        ModernButton(
            info_frame,
            text="Excel Dosyası Seç ve Yükle",
            bg='#3498db',
            fg='white',
            command=upload_students
        ).pack(pady=10)
    
    # Öğrenci Listesi
    def show_student_list(self):
        """Öğrenci listesi ekranı"""
        if not self.current_user.get('bolum_id'):
            messagebox.showerror("Hata", "Lütfen önce bir bölüm seçin!")
            return
        
        self.clear_content()
        
        tk.Label(
            self.content_frame,
            text="Öğrenci Listesi",
            font=("Arial", 18, "bold"),
            bg='#ecf0f1'
        ).pack(pady=20)
        
        # Arama formu
        search_frame = tk.Frame(self.content_frame, bg='white', padx=30, pady=20)
        search_frame.pack(pady=10)
        
        tk.Label(search_frame, text="Öğrenci No:", bg='white').pack(side=tk.LEFT, padx=5)
        search_entry = tk.Entry(search_frame, width=20)
        search_entry.pack(side=tk.LEFT, padx=5)
        
        result_text = tk.Text(self.content_frame, width=80, height=20, wrap=tk.WORD)
        result_text.pack(pady=20)
        
        def search_student():
            ogrenci_no = search_entry.get().strip()
            if not ogrenci_no:
                messagebox.showerror("Hata", "Lütfen öğrenci numarası girin!")
                return
            
            ogrenci = self.db.get_ogrenci_by_no(self.current_user['bolum_id'], ogrenci_no)
            
            if ogrenci:
                dersler = self.db.get_ogrenci_dersleri(ogrenci[0])
                
                result_text.delete(1.0, tk.END)
                result_text.insert(tk.END, f"Öğrenci: {ogrenci[3]}\n")
                result_text.insert(tk.END, f"Numara: {ogrenci[2]}\n")
                result_text.insert(tk.END, f"Sınıf: {ogrenci[4]}\n\n")
                result_text.insert(tk.END, "Aldığı Dersler:\n")
                result_text.insert(tk.END, "-" * 50 + "\n")
                
                for ders in dersler:
                    result_text.insert(tk.END, f"- {ders[2]} - {ders[3]}\n")
            else:
                messagebox.showinfo("Bilgi", "Öğrenci bulunamadı!")
        
        ModernButton(
            search_frame,
            text="Ara",
            bg='#3498db',
            fg='white',
            command=search_student
        ).pack(side=tk.LEFT, padx=5)
    
    # Ders Listesi
    def show_course_list(self):
        """Ders listesi ekranı"""
        if not self.current_user.get('bolum_id'):
            messagebox.showerror("Hata", "Lütfen önce bir bölüm seçin!")
            return
        
        self.clear_content()
        
        tk.Label(
            self.content_frame,
            text="Ders Listesi",
            font=("Arial", 18, "bold"),
            bg='#ecf0f1'
        ).pack(pady=20)
        
        # İki sütunlu düzen
        main_container = tk.Frame(self.content_frame, bg='#ecf0f1')
        main_container.pack(fill=tk.BOTH, expand=True)
        
        # Sol: Ders listesi
        left_frame = tk.Frame(main_container, bg='white', padx=20, pady=20)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        tk.Label(
            left_frame,
            text="Dersler",
            font=("Arial", 14, "bold"),
            bg='white'
        ).pack(pady=10)
        
        # Listbox ile dersler
        ders_listbox = tk.Listbox(left_frame, height=25, font=("Arial", 10))
        ders_listbox.pack(fill=tk.BOTH, expand=True)
        
        scrollbar = tk.Scrollbar(left_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        ders_listbox.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=ders_listbox.yview)
        
        # Dersler yükle
        dersler = self.db.get_dersler(self.current_user['bolum_id'])
        ders_dict = {}
        for ders in dersler:
            ders_dict[ders[0]] = ders
            ders_listbox.insert(tk.END, f"{ders[2]} - {ders[3]}")
        
        # Sağ: Dersi alan öğrenciler
        right_frame = tk.Frame(main_container, bg='white', padx=20, pady=20)
        right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        tk.Label(
            right_frame,
            text="Dersi Alan Öğrenciler",
            font=("Arial", 14, "bold"),
            bg='white'
        ).pack(pady=10)
        
        ogrenci_text = tk.Text(right_frame, wrap=tk.WORD)
        ogrenci_text.pack(fill=tk.BOTH, expand=True)
        
        def show_students(event):
            selection = ders_listbox.curselection()
            if selection:
                index = selection[0]
                ders_id = list(ders_dict.keys())[index]
                ders = ders_dict[ders_id]
                
                ogrenciler = self.db.get_dersi_alan_ogrenciler(ders_id)
                
                ogrenci_text.delete(1.0, tk.END)
                ogrenci_text.insert(tk.END, f"Ders: {ders[2]} - {ders[3]}\n")
                ogrenci_text.insert(tk.END, f"Öğretim Elemanı: {ders[4]}\n")
                ogrenci_text.insert(tk.END, f"Sınıf: {ders[5]}\n\n")
                ogrenci_text.insert(tk.END, f"Dersi Alan Öğrenciler ({len(ogrenciler)}):\n")
                ogrenci_text.insert(tk.END, "-" * 50 + "\n")
                
                for ogr in ogrenciler:
                    ogrenci_text.insert(tk.END, f"{ogr[2]} - {ogr[3]}\n")
        
        ders_listbox.bind('<<ListboxSelect>>', show_students)
    
    # Sınav Programı Oluşturma (devamı bir sonraki mesajda)
    def show_exam_schedule(self):
        """Sınav programı oluşturma ekranı"""
        if not self.current_user.get('bolum_id'):
            messagebox.showerror("Hata", "Lütfen önce bir bölüm seçin!")
            return
        
        self.clear_content()
        
        tk.Label(
            self.content_frame,
            text="Sınav Programı Oluştur",
            font=("Arial", 18, "bold"),
            bg='#ecf0f1'
        ).pack(pady=20)
        
        # Kısıtlar formu
        form_frame = tk.Frame(self.content_frame, bg='white', padx=40, pady=30)
        form_frame.pack(pady=20, fill=tk.BOTH, expand=True)
        
        # Sınav türü
        tk.Label(form_frame, text="Sınav Türü:", bg='white', font=("Arial", 11)).grid(
            row=0, column=0, sticky='w', pady=10
        )
        sinav_turu_var = tk.StringVar(value="Vize")
        sinav_turu_combo = ttk.Combobox(
            form_frame, textvariable=sinav_turu_var, width=28, state='readonly'
        )
        sinav_turu_combo['values'] = ('Vize', 'Final', 'Bütünleme')
        sinav_turu_combo.grid(row=0, column=1, pady=10, padx=10)
        
        # Tarih aralığı
        tk.Label(form_frame, text="Başlangıç Tarihi (GG.AA.YYYY):", bg='white', font=("Arial", 11)).grid(
            row=1, column=0, sticky='w', pady=10
        )
        baslangic_entry = tk.Entry(form_frame, width=30)
        baslangic_entry.grid(row=1, column=1, pady=10, padx=10)
        baslangic_entry.insert(0, (date.today() + timedelta(days=7)).strftime('%d.%m.%Y'))
        
        tk.Label(form_frame, text="Bitiş Tarihi (GG.AA.YYYY):", bg='white', font=("Arial", 11)).grid(
            row=2, column=0, sticky='w', pady=10
        )
        bitis_entry = tk.Entry(form_frame, width=30)
        bitis_entry.grid(row=2, column=1, pady=10, padx=10)
        bitis_entry.insert(0, (date.today() + timedelta(days=21)).strftime('%d.%m.%Y'))
        
        # Varsayılan sınav süresi
        tk.Label(form_frame, text="Varsayılan Sınav Süresi (dk):", bg='white', font=("Arial", 11)).grid(
            row=3, column=0, sticky='w', pady=10
        )
        sure_entry = tk.Entry(form_frame, width=30)
        sure_entry.grid(row=3, column=1, pady=10, padx=10)
        sure_entry.insert(0, "75")
        
        # Bekleme süresi
        tk.Label(form_frame, text="Bekleme Süresi (dk):", bg='white', font=("Arial", 11)).grid(
            row=4, column=0, sticky='w', pady=10
        )
        bekleme_entry = tk.Entry(form_frame, width=30)
        bekleme_entry.grid(row=4, column=1, pady=10, padx=10)
        bekleme_entry.insert(0, "15")
        
        # Aynı anda sınav yapılamaz
        ayni_anda_var = tk.BooleanVar(value=True)
        tk.Checkbutton(
            form_frame,
            text="Sınavlar aynı anda yapılamaz (bir sınav bitene kadar diğeri başlamasın)",
            variable=ayni_anda_var,
            bg='white',
            font=("Arial", 10)
        ).grid(row=5, column=0, columnspan=2, pady=10)
        
        # Program oluştur butonu
        def create_schedule():
            try:
                baslangic = datetime.strptime(baslangic_entry.get(), '%d.%m.%Y')
                bitis = datetime.strptime(bitis_entry.get(), '%d.%m.%Y')
                sure = int(sure_entry.get())
                bekleme = int(bekleme_entry.get())
                
                # Tüm dersleri dahil et
                dersler = self.db.get_dersler(self.current_user['bolum_id'])
                dahil_dersler = [d[0] for d in dersler]
                
                if not dahil_dersler:
                    messagebox.showerror("Hata", "Ders listesi bulunamadı! Önce ders yüklemelisiniz.")
                    return
                
                kisitlar = {
                    'dahil_dersler': dahil_dersler,
                    'baslangic_tarihi': baslangic,
                    'bitis_tarihi': bitis,
                    'tatil_gunleri': [5, 6],  # Cumartesi, Pazar
                    'sinav_turu': sinav_turu_var.get(),
                    'varsayilan_sure': sure,
                    'ozel_sureler': {},
                    'bekleme_suresi': bekleme,
                    'ayni_anda_yapilamaz': ayni_anda_var.get()
                }
                
                olusturucu = SinavProgramiOlusturucu(self.db)
                basari, mesaj = olusturucu.program_olustur(
                    self.current_user['bolum_id'],
                    kisitlar
                )
                
                if basari:
                    messagebox.showinfo("Başarılı", mesaj)
                    
                    # Excel raporu oluştur
                    rapor = RaporOlusturucu(self.db)
                    excel_dosya = filedialog.asksaveasfilename(
                        defaultextension=".xlsx",
                        filetypes=[("Excel files", "*.xlsx")],
                        initialfile=f"sinav_programi_{datetime.now().strftime('%Y%m%d')}.xlsx"
                    )
                    
                    if excel_dosya:
                        basari_excel, mesaj_excel = rapor.sinav_programi_excel(
                            self.current_user['bolum_id'],
                            excel_dosya
                        )
                        if basari_excel:
                            messagebox.showinfo("Başarılı", mesaj_excel)
                else:
                    hatalar = "\n".join(olusturucu.get_hatalar()[:5])
                    messagebox.showerror("Hata", f"{mesaj}\n\nHatalar:\n{hatalar}")
            
            except ValueError as e:
                messagebox.showerror("Hata", f"Tarih formatı hatalı! GG.AA.YYYY formatında girin.\n{str(e)}")
        
        ModernButton(
            form_frame,
            text="Programı Oluştur ve İndir",
            bg='#27ae60',
            fg='white',
            font=("Arial", 12, "bold"),
            command=create_schedule
        ).grid(row=6, column=0, columnspan=2, pady=30)
    
    # Oturma Düzeni
    def show_seating_arrangement(self):
        """Oturma düzeni ekranı"""
        if not self.current_user.get('bolum_id'):
            messagebox.showerror("Hata", "Lütfen önce bir bölüm seçin!")
            return
        
        self.clear_content()
        
        tk.Label(
            self.content_frame,
            text="Oturma Düzeni",
            font=("Arial", 18, "bold"),
            bg='#ecf0f1'
        ).pack(pady=20)
        
        # Sınav programını al
        sinavlar = self.db.get_sinav_programi(self.current_user['bolum_id'])
        
        if not sinavlar:
            tk.Label(
                self.content_frame,
                text="Henüz sınav programı oluşturulmamış!",
                font=("Arial", 12),
                bg='#ecf0f1',
                fg='#e74c3c'
            ).pack(pady=50)
            return
        
        # Sınav listesi
        list_frame = tk.Frame(self.content_frame, bg='white', padx=30, pady=30)
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        tk.Label(
            list_frame,
            text="Sınavlar",
            font=("Arial", 14, "bold"),
            bg='white'
        ).pack(pady=10)
        
        # Treeview
        columns = ('Tarih', 'Saat', 'Ders', 'Derslik')
        tree = ttk.Treeview(list_frame, columns=columns, show='headings', height=15)
        
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=150)
        
        sinav_dict = {}
        for sinav in sinavlar:
            tree.insert('', tk.END, values=(
                sinav[4],  # tarih
                sinav[5],  # baslangic
                f"{sinav[9]} - {sinav[10]}",  # ders
                sinav[11]  # derslik
            ))
            sinav_dict[len(sinav_dict)] = sinav
        
        tree.pack(fill=tk.BOTH, expand=True, pady=10)
        
        def create_seating():
            selection = tree.selection()
            if not selection:
                messagebox.showerror("Hata", "Lütfen bir sınav seçin!")
                return
            
            index = tree.index(selection[0])
            sinav = sinav_dict[index]
            sinav_id = sinav[0]
            
            olusturucu = OturmaDuzeniOlusturucu(self.db)
            basari, mesaj = olusturucu.oturma_olustur(sinav_id)
            
            if basari:
                messagebox.showinfo("Başarılı", mesaj)
                
                # PDF raporu oluştur
                rapor = RaporOlusturucu(self.db)
                pdf_dosya = filedialog.asksaveasfilename(
                    defaultextension=".pdf",
                    filetypes=[("PDF files", "*.pdf")],
                    initialfile=f"oturma_duzeni_{sinav[9]}_{datetime.now().strftime('%Y%m%d')}.pdf"
                )
                
                if pdf_dosya:
                    basari_pdf, mesaj_pdf = rapor.oturma_duzeni_pdf(sinav_id, pdf_dosya)
                    if basari_pdf:
                        messagebox.showinfo("Başarılı", mesaj_pdf)
            else:
                messagebox.showerror("Hata", mesaj)
        
        ModernButton(
            list_frame,
            text="Oturma Düzeni Oluştur ve PDF İndir",
            bg='#3498db',
            fg='white',
            font=("Arial", 11, "bold"),
            command=create_seating
        ).pack(pady=20)


def main():
    root = tk.Tk()
    app = SinavTakvimiApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()

