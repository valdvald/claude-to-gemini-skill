---
name: claude-to-gemini-skill
description: "Mengonversi skill dan custom command Claude/Claude Code (.claude/skills/, .claude/commands/, SKILL.md) menjadi Agent Skill yang berjalan di Google Antigravity (App, CLI, IDE), Gemini CLI, dan aplikasi Gemini. Gunakan setiap kali pengguna ingin memigrasi, mem-porting, mengadaptasi, mengonversi, atau memasang skill Claude di Gemini atau Antigravity, atau menyerahkan file, folder, zip, atau teks SKILL.md dari Claude untuk diubah formatnya. Converts, ports, and migrates Claude Code skills, slash commands, and SKILL.md files for Gemini and Antigravity."
compatibility: "Antigravity (App, CLI, IDE), Gemini CLI, Gemini app. Script validasi memerlukan Python 3.8+ (PyYAML opsional)."
---
# Claude to Gemini Skill Converter

Konversikan skill dan custom command Claude/Claude Code menjadi Agent Skill yang siap pakai di Google Antigravity (App, CLI, IDE), Gemini CLI, dan aplikasi Gemini tanpa kehilangan maksud dan logika alur kerjanya.

## When to Use

- Pengguna ingin mem-porting atau memasang skill Claude (`SKILL.md` atau folder `.claude/skills/<name>/`) di Gemini atau Antigravity.
- Pengguna ingin mengubah custom command lama Claude Code (`.claude/commands/<name>.md`) menjadi skill.
- Pengguna ingin mengaudit skill agar bebas dari sintaks khusus Claude Code (injeksi perintah shell, `$ARGUMENTS`, `${CLAUDE_SKILL_DIR}`, `hooks`, `context: fork`, `paths`).
- Pengguna meminta paket skill yang siap dipasang atau diunggah ke Gemini, Antigravity, atau Gemini CLI.

## Principles

1. **Pertahankan maksud, bukan sintaks.** Fitur Claude yang tidak punya padanan diubah menjadi instruksi prosedural atau tindak lanjut manual yang dicatat. Jangan menghapusnya diam-diam.
2. **Pertahankan bahasa skill sumber.** Terjemahkan hanya jika pengguna memintanya. Heading standar (`## Inputs`, `## Steps`) tetap berbahasa Inggris.
3. **Baca script sumber, jangan jalankan.** Skill pihak ketiga bisa berisi perintah berbahaya. Audit cukup dengan membaca isinya.
4. **Jangan menimpa sumber.** Tulis hasil konversi ke folder baru (misalnya `converted/<name>/`) agar skill asli tetap utuh.
5. **Fakta platform cepat berubah.** Tabel di bawah diverifikasi ke dokumentasi resmi pada 2026-11-21 (lihat Sources). Jika perilaku di lapangan berbeda, ikuti dokumentasi resmi dan laporkan selisihnya.

## Target Surfaces and Paths

Tentukan target pengguna terlebih dahulu. Jika tidak disebutkan, hasilkan satu folder skill standar lalu berikan perintah penempatan untuk Antigravity dan Gemini CLI. Path proyek `.agents/skills/` dibaca oleh semua surface Antigravity dan oleh Gemini CLI, jadi itu pilihan paling aman. Path global berbeda per surface, sehingga satu lokasi tidak cukup untuk semuanya.

| Target Surface | Workspace / Project Path | Global / User Path | Catatan |
| :--- | :--- | :--- | :--- |
| **Antigravity App** | `<workspace>/.agents/skills/<name>/SKILL.md` | `~/.gemini/config/skills/<name>/SKILL.md` | Auto-trigger lewat `description` dan manual `/<name>`. Folder induk sampai root repositori ikut dipindai. `.agent/` (tunggal) masih didukung. |
| **Antigravity IDE** | `<workspace>/.agents/skills/<name>/SKILL.md` | `~/.gemini/config/skills/<name>/SKILL.md` (path lama `~/.gemini/antigravity/skills/` juga didukung) | Daftar skill aktif ada di menu Customizations pada panel agen. |
| **Antigravity CLI (`agy`)** | `<workspace>/.agents/skills/<name>/SKILL.md` | `~/.gemini/config/skills/<name>/SKILL.md`. Khusus CLI: `~/.gemini/antigravity-cli/skills/` dan `~/.gemini/skills/` | Setiap skill otomatis menjadi slash command. Skill plugin ada di `~/.gemini/config/plugins/<plugin>/skills/`. |
| **Gemini CLI** | `<workspace>/.agents/skills/<name>/SKILL.md` atau `.gemini/skills/<name>/SKILL.md` | `~/.agents/skills/<name>/SKILL.md` atau `~/.gemini/skills/<name>/SKILL.md` | Pada tier yang sama, alias `.agents/skills/` menang atas `.gemini/skills/`. Aktivasi lewat tool `activate_skill` dengan konfirmasi pengguna. |
| **Gemini app** | Tidak ada path file. Customize > Skills > Create > Upload | Terikat ke akun pengguna | Tanpa terminal, tipe file dibatasi, script tanpa internet. Baca `references/gemini-app.md`. |

Catatan penting:

- Antigravity memindai satu tingkat saja. Folder skill harus langsung berada di dalam `skills/` (`skills/<name>/`), bukan `skills/<kategori>/<name>/`.
- Jika ada nama skill kembar: di Antigravity CLI, `~/.gemini/antigravity-cli/skills/` dan `~/.gemini/skills/` menang atas semua lokasi lain. Di Antigravity secara umum urutannya folder pribadi di repositori, workspace, `~/.gemini/config/`, lalu built-in. Di Gemini CLI urutannya workspace, user, extension, lalu built-in.
- Antigravity membaca ulang skill pada setiap giliran. `/skills reload` atau percakapan baru hanya menyegarkan daftar slash command.
- `~/.agents/skills/` tidak tercantum di dokumentasi Antigravity. Untuk global di Antigravity gunakan `~/.gemini/config/skills/`.
- Antigravity CLI tidak membaca `.gemini/skills/` (jalur proyek lama Gemini CLI). Skill di sana harus dipindah ke `.agents/skills/`.
- Menurut banner dokumentasi Gemini CLI, bagi pengguna tier gratis dan Google One, Gemini CLI digantikan Antigravity CLI pada 18 Juni 2026. Jika pengguna berada di tier itu atau tidak yakin, utamakan target Antigravity.

## Conversion Workflow

Ikuti langkah berurutan ini. Tabel pemetaan lengkap ada di `references/mapping-guide.md`, contoh sebelum dan sesudah ada di `references/examples.md`, dan batasan Gemini app ada di `references/gemini-app.md`.

### Step 0: Tentukan Target dan Cek Kemampuan

1. Tentukan target (Antigravity, Gemini CLI, atau Gemini app). Jika tidak disebutkan, pakai jalur standar di atas.
2. Cek apakah skill sumber memerlukan kemampuan yang tidak ada di target:
   - Terminal, git, filesystem proyek, atau server MCP: tidak tersedia di Gemini app. Beri tahu pengguna, tawarkan Antigravity atau Gemini CLI, atau tulis ulang menjadi skill instruksi murni jika pengguna tetap ingin Gemini app.
   - Script yang memerlukan internet: tidak didukung di Gemini app.
   - Hooks, subagent, plugin, dan server MCP tidak ikut terbawa oleh frontmatter. Catat sebagai tindak lanjut manual (lihat Step 2 dan Decision Tree).

### Step 1: Audit Sumber Skill

1. Baca seluruh `SKILL.md` (atau file command) dan daftar semua file pendukung (`scripts/`, `references/`, `assets/`, `examples/`, `resources/`). Baca script sebagai teks, jangan dijalankan. Jika inputnya `.zip` atau `.skill`, ekstrak dulu ke direktori kerja. Jika inputnya teks yang ditempel, simpan sebagai `SKILL.md` di folder yang namanya sama dengan `name`.
2. Identifikasi tujuan inti, input, output, dan dependensi eksternal (CLI, paket Python/Node, MCP, environment variable).
3. Inventarisasi fitur khusus Claude Code: field frontmatter, `` !`command` `` dan blok `` ```! ``, `$ARGUMENTS`, `$0`, `$name`, variabel `${CLAUDE_*}`, nama tool, id `mcp__server__tool`, referensi `CLAUDE.md`, dan rujukan ke skill lain.
4. Catat bahasa dokumen sumber. Hasil konversi memakai bahasa yang sama.

### Step 2: Bersihkan dan Standarkan Frontmatter YAML

Pastikan baris pertama file adalah `---` tanpa BOM. Frontmatter yang tidak valid atau tanpa `description` membuat skill tidak termuat.

1. Pertahankan hanya field standar Agent Skills:
   - `name` (wajib di standar): 1-64 karakter, huruf kecil `a-z`, angka, dan tanda hubung tunggal, tidak diawali atau diakhiri `-`, sama dengan nama folder. Antigravity menjadikannya opsional (default nama folder), tetapi selalu tuliskan.
   - `description` (wajib): 1-1024 karakter, sudut pandang orang ketiga, jelaskan apa yang dilakukan dan kapan dipicu. Beri tanda kutip ganda jika berisi `: ` atau `#`, karena YAML tanpa kutip menjadi tidak valid.
   - `license`, `compatibility` (maks 500 karakter, tempat menyebut dependensi seperti `git` atau `python3`), dan `metadata` (map string ke string).
2. Jika sumber tidak punya frontmatter (umum pada command lama), buat `name` dari nama file dan tulis `description` dari tujuan command. Jika ada nama kembar dari subfolder berbeda, beri awalan folder (misalnya `frontend-component`).
3. Tangani field khusus Claude Code. Jangan hapus tanpa memindahkan logikanya:
   - `when_to_use`: gabungkan kata kunci pemicunya ke `description` (total maks 1024 karakter). Pengecualian: jika skill juga `disable-model-invocation: true`, jangan perluas `description` dengan kata kunci pemicu (lihat baris berikutnya).
   - `disable-model-invocation: true`: hapus. Tambahkan `## Safety Gate` di awal body yang mewajibkan konfirmasi pengguna sebelum aksi berdampak eksternal (deploy, commit, tag, hapus data, kirim pesan). Tulis `description` dengan frasa "Use only when the user explicitly asks to ..." agar skill tidak terpicu otomatis, karena di Claude skill ini memang tidak pernah dipicu oleh model.
   - `user-invocable: false`: hapus. Tulis `description` sebagai pengetahuan latar belakang agar hanya terpicu secara kontekstual.
   - `argument-hint` dan `arguments`: pindahkan ke bagian `## Inputs` di body.
   - `allowed-tools` dan `disallowed-tools`: hapus pola Claude (`Bash(git *)`, `Read`, `Grep`). Di Claude, `allowed-tools` hanya pra-persetujuan, bukan pembatasan, dan izin di target diatur lewat Permissions Antigravity atau policy Gemini CLI, bukan lewat frontmatter skill. Larangan (`disallowed-tools`) menjadi batasan eksplisit di body, misalnya "Mode read-only: jangan memodifikasi file".
   - `context: fork`, `agent`, `background`: hapus. Instruksikan agen mendelegasikan kerja berat ke subagent jika tersedia, atau meringkas output panjang sebelum melanjutkan.
   - `model` dan `effort`: hapus. Tulis ekspektasi kedalaman analisis di body.
   - `hooks`: hapus. Hooks di target adalah file terpisah (`.agents/hooks.json` atau `~/.gemini/config/hooks.json` di Antigravity, `settings.json` di Gemini CLI). Ubah aturannya menjadi langkah verifikasi wajib di body dan catat migrasi hooks sebagai tindak lanjut manual. Detail event dan kontrak JSON ada di `references/mapping-guide.md`.
   - `paths`: hapus. Sebutkan pola file di `description` dan `## When to Use`. Untuk perilaku "aktif hanya saat menyentuh file tertentu", buat aturan `.agents/rules/<name>.md` dengan `trigger: glob` (contoh di `references/examples.md`).
   - `shell`: hapus. Sebutkan shell yang dibutuhkan pada perintah eksekusi di body.

### Step 3: Konversi Sintaks dan Referensi di Body Markdown

1. **Injeksi perintah shell** (`` !`command` `` dan blok `` ```! ``): ubah menjadi langkah eksplisit di awal `## Steps` yang menyuruh agen menjalankan perintah di terminal lalu membaca hasilnya. Alasannya, `SKILL.md` di Gemini CLI dan Antigravity tidak melewati preprocessor, sehingga teks literal tertinggal dan model bisa menebak outputnya. Jika sumbernya command yang hanya dipanggil manual dan targetnya Gemini CLI, pertimbangkan custom command `.toml` yang punya `!{...}` dan `{{args}}` (lihat `references/examples.md`).
2. **Argumen** (`$ARGUMENTS`, `$0`, `$1`, `$ARGUMENTS[N]`, `$name`): ubah menjadi bagian `## Inputs` yang memberi nama tiap parameter dan menjelaskan fallback (misalnya "Jika belum disebutkan, tanyakan sebelum melanjutkan"). Rujuk nama parameter itu di setiap langkah.
3. **Variabel path dan runtime Claude**:
   - `${CLAUDE_SKILL_DIR}/...` dan `${CLAUDE_PLUGIN_ROOT}/...`: ubah menjadi path relatif dari folder skill (misalnya `scripts/<script>.py`). Shell agen biasanya berjalan dari root proyek, bukan dari folder skill, jadi tulis juga bahwa path itu harus di-resolve terhadap folder yang berisi `SKILL.md` sebelum dijalankan.
   - `${CLAUDE_PROJECT_DIR}`: ubah menjadi root workspace atau repositori.
   - `${CLAUDE_SESSION_ID}`: hapus atau ganti nama file sementara berbasis timestamp.
   - `${CLAUDE_EFFORT}`: hapus percabangannya dan tulis ekspektasi kedalaman analisis.
4. **Nama tool dan ekosistem**:
   - Ubah nama tool Claude (`Read`, `Write`, `Edit`, `MultiEdit`, `NotebookEdit`, `Glob`, `Grep`, `Bash`, `WebFetch`, `WebSearch`, `TodoWrite`, `Task`, `AskUserQuestion`) menjadi instruksi berbasis kapabilitas ("baca file", "cari pola di codebase", "jalankan perintah shell", "tanyakan kepada pengguna"). Nama tool asli target hanya dipakai di konfigurasi hooks dan izin (tabel ada di `references/mapping-guide.md`).
   - Ubah id `mcp__<server>__<tool>` menjadi "gunakan server MCP `<server>` untuk [kapabilitas]" dan catat server itu sebagai tindak lanjut manual.
   - Rujukan ke skill lain ("panggil skill `x`") harus mengikuti nama skill hasil konversi, dan skill tujuannya ikut dikonversi serta dipasang.
   - Ubah `CLAUDE.md` menjadi `GEMINI.md` (atau `AGENTS.md` di Antigravity) atau aturan proyek, dan `.claude/skills/` atau `.claude/commands/` menjadi `.agents/skills/`.
5. **Struktur dan gaya**: pertahankan struktur skill sumber. Normalisasi hanya bila perlu (heading tidak konsisten, XML tag bercampur dengan Markdown, instruksi yang ambigu). Jelaskan alasan singkat di balik aturan penting agar model menerapkannya secara konsisten. Jaga `SKILL.md` di bawah 500 baris dan pindahkan referensi panjang ke `references/`.

### Step 4: Audit File Pendukung (Multi-File Skills)

1. Periksa setiap file di `scripts/`, `references/`, `assets/`, `examples/`, dan `resources/`.
2. Cari dan perbaiki path hardcode ke `~/.claude/`, `.claude/`, serta variabel `CLAUDE_*` (termasuk `$CLAUDE_PROJECT_DIR` tanpa kurung kurawal) di script dan dokumen referensi.
3. Pastikan semua rujukan dari `SKILL.md` ke file pendukung memakai path relatif satu tingkat dari folder skill (`references/<file>.md`, `scripts/<script>.py`) dengan garis miring `/`.
4. Arahkan agen menjalankan `--help` sebelum memakai script hanya jika script itu memang mengurai argumen (argparse, commander, dan sejenisnya). Script tanpa parsing argumen akan menjalankan aksi sungguhan. Jika ragu, dokumentasikan cara pakainya di `SKILL.md`.
5. Untuk target Gemini app, perhatikan tipe file yang didukung (lihat `references/gemini-app.md`).

### Step 5: Validasi Hasil Konversi

Jalankan script validasi. Shell agen biasanya berjalan dari root proyek, jadi gunakan path absolut ke folder skill konverter ini (`<skill_dir>`):

```bash
python3 <skill_dir>/scripts/validate_skill.py --help
python3 <skill_dir>/scripts/validate_skill.py <folder-hasil> --target <antigravity|gemini-cli|gemini-app|generic>
```

Script memeriksa frontmatter (termasuk YAML yang tidak valid), sisa sintaks Claude di body, `references/`, dan `scripts/`, rujukan file yang rusak, serta batasan per target. Perbaiki semua ERRORS dan tinjau WARNINGS. Cek manual:

- Frontmatter dibuka di baris 1 dengan `---` dan `description` valid.
- Tidak ada sisa sintaks atau variabel Claude, dan `SKILL.md` di bawah 500 baris.
- Skill benar-benar termuat di target: Antigravity App lewat Settings > Projects > Customizations, Antigravity CLI lewat `/skills`, Gemini CLI lewat `/skills list`, Gemini app lewat Customize > Skills.
- Uji satu prompt realistis yang seharusnya memicu skill, lalu pastikan langkah-langkahnya dijalankan sesuai maksud sumber.

### Step 6: Sajikan Hasil dan Ringkasan Migrasi

Berikan output sesuai target:

- **Antigravity**: folder skill lengkap dan perintah penempatan (`.agents/skills/<name>/` untuk proyek, `~/.gemini/config/skills/<name>/` untuk global).
- **Gemini CLI**: folder skill dan `gemini skills install <path>` (tambahkan `--scope workspace` untuk proyek).
- **Gemini app**: folder atau `.zip` dengan `SKILL.md` di folder utama, untuk diunggah lewat Customize > Skills > Create > Upload.

Perintah lengkap dan cara verifikasinya ada di `references/mapping-guide.md`. Selalu sertakan **Ringkasan Migrasi** singkat:

1. **Perubahan Utama**: field frontmatter, sintaks, dan path yang dikonversi.
2. **Adaptasi Perilaku**: fitur Claude yang diubah menjadi instruksi prosedural (`disable-model-invocation`, injeksi shell, `context: fork`).
3. **Tindak Lanjut Manual**: hooks, aturan `.agents/rules/`, server MCP, subagent, dan izin yang perlu dikonfigurasi terpisah di target.
4. **Verifikasi**: hasil `validate_skill.py` dan hasil uji muat di target.

## Decision Tree for Unsupported Extensions

| Fitur Claude Code | Strategi Konversi ke Gemini / Antigravity |
| :--- | :--- |
| `` !`cmd` `` atau blok `` ```! `` | Langkah pertama eksplisit: jalankan perintah via terminal dan baca outputnya. Gemini CLI custom command: `!{cmd}`. |
| `$ARGUMENTS`, `$0`, `$1`, `$name` | Bagian `## Inputs` dengan nama parameter dan fallback jika kosong. Gemini CLI custom command: `{{args}}` (satu string utuh). |
| `disable-model-invocation: true` | `## Safety Gate` di awal body dan `description` "Use only when the user explicitly asks ...". |
| `context: fork` dan `agent` | Instruksikan subagent terisolasi (jika tersedia) atau ringkasan agar konteks utama tetap bersih. |
| `hooks` | Langkah verifikasi wajib di body, lalu catat migrasi ke `hooks.json` Antigravity atau `settings.json` Gemini CLI. Skrip hook harus ditulis ulang karena kontrak JSON berbeda. |
| `paths` (glob) | Sebut di `description`, dan buat aturan `.agents/rules/<name>.md` dengan `trigger: glob` jika perlu aktivasi otomatis per file. |
| `allowed-tools` | Hapus. Atur izin di Permissions Antigravity atau policy Gemini CLI. |
| `mcp__<server>__<tool>` | Tulis sebagai kapabilitas plus nama server MCP, catat konfigurasi server sebagai tindak lanjut. |
| `.claude/commands/<name>.md` | Bungkus menjadi folder `<name>/SKILL.md`. Untuk command manual-only di Gemini CLI, alternatifnya `.gemini/commands/<name>.toml`. |
| `.claude/agents/*.md`, plugin, `.mcp.json` | Di luar cakupan skill ini. Laporkan sebagai tindak lanjut (custom agents, plugins, `mcp_config.json` di Antigravity). |

## Gotchas

- **Memperluas `description` pada skill manual-only**: `when_to_use` yang digabung ke skill `disable-model-invocation: true` membuatnya terpicu otomatis di target. Tulis "Use only when the user explicitly asks ..." dan tetap pasang Safety Gate.
- **Menghapus `when_to_use` begitu saja**: pada skill yang boleh dipicu otomatis, kata kunci pemicunya hilang dan skill tidak pernah terpicu. Gabungkan ke `description`.
- **`description` tanpa tanda kutip yang berisi `: `**: YAML menjadi tidak valid (contoh: `description: Use when: user asks X`) dan skill bisa gagal dimuat. Kutip dengan tanda kutip ganda.
- **Path relatif vs direktori kerja**: `scripts/<script>.py` relatif terhadap folder skill, sedangkan shell agen biasanya berjalan dari root proyek. Tulis eksplisit agar path di-resolve terhadap folder yang berisi `SKILL.md`.
- **Membiarkan injeksi shell tertulis**: baik `` !`command` `` maupun blok `` ```! `` hanya menjadi teks literal. Model bisa mengira outputnya sudah ada atau menebak isinya.
- **Path hardcode di dalam `scripts/` dan `references/`**: `SKILL.md` sering sudah bersih sementara script masih merujuk ke `~/.claude/skills/...`, `$CLAUDE_PROJECT_DIR`, atau `${CLAUDE_PLUGIN_ROOT}`. Selalu audit isinya.
- **Nama tool Claude yang tidak ada di target**: "Use the MultiEdit tool" atau "Call TodoWrite" membingungkan agen Gemini. Ubah ke kata kerja kapabilitas yang netral.
- **Pola `--help` pada script yang tidak mendukungnya**: menjalankan script tanpa parsing argumen dengan `--help` bisa mengeksekusi aksi nyata. Pastikan dulu dari kode atau dokumentasinya.
- **File aturan tanpa frontmatter**: file di `.agents/rules/` tanpa frontmatter atau dengan `trigger` yang tidak dikenal dibuang diam-diam. Nilai yang valid: `always_on`, `model_decision`, `glob`, `manual`.
- **Skill bersarang**: Antigravity hanya memindai satu tingkat, jadi `skills/<kategori>/<name>/` tidak akan termuat tanpa manifest `skills.json`.
- **Menerjemahkan isi skill**: mengubah bahasa instruksi mengubah perilaku dan memutus kata kunci pemicu. Terjemahkan hanya atas permintaan pengguna.
- **Konversi mekanis tanpa menjaga maksud**: jangan menghapus `disable-model-invocation: true` pada skill deploy atau produksi tanpa gerbang konfirmasi di body.
- **Mengunggah ke Gemini app tanpa membersihkan bundel**: file `.DS_Store`, `.pyc`, serta tipe file yang tidak didukung (misalnya `.ts`, `.sql`) bisa membuat unggahan gagal.

## Sources

Path dan perilaku di bawah ini diverifikasi pada 2026-11-21. Periksa ulang bila hasil di lapangan berbeda.

- Antigravity: https://antigravity.google/docs/skills, https://antigravity.google/docs/rules, https://antigravity.google/docs/hooks, https://antigravity.google/docs/customization-discovery, https://antigravity.google/docs/cli/gcli-migration/
- Gemini CLI: https://geminicli.com/docs/cli/skills/, https://geminicli.com/docs/cli/custom-commands, https://geminicli.com/docs/hooks, https://geminicli.com/docs/reference/tools
- Gemini app: https://support.google.com/gemini/answer/17094296 dan https://support.google.com/gemini/answer/17102773
- Standar Agent Skills: https://agentskills.io/specification
- Claude Code skills: https://code.claude.com/docs/en/skills
