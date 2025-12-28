import sys
import subprocess
from datetime import datetime
import os

LOG_DIR = os.path.join(os.path.dirname(__file__), 'logs')
os.makedirs(LOG_DIR, exist_ok=True)
TS = datetime.now().strftime('%Y%m%d_%H%M%S')
LOG_FILE = os.path.join(LOG_DIR, f'test_run_{TS}.log')
LATEST_LOG = os.path.join(LOG_DIR, 'test_run_latest.log')

def run_and_log(cmd):
    with open(LOG_FILE, 'a', encoding='utf-8') as f, open(LATEST_LOG, 'w', encoding='utf-8') as latest:
        f.write(f'\n$ {cmd}\n')
        latest.write(f'\n$ {cmd}\n')
        proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        for line in proc.stdout:
            line = line.decode(errors='replace')
            f.write(line)
            latest.write(line)
            sys.stdout.write(line)
        proc.wait()
        f.write(f'Exit code: {proc.returncode}\n')
        latest.write(f'Exit code: {proc.returncode}\n')
        return proc.returncode

if __name__ == '__main__':
    for cmd in sys.argv[1:]:
        run_and_log(cmd)
