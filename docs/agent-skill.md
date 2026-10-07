# Claude Code·Codex 공통 스킬

`chrome-rustdesk` 스킬은 이 이미지로 Chrome을 실행하고 사용자의 로그인과 에이전트의 브라우저 제어를 번갈아 진행하는 방법을 제공한다. Claude Code와 Codex에서 같은 Agent Skills 원문을 사용한다.

## 저장소 구성

```text
skills/chrome-rustdesk/
  SKILL.md
  agents/openai.yaml
  references/run.md
  references/browser.md
.agents/skills/chrome-rustdesk -> ../../skills/chrome-rustdesk
.claude/skills/chrome-rustdesk -> ../../skills/chrome-rustdesk
```

`skills/`가 배포 원본이다. `.agents/skills`와 `.claude/skills`는 이 저장소에서 작업하는 Codex와 Claude Code가 원본을 읽는 링크다. 설치받은 스킬도 참고 파일을 함께 가져가므로 이 저장소의 README나 로컬 경로에 의존하지 않는다.

스킬에는 Docker 이미지 이름과 실제 기능만 기록한다. 사용자의 IP, 로그인 정보, 접속 암호, 작업 폴더는 넣지 않는다. Docker 권한이나 외부 작업의 승인 범위는 실행 환경과 사용자 요청을 따른다.

## 공통 설치

Node.js와 npm이 있는 환경에서, 스킬을 사용할 프로젝트 폴더로 이동한 뒤 실행한다. [Vercel Labs skills CLI](https://github.com/vercel-labs/skills)는 제삼자 설치 도구이며 Claude Code와 Codex를 모두 지원한다. 아래는 검증한 CLI 버전이다.

```bash
npx --yes skills@1.7.1 add KentLee86/chrome-rustdesk-korean \
  --skill chrome-rustdesk --agent claude-code codex --copy --yes
```

프로젝트에 `.claude/skills/chrome-rustdesk`와 `.agents/skills/chrome-rustdesk`를 설치한다. `--copy`는 독립 복사 방식이다. 업데이트할 때 설치 도구의 안내에 따라 같은 소스를 다시 설치한다. 설치 결과를 프로젝트와 공유하려면 팀의 정책에 맞게 Git에 포함한다.

설치 전에 제공되는 스킬을 확인할 수 있다.

```bash
npx --yes skills@1.7.1 add KentLee86/chrome-rustdesk-korean --list
```

## 공식 경로에 직접 설치

공통 설치 도구를 사용하지 않을 때는 저장소를 clone하고 `skills/chrome-rustdesk` 폴더 전체를 다음 경로에 복사한다. 같은 이름의 기존 스킬이 있으면 덮어쓰기 전에 내용을 확인한다.

| 도구 | 프로젝트 설치 | 사용자 설치 |
|---|---|---|
| Claude Code | `<project>/.claude/skills/chrome-rustdesk/` | `~/.claude/skills/chrome-rustdesk/` |
| Codex | `<project>/.agents/skills/chrome-rustdesk/` | `~/.agents/skills/chrome-rustdesk/` |

Codex에서는 `$skill-installer`에 [GitHub 스킬 폴더](https://github.com/KentLee86/chrome-rustdesk-korean/tree/main/skills/chrome-rustdesk)를 설치해 달라고 요청하는 방법도 있다. 관리형 환경에서는 조직 정책이 설치나 실행을 제한할 수 있다.

## 호출 예시

Claude Code:

```text
/chrome-rustdesk 새 Chrome을 켜줘. 로그인 프로필은 내 폴더에 저장하고 RustDesk로 접속할게.
```

Codex:

```text
$chrome-rustdesk 임시 Chrome을 noVNC로 열어줘. 내가 로그인하면 같은 탭에서 이어서 작업해줘.
```

도구가 파일을 새로 읽지 않으면 세션을 재시작한다. Docker가 설치되고 접근 가능한 Linux amd64 호스트가 필요하다. 원격 화면을 열 때는 그 호스트에 접근할 수 있는 실제 주소가 필요하다.

## 검증과 유지관리

Agent Skills는 `name`, `description`이 있는 `SKILL.md`를 중심으로 공유한다. 제품별 전용 프런트매터 대신 공통 필드를 사용하고, Codex UI 정보만 `agents/openai.yaml`에 둔다. 스킬 지침은 자동 선택할 수 있으며 불필요한 도구 권한을 선언하지 않는다.

이번 배포에서 스킬 형식 검사, 잘못된 이름의 실패 대조군, 설치 도구의 발견, 임시 프로젝트의 양쪽 설치 경로와 참고 파일 전체 일치를 검증했다. Claude/Codex 모델이 자연어 요청에 따라 스킬을 선택하는 행동 시험은 별도다. 이미지 기능이 바뀌면 실행 참고 문서와 해당 Docker 검증을 함께 갱신한다.

근거:

- [Agent Skills 공개 규격](https://agentskills.io/specification)
- [Claude Code 공식 스킬 문서](https://code.claude.com/docs/en/skills)
- [Codex 공식 스킬 문서](https://learn.chatgpt.com/docs/build-skills)
- [Vercel Labs 설치 도구 문서](https://github.com/vercel-labs/skills)
