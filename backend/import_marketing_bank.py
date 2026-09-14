"""Strict Markdown adapter for the supplied Marketing bank; no assessment logic."""
import argparse
import copy
import hashlib
import json
import re
import sqlite3
from collections import Counter
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'question-banks'/'MARKETING_TRACK_QUESTION_BANK.md'
BANK=ROOT/'backend'/'question_bank.json'
DB=ROOT/'backend'/'data'/'career.sqlite3'
MANIFEST=ROOT/'question-banks'/'marketing_import_manifest.json'

def parse(source=SOURCE):
    text=source.read_text(encoding='utf-8-sig')
    tiers={}
    for name in ['1','2a','2b','3']:
        match=re.search(r'^## TIER '+name+r' —[^\n]*\n(.*?)(?=^## |\Z)',text,re.M|re.S)
        if not match: raise ValueError('Missing Tier '+name)
        tiers[name]=match.group(1)
    questions=[]
    for tier,size in [('1',15),('2a',5),('2b',5)]:
        rows=[]
        for line in tiers[tier].splitlines():
            if not re.match(r'^\|\s*\d+\s*\|',line): continue
            cells=[v.strip() for v in line.strip().strip('|').split('|')]
            if len(cells)!=(2 if tier=='2b' else 3): raise ValueError('Unexpected table shape')
            rows.append(cells)
        if [r[0] for r in rows]!=[str(n) for n in range(1,size+1)]: raise ValueError('Unexpected table count/order: '+tier)
        for cells in rows:
            number=int(cells[0])
            # Table row numbers are local to their tier, not global source IDs.
            q={'id':f'marketing_t{tier}_q{number:02d}','source_number':number,'source_tier':'Tier '+tier,
               'track':'marketing','skill':cells[1] if tier!='2b' else 'Adaptive / Project Context',
               'tier':1 if tier=='1' else 2,'prompt_text':cells[-1]}
            if tier=='1': q.update(type='self_rating',min=1,max=10)
            elif tier=='2a': q.update(type='project_count',phase='counts',counts=True,options=['0','1','2–3','4–5','6+'])
            else:
                q.update(phase='context',context=True,optional=number in (1,4))
                if number in (1,4): q['type']='project_note'
                elif number==5: q.update(type='self_rating',min=1,max=10)
                else: q.update(type='context_choice',options=['Mostly myself','Shared team contribution','Small contribution'] if number==2 else ['Barely used it','Used it for some parts','Used it heavily'])
            questions.append(q)
    pattern=r'^\*\*(Q\d+)\*\* — Skill: (.*?) \| Type: (.*?) \| Requires Tier-2 flag: (.*?)\n(.*?)(?=^\*\*Q\d+\*\*|\Z)'
    blocks=list(re.finditer(pattern,tiers['3'],re.M|re.S))
    if [m[1] for m in blocks]!=[f'Q{i}' for i in range(1,61)]: raise ValueError('Expected Q1–Q60 exactly')
    for match in blocks:
        identity,skill,kind,flag,body=match.groups()
        quoted=[line[2:] for line in body.splitlines() if line.startswith('> ')]
        if len(quoted)!=3: raise ValueError('Unexpected question block: '+identity)
        answer=re.fullmatch(r'\*\*Correct: ([ABCD])\*\*',quoted[2])
        options=re.fullmatch(r'A\. (.*?)  B\. (.*?)  C\. (.*?)  D\. (.*)',quoted[1])
        if not answer or not options: raise ValueError('Invalid options/answer: '+identity)
        if kind not in {'scenario_judgment','numerical_case','project_verification'}: raise ValueError('Unsupported type: '+kind)
        questions.append({'id':identity,'source_tier':'Tier 3','track':'marketing','skill':skill,'tier':3,
            'type':kind,'prompt_text':quoted[0],'options':list(options.groups()),'correct_option':'ABCD'.index(answer[1]),
            'requires_tier2_flag':flag,'verification_kind':'project' if kind=='project_verification' else 'skill'})
    flags={q['skill'] for q in questions if q.get('phase')=='counts'}
    if any(q['requires_tier2_flag'] not in flags for q in questions if q['tier']==3): raise ValueError('Unresolved eligibility flag')
    if len(questions)!=85 or len({q['id'] for q in questions})!=85: raise ValueError('Invalid question count/IDs')
    return questions

def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,ensure_ascii=False).encode('utf-8')).hexdigest()

def audit():
    from .adaptive_quiz import bank
    rows=bank(); result={}
    with sqlite3.connect(f'file:{DB.as_posix()}?mode=ro',uri=True) as db:
        for track in ['backend','frontend','data-ml','health-admin','legal-support','business-development','marketing','business-marketing','hr']:
            source=sorted([q for q in rows if q['track']==track],key=lambda q:q['id'])
            stored=sorted([json.loads(r[0]) for r in db.execute('SELECT payload FROM questions WHERE track=?',(track,))],key=lambda q:q['id'])
            counts=Counter('Tier 1' if q['tier']==1 else 'Tier 3' if q['tier']==3 else 'Tier 2b' if q.get('phase')=='context' else 'Tier 2a' for q in stored)
            result[track]={'engine':len(source),'database':len(stored),'identical':source==stored,
                           'tiers':{name:counts[name] for name in ['Tier 1','Tier 2a','Tier 2b','Tier 3']}}
    return result

def validate(questions):
    from . import adaptive_quiz as quiz
    from .domain import SKILLS
    old=quiz.bank();other=[q for q in old if q['track']!='marketing']
    if {q['id'] for q in other}&{q['id'] for q in questions}: raise ValueError('Question ID collision with another track')
    missing=sorted({q['skill'] for q in questions}-set(SKILLS))
    originals=quiz.SKILLS
    # Only prospective taxonomy metadata is patched; the production engine is untouched.
    quiz.SKILLS=[*SKILLS,*missing]
    try:
        flags=[q['skill'] for q in questions if q.get('phase')=='counts']
        for enabled in [[],*[[flag] for flag in flags],flags]:
            for correct in [True,False]:
                state={'track':'marketing','field':'marketing-sales','phase':'confidence','answers':{},'bank':other+questions,
                       'pending':[q for q in questions if q['tier']==1]}
                while state['phase']!='complete':
                    answers=[]
                    for q in state['pending']:
                        value=8 if q['type']=='self_rating' else '' if q['type']=='project_note' else (q['correct_option'] if correct else (q['correct_option']+1)%4) if q['tier']==3 else (2 if q['skill'] in enabled else 0) if q['type']=='project_count' else 0
                        answers.append({'question_id':q['id'],'value':value})
                    quiz.advance(state,answers)
                vector,evidence=quiz.score(state)
                assert len(state.get('verification',[]))<=15
                assert all(q['requires_tier2_flag'] in enabled for q in state.get('verification',[]))
                assert sum(e['assessed'] for e in evidence.values())==15
                if len(enabled)==5: assert len(state['verification'])==15
    finally: quiz.SKILLS=originals
    baselines={q['skill'] for q in questions if q['tier']==1}
    checks={q['skill'] for q in questions if q['tier']==3}
    return {'unknown_labels':missing,'checks_without_baselines':sorted(checks-baselines),
            'baselines_without_checks':sorted(baselines-checks),'other_tracks_hash':digest(other),
            'business_marketing_hash':digest([q for q in old if q['track']=='business-marketing'])}

def commit(questions,validation):
    # Taxonomy labels must be registered in configuration before the write phase.
    from .domain import SKILLS
    if any(q['skill'] not in SKILLS for q in questions): raise ValueError('Register exact Marketing labels before importing')
    old=json.loads(BANK.read_text(encoding='utf-8-sig'))
    other=[q for q in old if q['track']!='marketing']
    if digest(other)!=validation['other_tracks_hash']: raise ValueError('Question bank changed during validation')
    snapshot_dir=ROOT.parent.parent/'work'/'marketing-import-backup'
    snapshot_dir.mkdir(parents=True,exist_ok=True)
    backup=snapshot_dir/'question_bank.before.json'
    if not backup.exists(): backup.write_bytes(BANK.read_bytes())
    protected=['domain.py','adaptive_quiz.py','addon_api.py','main.py']
    hashes={name:hashlib.sha256((ROOT/'backend'/name).read_bytes()).hexdigest() for name in protected}
    merged=other+questions
    # Only Marketing rows are replaced in SQLite; no full-table migration is invoked.
    with sqlite3.connect(DB) as db:
        db.execute('BEGIN IMMEDIATE')
        before_other=db.execute("SELECT * FROM questions WHERE track!='marketing' ORDER BY id").fetchall()
        db.execute("DELETE FROM questions WHERE track='marketing'")
        db.executemany('INSERT INTO questions VALUES (?,?,?,?,?,?,?,?,?,?)',[(q['id'],q['track'],q['skill'],q['tier'],q['type'],q['prompt_text'],json.dumps(q.get('options')),q.get('correct_option'),q.get('requires_tier2_flag'),json.dumps(q,ensure_ascii=False)) for q in questions])
        assert before_other==db.execute("SELECT * FROM questions WHERE track!='marketing' ORDER BY id").fetchall()
        tmp=BANK.with_suffix('.marketing.tmp')
        tmp.write_text(json.dumps(merged,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        try:
            tmp.replace(BANK)
            db.commit()
        except BaseException:
            BANK.write_text(json.dumps(old,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
            raise
    for name,sha in hashes.items(): assert hashlib.sha256((ROOT/'backend'/name).read_bytes()).hexdigest()==sha
    report={**validation,'source':str(SOURCE.relative_to(ROOT)),'source_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
            'questions_imported':85,'tier3_candidates':60,'core_hashes':hashes,'loaded_audit':audit(),
            'notes':['Source Tier-3 IDs Q1–Q60 preserved verbatim. Tables supply local row numbers only; tier-scoped storage IDs generated and source_number retained.',
                     'Response controls follow the existing HR/Business Development adapter conventions.',
                     'Source labels remain distinct. Missing baselines and coverage are not invented.',
                     'Context IDs follow the existing imported-bank convention: retained in session, not connected to generic context-ai/context-focus or profile note saving.',
                     'All 60 correct answers are A in the source; preserved without reshuffling.',
                     'Frontend remains a 23-question starter bank; no authored Frontend source found in the project.']}
    MANIFEST.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    return report

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--apply',action='store_true');args=parser.parse_args()
    questions=parse();result=validate(questions)
    if args.apply: result=commit(questions,result)
    print(json.dumps(result,ensure_ascii=False,indent=2))
