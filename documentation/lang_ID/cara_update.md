# Cara Update Image-Tea-nano

Berikut adalah langkah-langkah update 
Image-Tea-nano ke versi terbaru:

1. **Masuk ke Folder Project**
   - Buka folder `Image-Tea-nano` hasil clone.

2. **Jalankan Update**
   - Jalankan file `update via git.bat` dengan 
     klik dua kali, atau lewat Command Prompt:
     ```
     update via git.bat
     ```

3. **Ikuti Petunjuk**
   - Script akan menampilkan peringatan jika 
     ada perubahan struktur database.
   - Pilih apakah ingin menghapus database lama 
     (`database\database.db`) atau tidak.
   - Jika database dihapus, semua data dan API key 
     akan hilang.
   - Jika tidak dihapus, lanjutkan update dengan 
     risiko data lama mungkin tidak kompatibel.

4. **Login Git (Jika Diminta)**
   - Jika belum pernah login git, masukkan username 
     dan email GitHub saat diminta.

5. **Tunggu Proses Selesai**
   - Script akan menjalankan `git pull` untuk 
     mengambil update terbaru.
   - Setelah selesai, aplikasi akan otomatis 
     menjalankan `Launcher.bat`.

**Catatan Penting:**
- Backup API key dan data penting sebelum update, 
  terutama jika memilih hapus database lama.
- Aplikasi tidak mendukung migrasi database otomatis.
- Jika update gagal karena Git belum terinstall, 
  install Git terlebih dahulu.

Panduan ini hanya untuk Windows. Untuk sistem 
operasi lain, silakan tanyakan di grup WhatsApp 
komunitas.
