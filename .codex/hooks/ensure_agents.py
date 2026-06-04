import json
import shutil
import subprocess
import sys
from pathlib import Path


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


def is_template_repo(root: Path) -> bool:
    if root.name.lower() == "andrej-karpathy-skills":
        return True
    result = subprocess.run(
        ["git", "-C", str(root), "config", "--get", "remote.origin.url"],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    return result.returncode == 0 and "andrej-karpathy-skills" in result.stdout.lower()


def find_template(root: Path) -> Path | None:
    candidates = [
        root / ".codex" / "templates" / "AGENTS.md",
        Path(__file__).resolve().parent.parent / "templates" / "AGENTS.md",
    ]
    for path in candidates:
        if path.is_file():
            return path
    return None


def main() -> int:
    payload = load_payload()
    root = repo_root(payload.get("cwd"))
    if is_template_repo(root):
        return 0

    target = root / "AGENTS.md"
    if target.exists():
        return 0

    template = find_template(root)
    if template is None:
        return 0

    shutil.copyfile(template, target)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
