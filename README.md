# 🩸 KanVer - Konum Tabanlı Acil Kan Bağış Ağı
 
[![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://www.python.org/)

[![Status](https://img.shields.io/badge/Status-Prototip-success.svg)]()
 
**KanVer**, acil kan ihtiyacı duyan hastalar ile o an yakında bulunan gönüllü bağışçıları hızlı, güvenli ve anonim bir şekilde eşleştiren konum tabanlı bir dijital dayanışma platformudur.
 
Bu proje, **Toplumsal Dayanışma** dersi kapsamında geleneksel kan arama süreçlerindeki (sosyal medya karmaşası, zaman kaybı, bilgi kirliliği) sorunları çözmek amacıyla "Minimum Viable Product (MVP)" mimarisiyle geliştirilmiştir. Pilot bölge olarak **Antalya** seçilmiştir.
 
---
 
## 🚀 Temel Özellikler (Core Features)
 
* **📍 Konum Tabanlı Eşleşme (Geofencing):** Kan talepleri sadece hastane konumunda (örn: Akdeniz Üni. Hastanesi 500m çapı) oluşturulabilir ve yalnızca yakınlardaki (örn: 5-10 km) kullanıcılara bildirim gider.

* **📍 Talep oluşturulurken kullanıcıya sor:**

🔴 Tam Kan (Stok Takası): "Hastaya kan bankasından kan verilecek, yerine koymak için bağışçı aranıyor." (Daha az acil, 24 saat içinde bulunsa da olur).

⚪ Aferez Trombosit: "Hastaya taze trombosit lazım." (Çok acil, bağışçı hemen makineye bağlanmalı).

* **🔒 Dijital El Sıkışma & QR Onay:** KVKK gereği hasta ve bağışçı isimleri paylaşılmaz. Sistem `#ANT-KAN-482` gibi bir referans kodu üretir. Hastanedeki yetkili hemşire, bağışçının uygulamasındaki QR kodu okutarak işlemi güvenle tamamlar.

* **🤖 KanVer AI (LLM Entegrasyonu):** Kızılay kan bağışı kurallarına hakim, bağışçıların uygunluk durumunu (kullanılan ilaçlar, dövme geçmişi vb.) hastaneye gitmeden önce test eden yapay zeka destekli ön eleme asistanı.

* **⛓️ Hash Zinciri ile Veri Bütünlüğü:** Geçmiş bağış kayıtlarının manipüle edilmesini önlemek amacıyla, her işlemin bir önceki işlemin özetine (Hash) bağlandığı "Değiştirilemez (Immutable)" veritabanı mimarisi.

* **🔄 Dinamik Yönlendirme Algoritması (Race Condition Çözümü):** Aynı hasta için birden fazla bağışçı hastaneye ulaşırsa, sistem "N+1" kuralı ile fazla bağışçıları mağdur etmeden hastanenin genel kan stoğuna yönlendirir.
 
---
 
## 🛠️ Teknik Mimari (Tech Stack)
 
* **Frontend & Backend:** flutter + Python (Hızlı mobil/web prototipleme ve harita görselleştirme)

* **Veritabanı:** PostgreSQL / PostGIS (Rol tabanlı kullanıcı ve Hash zinciri yönetimi)

* **Yapay Zeka:** Google Gemini API (KanVer AI Chatbot altyapısı)

* **Konum Servisleri:** Geopy (Harita üzerinde hastane ve Kızılay tırlarının gösterimi, mesafe hesaplama)
 
---
 
## 📱 Kullanım Senaryosu (Workflow)
 
1. **Talep Oluşturma:** Hasta yakını, bulunduğu hastane konumunu doğrulayarak sistemi tetikler.

2. **Bildirim & Adaylık:** Yakındaki uygun kan grubuna sahip kullanıcılara bildirim gider. Gönüllüler "Geliyorum" diyerek havuzda (Pool) toplanır (Talep hemen kapanmaz).

3. **Ön Kontrol:** Yola çıkan bağışçı, uygulamadaki **KanVer AI**'a sorular sorarak kan vermeye uygun olup olmadığını teyit edebilir.

4. **Hastanede Doğrulama:** Bağışçı Kan Merkezi'ne ulaşır. Sisteme "Hemşire/Personel" rolüyle giriş yapan yetkili, bağışçının telefonundaki QR kodu okutur.

5. **İşlem Tamamlama:** Kan alımından sonra hemşire onay verir. Talep kapanır, bağışçının son bağış tarihi güncellenir ve sistemde "Kahramanlık Puanı" kazanır.
 
---
 
## 🛡️ Güvenlik ve Doğrulama Katmanları
 
Projeyi tasarlarken olası suistimalleri önlemek için aşağıdaki algoritmalar geliştirilmiştir:

- **No-Show Koruması:** "Geliyorum" deyip gelmeyen kullanıcılar için zaman aşımı (Time-out) ve güven puanı düşürme sistemi.

- **Sahte Talep Koruması:** Geofencing ile sadece hastane sınırları içinden talep açılabilmesi ve opsiyonel belge yükleme (OCR simülasyonu) zorunluluğu.

- **Veri Güvenliği (RBAC):** Sistemde *Kullanıcı*, *Hemşire* ve *Admin* olmak üzere 3 farklı yetki seviyesi bulunur. Hasta detaylarını sadece QR kodu okutan Hemşire görebilir.
 
---
 
## ⚙️ Kurulum (Kurulum Adımları)
 
Projeyi yerel ortamınızda çalıştırmak için:
 
```bash
 
# 2. Gerekli kütüphaneleri yükleyin

pip install -r requirements.txt
 
# 3. Çevre değişkenlerini ayarlayın (.env)

# GEMINI_API_KEY=your_api_key_here

 