"""Portable Docker smoke + Newman checks, including a TLS DinD engine."""
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import urllib.error
import urllib.request

image = sys.argv[1]
root = Path(__file__).resolve().parents[1]
host = os.environ.get('DOCKER_TEST_HOST', '127.0.0.1')
publish_ip = os.environ.get('DOCKER_PUBLISH_IP', '127.0.0.1')
version = os.environ.get('COMMIT_SHA', 'ci')
container = None


def command(*args):
    return subprocess.check_output(args, text=True).strip()


def request(url, accept=None):
    headers = {'Accept': accept} if accept else {}
    with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=5) as response:
        return response.read()


try:
    container = command('docker', 'run', '-d', '--rm', '-p', f'{publish_ip}::5000',
                        '-e', f'APP_VERSION={version}', image)
    port = command('docker', 'port', container, '5000/tcp').splitlines()[0].rsplit(':', 1)[1]
    base = f'http://{host}:{port}'
    for _ in range(45):
        try:
            assert json.loads(request(base + '/health'))['status'] == 'ok'
            break
        except (urllib.error.URLError, TimeoutError):
            time.sleep(1)
    else:
        raise RuntimeError('Container health check timed out')
    assert command('docker', 'exec', container, 'id', '-u') == '10001'
    assert b'id="inventory-body"' in request(base, 'text/html')
    assert json.loads(request(base + '/api'))['version'] == version
    for asset in ['/static/styles.css', '/static/app.js']:
        assert request(base + asset)
    result = subprocess.run(['node', 'node_modules/newman/bin/newman.js', 'run',
                             'postman/collection.json', '--env-var', f'baseUrl={base}',
                             '--reporters', 'cli,junit', '--reporter-junit-export',
                             'reports/newman.xml'], cwd=root, check=False)
    sys.exit(result.returncode)
finally:
    if container:
        subprocess.run(['docker', 'stop', container], check=True, stdout=subprocess.DEVNULL)
