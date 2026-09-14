"""Offline, read-only XLSX extraction into a filtered JSON corpus. Run as a module."""
import hashlib
import json
from collections import Counter
from pathlib import Path
from .assessment_config import FIELDS, ASSESSMENT_TRACKS, SOFT
from .domain import SKILLS
from .onet_policy import POOLS, SOFTWARE, TASK_SKILLS, APPROVED, HELD, DEFERRED_INTERFACE_TRACKS, assignments, candidates, title_key
from .onet_policy import MARKETING_PROXY_CODES, MARKETING_SOFTWARE_PROXIES, MARKETING_TASK_PROXIES

ROOT=Path(__file__).resolve().parents[1]
SOURCES=ROOT/'onet'/'onet_data'
OUTPUT=ROOT/'backend'/'data'/'onet-corpus.json'

def rows(name, directory=SOURCES):
    from openpyxl import load_workbook
    book=load_workbook(directory/(name+'.xlsx'),read_only=True,data_only=True)
    try:
        stream=iter(book.active.values)
        header=next(stream)
        for values in stream: yield dict(zip(header,values))
    finally: book.close()

def derive_vector(occupation):
    allowed=set(ASSESSMENT_TRACKS[occupation['track']]['skills']) | set(SOFT)
    marketing_proxy=occupation['track']=='marketing' and occupation.get('code') in MARKETING_PROXY_CODES
    evidence={}
    def add(skill, item):
        if skill in allowed and skill in SKILLS:
            evidence.setdefault(skill,[]).append(item)
    for item in occupation['skills']:
        # IM=1 means not important. Retain raw ratings, never reinterpret as proficiency.
        if item.get('importance',0)<=item.get('importance_min',1): continue
        if item['name'] in SKILLS: add(item['name'],item)
    for item in occupation['software']:
        names=SOFTWARE.get(item['name'], [item['name']] if item['name'] in SKILLS else [])
        for skill in names: add(skill,item)
        if marketing_proxy:
            for skill in MARKETING_SOFTWARE_PROXIES.get(item['name'],[]):
                add(skill,{**item,'mapping_basis':'user-approved occupation-specific proxy'})
    for item in occupation['tasks']:
        if item.get('suppressed') or item.get('importance',0)<=item.get('importance_min',1): continue
        for skill in TASK_SKILLS.get(item['id'],[]): add(skill,item)
        if marketing_proxy:
            for skill in MARKETING_TASK_PROXIES.get(item['id'],[]):
                add(skill,{**item,'mapping_basis':'user-approved occupation-specific proxy'})
    return {skill:5.0 for skill in evidence}, evidence

def derive_profile(occupation, tracks):
    """Keep each approved track's vector, then form a presence union for shared listings."""
    vectors={}; evidence={}
    for track in tracks:
        vector,items=derive_vector({**occupation,'track':track})
        vectors[track]=vector
        for skill,records in items.items():
            target=evidence.setdefault(skill,[])
            for record in records:
                if record not in target: target.append(record)
    return {**occupation,'track':tracks[0] if len(tracks)==1 else None,'tracks':tracks,
            'track_vectors':vectors,'vector':{s:value for v in vectors.values() for s,value in v.items()},
            'evidence':evidence}

def build():
    assert set(POOLS)==set(ASSESSMENT_TRACKS), 'Track inventory changed; review pools before building'
    occupations={r['O*NET-SOC Code']:r for r in rows('Occupation Data')}
    pools=candidates()
    selected=assignments()
    unknown=sorted(set(pools)-occupations.keys())
    if unknown: raise ValueError(f'Unknown occupation codes: {unknown}')
    conflicts=[{'code':code,'title':occupations[code]['Title'],'candidate_tracks':tracks,
                'status':'approval_required; excluded from active corpus'} for code,tracks in pools.items() if len(tracks)>1 and code not in APPROVED and code not in HELD]
    held=[{'code':code,'title':occupations[code]['Title'],'reason':reason} for code,reason in HELD.items()]
    retained={code:{'code':code,'title':occupations[code]['Title'],'track':tracks[0] if len(tracks)==1 else None,'tracks':tracks,
                   'field':ASSESSMENT_TRACKS[tracks[0]]['field'],'aliases':[occupations[code]['Title']],
                   'skills':[],'software':[],'tasks':[]} for code,tracks in selected.items()}
    validation={}
    scales={r['Scale ID']:(r['Minimum'],r['Maximum']) for r in rows('Scales Reference')}
    for name in ['Essential Skills','Transferable Skills','Knowledge']:
        grouped={}; counts=Counter(); examples=[]
        for row in rows(name):
            scale=row['Scale ID'];value=row['Data Value'];code=row['O*NET-SOC Code']
            if scale not in {'IM','LV'}: continue
            if isinstance(value,bool) or not isinstance(value,(int,float)) or not scales[scale][0]<=value<=scales[scale][1]:
                raise ValueError(f'Invalid numeric rating in {name}: {code}')
            counts[scale]+=1
            if len(examples)<2: examples.append({k:row[k] for k in ['O*NET-SOC Code','Element Name','Scale ID','Data Value']})
            if code not in retained or row.get('Recommend Suppress')=='Y' or row.get('Not Relevant')=='Y': continue
            key=(code,row['Element ID'])
            item=grouped.setdefault(key,{'kind':name,'id':row['Element ID'],'name':row['Element Name']})
            item['importance' if scale=='IM' else 'level']=value
        if not counts['IM'] or not counts['LV']: raise ValueError(f'{name} has no real ratings')
        validation[name]={'numeric_ratings':dict(counts),'examples':examples}
        for (code,_),item in grouped.items(): retained[code]['skills'].append(item)
    for row in rows('Software Skills'):
        code=row['O*NET-SOC Code']
        if code in retained:
            retained[code]['software'].append({'kind':'Software Skills','id':row['Element ID'],
                'name':row['Workplace Example'],'category':row['Element Name'],
                'hot_technology':row['Hot Technology']=='Y','in_demand':row['In Demand']=='Y'})
    tasks={}
    for row in rows('Task Statements'):
        if row['O*NET-SOC Code'] in retained:
            tasks[(row['O*NET-SOC Code'],str(row['Task ID']))]={'kind':'Task Statements','id':str(row['Task ID']),
                'name':row['Task'],'task_type':row['Task Type']}
    task_count=0
    for row in rows('Task Ratings'):
        if row['Scale ID']!='IM': continue
        value=row['Data Value']
        if not isinstance(value,(int,float)) or not 1<=value<=5: raise ValueError('Invalid task importance')
        task_count+=1
        key=(row['O*NET-SOC Code'],str(row['Task ID']))
        if key in tasks:
            tasks[key]['importance']=value
            tasks[key]['suppressed']=row.get('Recommend Suppress')=='Y'
    validation['Task Ratings']={'numeric_importance_rows':task_count}
    for (code,_),item in tasks.items(): retained[code]['tasks'].append(item)
    # Build alias collisions against ALL occupations, including excluded ones.
    alias_codes={}
    for code,row in occupations.items(): alias_codes.setdefault(title_key(row['Title']),set()).add(code)
    for row in rows('Job Titles'):
        code=row['O*NET-SOC Code'];title=row['Job Title']
        if not title: continue
        alias_codes.setdefault(title_key(title),set()).add(code)
        if code in retained: retained[code]['aliases'].append(title)
    ambiguous_aliases={key:sorted(codes) for key,codes in alias_codes.items() if len(codes)>1 and set(codes)&retained.keys()}
    for code,item in retained.items():
        item['aliases']=sorted(set(a for a in item['aliases'] if len(alias_codes.get(title_key(a),set()))==1))
        retained[code]=derive_profile(item,selected[code])
    mapped=set(s for item in retained.values() for s in item['vector'])
    coverage={}
    for field,config in FIELDS.items():
        active=[v for v in retained.values() if v['field']==field]
        covered=sorted(set(t for v in active for t,vector in v['track_vectors'].items() if vector))
        coverage[config['label']]={'occupations':len(active),'mapped_skills':len(set(s for v in active for s in v['vector'])),
            'tracks_with_coverage':covered,'tracks_without_coverage':sorted(set(config['tracks'])-set(covered))}
    used=['Occupation Data','Job Titles','Essential Skills','Transferable Skills','Knowledge','Software Skills','Task Statements','Task Ratings','Scales Reference']
    manifest={name+'.xlsx':hashlib.sha256((SOURCES/(name+'.xlsx')).read_bytes()).hexdigest() for name in used}
    payload={'version':1,'source':'O*NET 31.0','license':'CC BY 4.0; National Center for O*NET Development',
        'source_url':'https://www.onetcenter.org/database.html','source_hashes':manifest,'occupations':retained,
        'blocked_codes':[code for code in pools if code not in selected], 'ambiguous_aliases':ambiguous_aliases}
    report={'status':'partial_coverage_pending_approval' if conflicts else 'partial_skill_coverage','validation':validation,'retained_occupations':len(retained),
        'mapped_astra_skills':len(mapped),'coverage':coverage,'occupation_approval_required':conflicts,
        'approved_assignments':APPROVED,'held_occupations':held,'deferred_interface_tracks':DEFERRED_INTERFACE_TRACKS,
        'bank_issues':['Sharing an occupation does not share questions. Bank counts are available from the assessment catalog and SQLite questions table.'],
        'ambiguous_title_count':len(ambiguous_aliases),'zero_coverage_skills':sorted(set(SKILLS)-mapped),
        'zero_coverage_by_track':{t:sorted(set(c['skills'])-set(s for v in retained.values() for s in v['track_vectors'].get(t,{}))) for t,c in ASSESSMENT_TRACKS.items()},
        'limitations':['Conservative occupation allowlist; ambiguous pools excluded pending explicit approval.',
        'Exact source labels/product equivalents and reviewed task-ID mappings only. Broader equivalences remain unmapped.',
        'Occupation skill presence uses the existing 5/10 learning baseline; importance/level are retained as source evidence, not converted to proficiency.',
        'Only unambiguous title/code joins enrich actual listings; occupation profiles never become fictional job openings.'],
        'source_hashes':manifest}
    OUTPUT.parent.mkdir(parents=True,exist_ok=True)
    OUTPUT.write_text(json.dumps(payload,ensure_ascii=False,separators=(',',':'))+'\n',encoding='utf-8')
    (ROOT/'ONET_COMPATIBILITY_REPORT.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    write_report(report)
    print(json.dumps({k:report[k] for k in ['retained_occupations','mapped_astra_skills','coverage']},indent=2))
    return report

def write_report(report):
    lines=['# O*NET alignment coverage','',
        f"Retained {report['retained_occupations']} occupation profiles; mapped {report['mapped_astra_skills']} exact Astra skill labels.",'',
        '| Field | Occupations | Mapped skills | Tracks with vector coverage |',
        '|---|---:|---:|---|']
    for field,item in report['coverage'].items():
        lines.append(f"| {field} | {item['occupations']} | {item['mapped_skills']} | {', '.join(item['tracks_with_coverage']) or 'None'} |")
    lines+=['','## Question-bank blockers','',*['- '+issue for issue in report['bank_issues']],
        '', 'Marketing occupation approval is active. No question content is generated by this alignment builder.',
        '', '## Approved assignments','']
    for code,tracks in APPROVED.items():
        state='held: '+HELD[code] if code in HELD else 'active'
        lines.append(f"- {code}: {', '.join(tracks)} ({state}).")
    lines+=['','Web/Digital Interface Designers is assigned only to frontend. ui-ux and product-design are unauthored starter tracks deferred for this interface-designer assignment. Their questions and other existing mappings were not changed.',
        '', '## Explicit holds','']
    for item in report['held_occupations']:
        lines.append(f"- {item['code']} — {item['title']}: {item['reason']}")
    lines+=['','## Remaining occupation decisions','']
    for item in report['occupation_approval_required']:
        lines.append(f"- {item['code']} — {item['title']}: {', '.join(item['candidate_tracks'])}. Excluded pending approval.")
    lines+=['','## Unresolved skill coverage','',', '.join(report['zero_coverage_skills']),
        '', 'Per-track missing labels, numeric source validation, and source hashes are in ONET_COMPATIBILITY_REPORT.json.',
        '', '## Compatibility behaviour','',
        'Original occupation records are stored once. Explicitly shared occupations retain separate track_vectors, and the listing input uses their skill-presence union. No candidate scoring, weighting, normalization or adaptive selection changed. Existing listing values win; added dimensions retain the established 5/10 learning baseline. O*NET importance and level remain source evidence, not proficiency scores.',
        '', 'Actual job IDs, Apply URLs and listing counts remain intact. Local occupation data is primary; missing allowed profiles may use O*NET API then cache, with unchanged listing skills as the final fallback. Held and unapproved occupations cannot be restored through API or cache.',
        '', 'Rebuild: python -m backend.prepare_onet. Optional ONET_API_KEY is read from the existing .env. Source XLSX files stay in onet/onet_data and are never modified. Runtime reads only the processed corpus.',
        '', 'Source: O*NET 31.0, National Center for O*NET Development, https://www.onetcenter.org/database.html, CC BY 4.0. Astra-specific mapping decisions are not endorsed by O*NET.',
        '', '## Files changed for these approval decisions','',
        'backend/onet_policy.py; backend/prepare_onet.py; backend/onet_alignment.py; backend/data/onet-corpus.json; tests/test_onet_alignment.py; ONET_COMPATIBILITY_REPORT.json; ONET_ALIGNMENT.md. No question banks or assessment configuration were changed.']
    (ROOT/'ONET_ALIGNMENT.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')

if __name__=='__main__': build()
