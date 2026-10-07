FROM debian:bookworm-slim

ARG RUSTDESK_VERSION=1.4.7
ARG RUSTDESK_SHA256=12f61bb5ceb10a708089903357bd1f98dcb618bd0ea56ec568aaf1713a38070a
ARG PATCHRIGHT_VERSION=1.63.0
ENV DEBIAN_FRONTEND=noninteractive LANG=ko_KR.UTF-8 TZ=Asia/Seoul
RUN test "$(dpkg --print-architecture)" = amd64 \
 && apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates curl gnupg locales tzdata \
    xvfb fluxbox x11vnc novnc websockify socat \
    fonts-noto-cjk fonts-noto-color-emoji python3 python3-venv procps \
    dbus-x11 fcitx5 fcitx5-hangul fcitx5-frontend-gtk3 fcitx5-frontend-gtk2 \
    x11-utils x11-xserver-utils xdotool \
    libayatana-appindicator3-1 libpulse0 libgstreamer1.0-0 \
    libgstreamer-plugins-base1.0-0 libxdo3 libegl1 libgles2 \
 && sed -i 's/# ko_KR.UTF-8/ko_KR.UTF-8/' /etc/locale.gen && locale-gen \
 && curl -fsSL https://dl.google.com/linux/linux_signing_key.pub | gpg --dearmor -o /usr/share/keyrings/google.gpg \
 && echo 'deb [arch=amd64 signed-by=/usr/share/keyrings/google.gpg] https://dl.google.com/linux/chrome/deb/ stable main' > /etc/apt/sources.list.d/google.list \
 && curl -fL --retry 3 "https://github.com/rustdesk/rustdesk/releases/download/${RUSTDESK_VERSION}/rustdesk-${RUSTDESK_VERSION}-x86_64.deb" -o /tmp/rustdesk.deb \
 && echo "${RUSTDESK_SHA256}  /tmp/rustdesk.deb" | sha256sum -c - \
 && apt-get update && apt-get install -y --no-install-recommends google-chrome-stable /tmp/rustdesk.deb \
 && rm -rf /var/lib/apt/lists/* /tmp/rustdesk.deb

RUN python3 -m venv /opt/venv \
 && /opt/venv/bin/pip install --no-cache-dir "patchright==${PATCHRIGHT_VERSION}" \
 && rm -f /usr/share/dbus-1/services/org.fcitx.Fcitx5.service
ENV PATH=/opt/venv/bin:$PATH DISPLAY=:99 GTK_IM_MODULE=fcitx QT_IM_MODULE=fcitx XMODIFIERS=@im=fcitx
RUN useradd -m -u 1000 -s /bin/bash app \
 && mkdir -p /tmp/.X11-unix /data/chrome-profile /config /run/remote-chrome /home/app/.config \
 && chmod 1777 /tmp/.X11-unix \
 && ln -s /config/rustdesk /home/app/.config/rustdesk \
 && chown -R app:app /data /config /run/remote-chrome /home/app
COPY config/fcitx5/ /etc/remote-chrome/fcitx5/
COPY init-runtime.py /usr/local/bin/init-runtime
COPY start-desktop.sh /usr/local/bin/start-desktop
COPY entrypoint.sh /usr/local/bin/entrypoint
RUN chmod 755 /usr/local/bin/init-runtime /usr/local/bin/start-desktop /usr/local/bin/entrypoint
LABEL org.opencontainers.image.title="Chrome RustDesk Korean" \
      org.opencontainers.image.description="Google Chrome desktop with optional RustDesk, authenticated noVNC and Korean input" \
      org.opencontainers.image.source="https://github.com/KentLee86/chrome-rustdesk-korean"
USER app
WORKDIR /home/app
EXPOSE 6080 21118 9223
ENTRYPOINT ["/usr/local/bin/entrypoint"]
