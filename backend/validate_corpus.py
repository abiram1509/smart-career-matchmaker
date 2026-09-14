"""Offline corpus integrity and 30-track adaptive assessment smoke checks."""
import hashlib,json,tempfile
from pathlib import Path
import numpy as np
from .loader import HybridJobLoader,DATA
from .domain import SKILLS,rank_jobs
from .assessment_config import ASSESSMENT_TRACKS
from . import adaptive_quiz as quiz

def validate():
 with tempfile.TemporaryDirectory() as d:loader=HybridJobLoader(DATA/'jobs.csv',Path(d)/'absent.json','')
 report=json.loads((DATA/'dataset_report.json').read_text(encoding='utf-8'))
 assert len(loader.jobs)==report['jobs'] and len({j['id'] for j in loader.jobs})==len(loader.jobs)
 assert all(set(j['skills'])<=set(SKILLS) for j in loader.jobs)
 np.savez_compressed(DATA/'skill_vectors.npz',matrix=loader.matrix,skills=np.array(SKILLS),job_ids=np.array([j['id'] for j in loader.jobs]))
 manifest={'kind':'Deterministic fixed skill-vector cosine index','records':len(loader.jobs),'dimensions':len(SKILLS),'csv_sha256':hashlib.sha256((DATA/'jobs.csv').read_bytes()).hexdigest(),'index_file':'skill_vectors.npz','proficiency_labels':'Description targets 6/7 and category targets 5 are heuristic, not employer-stated proficiency.','salary_prediction':False}
 (DATA/'model_manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
 checks={}
 for track,c in ASSESSMENT_TRACKS.items():
  state=quiz.initial(c['field'],track)
  while state['phase']!='complete':
   answers=[]
   for q in state['pending']:
    value=7 if q['type']=='self_rating' else '' if q['type']=='project_note' else q['correct_option'] if q['tier']==3 else 2 if q['type']=='project_count' else 0
    answers.append({'question_id':q['id'],'value':value})
   state=quiz.advance(state,answers)
  v,e=quiz.score(state)
  indices=[i for i,j in enumerate(loader.jobs) if j.get('field')==c['job_field'] or c['job_field'] in (j.get('category_fields') or [])]
  matches=rank_jobs(v,[loader.jobs[i] for i in indices],10,loader.matrix[indices],e)
  assert matches,(track,'No corpus matches')
  checks[track]={'matches':len(matches),'quiz_checks':len(state.get('verification',[])),'top_title':matches[0]['job']['title']}
 result={'jobs':len(loader.jobs),'dimensions':len(SKILLS),'salary_jobs':sum(bool(j.get('salary_data')) for j in loader.jobs),'checks':checks,'test_scope':'Functional integrity and example-quiz smoke checks, not measured recommendation accuracy.'}
 assert result['salary_jobs']==report['salary_jobs']
 (DATA/'validation_report.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
 print(json.dumps({k:v for k,v in result.items() if k!='checks'}));print('Passed',len(checks),'adaptive tracks')
if __name__=='__main__':validate()
