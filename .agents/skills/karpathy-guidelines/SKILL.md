---
name: karpathy-guidelines
description: Coding behavior guidelines for Codex. Use when writing, reviewing, debugging, or refactoring code; apply think-before-coding, simplicity-first, surgical changes, and goal-driven verification to avoid hidden assumptions, overengineering, unrelated edits, and unverified work.
---

# Karpathy Guidelines

LLM 코딩 작업에서 자주 생기는 실패 패턴을 줄이기 위한 Codex 행동 지침이다. 단순 오타 수정이나 명백한 한 줄 변경에는 판단해서 축소 적용한다.

## 1. 먼저 생각하기

- 가정과 불확실성을 드러낸다.
- 해석이 여러 개면 조용히 하나를 고르지 않는다.
- 더 단순한 접근이 있으면 제안한다.
- 이해하지 못한 부분은 멈추고 무엇이 불명확한지 말한다.

## 2. 단순함 우선

- 요청받지 않은 기능을 추가하지 않는다.
- 한 번만 쓰는 코드를 위해 추상화하지 않는다.
- 요구되지 않은 설정 가능성, 범용화, 방어 코드를 늘리지 않는다.
- 숙련된 엔지니어가 "과하다"고 볼 코드라면 줄인다.
- 명확한 요청은 별도 계획 문서나 승인 단계 없이 바로 수행한다.
- 사용자가 명시하지 않으면 계획/명세 문서, 새 테스트 파일, worktree, subagent를 생성하지 않는다.
- 배포용 `README.md`에는 내부 작업 범위, 제외한 원본/산출물, Git에 올리지 않는 파일 목록 같은 AI용 설명을 길게 쓰지 않는다. 그런 맥락은 필요하면 AI가 읽는 내부 `.md`에만 둔다.
- 새 코드에는 불필요한 주석, 모듈 docstring, 함수 docstring을 넣지 않는다.
- `#!/usr/bin/env python3` 같은 shebang은 실행 파일로 직접 호출해야 할 때만 넣는다.
- `from __future__ import annotations`는 현재 지원 Python 버전이나 실제 타입 평가 문제 때문에 필요할 때만 넣는다.
- 새로 만드는 텍스트 파일의 개행문자는 CRLF를 사용하되, 기존 파일을 수정하는 경우 기존 개행문자를 따른다.

## 3. 외과적 변경

- 사용자 요청과 직접 연결되는 파일과 줄만 바꾼다.
- 인접 코드, 주석, 포맷을 취향으로 개선하지 않는다.
- 기존 스타일을 따른다.
- 내가 만든 미사용 import, 변수, 함수, 생성물만 정리한다.
- 기존부터 있던 죽은 코드는 요청받지 않았다면 언급만 한다.

## 4. 검증까지 실행

- 시작 전에 성공 기준과 검증 방법을 정한다.
- 버그 수정은 가장 작은 진단 명령으로 증상을 재현하고 원인을 확인한 뒤 고친다.
- 기존 검증 수단이 있으면 변경 전후 결과를 비교하되, 검증만을 위해 새 테스트 파일을 자동 생성하지 않는다.
- 완료라고 말하기 전에 실제 명령을 실행하고 결과를 확인한다.
- 작은 의미 단위 작업이 완료되고 검증되면 자율적으로 커밋한다.
- 커밋 전 `git status --short`, 변경 범위, 검증 결과를 확인한다.
- 관련 없는 사용자 변경은 커밋에 섞지 않는다.
- 검증 실패, git 작업 진행 중, 변경 목적 불명확 상태에서는 커밋하지 않는다.
- 커밋 메시지는 의미 있는 영어로 작성한다.

## 5. Windows와 UTF-8

- 기본 셸은 Windows PowerShell로 본다.
- Python 명령은 Microsoft Store 실행 별칭을 제외하고 실제 인터프리터 경로를 먼저 해석한다. 사용자명이나 Python 버전이 들어간 절대경로를 지침에 하드코딩하지 않는다.
- 아래 PowerShell 예시의 `$Python`은 이 기준으로 미리 해석한 실행 파일 경로다.
- 문서, 예시, 설정, 스크립트에 파일시스템 경로를 적을 때는 상대경로를 사용한다.
- Bash heredoc `python <<'PY'`를 쓰지 않는다.
- 인라인 Python은 here-string을 사용한다.

```powershell
@'
print("hello")
'@ | & $Python -X utf8 -
```

- PowerShell `foreach (...) { ... }` 바로 뒤에 파이프를 붙이지 않는다. 결과를 변수에 담거나 식을 감싼다.
- 디렉터리 생성 예시는 `New-Item -Path ... -ItemType Directory -Force`를 사용하고, `New-Item -LiteralPath`에 의존하지 않는다.
- Python 명령에 `*.py`를 그대로 넘기지 않는다. 먼저 PowerShell에서 파일 목록을 만든다.
- Python 문법 검증만 필요하면 `py_compile` 대신 cache 없는 `compile()` 검증을 사용한다.
- `$HOME` 같은 리터럴 검색은 작은따옴표나 fixed-string 검색을 사용한다.
- Python 텍스트 입출력은 `encoding="utf-8"`을 명시한다.
- CSV 입력은 BOM 가능성을 고려해 `encoding="utf-8-sig"`로 읽는다.
- CSV 출력은 `encoding="utf-8"`, `newline=""`, `quoting=csv.QUOTE_ALL`을 사용한다.
- CSV 내부 줄바꿈은 대상 import/export 포맷에 맞춰 정규화한다. 표시 줄바꿈은 대상 엔진의 제어코드 규칙을 따른다.
- 사용자 환경의 `PYTHONUTF8=1`, `PYTHONIOENCODING=utf-8`은 의도된 기본값으로 취급한다.
- 일본어, 한글, 특수문자를 출력하는 임시 분석 명령은 UTF-8 출력 환경을 보장한다.
- `.bat` 파일은 필수 명령만 상대 경로로 쓰고 마지막 명령은 `pause`로 둔다.
- Python 또는 한국어 텍스트를 다루는 `.bat` 파일은 `chcp 65001`, `PYTHONUTF8=1`, `PYTHONIOENCODING=utf-8`만 포함한다.
- 전역 `PYTHONHOME` 또는 `PYTHONPATH`는 프로젝트가 요구하지 않는 한 설정하지 않는다.
