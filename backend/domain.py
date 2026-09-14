"""Shared skill taxonomy, assessment content and explainable matching."""
import math
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from .career_fields import TRACKS, EXTRA_TECH, track_questions

TAXONOMY = {
    'Backend': ['Python', 'Java', 'Node.js', 'Go', 'SQL', 'PostgreSQL', 'MongoDB', 'REST APIs', 'C#', 'C++'],
    'Frontend': ['React', 'Vue', 'Angular', 'JavaScript', 'TypeScript', 'CSS', 'HTML', 'Accessibility', 'Next.js', 'Responsive Design'],
    'Cloud & DevOps': ['AWS', 'GCP', 'Azure', 'Docker', 'Kubernetes', 'Linux', 'CI/CD', 'Terraform', 'Networking', 'Git'],
    'Data & AI': ['Machine Learning', 'Data Science', 'Pandas', 'TensorFlow', 'Statistics', 'Excel', 'Power BI', 'Data Visualization', 'NumPy', 'Data Engineering'],
    'Engineering': ['Testing', 'System Design', 'Data Structures', 'Algorithms', 'Cybersecurity', 'Agile', 'Debugging', 'Documentation', 'UI/UX', 'Figma'],
    'People': ['Communication', 'Leadership', 'Problem Solving', 'Teamwork', 'Time Management', 'Adaptability', 'Critical Thinking', 'Presentation', 'Collaboration', 'Research'],
}
for track, config in TRACKS.items():
    TAXONOMY[config['label']] = config['skills']
TAXONOMY['Additional technology'] = EXTRA_TECH
from .assessment_config import ASSESSMENT_TRACKS
for config in ASSESSMENT_TRACKS.values(): TAXONOMY[config['label']]=list(dict.fromkeys([*TAXONOMY.get(config['label'],[]),*config['skills']]))
TAXONOMY['Backend'].extend(['Backend Testing','Adaptive / Project Context'])
SKILLS = list(dict.fromkeys(s for group in TAXONOMY.values() for s in group))
ASSESSED = ['Python', 'SQL', 'React', 'JavaScript', 'HTML', 'CSS', 'Git', 'REST APIs', 'AWS', 'Docker', 'Data Structures', 'Testing', 'Communication', 'Teamwork', 'Problem Solving']
QUESTIONS = [{'id': f'r{i}', 'kind': 'rating', 'skills': [skill], 'title': f'How confident are you with {skill}?', 'hint': '0 = no experience Ã‚· 5 = can work with guidance Ã‚· 10 = can independently teach others'} for i, skill in enumerate(ASSESSED)]
for i, skill in enumerate(['Python', 'SQL', 'React', 'AWS', 'Docker']):
    QUESTIONS.append({'id': f'p{i}', 'kind': 'projects', 'skills': [skill], 'title': f'How many completed projects have you used {skill} in?', 'hint': 'Count projects you personally contributed to.', 'options': ['None yet', '1 project', '2Ã¢â‚¬“3 projects', '4Ã¢â‚¬“5 projects', '6+ projects']})
SCENARIOS = [
    ('An API request fails with a 500 response. What is your best first step?', ['Retry forever', 'Inspect server logs and reproduce the request', 'Change the CSS', 'Delete the database'], 1, ['REST APIs', 'Problem Solving', 'Testing']),
    ('Which SQL clause filters grouped aggregate results?', ['WHERE', 'ORDER BY', 'HAVING', 'LIMIT'], 2, ['SQL']),
    ('A React state update depends on its previous value. Which is safest?', ['Mutate the state directly', 'Reload the page', 'Use a global variable', 'Use a functional state updater'], 3, ['React', 'JavaScript']),
    ('A teammate is blocked and your deadline is near. What should you do?', ['Discuss the blocker and agree on a shared plan', 'Ignore it', 'Assign blame in the group chat', 'Quietly remove their work'], 0, ['Teamwork', 'Communication']),
    ('You need fast lookup of a value by a unique key. Which structure fits best?', ['Unsorted list', 'Stack', 'Hash map', 'Queue'], 2, ['Data Structures', 'Problem Solving']),
]
ANSWERS = {}
for i, (title, options, answer, skills) in enumerate(SCENARIOS):
    key = f's{i}'
    QUESTIONS.append({'id': key, 'kind': 'scenario', 'skills': skills, 'title': title, 'hint': 'Choose the best answer.', 'options': options})
    ANSWERS[key] = answer

def get_assessment(track='technology'):
    if track not in TRACKS: raise ValueError('Unknown career field.')
    if track == 'technology': return ASSESSED, QUESTIONS, ANSWERS
    return track_questions(track)

def score_answers(answers, track='technology'):
    assessed, questions, answer_keys = get_assessment(track)
    expected = {q['id'] for q in questions}
    if len(answers) != len(expected) or {a.question_id for a in answers} != expected:
        raise ValueError('Submit each of the 25 questions exactly once.')
    supplied = {a.question_id: a.value for a in answers}
    evidence = {s: [] for s in assessed}
    for q in questions:
        value = supplied[q['id']]
        limit = 10 if q['kind'] == 'rating' else len(q['options']) - 1
        if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= limit:
            raise ValueError(f"Invalid answer for {q['id']}.")
        points, weight = (value, 1) if q['kind'] == 'rating' else (([0, 3, 5, 7, 10][value], 1.5) if q['kind'] == 'projects' else (10 if value == answer_keys[q['id']] else 0, 2))
        for skill in q['skills']:
            evidence[skill].append((points, weight))
    return {s: round(sum(p*w for p,w in values)/sum(w for _,w in values), 1) for s, values in evidence.items()}

def build_job_matrix(jobs):
    matrix = np.zeros((len(jobs),len(SKILLS)),dtype=np.float32)
    index = {skill:i for i,skill in enumerate(SKILLS)}
    for row,job in enumerate(jobs):
        for skill,value in job['skills'].items():
            if skill in index: matrix[row,index[skill]]=value
    return matrix

def rank_jobs(vector, jobs, limit=10, matrix=None, evidence=None):
    if not jobs: return []
    s = [vector.get(skill, 0) for skill in SKILLS]
    if matrix is None: matrix=build_job_matrix(jobs)
    scores=cosine_similarity([s],matrix)[0]
    selected=sorted(range(len(jobs)),key=lambda i:(-round(float(scores[i])*100,1),jobs[i]['id']))[:limit]
    from .learning_resources import resources
    links=resources()
    ranked = []
    for idx in selected:
        job=jobs[idx]
        score = round(float(scores[idx])*100, 1)
        met, gaps = [], []
        for skill, required in job['skills'].items():
            actual = vector.get(skill, 0)
            item = {'skill': skill, 'actual': actual, 'required': required, 'delta': round(max(0, required-actual), 1), 'assessed': evidence.get(skill,{}).get('assessed',False) if evidence is not None else skill in vector, 'evidence': evidence.get(skill,{}).get('basis','Untested') if evidence is not None else 'Self-reported; not verified', 'resources':links.get(skill,[])}
            (met if actual >= required else gaps).append(item)
        gaps.sort(key=lambda g: (-g['delta'], g['skill']))
        ranked.append({'job': job, 'match_score': score, 'matched_skills': met, 'gaps': gaps, 'suggestions': [{'skill': g['skill'], 'weeks': math.ceil(g['delta']*2), 'text': f"Improve {g['skill']} from {g['actual']}/10 to {g['required']}/10 with focused practice.", 'estimated': True} for g in [g for g in gaps if g['assessed']][:3]]})
    return sorted(ranked, key=lambda r: (-r['match_score'], r['job']['id']))[:limit]
