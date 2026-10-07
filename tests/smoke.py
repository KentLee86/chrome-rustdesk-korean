"""Integration tests using isolated Docker containers and synthetic cookies."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import uuid
import urllib.request

image = sys.argv[1] if len(sys.argv) > 1 else 'chrome-rustdesk-korean:local'
prefix = 'chrome-smoke-' + uuid.uuid4().hex[:10]
names = []
volumes = [prefix + '-profile', prefix + '-config']
script = Path(__file__).with_name('desktop-check.py').read_text()


def docker(*args, **kwargs):
    return subprocess.run(['docker', *args], check=True, text=True, capture_output=True, **kwargs).stdout.strip()


def start(suffix, rustdesk, persisted=False, bind_profile=None):
    name = prefix + '-' + suffix
    names.append(name)
    args = ['run', '-d', '--name', name, '--shm-size=1g', '--cap-add=SYS_ADMIN',
            '--security-opt', 'seccomp=unconfined', '--security-opt', 'apparmor=unconfined',
            '-e', 'ENABLE_CDP=true', '-e', 'ENABLE_RUSTDESK=' + rustdesk,
            '-p', '127.0.0.1::6080', '-p', '127.0.0.1::9223', '-p', '127.0.0.1::21118']
    if persisted:
        args += ['-v', volumes[0] + ':/data/chrome-profile', '-v', volumes[1] + ':/config']
    elif bind_profile:
        args += ['--mount', 'type=bind,src=' + bind_profile + ',dst=/data/chrome-profile',
                 '--tmpfs', '/config:uid=1000,gid=1000,mode=0700']
    else:
        args += ['--tmpfs', '/data/chrome-profile:uid=1000,gid=1000,mode=0700',
                 '--tmpfs', '/config:uid=1000,gid=1000,mode=0700']
    docker(*args, image)
    for _ in range(60):
        ports = json.loads(docker('inspect', name))[0]['NetworkSettings']['Ports']
        port = ports['9223/tcp'][0]['HostPort']
        try:
            with urllib.request.urlopen('http://127.0.0.1:' + port + '/json/version', timeout=1):
                break
        except Exception:
            if docker('inspect', '-f', '{{.State.Running}}', name) != 'true':
                raise RuntimeError(docker('logs', name))
            time.sleep(1)
    else:
        raise RuntimeError('Chrome readiness timeout: ' + docker('logs', name))
    with urllib.request.urlopen('http://127.0.0.1:' + ports['6080/tcp'][0]['HostPort'] + '/vnc.html', timeout=5) as response:
        assert response.status == 200
    return name


def check(name, mode='desktop', negative=False):
    result = subprocess.run(['docker', 'exec', '-i', name, 'python3', '-', mode] + (['--negative'] if negative else []),
                            input=script, text=True, capture_output=True)
    if negative:
        assert result.returncode != 0 and 'AssertionError' in result.stderr, result
        print('PASS: disabled IME negative control fails')
    else:
        assert result.returncode == 0, result.stderr + result.stdout
        print(result.stdout.strip())


try:
    for volume in volumes:
        docker('volume', 'create', volume)
    first = start('persist', 'true', True)
    # RustDesk server must actually accept direct TCP connections.
    docker('exec', first, 'python3', '-c',
           "import socket,time\nfor _ in range(30):\n try:\n  socket.create_connection(('127.0.0.1',21118),1).close();break\n except OSError:time.sleep(1)\nelse:raise RuntimeError('RustDesk port closed')")
    check(first, 'no-cookie')
    check(first, negative=True)
    check(first)
    check(first, 'set-cookie')
    identity = docker('exec', first, 'sha256sum', '/config/rustdesk/connection-password.txt')
    docker('stop', '-t', '15', first)
    docker('rm', first)
    second = start('restored', 'true', True)
    check(second, 'has-cookie')
    assert docker('exec', second, 'sha256sum', '/config/rustdesk/connection-password.txt') == identity
    print('PASS: profile and RustDesk credentials persist across container recreation')
    third = start('temporary', 'false')
    check(third, 'no-cookie')
    docker('exec', third, 'python3', '-c',
           "import socket,pathlib\ns=socket.socket();s.settimeout(1)\nassert s.connect_ex(('127.0.0.1',21118)) != 0\nassert not pathlib.Path('/config/rustdesk/RustDesk.toml').exists()")
    check(third, 'set-cookie')
    docker('stop', '-t', '15', third)
    docker('start', third)
    for _ in range(60):
        try:
            check(third, 'no-cookie')
            break
        except AssertionError:
            time.sleep(1)
    else:
        raise RuntimeError('Temporary profile survived restart or Chrome failed to restart')
    print('PASS: temporary profile disappears on stop; RustDesk is disabled')
    default = prefix + '-defaults'
    names.append(default)
    docker('run', '-d', '--name', default, '--shm-size=1g', '--cap-add=SYS_ADMIN',
           '--security-opt', 'seccomp=unconfined', '--security-opt', 'apparmor=unconfined',
           '-e', 'ENABLE_RUSTDESK=false', image)
    docker('exec', default, 'python3', '-c',
           "import socket,time,subprocess\nfor _ in range(60):\n r=subprocess.run(['xdotool','search','--class','google-chrome'],capture_output=True)\n if r.returncode==0:break\n time.sleep(1)\nelse:raise RuntimeError('Chrome window not ready')\nfor port in (21118,9222,9223):\n s=socket.socket();s.settimeout(1);assert s.connect_ex(('127.0.0.1',port))!=0,port;s.close()")
    print('PASS: default CDP is disabled and Chrome runs without debug access')
    with tempfile.TemporaryDirectory(prefix='chrome-profile-smoke-') as folder:
        # Test fixtures only: allow UID 1000 to write when the host UID differs.
        Path(folder).chmod(0o777)
        host = start('host-folder', 'false', bind_profile=folder)
        check(host, 'set-cookie')
        docker('stop', '-t', '15', host)
        docker('rm', host)
        assert (Path(folder) / 'Local State').exists(), 'Host folder was not used'
        host2 = start('host-restored', 'false', bind_profile=folder)
        check(host2, 'has-cookie')
        docker('stop', '-t', '15', host2)
        docker('rm', host2)
        print('PASS: host-folder profile survives container recreation')
finally:
    for name in names:
        subprocess.run(['docker', 'rm', '-f', name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for volume in volumes:
        subprocess.run(['docker', 'volume', 'rm', volume], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
