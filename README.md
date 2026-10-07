# Chrome RustDesk Korean

Google Chrome, 한글 입력(Fcitx5), 암호 인증 noVNC, 선택형 RustDesk 직접 접속을 제공하는 단일 Docker 이미지입니다. 사람이 로그인하고 CDP 자동화가 같은 브라우저를 이어서 제어하는 작업에 사용할 수 있습니다. Compose는 필요하지 않습니다.

현재 지원 플랫폼은 **Linux x86-64(amd64)**입니다. 로그인 정보와 접속 암호는 이미지에 포함하지 않습니다.

## Claude Code·Codex 스킬 설치

같은 브라우저에서 사용자가 로그인하고 에이전트가 이어서 작업하는 방법을 `chrome-rustdesk` 스킬로 제공합니다. 스킬을 사용할 프로젝트 폴더에서 설치합니다.

```bash
npx --yes skills@1.7.1 add KentLee86/chrome-rustdesk-korean \
  --skill chrome-rustdesk --agent claude-code codex --copy --yes
```

Claude Code에서는 `/chrome-rustdesk`, Codex에서는 `$chrome-rustdesk`로 호출합니다. [설치 방식·저장소 구조·사용 예시](https://github.com/KentLee86/chrome-rustdesk-korean/blob/main/docs/agent-skill.md)를 참고하세요. 이 명령은 Vercel Labs의 공통 설치 도구를 사용하며 Node.js와 npm이 필요합니다.

## Docker Hub에서 실행

[Docker Hub 이미지](https://hub.docker.com/r/wslee407/chrome-rustdesk-korean)의 `0.1.0` 태그를 사용할 수 있습니다. `latest`도 같은 버전을 가리키며 이후 릴리스에서 바뀔 수 있습니다.

```bash
docker pull wslee407/chrome-rustdesk-korean:0.1.0
docker run -d --name remote-chrome --shm-size=1g --stop-timeout=20 \
  --cap-add=SYS_ADMIN \
  --security-opt seccomp=unconfined --security-opt apparmor=unconfined \
  -p 6085:6080 -p 21120:21118 \
  -v chrome-profile:/data/chrome-profile \
  -v remote-settings:/config \
  wslee407/chrome-rustdesk-korean:0.1.0
```

이 예시는 Chrome 프로필과 원격 접속 설정을 각각 Docker 볼륨에 보존합니다. 아래 저장·포트·RustDesk 선택 옵션은 공개 이미지에도 동일하게 적용됩니다. 직접 빌드하는 예시의 `chrome-rustdesk-korean:local`을 공개 이미지 이름으로 바꾸면 됩니다.

## 빌드와 실행

```bash
docker build -t chrome-rustdesk-korean:local .
docker run -d --name remote-chrome --shm-size=1g --stop-timeout=20 \
  --cap-add=SYS_ADMIN \
  --security-opt seccomp=unconfined --security-opt apparmor=unconfined \
  -p 6085:6080 -p 21120:21118 \
  chrome-rustdesk-korean:local
```

Chrome 샌드박스의 namespace 생성에 필요한 권한을 위 실행 명령으로 제공합니다. 호스트 정책에 따라 실행이 제한될 수 있습니다. 이 예시는 컨테이너 격리를 완화하므로 신뢰하는 LAN/VPN에서 사용하세요. noVNC의 전통 VNC 인증은 암호의 **앞 8글자만 사용**하며 HTTPS를 제공하지 않습니다. 인터넷 연결에는 TLS와 별도 인증을 적용한 역방향 프록시가 필요합니다.

- noVNC: `http://<Docker 호스트 주소>:6085/vnc.html?autoconnect=1&resize=scale`
- RustDesk: 원격 ID 입력란에 `<Docker 호스트 주소>:21120` 입력
- 한/영 전환: **Ctrl+Space**, 두벌식. 클라이언트 키 전달 방식에 따라 동작이 달라질 수 있습니다.

자동 생성한 암호는 다음 명령으로 본인 환경에서 확인합니다. 암호 자체는 시작 로그에 출력하지 않습니다.

```bash
docker exec remote-chrome cat /config/vnc-password.txt
docker exec remote-chrome cat /config/rustdesk/connection-password.txt
```

컨테이너를 재시작하면 쓰기 레이어의 설정은 남습니다. 삭제 후 다시 만들 때 유지하려면 다음 저장 옵션을 사용합니다.

## Chrome 로그인 정보 저장 선택

다음 옵션은 `docker run`의 이미지 이름 **앞**에 추가합니다.

| 방식 | 옵션 | 유지 범위 |
|---|---|---|
| 내 컴퓨터 폴더 | `--mount type=bind,src=/절대경로/chrome-profile,dst=/data/chrome-profile` | 컨테이너를 삭제해도 호스트 폴더에 유지 |
| Docker 볼륨 | `-v chrome-profile:/data/chrome-profile` | 컨테이너를 삭제해도 볼륨에 유지 |
| 임시 메모리 | `--tmpfs /data/chrome-profile:uid=1000,gid=1000,mode=0700` | 컨테이너 중지 시 삭제 |
| 지정 없음 | 추가 옵션 없음 | 컨테이너 재시작에는 유지, 삭제 시 삭제 |

호스트 폴더를 연결할 때는 미리 만들고 컨테이너 사용자 **UID/GID 1000:1000**이 읽고 쓸 수 있게 준비합니다. 폴더는 Docker가 실행되는 컴퓨터에 있어야 합니다. 동시에 실행하는 Chrome끼리 프로필을 공유하지 마세요. 서비스가 세션을 만료하면 저장 모드에서도 재로그인이 필요합니다.

```bash
mkdir -p "$PWD/chrome-profile"
# Linux에서 폴더 소유자가 UID 1000이 아니라면 해당 폴더만 권한 조정
# sudo chown 1000:1000 "$PWD/chrome-profile"
docker run -d --name remote-chrome --shm-size=1g --stop-timeout=20 \
  --cap-add=SYS_ADMIN \
  --security-opt seccomp=unconfined --security-opt apparmor=unconfined \
  -p 6085:6080 -p 21120:21118 \
  --mount "type=bind,src=$PWD/chrome-profile,dst=/data/chrome-profile" \
  chrome-rustdesk-korean:local
```

Chrome는 headless 환경에서 `--password-store=basic`을 사용합니다. 프로필에는 쿠키와 저장한 비밀번호 등 민감 정보가 있으므로 호스트 폴더와 백업을 공개하지 마세요.

## RustDesk 사용 및 설정 저장 선택

- 켜기: 기본값 또는 `-e ENABLE_RUSTDESK=true`
- 끄기: `-e ENABLE_RUSTDESK=false`, `-p ...:21118`도 생략
- RustDesk 설정만 유지: `-v rustdesk-settings:/config/rustdesk`
- noVNC 암호까지 모두 유지: `-v remote-settings:/config`
- RustDesk 설정만 임시: `--tmpfs /config/rustdesk:uid=1000,gid=1000,mode=0700`
- 전체 원격 접속 설정 임시: `--tmpfs /config:uid=1000,gid=1000,mode=0700`

Chrome 프로필 유지와 RustDesk 설정 유지는 독립적입니다. 저장 옵션이 없으면 컨테이너 삭제 때 설정이 사라집니다. tmpfs 설정에서는 재시작할 때도 새 암호가 생성됩니다. 외부에서 고정 암호를 제공했다면 같은 암호를 다시 사용합니다.

다음은 RustDesk를 끄고 Chrome 프로필과 원격 설정을 모두 임시로 사용하는 예시입니다.

```bash
docker run -d --name temporary-chrome --shm-size=1g --stop-timeout=20 \
  --cap-add=SYS_ADMIN \
  --security-opt seccomp=unconfined --security-opt apparmor=unconfined \
  -e ENABLE_RUSTDESK=false -p 6085:6080 \
  --tmpfs /data/chrome-profile:uid=1000,gid=1000,mode=0700 \
  --tmpfs /config:uid=1000,gid=1000,mode=0700 \
  chrome-rustdesk-korean:local
```

## 포트와 실행 옵션

외부 포트는 `-p <호스트 포트>:<내부 포트>`로 지정합니다. 컨테이너 내부 포트는 고정입니다. `EXPOSE`는 설명용이며 포트를 자동 공개하지 않습니다. RustDesk를 끄면 내부 RustDesk 서비스도 실행하지 않습니다.

| 내부 포트 | 용도 | 실행 예시 |
|---|---|---|
| `6080` | noVNC 웹 화면 | `-p 6085:6080` |
| `21118` | RustDesk 직접 TCP 연결 | `-p 21120:21118` |
| `9223` | CDP 자동화, 기본 꺼짐 | `-e ENABLE_CDP=true -p 127.0.0.1:9325:9223` |

CDP는 인증 없이 브라우저를 제어하는 인터페이스입니다. 필요할 때만 켜고 호스트 루프백으로 연결하세요. 자동화 도구는 `http://127.0.0.1:9325`에 연결합니다.

| 환경변수 | 기본값 | 설명 |
|---|---|---|
| `ENABLE_RUSTDESK` | `true` | `true` 또는 `false` |
| `ENABLE_CDP` | `false` | `true` 또는 `false` |
| `START_URL` | `about:blank` | Chrome 시작 주소 |
| `SCREEN_SIZE` | `1400x1000x24` | 가상 화면 크기, 창 초기 크기는 1400×1000 |
| `VNC_PASSWORD` | 자동 생성 | ASCII 8글자 이상, 앞 8글자로 인증 |
| `VNC_PASSWORD_FILE` | 없음 | 암호를 읽을 컨테이너 내 파일 경로, 환경변수 암호보다 우선 |
| `RUSTDESK_PASSWORD` | 자동 생성 | 12글자 이상, 지정 시 저장된 암호 갱신 |
| `RUSTDESK_PASSWORD_FILE` | 없음 | 암호 파일 경로, 환경변수 암호보다 우선 |

환경변수에 암호를 직접 넣으면 Docker inspect 등에 보일 수 있습니다. 파일 마운트 방식으로 제공할 수 있습니다. 파일은 UID 1000이 읽을 수 있어야 합니다.

```bash
# 기존 docker run 옵션에 추가하는 예시
--mount type=bind,src=/절대경로/vnc-secret,dst=/run/secrets/vnc,readonly \
-e VNC_PASSWORD_FILE=/run/secrets/vnc
```

## 이미지 파일로 이동

```bash
docker save chrome-rustdesk-korean:local | gzip > chrome-rustdesk-korean-amd64.tar.gz
# 다른 컴퓨터에서
gzip -dc chrome-rustdesk-korean-amd64.tar.gz | docker load
```

로그인한 컨테이너를 `docker commit`해서 공유하지 마세요. 배포할 이미지는 이 Dockerfile에서 새로 빌드합니다. 기본 이미지와 Chrome apt 패키지는 빌드 시점에 따라 갱신됩니다. RustDesk 1.4.7 패키지는 SHA-256 검증으로 고정하고 Patchright는 1.63.0으로 고정합니다.

## 검증

```bash
python3 tests/test-init.py
python3 tests/smoke.py chrome-rustdesk-korean:local
```

smoke 검증은 독립 컨테이너와 시험용 볼륨을 만들고 종료 시 삭제합니다. Chrome 한글/영문 조합, VNC 인증 필수, RustDesk 직접 TCP 포트, 프로필·암호의 컨테이너 재생성 후 유지, tmpfs 프로필의 중지 후 삭제, 호스트 폴더에 저장한 프로필의 재사용을 검사합니다. 시험용 쿠키만 생성하며 실제 계정 로그인이나 외부 메일 전송은 하지 않습니다.

## 라이선스와 출처

이 저장소의 스크립트와 문서는 MIT 라이선스입니다. 이미지에 설치되는 타사 프로그램은 각각의 라이선스를 따릅니다.

- [RustDesk 소스와 라이선스](https://github.com/rustdesk/rustdesk/tree/1.4.7): AGPL-3.0, 수정하지 않은 공식 릴리스 패키지 사용
- [Google Chrome](https://www.google.com/chrome/terms/): Google 약관 적용
- [Fcitx5](https://github.com/fcitx/fcitx5), [한글 입력 엔진](https://github.com/fcitx/fcitx5-hangul)
- [noVNC](https://github.com/novnc/noVNC), [x11vnc](https://github.com/LibVNC/x11vnc), [Patchright](https://github.com/Kaliiiiiiiiii-Vinyzu/patchright-python)

이 저장소는 Google·RustDesk의 공식 프로젝트가 아닙니다. 빌드 소스는 이 GitHub 저장소에, 이미지는 `wslee407/chrome-rustdesk-korean` Docker Hub 저장소에 공개합니다.
