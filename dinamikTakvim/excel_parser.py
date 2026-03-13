

import pandas as pd
import traceback
from database import Database


class ExcelParser:
    def __init__(self, db: Database):
        self.db = db
        self.hatalar = []
    
    def ders_listesi_yukle(self, excel_dosyasi, bolum_id):
        """
        Ders listesi Excel dosyasını parse et ve veritabanına yükle
        
        Args:
            excel_dosyasi: Excel dosya yolu
            bolum_id: Bölüm ID
            
        Returns:
            (basari, mesaj, hatalar)
        """
        self.hatalar = []
        eklenen_ders_sayisi = 0
        
        try:
            # Excel dosyasını oku
            xls = pd.ExcelFile(excel_dosyasi)
            
            # Her sheet bir sınıfı temsil ediyor
            for sheet_name in xls.sheet_names:
                try:
                    df = pd.read_excel(excel_dosyasi, sheet_name=sheet_name, header=None)
                    
                    # Sınıf bilgisini sheet adından al
                    sinif = sheet_name.strip()
                    
                    # İlk satır başlık olabilir, kontrol et
                    baslik_satiri = 0
                    for i, row in df.iterrows():
                        # Başlık satırı tespiti - daha spesifik kontrol
                        row_str = ' '.join([str(cell).upper() for cell in row if pd.notna(cell)])
                        
                        # "DERS KODU" VE "DERS ADI" gibi başlık ifadeleri aynı satırda mı?
                        if ("DERS" in row_str and "KOD" in row_str) or \
                           ("DERS" in row_str and "AD" in row_str) or \
                           ("DERS" in row_str and "İSİM" in row_str):
                            baslik_satiri = i + 1
                            break
                    
                    # Başlık satırından sonraki verileri oku
                    for idx, row in df.iterrows():
                        if idx < baslik_satiri:
                            continue
                        
                        try:
                            # NaN değerleri kontrol et
                            if pd.isna(row[0]) or str(row[0]).strip() == "":
                                continue
                            
                            ders_kodu = str(row[0]).strip()
                            ders_adi = str(row[1]).strip() if pd.notna(row[1]) else ""
                            ogretim_elemani = str(row[2]).strip() if pd.notna(row[2]) else ""
                            
                            # Başlık satırı ise atla (ekstra kontrol)
                            if "DERS" in ders_kodu.upper() and "KOD" in ders_kodu.upper():
                                continue
                            
                            # Ders kodu formatı kontrolü (gerçek ders kodları harf+sayı formatında)
                            if not any(c.isdigit() for c in ders_kodu):
                                # Hiç rakam yok, muhtemelen başlık
                                continue
                            
                            if not any(c.isalpha() for c in ders_kodu):
                                # Hiç harf yok, muhtemelen geçersiz
                                continue
                            
                            # Boş değer kontrolü
                            if not ders_kodu or not ders_adi:
                                continue
                            
                            # Ders türünü belirle (zorunlu/seçmeli)
                            # Ders kodu son karakteri 7 veya 9 ise seçmeli olabilir
                            ders_turu = "Zorunlu"
                            if ders_kodu[-1] in ['7', '9']:
                                ders_turu = "Seçmeli"
                            
                            # Dersi veritabanına ekle
                            basari, sonuc = self.db.ders_ekle(
                                bolum_id=bolum_id,
                                ders_kodu=ders_kodu,
                                ders_adi=ders_adi,
                                ogretim_elemani=ogretim_elemani,
                                sinif=sinif,
                                ders_turu=ders_turu
                            )
                            
                            if basari:
                                eklenen_ders_sayisi += 1
                            else:
                                self.hatalar.append(f"Sheet '{sheet_name}', Satır {idx+1}: {sonuc}")
                        
                        except Exception as e:
                            self.hatalar.append(f"Sheet '{sheet_name}', Satır {idx+1}: {str(e)}")
                
                except Exception as e:
                    self.hatalar.append(f"Sheet '{sheet_name}' okuma hatası: {str(e)}")
            
            if self.hatalar:
                return True, f"{eklenen_ders_sayisi} ders yüklendi, {len(self.hatalar)} hata oluştu", self.hatalar
            else:
                return True, f"{eklenen_ders_sayisi} ders başarıyla yüklendi", []
        
        except Exception as e:
            return False, f"Excel dosyası okuma hatası: {str(e)}\n{traceback.format_exc()}", []
    
    def ogrenci_listesi_yukle(self, excel_dosyasi, bolum_id):
        """
        Öğrenci listesi Excel dosyasını parse et ve veritabanına yükle
        
        Args:
            excel_dosyasi: Excel dosya yolu
            bolum_id: Bölüm ID
            
        Returns:
            (basari, mesaj, hatalar)
        """
        self.hatalar = []
        eklenen_ogrenci_sayisi = 0
        eklenen_iliski_sayisi = 0
        
        try:
            # Excel dosyasını oku
            df = pd.read_excel(excel_dosyasi)
            
            # Sütun adlarını normalize et
            df.columns = df.columns.str.strip()
            
            # Gerekli sütunları bul
            ogrenci_no_col = None
            ad_soyad_col = None
            sinif_col = None
            ders_col = None
            
            for col in df.columns:
                col_lower = col.lower()
                if 'no' in col_lower or 'numara' in col_lower:
                    ogrenci_no_col = col
                elif 'ad' in col_lower or 'soyad' in col_lower or 'isim' in col_lower:
                    ad_soyad_col = col
                elif 'sınıf' in col_lower or 'sinif' in col_lower or 'sınf' in col_lower:
                    sinif_col = col
                elif 'ders' in col_lower:
                    ders_col = col
            
            if not all([ogrenci_no_col, ad_soyad_col, sinif_col, ders_col]):
                return False, "Excel dosyasında gerekli sütunlar bulunamadı (Öğrenci No, Ad Soyad, Sınıf, Ders)", []
            
            # Her satırı işle
            for idx, row in df.iterrows():
                try:
                    ogrenci_no = str(row[ogrenci_no_col]).strip()
                    ad_soyad = str(row[ad_soyad_col]).strip()
                    sinif = str(row[sinif_col]).strip()
                    ders_kodu = str(row[ders_col]).strip()
                    
                    # Boş değer kontrolü
                    if pd.isna(row[ogrenci_no_col]) or pd.isna(row[ad_soyad_col]):
                        continue
                    
                    # Öğrenciyi ekle veya getir
                    basari, ogrenci_id = self.db.ogrenci_ekle(
                        bolum_id=bolum_id,
                        ogrenci_no=ogrenci_no,
                        ad_soyad=ad_soyad,
                        sinif=sinif
                    )
                    
                    if basari and isinstance(ogrenci_id, int):
                        # Öğrenci ilk kez eklendiyse sayacı artır
                        ogrenci = self.db.get_ogrenci_by_no(bolum_id, ogrenci_no)
                        if ogrenci and idx == df[df[ogrenci_no_col] == row[ogrenci_no_col]].index[0]:
                            eklenen_ogrenci_sayisi += 1
                    else:
                        if not basari:
                            self.hatalar.append(f"Satır {idx+2}: Öğrenci eklenemedi - {ogrenci_id}")
                            continue
                    
                    # Dersi bul
                    ders = self.db.get_ders_by_kod(bolum_id, ders_kodu)
                    if not ders:
                        self.hatalar.append(f"Satır {idx+2}: Ders bulunamadı - {ders_kodu}")
                        continue
                    
                    ders_id = ders[0]
                    
                    # Öğrenci-Ders ilişkisini ekle
                    if self.db.ogrenci_ders_ekle(ogrenci_id, ders_id):
                        eklenen_iliski_sayisi += 1
                
                except Exception as e:
                    self.hatalar.append(f"Satır {idx+2}: {str(e)}")
            
            mesaj = f"{eklenen_ogrenci_sayisi} öğrenci, {eklenen_iliski_sayisi} ders ilişkisi yüklendi"
            if self.hatalar:
                mesaj += f", {len(self.hatalar)} hata oluştu"
            
            return True, mesaj, self.hatalar
        
        except Exception as e:
            return False, f"Excel dosyası okuma hatası: {str(e)}\n{traceback.format_exc()}", []
    
    def get_hatalar(self):
        """Son işlemdeki hataları döndür"""
        return self.hatalar


def test_parser():
    """Parser'ı test et"""
    db = Database("test_sinav_takvimi.db")
    parser = ExcelParser(db)
    
    # Bilgisayar Mühendisliği bölümünü bul
    bolumler = db.get_bolumler()
    blm_bolum = None
    for bolum in bolumler:
        if bolum[2] == 'BLM':  # bolum_kodu
            blm_bolum = bolum
            break
    
    if not blm_bolum:
        print("Bilgisayar Mühendisliği bölümü bulunamadı!")
        return
    
    bolum_id = blm_bolum[0]
    
    # Ders listesini yükle
    print("Ders listesi yükleniyor...")
    basari, mesaj, hatalar = parser.ders_listesi_yukle("ders_listesi.xlsx", bolum_id)
    print(f"Sonuç: {mesaj}")
    if hatalar:
        print("Hatalar:")
        for hata in hatalar[:10]:  # İlk 10 hatayı göster
            print(f"  - {hata}")
    
    # Öğrenci listesini yükle
    print("\nÖğrenci listesi yükleniyor...")
    basari, mesaj, hatalar = parser.ogrenci_listesi_yukle("ogrenci_listesi.xlsx", bolum_id)
    print(f"Sonuç: {mesaj}")
    if hatalar:
        print("Hatalar:")
        for hata in hatalar[:10]:  # İlk 10 hatayı göster
            print(f"  - {hata}")
    
    db.close()


if __name__ == "__main__":
    test_parser()

