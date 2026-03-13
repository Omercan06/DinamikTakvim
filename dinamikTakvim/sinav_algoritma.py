

from datetime import datetime, timedelta, time
from database import Database
import random


class SinavProgramiOlusturucu:
    def __init__(self, db: Database):
        self.db = db
        self.hatalar = []
        self.uyarilar = []
        self.derslik_kullanim = {}  # {(tarih, derslik_id): [(baslangic, bitis), ...]}
    
    def program_olustur(self, bolum_id, kısıtlar):
        """
        Sınav programını oluştur - İyileştirilmiş Algoritma
        
        Args:
            bolum_id: Bölüm ID
            kısıtlar: {
                'dahil_dersler': [ders_id_list],
                'baslangic_tarihi': datetime,
                'bitis_tarihi': datetime,
                'tatil_gunleri': [0-6 arası günler, 0=Pazartesi],
                'sinav_turu': str,
                'varsayilan_sure': int (dakika),
                'ozel_sureler': {ders_id: sure},
                'bekleme_suresi': int (dakika),
                'ayni_anda_yapilamaz': bool
            }
        
        Returns:
            (basari, mesaj)
        """
        self.hatalar = []
        self.uyarilar = []
        self.derslik_kullanim = {}
        
        # Önceki programı temizle
        self.db.sinav_programi_temizle(bolum_id)
        
        # Kısıtları al
        dahil_dersler = kısıtlar.get('dahil_dersler', [])
        baslangic_tarihi = kısıtlar.get('baslangic_tarihi')
        bitis_tarihi = kısıtlar.get('bitis_tarihi')
        tatil_gunleri = kısıtlar.get('tatil_gunleri', [5, 6])  # Cumartesi, Pazar
        sinav_turu = kısıtlar.get('sinav_turu', 'Vize')
        varsayilan_sure = kısıtlar.get('varsayilan_sure', 75)
        ozel_sureler = kısıtlar.get('ozel_sureler', {})
        bekleme_suresi = kısıtlar.get('bekleme_suresi', 15)
        ayni_anda_yapilamaz = kısıtlar.get('ayni_anda_yapilamaz', False)
        
        # Derslikleri al
        derslikler = self.db.get_derslikler(bolum_id)
        if not derslikler:
            return False, "Bölüme ait derslik bulunamadı!"
        
        # En büyük derslik kapasitesini bul
        max_derslik_kapasite = max(d[4] for d in derslikler)
        
        # Sınav günlerini oluştur
        sinav_gunleri = []
        current_date = baslangic_tarihi
        while current_date <= bitis_tarihi:
            if current_date.weekday() not in tatil_gunleri:
                sinav_gunleri.append(current_date)
            current_date += timedelta(days=1)
        
        if not sinav_gunleri:
            return False, "Seçilen tarih aralığında sınav yapılabilecek gün yok!"
        
        # Günlük kapasite hesapla
        gun_basi_saat = (18 - 8) * 60  # 10 saat = 600 dakika
        ortalama_sinav_suresi = varsayilan_sure + bekleme_suresi
        gun_basi_max_sinav = gun_basi_saat // ortalama_sinav_suresi
        
        # Gereken minimum gün sayısı
        gerekli_gun_sayisi = (len(dahil_dersler) + gun_basi_max_sinav - 1) // gun_basi_max_sinav
        
        if gerekli_gun_sayisi > len(sinav_gunleri) and ayni_anda_yapilamaz:
            self.uyarilar.append(
                f"İdeal senaryo için en az {gerekli_gun_sayisi} gün gerekli, "
                f"{len(sinav_gunleri)} gün mevcut. Program sıkışık olabilir."
            )
        
        # Dersleri hazırla ve sınıflara göre grupla
        ders_bilgileri = []
        sinif_dersleri = {}
        
        for ders_id in dahil_dersler:
            ders = self.db.cursor.execute(
                "SELECT * FROM dersler WHERE id = ?", (ders_id,)
            ).fetchone()
            
            if not ders:
                continue
            
            sinif = ders[5]  # sinif
            ders_suresi = ozel_sureler.get(ders_id, varsayilan_sure)
            ogrenciler = self.db.get_dersi_alan_ogrenciler(ders_id)
            
            ders_info = {
                'ders': ders,
                'ders_id': ders_id,
                'ders_kodu': ders[2],
                'sinif': sinif,
                'sure': ders_suresi,
                'ogrenciler': ogrenciler,
                'ogrenci_sayisi': len(ogrenciler)
            }
            
            ders_bilgileri.append(ders_info)
            
            if sinif not in sinif_dersleri:
                sinif_dersleri[sinif] = []
            sinif_dersleri[sinif].append(ders_info)
        
        # Dersleri önceliğe göre sırala (öğrenci sayısı fazla olanlar önce)
        ders_bilgileri.sort(key=lambda d: d['ogrenci_sayisi'], reverse=True)
        
        # Ana planlama algoritması
        if ayni_anda_yapilamaz:
            # Mod 1: Sıralı sınav (bir sınav bitene kadar diğeri başlamaz)
            basari = self._sirali_planla(
                bolum_id, ders_bilgileri, sinav_gunleri, derslikler,
                sinav_turu, bekleme_suresi, max_derslik_kapasite
            )
        else:
            # Mod 2: Paralel sınav (öğrenci çakışması kontrollü)
            basari = self._paralel_planla(
                bolum_id, ders_bilgileri, sinav_gunleri, derslikler,
                sinav_turu, bekleme_suresi, max_derslik_kapasite
            )
        
        if not basari:
            if self.hatalar:
                return False, f"Program oluşturulamadı: {len(self.hatalar)} hata oluştu"
            else:
                return False, "Program oluşturulamadı: Bilinmeyen hata"
        
        if self.hatalar:
            return False, f"Program kısmen oluşturuldu ancak {len(self.hatalar)} hata oluştu"
        
        mesaj = "Sınav programı başarıyla oluşturuldu"
        if self.uyarilar:
            mesaj += f" ({len(self.uyarilar)} uyarı)"
        
        return True, mesaj
    
    def _sirali_planla(self, bolum_id, ders_bilgileri, sinav_gunleri, derslikler,
                       sinav_turu, bekleme_suresi, max_kapasite):
        """Sıralı planlama - Bir sınav bitene kadar diğeri başlamaz"""
        
        # Sınav saatleri
        gun_baslangic = time(8, 0)
        gun_bitis_saat = time(18, 0)
        
        gun_index = 0
        current_time = datetime.combine(sinav_gunleri[gun_index], gun_baslangic)
        gun_bitis = datetime.combine(sinav_gunleri[gun_index], gun_bitis_saat)
        
        for ders_info in ders_bilgileri:
            ders = ders_info['ders']
            ders_id = ders_info['ders_id']
            sure = ders_info['sure']
            ogrenci_sayisi = ders_info['ogrenci_sayisi']
            ogrenciler = ders_info['ogrenciler']
            
            sinav_bitis = current_time + timedelta(minutes=sure)
            
            # Gün sonu kontrolü - bir sonraki güne geç
            while sinav_bitis > gun_bitis:
                gun_index += 1
                
                if gun_index >= len(sinav_gunleri):
                    self.hatalar.append(
                        f"Tarih aralığı tüm sınavları barındırmıyor! "
                        f"Ders {ders_info['ders_kodu']} planlanamadı."
                    )
                    return False
                
                current_time = datetime.combine(sinav_gunleri[gun_index], gun_baslangic)
                gun_bitis = datetime.combine(sinav_gunleri[gun_index], gun_bitis_saat)
                sinav_bitis = current_time + timedelta(minutes=sure)
            
            # Birden fazla derslik gerekebilir
            if ogrenci_sayisi > max_kapasite:
                # Öğrencileri gruplara böl
                grup_sayisi = (ogrenci_sayisi + max_kapasite - 1) // max_kapasite
                # Her grubun maksimum boyutunu hesapla (eşit dağıtım için)
                grup_max_boyut = (ogrenci_sayisi + grup_sayisi - 1) // grup_sayisi
                
                for grup_idx in range(grup_sayisi):
                    grup_baslangic = grup_idx * grup_max_boyut
                    grup_bitis = min((grup_idx + 1) * grup_max_boyut, ogrenci_sayisi)
                    grup_ogrenci_sayisi = grup_bitis - grup_baslangic
                    
                    # Bu grup için derslik bul
                    derslik = self._uygun_derslik_bul(
                        derslikler, grup_ogrenci_sayisi,
                        sinav_gunleri[gun_index], current_time, sinav_bitis
                    )
                    
                    if not derslik:
                        self.hatalar.append(
                            f"Ders {ders_info['ders_kodu']} (Grup {grup_idx+1}) için "
                            f"uygun derslik bulunamadı! Gerekli kapasite: {grup_ogrenci_sayisi}"
                        )
                        continue
                    
                    # Sınavı veritabanına ekle
                    basari, sinav_id = self.db.sinav_ekle(
                        bolum_id=bolum_id,
                        ders_id=ders_id,
                        derslik_id=derslik[0],
                        tarih=sinav_gunleri[gun_index].strftime('%Y-%m-%d'),
                        baslangic_saati=current_time.strftime('%H:%M'),
                        bitis_saati=sinav_bitis.strftime('%H:%M'),
                        sinav_turu=f"{sinav_turu} (Grup {grup_idx+1}/{grup_sayisi})"
                    )
                    
                    if not basari:
                        self.hatalar.append(f"Sınav eklenemedi: {sinav_id}")
                
                # Bir sonraki sınav için zamanı ayarla
                current_time = sinav_bitis + timedelta(minutes=bekleme_suresi)
            
            else:
                # Normal tek derslik
                derslik = self._uygun_derslik_bul(
                    derslikler, ogrenci_sayisi,
                    sinav_gunleri[gun_index], current_time, sinav_bitis
                )
                
                if not derslik:
                    self.hatalar.append(
                        f"Ders {ders_info['ders_kodu']} için uygun derslik bulunamadı! "
                        f"Gerekli kapasite: {ogrenci_sayisi}"
                    )
                    continue
                
                # Sınavı veritabanına ekle
                basari, sinav_id = self.db.sinav_ekle(
                    bolum_id=bolum_id,
                    ders_id=ders_id,
                    derslik_id=derslik[0],
                    tarih=sinav_gunleri[gun_index].strftime('%Y-%m-%d'),
                    baslangic_saati=current_time.strftime('%H:%M'),
                    bitis_saati=sinav_bitis.strftime('%H:%M'),
                    sinav_turu=sinav_turu
                )
                
                if not basari:
                    self.hatalar.append(f"Sınav eklenemedi: {sinav_id}")
                
                # Bir sonraki sınav için zamanı ayarla
                current_time = sinav_bitis + timedelta(minutes=bekleme_suresi)
        
        return True
    
    def _paralel_planla(self, bolum_id, ders_bilgileri, sinav_gunleri, derslikler,
                        sinav_turu, bekleme_suresi, max_kapasite):
        """Paralel planlama - Öğrenci çakışması olmadığı sürece aynı anda sınavlar olabilir"""
        
        # Her öğrencinin sınav saatlerini takip et
        ogrenci_sinavlari = {}  # {ogrenci_id: [(baslangic, bitis), ...]}
        
        # Zaman slotları
        gun_baslangic = time(8, 0)
        gun_bitis = time(18, 0)
        slot_araligi = 15  # 15 dakika
        
        for ders_info in ders_bilgileri:
            ders_id = ders_info['ders_id']
            sure = ders_info['sure']
            ogrenciler = ders_info['ogrenciler']
            ogrenci_sayisi = ders_info['ogrenci_sayisi']
            ogrenci_ids = [o[0] for o in ogrenciler]
            
            # Birden fazla derslik gerekiyorsa
            if ogrenci_sayisi > max_kapasite:
                grup_sayisi = (ogrenci_sayisi + max_kapasite - 1) // max_kapasite
                # Her grubun maksimum boyutunu hesapla (eşit dağıtım için)
                grup_max_boyut = (ogrenci_sayisi + grup_sayisi - 1) // grup_sayisi
                
                for grup_idx in range(grup_sayisi):
                    grup_baslangic_idx = grup_idx * grup_max_boyut
                    grup_bitis_idx = min((grup_idx + 1) * grup_max_boyut, ogrenci_sayisi)
                    grup_ogrenciler = ogrenciler[grup_baslangic_idx:grup_bitis_idx]
                    grup_ogrenci_ids = [o[0] for o in grup_ogrenciler]
                    grup_ogrenci_sayisi = len(grup_ogrenciler)
                    
                    # Bu grup için slot bul
                    slot_bulundu = False
                    for gun in sinav_gunleri:
                        if slot_bulundu:
                            break
                        
                        # Zaman slotlarını oluştur
                        current = datetime.combine(gun, gun_baslangic)
                        end_of_day = datetime.combine(gun, gun_bitis)
                        
                        while current < end_of_day:
                            slot_bitis = current + timedelta(minutes=sure)
                            
                            if slot_bitis > end_of_day:
                                break
                            
                            # Öğrenci çakışması var mı?
                            cakisma = self._cakisma_kontrol(
                                grup_ogrenci_ids, current, slot_bitis,
                                ogrenci_sinavlari, bekleme_suresi
                            )
                            
                            if not cakisma:
                                # Derslik bul
                                derslik = self._uygun_derslik_bul(
                                    derslikler, grup_ogrenci_sayisi, gun, current, slot_bitis
                                )
                                
                                if derslik:
                                    # Sınavı ekle
                                    basari, sinav_id = self.db.sinav_ekle(
                                        bolum_id=bolum_id,
                                        ders_id=ders_id,
                                        derslik_id=derslik[0],
                                        tarih=gun.strftime('%Y-%m-%d'),
                                        baslangic_saati=current.strftime('%H:%M'),
                                        bitis_saati=slot_bitis.strftime('%H:%M'),
                                        sinav_turu=f"{sinav_turu} (Grup {grup_idx+1}/{grup_sayisi})"
                                    )
                                    
                                    if basari:
                                        # Öğrencilerin sınav saatlerini kaydet
                                        for ogr_id in grup_ogrenci_ids:
                                            if ogr_id not in ogrenci_sinavlari:
                                                ogrenci_sinavlari[ogr_id] = []
                                            ogrenci_sinavlari[ogr_id].append((current, slot_bitis))
                                        
                                        slot_bulundu = True
                                        break
                            
                            # Sonraki slot
                            current += timedelta(minutes=slot_araligi)
                    
                    if not slot_bulundu:
                        self.hatalar.append(
                            f"Ders {ders_info['ders_kodu']} (Grup {grup_idx+1}) için "
                            f"uygun zaman veya derslik bulunamadı!"
                        )
            
            else:
                # Normal tek derslik durumu
                slot_bulundu = False
                for gun in sinav_gunleri:
                    if slot_bulundu:
                        break
                    
                    current = datetime.combine(gun, gun_baslangic)
                    end_of_day = datetime.combine(gun, gun_bitis)
                    
                    while current < end_of_day:
                        slot_bitis = current + timedelta(minutes=sure)
                        
                        if slot_bitis > end_of_day:
                            break
                        
                        # Öğrenci çakışması var mı?
                        cakisma = self._cakisma_kontrol(
                            ogrenci_ids, current, slot_bitis,
                            ogrenci_sinavlari, bekleme_suresi
                        )
                        
                        if not cakisma:
                            # Derslik bul
                            derslik = self._uygun_derslik_bul(
                                derslikler, ogrenci_sayisi, gun, current, slot_bitis
                            )
                            
                            if derslik:
                                # Sınavı ekle
                                basari, sinav_id = self.db.sinav_ekle(
                                    bolum_id=bolum_id,
                                    ders_id=ders_id,
                                    derslik_id=derslik[0],
                                    tarih=gun.strftime('%Y-%m-%d'),
                                    baslangic_saati=current.strftime('%H:%M'),
                                    bitis_saati=slot_bitis.strftime('%H:%M'),
                                    sinav_turu=sinav_turu
                                )
                                
                                if basari:
                                    # Öğrencilerin sınav saatlerini kaydet
                                    for ogr_id in ogrenci_ids:
                                        if ogr_id not in ogrenci_sinavlari:
                                            ogrenci_sinavlari[ogr_id] = []
                                        ogrenci_sinavlari[ogr_id].append((current, slot_bitis))
                                    
                                    slot_bulundu = True
                                    break
                        
                        # Sonraki slot
                        current += timedelta(minutes=slot_araligi)
                
                if not slot_bulundu:
                    self.hatalar.append(
                        f"Ders {ders_info['ders_kodu']} için uygun zaman veya derslik bulunamadı!"
                    )
        
        return True
    
    def _uygun_derslik_bul(self, derslikler, ogrenci_sayisi, tarih, baslangic, bitis):
        """Uygun derslik bul - Kullanım takipli"""
        
        # Küçükten büyüğe sırala (en uygun kapasiteli dersliği bul)
        for derslik in sorted(derslikler, key=lambda d: d[4]):
            if derslik[4] < ogrenci_sayisi:
                continue
            
            derslik_id = derslik[0]
            tarih_str = tarih.strftime('%Y-%m-%d')
            anahtar = (tarih_str, derslik_id)
            
            # Bu derslik bu tarihte kullanılıyor mu?
            if anahtar in self.derslik_kullanim:
                # Zaman çakışması var mı kontrol et
                musait = True
                for kullanim_bas, kullanim_bit in self.derslik_kullanim[anahtar]:
                    # Çakışma kontrolü
                    if not (bitis <= kullanim_bas or baslangic >= kullanim_bit):
                        musait = False
                        break
                
                if not musait:
                    continue
            
            # Derslik uygun, rezerve et
            if anahtar not in self.derslik_kullanim:
                self.derslik_kullanim[anahtar] = []
            self.derslik_kullanim[anahtar].append((baslangic, bitis))
            
            return derslik
        
        return None
    
    def _cakisma_kontrol(self, ogrenci_ids, baslangic, bitis, ogrenci_sinavlari, bekleme_suresi):
        """Öğrenci çakışması kontrol et"""
        
        for ogrenci_id in ogrenci_ids:
            if ogrenci_id in ogrenci_sinavlari:
                for sinav_bas, sinav_bit in ogrenci_sinavlari[ogrenci_id]:
                    # Zaman çakışması
                    if not (bitis <= sinav_bas or baslangic >= sinav_bit):
                        return True
                    
                    # Bekleme süresi kontrolü
                    fark_dakika = abs((baslangic - sinav_bit).total_seconds()) / 60
                    if fark_dakika < bekleme_suresi:
                        return True
        
        return False
    
    def get_hatalar(self):
        """Hataları döndür"""
        return self.hatalar
    
    def get_uyarilar(self):
        """Uyarıları döndür"""
        return self.uyarilar
    
    def get_uyarilar(self):
        """Uyarıları döndür"""
        return self.uyarilar


class OturmaDuzeniOlusturucu:
    def __init__(self, db: Database):
        self.db = db
        self.hatalar = []
        self.uyarilar = []
    
    def oturma_olustur(self, sinav_id):
        """
        Belirli bir sınav için oturma düzeni oluştur
        
        Args:
            sinav_id: Sınav ID
            
        Returns:
            (basari, mesaj)
        """
        self.hatalar = []
        
        # Önceki oturma düzenini temizle
        self.db.oturma_temizle(sinav_id)
        
        # Sınav bilgilerini al
        sinav = self.db.cursor.execute('''
            SELECT * FROM sinav_programi WHERE id = ?
        ''', (sinav_id,)).fetchone()
        
        if not sinav:
            return False, "Sınav bulunamadı!"
        
        ders_id = sinav[2]
        derslik_id = sinav[3]
        
        # Derslik bilgilerini al
        derslik = self.db.cursor.execute('''
            SELECT * FROM derslikler WHERE id = ?
        ''', (derslik_id,)).fetchone()
        
        if not derslik:
            return False, "Derslik bulunamadı!"
        
        kapasite = derslik[4]
        enine_sira = derslik[5]  # Sütun sayısı
        boyuna_sira = derslik[6]  # Satır sayısı
        sira_yapisi = derslik[7]  # 2 veya 3 (ikişerli/üçerli)
        
        # Dersi alan öğrencileri al
        ogrenciler = self.db.get_dersi_alan_ogrenciler(ders_id)
        
        if not ogrenciler:
            return False, "Dersi alan öğrenci bulunamadı!"
        
        # NOT: Eğer ders birden fazla gruba bölünmüşse, her grup için ayrı sınav kaydı var.
        # Bu oturma düzeni sadece bu dersliğe sığan kadar öğrenciyi yerleştirecek.
        # Kapasite kontrolü - sadece uyarı ver, yerleştirmeyi durdurma
        if len(ogrenciler) > kapasite:
            self.uyarilar.append(
                f"Bu sınav için {len(ogrenciler)} öğrenci var, "
                f"derslik kapasitesi {kapasite}. "
                f"İlk {kapasite} öğrenci yerleştirilecek (grup sistemi)."
            )
        
        # Sadece derslik kapasitesi kadar öğrenci yerleştir
        # (Ders birden fazla gruba bölünmüşse, her grup için ayrı oturma düzeni oluşur)
        yerlestirilecek_ogrenciler = ogrenciler[:kapasite]  # İlk N öğrenci
        
        # Oturma düzenini oluştur
        # Zigzag pattern ile yerleştirme
        ogrenci_index = 0
        yerlestirildi = 0
        
        for sira in range(boyuna_sira):
            for sutun in range(enine_sira):
                # Sıra yapısına göre boşluk bırak
                # Örnek: 3'erli sıra → 3 öğrenci, 1 boşluk, 3 öğrenci, 1 boşluk...
                pozisyon_mod = sutun % (sira_yapisi + 1)
                
                if pozisyon_mod == sira_yapisi:
                    # Boşluk - atla
                    continue
                
                if ogrenci_index >= len(yerlestirilecek_ogrenciler):
                    # Tüm öğrenciler yerleşti
                    break
                
                ogrenci = yerlestirilecek_ogrenciler[ogrenci_index]
                ogrenci_id = ogrenci[0]
                
                # Oturma düzenine ekle
                basari = self.db.oturma_ekle(
                    sinav_id=sinav_id,
                    ogrenci_id=ogrenci_id,
                    derslik_id=derslik_id,
                    sira_no=sira,
                    sutun_no=sutun
                )
                
                if basari:
                    yerlestirildi += 1
                
                ogrenci_index += 1
            
            # Tüm öğrenciler yerleştiyse dur
            if ogrenci_index >= len(yerlestirilecek_ogrenciler):
                break
        
        mesaj = f"{yerlestirildi} öğrenci başarıyla yerleştirildi"
        
        if len(ogrenciler) > kapasite:
            mesaj += f" (Toplam {len(ogrenciler)} öğrenciden {yerlestirildi} tanesi - Grup sistemi)"
        
        return True, mesaj
    
    def get_hatalar(self):
        """Hataları döndür"""
        return self.hatalar
    
    def get_uyarilar(self):
        """Uyarıları döndür"""
        return self.uyarilar
