# Claude to Gemini/Antigravity Skill Mapping Guide

Panduan referensi untuk memetakan struktur direktori, frontmatter YAML, sintaks substitusi, nama tool, hooks, dan aturan dari Claude/Claude Code ke Google Antigravity, Gemini CLI, dan aplikasi Gemini. Diverifikasi ke dokumentasi resmi pada 2026-11-21 (daftar sumber ada di `SKILL.md`).

## Daftar Isi

1. Lokasi dan Scope Direktori
2. Pemetaan Frontmatter YAML
3. Pemetaan Sintaks Body dan Substitusi
4. Pemetaan Nama Tool
5. Hooks
6. Rules dan Konteks Selalu Aktif
7. Instalasi dan Verifikasi
8. Penyesuaian Gaya Prompt

## 1. Lokasi dan Scope Direktori

| Scope | Claude Code | Antigravity (App / CLI / IDE) | Gemini CLI |
| :--- | :--- | :--- | :--- |
| **Project** | `.claude/skills/<name>/SKILL.md` | `.agents/skills/<name>/SKILL.md` (lama: `.agent/`; folder induk sampai root repositori ikut dipindai) | `.agents/skills/<name>/` atau `.gemini/skills/<name>/` |
| **Global** | `~/.claude/skills/<name>/SKILL.md` | `~/.gemini/config/skills/<name>/SKILL.md` (IDE lama: `~/.gemini/antigravity/skills/`; CLI juga `~/.gemini/skills/` dan `~/.gemini/antigravity-cli/skills/`) | `~/.agents/skills/<name>/` atau `~/.gemini/skills/<name>/` |
| **Legacy command** | `.claude/commands/<name>.md` | Skill `<name>/SKILL.md`. Jangan pakai workflows Antigravity, fitur itu sudah deprecated. (`agy plugin import gemini` juga mengonversi command Gemini CLI lama menjadi skill.) | Skill, atau `.gemini/commands/<name>.toml` untuk command yang hanya dipanggil manual |
| **Plugin skills** | `<plugin>/skills/<name>/SKILL.md` | `~/.gemini/config/plugins/<plugin>/skills/` (dinamai `<plugin>:<skill>`, kelola dengan `agy plugin`) | Skill dari extension |
| **Konteks selalu aktif** | `CLAUDE.md`, `.claude/rules/*.md` | `AGENTS.md` atau `GEMINI.md`, `.agents/rules/*.md` | `GEMINI.md` |
| **Subagent** | `.claude/agents/*.md` | Custom agents: `.agents/agents/<name>.md` | Di luar cakupan skill ini |
| **MCP** | `.mcp.json` | `mcp_config.json` di `.agents/` atau `~/.gemini/config/` (kunci URL server remote: `serverUrl`) | `mcpServers` di `settings.json` |
| **Hooks** | Field `hooks`, settings, plugin | `.agents/hooks.json`, `~/.gemini/config/hooks.json` | `hooks` di `settings.json` |

Antigravity CLI tidak membaca `.gemini/skills/` (jalur proyek lama Gemini CLI), jadi pindahkan skill proyek ke `.agents/skills/`. Antigravity memindai satu tingkat saja dan hanya memuat folder skill yang langsung berada di dalam `skills/`. Untuk memuat skill dari folder lain atau yang bersarang tanpa menyalin, gunakan manifest `skills.json` (di `.agents/` untuk proyek atau `~/.gemini/config/` untuk pribadi). Path di manifest harus absolut atau relatif terhadap folder yang benar, dan `~` tidak diekspansi:

```json
{
  "entries": [
    { "path": "/home/dev/team-config/skills", "exclude": ["draft-skill"] }
  ]
}
```

## 2. Pemetaan Frontmatter YAML

Standar Agent Skills hanya mendefinisikan `name`, `description`, `license`, `compatibility`, `metadata`, dan `allowed-tools` (eksperimental). Sisanya adalah ekstensi Claude Code.

| Field Claude Code | Status di target | Aksi Konversi |
| :--- | :--- | :--- |
| `name` | Wajib di standar dan Gemini CLI. Opsional di Antigravity (default nama folder). Gemini app mewajibkan huruf kecil dan tanda hubung. | Pertahankan. 1-64 karakter, `a-z`, `0-9`, tanda hubung tunggal, sama dengan nama folder. |
| `description` | Wajib. Maks 1024 karakter. | Pertahankan dan perkuat: apa yang dilakukan dan kapan dipakai, orang ketiga, kutip jika berisi `: ` atau `#`. |
| `license` | Standar, opsional | Pertahankan. |
| `compatibility` | Standar, opsional, maks 500 karakter | Pertahankan. Ganti "Designed for Claude Code" menjadi lingkungan yang dibutuhkan (misalnya "Requires git and python3"). |
| `metadata` | Standar, opsional | Pertahankan sebagai map string ke string (kutip angka seperti `"1.0"`). |
| `allowed-tools` | Standar tetapi eksperimental, dukungan berbeda antar platform | Hapus. Di Claude ini pra-persetujuan izin, bukan pembatasan. Izin di target diatur lewat Permissions Antigravity atau policy Gemini CLI. |
| `when_to_use` | Ekstensi Claude Code | Gabungkan ke `description` (total maks 1024). Jangan untuk skill manual-only (lihat `disable-model-invocation`). |
| `argument-hint`, `arguments` | Ekstensi Claude Code | Hapus, pindahkan ke `## Inputs`. |
| `disable-model-invocation` | Ekstensi Claude Code | Hapus. Jika `true`: `## Safety Gate` di awal body, dan `description` berbunyi "Use only when the user explicitly asks ...". |
| `user-invocable` | Ekstensi Claude Code | Hapus. Jika `false`, tulis `description` sebagai pengetahuan latar belakang. |
| `disallowed-tools` | Ekstensi Claude Code | Hapus. Jadikan aturan perilaku eksplisit di body ("Jangan mengedit atau menulis file"). |
| `context` (`fork`) | Ekstensi Claude Code | Hapus. Instruksikan eksplorasi berat di subagent (jika tersedia) dan bawa hanya ringkasannya. |
| `agent` (`Explore`, `Plan`, dll.) | Ekstensi Claude Code | Hapus. Ubah peran menjadi instruksi fokus peran di awal body. |
| `background` | Ekstensi Claude Code | Hapus. Jelaskan di body jika proses panjang sebaiknya dijalankan di background. |
| `model`, `effort` | Ekstensi Claude Code | Hapus. Jangan hardcode nama model Claude. Tulis kedalaman analisis yang diharapkan. |
| `hooks` | Ekstensi Claude Code | Hapus. Lihat bagian 5. |
| `paths` | Ekstensi Claude Code | Hapus. Sebut pola di `description` dan `## When to Use`. Untuk aktivasi otomatis per file lihat bagian 6. |
| `shell` | Ekstensi Claude Code | Hapus. Sebut shell yang dibutuhkan pada perintah eksekusi dan di shebang script. |

## 3. Pemetaan Sintaks Body dan Substitusi

| Sintaks Claude Code | Perilaku di Claude Code | Bentuk Konversi |
| :--- | :--- | :--- |
| `` !`git diff HEAD` `` | Dijalankan sebelum prompt masuk ke model, output menggantikan barisnya | Langkah eksplisit: "Jalankan `git diff HEAD` di terminal dan baca hasilnya." Gemini CLI custom command: `!{git diff HEAD}` (meminta konfirmasi). |
| Blok `` ```! `` | Sama, untuk beberapa perintah sekaligus | Satu langkah per perintah, atau satu script di `scripts/`. |
| `$ARGUMENTS` | Semua argumen setelah `/nama`. Tanpa placeholder, Claude Code menambahkan `ARGUMENTS: <nilai>` | `## Inputs` dengan fallback bertanya. Gemini CLI custom command: `{{args}}`. |
| `$0`, `$1`, `$ARGUMENTS[0]` | Argumen posisional dengan quoting ala shell | Nama parameter jelas di `## Inputs` (`<environment>`, `<target_file>`). Custom command TOML tidak punya argumen posisional. |
| `$name` | Argumen bernama dari field `arguments` | Nama yang sama di `## Inputs`. |
| `${CLAUDE_SKILL_DIR}` | Path absolut folder skill | Path relatif dari folder skill (`scripts/check.py`), plus instruksi untuk me-resolve terhadap folder yang berisi `SKILL.md` karena shell biasanya berjalan dari root proyek. |
| `${CLAUDE_PLUGIN_ROOT}` | Path absolut root plugin | Sama dengan di atas. |
| `${CLAUDE_PROJECT_DIR}` | Path absolut root proyek | Root workspace atau repositori (`./`, "dari root repositori"). |
| `${CLAUDE_SESSION_ID}` | ID sesi unik | Hapus, atau pakai nama file sementara berbasis timestamp (`/tmp/report-<timestamp>.md`). |
| `${CLAUDE_EFFORT}` | Level effort sesi saat ini | Hapus percabangannya. Tulis ekspektasi kedalaman analisis di body. |

## 4. Pemetaan Nama Tool

Di body skill, gunakan frasa kapabilitas netral karena nama tool berbeda per surface dan versi. Nama tool asli target hanya dipakai di konfigurasi hooks dan izin.

| Tool Claude Code | Frasa netral untuk body skill | Gemini CLI | Antigravity |
| :--- | :--- | :--- | :--- |
| `Read` | Baca isi file terkait | `read_file`, `read_many_files` | `view_file` |
| `Write` | Buat atau tulis file baru | `write_file` | `write_to_file` |
| `Edit` | Perbarui bagian terkait pada file | `replace` | `replace_file_content` |
| `MultiEdit` | Perbarui beberapa bagian pada satu file | `replace` | `multi_replace_file_content` |
| `NotebookEdit` | Ubah sel notebook | Tidak ada tool khusus terdokumentasi | Lihat dokumentasi Jupyter notebooks |
| `Glob` | Cari file berdasarkan pola nama | `glob` | `find_by_name` |
| `Grep` | Cari teks atau regex di codebase | `grep_search` | `grep_search` |
| `LS` | Daftar isi direktori | `list_directory` | `list_dir` |
| `Bash` | Jalankan perintah shell | `run_shell_command` | `run_command` |
| `WebFetch` | Ambil dan baca halaman URL | `web_fetch` | `read_url_content` |
| `WebSearch` | Lakukan pencarian web | `google_web_search` | `search_web` |
| `TodoWrite` | Buat dan perbarui daftar langkah kerja | `write_todos` | Tidak ada padanan 1:1 terdokumentasi |
| `Task` / `Agent` | Delegasikan subtugas ke subagent (jika tersedia) | Subagent jika diaktifkan | `invoke_subagent` |
| `AskUserQuestion` | Tanyakan kepada pengguna | `ask_user` | `ask_question` |
| `Skill` | Gunakan skill lain berdasarkan nama | `activate_skill` | Panggil `/<name>` atau sebut nama skill |
| `mcp__<server>__<tool>` | Gunakan server MCP `<server>` untuk [kapabilitas] | Tool dari server MCP | Tool dari server MCP |

## 5. Hooks

Hooks tidak hidup di frontmatter skill. Di Antigravity hooks adalah file `hooks.json` (workspace: `.agents/hooks.json`, global: `~/.gemini/config/hooks.json`, atau dalam plugin). Di Gemini CLI hooks ada di objek `hooks` pada `settings.json` (proyek, user, sistem, atau extension). Hanya handler bertipe `command` yang didukung di Antigravity.

| Event Claude Code | Antigravity | Gemini CLI |
| :--- | :--- | :--- |
| `PreToolUse` | `PreToolUse` | `BeforeTool` |
| `PostToolUse` | `PostToolUse` | `AfterTool` |
| `SessionStart` | `SessionStart` | `SessionStart` |
| `Stop` | `Stop` | `AfterAgent` (terpicu saat giliran agen selesai; dukung retry) |
| `UserPromptSubmit` | Tidak 1:1 (`PreInvocation` terpicu sebelum setiap panggilan model) | `BeforeAgent` (terpicu setelah user mengirim prompt, sebelum planning) |

`matcher` pada event tool adalah regex atas nama tool target, bukan nama tool Claude:

| Claude Code | Antigravity | Gemini CLI |
| :--- | :--- | :--- |
| `Bash` | `run_command` | `run_shell_command` |
| `Edit`, `Write` | `replace_file_content`, `multi_replace_file_content`, `write_to_file` | `replace`, `write_file` |
| `Read` | `view_file` | `read_file` |
| `mcp__<server>__<tool>` | Pola tool MCP Antigravity | `mcp_<server>_<tool>` (garis bawah tunggal) |

Contoh `hooks.json` Antigravity yang menjalankan skrip pemeriksa sebelum setiap perintah shell (konfirmasi muncul bila skrip membalas `decision: "ask"`):

```json
{
  "safety-gate": {
    "PreToolUse": [
      {
        "matcher": "run_command",
        "hooks": [
          { "type": "command", "command": "./scripts/safety-check.sh", "timeout": 10 }
        ]
      }
    ]
  }
}
```

Kontrak input/output berbeda. Hook Antigravity menerima JSON camelCase di stdin (misalnya `toolCall.name`, `toolCall.args`, `conversationId`). Hook `PreToolUse` wajib membalas JSON di stdout dengan `decision` (`allow`, `auto_approve`, `deny`, `ask`, `force_ask`, atau `deny_unless_prior_grant`) dan boleh menyertakan `reason`. Hook `PostToolUse` membalas `{}`, dan hook `Stop` membalas `decision: "continue"` untuk mencegah agen berhenti. Skrip hook Claude Code (exit code dan JSON-nya sendiri) tidak bisa dipakai apa adanya, jadi tandai sebagai tindak lanjut manual dan tulis ulang skripnya. Di Antigravity CLI, hooks di `~/.gemini/antigravity-cli/settings.json` tidak dimuat, dan perintah `/hooks` menampilkan hooks yang aktif.

## 6. Rules dan Konteks Selalu Aktif

`AGENTS.md` dan `GEMINI.md` tidak memakai frontmatter dan selalu aktif. Setiap file di `.agents/rules/*.md` wajib diawali frontmatter dengan `trigger` yang valid. Tanpa itu, atau dengan nilai tidak dikenal (misalnya `alwaysOn`), aturan dibuang diam-diam.

| `trigger` | Perilaku | Dipakai untuk |
| :--- | :--- | :--- |
| `always_on` | Selalu dimuat penuh | Pengganti `CLAUDE.md` atau rule Claude tanpa `paths` |
| `glob` | Aktif saat agen menyentuh file yang cocok dengan `globs` | Pengganti `paths` |
| `model_decision` | Hanya path dan `description` yang dimuat, isi dibaca bila relevan | Panduan domain yang panjang |
| `manual` | Hanya lewat `@`-mention (tidak didukung di CLI) | Checklist atau rubrik audit |

```markdown
---
trigger: glob
globs: "migrations/**/*.sql"
description: "SQL migration conventions and audit reminder."
---

Before finishing work on SQL migration files, audit them with the `sql-audit` skill.
```

Batasan: Antigravity hanya memindai file `.md` yang langsung berada di `.agents/rules/` (subfolder diabaikan kecuali didaftarkan di `.agents/rules.json`). File aturan di atas 24.000 byte dipotong, dan aturan global serta `always_on` berbagi anggaran 20.000 token (jika terlampaui, aturan terbesar diubah menjadi penunjuk yang dibaca sesuai kebutuhan). Pola `globs` yang diawali `*` harus dikutip. Antigravity juga membaca `AGENTS.md` dan `GEMINI.md` di setiap folder induk sampai root repositori. Untuk tugas multi-langkah gunakan skill, bukan aturan: aturan ditujukan bagi batasan dan invarian.

Konversi `CLAUDE.md`: referensi ke file itu di dalam skill diubah menjadi `GEMINI.md` (Gemini CLI dan Antigravity) atau `AGENTS.md` (Antigravity). Konversi isi file `CLAUDE.md` itu sendiri di luar cakupan, kecuali pengguna memintanya. Jika pengguna memintanya, impor `@path` yang menyisipkan isi file punya padanan `@[label](path)` pada file aturan Antigravity (path relatif terhadap file aturan, frontmatter file yang disisipkan dibuang). Penulisan `@nama-file` biasa di Antigravity hanya menjadi rujukan path, bukan penyisipan isi.

## 7. Instalasi dan Verifikasi

Antigravity, proyek (dibaca App, CLI, dan IDE):

```bash
mkdir -p .agents/skills
cp -R ./<name> .agents/skills/<name>
```

Antigravity, global (dibaca App, CLI, dan IDE):

```bash
mkdir -p ~/.gemini/config/skills
cp -R ./<name> ~/.gemini/config/skills/<name>
```

Antigravity CLI, sebagai paket plugin (skill ikut terkelola oleh `agy plugin`):

```bash
agy plugin install ./my-skills-plugin
agy plugin list --json
```

Gemini CLI:

```bash
gemini skills install ./<name>                      # scope user (default)
gemini skills install ./<name> --scope workspace    # scope proyek
```

Di dalam sesi Gemini CLI, `/skills link /path/to/skills-repo --scope workspace` menautkan folder skill tanpa menyalin, dan `/skills reload` menyegarkan daftar. Opsi `--consent` pada `gemini skills install` melewati konfirmasi keamanan, jadi jangan dipakai untuk skill pihak ketiga yang belum diaudit.

Gemini app: Customize > Skills > Create > Upload, lalu pilih `SKILL.md`, folder, atau `.zip` dengan `SKILL.md` di folder utama. Detail di `references/gemini-app.md`.

Verifikasi bahwa skill termuat:

| Target | Cara cek |
| :--- | :--- |
| Antigravity App | Settings > Projects > pilih proyek > Customizations, atau Customizations > Installed |
| Antigravity CLI | `/skills` (jalankan `/skills reload` atau mulai percakapan baru setelah menambah skill) |
| Antigravity IDE | Menu Customizations pada panel agen |
| Gemini CLI | `/skills list` |
| Gemini app | Customize > Skills |

Jika skill tidak termuat, cek berurutan: lokasi folder, kedalaman (langsung di dalam `skills/`), nama file `SKILL.md`, frontmatter YAML valid, dan nama kembar di lokasi berprioritas lebih tinggi.

## 8. Penyesuaian Gaya Prompt

- **Pertahankan struktur sumber.** Normalisasi hanya bila perlu, misalnya XML tag yang bercampur dengan Markdown atau heading yang tidak konsisten. Pilih satu gaya pemisah dan pakai secara konsisten.
- **Progressive Disclosure.** Pisahkan tabel referensi besar, schema, atau contoh panjang ke `references/` atau `assets/` agar `SKILL.md` tetap di bawah 500 baris.
- **Script sebagai black box.** Arahkan agen menjalankan `python3 scripts/<name>.py --help` terlebih dahulu hanya jika script mengurai argumen. Jika tidak, dokumentasikan cara pakainya di `SKILL.md`.
- **Decision Tree.** Jika skill punya beberapa jalur pengerjaan, ringkas cabangnya dalam tabel atau pohon keputusan singkat.
- **Sertakan alasan.** Aturan penting disertai satu kalimat "mengapa" agar diterapkan konsisten tanpa kaku.
