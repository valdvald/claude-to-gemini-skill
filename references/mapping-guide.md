# Claude to Gemini/Antigravity Skill Mapping Guide

Reference guide for mapping directory structures, YAML frontmatter, substitution syntax, tool names, hooks, and rules from Claude/Claude Code to Google Antigravity, Gemini CLI, and the Gemini app. Verified against official documentation on 2026-11-21 (see `SKILL.md` for source URLs).

## Contents

1. Directory Locations and Scopes
2. YAML Frontmatter Mapping
3. Body Syntax and Substitutions
4. Tool Name Mapping
5. Hooks
6. Rules and Always-On Context
7. Installation and Verification
8. Prompt Style Adjustments

## 1. Directory Locations and Scopes

| Scope | Claude Code | Antigravity (App / CLI / IDE) | Gemini CLI |
| :--- | :--- | :--- | :--- |
| **Project** | `.claude/skills/<name>/SKILL.md` | `.agents/skills/<name>/SKILL.md` (legacy: `.agent/`; parent folders up to repo root are also scanned) | `.agents/skills/<name>/` or `.gemini/skills/<name>/` |
| **Global** | `~/.claude/skills/<name>/SKILL.md` | `~/.gemini/config/skills/<name>/SKILL.md` (legacy IDE: `~/.gemini/antigravity/skills/`; CLI also reads `~/.gemini/skills/` and `~/.gemini/antigravity-cli/skills/`) | `~/.agents/skills/<name>/` or `~/.gemini/skills/<name>/` |
| **Legacy command** | `.claude/commands/<name>.md` | Skill `<name>/SKILL.md`. Do not use Antigravity workflows (deprecated). (`agy plugin import gemini` also converts legacy Gemini CLI commands into skills.) | Skill, or `.gemini/commands/<name>.toml` for manual-only commands |
| **Plugin skills** | `<plugin>/skills/<name>/SKILL.md` | `~/.gemini/config/plugins/<plugin>/skills/` (namespaced `<plugin>:<skill>`, managed via `agy plugin`) | Extension skills |
| **Always-on context** | `CLAUDE.md`, `.claude/rules/*.md` | `AGENTS.md` or `GEMINI.md`, `.agents/rules/*.md` | `GEMINI.md` |
| **Subagents** | `.claude/agents/*.md` | Custom agents: `.agents/agents/<name>.md` | Out of scope for this skill |
| **MCP** | `.mcp.json` | `mcp_config.json` in `.agents/` or `~/.gemini/config/` (remote server URL key: `serverUrl`) | `mcpServers` in `settings.json` |
| **Hooks** | `hooks` field, settings, plugins | `.agents/hooks.json`, `~/.gemini/config/hooks.json` | `hooks` in `settings.json` |

Antigravity CLI does not read `.gemini/skills/` (the legacy Gemini CLI project path), so move project skills to `.agents/skills/`. Antigravity scans only one level deep and loads skill folders sitting directly inside `skills/`. To load skills from another directory or nested structure without copying, use a `skills.json` manifest (in `.agents/` for project scope or `~/.gemini/config/` for user scope). Paths in the manifest must be absolute or relative to the proper folder, and `~` is not expanded:

```json
{
  "entries": [
    { "path": "/home/dev/team-config/skills", "exclude": ["draft-skill"] }
  ]
}
```

## 2. YAML Frontmatter Mapping

The Agent Skills open standard defines `name`, `description`, `license`, `compatibility`, `metadata`, and `allowed-tools` (experimental). All other fields are Claude Code extensions.

| Claude Code Field | Status on Target | Conversion Action |
| :--- | :--- | :--- |
| `name` | Required by spec and Gemini CLI. Optional in Antigravity (defaults to folder name). Gemini app requires lowercase with hyphens. | Keep. 1-64 characters, `a-z`, `0-9`, single hyphens, matching folder name. |
| `description` | Required. Max 1024 characters. | Keep and strengthen: state what it does and when to use it, third person, quote if it contains `: ` or `#`. |
| `license` | Standard, optional | Keep. |
| `compatibility` | Standard, optional, max 500 characters | Keep. Replace "Designed for Claude Code" with actual environment requirements (for example "Requires git and python3"). |
| `metadata` | Standard, optional | Keep as a string-to-string map (quote numbers such as `"1.0"`). |
| `allowed-tools` | Standard but experimental; support varies across platforms | Remove. In Claude this pre-approves tools rather than restricting them. Configure permissions via Antigravity Permissions or Gemini CLI policy. |
| `when_to_use` | Claude Code extension | Merge into `description` (total max 1024). Do not merge for manual-only skills (see `disable-model-invocation`). |
| `argument-hint`, `arguments` | Claude Code extension | Remove and move to `## Inputs`. |
| `disable-model-invocation` | Claude Code extension | Remove. If `true`: add `## Safety Gate` at the top of the body, and phrase `description` with "Use only when the user explicitly asks ...". |
| `user-invocable` | Claude Code extension | Remove. If `false`, phrase `description` as background reference knowledge. |
| `disallowed-tools` | Claude Code extension | Remove. Turn into explicit behavioral constraints in the body ("Do not edit or write files"). |
| `context` (`fork`) | Claude Code extension | Remove. Instruct running heavy exploration in a subagent (if available) and returning only a concise summary. |
| `agent` (`Explore`, `Plan`, etc.) | Claude Code extension | Remove. Convert the intended agent role into a role-focus instruction at the top of the body. |
| `background` | Claude Code extension | Remove. Note in the body if long-running processes should run in the background. |
| `model`, `effort` | Claude Code extension | Remove. Never hardcode Claude model names. Describe the expected depth of analysis instead. |
| `hooks` | Claude Code extension | Remove. See Section 5. |
| `paths` | Claude Code extension | Remove. Mention patterns in `description` and `## When to Use`. For automatic per-file activation see Section 6. |
| `shell` | Claude Code extension | Remove. Specify the required shell in the execution command and script shebang. |

## 3. Body Syntax and Substitutions

| Claude Code Syntax | Behavior in Claude Code | Converted Form |
| :--- | :--- | :--- |
| `` !`git diff HEAD` `` | Executed before the prompt reaches the model; output replaces the line | Explicit step: "Run `git diff HEAD` in the terminal and read the output." Gemini CLI custom command: `!{git diff HEAD}` (prompts for confirmation). |
| `` ```! `` block | Same, for multiple commands | One explicit step per command, or a single helper script in `scripts/`. |
| `$ARGUMENTS` | All arguments after `/name`. If omitted from body, Claude Code appends `ARGUMENTS: <value>` | `## Inputs` with a fallback to ask the user. Gemini CLI custom command: `{{args}}`. |
| `$0`, `$1`, `$ARGUMENTS[0]` | Positional arguments with shell-style quoting | Named parameters under `## Inputs` (`<environment>`, `<target_file>`). TOML custom commands do not support positional arguments. |
| `$name` | Named argument declared in `arguments` | Same parameter name under `## Inputs`. |
| `${CLAUDE_SKILL_DIR}` | Absolute path to the current skill folder | Relative path from the skill folder (`scripts/check.py`), plus an instruction to resolve against the folder containing `SKILL.md` since shells typically run from the project root. |
| `${CLAUDE_PLUGIN_ROOT}` | Absolute path to the plugin root | Same as above. |
| `${CLAUDE_PROJECT_DIR}` | Absolute path to the project root | Workspace or repository root (`./`, "from the repository root"). |
| `${CLAUDE_SESSION_ID}` | Unique session ID | Remove, or use a timestamp-based temp filename (`/tmp/report-<timestamp>.md`). |
| `${CLAUDE_EFFORT}` | Current session effort level | Remove conditional branches. State the expected depth of analysis in the body. |

## 4. Tool Name Mapping

In skill bodies, use neutral capability phrasing because internal tool names vary across surfaces and versions. Use target-specific tool names only in hook and permission configurations.

| Claude Code Tool | Neutral phrasing for skill body | Gemini CLI | Antigravity |
| :--- | :--- | :--- | :--- |
| `Read` | Read the relevant file | `read_file`, `read_many_files` | `view_file` |
| `Write` | Create or write a new file | `write_file` | `write_to_file` |
| `Edit` | Update the relevant section of the file | `replace` | `replace_file_content` |
| `MultiEdit` | Update multiple sections in one file | `replace` | `multi_replace_file_content` |
| `NotebookEdit` | Edit notebook cells | No dedicated documented tool | See Jupyter notebooks docs |
| `Glob` | Find files by name pattern | `glob` | `find_by_name` |
| `Grep` | Search text or regex across the codebase | `grep_search` | `grep_search` |
| `LS` | List directory contents | `list_directory` | `list_dir` |
| `Bash` | Run a shell command | `run_shell_command` | `run_command` |
| `WebFetch` | Fetch and read a URL's content | `web_fetch` | `read_url_content` |
| `WebSearch` | Perform a web search | `google_web_search` | `search_web` |
| `TodoWrite` | Create and update a task checklist | `write_todos` | No documented 1:1 equivalent |
| `Task` / `Agent` | Delegate subtasks to a subagent (if available) | Subagent when enabled | `invoke_subagent` |
| `AskUserQuestion` | Ask the user | `ask_user` | `ask_question` |
| `Skill` | Invoke another skill by name | `activate_skill` | Call `/<name>` or name the skill |
| `mcp__<server>__<tool>` | Use the `<server>` MCP server to [capability] | Tool from MCP server | Tool from MCP server |

## 5. Hooks

Hooks do not live in skill frontmatter. In Antigravity, hooks live in `hooks.json` (workspace: `.agents/hooks.json`, global: `~/.gemini/config/hooks.json`, or inside plugins). In Gemini CLI, hooks live under the `hooks` key in `settings.json` (project, user, system, or extension). Antigravity supports only `command` handlers.

| Claude Code Event | Antigravity | Gemini CLI |
| :--- | :--- | :--- |
| `PreToolUse` | `PreToolUse` | `BeforeTool` |
| `PostToolUse` | `PostToolUse` | `AfterTool` |
| `SessionStart` | `SessionStart` | `SessionStart` |
| `Stop` | `Stop` | `AfterAgent` (fires when the agent turn ends; supports retry) |
| `UserPromptSubmit` | Not 1:1 (`PreInvocation` fires before each model call) | `BeforeAgent` (fires after user submits a prompt, before planning) |

Tool event `matcher` values are regexes over the target's tool names, not Claude's:

| Claude Code | Antigravity | Gemini CLI |
| :--- | :--- | :--- |
| `Bash` | `run_command` | `run_shell_command` |
| `Edit`, `Write` | `replace_file_content`, `multi_replace_file_content`, `write_to_file` | `replace`, `write_file` |
| `Read` | `view_file` | `read_file` |
| `mcp__<server>__<tool>` | Antigravity MCP tool pattern | `mcp_<server>_<tool>` (single underscores) |

Example Antigravity `hooks.json` running a check script before every shell command (prompts the user when the script returns `decision: "ask"`):

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

Input/output contracts differ. Antigravity hooks receive camelCase JSON on stdin (such as `toolCall.name`, `toolCall.args`, `conversationId`). `PreToolUse` hooks must print JSON to stdout with `decision` (`allow`, `auto_approve`, `deny`, `ask`, `force_ask`, or `deny_unless_prior_grant`) and an optional `reason`. `PostToolUse` hooks return `{}`, and `Stop` hooks return `decision: "continue"` to keep the agent going. Claude Code hook scripts (with their own exit codes and JSON schema) cannot be reused verbatim; mark them as a manual follow-up and rewrite them. In Antigravity CLI, hooks in `~/.gemini/antigravity-cli/settings.json` are not loaded, and `/hooks` lists active hooks.

## 6. Rules and Always-On Context

`AGENTS.md` and `GEMINI.md` use no frontmatter and are always loaded. Every file in `.agents/rules/*.md` must begin with frontmatter containing a valid `trigger`. Without it, or with an unrecognized value (such as `alwaysOn`), the rule is silently dropped.

| `trigger` | Behavior | Used For |
| :--- | :--- | :--- |
| `always_on` | Always loaded in full | Replacement for `CLAUDE.md` or Claude rules without `paths` |
| `glob` | Activates when the agent touches files matching `globs` | Replacement for `paths` |
| `model_decision` | Only path and `description` load initially; body is read when relevant | Long domain guidelines |
| `manual` | Loaded only via `@`-mention (not supported in CLI) | Checklists or audit rubrics |

```markdown
---
trigger: glob
globs: "migrations/**/*.sql"
description: "SQL migration conventions and audit reminder."
---

Before finishing work on SQL migration files, audit them with the `sql-audit` skill.
```

Limits: Antigravity scans only `.md` files directly inside `.agents/rules/` (subfolders are ignored unless registered in `.agents/rules.json`). Rule files larger than 24,000 bytes are truncated, and global plus `always_on` rules share a 20,000-token budget (if exceeded, the largest rules become on-demand pointers). Quote `globs` patterns that start with `*`. Antigravity also reads `AGENTS.md` and `GEMINI.md` in each parent folder up to the repository root. Use skills for multi-step workflows and rules for constraints and invariants.

Converting `CLAUDE.md`: update references inside skills to `GEMINI.md` (Gemini CLI and Antigravity) or `AGENTS.md` (Antigravity). Converting the contents of `CLAUDE.md` itself is out of scope unless requested. If requested, `@path` file-inlining imports map to `@[label](path)` in Antigravity rule files (paths relative to the rule file; imported frontmatter is stripped). Plain `@filename` in Antigravity only references the path without inlining its content.

## 7. Installation and Verification

Antigravity, project scope (read by App, CLI, and IDE):

```bash
mkdir -p .agents/skills
cp -R ./<name> .agents/skills/<name>
```

Antigravity, global scope (read by App, CLI, and IDE):

```bash
mkdir -p ~/.gemini/config/skills
cp -R ./<name> ~/.gemini/config/skills/<name>
```

Antigravity CLI, packaged as a plugin (managed via `agy plugin`):

```bash
agy plugin install ./my-skills-plugin
agy plugin list --json
```

Gemini CLI:

```bash
gemini skills install ./<name>                      # user scope (default)
gemini skills install ./<name> --scope workspace    # project scope
```

Inside a Gemini CLI session, `/skills link /path/to/skills-repo --scope workspace` links a skill folder without copying, and `/skills reload` refreshes the list. The `--consent` flag on `gemini skills install` skips the security prompt, so avoid using it on unaudited third-party skills.

Gemini app: Customize > Skills > Create > Upload, then select `SKILL.md`, a folder, or a `.zip` containing `SKILL.md` at its root. See `references/gemini-app.md` for details.

Verify that the skill loaded:

| Target | How to Check |
| :--- | :--- |
| Antigravity App | Settings > Projects > select project > Customizations, or Customizations > Installed |
| Antigravity CLI | `/skills` (run `/skills reload` or start a new conversation after adding a skill) |
| Antigravity IDE | Customizations menu in the agent panel |
| Gemini CLI | `/skills list` |
| Gemini app | Customize > Skills |

If a skill does not load, check in order: folder location, nesting depth (directly under `skills/`), exact filename `SKILL.md`, valid YAML frontmatter, and duplicate names in a higher-precedence location.

## 8. Prompt Style Adjustments

- **Preserve source structure.** Normalize only when needed, such as mixed XML tags and Markdown or inconsistent headings. Pick one delimiter style and use it consistently.
- **Progressive disclosure.** Move large reference tables, schemas, or long examples to `references/` or `assets/` so `SKILL.md` stays under 500 lines.
- **Scripts as black boxes.** Instruct the agent to run `python3 scripts/<name>.py --help` first only when the script parses arguments. Otherwise, document its usage in `SKILL.md`.
- **Decision trees.** Summarize branching workflows in a compact table or decision tree.
- **Explain the "why".** Pair important rules with a short reason so the model applies them consistently without rigidity.
