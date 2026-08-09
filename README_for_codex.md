# Codex Global Install

이 문서는 Codex가 이 저장소를 열고 `$karpathy-guidelines` skill과 관련 hook을 사용자 전역으로 설치할 때 따른다.

## 전제

- 현재 작업 디렉터리는 이 저장소 루트다.
- PowerShell에서 실행한다.
- 소스 경로는 이 저장소 기준 상대경로만 사용한다.
- 대상 경로는 환경값으로 해석하고, 고정 절대경로를 하드코딩하지 않는다.
- 기존 사용자 설정은 보존하고 필요한 항목만 병합한다.

## PowerShell 실행 규칙

- 디렉터리는 `New-Item -Path <path> -ItemType Directory -Force`로 만든다. `New-Item -LiteralPath`에 의존하지 않는다.
- Python 명령에 `*.py`를 그대로 넘기지 않는다. 먼저 `Get-ChildItem`으로 파일 목록을 만든다.
- `$HOME` 같은 리터럴을 찾을 때는 작은따옴표나 `Select-String -SimpleMatch`를 쓴다.
- `foreach (...) { ... }` 결과는 변수에 담은 뒤 파이프한다.

## 설치 대상

- 사용자 skill 위치: Codex USER scope의 `.agents\skills`
- Codex home: `CODEX_HOME`이 있으면 그 값을 사용하고, 없으면 사용자 기본 Codex home을 사용한다.
- 전역 hook 스크립트: Codex home 아래 `hooks`
- 전역 AGENTS 템플릿: Codex home 아래 `templates`
- 전역 hook 설정: Codex home의 `hooks.json`

## 설치 절차

1. 사용자 skill 위치에 `.agents\skills\karpathy-guidelines`를 복사한다.
2. Codex home의 `hooks` 디렉터리에 아래 파일을 복사한다.

```text
.codex/hooks/ensure_agents.py
.codex/hooks/karpathy_context.py
.codex/hooks/normalize_text_line_endings.py
.codex/hooks/run_python_hook.ps1
```

3. Codex home의 `templates` 디렉터리에 `.codex\templates\AGENTS.md`를 복사한다.
4. Codex home의 `config.toml`에 `[features] hooks = false`가 명시되어 있으면 `true`로 바꾸고, 다른 설정은 보존한다.
5. Codex home의 `hooks.json`을 읽고, 없으면 새로 만든다.
6. 기존 hook 중 아래 script basename을 command에 포함하는 항목은 제거한다.

```text
ensure_agents.py
karpathy_context.py
normalize_text_line_endings.py
run_python_hook.ps1
```

7. Codex home의 `hooks.json`에 아래 전역 hook을 병합한다.

- `SessionStart` `startup`: `ensure_agents.py`
- `SessionStart` `startup|resume|clear|compact`: `karpathy_context.py`
- `PostCompact` `manual|auto`: `karpathy_context.py`
- `PostToolUse` `.*`: `normalize_text_line_endings.py`

각 hook의 `command`는 비-Windows용 Python 명령과 Codex home에 복사한 script의 해석된 경로를 사용한다. Windows용 `commandWindows`는 PowerShell 호출 연산자(`&`)로 전역 `run_python_hook.ps1`과 대상 Python script의 해석된 경로를 호출한다. 실행기는 Store 별칭을 제외하고 실제 Python을 동적으로 찾으므로 사용자명, 설치 경로, Python 버전을 하드코딩하지 않는다. 필요하면 `KARPATHY_PYTHON` 환경 변수로 `python.exe`를 지정한다. repo-local `.codex\hooks.json`은 명령 경로가 저장소 기준이므로 전역 `hooks.json`에 그대로 복사하지 않는다.

## 설치 후 검증

PowerShell에서 아래 내용을 확인한다.

```powershell
$hookFiles = (Get-ChildItem -Path .codex\hooks -Filter *.py).FullName
foreach ($hookFile in $hookFiles) {
    & .\.codex\hooks\run_python_hook.ps1 $hookFile -CompileOnly
}
'{"hook_event_name":"SessionStart","source":"startup","cwd":"."}' | & .\.codex\hooks\run_python_hook.ps1 .\.codex\hooks\karpathy_context.py
git diff --check
```

추가로 설치 대상의 hook script도 같은 cache 없는 `compile()` 검증으로 확인한다.

임시 Git 저장소를 만들고 전역 `ensure_agents.py`를 실행해 `AGENTS.md`가 생성되는지 확인한다. 이 저장소 자체에서는 루트 `AGENTS.md`가 생성되지 않아야 한다.

CSV 파일은 줄끝 정규화 hook의 대상이 아니어야 한다. quoted field 안의 LF가 보존되는지 간단한 샘플로 확인한다.

## 완료 보고

사용자에게 아래 항목만 간단히 보고한다.

- 설치된 skill 이름
- 병합된 hook 이벤트
- 검증 명령 결과
- Codex에서 `/hooks`로 새 전역 hook을 승인해야 한다는 점
