# 같은 Chrome 세션 제어

`ENABLE_CDP=true`로 실행한 컨테이너에서 사용한다. Patchright는 이미지 내부에 있으므로 `docker exec`를 사용하면 호스트에 추가 설치할 필요가 없다. 이름과 URL은 실제 작업에 맞게 고른다.

## 탭을 읽고 목표 페이지 열기

```bash
docker exec -i remote-chrome python3 - <<'PY'
from patchright.sync_api import sync_playwright
with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp('http://127.0.0.1:9222')
    context = browser.contexts[0]
    for index, page in enumerate(context.pages):
        print(index, page.title())
    page = context.new_page()
    page.goto('https://example.com', wait_until='domcontentloaded')
    page.bring_to_front()
PY
```

연결된 브라우저에 `browser.close()`를 호출하지 않는다. 작업 후 Patchright 연결만 끝내면 사용자 화면은 유지된다. `page.close()`도 사용자가 필요한 탭에는 호출하지 않는다. 기존 탭의 계정·작업이 필요할 때는 제목/도메인/화면을 제한적으로 확인해 그 탭을 선택한다. 탭 순서는 고정하지 않는다.

## 읽기와 조작

역할과 접근성 이름으로 요소를 선택한다. 민감한 내용이 있는 페이지 전체를 출력하는 대신 필요한 요소만 읽는다.

```python
page.get_by_role('button', name='Continue', exact=True).click()
print(page.get_by_role('heading').all_text_contents())
```

로그인 정보나 MFA를 사용자에게 입력받을 때는 해당 화면을 전면에 두고 입력을 기다린다. 완료 통지를 받으면 인증 후 화면을 다시 읽어 실제 계정과 상태를 확인한다. 메일함 등 관련 없는 탭의 내용을 수집하지 않는다. 스크린샷에 암호나 개인정보가 보이면 공개 산출물에 포함하지 않는다.

## 공동 작업과 한글 검증

사용자가 noVNC 또는 RustDesk에서 조작하는 동안 같은 탭에 입력·클릭을 보내지 않는다. 원격 클라이언트 화면 크기 변경 후에는 버튼/입력칸 위치를 다시 확인한다. X11 좌표로 입력한다면 클릭 뒤 포커스가 전달될 시간을 준다.

RustDesk를 통한 실제 한글 입력 검증은 클라이언트에서 `Ctrl+Space`, 영문 키 `gksrmf`, Space를 입력해 서버 Chrome 입력값에 `한글 `이 생겼는지 확인한다. 서버 안에서만 키를 보내는 시험은 입력기 자체의 시험이며 RustDesk 키 전달까지 검증한 것은 아니다. `xdotool type`은 뒤의 인자를 모두 텍스트로 소비하므로 이후 `key space`는 별도 명령으로 실행한다.

브라우저 CDP `fill()`로 한글 문자열을 직접 넣는 것은 한글 입력기 검증이 아니다. 새 시험 입력칸이나 사용자 작업과 분리된 탭을 사용하고, 검증 때문에 실제 작성 중인 내용을 지우지 않는다.
