

import pandas as pd
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from datetime import datetime
from database import Database
import os


class RaporOlusturucu:
    def __init__(self, db: Database):
        self.db = db
        
        # PDF için Türkçe karakter desteği
        # Not: Arial fontunu kullanacağız (Windows'ta mevcut)
        try:
            # Windows sistem fontlarından Arial'ı kullan
            pdfmetrics.registerFont(TTFont('Arial', 'C:\\Windows\\Fonts\\arial.ttf'))
            pdfmetrics.registerFont(TTFont('Arial-Bold', 'C:\\Windows\\Fonts\\arialbd.ttf'))
        except:
            pass  # Font yüklenemezse default font kullanılacak
    
    def sinav_programi_excel(self, bolum_id, dosya_adi):
        """
        Sınav programını Excel olarak dışa aktar
        
        Args:
            bolum_id: Bölüm ID
            dosya_adi: Çıktı dosya adı
            
        Returns:
            (basari, mesaj)
        """
        try:
            # Sınav programını al
            sinavlar = self.db.get_sinav_programi(bolum_id)
            
            if not sinavlar:
                return False, "Sınav programı bulunamadı!"
            
            # Günlere göre grupla
            gunluk_program = {}
            for sinav in sinavlar:
                tarih = sinav[4]  # tarih
                if tarih not in gunluk_program:
                    gunluk_program[tarih] = []
                gunluk_program[tarih].append(sinav)
            
            # Excel writer oluştur
            with pd.ExcelWriter(dosya_adi, engine='openpyxl') as writer:
                # Her gün için ayrı sheet
                for tarih in sorted(gunluk_program.keys()):
                    gunun_sinavlari = gunluk_program[tarih]
                    
                    # DataFrame oluştur
                    data = []
                    for sinav in gunun_sinavlari:
                        ders_kodu = sinav[9]
                        ders_adi = sinav[10]
                        derslik_adi = sinav[11]
                        baslangic = sinav[5]
                        bitis = sinav[6]
                        sinav_turu = sinav[7]
                        
                        # Öğrenci sayısını al
                        ogrenciler = self.db.get_dersi_alan_ogrenciler(sinav[2])
                        
                        data.append({
                            'Ders Kodu': ders_kodu,
                            'Ders Adı': ders_adi,
                            'Derslik': derslik_adi,
                            'Başlangıç': baslangic,
                            'Bitiş': bitis,
                            'Sınav Türü': sinav_turu,
                            'Öğrenci Sayısı': len(ogrenciler)
                        })
                    
                    df = pd.DataFrame(data)
                    
                    # Tarih formatını düzenle (sheet ismi için)
                    sheet_name = tarih.replace('-', '_')
                    df.to_excel(writer, sheet_name=sheet_name, index=False)
            
            return True, f"Excel raporu başarıyla oluşturuldu: {dosya_adi}"
        
        except Exception as e:
            return False, f"Excel oluşturma hatası: {str(e)}"
    
    def sinav_programi_pdf(self, bolum_id, dosya_adi):
        """
        Sınav programını PDF olarak dışa aktar
        
        Args:
            bolum_id: Bölüm ID
            dosya_adi: Çıktı dosya adı
            
        Returns:
            (basari, mesaj)
        """
        try:
            # Sınav programını al
            sinavlar = self.db.get_sinav_programi(bolum_id)
            
            if not sinavlar:
                return False, "Sınav programı bulunamadı!"
            
            # Bölüm bilgisini al
            bolum = self.db.get_bolum_by_id(bolum_id)
            bolum_adi = bolum[1] if bolum else "Bilinmeyen Bölüm"
            
            # PDF oluştur
            doc = SimpleDocTemplate(dosya_adi, pagesize=landscape(A4))
            story = []
            
            # Stil tanımlamaları
            styles = getSampleStyleSheet()
            
            # Başlık stili
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=16,
                textColor=colors.HexColor('#1f4788'),
                spaceAfter=30,
                alignment=TA_CENTER,
                fontName='Arial-Bold'
            )
            
            # Günlere göre grupla
            gunluk_program = {}
            for sinav in sinavlar:
                tarih = sinav[4]
                if tarih not in gunluk_program:
                    gunluk_program[tarih] = []
                gunluk_program[tarih].append(sinav)
            
            # Her gün için tablo oluştur
            for tarih in sorted(gunluk_program.keys()):
                # Tarih başlığı
                tarih_obj = datetime.strptime(tarih, '%Y-%m-%d')
                tarih_str = tarih_obj.strftime('%d.%m.%Y - %A')
                
                title = Paragraph(f"{bolum_adi}<br/>Sınav Programı - {tarih_str}", title_style)
                story.append(title)
                story.append(Spacer(1, 12))
                
                # Tablo verileri
                gunun_sinavlari = gunluk_program[tarih]
                
                data = [['Ders Kodu', 'Ders Adı', 'Derslik', 'Başlangıç', 'Bitiş', 'Öğrenci Sayısı']]
                
                for sinav in gunun_sinavlari:
                    ders_kodu = sinav[9]
                    ders_adi = sinav[10]
                    derslik_adi = sinav[11]
                    baslangic = sinav[5]
                    bitis = sinav[6]
                    
                    # Öğrenci sayısını al
                    ogrenciler = self.db.get_dersi_alan_ogrenciler(sinav[2])
                    
                    data.append([
                        ders_kodu,
                        ders_adi[:30],  # Uzun isimleri kısalt
                        derslik_adi,
                        baslangic,
                        bitis,
                        str(len(ogrenciler))
                    ])
                
                # Tablo oluştur
                table = Table(data, colWidths=[3*cm, 6*cm, 3*cm, 2.5*cm, 2.5*cm, 3*cm])
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f4788')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Arial-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 12),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('FONTNAME', (0, 1), (-1, -1), 'Arial'),
                    ('FONTSIZE', (0, 1), (-1, -1), 10),
                ]))
                
                story.append(table)
                story.append(PageBreak())
            
            # PDF'i kaydet
            doc.build(story)
            
            return True, f"PDF raporu başarıyla oluşturuldu: {dosya_adi}"
        
        except Exception as e:
            return False, f"PDF oluşturma hatası: {str(e)}"
    
    def oturma_duzeni_pdf(self, sinav_id, dosya_adi):
        """
        Oturma düzenini PDF olarak dışa aktar
        
        Args:
            sinav_id: Sınav ID
            dosya_adi: Çıktı dosya adı
            
        Returns:
            (basari, mesaj)
        """
        try:
            # Sınav bilgilerini al
            sinav = self.db.cursor.execute('''
                SELECT sp.*, d.ders_kodu, d.ders_adi
                FROM sinav_programi sp
                INNER JOIN dersler d ON sp.ders_id = d.id
                WHERE sp.id = ?
            ''', (sinav_id,)).fetchone()
            
            if not sinav:
                return False, "Sınav bulunamadı!"
            
            # Oturma düzenini al
            oturma = self.db.get_oturma_duzeni(sinav_id)
            
            if not oturma:
                return False, "Oturma düzeni bulunamadı!"
            
            # PDF oluştur
            doc = SimpleDocTemplate(dosya_adi, pagesize=landscape(A4))
            story = []
            
            # Stil tanımlamaları
            styles = getSampleStyleSheet()
            
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=14,
                textColor=colors.HexColor('#1f4788'),
                spaceAfter=20,
                alignment=TA_CENTER,
                fontName='Arial-Bold'
            )
            
            # Başlık
            ders_kodu = sinav[9]
            ders_adi = sinav[10]
            tarih = sinav[4]
            baslangic = sinav[5]
            
            title = Paragraph(
                f"Oturma Düzeni<br/>{ders_kodu} - {ders_adi}<br/>{tarih} {baslangic}",
                title_style
            )
            story.append(title)
            story.append(Spacer(1, 12))
            
            # Dersliklere göre grupla
            derslik_oturma = {}
            for kayit in oturma:
                derslik_adi = kayit[8]
                if derslik_adi not in derslik_oturma:
                    derslik_oturma[derslik_adi] = []
                derslik_oturma[derslik_adi].append(kayit)
            
            # Her derslik için tablo
            for derslik_adi, kayitlar in derslik_oturma.items():
                # Derslik başlığı
                derslik_title = Paragraph(f"Derslik: {derslik_adi}", styles['Heading2'])
                story.append(derslik_title)
                story.append(Spacer(1, 12))
                
                # Tablo verileri
                data = [['Sıra No', 'Sütun No', 'Öğrenci No', 'Ad Soyad']]
                
                for kayit in sorted(kayitlar, key=lambda k: (k[4], k[5])):  # sira_no, sutun_no
                    sira_no = kayit[4]
                    sutun_no = kayit[5]
                    ogrenci_no = kayit[6]
                    ad_soyad = kayit[7]
                    
                    data.append([
                        str(sira_no + 1),
                        str(sutun_no + 1),
                        ogrenci_no,
                        ad_soyad
                    ])
                
                # Tablo oluştur
                table = Table(data, colWidths=[2*cm, 2*cm, 3*cm, 8*cm])
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f4788')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Arial-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 11),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('FONTNAME', (0, 1), (-1, -1), 'Arial'),
                    ('FONTSIZE', (0, 1), (-1, -1), 9),
                ]))
                
                story.append(table)
                story.append(Spacer(1, 20))
            
            # PDF'i kaydet
            doc.build(story)
            
            return True, f"Oturma düzeni PDF'i başarıyla oluşturuldu: {dosya_adi}"
        
        except Exception as e:
            return False, f"PDF oluşturma hatası: {str(e)}"

