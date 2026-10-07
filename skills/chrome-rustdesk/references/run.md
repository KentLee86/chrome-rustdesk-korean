# 실행과 저장 옵션

이미지는 Linux amd64용이다. Docker context가 원격이면 bind 경로는 Docker 서버의 경로다. 실제 IP, 작업 폴더와 고유 이름은 현재 요청에 맞게 정한다. 아래 `remote-chrome`은 예시 이름이다.

## 기본 실행

```bash
docker pull wslee407/chrome-rustdesk-korean:0.1.0
docker run -d --name remote-chrome --shm-size=1g --stop-timeout=20 \
  --cap-add=SYS_ADMIN \
  --security-opt seccomp=unconfined --security-opt apparmor=unconfined \
  -e ENABLE_RUSTDESK=true -e ENABLE_CDP=true \
  -e START_URL=about:blank \
  -p 0.0.0.0::6080 -p 0.0.0.0::21118 -p 127.0.0.1::9223 \
  wslee407/chrome-rustdesk-korean:0.1.0
docker port remote-chrome
```

빈 호스트 포트는 Docker가 할당한다. 사용자가 포트를 지정하면 `-p 6085:6080`, `-p 21120:21118`, `-p 127.0.0.1:9325:9223`처럼 바꾼다. noVNC와 RustDesk는 원격 접속을 위해 외부 인터페이스에 바인딩하며 CDP는 루프백에만 둔다. RustDesk 없이 실행할 때는 `ENABLE_RUSTDESK=false`로 바꾸고 해당 매핑을 삭제한다. 자동화가 필요 없으면 `ENABLE_CDP`와 `9223` 매핑을 생략한다.

기본 예시는 컨테이너 삭제 시 프로필과 설정이 사라진다. `--restart unless-stopped`는 계속 유지할 서비스일 때 추가하고, 요청 없이 기본으로 켜지 않는다.

## 저장 위치 선택

이미지 이름 앞에 필요한 옵션만 추가한다. 한 경로에 여러 저장 방식을 동시에 지정하지 않는다.

| 저장 대상 | Docker 볼륨 유지 | 중지 시 삭제 |
|---|---|---|
| Chrome 프로필 | `-v remote-chrome-profile:/data/chrome-profile` | `--tmpfs /data/chrome-profile:uid=1000,gid=1000,mode=0700` |
| RustDesk 설정만 | `-v remote-chrome-rustdesk:/config/rustdesk` | `--tmpfs /config/rustdesk:uid=1000,gid=1000,mode=0700` |
| noVNC 암호 포함 전체 접속 설정 | `-v remote-chrome-settings:/config` | `--tmpfs /config:uid=1000,gid=1000,mode=0700` |

호스트 폴더 유지 예시:

```bash
mkdir -p "$PWD/profile" "$PWD/settings"
# 생성한 폴더에 UID/GID 1000:1000의 읽기·쓰기 권한이 있어야 한다.
--mount "type=bind,src=$PWD/profile,dst=/data/chrome-profile"
--mount "type=bind,src=$PWD/settings,dst=/config"
```

위 `--mount` 줄은 독립 명령이 아니라 `docker run`에 붙이는 옵션이다. 폴더 권한을 확인하고 필요한 경우 해당 폴더에만 조정한다. 기존 프로필을 임의로 `chown -R`하지 않는다. 동일 프로필을 동시에 두 Chrome에서 사용하지 않는다. 세션 만료 시 재로그인이 필요하다.

## 접속 암호

기본은 실행 시 생성이다. 값을 지정하려면 `VNC_PASSWORD` 또는 `RUSTDESK_PASSWORD` 환경변수, 또는 각각의 `_FILE` 환경변수로 암호 파일을 전달한다. 파일 방식이 있으면 그 파일을 우선한다. VNC는 ASCII 8글자 이상을 받지만 **앞 8글자만 인증에 사용**한다. RustDesk는 12글자 이상이다. 설정을 tmpfs로 두면 재시작 시 새 암호가 생성되며, 외부에서 지정한 암호는 그대로 적용한다.

```bash
docker exec remote-chrome cat /config/vnc-password.txt
docker exec remote-chrome cat /config/rustdesk/connection-password.txt
```

암호는 이 접속을 요청한 사용자에게만 전달한다. 이미 저장된 설정이 있는 컨테이너에 암호 환경변수를 다시 지정하면 암호가 교체된다.

## 준비 확인과 문제 진단

```bash
docker inspect --format '{{.State.Status}}' remote-chrome
docker port remote-chrome
docker logs --tail 40 remote-chrome
```

로그를 읽을 때 로그인 URL, 인증 정보나 민감한 페이지 내용을 그대로 공유하지 않는다. noVNC `vnc.html`의 HTTP 200은 페이지 제공만 확인한다. RustDesk TCP 연결도 서버 준비만 확인하므로 실제 인증·화면 연결과 구분해 보고한다. 실제 사용자에게 접속을 맡겼다면 그 결과는 사용자 확인 전까지 미확인으로 표시한다.

컨테이너 안에서 CDP와 RustDesk 준비를 확인하려면:

```bash
docker exec remote-chrome python3 -c "import socket; socket.create_connection(('127.0.0.1',9222),5).close(); socket.create_connection(('127.0.0.1',21118),5).close()"
```

비활성화한 서비스의 포트는 검사 대상에서 뺀다. 아직 초기화 중이면 짧게 재확인하고, 종료했거나 준비가 계속 실패하면 Chrome/RustDesk 로그를 읽는다.

이 실행 예시는 Chrome namespace 샌드박스를 위해 컨테이너 권한을 완화한다. 신뢰하는 LAN/VPN에서 사용하고, 인터넷 접속은 TLS와 별도 인증을 갖춘 프록시를 구성한 요청에서 다룬다. noVNC의 VNC 인증은 TLS를 대체하지 않는다.
