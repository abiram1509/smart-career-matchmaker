import unittest
from backend import adaptive_quiz as q
from backend.assessment_config import FIELDS

class ServingLimitsTests(unittest.TestCase):
 def test_all_tracks_ten_baselines_and_unchanged_counts(self):
  for field,info in FIELDS.items():
   for track in info['tracks']:
    s=q.initial(field,track)
    original=[x for x in s['bank'] if x['track'] in [track,'Universal'] and x['tier']==1]
    self.assertEqual(s['pending'],original[:10])
    q.advance(s,[{'question_id':x['id'],'value':7} for x in s['pending']])
    self.assertEqual(s['pending'],[x for x in s['bank'] if x['track']==track and x['tier']==2 and x.get('phase')=='counts'])
    q.advance(s,[{'question_id':x['id'],'value':0} for x in s['pending']])
    self.assertEqual(s['phase'],'complete')
    _,e=q.score(s);self.assertEqual(sum(x['assessed'] for x in e.values()),10)
 def test_twenty_eligible_checks(self):
  candidates=[{'id':str(i),'tier':3,'track':'frontend','skill':'JavaScript','requires_tier2_flag':'JavaScript','verification_kind':'skill'} for i in range(30)]
  s={'flags':['JavaScript'],'answers':{},'track':'frontend','bank':candidates}
  self.assertEqual(q.select_verification(s),candidates[:20])
  s['bank']=candidates[:4];self.assertEqual(len(q.select_verification(s)),4)
 def test_unrated_checks_do_not_create_score(self):
  s=q.initial('tech','backend');rated=s['pending'];missing=next(x for x in s['bank'] if x['track']=='backend' and x['tier']==1 and x not in rated)
  s.update(phase='complete',answers={x['id']:7 for x in rated},verification=[{'id':'check','skill':missing['skill'],'correct_option':0}]);s['answers']['check']=0
  v,e=q.score(s);self.assertEqual(v[missing['skill']],0);self.assertFalse(e[missing['skill']]['assessed']);self.assertFalse(e[missing['skill']]['verified'])
