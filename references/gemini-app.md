# Gemini App (Skills): Limits and Upload Guide

The Gemini app (gemini.google.com, the Gemini app on Mac, and the mobile app) is a conversational environment rather than a local coding agent. Many Claude Code skills cannot run there as-is. Read this file before converting for the Gemini app target. Verified against official help pages on 2026-11-21 (https://support.google.com/gemini/answer/17094296 and https://support.google.com/gemini/answer/17102773). Current requirements include being 18+ and signed in to a Gemini account. Account eligibility, availability, and limits may change, so re-check those pages if behavior differs.

## How to Upload

1. Open gemini.google.com (or the Gemini app on Mac), click **Customize** in the sidebar (click **More** first if hidden), and select **Skills** at the top.
2. Click **Create** > **Upload**, then select a `SKILL.md` file, a folder, or a `.zip` archive with `SKILL.md` in its root folder.
3. Review the skill, make any edits, and click **Create**.

Notes:

- Uploading is most reliable on the web (gemini.google.com). The Android help page notes that file upload is not yet available in the mobile app, and full management (including sharing) is web-only. Skills created on the web still work in the mobile app.
- To update files inside a skill, re-upload the entire skill along with its reference files (or use **Replace skill**). Reference files can only be added during upload.
- Skills may reference other skills in their instructions (per the help docs), so upload all interdependent skills.
- Manual invocation: type `/` (or `@`) in chat and pick the skill. Gemini also activates enabled skills automatically based on context.
- Skills can be turned off without deleting via the skill menu (Deactivate), and can be shared from the web app.

## Limits Affecting Conversion

1. **No terminal, git, or local project filesystem.** Skills relying on shell commands, `git`, or reading local repositories will not work. Rewrite them as pure instruction skills (for example, asking the user to paste a diff or file contents), or recommend Antigravity or Gemini CLI instead.
2. **Offline scripts only.** Scripts requiring internet access are not supported, and scripts must not make requests to external websites.
3. **Reference file types.** Supported types include `.md`, `.txt`, `.pdf`, `.docx`, `.xlsx`, `.pptx`, `.csv`, `.json`, `.yaml`, `.toml`, `.xml`, `.html`, `.css`, common image formats, plus `.py`, `.sh`, `.js`, and `.ipynb`. Unsupported types: `.doc`, `.xls`, `.ppt`, `.raw`, audio and video, archives (zip, tar, etc.), `.cs`, `.kt`, `.kts`, `.php`, `.r`, `.rb`, `.scala`, `.swift`, `.ts`, `.jsx`, `.tsx`, and `.sql`.
4. **Bundle size and cleanliness.** Total size across all files must not exceed 100 MB. Hidden binary or metadata files such as `.DS_Store` and `.pyc` can cause uploads to fail.
5. **Skill name.** Inside `SKILL.md`, `name` must be all lowercase with words separated by hyphens (for example `my-new-skill`).
6. **Google services.** Accessing Google Workspace (Calendar, Drive) from a skill depends on the Keep Activity setting. With Keep Activity off, those integrations are unavailable.
7. **No hooks, subagents, plugins, or MCP** as in Antigravity or Gemini CLI.

## How to Adapt a Skill

- Replace unsupported file types with supported ones: convert `.ts` or `.sql` reference files to `.txt` or `.md`, or inline their contents into `SKILL.md` or `references/*.md`.
- Remove `.DS_Store`, `__pycache__`, `*.pyc`, and unnecessary dotfiles (such as `.gitattributes`) before uploading.
- Remove terminal steps. Replace them with instructions asking the user to provide the required text or files directly in chat.
- Write `description` in the third person (under 1024 characters) including clear "Use when ..." triggers. Start `name` with an action verb and avoid generic names like `helper` or `tools`.
- Keep the skill concise like a cheat sheet: clear steps, formatting rules, and common pitfalls to avoid. Tell Gemini what to do when details are missing (ask the user instead of guessing).

## Validate Before Uploading

```bash
python3 <skill_dir>/scripts/validate_skill.py <skill-folder> --target gemini-app
```

The `gemini-app` target checks for unsupported file types, hidden files, total bundle size, and scripts that appear to access the network.
