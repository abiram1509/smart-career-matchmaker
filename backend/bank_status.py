"""Presentation metadata from stored questions; no assessment decisions or scoring."""
from collections import Counter

def summarize(rows):
    rows=list(rows)
    counts=Counter('tier1' if q['tier']==1 else 'tier3' if q['tier']==3 else 'tier2b' if q.get('phase')=='context' else 'tier2a' for q in rows)
    counts={name:counts[name] for name in ['tier1','tier2a','tier2b','tier3']}
    full=counts=={'tier1':15,'tier2a':5,'tier2b':5,'tier3':60} and not any(q.get('example') for q in rows)
    starter=bool(rows) and any(q.get('example') for q in rows)
    return {**counts,'total':len(rows),'kind':'authored' if full else 'starter' if starter else 'partial' if rows else 'empty'}

def notice(summary):
    label={'authored':'Full authored bank','starter':'Starter/example bank','partial':'Partial bank','empty':'No stored questions'}[summary['kind']]
    return f"{label}: {summary['total']} stored questions, including {summary['tier3']} Tier-3 candidates. Up to 15 eligible checks are served. Missing coverage is not counted as a pass. Quiz checks do not verify employment experience, credentials or clinical competence."
