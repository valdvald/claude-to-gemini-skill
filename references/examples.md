# Conversion Examples

Contoh konversi dari skill dan command Claude Code ke format standar Gemini / Google Antigravity. Perhatikan dua hal yang konsisten di semua contoh: isi skill hasil konversi mempertahankan bahasa sumber (di sini Inggris), dan hanya catatan migrasi yang berbahasa Indonesia.

## Example 1: Skill Manual-Only dengan Injeksi Shell, Argumen, dan Pembatasan

### Sebelum (Claude Code: `.claude/skills/release-check/SKILL.md`)

````markdown
---
name: release-check
description: Prepare a release checklist
when_to_use: Use when cutting a release or tagging a new version
argument-hint: "[version]"
disable-model-invocation: true
allowed-tools: Bash(git *), Read
model: sonnet
---

## Current Git State

!`git status --short`
!`git log -n 5 --oneline`

## Instructions

1. Target version is `$0` (all args: `$ARGUMENTS`).
2. Run `${CLAUDE_SKILL_DIR}/scripts/check_changelog.py` using Bash.
3. Read `CLAUDE.md` for release rules and use `Grep` to check for `TODO` markers.
4. Draft release notes and run `git tag v$0`.
````

### Sesudah (Gemini / Antigravity: `.agents/skills/release-check/SKILL.md`)

````markdown
---
name: release-check
description: "Prepares a release checklist, validates the changelog, checks for leftover TODO markers, and drafts release notes for a target version. Use only when the user explicitly asks to cut a release, run the release check, or tag a new version."
compatibility: "Requires git and python3."
---
# Release Check

## Safety Gate

This skill touches the release process. Never run `git tag` or `git push` without explicit confirmation from the user first.

## Inputs

- `version`: target version number (for example `1.4.0`). If the user did not provide it, ask before continuing.

## Steps

1. Inspect the repository by running `git status --short` and `git log -n 5 --oneline` in the terminal and reading the output.
2. Run `scripts/check_changelog.py` for the target version. The path is relative to this skill's folder, so resolve it against the folder that contains this SKILL.md before running.
3. Read the project release rules (`GEMINI.md`, or the release conventions document in the repository root) and search the codebase for leftover `TODO` markers.
4. Draft the release notes and show the user a summary of the checks.
5. Ask the user to confirm before running `git tag v<version>`.
````

### Catatan Migrasi (Example 1)

- `disable-model-invocation: true` menjadi `## Safety Gate`. `description` memakai "Use only when the user explicitly asks ..." dan tidak diperluas dengan kata kunci dari `when_to_use`, supaya skill tetap tidak terpicu otomatis seperti di sumber.
- `when_to_use` tidak digabung penuh karena skill ini manual-only. Frasa pemicunya hanya dipakai untuk menyempitkan kapan skill boleh dijalankan.
- `` !`git status --short` `` dan `` !`git log -n 5 --oneline` `` menjadi langkah terminal eksplisit pada Step 1.
- `$0` dan `$ARGUMENTS` menjadi `## Inputs`, dan `argument-hint` ikut terserap di sana.
- `${CLAUDE_SKILL_DIR}/scripts/check_changelog.py` menjadi path relatif plus instruksi me-resolve, karena shell biasanya berjalan dari root proyek.
- `CLAUDE.md`, `Bash`, dan `Grep` menjadi referensi netral. `allowed-tools` dan `model` dihapus. Izin menjalankan `git` diatur di Permissions Antigravity atau policy Gemini CLI (tindak lanjut manual).
- Dependensi `git` dan `python3` dipindahkan ke `compatibility`. Bahasa isi skill tetap Inggris sesuai sumber.

## Example 2: Legacy Command dengan `context: fork` dan `paths`

### Sebelum (Claude Code: `.claude/commands/sql-audit.md`)

````markdown
---
description: Audit SQL migrations for breaking changes
context: fork
agent: Explore
paths:
  - "migrations/**/*.sql"
disallowed-tools: Write, Edit
---

Inspect `$ARGUMENTS` in `${CLAUDE_PROJECT_DIR}` and report unsafe DDL operations (DROP COLUMN, lock-heavy ALTER TABLE).
````

### Sesudah (Gemini / Antigravity: `.agents/skills/sql-audit/SKILL.md`)

````markdown
---
name: sql-audit
description: "Audits SQL migration files (migrations/**/*.sql) for breaking or lock-heavy DDL such as DROP COLUMN or unsafe ALTER TABLE. Use when reviewing SQL migrations or database schema changes."
---
# SQL Migration Audit

Audit SQL migration files read-only and report unsafe DDL operations before they reach production.

## Scope and Constraints

- Read-only mode: do not modify, write, or delete any file.
- Focus on the migration files the user names, or on `migrations/**/*.sql` in the workspace root when none is given.
- If the migration list is large, analyze it in an isolated subagent when the target supports one, and bring back only a short list of findings so the main context stays clean.

## Steps

1. Identify the target migration files from the request (the project root is the workspace root).
2. Check every DDL statement for downtime or data-loss risk (`DROP COLUMN`, `DROP TABLE`, `ALTER TABLE` without a lock timeout, destructive type changes).
3. Report findings in a table: file, line number, risk type, and a safer mitigation.
````

Opsional, aturan Antigravity agar skill ini diingatkan otomatis saat migrasi disentuh (`.agents/rules/sql-migrations.md`):

````markdown
---
trigger: glob
globs: "migrations/**/*.sql"
description: "Reminder to audit SQL migrations."
---

Before finishing work on SQL migration files, audit them with the `sql-audit` skill.
````

### Catatan Migrasi (Example 2)

- File tunggal `.claude/commands/sql-audit.md` dibungkus menjadi direktori `sql-audit/SKILL.md` dengan `name: sql-audit` dan `description` baru (sumber hanya punya satu kalimat pendek).
- `disallowed-tools: Write, Edit` menjadi aturan eksplisit mode read-only.
- `paths` dipindahkan ke `description` dan `## Scope and Constraints`. Untuk aktivasi otomatis per file dibuat aturan `trigger: glob` (tindak lanjut manual jika pengguna ingin memakainya). File aturan wajib berfrontmatter, kalau tidak dibuang diam-diam.
- `context: fork` dan `agent: Explore` menjadi panduan isolasi analisis dan pelaporan ringkas.
- `${CLAUDE_PROJECT_DIR}` menjadi root workspace, dan `$ARGUMENTS` menjadi "file yang disebut pengguna".

## Example 3: Command Manual-Only untuk Gemini CLI (`.toml`)

Untuk command yang hanya dipanggil manual dan memakai injeksi shell plus argumen, Gemini CLI punya padanan yang lebih dekat daripada skill: custom command TOML. Skill tidak melewati preprocessor, sedangkan command TOML punya `!{...}` dan `{{args}}`.

### Sebelum (Claude Code: `.claude/commands/changes.md`)

````markdown
---
description: Review uncommitted changes
disable-model-invocation: true
argument-hint: "[focus]"
allowed-tools: Bash(git diff *)
---
Review the uncommitted changes below. Extra focus: $ARGUMENTS

!`git diff HEAD`
````

### Sesudah (Gemini CLI: `.gemini/commands/changes.toml`, dipanggil dengan `/changes`)

````toml
description = "Review uncommitted changes"
prompt = """
Review the uncommitted changes below. Extra focus: {{args}}

!{git diff HEAD}
"""
````

### Catatan Migrasi (Example 3)

- `$ARGUMENTS` menjadi `{{args}}`. Di dalam blok `!{...}`, `{{args}}` otomatis di-escape untuk shell.
- `` !`git diff HEAD` `` menjadi `!{git diff HEAD}`. Gemini CLI meminta konfirmasi sebelum menjalankan perintah shell di command.
- `disable-model-invocation: true` otomatis terpenuhi, karena command TOML hanya berjalan saat pengguna mengetiknya.
- `allowed-tools` dan `argument-hint` dihapus. Gunakan `/commands reload` setelah menambah atau mengubah file `.toml`.
- Isi `!{...}` harus memiliki kurung kurawal yang seimbang. Untuk perintah yang rumit, taruh di script lalu panggil script itu dari `!{...}`.
- Target Antigravity tidak punya format ini. Konversi command yang sama untuk Antigravity mengikuti pola Example 1 (skill dengan Safety Gate). Antigravity CLI sendiri mengonversi command TOML lama menjadi skill lewat `agy plugin import gemini`.
- Bagi pengguna tier gratis dan Google One, Gemini CLI sudah digantikan Antigravity CLI (lihat `SKILL.md`), jadi format `.toml` ini hanya relevan untuk pengguna yang masih memakai Gemini CLI.

## Example 4: Skill dengan Blok `` ```! ``, Argumen Bernama, dan Dependensi CLI

### Sebelum (Claude Code: `.claude/skills/pr-summary/SKILL.md`)

````markdown
---
name: pr-summary
description: Summarize a pull request
when_to_use: Use when the user asks for a PR summary or release notes from a PR
arguments: [pr_number]
allowed-tools: Bash(gh *)
effort: low
---

## PR data

```!
gh pr view $pr_number --json title,body
gh pr diff $pr_number --stat
```

Summarize PR #$pr_number in three bullet points for release notes. Format the result with `${CLAUDE_SKILL_DIR}/scripts/format_notes.py`.
````

### Sesudah (Gemini / Antigravity: `.agents/skills/pr-summary/SKILL.md`)

````markdown
---
name: pr-summary
description: "Summarizes a GitHub pull request in three bullet points for release notes. Use when the user asks for a PR summary or release notes from a pull request."
compatibility: "Requires the GitHub CLI (gh), authenticated, and python3."
---
# PR Summary

## Inputs

- `pr_number`: the pull request number. If the user did not provide it, ask before continuing.

## Steps

1. Fetch the PR data by running `gh pr view <pr_number> --json title,body` and `gh pr diff <pr_number> --stat` in the terminal, then read the output.
2. Summarize the PR in three bullet points suitable for release notes.
3. Format the result with `scripts/format_notes.py`. The path is relative to this skill's folder, so resolve it against the folder that contains this SKILL.md before running.
````

### Catatan Migrasi (Example 4)

- Blok `` ```! `` berisi dua perintah, jadi keduanya menjadi satu langkah eksplisit yang menyebut kedua perintah itu. Tanpa konversi, blok itu hanya menjadi teks literal.
- `$pr_number` (argumen bernama dari `arguments`) menjadi parameter `pr_number` di `## Inputs`.
- Skill ini tidak manual-only, jadi `when_to_use` digabung ke `description` agar auto-trigger tetap akurat.
- `allowed-tools: Bash(gh *)` dihapus dan dicatat sebagai tindak lanjut (izin `gh` di Permissions Antigravity atau policy Gemini CLI). Kebutuhan `gh` dan `python3` pindah ke `compatibility`.
- `effort: low` dihapus tanpa pengganti karena tugasnya ringan. Untuk target Gemini app, skill ini tidak cocok karena bergantung pada terminal dan `gh`.

## Contoh Ringkasan Migrasi (untuk Example 1)

1. **Perubahan Utama**: `when_to_use`, `argument-hint`, `allowed-tools`, dan `model` dihapus dari frontmatter. `description` ditulis ulang dan `compatibility` ditambahkan. Injeksi shell menjadi langkah terminal, `$0` dan `$ARGUMENTS` menjadi `## Inputs`, `${CLAUDE_SKILL_DIR}` menjadi path relatif, `CLAUDE.md` menjadi `GEMINI.md`.
2. **Adaptasi Perilaku**: `disable-model-invocation: true` menjadi `## Safety Gate` dan `description` "Use only when ...". Instruksi `Bash` dan `Grep` menjadi kapabilitas netral.
3. **Tindak Lanjut Manual**: atur izin `git` di Permissions Antigravity atau policy Gemini CLI. Pasang skill dengan `cp -R release-check .agents/skills/` (Antigravity) atau `gemini skills install ./release-check --scope workspace` (Gemini CLI).
4. **Verifikasi**: `validate_skill.py --target antigravity` lulus tanpa error. Skill muncul di `/skills` dan terpicu saat pengguna meminta rilis secara eksplisit.
