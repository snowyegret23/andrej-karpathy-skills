import json
import sys


SUPPORTED_EVENTS = {"SessionStart", "PostCompact"}


def load_payload() -> dict:
    try:
        return json.load(sys.stdin)
    except json.JSONDecodeError as exc:
        print(f"karpathy_context: invalid hook JSON: {exc}", file=sys.stderr)
        raise SystemExit(1)


def main() -> int:
    payload = load_payload()
    event_name = payload.get("hook_event_name", "")
    if event_name not in SUPPORTED_EVENTS:
        return 0

    context = (
        "Use $karpathy-guidelines for code/review/debug/refactor/plans. "
        "Follow AGENTS.md. Windows: PowerShell, no Bash heredocs, UTF-8 Python "
        "text IO, relative paths."
    )

    output = {
        "hookSpecificOutput": {
            "hookEventName": event_name,
            "additionalContext": context,
        }
    }
    print(json.dumps(output))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
