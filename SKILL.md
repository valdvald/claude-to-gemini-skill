---
name: claude-to-gemini-skill
description: "Converts Claude and Claude Code skills and custom commands (.claude/skills/, .claude/commands/, SKILL.md) into Agent Skills compatible with Google Antigravity (App, CLI, IDE), Gemini CLI, and the Gemini app. Use whenever the user wants to migrate, port, adapt, convert, or install a Claude skill on Gemini or Antigravity, or provides a Claude SKILL.md file, folder, zip archive, or pasted text for conversion."
compatibility: "Antigravity (App, CLI, IDE), Gemini CLI, Gemini app. Validation script requires Python 3.8+ (PyYAML optional)."
---
# Claude to Gemini Skill Converter

Convert Claude and Claude Code skills and custom commands into portable Agent Skills ready for Google Antigravity (App, CLI, IDE), Gemini CLI, and the Gemini app without losing the original intent or workflow logic.

## When to Use

- The user wants to port or install a Claude skill (`SKILL.md` or `.claude/skills/<name>/` folder) on Gemini or Antigravity.
- The user wants to convert a legacy Claude Code custom command (`.claude/commands/<name>.md`) into a standard skill.
- The user wants to audit a skill to remove Claude Code-specific syntax (shell command injection, `$ARGUMENTS`, `${CLAUDE_SKILL_DIR}`, `hooks`, `context: fork`, `paths`).
- The user asks for a skill package ready to install or upload to Gemini, Antigravity, or Gemini CLI.

## Principles

1. **Preserve intent, not syntax.** Convert Claude features without a direct equivalent into procedural instructions or documented manual follow-ups. Never drop them silently.
2. **Preserve the source skill's language.** Translate only if the user explicitly asks. Keep standard headings (`## Inputs`, `## Steps`) in English.
3. **Read source scripts; do not run them.** Third-party skills may contain unsafe commands. Audit them strictly by reading their contents.
4. **Do not overwrite the source.** Write the converted output to a new folder (for example `converted/<name>/`) so the original skill remains intact.
5. **Platform details evolve quickly.** The tables below were verified against official documentation on 2026-11-21 (see Sources). If live behavior differs, follow the official docs and note the discrepancy.

## Target Surfaces and Paths

Identify the user's target first. If none is specified, generate one standard skill folder and provide placement commands for Antigravity and Gemini CLI. The project path `.agents/skills/` is read by all Antigravity surfaces and by Gemini CLI, making it the safest default. Global paths differ per surface, so no single global path covers all of them.

| Target Surface | Workspace / Project Path | Global / User Path | Notes |
| :--- | :--- | :--- | :--- |
| **Antigravity App** | `<workspace>/.agents/skills/<name>/SKILL.md` | `~/.gemini/config/skills/<name>/SKILL.md` | Auto-triggered via `description` or manually via `/<name>`. Parent folders up to the repository root are also scanned. Singular `.agent/` is still supported. |
| **Antigravity IDE** | `<workspace>/.agents/skills/<name>/SKILL.md` | `~/.gemini/config/skills/<name>/SKILL.md` (legacy `~/.gemini/antigravity/skills/` also supported) | Active skills appear in the Customizations menu on the agent panel. |
| **Antigravity CLI (`agy`)** | `<workspace>/.agents/skills/<name>/SKILL.md` | `~/.gemini/config/skills/<name>/SKILL.md`. CLI-only: `~/.gemini/antigravity-cli/skills/` and `~/.gemini/skills/` | Every skill automatically becomes a slash command. Plugin skills live in `~/.gemini/config/plugins/<plugin>/skills/`. |
| **Gemini CLI** | `<workspace>/.agents/skills/<name>/SKILL.md` or `.gemini/skills/<name>/SKILL.md` | `~/.agents/skills/<name>/SKILL.md` or `~/.gemini/skills/<name>/SKILL.md` | Within the same tier, `.agents/skills/` takes precedence over `.gemini/skills/`. Activated via `activate_skill` with user confirmation. |
| **Gemini app** | No filesystem path. Customize > Skills > Create > Upload | Tied to the user's account | No terminal, restricted file types, offline scripts only. Read `references/gemini-app.md`. |

Important notes:

- Antigravity scans only one level deep. Skill folders must sit directly inside `skills/` (`skills/<name>/`), not nested as `skills/<category>/<name>/`.
- Precedence for duplicate skill names: in Antigravity CLI, `~/.gemini/antigravity-cli/skills/` and `~/.gemini/skills/` override all other locations. Across Antigravity generally, precedence is personal folder in repo, workspace, `~/.gemini/config/`, then built-in. In Gemini CLI, precedence is workspace, user, extension, then built-in.
- Antigravity re-reads skills on every turn. `/skills reload` or a new conversation only refreshes the slash command list.
- `~/.agents/skills/` is not listed in Antigravity's documentation. Use `~/.gemini/config/skills/` for global Antigravity skills.
- Antigravity CLI does not read `.gemini/skills/` (the legacy Gemini CLI project path). Move skills there to `.agents/skills/`.
- Per the Gemini CLI documentation banner, for free-tier and Google One users, Gemini CLI was replaced by Antigravity CLI on June 18, 2026. If the user is on those tiers or unsure, prioritize Antigravity as the target.

## Conversion Workflow

Follow these steps in order. See `references/mapping-guide.md` for full field and syntax tables, `references/examples.md` for before-and-after examples, and `references/gemini-app.md` for Gemini app constraints.

### Step 0: Identify Target and Check Capabilities

1. Determine the target (Antigravity, Gemini CLI, or Gemini app). If unspecified, use the standard path above.
2. Check whether the source skill relies on capabilities absent from the target:
   - Terminal, git, local project filesystem, or MCP servers: unavailable in the Gemini app. Inform the user, recommend Antigravity or Gemini CLI, or rewrite as a pure instruction skill if the user still wants the Gemini app.
   - Scripts requiring internet access: not supported in the Gemini app.
   - Hooks, subagents, plugins, and MCP servers do not transfer via frontmatter. Record them as manual follow-ups (see Step 2 and the Decision Tree).

### Step 1: Audit the Source Skill

1. Read the entire `SKILL.md` (or command file) and list all supporting files (`scripts/`, `references/`, `assets/`, `examples/`, `resources/`). Read scripts as text without executing them. If the input is a `.zip` or `.skill` archive, extract it to a working directory first. If the input is pasted text, save it as `SKILL.md` in a folder matching `name`.
2. Identify the core purpose, expected inputs, outputs, and external dependencies (CLIs, Python/Node packages, MCP servers, environment variables).
3. Inventory all Claude Code-specific features: frontmatter fields, `` !`command` `` and `` ```! `` blocks, `$ARGUMENTS`, `$0`, `$name`, `${CLAUDE_*}` variables, tool names, `mcp__server__tool` IDs, `CLAUDE.md` references, and references to other skills.
4. Note the source document's language. Keep the converted output in the same language.

### Step 2: Clean and Standardize YAML Frontmatter

Ensure line 1 is `---` with no UTF-8 BOM. Invalid frontmatter or a missing `description` causes the skill to be silently skipped.

1. Keep only standard Agent Skills fields:
   - `name` (required by spec): 1-64 characters, lowercase `a-z`, digits, and single hyphens, no leading or trailing `-`, matching the folder name. Optional in Antigravity (defaults to folder name), but always include it.
   - `description` (required): 1-1024 characters, third person, stating both what the skill does and when to trigger it. Wrap in double quotes if it contains `: ` or `#`, as unquoted values produce invalid YAML.
   - `license`, `compatibility` (max 500 characters; note dependencies like `git` or `python3`), and `metadata` (string-to-string map).
2. If the source lacks frontmatter (common in legacy commands), derive `name` from the filename and write `description` from the command's purpose. Prefix with the subfolder name if duplicates occur across subfolders (for example `frontend-component`).
3. Handle Claude Code-only fields without losing their logic:
   - `when_to_use`: merge its trigger keywords into `description` (total max 1024 characters). Exception: if `disable-model-invocation: true` is also set, do not broaden `description` with auto-trigger phrases (see next item).
   - `disable-model-invocation: true`: remove. Add a `## Safety Gate` section at the top of the body requiring explicit user confirmation before external side effects (deploy, commit, tag, delete data, send messages). Phrase `description` with "Use only when the user explicitly asks to ..." so it does not auto-trigger.
   - `user-invocable: false`: remove. Write `description` as background reference knowledge so it activates only contextually.
   - `argument-hint` and `arguments`: move to an `## Inputs` section in the body.
   - `allowed-tools` and `disallowed-tools`: remove Claude patterns (`Bash(git *)`, `Read`, `Grep`). In Claude, `allowed-tools` only pre-approves tools rather than restricting them; target permissions are configured in Antigravity Permissions or Gemini CLI policy, not skill frontmatter. Convert `disallowed-tools` into explicit body constraints (for example, "Read-only mode: do not modify any files").
   - `context: fork`, `agent`, `background`: remove. Instruct the agent to delegate heavy work to an isolated subagent if available, or summarize verbose output before continuing.
   - `model` and `effort`: remove. State the expected depth of analysis in the body.
   - `hooks`: remove. Target hooks live in separate files (`.agents/hooks.json` or `~/.gemini/config/hooks.json` in Antigravity, `settings.json` in Gemini CLI). Convert the checks into mandatory verification steps in the body and log hook migration as a manual follow-up. See `references/mapping-guide.md` for event and JSON contract details.
   - `paths`: remove. Mention the file patterns in `description` and `## When to Use`. For automatic activation when touching specific files, create an `.agents/rules/<name>.md` rule with `trigger: glob` (see `references/examples.md`).
   - `shell`: remove. Specify the required shell in the execution command in the body.

### Step 3: Convert Body Syntax and References

1. **Shell command injection** (`` !`command` `` and `` ```! `` blocks): convert into explicit initial steps under `## Steps` instructing the agent to run the command in the terminal and read the output. Gemini CLI and Antigravity do not preprocess `SKILL.md`, so literal injection syntax would remain unexecuted and cause the model to guess outputs. For manual-only commands targeting Gemini CLI, consider a `.toml` custom command, which supports `!{...}` and `{{args}}` (see `references/examples.md`).
2. **Arguments** (`$ARGUMENTS`, `$0`, `$1`, `$ARGUMENTS[N]`, `$name`): convert into an `## Inputs` section naming each parameter and defining fallbacks (for example, "If not provided, ask the user before continuing"). Reference those parameter names in each step.
3. **Claude path and runtime variables**:
   - `${CLAUDE_SKILL_DIR}/...` and `${CLAUDE_PLUGIN_ROOT}/...`: convert to paths relative to the skill folder (for example `scripts/<script>.py`). Because the agent's shell typically runs from the project root rather than the skill folder, explicitly note that the path must be resolved relative to the folder containing `SKILL.md` before execution.
   - `${CLAUDE_PROJECT_DIR}`: replace with the workspace or repository root.
   - `${CLAUDE_SESSION_ID}`: remove or replace with a timestamp-based temporary filename.
   - `${CLAUDE_EFFORT}`: remove conditional branches and state the expected analysis depth directly.
4. **Tool names and ecosystem references**:
   - Replace Claude tool names (`Read`, `Write`, `Edit`, `MultiEdit`, `NotebookEdit`, `Glob`, `Grep`, `Bash`, `WebFetch`, `WebSearch`, `TodoWrite`, `Task`, `AskUserQuestion`) with capability-based phrasing ("read the file", "search the codebase", "run a shell command", "ask the user"). Target-specific tool names belong only in hooks and permission configs (see `references/mapping-guide.md`).
   - Replace `mcp__<server>__<tool>` IDs with "use the `<server>` MCP server to [capability]" and list the server as a manual follow-up.
   - Update references to other skills ("invoke skill `x`") to match converted skill names, and convert and install those dependency skills too.
   - Replace `CLAUDE.md` with `GEMINI.md` (or `AGENTS.md` in Antigravity) or project rules, and replace `.claude/skills/` or `.claude/commands/` with `.agents/skills/`.
5. **Structure and style**: preserve the source skill's structure. Normalize only when needed (inconsistent headings, mixed XML tags and Markdown, ambiguous instructions). Briefly explain the "why" behind important rules so the model follows them consistently. Keep `SKILL.md` under 500 lines and move long reference material into `references/`.

### Step 4: Audit Supporting Files (Multi-File Skills)

1. Inspect every file in `scripts/`, `references/`, `assets/`, `examples/`, and `resources/`.
2. Find and fix hardcoded `~/.claude/`, `.claude/`, and `CLAUDE_*` variables (including unbraced `$CLAUDE_PROJECT_DIR`) in scripts and reference docs.
3. Ensure all references from `SKILL.md` to supporting files use one-level-deep relative paths from the skill folder (`references/<file>.md`, `scripts/<script>.py`) with forward slashes `/`.
4. Instruct the agent to run `--help` before using a script only if the script actually parses arguments (such as `argparse` or `commander`). Scripts without argument parsing will execute immediately. When in doubt, document usage directly in `SKILL.md`.
5. For the Gemini app target, verify all bundled file types are supported (see `references/gemini-app.md`).

### Step 5: Validate the Converted Skill

Run the validation script. Because the agent's shell usually runs from the project root, use the absolute path to this converter skill's folder (`<skill_dir>`):

```bash
python3 <skill_dir>/scripts/validate_skill.py --help
python3 <skill_dir>/scripts/validate_skill.py <output-folder> --target <antigravity|gemini-cli|gemini-app|generic>
```

The script checks YAML frontmatter validity, residual Claude syntax in the body, `references/`, and `scripts/`, broken file links, and target-specific constraints. Fix all ERRORS and review WARNINGS. Manual checks:

- Frontmatter opens on line 1 with `---` and has a valid `description`.
- No residual Claude syntax or variables remain, and `SKILL.md` is under 500 lines.
- The skill loads in the target: Antigravity App via Settings > Projects > Customizations, Antigravity CLI via `/skills`, Gemini CLI via `/skills list`, Gemini app via Customize > Skills.
- Test one realistic prompt that should trigger the skill and verify its steps match the source intent.

### Step 6: Deliver the Output and Migration Summary

Deliver the output tailored to the target:

- **Antigravity**: complete skill folder and placement commands (`.agents/skills/<name>/` for project scope, `~/.gemini/config/skills/<name>/` for global scope).
- **Gemini CLI**: skill folder and `gemini skills install <path>` (add `--scope workspace` for project scope).
- **Gemini app**: folder or `.zip` with `SKILL.md` at the root, ready to upload via Customize > Skills > Create > Upload.

Full installation and verification commands are in `references/mapping-guide.md`. Always include a concise **Migration Summary**:

1. **Key Changes**: converted frontmatter fields, syntax, and paths.
2. **Behavior Adaptations**: Claude features rewritten as procedural instructions (`disable-model-invocation`, shell injection, `context: fork`).
3. **Manual Follow-Ups**: hooks, `.agents/rules/` files, MCP servers, subagents, and permissions requiring separate configuration in the target.
4. **Verification**: `validate_skill.py` results and target load check status.

## Decision Tree for Unsupported Extensions

| Claude Code Feature | Conversion Strategy for Gemini / Antigravity |
| :--- | :--- |
| `` !`cmd` `` or `` ```! `` block | Explicit first step: run the command in the terminal and read its output. Gemini CLI custom command: `!{cmd}`. |
| `$ARGUMENTS`, `$0`, `$1`, `$name` | `## Inputs` section with named parameters and fallbacks when omitted. Gemini CLI custom command: `{{args}}` (single string). |
| `disable-model-invocation: true` | `## Safety Gate` at the top of the body plus `description` starting with "Use only when the user explicitly asks ...". |
| `context: fork` and `agent` | Instruct using an isolated subagent (if available) or summarizing output to keep the main context clean. |
| `hooks` | Mandatory verification step in the body, plus note migrating to Antigravity `hooks.json` or Gemini CLI `settings.json`. Hook scripts must be rewritten due to different JSON contracts. |
| `paths` (glob) | Mention patterns in `description`, and create `.agents/rules/<name>.md` with `trigger: glob` if automatic per-file activation is needed. |
| `allowed-tools` | Remove. Configure permissions in Antigravity Permissions or Gemini CLI policy. |
| `mcp__<server>__<tool>` | Rewrite as capability plus MCP server name, and log server configuration as a manual follow-up. |
| `.claude/commands/<name>.md` | Wrap into `<name>/SKILL.md`. For manual-only commands on Gemini CLI, `.gemini/commands/<name>.toml` is an alternative. |
| `.claude/agents/*.md`, plugins, `.mcp.json` | Out of scope for this skill. Report as manual follow-ups (custom agents, plugins, `mcp_config.json` in Antigravity). |

## Gotchas

- **Broadening `description` on manual-only skills**: merging `when_to_use` into a `disable-model-invocation: true` skill causes it to auto-trigger on the target. Use "Use only when the user explicitly asks ..." and include a Safety Gate.
- **Dropping `when_to_use` outright**: on auto-invocable skills, dropping it removes trigger keywords and stops the skill from firing. Merge them into `description`.
- **Unquoted `description` containing `: `**: breaks YAML parsing (for example `description: Use when: user asks X`) and prevents the skill from loading. Wrap it in double quotes.
- **Relative paths vs. working directory**: `scripts/<script>.py` is relative to the skill folder, while the agent's shell usually runs from the project root. Explicitly state to resolve paths against the folder containing `SKILL.md`.
- **Leaving shell injection syntax untouched**: both `` !`command` `` and `` ```! `` become literal text, causing the model to assume output is already present or fabricate it.
- **Hardcoded paths inside `scripts/` and `references/`**: `SKILL.md` is often cleaned while scripts still reference `~/.claude/skills/...`, `$CLAUDE_PROJECT_DIR`, or `${CLAUDE_PLUGIN_ROOT}`. Always audit supporting files.
- **Claude-only tool names**: phrases like "Use the MultiEdit tool" or "Call TodoWrite" confuse Gemini agents. Use neutral capability verbs instead.
- **Using `--help` on scripts without argument parsing**: running `--help` on a script without an argument parser may execute its real action. Check the script or its docs first.
- **Rule files without frontmatter**: files in `.agents/rules/` without frontmatter or with an unrecognized `trigger` are silently ignored. Valid values: `always_on`, `model_decision`, `glob`, `manual`.
- **Nested skill folders**: Antigravity scans only one level deep, so `skills/<category>/<name>/` will not load without a `skills.json` manifest.
- **Translating skill contents**: changing the instruction language alters behavior and breaks trigger keywords. Translate only when requested.
- **Mechanical conversion without preserving intent**: never strip `disable-model-invocation: true` from deploy or production skills without adding a confirmation gate in the body.
- **Uploading uncleaned bundles to the Gemini app**: hidden files like `.DS_Store`, `.pyc`, or unsupported extensions (such as `.ts`, `.sql`) can cause upload failures.

## Sources

Paths and behaviors below were verified on 2026-11-21. Re-check if live behavior differs.

- Antigravity: https://antigravity.google/docs/skills, https://antigravity.google/docs/rules, https://antigravity.google/docs/hooks, https://antigravity.google/docs/customization-discovery, https://antigravity.google/docs/cli/gcli-migration/
- Gemini CLI: https://geminicli.com/docs/cli/skills/, https://geminicli.com/docs/cli/custom-commands, https://geminicli.com/docs/hooks, https://geminicli.com/docs/reference/tools
- Gemini app: https://support.google.com/gemini/answer/17094296 and https://support.google.com/gemini/answer/17102773
- Agent Skills standard: https://agentskills.io/specification
- Claude Code skills: https://code.claude.com/docs/en/skills
