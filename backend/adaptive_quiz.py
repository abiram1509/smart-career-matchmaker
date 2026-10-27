"""Deterministic adaptive questionnaire. Answer keys never leave the backend."""
import json
from pathlib import Path
from .assessment_config import ASSESSMENT_TRACKS,FIELDS,SOFT,TIER1_SERVE_LIMIT,TIER3_SERVE_LIMIT
from .domain import SKILLS
BANK_PATH=Path(__file__).with_name('question_bank.json')

def bank():
 rows=json.loads(BANK_PATH.read_text(encoding='utf-8-sig'))
 seen=set()
 for q in rows:
  if q['id'] in seen or q['track'] not in [*ASSESSMENT_TRACKS,'Universal'] or q['skill'] not in SKILLS:raise ValueError('Invalid question bank identity, track or skill.')
  seen.add(q['id'])
  if q['tier']==3 and (type(q.get('correct_option')) is not int or not 0<=q['correct_option']<len(q.get('options',[]))):raise ValueError('Verification question requires a valid answer key.')
 return rows

def public(q):return {k:v for k,v in q.items() if k not in {'correct_option','accepted_answers'}}
def initial(field,track):
 if field not in FIELDS or track not in FIELDS[field]['tracks']:raise ValueError('Choose a track belonging to the selected field.')
 rows=bank()
 return {'field':field,'track':track,'phase':'confidence','answers':{},'bank':rows,'pending':[q for q in rows if q['track'] in [track,'Universal'] and q['tier']==1][:TIER1_SERVE_LIMIT]}

def validate(q,value):
 if q['type']=='project_note':
  if not isinstance(value,str) or len(value)>1000:raise ValueError('Project notes must contain at most 1,000 characters.')
  return value.strip()
 if type(value) is not int:raise ValueError('Choose an integer answer.')
 low=q.get('min',0); high=q.get('max',len(q.get('options',[]))-1)
 if not low<=value<=high:raise ValueError('Answer outside the question range.')
 return value

def contexts(flags):
 if not flags:return []
 kinds=[('summary','project_note','Briefly describe your project or supervised assignment. Optional; not graded.',None),('contribution','context_choice','How much did you contribute yourself?',['Mostly myself','Shared team contribution','Small contribution']),('ai','context_choice','How much did you rely on AI tools across these projects?',['Barely used it','Used it for some parts','Used it heavily']),('challenge','project_note','What was the hardest part? Optional; stored as project context, not graded.',None),('focus','context_choice','Which aspect would you like the project questions to focus on?',['Implementation','Checking and debugging','Planning and interpretation'])]
 result=[]
 for i,(key,kind,prompt,options) in enumerate(kinds):
  skill=flags[i%min(3,len(flags))]
  q={'id':'context-'+key,'track':'Universal','tier':2,'phase':'context','skill':skill,'type':kind,'prompt_text':prompt+(' ('+skill+')' if key!='ai' else ''),'optional':kind=='project_note'}
  if options:q['options']=options
  result.append(q)
 return result

def select_verification(state):
 flags=state['flags'];answers=state['answers'];deep=answers.get('context-ai')==2
 candidates=[q for q in state['bank'] if q['tier']==3 and q['track'] in [state['track'],'Universal'] and q.get('requires_tier2_flag') in flags and q['skill'] not in SOFT]
 pools={}
 for skill in flags:
  items=[q for q in candidates if q.get('requires_tier2_flag')==skill]
  pure=[q for q in items if q.get('verification_kind')=='skill']
  if state['track']=='backend':
   # Rotate scored dimensions within each eligibility cluster.
   groups={}
   for q in pure:groups.setdefault(q['skill'],[]).append(q)
   pure=[]
   while any(groups.values()):
    for group in groups.values():
     if group:pure.append(group.pop(0))
  project=[q for q in items if q.get('verification_kind')=='project' and q.get('difficulty','standard')==('deep' if deep else 'standard')]
  if not project:project=[q for q in items if q.get('verification_kind')=='project']
  focus=['implementation','debugging','planning'][answers.get('context-focus',0)]
  project.sort(key=lambda q:(focus not in q.get('context_tags',[]),q['id']))
  if state['track']=='backend':
   context=' '.join(str(answers.get('backend-user-context-'+str(i),'')) for i in (1,4)).lower()
   relevant=any(word in context for word in ('auth','login','commerce','order','payment','token'))
   if not relevant and answers.get('backend-user-context-3')!=2:
    pure.extend(project);project=[]
  mixed=[]
  for i in range(max(len(project),len(pure))):
   if i<len(project):mixed.append(project[i])
   if i<len(pure):mixed.append(pure[i])
  pools[skill]=mixed
 selected=[]
 while len(selected)<TIER3_SERVE_LIMIT and any(pools.values()):
  for skill in flags:
   if pools[skill] and len(selected)<TIER3_SERVE_LIMIT:selected.append(pools[skill].pop(0))
 return selected

def advance(state,answers):
 pending={q['id']:q for q in state['pending']}
 if len(answers)!=len(pending) or {a['question_id'] for a in answers}!=set(pending):raise ValueError('Answer each question in this step exactly once.')
 for a in answers:state['answers'][a['question_id']]=validate(pending[a['question_id']],a['value'])
 phase=state['phase'];rows=state['bank'];track=state['track']
 if phase=='confidence':
  state['phase']='counts';state['pending']=[q for q in rows if q['track']==track and q['tier']==2 and q.get('phase')=='counts']
 elif phase=='counts':
  ratings={q['skill']:state['answers'][q['id']] for q in rows if q['track']==track and q['tier']==1 and q['id'] in state['answers']}
  flags=[q['skill'] for q in state['pending'] if state['answers'][q['id']]>=2]
  state['flags']=sorted(flags,key=lambda s:(-ratings.get(s,0),s));state['phase']='context';state['pending']=([q for q in rows if q['track']==track and q['tier']==2 and q.get('phase')=='context'] or contexts(state['flags'])) if state['flags'] else []
  if not state['pending']:state['phase']='complete'
 elif phase=='context':
  state['pending']=select_verification(state);state['verification']=state['pending'];state['phase']='verification' if state['pending'] else 'complete'
 elif phase=='verification':state['pending']=[];state['phase']='complete'
 else:raise ValueError('Assessment already completed.')
 return state

def score(state):
 if state['phase']!='complete':raise ValueError('Complete the assessment before scoring.')
 vector={s:0 for s in SKILLS};evidence={s:{'assessed':False,'verified':False,'basis':'Untested'} for s in SKILLS}
 for q in state['bank']:
  if q['tier']!=1 or q['id'] not in state['answers']:continue
  skill=q['skill'];rating=state['answers'][q['id']]
  checks=[v for v in state.get('verification',[]) if v['skill']==skill]
  correct=sum(state['answers'][v['id']]==v['correct_option'] for v in checks)
  passed=bool(checks) and correct==len(checks)
  vector[skill]=min(rating,4) if checks and not passed else rating
  evidence[skill]={'assessed':True,'verified':passed,'self_rating':rating,'checks':len(checks),'correct':correct,'example_checks':any(v.get('example') for v in checks),'basis':('Example checks passed; not a credential' if any(v.get('example') for v in checks) else 'Quiz checks passed; not a credential') if passed else 'Applied checks incomplete or incorrect' if checks else 'No applied check selected; self-reported' if skill in state.get('flags',[]) else 'Self-reported; not verified'}
 for skill in {q['skill'] for q in state.get('verification',[])}:
  if evidence[skill]['assessed']:continue
  checks=[q for q in state['verification'] if q['skill']==skill]
  evidence[skill]={'assessed':False,'verified':False,'checks':len(checks),'correct':sum(state['answers'][q['id']]==q['correct_option'] for q in checks),'example_checks':False,'basis':'Applied checks recorded; no Tier 1 baseline, so no numeric proficiency assigned'}
 return vector,evidence

def view(state):
 return {'field':state['field'],'track':state['track'],'phase':state['phase'],'questions':[public(q) for q in state['pending']],'flagged_skills':state.get('flags',[]),'notice':('Backend bank: 60 applied questions available.' if state['track']=='backend' else 'Starter example bank.')+' Tier 3 contains only available relevant questions, up to 20. Missing coverage is not counted as a pass. Quiz checks do not verify employment experience, credentials or clinical competence.'}
