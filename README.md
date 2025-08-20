# Ringkasan Image-Tea-nano

**Image-Tea-nano** adalah generator metadata ringan, simpel, dan mudah digunakan. Fokus utamanya fungsi, bukan tampilan fancy.

---

## Install & Clone

1. **Install Git**: Unduh di [git-scm.com](https://git-scm.com/download/win).
2. **Buka CMD/PowerShell**.
3. **Pilih folder project**:

   ```bash
   cd /d D:\Project
   ```

   atau ke Desktop:

   ```bash
   cd %USERPROFILE%\Desktop
   ```
4. **Clone repo**:

   ```bash
   git clone https://github.com/mudrikam/Image-Tea-nano.git
   ```
5. **Masuk folder**:

   ```bash
   cd Image-Tea-nano
   ```

---

## Jalankan Aplikasi

* Klik `Launcher.bat` atau jalankan di CMD:

  ```bash
  Launcher.bat
  ```

---

## Update Aplikasi

1. Pastikan berada di folder `Image-Tea-nano`.
2. Jalankan:

   ```bash
   update via git.bat
   ```
3. Pilih opsi jika ingin hapus database lama (`database\database.db`).
4. Update selesai → otomatis jalankan `Launcher.bat`.

---

## Catatan Penting

* Backup API key & data sebelum update.
* Hapus database lama jika struktur berubah (data lama hilang).
* Jika Git error, pastikan sudah terinstall dan masuk PATH.
