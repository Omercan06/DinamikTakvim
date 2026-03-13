

import sys
import io

# Windows konsol encoding sorununu coz
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from database import Database
from excel_parser import ExcelParser
from sinav_algoritma import SinavProgramiOlusturucu, OturmaDuzeniOlusturucu
from raporlama import RaporOlusturucu
from datetime import datetime, timedelta
import os

def test_database():
    """Veritabani modulunu test et"""
    print("=" * 60)
    print("VERITABANI TESTI")
    print("=" * 60)
    
    db = Database("test_db.db")
    
    # Bölümleri kontrol et
    bolumler = db.get_bolumler()
    print(f"[OK] {len(bolumler)} bolum bulundu")
    
    # Admin kullanıcısını kontrol et
    admin = db.giris_yap("admin@kocaeli.edu.tr", "admin123")
    if admin:
        print(f"[OK] Admin girisi basarili: {admin[1]}")
    else:
        print("[HATA] Admin girisi basarisiz!")
        return False
    
    db.close()
    print("[OK] Veritabani testi basarili!\n")
    return True


def test_excel_parser():
    """Excel parser modulunu test et"""
    print("=" * 60)
    print("EXCEL PARSER TESTI")
    print("=" * 60)
    
    if not os.path.exists("ders_listesi.xlsx"):
        print("[HATA] ders_listesi.xlsx bulunamadi!")
        return False
    
    if not os.path.exists("ogrenci_listesi.xlsx"):
        print("[HATA] ogrenci_listesi.xlsx bulunamadi!")
        return False
    
    db = Database("test_db.db")
    parser = ExcelParser(db)
    
    # BLM bölümünü bul
    bolumler = db.get_bolumler()
    blm_bolum = None
    for bolum in bolumler:
        if bolum[2] == 'BLM':
            blm_bolum = bolum
            break
    
    if not blm_bolum:
        print("[HATA] BLM bolumu bulunamadi!")
        return False
    
    bolum_id = blm_bolum[0]
    
    # Ders listesini yükle
    print("Ders listesi yukleniyor...")
    basari, mesaj, hatalar = parser.ders_listesi_yukle("ders_listesi.xlsx", bolum_id)
    if basari:
        print(f"[OK] {mesaj}")
        if hatalar:
            print(f"  Uyari: {len(hatalar)} hata olustu")
    else:
        print(f"[HATA] Ders listesi yuklenemedi: {mesaj}")
        return False
    
    # Öğrenci listesini yükle
    print("Ogrenci listesi yukleniyor...")
    basari, mesaj, hatalar = parser.ogrenci_listesi_yukle("ogrenci_listesi.xlsx", bolum_id)
    if basari:
        print(f"[OK] {mesaj}")
        if hatalar:
            print(f"  Uyari: {len(hatalar)} hata olustu")
    else:
        print(f"[HATA] Ogrenci listesi yuklenemedi: {mesaj}")
        return False
    
    # Verileri kontrol et
    dersler = db.get_dersler(bolum_id)
    print(f"[OK] {len(dersler)} ders yuklendi")
    
    db.close()
    print("[OK] Excel parser testi basarili!\n")
    return True


def test_sinav_programi():
    """Sinav programi algoritmasini test et"""
    print("=" * 60)
    print("SINAV PROGRAMI ALGORITMASI TESTI")
    print("=" * 60)
    
    db = Database("test_db.db")
    
    # BLM bölümünü bul
    bolumler = db.get_bolumler()
    blm_bolum = None
    for bolum in bolumler:
        if bolum[2] == 'BLM':
            blm_bolum = bolum
            break
    
    bolum_id = blm_bolum[0]
    
    # Dersleri al
    dersler = db.get_dersler(bolum_id)
    if not dersler:
        print("[HATA] Ders bulunamadi!")
        return False
    
    print(f"[OK] {len(dersler)} ders bulundu")
    
    # Kısıtları oluştur
    kisitlar = {
        'dahil_dersler': [d[0] for d in dersler],
        'baslangic_tarihi': datetime.now() + timedelta(days=7),
        'bitis_tarihi': datetime.now() + timedelta(days=30),
        'tatil_gunleri': [5, 6],
        'sinav_turu': 'Test',
        'varsayilan_sure': 75,
        'ozel_sureler': {},
        'bekleme_suresi': 15,
        'ayni_anda_yapilamaz': True
    }
    
    # Program oluştur
    print("Sinav programi olusturuluyor...")
    olusturucu = SinavProgramiOlusturucu(db)
    basari, mesaj = olusturucu.program_olustur(bolum_id, kisitlar)
    
    if basari:
        print(f"[OK] {mesaj}")
        
        # Programı kontrol et
        program = db.get_sinav_programi(bolum_id)
        print(f"[OK] {len(program)} sinav planlandi")
        
        # İlk 5 sınavı göster
        print("\nIlk 5 Sinav:")
        for sinav in program[:5]:
            print(f"  - {sinav[4]} {sinav[5]}: {sinav[9]} - {sinav[10]} ({sinav[11]})")
    else:
        print(f"[HATA] Sinav programi olusturulamadi: {mesaj}")
        hatalar = olusturucu.get_hatalar()
        if hatalar:
            print("Hatalar:")
            for hata in hatalar[:5]:
                print(f"  - {hata}")
        return False
    
    db.close()
    print("[OK] Sinav programi testi basarili!\n")
    return True


def test_oturma_duzeni():
    """Oturma duzeni algoritmasini test et"""
    print("=" * 60)
    print("OTURMA DUZENI ALGORITMASI TESTI")
    print("=" * 60)
    
    db = Database("test_db.db")
    
    # BLM bölümünü bul
    bolumler = db.get_bolumler()
    blm_bolum = None
    for bolum in bolumler:
        if bolum[2] == 'BLM':
            blm_bolum = bolum
            break
    
    bolum_id = blm_bolum[0]
    
    # Sınav programından ilk sınavı al
    program = db.get_sinav_programi(bolum_id)
    if not program:
        print("[HATA] Sinav programi bulunamadi!")
        return False
    
    sinav = program[0]
    sinav_id = sinav[0]
    
    print(f"Test sinavi: {sinav[9]} - {sinav[10]}")
    
    # Oturma düzeni oluştur
    print("Oturma duzeni olusturuluyor...")
    olusturucu = OturmaDuzeniOlusturucu(db)
    basari, mesaj = olusturucu.oturma_olustur(sinav_id)
    
    if basari:
        print(f"[OK] {mesaj}")
        
        # Oturma düzenini kontrol et
        oturma = db.get_oturma_duzeni(sinav_id)
        print(f"[OK] {len(oturma)} ogrenci yerlestirildi")
        
        # İlk 5 yerleştirmeyi göster
        print("\nIlk 5 Yerlestirme:")
        for kayit in oturma[:5]:
            print(f"  - Sira {kayit[4]+1}, Sutun {kayit[5]+1}: {kayit[6]} - {kayit[7]}")
    else:
        print(f"[HATA] Oturma duzeni olusturulamadi: {mesaj}")
        return False
    
    db.close()
    print("[OK] Oturma duzeni testi basarili!\n")
    return True


def test_raporlama():
    """Raporlama modulunu test et"""
    print("=" * 60)
    print("RAPORLAMA MODULU TESTI")
    print("=" * 60)
    
    db = Database("test_db.db")
    rapor = RaporOlusturucu(db)
    
    # BLM bölümünü bul
    bolumler = db.get_bolumler()
    blm_bolum = None
    for bolum in bolumler:
        if bolum[2] == 'BLM':
            blm_bolum = bolum
            break
    
    bolum_id = blm_bolum[0]
    
    # Excel raporu oluştur
    print("Excel raporu olusturuluyor...")
    basari, mesaj = rapor.sinav_programi_excel(bolum_id, "test_sinav_programi.xlsx")
    if basari:
        print(f"[OK] {mesaj}")
    else:
        print(f"[HATA] Excel raporu olusturulamadi: {mesaj}")
        return False
    
    # PDF raporu oluştur
    print("PDF raporu olusturuluyor...")
    basari, mesaj = rapor.sinav_programi_pdf(bolum_id, "test_sinav_programi.pdf")
    if basari:
        print(f"[OK] {mesaj}")
    else:
        print(f"[HATA] PDF raporu olusturulamadi: {mesaj}")
        return False
    
    # Oturma düzeni PDF'i
    program = db.get_sinav_programi(bolum_id)
    if program:
        sinav_id = program[0][0]
        print("Oturma duzeni PDF'i olusturuluyor...")
        basari, mesaj = rapor.oturma_duzeni_pdf(sinav_id, "test_oturma_duzeni.pdf")
        if basari:
            print(f"[OK] {mesaj}")
        else:
            print(f"[HATA] Oturma duzeni PDF'i olusturulamadi: {mesaj}")
            return False
    
    db.close()
    print("[OK] Raporlama testi basarili!\n")
    return True


def cleanup():
    """Test dosyalarini temizle"""
    print("=" * 60)
    print("TEMIZLIK")
    print("=" * 60)
    
    test_files = [
        "test_db.db",
        "test_sinav_programi.xlsx",
        "test_sinav_programi.pdf",
        "test_oturma_duzeni.pdf"
    ]
    
    for file in test_files:
        if os.path.exists(file):
            os.remove(file)
            print(f"[OK] {file} silindi")
    
    print()


def main():
    """Ana test fonksiyonu"""
    print("\n" + "=" * 60)
    print("DINAMIK SINAV TAKVIMI SISTEMI - KAPSAMLI TEST")
    print("=" * 60)
    print()
    
    testler = [
        ("Veritabani", test_database),
        ("Excel Parser", test_excel_parser),
        ("Sinav Programi Algoritmasi", test_sinav_programi),
        ("Oturma Duzeni Algoritmasi", test_oturma_duzeni),
        ("Raporlama", test_raporlama),
    ]
    
    basarili = 0
    basarisiz = 0
    
    for test_adi, test_func in testler:
        try:
            if test_func():
                basarili += 1
            else:
                basarisiz += 1
        except Exception as e:
            print(f"[HATA] {test_adi} testi hata verdi: {str(e)}\n")
            basarisiz += 1
    
    # Sonuçları göster
    print("=" * 60)
    print("TEST SONUCLARI")
    print("=" * 60)
    print(f"Toplam Test: {basarili + basarisiz}")
    print(f"[OK] Basarili: {basarili}")
    print(f"[HATA] Basarisiz: {basarisiz}")
    print()
    
    if basarisiz == 0:
        print("[BASARILI] TUM TESTLER BASARILI!")
    else:
        print("[UYARI] BAZI TESTLER BASARISIZ!")
    
    print("=" * 60)
    print()
    
    # Temizlik
    cleanup()


if __name__ == "__main__":
    main()

