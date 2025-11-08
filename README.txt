# 🧬 PDF Encryptor – ROT47 + XOR + Base64

## 📖 Deskripsi
Aplikasi ini adalah **web tool enkripsi dan dekripsi file PDF** berbasis Python Flask.  
Sistem ini mengimplementasikan metode **enkripsi berlapis** menggunakan algoritma ringan yang bersifat **reversible (bisa dibalik)**, yaitu:
- **Base64 Encoding**
- **ROT47 Cipher**
- **XOR Password Encryption**

Tujuannya adalah untuk **mendemonstrasikan konsep dasar kriptografi sederhana** dalam bentuk aplikasi web interaktif.

---

## ⚙️ Fitur
- Enkripsi teks PDF dengan urutan **Base64 → ROT47 → XOR(password)**  
- Dekripsi teks PDF dengan urutan kebalikan  
- Hasil akhir tetap berupa **file PDF valid** yang dapat dibuka  
- Dapat dijalankan secara **lokal** melalui web browser  
- Tampilan futuristik berbasis **HTML + CSS (Glassmorphism UI)**

---

## 🧩 Arsitektur Sistem
Client (Browser)
│
├── Upload file PDF + password
│
Flask Backend (Python)
├── Ekstraksi teks PDF
├── Enkripsi teks (Base64 + ROT47 + XOR)
├── Buat file PDF baru berisi hasil enkripsi
│
└── Kirim hasil ke client untuk diunduh

yaml
Salin kode

---

## 🔐 Alur Enkripsi
1. Teks dari file PDF diekstraksi.
2. Hasil teks dikonversi ke format **Base64**.
3. Dilakukan transformasi karakter dengan **ROT47**.
4. Hasil ROT47 diubah menggunakan **XOR** berdasarkan password.
5. Output akhir diubah kembali ke **Base64** agar bisa ditulis ke file PDF.

---

## 🔓 Alur Dekripsi
1. Decode Base64 dari teks terenkripsi.
2. XOR hasilnya dengan password yang sama.
3. Balikkan transformasi ROT47.
4. Decode Base64 terakhir untuk mendapatkan teks asli.
5. Hasil dekripsi ditulis kembali ke halaman PDF baru.

---

## 🧠 Fungsi Utama
| Fungsi | Deskripsi |
|--------|------------|
| `rot47(s)` | Menggeser karakter ASCII sejauh 47 posisi (33–126). |
| `xor_with_password(data, password)` | Melakukan XOR setiap byte dengan password. |
| `encrypt_text_payload(plain_bytes, password, label)` | Menjalankan pipeline Base64 → ROT47 → XOR → Base64. |
| `decrypt_text_payload(enc_text, password)` | Membalik seluruh urutan enkripsi untuk mendapatkan teks asli. |
| `make_overlay_pdf(w, h, text)` | Membuat halaman PDF berisi teks terenkripsi/dekripsi. |

---

## 🗂️ Struktur Folder
project_root/
│
├── app.py # File utama Flask
├── templates/
│ └── index.html # Tampilan upload PDF
├── static/
│ └── style.css # Desain antarmuka
└── README.md # Dokumentasi proyek

yaml
Salin kode

---

## 🧰 Instalasi dan Menjalankan Aplikasi

### 1️⃣ Install dependensi
```bash
pip install flask pypdf reportlab
2️⃣ Jalankan server lokal
bash
Salin kode
python app.py
3️⃣ Akses melalui browser
cpp
Salin kode
http://127.0.0.1:5000
💡 Catatan
Sistem ini bukan untuk keamanan nyata, hanya untuk edukasi dan riset konsep kriptografi dasar.

Hasil enkripsi tidak bisa dibuka tanpa password yang tepat.

Algoritma ROT47 dan XOR bersifat deterministik: output selalu sama untuk kombinasi pesan dan password yang sama.

Semua proses dijalankan lokal tanpa menyimpan data pengguna.

👨‍💻 Developer Notes
Project ini dirancang untuk pembelajaran enkripsi tingkat dasar dengan implementasi web-based real-time.
Menggabungkan konsep data encoding, cipher rotation, dan XOR masking dalam satu pipeline yang mudah dipahami.

📚 Lisensi
Proyek ini bersifat open-source untuk keperluan pembelajaran dan penelitian.
Penggunaan untuk data sensitif tidak disarankan.