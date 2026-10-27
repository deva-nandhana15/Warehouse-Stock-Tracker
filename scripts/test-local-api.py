"""Run Newman against a temporary local Flask process; no Docker substitution claim."""
import os
from pathlib import Path
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request

root = Path(__file__).resolve().parents[1]
with socket.socket() as sock:
    sock.bind(('127.0.0.1', 0))
    port = sock.getsockname()[1]
env = dict(os.environ, PORT=str(port))
with (root / 'reports' / 'local-api.log').open('w') as log:
    process = subprocess.Popen([sys.executable, 'app/app.py'], cwd=root, env=env,
                               stdout=log, stderr=log)
    try:
        for _ in range(30):
            if process.poll() is not None:
                raise RuntimeError('Flask exited; see reports/local-api.log')
            try:
                with urllib.request.urlopen(f'http://127.0.0.1:{port}/health', timeout=1):
                    break
            except (urllib.error.URLError, TimeoutError):
                time.sleep(0.2)
        else:
            raise RuntimeError('API did not become healthy')
        result = subprocess.run([
            'node', 'node_modules/newman/bin/newman.js', 'run', 'postman/collection.json',
            '--env-var', f'baseUrl=http://127.0.0.1:{port}', '--reporters', 'cli,junit',
            '--reporter-junit-export', 'reports/newman-local.xml',
        ], cwd=root, check=False)
        sys.exit(result.returncode)
    finally:
        process.terminate()
        process.wait(timeout=5)
