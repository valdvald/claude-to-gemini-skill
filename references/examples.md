# Conversion Examples

Real-world before-and-after examples converting Claude Code skills and commands into standard Gemini / Google Antigravity Agent Skills. Note that converted skill bodies always preserve the source language.

## Example 1: Manual-Only Skill with Shell Injection, Arguments, and Restrictions

### Before (Claude Code: `.claude/skills/release-check/SKILL.md`)

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

### After (Gemini / Antigravity: `.agents/skills/release-check/SKILL.md`)

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

### Migration Notes (Example 1)

- `disable-model-invocation: true` becomes `## Safety Gate`. `description` uses "Use only when the user explicitly asks ..." and does not expand auto-trigger keywords from `when_to_use`, preserving manual-only behavior.
- `when_to_use` is not merged broadly because this skill is manual-only; its phrases are used only to scope explicit user requests.
- `` !`git status --short` `` and `` !`git log -n 5 --oneline` `` become explicit terminal commands in Step 1.
- `$0` and `$ARGUMENTS` become `## Inputs`, absorbing `argument-hint`.
- `${CLAUDE_SKILL_DIR}/scripts/check_changelog.py` becomes a relative path plus a resolution reminder, since the shell typically runs from the project root.
- `CLAUDE.md`, `Bash`, and `Grep` become neutral references. `allowed-tools` and `model` are removed; `git` permissions move to Antigravity Permissions or Gemini CLI policy (manual follow-up).
- `git` and `python3` requirements move to `compatibility`.

## Example 2: Legacy Command with `context: fork` and `paths`

### Before (Claude Code: `.claude/commands/sql-audit.md`)

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

### After (Gemini / Antigravity: `.agents/skills/sql-audit/SKILL.md`)

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

Optional Antigravity rule to automatically remind the agent whenever migration files are touched (`.agents/rules/sql-migrations.md`):

````markdown
---
trigger: glob
globs: "migrations/**/*.sql"
description: "Reminder to audit SQL migrations."
---

Before finishing work on SQL migration files, audit them with the `sql-audit` skill.
````

### Migration Notes (Example 2)

- The single file `.claude/commands/sql-audit.md` is wrapped into `sql-audit/SKILL.md` with `name: sql-audit` and an expanded `description`.
- `disallowed-tools: Write, Edit` becomes an explicit read-only rule.
- `paths` moves into `description` and `## Scope and Constraints`. For automatic per-file activation, an optional `trigger: glob` rule is created (frontmatter is mandatory or the rule is silently dropped).
- `context: fork` and `agent: Explore` become guidance to isolate analysis and return concise findings.
- `${CLAUDE_PROJECT_DIR}` becomes the workspace root, and `$ARGUMENTS` becomes the user-specified files.

## Example 3: Manual-Only Command for Gemini CLI (`.toml`)

For manual-only commands using shell injection and arguments, Gemini CLI has a closer match than a skill: a TOML custom command. Skills are not preprocessed, whereas TOML commands support `!{...}` and `{{args}}`.

### Before (Claude Code: `.claude/commands/changes.md`)

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

### After (Gemini CLI: `.gemini/commands/changes.toml`, invoked with `/changes`)

````toml
description = "Review uncommitted changes"
prompt = """
Review the uncommitted changes below. Extra focus: {{args}}

!{git diff HEAD}
"""
````

### Migration Notes (Example 3)

- `$ARGUMENTS` becomes `{{args}}`. Inside `!{...}`, `{{args}}` is automatically shell-escaped.
- `` !`git diff HEAD` `` becomes `!{git diff HEAD}`. Gemini CLI asks for confirmation before running shell commands in custom commands.
- `disable-model-invocation: true` is satisfied natively because TOML commands only run when invoked by the user.
- `allowed-tools` and `argument-hint` are removed. Run `/commands reload` after adding or editing `.toml` files.
- Braces inside `!{...}` must be balanced. For complex commands, put the logic in a script and call that script from `!{...}`.
- Antigravity does not use this format; convert the same command for Antigravity using the Example 1 pattern (a skill with a Safety Gate). Antigravity CLI converts legacy TOML commands into skills via `agy plugin import gemini`.
- For free-tier and Google One users, Gemini CLI was replaced by Antigravity CLI (see `SKILL.md`), so `.toml` applies only to users still on Gemini CLI.

## Example 4: Skill with `` ```! `` Block, Named Arguments, and CLI Dependencies

### Before (Claude Code: `.claude/skills/pr-summary/SKILL.md`)

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

### After (Gemini / Antigravity: `.agents/skills/pr-summary/SKILL.md`)

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

### Migration Notes (Example 4)

- The `` ```! `` block contains two commands, so both become explicit terminal commands in Step 1. Without conversion, the block would remain literal text.
- `$pr_number` (named argument from `arguments`) becomes `pr_number` under `## Inputs`.
- Because this skill is not manual-only, `when_to_use` is merged into `description` to preserve auto-trigger accuracy.
- `allowed-tools: Bash(gh *)` is removed and noted as a manual follow-up (configure `gh` in Antigravity Permissions or Gemini CLI policy). The `gh` and `python3` dependencies move to `compatibility`.
- `effort: low` is dropped with no replacement needed. This skill is unsuitable for the Gemini app because it requires a terminal and `gh`.

## Sample Migration Summary (for Example 1)

1. **Key Changes**: Removed `when_to_use`, `argument-hint`, `allowed-tools`, and `model` from frontmatter. Rewrote `description` and added `compatibility`. Converted shell injections into terminal steps, `$0` and `$ARGUMENTS` into `## Inputs`, `${CLAUDE_SKILL_DIR}` into a relative path, and `CLAUDE.md` into `GEMINI.md`.
2. **Behavior Adaptations**: Converted `disable-model-invocation: true` into `## Safety Gate` and a "Use only when ..." description. Replaced `Bash` and `Grep` tool names with neutral capability phrasing.
3. **Manual Follow-Ups**: Configure `git` permissions in Antigravity Permissions or Gemini CLI policy. Install via `cp -R release-check .agents/skills/` (Antigravity) or `gemini skills install ./release-check --scope workspace` (Gemini CLI).
4. **Verification**: `validate_skill.py --target antigravity` passed with 0 errors. Skill appears in `/skills` and triggers only when explicitly requested.
