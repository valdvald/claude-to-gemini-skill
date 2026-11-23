# Claude to Gemini Skill Converter

An [Agent Skill](https://agentskills.io/specification) that converts Claude and Claude Code skills (`.claude/skills/`) and custom commands (`.claude/commands/`) into portable skills for **Google Antigravity** (App, CLI, IDE), **Gemini CLI**, and the **Gemini app**.

## What It Does

- Audits source `SKILL.md` files, legacy `.claude/commands/*.md` commands, and supporting directories (`scripts/`, `references/`, `assets/`).
- Standardizes YAML frontmatter and preserves the intent of Claude Code-only fields (`disable-model-invocation`, `when_to_use`, `context: fork`, `hooks`, `paths`, `allowed-tools`, `disallowed-tools`).
- Rewrites Claude-specific body syntax (`` !`command` ``, `` ```! ``, `$ARGUMENTS`, `$0`, `${CLAUDE_SKILL_DIR}`, `CLAUDE.md`, Claude tool names, and `mcp__server__tool` IDs) into target-compatible instructions.
- Includes a Python validator (`scripts/validate_skill.py`) with per-target checks (`generic`, `antigravity`, `gemini-cli`, `gemini-app`).

## Repository Structure

```text
claude-to-gemini-skill/
├── SKILL.md                      # Main converter instructions and workflow
├── references/
│   ├── mapping-guide.md          # Paths, frontmatter, tools, hooks, and rules mapping
│   ├── examples.md               # Before-and-after conversion examples
│   └── gemini-app.md             # Gemini app upload rules and bundle constraints
├── scripts/
│   └── validate_skill.py         # Validator for converted skills (Python 3.8+)
└── README.md
```

## Installation

### Google Antigravity (App, CLI, and IDE)

Clone or copy the repository into your project or global skills directory:

```bash
# Project scope (recommended, shared with Gemini CLI)
mkdir -p .agents/skills
git clone https://github.com/zakirevaldi/claude-to-gemini-skill.git .agents/skills/claude-to-gemini-skill

# Global scope (all workspaces)
mkdir -p ~/.gemini/config/skills
git clone https://github.com/zakirevaldi/claude-to-gemini-skill.git ~/.gemini/config/skills/claude-to-gemini-skill
```

In Antigravity CLI, run `/skills` (or `/skills reload`) to verify the skill is loaded.

### Gemini CLI

Install directly from GitHub:

```bash
# User scope (default)
gemini skills install https://github.com/zakirevaldi/claude-to-gemini-skill.git

# Workspace / project scope
gemini skills install https://github.com/zakirevaldi/claude-to-gemini-skill.git --scope workspace
```

Verify inside a session with `/skills list`.

### Gemini App (Web)

1. Download the repository as a `.zip` (or zip the folder locally) and make sure `SKILL.md` is at the root of the archive.
2. Remove hidden files such as `.gitattributes` or `.DS_Store` before uploading so the Gemini app uploader does not reject the bundle.
3. Open [gemini.google.com](https://gemini.google.com), go to **Menu > Customize > Skills > Create > Upload**, select the `.zip` file, review, and click **Create**.

## Usage

Invoke the skill automatically by asking Gemini or Antigravity to convert a Claude skill, or call it explicitly with `/claude-to-gemini-skill`:

> "Convert this Claude Code skill so it works in Google Antigravity and Gemini CLI: [paste SKILL.md or attach folder]"

### Running the Validator

```bash
python3 scripts/validate_skill.py <path-to-converted-skill> --target antigravity
```

Available `--target` values: `generic` (default), `antigravity`, `gemini-cli`, `gemini-app`. Add `--strict` to treat warnings as errors, or `--style` for optional Markdown formatting checks.

## License

Add a `LICENSE` file (such as MIT) if you plan to distribute this repository publicly.
