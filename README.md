# andrej-karpathy-skills

Codex에서 `$karpathy-guidelines`를 repo-local skill로 쓰기 위한 파일 모음입니다.

## 파일 구성

```text
.agents/skills/karpathy-guidelines/SKILL.md
.agents/skills/karpathy-guidelines/agents/openai.yaml
.codex/config.toml
.codex/hooks.json
.codex/hooks/ensure_agents.py
.codex/hooks/karpathy_context.py
.codex/hooks/normalize_text_line_endings.py
.codex/templates/AGENTS.md
README_for_codex.md
```

- `.agents/skills/karpathy-guidelines/SKILL.md`: 공통 코딩 행동 지침입니다.
- `.agents/skills/karpathy-guidelines/agents/openai.yaml`: Codex UI에 표시할 skill 메타데이터입니다.
- `.codex/config.toml`: Codex hooks 기능을 켭니다.
- `.codex/hooks.json`: 수명 주기 hook 실행 조건과 명령을 정의합니다.
- `.codex/templates/AGENTS.md`: 대상 저장소에 복사할 자체 완결형 `AGENTS.md` 템플릿입니다.
- `README_for_codex.md`: Codex에게 사용자 전역 설치를 맡길 때 읽히는 절차서입니다.

## Hook 동작

- `ensure_agents.py`: `SessionStart startup`에서 `AGENTS.md`가 없으면 템플릿을 복사합니다.
- `karpathy_context.py`: `SessionStart`와 `PostCompact`에서 skill, AGENTS, Windows 실행 지침만 짧게 주입합니다.
- `normalize_text_line_endings.py`: 새 텍스트 파일은 CRLF로 맞추고, 기존 추적 텍스트 파일은 기존 개행 스타일을 따릅니다.
- `PostToolUse` matcher는 `.*`로 두고, 각 hook script가 payload를 보고 필요한 경우에만 동작합니다.

## 다른 저장소에 적용

이 저장소 루트에서 실행하는 예시입니다.

```powershell
$Target = "..\my-project"

New-Item -Path "$Target\.agents\skills" -ItemType Directory -Force | Out-Null
New-Item -Path "$Target\.codex\hooks" -ItemType Directory -Force | Out-Null
New-Item -Path "$Target\.codex\templates" -ItemType Directory -Force | Out-Null

Copy-Item -Recurse -Force ".\.agents\skills\karpathy-guidelines" "$Target\.agents\skills\"
Copy-Item -Force ".\.codex\config.toml" "$Target\.codex\config.toml"
Copy-Item -Force ".\.codex\hooks.json" "$Target\.codex\hooks.json"
Copy-Item -Force ".\.codex\hooks\*.py" "$Target\.codex\hooks\"
Copy-Item -Force ".\.codex\templates\AGENTS.md" "$Target\.codex\templates\AGENTS.md"
```

대상 저장소에 기존 `.codex/config.toml`, `.codex/hooks.json`, `AGENTS.md`가 있으면 덮어쓰지 말고 필요한 항목만 병합하세요.

## 사용자 전역 설치

다른 컴퓨터에서 이 저장소를 연 뒤 Codex에게 아래처럼 요청하면 됩니다.

```text
README_for_codex.md를 읽고 이 skill과 hook을 사용자 전역으로 설치해 주세요.
```

## 확인

```powershell
$hookFiles = (Get-ChildItem -Path .codex\hooks -Filter *.py).FullName
@'
import sys
from pathlib import Path

for name in sys.argv[1:]:
    path = Path(name)
    compile(path.read_text(encoding="utf-8"), str(path), "exec")
'@ | python - $hookFiles
'{"hook_event_name":"SessionStart","source":"startup","cwd":"."}' | python .codex\hooks\karpathy_context.py
git diff --check
```

Codex에서 hook을 쓰려면 해당 저장소를 신뢰하고, 새 hook 또는 변경된 hook은 `/hooks`에서 승인해야 합니다.

## License

MIT
