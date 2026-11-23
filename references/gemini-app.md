# Gemini App (Skills): Batasan dan Cara Pasang

Gemini app (gemini.google.com, app Gemini di Mac, dan app mobile) adalah lingkungan percakapan, bukan agen coding lokal. Banyak skill Claude Code tidak bisa berjalan di sana apa adanya. Baca file ini sebelum mengonversi untuk target Gemini app. Diverifikasi ke halaman bantuan resmi pada 2026-11-21 (https://support.google.com/gemini/answer/17094296 dan https://support.google.com/gemini/answer/17102773). Saat ini syaratnya berusia 18 tahun ke atas dan masuk ke akun Gemini. Syarat akun, ketersediaan, dan batasan bisa berubah, jadi cek ulang halaman itu bila ada selisih.

## Cara Memasang

1. Buka gemini.google.com (atau app Gemini di Mac), lalu di sidebar klik **Customize** (jika tidak terlihat, klik **More** dulu) dan pilih **Skills** di bagian atas.
2. Klik **Create** > **Upload**, lalu pilih salah satu: file `SKILL.md`, folder, atau `.zip` yang berisi `SKILL.md` di folder utama (root).
3. Tinjau skill, ubah bila perlu, lalu klik **Create**.

Catatan:

- Unggah paling andal lewat web (gemini.google.com). Halaman bantuan Android menyebut opsi unggah belum tersedia di app mobile, dan pengelolaan penuh (termasuk berbagi) hanya di web. Skill yang dibuat di web tetap bisa dipakai di app mobile.
- Untuk memperbarui file di dalam skill, unggah ulang seluruh skill beserta file referensinya (atau gunakan **Replace skill**). File referensi hanya bisa ditambahkan saat unggah.
- Skill boleh merujuk skill lain di dalam instruksinya (menurut halaman bantuan), jadi unggah semua skill yang saling merujuk.
- Pemanggilan manual: ketik `/` (atau `@`) di percakapan lalu pilih skill. Gemini juga memakai skill yang aktif secara otomatis berdasarkan konteks.
- Skill dapat dinonaktifkan tanpa dihapus lewat menu skill (Deactivate), dan dapat dibagikan dari web.

## Batasan yang Mempengaruhi Konversi

1. **Tidak ada terminal, git, atau filesystem proyek.** Skill yang berbasis perintah shell, `git`, atau membaca repositori lokal tidak akan berfungsi. Ubah menjadi skill instruksi murni (misalnya minta pengguna menempelkan diff atau isi file), atau sarankan Antigravity atau Gemini CLI.
2. **Script tanpa internet.** Script yang membutuhkan internet tidak didukung, dan script tidak boleh membuat permintaan ke situs eksternal.
3. **Tipe file referensi.** Didukung antara lain `.md`, `.txt`, `.pdf`, `.docx`, `.xlsx`, `.pptx`, `.csv`, `.json`, `.yaml`, `.toml`, `.xml`, `.html`, `.css`, gambar umum, serta `.py`, `.sh`, `.js`, dan `.ipynb`. Tidak didukung: `.doc`, `.xls`, `.ppt`, `.raw`, audio dan video, arsip (zip, tar, dan sejenisnya), `.cs`, `.kt`, `.kts`, `.php`, `.r`, `.rb`, `.scala`, `.swift`, `.ts`, `.jsx`, `.tsx`, dan `.sql`.
4. **Ukuran dan bundel.** Total semua file maksimal 100 MB. File biner tersembunyi seperti `.DS_Store` dan `.pyc` dapat membuat unggahan gagal.
5. **Nama skill.** Di `SKILL.md`, `name` wajib huruf kecil dengan kata dipisah tanda hubung (misalnya `my-new-skill`).
6. **Layanan Google.** Akses ke Google Workspace (Calendar, Drive) dari skill bergantung pada pengaturan Keep Activity. Dengan Keep Activity mati, fitur itu tidak tersedia.
7. **Tidak ada hooks, subagent, plugin, dan MCP** seperti di Antigravity atau Gemini CLI.

## Cara Menyesuaikan Skill

- Ganti file bertipe tidak didukung dengan versi yang didukung: ubah `.ts` atau `.sql` referensi menjadi `.txt` atau `.md`, atau pindahkan isinya ke `SKILL.md` atau `references/*.md`.
- Hapus `.DS_Store`, `__pycache__`, dan `*.pyc` sebelum mengunggah.
- Hapus langkah terminal. Ganti dengan instruksi yang meminta pengguna menyediakan data langsung di percakapan.
- Tulis `description` dengan awalan "Use when ..." dalam sudut pandang orang ketiga, kurang dari 1024 karakter. Awali `name` dengan kata kerja yang menjelaskan aksi dan hindari kata generik seperti `helper` atau `tools`.
- Pertahankan skill sebagai lembar contekan yang ringkas: instruksi cepat, aturan format, dan kesalahan umum yang harus dihindari. Beri tahu Gemini apa yang harus dilakukan bila informasi kurang (tanya pengguna, jangan menebak).

## Validasi Sebelum Unggah

```bash
python3 <skill_dir>/scripts/validate_skill.py <folder-skill> --target gemini-app
```

Mode `gemini-app` memeriksa tipe file yang tidak didukung, file tersembunyi, ukuran bundel, dan script yang tampak memakai jaringan.
