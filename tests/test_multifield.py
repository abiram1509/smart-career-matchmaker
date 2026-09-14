import unittest
from backend.domain import get_assessment,score_answers,SKILLS,rank_jobs
from backend.career_fields import TRACKS
from backend.prepare_data import extract_skills,career_field,salary
from backend.main import Answer

class MultiFieldTests(unittest.TestCase):
    def test_all_tracks_complete_and_nontechnical(self):
        for track in TRACKS:
            skills,questions,keys=get_assessment(track)
            self.assertEqual(len(questions),25)
            self.assertEqual(len(set(skills)),15)
            self.assertTrue(set(skills)<=set(SKILLS))
            answers=[Answer(question_id=q['id'],value=10 if q['kind']=='rating' else 4 if q['kind']=='projects' else keys[q['id']]) for q in questions]
            self.assertTrue(all(v==10 for v in score_answers(answers,track).values()))
            if track!='technology': self.assertNotIn('Python',skills)
        with self.assertRaises(ValueError): get_assessment('unknown')

    def test_cross_sector_extraction_and_regex_boundaries(self):
        for text,expected in [('Accounting and reconciliation',{'Accounting','Reconciliation'}),('Teaching and lesson planning',{'Teaching','Lesson Planning'}),('C++ and C# with Node.js',{'C++','C#','Node.js'}),('Sales and customer service',{'Sales','Customer Service'})]:
            self.assertTrue(expected<=set(extract_skills(text)))
        self.assertNotIn('Java',extract_skills('JavaScript'))
        self.assertNotIn('Jenkins',extract_skills('CI/CD'))
        self.assertNotIn('Salesforce',extract_skills('CRM'))
        self.assertNotIn('R',extract_skills('Our team is ready'))

    def test_fields(self):
        for title,field in [('Registered Nurse','healthcare'),('Legal Assistant Paralegal','legal'),('Accountant','finance'),('Early Education Teacher','education'),('Software Engineer','technology'),('Civil Engineer','operations'),('Sales Representative','sales')]:
            self.assertEqual(career_field(title),field)

    def test_salary_preserves_units_and_rejects_unknown(self):
        text,data=salary({'min_salary':'20','max_salary':'30','currency':'USD','pay_period':'HOURLY'})
        self.assertEqual(text,'USD 20–30 / hour');self.assertEqual(data['period'],'HOURLY')
        self.assertIsNone(salary({'income':'45000','age':'40'})[1])
        self.assertIsNone(salary({'min_salary':'30','max_salary':'20','currency':'USD','pay_period':'HOURLY'})[1])

    def test_nonengineering_profile_ranks_relevant_role(self):
        jobs=[{'id':'tech','skills':{'Python':5,'Docker':5}}, {'id':'finance','skills':{'Accounting':5,'Reconciliation':5}}]
        self.assertEqual(rank_jobs({'Accounting':8,'Reconciliation':7},jobs)[0]['job']['id'],'finance')
