"""Read local API settings without adding a dependency or exposing secrets."""
import os
from pathlib import Path

CONFIG_PATH=Path(__file__).resolve().parents[1]/'.env'

def load_environment(path=CONFIG_PATH):
    if not path.exists(): return
    for line in path.read_text(encoding='utf-8-sig').splitlines():
        line=line.strip()
        if not line or line.startswith('#') or '=' not in line: continue
        key,value=line.split('=',1)
        key=key.strip();value=value.strip()
        if key not in {'SITE_OPERATOR_NAME','SITE_PRIVACY_EMAIL','ONET_API_KEY','JOBS_API_URL','JOBS_API_KEY','JOBS_API_KEY_HEADER','JOBS_API_KEY_PREFIX','JOBS_CSV','JOBS_API_SEARCH_MODE'}: continue
        if len(value)>=2 and value[0]==value[-1] and value[0] in {'"',"'"}: value=value[1:-1]
        if value: os.environ.setdefault(key,value)
