import json
import re
import shlex
import subprocess
import sys
from pathlib import Path


TEXT_SUFFIXES = {".py", ".ps1", ".bat", ".md", ".json", ".yaml", ".yml", ".toml", ".txt"}
TEXT_NAMES = {".gitattributes", ".gitignore"}
DEFAULT_EOL = b"\r\n"
SKIP_DIRS = {
    ".git",
    ".venv",
    "venv",
    "env",
    "node_modules",
    "dist",
    "build",
    "out",
    "target",
    "__pycache__",
}
PATHISH_KEYS = {
    "file",
    "file_path",
    "filepath",
    "filename",
    "path",
    "target_file",
    "target_path",
}
COMMAND_KEYS = {"command", "cmd", "script", "tool_input"}
PATCH_PATH_RE = re.compile(r"^\*\*\* (?:Update|Add|Delete) File: (.+)$")
PATCH_MOVE_RE = re.compile(r"^\*\*\* Move to: (.+)$")


def load_payload() -> dict:
    try:
        return json.load(sys.stdin)
    except json.JSONDecodeError:
        return {}


def repo_root(cwd: str | None) -> Path:
    base = Path(cwd or ".").resolve()
    result = subprocess.run(
        ["git", "-C", str(base), "rev-parse", "--show-toplevel"],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode == 0 and result.stdout.strip():
        return Path(result.stdout.strip()).resolve()
    return base


def is_under(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root)
    except (OSError, ValueError):
        return False
    return True


def is_text_target(path: Path) -> bool:
    return path.suffix.lower() in TEXT_SUFFIXES or path.name.lower() in TEXT_NAMES


def iter_text_files(root: Path):
    stack = [root]
    while stack:
        current = stack.pop()
        try:
            children = list(current.iterdir())
        except OSError:
            continue
        for path in children:
            if path.is_symlink():
                continue
            if path.is_dir():
                if path.name not in SKIP_DIRS:
                    stack.append(path)
            elif path.suffix.lower() in TEXT_SUFFIXES or path.name.lower() in TEXT_NAMES:
                yield path


def iter_payload_items(value, key: str = ""):
    if isinstance(value, dict):
        for child_key, child_value in value.items():
            yield from iter_payload_items(child_value, str(child_key))
    elif isinstance(value, list):
        for item in value:
            yield from iter_payload_items(item, key)
    else:
        yield key, value


def command_tokens(command: str) -> list[str]:
    try:
        return shlex.split(command, posix=False)
    except ValueError:
        return re.findall(r'"([^"]+)"|\'([^\']+)\'|(\S+)', command)


def clean_token(token) -> str:
    if isinstance(token, tuple):
        token = next((part for part in token if part), "")
    return str(token).strip().strip("\"'")


def looks_pathish(text: str) -> bool:
    if not text or any(char in text for char in "*?[]"):
        return False
    path = Path(text)
    return (
        path.suffix.lower() in TEXT_SUFFIXES
        or path.name.lower() in TEXT_NAMES
        or "\\" in text
        or "/" in text
    )


def payload_path_strings(payload: dict) -> set[str]:
    paths: set[str] = set()
    for key, value in iter_payload_items(payload):
        if not isinstance(value, str):
            continue
        lower_key = key.lower()
        for line in value.splitlines():
            match = PATCH_PATH_RE.match(line) or PATCH_MOVE_RE.match(line)
            if match:
                paths.add(match.group(1).strip())
        if lower_key in PATHISH_KEYS:
            paths.add(value)
        elif lower_key in COMMAND_KEYS:
            for token in command_tokens(value):
                cleaned = clean_token(token)
                if looks_pathish(cleaned):
                    paths.add(cleaned)
    return paths


def resolve_payload_paths(payload: dict, root: Path) -> list[Path]:
    base = Path(payload.get("cwd") or ".").resolve()
    result: list[Path] = []
    seen: set[Path] = set()
    for raw in payload_path_strings(payload):
        candidate = Path(raw)
        options = [candidate] if candidate.is_absolute() else [base / candidate, root / candidate]
        for option in options:
            try:
                resolved = option.resolve()
            except OSError:
                continue
            if resolved in seen or not is_under(resolved, root):
                continue
            if resolved.is_file() and is_text_target(resolved):
                result.append(resolved)
                seen.add(resolved)
                break
            if resolved.is_dir() and resolved != root:
                result.append(resolved)
                seen.add(resolved)
                break
    return result


def iter_target_text_files(target: Path):
    if target.is_file():
        if is_text_target(target):
            yield target
    elif target.is_dir():
        yield from iter_text_files(target)


def git_head_bytes(root: Path, path: Path) -> bytes | None:
    try:
        rel_path = path.resolve().relative_to(root).as_posix()
    except ValueError:
        return None
    result = subprocess.run(
        ["git", "-C", str(root), "show", f"HEAD:{rel_path}"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != 0:
        return None
    return result.stdout


def detect_eol(data: bytes) -> bytes | None:
    crlf = data.count(b"\r\n")
    stripped = data.replace(b"\r\n", b"")
    lf = stripped.count(b"\n")
    cr = stripped.count(b"\r")
    if crlf == 0 and lf == 0 and cr == 0:
        return None
    if crlf >= lf and crlf >= cr:
        return b"\r\n"
    if lf >= cr:
        return b"\n"
    return b"\r"


def normalize_bytes(data: bytes, eol: bytes) -> bytes:
    normalized = data.replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    if eol == b"\n":
        return normalized
    if eol == b"\r":
        return normalized.replace(b"\n", b"\r")
    return normalized.replace(b"\n", b"\r\n")


def normalize_file(root: Path, path: Path) -> None:
    try:
        data = path.read_bytes()
    except OSError:
        return
    base_data = git_head_bytes(root, path)
    if base_data is None:
        eol = DEFAULT_EOL
    else:
        eol = detect_eol(data) or detect_eol(base_data) or DEFAULT_EOL
    normalized = normalize_bytes(data, eol)
    if normalized != data:
        try:
            path.write_bytes(normalized)
        except OSError:
            return


def main() -> int:
    payload = load_payload()
    root = repo_root(payload.get("cwd"))
    for target in resolve_payload_paths(payload, root):
        for path in iter_target_text_files(target):
            normalize_file(root, path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
