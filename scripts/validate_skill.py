#!/usr/bin/env python3
"""Validate a converted Gemini / Antigravity Agent Skill.

Checks the YAML frontmatter against the Agent Skills spec and common loader
pitfalls, looks for leftover Claude Code syntax in SKILL.md, references/ and
scripts/, verifies relative file references, and applies target-specific rules.

Usage:
    python3 validate_skill.py <skill-dir-or-SKILL.md> [--target TARGET]
                              [--allow-claude-references] [--style] [--strict]

Exit code: 0 when there are no errors (and no warnings with --strict), else 1.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

try:  # PyYAML is optional. When present, the frontmatter is parsed strictly.
    import yaml  # type: ignore
except Exception:  # pragma: no cover - depends on the environment
    yaml = None

TARGETS = ("generic", "antigravity", "gemini-cli", "gemini-app")

MAX_NAME = 64
MAX_DESCRIPTION = 1024
MAX_COMPATIBILITY = 500
MAX_LINES = 500
GEMINI_APP_MAX_BYTES = 100 * 1024 * 1024

# Fields defined by the Agent Skills open standard.
STANDARD_KEYS = {"name", "description", "license", "compatibility", "metadata", "allowed-tools"}

# Claude Code extensions that Gemini and Antigravity do not read.
CLAUDE_ONLY_FRONTMATTER_KEYS = {
    "when_to_use",
    "argument-hint",
    "arguments",
    "disable-model-invocation",
    "user-invocable",
    "disallowed-tools",
    "model",
    "effort",
    "context",
    "agent",
    "background",
    "hooks",
    "paths",
    "shell",
}

# Leftover Claude syntax in SKILL.md and references/ (errors; notes with
# --allow-claude-references).
CLAUDE_BODY_PATTERNS = [
    (re.compile(r"!\s*`[^`\n]+`"), "Claude inline shell injection (!`command`)"),
    (re.compile(r"^[ \t]*```!", re.M), "Claude fenced shell injection block (```!)"),
    (re.compile(r"\$ARGUMENTS(?:\[\d+\])?"), "Claude argument substitution ($ARGUMENTS)"),
    (re.compile(r"\$\{?CLAUDE_[A-Z0-9_]+\}?"), "Claude variable ($CLAUDE_* or ${CLAUDE_*})"),
    (re.compile(r"(?:~/)?\.claude(?:-plugin)?/"), "Claude directory path (.claude/...)"),
    (re.compile(r"\bCLAUDE(?:\.local)?\.md\b"), "Claude context file (CLAUDE.md)"),
    (
        re.compile(
            r"\b(?:MultiEdit|TodoWrite|NotebookEdit|WebFetch|WebSearch|AskUserQuestion"
            r"|ExitPlanMode|EnterPlanMode|BashOutput|KillShell|SlashCommand)\b"
        ),
        "Claude tool name",
    ),
    (re.compile(r"\bmcp__[A-Za-z0-9_-]+__[A-Za-z0-9_-]+"), "Claude MCP tool id (mcp__server__tool)"),
]

# Ambiguous words that are only suspicious in context (warnings).
CLAUDE_BODY_WARN_PATTERNS = [
    (re.compile(r"`(?:Read|Write|Edit|Glob|Grep|Bash|Task|Skill|LS)`"), "possible Claude tool name in backticks"),
    (re.compile(r"\b(?:Read|Write|Edit|Glob|Grep|Bash|Task)\s+tool\b"), "possible Claude tool reference ('<Tool> tool')"),
    (re.compile(r"\b(?:Bash|Read|Write|Edit)\([^)\n]*\)"), "Claude permission rule syntax (for example Bash(git *))"),
    (re.compile(r"\b(?:using|via|use)\s+(?:the\s+)?(?:Bash|Grep|Glob)\b"), "possible Claude tool reference ('using Bash')"),
]

# Narrower set for scripts, where words like '!`' can be legitimate shell code.
SCRIPT_PATTERNS = [
    (re.compile(r"\bCLAUDE_[A-Z0-9_]+\b"), "Claude environment variable (CLAUDE_*)"),
    (re.compile(r"(?:~/)?\.claude(?:-plugin)?/"), "Claude directory path (.claude/...)"),
    (re.compile(r"\bCLAUDE(?:\.local)?\.md\b"), "Claude context file (CLAUDE.md)"),
]

POSITIONAL_ARG_RE = re.compile(r"(?<![\w$])\$[0-9](?!\d)")
BACKSLASH_PATH_RE = re.compile(r"\b(?:scripts|references|assets|examples|resources)\\[\w.-]")
VALID_NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
FENCE_RE = re.compile(r"^[ \t]*(`{3,}|~{3,})")
LIST_ITEM_RE = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s+\S")
TRIGGER_RE = re.compile(
    r"\b(?:use|when|whenever|trigger|triggers|gunakan|pakai|ketika|saat|setiap kali|jika|bila)\b", re.I
)
PERSON_RE = re.compile(
    r"\b(?:I can|I will|I'll|I am|you can|you will|Anda dapat|Anda bisa|saya dapat|saya bisa)\b", re.I
)

MD_LINK_RE = re.compile(r"!?\[[^\]]*\]\(\s*<?([^)\s>]+)>?(?:\s+[\"'][^\"']*[\"'])?\s*\)")
CODE_REF_RE = re.compile(r"`((?:scripts|references|assets|examples|resources)/[^`\s]+)`")
EXTERNAL_PREFIXES = ("http://", "https://", "mailto:", "tel:", "data:", "#")
PLACEHOLDER_CHARS = set("<>*{}$|")
SUPPORT_DIRS = ("scripts", "references", "assets", "examples", "resources")

# File types that the Gemini app does not accept inside a skill upload.
GEMINI_APP_UNSUPPORTED_EXT = {
    ".doc", ".xls", ".ppt", ".raw",
    ".cs", ".kt", ".kts", ".php", ".r", ".rb", ".scala", ".swift", ".ts",
    ".jsx", ".tsx", ".sql",
    ".mp3", ".wav", ".m4a", ".aac", ".flac", ".ogg", ".mp4", ".mov", ".avi", ".mkv", ".webm", ".mpeg", ".mpg",
    ".zip", ".tar", ".gz", ".tgz", ".bz2", ".xz", ".7z", ".rar",
}
GEMINI_APP_JUNK_NAMES = {".DS_Store", "Thumbs.db"}
GEMINI_APP_JUNK_DIRS = {"__pycache__", ".git", ".svn", ".hg"}
GEMINI_APP_JUNK_EXT = {".pyc", ".pyo"}
NETWORK_RE = re.compile(
    r"\b(?:requests\.(?:get|post|put|patch|delete|request)|urllib|http\.client|httpx|aiohttp|urlopen|curl|wget|axios|socket\.connect)\b"
    r"|\bfetch\("
)


class Report:
    """Collects findings. Claude-syntax findings can be downgraded to notes."""

    def __init__(self, allow_claude_references: bool) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self.notes: list[str] = []
        self.allow = allow_claude_references

    def error(self, msg: str) -> None:
        self.errors.append(msg)

    def warn(self, msg: str) -> None:
        self.warnings.append(msg)

    def claude(self, msg: str, hard: bool = False) -> None:
        if self.allow:
            self.notes.append(msg)
        elif hard:
            self.errors.append(msg)
        else:
            self.warnings.append(msg)


def read_text(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return None


def line_of(text: str, index: int, first_line: int = 1) -> int:
    return first_line + text.count("\n", 0, index)


def mask_fenced_blocks(text: str) -> str:
    """Blank out fenced code blocks while keeping line numbers stable."""
    out: list[str] = []
    opener: str | None = None
    for line in text.splitlines():
        match = FENCE_RE.match(line)
        if opener is None:
            if match:
                opener = match.group(1)
                out.append("")
            else:
                out.append(line)
        else:
            if match and match.group(1)[0] == opener[0] and len(match.group(1)) >= len(opener):
                opener = None
            out.append("")
    return "\n".join(out)


# ---------------------------------------------------------------- frontmatter


def split_frontmatter(text: str, report: Report) -> tuple[str | None, str, int]:
    """Return (frontmatter_text, body, first_body_line)."""
    if text.startswith("\ufeff"):
        report.error("SKILL.md starts with a UTF-8 BOM. Remove it so '---' is the first thing in the file.")
        text = text.lstrip("\ufeff")
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        report.error("Frontmatter must start with '---' on line 1.")
        return None, text, 1
    for idx in range(1, len(lines)):
        if lines[idx].strip() == "---":
            return "\n".join(lines[1:idx]), "\n".join(lines[idx + 1 :]), idx + 2
    report.error("Closing '---' for YAML frontmatter not found.")
    return None, text, 1


def _unquote(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        return value[1:-1]
    return value


def naive_parse(fm_text: str) -> dict:
    """Small fallback parser used when PyYAML is unavailable or the YAML is invalid."""
    data: dict = {}
    key: str | None = None
    block: str | None = None
    for raw in fm_text.splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        stripped = raw.strip()
        indented = raw.startswith((" ", "\t"))
        if not indented and ":" in raw and not stripped.startswith("- "):
            k, v = raw.split(":", 1)
            key = k.strip()
            v = v.strip()
            if v[:1] in ("|", ">"):
                block = v[0]
                data[key] = ""
            else:
                block = None
                data[key] = _unquote(v)
            continue
        if key is None:
            continue
        current = data[key]
        if stripped.startswith("- "):
            item = _unquote(stripped[2:])
            if current == "" or isinstance(current, list):
                data[key] = (current if isinstance(current, list) else []) + [item]
            else:
                data[key] = f"{current} {stripped}"
            continue
        if indented and re.match(r"^[A-Za-z0-9_.-]+:\s*", stripped) and (current == "" or isinstance(current, dict)):
            k2, v2 = stripped.split(":", 1)
            mapping = current if isinstance(current, dict) else {}
            mapping[k2.strip()] = _unquote(v2)
            data[key] = mapping
            continue
        sep = "\n" if block == "|" else " "
        data[key] = f"{current}{sep}{stripped}".strip() if current else stripped
    return data


def parse_frontmatter(fm_text: str, report: Report) -> dict:
    if yaml is not None:
        try:
            data = yaml.safe_load(fm_text)
        except yaml.YAMLError as exc:  # type: ignore[attr-defined]
            detail = " ".join(str(exc).split())[:160]
            report.error(
                f"Frontmatter is not valid YAML ({detail}). A description containing ': ' or ' #' "
                "must be wrapped in double quotes."
            )
            return naive_parse(fm_text)
        if data is None:
            return {}
        if not isinstance(data, dict):
            report.error("Frontmatter must be a YAML mapping of keys to values.")
            return {}
        return data
    return naive_parse(fm_text)


def check_raw_description(fm_text: str, report: Report) -> None:
    for raw in fm_text.splitlines():
        match = re.match(r"^description:[ \t]*(.*)$", raw)
        if not match:
            continue
        value = match.group(1).strip()
        if not value or value[0] in "\"'|>":
            return
        if " #" in value:
            report.warn(
                "description contains ' #' outside quotes. YAML treats the rest of the line as a comment "
                "and truncates the description. Wrap it in double quotes."
            )
        if yaml is None and ": " in value:
            report.warn(
                "description contains ': ' outside quotes and may be invalid YAML (PyYAML is not installed "
                "to confirm). Wrap it in double quotes."
            )
        return


def check_fields(data: dict, skill_dir: Path | None, target: str, report: Report) -> None:
    name = data.get("name")
    if name is None or name == "":
        if target == "antigravity":
            report.warn("Missing 'name'. Antigravity defaults to the folder name, but the Agent Skills spec requires it.")
        else:
            report.error("Missing required frontmatter field: 'name'.")
    elif not isinstance(name, str):
        report.error("'name' must be a string.")
    else:
        if len(name) > MAX_NAME:
            report.error(f"'name' exceeds {MAX_NAME} characters ({len(name)}).")
        if not VALID_NAME_RE.match(name):
            report.error(
                f"Invalid 'name' value '{name}': use lowercase a-z, 0-9 and single hyphens, "
                "without a leading or trailing hyphen."
            )
        if skill_dir is not None and skill_dir.name != name:
            report.warn(f"Folder name '{skill_dir.name}' does not match frontmatter name '{name}'.")

    description = data.get("description")
    if description is None or (isinstance(description, str) and not description.strip()):
        report.error("Missing required frontmatter field: 'description'.")
    elif not isinstance(description, str):
        report.error("'description' must be a string (check for an unquoted [ or { at the start).")
    else:
        text = description.strip()
        if len(text) > MAX_DESCRIPTION:
            report.error(f"'description' exceeds {MAX_DESCRIPTION} characters ({len(text)}).")
        if not TRIGGER_RE.search(text):
            report.warn("description may not say WHEN to use the skill. Add trigger phrases such as 'Use when ...'.")
        if PERSON_RE.search(text):
            report.warn("description should use the third person (avoid 'I can ...' or 'You can ...').")

    compatibility = data.get("compatibility")
    if compatibility is not None:
        if not isinstance(compatibility, str):
            report.warn("'compatibility' should be a string.")
        elif len(compatibility) > MAX_COMPATIBILITY:
            report.error(f"'compatibility' exceeds {MAX_COMPATIBILITY} characters ({len(compatibility)}).")

    metadata = data.get("metadata")
    if metadata is not None:
        if not isinstance(metadata, dict):
            report.warn("'metadata' should be a map of string keys to string values.")
        elif any(not isinstance(v, str) for v in metadata.values()):
            report.warn("'metadata' values should be strings (quote numbers such as \"1.0\").")

    for key in data:
        if key in CLAUDE_ONLY_FRONTMATTER_KEYS:
            report.error(f"Residual Claude-only frontmatter field found: '{key}'.")
        elif key == "allowed-tools":
            report.warn(
                "'allowed-tools' is experimental in the Agent Skills spec and Claude's tool rules mean nothing "
                "in Gemini or Antigravity. Remove it and configure permissions in the target instead."
            )
        elif key not in STANDARD_KEYS:
            report.warn(f"Non-standard frontmatter field '{key}' will be ignored by Agent Skills loaders.")


# ----------------------------------------------------------------------- body


def check_body(body: str, first_line: int, report: Report) -> None:
    if not body.strip():
        report.error("SKILL.md body is empty.")
        return
    for pattern, label in CLAUDE_BODY_PATTERNS:
        match = pattern.search(body)
        if match:
            report.claude(f"SKILL.md line {line_of(body, match.start(), first_line)}: {label}.", hard=True)
    for pattern, label in CLAUDE_BODY_WARN_PATTERNS:
        match = pattern.search(body)
        if match:
            report.claude(f"SKILL.md line {line_of(body, match.start(), first_line)}: {label}.")
    masked = mask_fenced_blocks(body)
    match = POSITIONAL_ARG_RE.search(masked)
    if match:
        report.claude(
            f"SKILL.md line {line_of(masked, match.start(), first_line)}: positional argument placeholder "
            "($0, $1, ...). Replace with named inputs under '## Inputs'."
        )
    match = BACKSLASH_PATH_RE.search(body)
    if match:
        report.warn(
            f"SKILL.md line {line_of(body, match.start(), first_line)}: file reference uses a backslash. "
            "Use forward slashes."
        )


def check_references(body: str, skill_dir: Path, report: Report) -> None:
    root = skill_dir.resolve()
    seen: set[str] = set()
    candidates = [m.group(1) for m in MD_LINK_RE.finditer(body)] + [m.group(1) for m in CODE_REF_RE.finditer(body)]
    for raw in candidates:
        href = raw.strip()
        if href.startswith(EXTERNAL_PREFIXES):
            continue
        href = href.split("#", 1)[0].split("?", 1)[0]
        if not href or any(ch in href for ch in PLACEHOLDER_CHARS):
            continue
        if "/" not in href and not re.search(r"\.\w+$", href):
            continue
        if href in seen:
            continue
        seen.add(href)
        resolved = (skill_dir / href).resolve()
        try:
            resolved.relative_to(root)
        except ValueError:
            report.warn(f"File reference '{href}' points outside the skill folder. Keep skills self-contained.")
            continue
        if not resolved.exists():
            report.warn(f"Broken file reference in SKILL.md: '{href}'.")


def check_style(body: str, first_line: int, report: Report) -> None:
    if "\u2014" in body or "\u2013" in body:
        report.warn("[style] SKILL.md contains em-dash or en-dash characters.")
    lines = mask_fenced_blocks(body).splitlines()
    bad: list[int] = []
    for i in range(1, len(lines)):
        prev = lines[i - 1]
        if (
            LIST_ITEM_RE.match(lines[i])
            and prev.strip()
            and not LIST_ITEM_RE.match(prev)
            and not prev.startswith((" ", "\t"))
            and not prev.lstrip().startswith(("#", "|", ">"))
        ):
            bad.append(first_line + i)
    if bad:
        shown = ", ".join(str(n) for n in bad[:5])
        report.warn(f"[style] list without a blank line before it (line {shown}).")


# ------------------------------------------------------------ supporting files


def scan_supporting_files(skill_dir: Path, report: Report) -> None:
    for sub in SUPPORT_DIRS:
        directory = skill_dir / sub
        if not directory.is_dir():
            continue
        patterns = SCRIPT_PATTERNS if sub == "scripts" else CLAUDE_BODY_PATTERNS
        for path in sorted(directory.rglob("*")):
            if not path.is_file():
                continue
            text = read_text(path)
            if text is None:
                continue
            rel = path.relative_to(skill_dir).as_posix()
            for pattern, label in patterns:
                match = pattern.search(text)
                if match:
                    report.claude(f"{rel} line {line_of(text, match.start())}: {label}.")


# Folders that hold an Antigravity or Gemini customization tree (".agents/skills", "~/.gemini/config/skills").
CUSTOMIZATION_ROOTS = {".agents", ".agent", "_agents", "_agent", "config", ".gemini", "antigravity", "antigravity-cli"}


def check_nesting(skill_dir: Path, report: Report) -> None:
    """Warn when the skill sits one level too deep inside a known customization tree."""
    resolved = skill_dir.resolve()
    parent = resolved.parent
    grandparent = parent.parent
    if (
        parent.name != "skills"
        and grandparent.name == "skills"
        and grandparent.parent.name in CUSTOMIZATION_ROOTS
    ):
        report.warn(
            "Skill folder is nested below 'skills/'. Antigravity scans only one level, so it will not load "
            "'skills/<category>/<name>/' without a skills.json manifest."
        )


def check_gemini_app_bundle(skill_dir: Path, report: Report) -> None:
    total = 0
    for path in sorted(skill_dir.rglob("*")):
        rel = path.relative_to(skill_dir)
        parts = set(rel.parts)
        if parts & GEMINI_APP_JUNK_DIRS:
            if path.is_dir() and path.name in GEMINI_APP_JUNK_DIRS:
                report.error(f"Remove '{rel.as_posix()}' before uploading to the Gemini app (hidden or binary content).")
            continue
        if not path.is_file():
            continue
        total += path.stat().st_size
        suffix = path.suffix.lower()
        if path.name in GEMINI_APP_JUNK_NAMES or suffix in GEMINI_APP_JUNK_EXT:
            report.error(f"Remove '{rel.as_posix()}' before uploading to the Gemini app (hidden or binary file).")
        elif suffix in GEMINI_APP_UNSUPPORTED_EXT:
            report.error(
                f"'{rel.as_posix()}' has a file type the Gemini app does not accept ('{suffix}'). "
                "Convert it to .txt or .md, or inline its content."
            )
        elif path.name == ".env" or suffix == ".env":
            report.warn(f"'{rel.as_posix()}' may contain secrets. Do not upload credentials to a skill.")
        elif path.name.startswith(".") and path.name != ".gitkeep":
            report.warn(f"Hidden file '{rel.as_posix()}' may make the Gemini app upload fail.")
        if rel.parts and rel.parts[0] == "scripts" and suffix in {".py", ".sh", ".js"}:
            text = read_text(path)
            if text and NETWORK_RE.search(text):
                report.warn(
                    f"'{rel.as_posix()}' appears to use the network. The Gemini app does not support scripts "
                    "that need internet access."
                )
    if total > GEMINI_APP_MAX_BYTES:
        report.error(f"Bundle is {total / (1024 * 1024):.1f} MB. The Gemini app limit is 100 MB.")


# ----------------------------------------------------------------------- main


def validate(path: Path, target: str, report: Report, style: bool) -> None:
    if path.is_dir():
        skill_dir: Path | None = path
        skill_md = path / "SKILL.md"
    else:
        skill_dir = None
        skill_md = path
    if not skill_md.exists():
        report.error(f"SKILL.md not found at {skill_md}")
        return
    text = read_text(skill_md)
    if text is None:
        report.error(f"{skill_md} is not readable as UTF-8 text.")
        return

    line_count = len(text.splitlines())
    if line_count > MAX_LINES:
        report.warn(f"SKILL.md has {line_count} lines (recommended <= {MAX_LINES}). Move detail to references/.")

    fm_text, body, first_line = split_frontmatter(text, report)
    if fm_text is not None:
        check_raw_description(fm_text, report)
        data = parse_frontmatter(fm_text, report)
        check_fields(data, skill_dir, target, report)
        check_body(body, first_line, report)
        if skill_dir is not None:
            check_references(body, skill_dir, report)
        if style:
            check_style(body, first_line, report)

    if skill_dir is not None:
        scan_supporting_files(skill_dir, report)
        if target in ("generic", "antigravity"):
            check_nesting(skill_dir, report)
        if target == "gemini-app":
            check_gemini_app_bundle(skill_dir, report)
    elif target == "gemini-app":
        report.warn("Pass the skill folder (not only SKILL.md) to check the bundle for the Gemini app.")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate a converted Gemini / Antigravity Agent Skill.",
        epilog=(
            "Targets: generic (default), antigravity, gemini-cli, gemini-app. "
            "The gemini-app target also checks the bundle (unsupported file types, hidden files, size, network scripts)."
        ),
    )
    parser.add_argument("path", help="Path to the skill directory or its SKILL.md.")
    parser.add_argument("--target", choices=TARGETS, default="generic", help="Target surface (default: generic).")
    parser.add_argument(
        "--allow-claude-references",
        action="store_true",
        help="Report Claude syntax found in text as notes instead of errors or warnings. "
        "Use for documentation-style skills such as this converter.",
    )
    parser.add_argument(
        "--style",
        action="store_true",
        help="Also run optional style checks (em/en dashes, blank line before lists).",
    )
    parser.add_argument("--strict", action="store_true", help="Exit with code 1 when there are warnings too.")
    args = parser.parse_args(argv)

    report = Report(allow_claude_references=args.allow_claude_references)
    validate(Path(args.path), args.target, report, args.style)

    if report.errors:
        print("ERRORS:")
        for item in report.errors:
            print(f"  - {item}")
    if report.warnings:
        print("WARNINGS:")
        for item in report.warnings:
            print(f"  - {item}")
    if report.notes:
        print("NOTES (Claude syntax allowed by --allow-claude-references):")
        for item in report.notes:
            print(f"  - {item}")

    if report.errors:
        print(f"FAILED: {len(report.errors)} error(s), {len(report.warnings)} warning(s).")
    elif report.warnings:
        print("PASS WITH WARNINGS: No blocking errors found.")
    else:
        print("OK: Skill passed all validation checks.")

    failed = bool(report.errors) or (args.strict and bool(report.warnings))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
