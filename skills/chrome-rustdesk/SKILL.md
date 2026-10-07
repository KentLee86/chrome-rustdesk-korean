---
name: chrome-rustdesk
description: "Run the chrome-rustdesk-korean Docker image for a shared Chrome session with human login, Korean input, noVNC or RustDesk access, selectable profile persistence, and CDP automation. Use for launching or operating this image, not arbitrary remote desktops or RustDesk relay servers."
license: MIT
---

# Chrome RustDesk

사용자와 같은 Chrome 화면을 보며 작업할 때 사용한다. 공개 이미지:
`wslee407/chrome-rustdesk-korean:0.1.0`.
셸, Docker CLI와 Linux amd64 Docker 호스트 접근이 필요하다. Claude Code와 Codex에서 사용하며 브라우저 자동화 코드는 컨테이너 안에서 실행한다.

## 실행 계획

- 기존 대화에서 정한 컨테이너, 포트, 접속 방식, 프로필 저장 선택을 따른다. 필요한 선택이 이미 있으면 다시 묻지 않는다.
- 새 세션은 새 프로필로 시작한다. 기존 로그인 프로필은 사용자가 지정한 경우에 연결한다. 로그인 유지 요청이면 별도 이름의 Docker 볼륨 또는 지정한 호스트 폴더를 사용하고, 임시 요청이면 tmpfs를 사용한다.
- noVNC는 모든 실행에서 제공한다. RustDesk는 `ENABLE_RUSTDESK=true/false`로 선택한다. RustDesk를 끌 때는 포트 `21118` 매핑도 생략한다. Chrome 프로필과 RustDesk 설정의 저장 방식은 독립적이다.
- 함께 브라우저를 조작할 때만 `ENABLE_CDP=true`를 지정하고 `9223`은 호스트 루프백에만 매핑한다. CDP는 인증 없이 브라우저를 제어할 수 있다.
- 생성과 접속 검증에는 [references/run.md](references/run.md)를 읽는다. 사용자별 IP나 폴더, 접속 암호를 이 스킬에 고정하지 않는다.

## 검증과 접속 안내

1. `docker version`으로 서버 접근 가능 여부와 Docker context를 확인한다. 이 이미지는 Linux amd64용이다. Docker가 다른 컴퓨터에서 실행된다면 bind 폴더도 그 컴퓨터의 경로다.
2. 이미지를 pull하고 고유한 컨테이너 이름으로 실행한다. 같은 이름의 컨테이너가 있으면 먼저 상태를 읽고, 요청 범위에서 재사용하거나 새 이름을 고른다. 기존 컨테이너나 프로필을 임의로 삭제하지 않는다.
3. `docker inspect`, `docker port`, 필요하면 `docker logs`로 실행 상태를 확인한다. 프로세스가 종료됐으면 그 오류부터 해결한다. 열린 TCP 포트만으로 실제 화면 연결 성공을 주장하지 않는다.
4. 확인된 Docker 호스트 주소와 실제 매핑 포트로 접속 정보를 만든다. 원격 사용자에게 `0.0.0.0`, 컨테이너 bridge IP, 자기 컴퓨터를 가리키는 `localhost`를 안내하지 않는다. 환경에 등록된 접속용 호스트 주소를 우선하고, 주소를 확인할 수 없으면 물어본다.
5. noVNC는 `http://<host>:<port>/vnc.html?autoconnect=1&resize=scale`, RustDesk는 원격 ID 입력란에 `<host>:<port>`를 넣는다. noVNC 암호는 `/config/vnc-password.txt`의 앞 8글자, RustDesk 암호는 `/config/rustdesk/connection-password.txt`다. 접속 안내에 필요한 암호만 사용자에게 전달하고 일반 로그나 저장소에는 넣지 않는다.
6. 한/영 전환은 `Ctrl+Space`로 안내한다. 클라이언트마다 키 전달이 다르므로 오른쪽 Alt 지원을 보장하지 않는다.

## 사용자와 브라우저를 번갈아 조작

- 로그인·MFA 등 사용자 입력이 필요하면 해당 화면을 전면에 열고 사용자 입력을 기다린다. 사용자가 입력하는 동안 같은 탭을 자동으로 조작하지 않는다.
- 사용자가 완료했다고 하면 현재 화면과 인증 상태를 다시 읽는다. 로그인된 계정이 여러 개면 탭 제목만으로 같은 계정이라고 판단하지 않는다.
- CDP 자동화 방법은 [references/browser.md](references/browser.md)를 읽는다. 컨테이너 내부에 Patchright가 설치되어 있으므로 호스트에 별도 패키지를 설치할 필요가 없다.
- 메일 발송, 구매, 설정 변경, 외부 게시 같은 실제 작업은 사용자가 요청한 범위에서 수행한다. 브라우저 접속 권한 자체를 모든 외부 작업의 승인으로 해석하지 않는다.

## 종료와 유지

접속할 수 있게 해달라는 요청이면 대상 컨테이너를 켜두고 상태를 알린다. 시험용 클라이언트만 만든 경우 그 클라이언트는 정리한다. 중지할 때는 `docker stop -t 20 <name>`으로 Chrome이 쿠키를 저장할 시간을 준다. 컨테이너·볼륨·호스트 폴더 삭제는 각각의 영향과 사용자 요청 범위를 확인한다.

쿠키·비밀번호·방문 기록이 있는 프로필이나 설정은 공개하지 않는다. 로그인한 컨테이너를 `docker commit`해서 배포하지 않는다.
