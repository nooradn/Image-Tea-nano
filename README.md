![WhatsApp Group](https://img.shields.io/badge/Join%20WhatsApp-Group-25D366?logo=whatsapp&style=for-the-badge&link=https://chat.whatsapp.com/CMQvDxpCfP647kBBA6dRn3)

## Mendapatkan API Key
Jika kamu tidak memiliki API key Gemini, kamu bisa join grup WhatsApp di atas untuk mendapatkan key shared dari komunitas.

# Image-Tea-nano


Image-Tea-nano adalah metadata generator ringan, simpel, dan jujur.

Fokus utama Image-Tea-nano adalah pada fungsi dan kemudahan penggunaan, bukan pada tampilan visual atau fitur-fitur fancy. Semua fitur dirancang agar sederhana, efisien, dan langsung ke tujuan.

## Cara Install Git
1. Download Git dari https://git-scm.com/download/win
2. Jalankan installer dan ikuti petunjuk instalasi.
3. Setelah selesai, pastikan perintah `git --version` dapat dijalankan di Command Prompt atau PowerShell.

### Langkah-langkah Clone Repository:

#### 1. Buka Command Prompt atau PowerShell
- Tekan tombol `Windows` di keyboard.
- Ketik `cmd` lalu tekan `Enter` untuk membuka Command Prompt, atau ketik `powershell` lalu tekan `Enter` untuk membuka PowerShell.

#### 2. Pilih Folder Tempat Menyimpan Project
- Misal kamu ingin menyimpan di folder `D:\Project`, maka ketik:
  ```
  cd /d D:\Project
  ```
  Jika folder belum ada, buat dulu dengan:
  ```
  mkdir D:\Project
  cd /d D:\Project
  ```
- Jika ingin di Desktop, ketik:
  ```
  cd %USERPROFILE%\Desktop
  ```

#### 3. Jalankan Perintah Clone
- Ketik perintah berikut lalu tekan `Enter`:
  ```
  git clone https://github.com/mudrikam/Image-Tea-nano.git
  ```
- Tunggu proses selesai. Akan muncul folder baru bernama `Image-Tea-nano` di lokasi yang kamu pilih.

#### 4. Masuk ke Folder Project
- Setelah proses clone selesai, masuk ke folder project dengan perintah:
  ```
  cd Image-Tea-nano
  ```

#### 5. Cek Isi Folder
- Untuk melihat file di dalam folder, ketik:
  ```
  dir
  ```
  (di Command Prompt/PowerShell Windows)
- Pastikan ada file seperti `Launcher.bat` dan folder lain.

### Catatan
- Jika muncul pesan error seperti `'git' is not recognized`, berarti Git belum terinstall atau belum ditambahkan ke PATH.
- Jika ingin mengulang proses clone, hapus dulu folder `Image-Tea-nano` yang lama.

## Cara Menjalankan
Setelah repository berhasil di-clone, jalankan file `Launcher.bat` dengan cara:

1. Buka folder hasil clone (`Image-Tea-nano`).
2. Klik dua kali `Launcher.bat` atau jalankan perintah berikut di Command Prompt:
   ```
   Launcher.bat
   ```

## Cara Update
Untuk memperbarui aplikasi ke versi terbaru, gunakan file `update via git.bat` yang sudah disediakan. Proses update ini juga memberikan opsi untuk menghapus database lama jika ada perubahan struktur database.

### Langkah-langkah Update:
1. **Pastikan sudah berada di folder `Image-Tea-nano`.**
2. **Jalankan file `update via git.bat`:**
   - Klik dua kali `update via git.bat` di Windows Explorer, atau
   - Jalankan perintah berikut di Command Prompt:
     ```
     update via git.bat
     ```
3. **Ikuti petunjuk di layar:**
   - Script akan menampilkan peringatan jika ada kemungkinan perubahan struktur database.
   - Kamu akan diberi pilihan untuk menghapus database lama (`database\database.db`). Jika database dihapus, semua data dan API key yang tersimpan akan hilang.
   - Jika memilih untuk tidak menghapus database, lanjutkan update dengan risiko data lama mungkin tidak kompatibel.
4. **Jika diminta login git:**
   - Jika belum pernah login git di komputer, masukkan username dan email GitHub kamu saat diminta.
5. **Script akan menjalankan perintah `git pull` untuk mengambil update terbaru dari repository.**
6. **Setelah update selesai, aplikasi akan otomatis menjalankan `Launcher.bat` untuk melanjutkan proses seperti biasa.**

### Catatan Penting:
- **Backup API key dan data penting kamu sebelum update**, terutama jika memilih menghapus database lama.
- **Aplikasi ini tidak mendukung migrasi database otomatis.** Jika ada perubahan struktur database, data lama bisa jadi tidak terbaca.
- **Jika update gagal karena Git belum terinstall**, silakan install Git terlebih dahulu seperti pada petunjuk di atas.

Dengan mengikuti langkah-langkah di atas, aplikasi kamu akan selalu terupdate ke versi terbaru dari repository resmi.