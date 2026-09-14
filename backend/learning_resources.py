"""Curated link-out resources; empty or missing entries are valid."""
import json
from pathlib import Path

def resources():
 try:raw=json.loads(Path(__file__).with_name('resources.json').read_text(encoding='utf-8-sig'))
 except (OSError,ValueError):return {}
 if not isinstance(raw,dict):return {}
 return {skill:[r for r in entries[:2] if isinstance(r,dict) and r.get('type') in {'video','course','doc'} and isinstance(r.get('url'),str) and r['url'].startswith(('https://','http://')) and r.get('title')] for skill,entries in raw.items() if isinstance(entries,list)}
