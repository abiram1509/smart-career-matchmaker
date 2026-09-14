"""Content-only Frontend Markdown import. Run without --apply to validate first."""
import argparse
import hashlib
import json
import re
import sqlite3
from .import_marketing_bank import ROOT, BANK, DB, digest, audit

SOURCE=ROOT/'question-banks'/'FRONTEND_TRACK_QUESTION_BANK.md'

def namespaced_id(track, source_id):
    """Future imports must namespace bare source IDs, leaving existing banks alone."""
    prefix='FE' if track=='frontend' else track.upper()
    return f'{prefix}-{source_id}'

def parse(source=SOURCE):
    text=source.read_text(encoding='utf-8-sig')
    tiers={}
    for tier in ['1','2a','2b','3']:
        match=re.search(r'^## TIER '+tier+r' —[^\n]*\n(.*?)(?=^## |\Z)',text,re.M|re.S)
        if not match: raise ValueError('Missing tier '+tier)
        tiers[tier]=match[1]
    questions=[]
    for tier,size in [('1',15),('2a',5),('2b',5)]:
        rows=[[cell.strip() for cell in line.strip('|').split('|')] for line in tiers[tier].splitlines() if re.match(r'^\|\s*\d+\s*\|',line)]
        if [r[0] for r in rows]!=[str(i) for i in range(1,size+1)] or any(len(r)!=(2 if tier=='2b' else 3) for r in rows):
            raise ValueError('Invalid table '+tier)
        for cells in rows:
            n=int(cells[0])
            q={'id':f'frontend_t{tier}_q{n:02d}','source_number':n,'source_tier':'Tier '+tier,
               'track':'frontend','skill':cells[1] if tier!='2b' else 'Adaptive / Project Context',
               'tier':1 if tier=='1' else 2,'prompt_text':cells[-1]}
            if tier=='1': q.update(type='self_rating',min=1,max=10)
            elif tier=='2a': q.update(type='project_count',phase='counts',counts=True,options=['0','1','2–3','4–5','6+'])
            else:
                q.update(phase='context',context=True,optional=n in (1,4))
                if n in (1,4): q['type']='project_note'
                elif n==5: q.update(type='self_rating',min=1,max=10)
                else: q.update(type='context_choice',options=['Mostly myself','Shared team contribution','Small contribution'] if n==2 else ['Barely used it','Used it for some parts','Used it heavily'])
            questions.append(q)
    pattern=r'^\*\*(Q\d+)\*\* — Skill: (.*?) \| Type: (.*?) \| Requires Tier-2 flag: (.*?)\n(.*?)(?=^\*\*Q\d+\*\*|\Z)'
    blocks=list(re.finditer(pattern,tiers['3'],re.M|re.S))
    if len(blocks)!=60 or {m[1] for m in blocks}!={f'Q{i}' for i in range(1,61)}: raise ValueError('Expected 60 unique candidates')
    for match in blocks:
        identity,skill,kind,flag,body=match.groups()
        quoted=[line[2:] if line.startswith('> ') else '' for line in body.splitlines() if line.startswith('>')]
        answer=re.fullmatch(r'\*\*Correct: ([ABCD])\*\*',quoted[-1])
        options=re.fullmatch(r'A\. (.*?)  B\. (.*?)  C\. (.*?)  D\. (.*)',quoted[-2])
        if not answer or not options or not quoted[:-2]: raise ValueError('Invalid block '+identity)
        if kind not in {'scenario_judgment','code_output_prediction','project_verification'}: raise ValueError('Unsupported type '+kind)
        questions.append({'id':namespaced_id('frontend',identity),'source_id':identity,'source_tier':'Tier 3',
            'track':'frontend','tier':3,'skill':skill,'type':kind,'prompt_text':'\n'.join(quoted[:-2]),
            'options':list(options.groups()),'correct_option':'ABCD'.index(answer[1]),'requires_tier2_flag':flag,
            'verification_kind':'project' if skill.startswith('Project-Informed ') or kind=='project_verification' else 'skill'})
    flags={q['skill'] for q in questions if q.get('phase')=='counts'}
    if any(q['requires_tier2_flag'] not in flags for q in questions if q['tier']==3): raise ValueError('Unresolved flag')
    return questions

def validate(questions):
    from . import adaptive_quiz as quiz
    from .domain import SKILLS
    old=quiz.bank();other=[q for q in old if q['track']!='frontend']
    if {q['id'] for q in other}&{q['id'] for q in questions}: raise ValueError('ID collision')
    missing=sorted({q['skill'] for q in questions}-set(SKILLS))
    if missing: raise ValueError('Register exact source labels in configuration: '+repr(missing))
    flags=[q['skill'] for q in questions if q.get('phase')=='counts']
    for enabled in [[],*[[flag] for flag in flags],flags]:
        for correct in [True,False]:
            state={'track':'frontend','field':'tech','phase':'confidence','answers':{},'bank':questions,'pending':[q for q in questions if q['tier']==1]}
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
    baselines={q['skill'] for q in questions if q['tier']==1};checks={q['skill'] for q in questions if q['tier']==3}
    return {'other_tracks_hash':digest(other),'checks_without_baselines':sorted(checks-baselines),'baselines_without_checks':sorted(baselines-checks)}

def commit(questions,validation):
    old=json.loads(BANK.read_text(encoding='utf-8-sig'));other=[q for q in old if q['track']!='frontend']
    if digest(other)!=validation['other_tracks_hash']: raise ValueError('Bank changed during validation')
    backup=ROOT.parent.parent/'work'/'frontend-import-backup';backup.mkdir(parents=True,exist_ok=True)
    if not (backup/'question_bank.before.json').exists(): (backup/'question_bank.before.json').write_bytes(BANK.read_bytes())
    with sqlite3.connect(DB) as db:
        db.execute('BEGIN IMMEDIATE')
        before=db.execute("SELECT * FROM questions WHERE track!='frontend' ORDER BY id").fetchall()
        db.execute("DELETE FROM questions WHERE track='frontend'")
        db.executemany('INSERT INTO questions VALUES (?,?,?,?,?,?,?,?,?,?)',[(q['id'],q['track'],q['skill'],q['tier'],q['type'],q['prompt_text'],json.dumps(q.get('options')),q.get('correct_option'),q.get('requires_tier2_flag'),json.dumps(q,ensure_ascii=False)) for q in questions])
        assert before==db.execute("SELECT * FROM questions WHERE track!='frontend' ORDER BY id").fetchall()
        tmp=BANK.with_suffix('.frontend.tmp');tmp.write_text(json.dumps(other+questions,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        try: tmp.replace(BANK);db.commit()
        except BaseException: BANK.write_text(json.dumps(old,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');raise
    report={**validation,'source_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),'questions_imported':len(questions),'loaded_audit':audit(),
        'notes':['Approved FE-Q1 through FE-Q60 storage IDs; source_id retains original Q labels. Source order retained.',
                 'Existing response controls used for tables without explicit options. Context integration limitation unchanged: context answers stay in sessions; generic routing/profile-note prefixes are not renamed.',
                 'Project-informed example triggers and code blocks retained in prompt text. No baselines or question content invented.']}
    (ROOT/'question-banks'/'frontend_import_manifest.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    return report

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--apply',action='store_true');args=parser.parse_args()
    questions=parse();report=validate(questions)
    if args.apply: report=commit(questions,report)
    print(json.dumps(report,ensure_ascii=True,indent=2))
