

import sqlite3
from datetime import datetime
import hashlib
import os


class Database:
    def __init__(self, db_name="sinav_takvimi.db"):
        self.db_name = db_name
        self.conn = None
        self.cursor = None
        self.connect()
        self.create_tables()
        self.initialize_default_data()
    
    def connect(self):
        """Veritabanına bağlan"""
        self.conn = sqlite3.connect(self.db_name)
        self.cursor = self.conn.cursor()
        self.conn.execute("PRAGMA foreign_keys = ON")
    
    def close(self):
        """Veritabanı bağlantısını kapat"""
        if self.conn:
            self.conn.close()
    
    def create_tables(self):
        """Tüm tabloları oluştur"""
        
        # Kullanıcılar tablosu
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS kullanicilar (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                sifre TEXT NOT NULL,
                rol TEXT NOT NULL,
                bolum_id INTEGER,
                aktif INTEGER DEFAULT 1,
                olusturma_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (bolum_id) REFERENCES bolumler(id)
            )
        ''')
        
        # Bölümler tablosu
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS bolumler (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                bolum_adi TEXT UNIQUE NOT NULL,
                bolum_kodu TEXT UNIQUE NOT NULL,
                aktif INTEGER DEFAULT 1
            )
        ''')
        
        # Derslikler tablosu
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS derslikler (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                bolum_id INTEGER NOT NULL,
                derslik_kodu TEXT NOT NULL,
                derslik_adi TEXT NOT NULL,
                kapasite INTEGER NOT NULL,
                enine_sira INTEGER NOT NULL,
                boyuna_sira INTEGER NOT NULL,
                sira_yapisi INTEGER NOT NULL,
                aktif INTEGER DEFAULT 1,
                FOREIGN KEY (bolum_id) REFERENCES bolumler(id),
                UNIQUE(bolum_id, derslik_kodu)
            )
        ''')
        
        # Dersler tablosu
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS dersler (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                bolum_id INTEGER NOT NULL,
                ders_kodu TEXT NOT NULL,
                ders_adi TEXT NOT NULL,
                ogretim_elemani TEXT NOT NULL,
                sinif TEXT NOT NULL,
                ders_turu TEXT,
                sinav_suresi INTEGER DEFAULT 75,
                aktif INTEGER DEFAULT 1,
                FOREIGN KEY (bolum_id) REFERENCES bolumler(id),
                UNIQUE(bolum_id, ders_kodu)
            )
        ''')
        
        # Öğrenciler tablosu
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS ogrenciler (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                bolum_id INTEGER NOT NULL,
                ogrenci_no TEXT NOT NULL,
                ad_soyad TEXT NOT NULL,
                sinif TEXT NOT NULL,
                aktif INTEGER DEFAULT 1,
                FOREIGN KEY (bolum_id) REFERENCES bolumler(id),
                UNIQUE(bolum_id, ogrenci_no)
            )
        ''')
        
        # Öğrenci-Ders ilişkisi tablosu
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS ogrenci_ders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ogrenci_id INTEGER NOT NULL,
                ders_id INTEGER NOT NULL,
                FOREIGN KEY (ogrenci_id) REFERENCES ogrenciler(id),
                FOREIGN KEY (ders_id) REFERENCES dersler(id),
                UNIQUE(ogrenci_id, ders_id)
            )
        ''')
        
        # Sınav Programı tablosu
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS sinav_programi (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                bolum_id INTEGER NOT NULL,
                ders_id INTEGER NOT NULL,
                derslik_id INTEGER NOT NULL,
                tarih DATE NOT NULL,
                baslangic_saati TIME NOT NULL,
                bitis_saati TIME NOT NULL,
                sinav_turu TEXT NOT NULL,
                olusturma_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (bolum_id) REFERENCES bolumler(id),
                FOREIGN KEY (ders_id) REFERENCES dersler(id),
                FOREIGN KEY (derslik_id) REFERENCES derslikler(id)
            )
        ''')
        
        # Oturma Düzeni tablosu
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS oturma_duzeni (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sinav_id INTEGER NOT NULL,
                ogrenci_id INTEGER NOT NULL,
                derslik_id INTEGER NOT NULL,
                sira_no INTEGER NOT NULL,
                sutun_no INTEGER NOT NULL,
                FOREIGN KEY (sinav_id) REFERENCES sinav_programi(id),
                FOREIGN KEY (ogrenci_id) REFERENCES ogrenciler(id),
                FOREIGN KEY (derslik_id) REFERENCES derslikler(id)
            )
        ''')
        
        self.conn.commit()
    
    def hash_password(self, password):
        """Şifreyi hash'le"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def initialize_default_data(self):
        """Varsayılan verileri oluştur (Admin kullanıcı ve bölümler)"""
        
        # Bölümleri ekle
        bolumler = [
            ('Bilgisayar Mühendisliği', 'BLM'),
            ('Yazılım Mühendisliği', 'YZM'),
            ('Elektrik Mühendisliği', 'ELK'),
            ('Elektronik Mühendisliği', 'ELN'),
            ('İnşaat Mühendisliği', 'INS')
        ]
        
        for bolum_adi, bolum_kodu in bolumler:
            try:
                self.cursor.execute('''
                    INSERT OR IGNORE INTO bolumler (bolum_adi, bolum_kodu)
                    VALUES (?, ?)
                ''', (bolum_adi, bolum_kodu))
            except:
                pass
        
        # Admin kullanıcıyı ekle
        try:
            admin_sifre = self.hash_password("admin123")
            self.cursor.execute('''
                INSERT OR IGNORE INTO kullanicilar (email, sifre, rol, bolum_id)
                VALUES (?, ?, ?, ?)
            ''', ("admin@kocaeli.edu.tr", admin_sifre, "Admin", None))
        except:
            pass
        
        # Bilgisayar Mühendisliği için varsayılan derslikleri ekle
        try:
            self.cursor.execute("SELECT id FROM bolumler WHERE bolum_kodu = 'BLM'")
            blm_id = self.cursor.fetchone()
            if blm_id:
                blm_id = blm_id[0]
                derslikler = [
                    (blm_id, '3001', '301', 42, 3, 7, 3),
                    (blm_id, '3002', 'Büyük Amfi', 48, 3, 8, 4),
                    (blm_id, '3003', '303', 42, 3, 7, 3),
                    (blm_id, '3004', 'EDA', 30, 5, 6, 2),
                    (blm_id, '3005', '305', 42, 3, 7, 3)
                ]
                
                for derslik in derslikler:
                    try:
                        self.cursor.execute('''
                            INSERT OR IGNORE INTO derslikler 
                            (bolum_id, derslik_kodu, derslik_adi, kapasite, 
                             enine_sira, boyuna_sira, sira_yapisi)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                        ''', derslik)
                    except:
                        pass
        except:
            pass
        
        self.conn.commit()
    
    # Kullanıcı işlemleri
    def giris_yap(self, email, sifre):
        """Kullanıcı girişi"""
        hashed_sifre = self.hash_password(sifre)
        self.cursor.execute('''
            SELECT k.id, k.email, k.rol, k.bolum_id, b.bolum_adi
            FROM kullanicilar k
            LEFT JOIN bolumler b ON k.bolum_id = b.id
            WHERE k.email = ? AND k.sifre = ? AND k.aktif = 1
        ''', (email, hashed_sifre))
        
        return self.cursor.fetchone()
    
    def kullanici_ekle(self, email, sifre, rol, bolum_id=None):
        """Yeni kullanıcı ekle"""
        try:
            hashed_sifre = self.hash_password(sifre)
            self.cursor.execute('''
                INSERT INTO kullanicilar (email, sifre, rol, bolum_id)
                VALUES (?, ?, ?, ?)
            ''', (email, hashed_sifre, rol, bolum_id))
            self.conn.commit()
            return True, "Kullanıcı başarıyla eklendi"
        except sqlite3.IntegrityError:
            return False, "Bu e-posta adresi zaten kullanılıyor"
        except Exception as e:
            return False, f"Hata: {str(e)}"
    
    # Bölüm işlemleri
    def get_bolumler(self):
        """Tüm bölümleri getir"""
        self.cursor.execute("SELECT * FROM bolumler WHERE aktif = 1")
        return self.cursor.fetchall()
    
    def get_bolum_by_id(self, bolum_id):
        """ID'ye göre bölüm getir"""
        self.cursor.execute("SELECT * FROM bolumler WHERE id = ?", (bolum_id,))
        return self.cursor.fetchone()
    
    # Derslik işlemleri
    def derslik_ekle(self, bolum_id, derslik_kodu, derslik_adi, kapasite, 
                     enine_sira, boyuna_sira, sira_yapisi):
        """Yeni derslik ekle"""
        try:
            self.cursor.execute('''
                INSERT INTO derslikler 
                (bolum_id, derslik_kodu, derslik_adi, kapasite, 
                 enine_sira, boyuna_sira, sira_yapisi)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (bolum_id, derslik_kodu, derslik_adi, kapasite, 
                  enine_sira, boyuna_sira, sira_yapisi))
            self.conn.commit()
            return True, "Derslik başarıyla eklendi"
        except sqlite3.IntegrityError:
            return False, "Bu derslik kodu zaten mevcut"
        except Exception as e:
            return False, f"Hata: {str(e)}"
    
    def derslik_guncelle(self, derslik_id, derslik_adi, kapasite, 
                         enine_sira, boyuna_sira, sira_yapisi):
        """Derslik bilgilerini güncelle"""
        try:
            self.cursor.execute('''
                UPDATE derslikler 
                SET derslik_adi = ?, kapasite = ?, enine_sira = ?, 
                    boyuna_sira = ?, sira_yapisi = ?
                WHERE id = ?
            ''', (derslik_adi, kapasite, enine_sira, boyuna_sira, 
                  sira_yapisi, derslik_id))
            self.conn.commit()
            return True, "Derslik başarıyla güncellendi"
        except Exception as e:
            return False, f"Hata: {str(e)}"
    
    def derslik_sil(self, derslik_id):
        """Dersliği sil (soft delete)"""
        try:
            self.cursor.execute('''
                UPDATE derslikler SET aktif = 0 WHERE id = ?
            ''', (derslik_id,))
            self.conn.commit()
            return True, "Derslik başarıyla silindi"
        except Exception as e:
            return False, f"Hata: {str(e)}"
    
    def get_derslikler(self, bolum_id):
        """Bölüme göre derslikleri getir"""
        self.cursor.execute('''
            SELECT * FROM derslikler 
            WHERE bolum_id = ? AND aktif = 1
        ''', (bolum_id,))
        return self.cursor.fetchall()
    
    def get_derslik_by_kod(self, bolum_id, derslik_kodu):
        """Derslik koduna göre derslik getir"""
        self.cursor.execute('''
            SELECT * FROM derslikler 
            WHERE bolum_id = ? AND derslik_kodu = ? AND aktif = 1
        ''', (bolum_id, derslik_kodu))
        return self.cursor.fetchone()
    
    # Ders işlemleri
    def ders_ekle(self, bolum_id, ders_kodu, ders_adi, ogretim_elemani, 
                  sinif, ders_turu="Zorunlu", sinav_suresi=75):
        """Yeni ders ekle"""
        try:
            self.cursor.execute('''
                INSERT INTO dersler 
                (bolum_id, ders_kodu, ders_adi, ogretim_elemani, 
                 sinif, ders_turu, sinav_suresi)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (bolum_id, ders_kodu, ders_adi, ogretim_elemani, 
                  sinif, ders_turu, sinav_suresi))
            self.conn.commit()
            return True, self.cursor.lastrowid
        except sqlite3.IntegrityError:
            # Ders zaten varsa ID'sini döndür
            self.cursor.execute('''
                SELECT id FROM dersler 
                WHERE bolum_id = ? AND ders_kodu = ?
            ''', (bolum_id, ders_kodu))
            result = self.cursor.fetchone()
            return True, result[0] if result else None
        except Exception as e:
            return False, f"Hata: {str(e)}"
    
    def get_dersler(self, bolum_id):
        """Bölüme göre dersleri getir"""
        self.cursor.execute('''
            SELECT * FROM dersler 
            WHERE bolum_id = ? AND aktif = 1
            ORDER BY sinif, ders_kodu
        ''', (bolum_id,))
        return self.cursor.fetchall()
    
    def get_ders_by_kod(self, bolum_id, ders_kodu):
        """Ders koduna göre ders getir"""
        self.cursor.execute('''
            SELECT * FROM dersler 
            WHERE bolum_id = ? AND ders_kodu = ? AND aktif = 1
        ''', (bolum_id, ders_kodu))
        return self.cursor.fetchone()
    
    def ders_sil(self, ders_id):
        """Dersi sil (soft delete)"""
        try:
            self.cursor.execute('''
                UPDATE dersler SET aktif = 0 WHERE id = ?
            ''', (ders_id,))
            self.conn.commit()
            return True, "Ders başarıyla silindi"
        except Exception as e:
            return False, f"Hata: {str(e)}"
    
    # Öğrenci işlemleri
    def ogrenci_ekle(self, bolum_id, ogrenci_no, ad_soyad, sinif):
        """Yeni öğrenci ekle"""
        try:
            self.cursor.execute('''
                INSERT INTO ogrenciler (bolum_id, ogrenci_no, ad_soyad, sinif)
                VALUES (?, ?, ?, ?)
            ''', (bolum_id, ogrenci_no, ad_soyad, sinif))
            self.conn.commit()
            return True, self.cursor.lastrowid
        except sqlite3.IntegrityError:
            # Öğrenci zaten varsa ID'sini döndür
            self.cursor.execute('''
                SELECT id FROM ogrenciler 
                WHERE bolum_id = ? AND ogrenci_no = ?
            ''', (bolum_id, ogrenci_no))
            result = self.cursor.fetchone()
            return True, result[0] if result else None
        except Exception as e:
            return False, f"Hata: {str(e)}"
    
    def get_ogrenci_by_no(self, bolum_id, ogrenci_no):
        """Öğrenci numarasına göre öğrenci bilgilerini getir"""
        self.cursor.execute('''
            SELECT * FROM ogrenciler 
            WHERE bolum_id = ? AND ogrenci_no = ? AND aktif = 1
        ''', (bolum_id, ogrenci_no))
        return self.cursor.fetchone()
    
    def get_ogrenci_dersleri(self, ogrenci_id):
        """Öğrencinin aldığı dersleri getir"""
        self.cursor.execute('''
            SELECT d.* FROM dersler d
            INNER JOIN ogrenci_ders od ON d.id = od.ders_id
            WHERE od.ogrenci_id = ? AND d.aktif = 1
        ''', (ogrenci_id,))
        return self.cursor.fetchall()
    
    # Öğrenci-Ders ilişkisi
    def ogrenci_ders_ekle(self, ogrenci_id, ders_id):
        """Öğrenciye ders ekle"""
        try:
            self.cursor.execute('''
                INSERT INTO ogrenci_ders (ogrenci_id, ders_id)
                VALUES (?, ?)
            ''', (ogrenci_id, ders_id))
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return True  # Zaten ekli
        except Exception as e:
            return False
    
    def get_dersi_alan_ogrenciler(self, ders_id):
        """Dersi alan öğrencileri getir"""
        self.cursor.execute('''
            SELECT o.* FROM ogrenciler o
            INNER JOIN ogrenci_ders od ON o.id = od.ogrenci_id
            WHERE od.ders_id = ? AND o.aktif = 1
            ORDER BY o.ogrenci_no
        ''', (ders_id,))
        return self.cursor.fetchall()
    
    # Sınav programı işlemleri
    def sinav_ekle(self, bolum_id, ders_id, derslik_id, tarih, 
                   baslangic_saati, bitis_saati, sinav_turu):
        """Sınav programına sınav ekle"""
        try:
            self.cursor.execute('''
                INSERT INTO sinav_programi 
                (bolum_id, ders_id, derslik_id, tarih, baslangic_saati, 
                 bitis_saati, sinav_turu)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (bolum_id, ders_id, derslik_id, tarih, baslangic_saati, 
                  bitis_saati, sinav_turu))
            self.conn.commit()
            return True, self.cursor.lastrowid
        except Exception as e:
            return False, f"Hata: {str(e)}"
    
    def get_sinav_programi(self, bolum_id):
        """Bölüme göre sınav programını getir"""
        self.cursor.execute('''
            SELECT sp.*, d.ders_kodu, d.ders_adi, dr.derslik_adi, dr.derslik_kodu
            FROM sinav_programi sp
            INNER JOIN dersler d ON sp.ders_id = d.id
            INNER JOIN derslikler dr ON sp.derslik_id = dr.id
            WHERE sp.bolum_id = ?
            ORDER BY sp.tarih, sp.baslangic_saati
        ''', (bolum_id,))
        return self.cursor.fetchall()
    
    def sinav_programi_temizle(self, bolum_id):
        """Bölümün sınav programını temizle"""
        try:
            self.cursor.execute('''
                DELETE FROM sinav_programi WHERE bolum_id = ?
            ''', (bolum_id,))
            self.conn.commit()
            return True
        except Exception as e:
            return False
    
    # Oturma düzeni işlemleri
    def oturma_ekle(self, sinav_id, ogrenci_id, derslik_id, sira_no, sutun_no):
        """Oturma düzenine kayıt ekle"""
        try:
            self.cursor.execute('''
                INSERT INTO oturma_duzeni 
                (sinav_id, ogrenci_id, derslik_id, sira_no, sutun_no)
                VALUES (?, ?, ?, ?, ?)
            ''', (sinav_id, ogrenci_id, derslik_id, sira_no, sutun_no))
            self.conn.commit()
            return True
        except Exception as e:
            return False
    
    def get_oturma_duzeni(self, sinav_id):
        """Sınava göre oturma düzenini getir"""
        self.cursor.execute('''
            SELECT od.*, o.ogrenci_no, o.ad_soyad, dr.derslik_adi, dr.derslik_kodu
            FROM oturma_duzeni od
            INNER JOIN ogrenciler o ON od.ogrenci_id = o.id
            INNER JOIN derslikler dr ON od.derslik_id = dr.id
            WHERE od.sinav_id = ?
            ORDER BY dr.id, od.sira_no, od.sutun_no
        ''', (sinav_id,))
        return self.cursor.fetchall()
    
    def oturma_temizle(self, sinav_id):
        """Sınavın oturma düzenini temizle"""
        try:
            self.cursor.execute('''
                DELETE FROM oturma_duzeni WHERE sinav_id = ?
            ''', (sinav_id,))
            self.conn.commit()
            return True
        except Exception as e:
            return False

