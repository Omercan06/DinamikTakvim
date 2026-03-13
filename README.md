# 🎓 Dinamik Sınav Takvimi Oluşturma Sistemi

Dinamik Sınav Takvimi Oluşturma Sistemi, üniversiteler ve eğitim kurumları (özellikle Kocaeli Üniversitesi altyapısı örnek alınarak geliştirilmiştir) için tasarlanmış kapsamlı bir masaüstü otomasyon uygulamasıdır. Bölüm koordinatörlerinin ders, öğrenci ve derslik bilgilerini yönetmesini, çakışmaları önleyerek otomatik sınav programı oluşturmasını ve oturma düzenlerini ayarlamasını sağlar.

## ✨ Özellikler

* **Rol Tabanlı Yetkilendirme**: Yönetici (Admin) ve Bölüm Koordinatörü olmak üzere iki farklı kullanıcı rolü ile güvenli erişim.
* **Excel Entegrasyonu**: Öğrenci listeleri ve ders programlarını Excel (`.xlsx`) formatında toplu olarak sisteme aktarabilme.
* **Gelişmiş Sınav Planlama Algoritması**: 
  * Öğrenci çakışmalarını (aynı anda iki sınavı olan öğrenciler) denetleme.
  * Sınavları kapasiteye göre uygun dersliklere otomatik dağıtma.
  * Sıralı (ardışık) veya Paralel (aynı anda çoklu) sınav planlama modları.
* **Akıllı Oturma Düzeni (Zigzag Algoritması)**: Sınıf kapasitesi ve sıra yapısına (ikili, üçerli vb.) uygun olarak öğrencileri yan yana gelmeyecek şekilde (boşluklu) sınav salonlarına yerleştirme.
* **PDF ve Excel Raporlama**: Oluşturulan sınav takvimini Excel dosyası olarak, oturma düzenlerini ise yoklama listesi şeklinde PDF olarak dışa aktarma.
* **Modern Arayüz**: `Tkinter` ve `ttk` kullanılarak geliştirilmiş, kullanıcı dostu ve modern masaüstü arayüzü.

## 🛠️ Kullanılan Teknolojiler

* **Programlama Dili**: Python 3.x
* **Kullanıcı Arayüzü (GUI)**: Tkinter
* **Veritabanı**: SQLite3 (Yerleşik)
* **Veri İşleme ve Excel**: Pandas, OpenPyXL
* **PDF Üretimi**: ReportLab

## 🚀 Kurulum

Projeyi yerel makinenizde çalıştırmak için aşağıdaki adımları izleyin:

1. **Depoyu Klonlayın:**
   ```bash
   git clone [https://github.com/kullaniciadi/DinamikTakvim.git](https://github.com/kullaniciadi/DinamikTakvim.git)
   cd DinamikTakvim
