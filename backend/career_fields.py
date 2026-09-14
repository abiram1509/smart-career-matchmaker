"""Cross-sector assessment tracks and explicit skill aliases."""
COMMON = ['Communication','Teamwork','Problem Solving','Time Management','Documentation']
TRACKS = {
 'technology': {'label':'Technology & data','skills':['Python','SQL','React','JavaScript','Git','REST APIs','AWS','Docker','Data Structures','Testing']},
 'sales': {'label':'Sales & customer service','skills':['Sales','Customer Service','Negotiation','CRM','Lead Generation','Account Management','Business Development','Presentation','Market Research','Excel']},
 'finance': {'label':'Finance & accounting','skills':['Accounting','Financial Analysis','Budgeting','Auditing','Taxation','Bookkeeping','Excel','Financial Reporting','Risk Management','Reconciliation']},
 'people': {'label':'HR & administration','skills':['Recruitment','HR Management','Scheduling','Office Administration','Payroll','Record Keeping','Excel','Customer Service','Training','Data Entry']},
 'education': {'label':'Education & training','skills':['Teaching','Lesson Planning','Curriculum Development','Assessment Design','Classroom Management','Training','Research','Presentation','Student Support','Record Keeping']},
 'healthcare': {'label':'Healthcare support','skills':['Patient Support','Medical Terminology','Health Records','Scheduling','Confidentiality','Infection Prevention','Care Coordination','Customer Service','Record Keeping','Quality Assurance']},
 'creative': {'label':'Marketing & creative work','skills':['Digital Marketing','Content Writing','SEO','Social Media','Graphic Design','Video Editing','Copywriting','Market Research','Campaign Management','Analytics']},
 'operations': {'label':'Engineering, operations & logistics','skills':['Project Management','Quality Assurance','Safety Procedures','Supply Chain','Inventory Management','Logistics','Manufacturing','Maintenance','CAD','Excel']},
 'legal': {'label':'Legal & compliance support','skills':['Legal Research','Compliance','Contract Review','Record Keeping','Confidentiality','Risk Management','Case Management','Writing','Research','Office Administration']},
}

# Aliases are literal phrases, escaped before boundary matching. Related tools
# remain separate skills (CI/CD is not Jenkins; Node.js is not JavaScript).
ALIASES = {
 'Node.js':['nodejs','node.js'], 'JavaScript':['javascript'], 'C++':['c++','cpp'], 'C#':['c#','csharp','c sharp'],
 'Go':['golang','go language'], 'R':['r programming','r language'], 'React':['react','reactjs','react.js'],
 'AWS':['aws','amazon web services'], 'GCP':['gcp','google cloud'], 'PostgreSQL':['postgresql','postgres'],
 'Machine Learning':['machine learning'], 'Scikit-learn':['scikit-learn','sklearn'], 'NLP':['nlp','natural language processing'],
 'CI/CD':['ci/cd','continuous integration','continuous delivery'], 'Power BI':['power bi','powerbi'],
 'Problem Solving':['problem solving','problem-solving'], 'Teamwork':['teamwork','team work','team player'],
 'Communication':['communication','communicate'], 'Documentation':['documentation','documenting'],
 'Sales':['sales','selling'], 'CRM':['crm','customer relationship management'],
 'Customer Service':['customer service','customer support'], 'Lead Generation':['lead generation','prospecting'],
 'Accounting':['accounting','accountant'], 'Auditing':['auditing','audit'], 'Taxation':['taxation','tax compliance','tax returns'],
 'Budgeting':['budgeting','budgets','budget management'], 'Reconciliation':['reconciliation','reconciling'],
 'Recruitment':['recruitment','recruiting','talent acquisition'], 'HR Management':['human resources','hr management'],
 'Office Administration':['office administration','administrative support','administrative assistant'],
 'Scheduling':['scheduling','schedule appointments'], 'Record Keeping':['record keeping','recordkeeping','maintain records'],
 'Teaching':['teaching','teacher','instructor'], 'Student Support':['student support','student services'],
 'Patient Support':['patient support','patient care','patient services'], 'Health Records':['health records','medical records','ehr','emr'],
 'Confidentiality':['confidentiality','confidential information'], 'Care Coordination':['care coordination','coordinate care'],
 'Infection Prevention':['infection prevention','infection control'], 'Quality Assurance':['quality assurance','quality control'],
 'Content Writing':['content writing','content creation'], 'Graphic Design':['graphic design','graphic designer'],
 'SEO':['seo','search engine optimization'], 'Social Media':['social media'], 'Writing':['writing','written reports'],
 'Safety Procedures':['safety procedures','safety protocols','workplace safety'], 'Supply Chain':['supply chain'],
 'CAD':['cad','computer aided design'], 'Maintenance':['maintenance','repair'],
 'Legal Research':['legal research'], 'Contract Review':['contract review','review contracts'],
 'Compliance':['compliance','regulatory requirements'],
}
EXTRA_TECH = ['Jenkins','ETL','Spark','Salesforce','R','Computer Vision','Spring','Big Data','MySQL','Tableau','Hadoop','Kafka','Scala','Deep Learning','PHP','Django','Flask','Go','NLP','PyTorch','Cassandra','Express','Redis','Kotlin','Ruby','DynamoDB','Elasticsearch','Scikit-learn','Rust','FastAPI']

# Five practical items per track, mixed with 15 ratings and 5 experience items.
# Healthcare assesses support/administrative skills, never clinical competence.
CASES = {
 'sales': [
 ('A customer says the price is too high. What should you do first?', ['Promise an unauthorized discount','Ask about their needs and explain relevant value','Pressure them to buy','Ignore their concern'],1,'Negotiation'),
 ('How should you maintain a shared customer record?', ['Log factual interactions and agreed next steps','Store payment passwords','Invent missing details','Keep everything only in memory'],0,'CRM'),
 ('How can you compare two sales campaigns fairly?', ['Use impressions alone','Ignore different time windows','Compare conversions over equivalent periods and audiences','Choose the larger total without context'],2,'Market Research')],
 'finance': [
 ('A bank statement and cash ledger disagree. What is the next step?', ['Change the balance until it matches','Delete the unmatched entries','Identify timing differences and reconcile supporting records','Ignore the difference'],2,'Reconciliation'),
 ('An expense lacks its supporting invoice. What should you do?', ['Create a fictional invoice','Request the supporting record and follow approval procedures','Approve it automatically','Record it twice'],1,'Auditing'),
 ('Which spreadsheet approach makes a budget easier to update?', ['Hardcode every total','Use one unexplained number','Link documented assumptions to formulas','Remove source amounts'],2,'Budgeting')],
 'people': [
 ('Two interviews overlap in the calendar. What should you do?', ['Confirm availability and agree a revised slot','Cancel both without notice','Ignore the conflict','Share private notes publicly'],0,'Scheduling'),
 ('A personnel record contains conflicting dates. What should you do?', ['Guess the date','Delete the record','Check authorized source records and document the correction','Copy someone else’s date'],2,'Record Keeping'),
 ('What makes an initial candidate review more consistent?', ['Use personal assumptions','Apply the same documented job-related criteria','Rank by unrelated personal traits','Ignore the role requirements'],1,'Recruitment')],
 'education': [
 ('How should a lesson assessment be designed?', ['Measure unrelated facts','Assess the stated learning objective','Use only the hardest possible questions','Avoid feedback'],1,'Assessment Design'),
 ('A learner is struggling with a concept. What is a useful next step?', ['Repeat the same explanation louder','Stop offering help','Identify the misconception and try a different example','Compare them publicly'],2,'Student Support'),
 ('What belongs in a lesson plan?', ['An objective, activities and a way to check learning','Only the textbook title','Only the attendance list','An unrelated examination'],0,'Lesson Planning')],
 'healthcare': [
 ('An unauthorized caller requests a patient record. What should support staff do?', ['Disclose it immediately','Post it publicly','Verify authorization through the approved privacy process','Guess the caller’s identity'],2,'Confidentiality'),
 ('An appointment request is missing essential scheduling details. What should you do?', ['Invent the details','Confirm required information through the approved channel','Discard it silently','Make a clinical diagnosis'],1,'Scheduling'),
 ('Two authorized records show different contact details. What should you do?', ['Verify through the approved record-correction process','Choose randomly','Remove all records','Send both to everyone'],0,'Health Records')],
 'creative': [
 ('A campaign aims to generate qualified enquiries. Which measure best fits?', ['Only font size','Only total followers','Qualified enquiry conversions','Only page length'],2,'Campaign Management'),
 ('What should guide a first content draft?', ['Copy a competitor verbatim','The brief, audience and communication goal','Unrelated trending words','Unverified claims'],1,'Content Writing'),
 ('A design brief changes. What should you do before revising?', ['Confirm the new requirements and document scope','Discard the brief','Ignore stakeholders','Publish unfinished assets'],0,'Graphic Design')],
 'operations': [
 ('A stock count differs from the inventory record. What should you do?', ['Adjust it without evidence','Ignore it','Recount and reconcile documented movements','Order random quantities'],2,'Inventory Management'),
 ('A potential workplace hazard is identified. What is appropriate?', ['Follow the approved safety and reporting procedure','Ignore it to meet a deadline','Hide it','Improvise an unapproved repair'],0,'Safety Procedures'),
 ('A project milestone slips. What should the coordinator do?', ['Change dates silently','Assess dependencies and agree an updated plan','Remove the milestone','Blame another team'],1,'Project Management')],
 'legal': [
 ('Two versions of a contract have different clauses. What should support staff do?', ['Choose randomly','Compare versions and flag changes for authorized review','Sign it without review','Delete both'],1,'Contract Review'),
 ('A research source may be outdated. What should you do?', ['Treat it as current','Hide its date','Verify currency and record the source','Invent an update'],2,'Legal Research'),
 ('A case document is sent to the wrong internal folder. What should you do?', ['Share it widely','Ignore access controls','Follow the approved access and correction process','Publish it'],2,'Confidentiality')],
}

def track_questions(track):
    config=TRACKS[track]
    assessed=config['skills']+COMMON
    questions=[{'id':f'{track}-r{i}','kind':'rating','skills':[s],'title':f'How confident are you with {s}?','hint':'0 = no experience · 5 = work with guidance · 10 = independently teach others'} for i,s in enumerate(assessed)]
    for i,s in enumerate(config['skills'][:5]):
        questions.append({'id':f'{track}-p{i}','kind':'projects','skills':[s],'title':f'How many completed tasks, assignments or projects have used {s}?','hint':'Count work you personally contributed to, including study or volunteering.','options':['None yet','1 task or project','2–3 tasks or projects','4–5 tasks or projects','6+ tasks or projects']})
    cases=CASES[track]+[
        ('A teammate is blocked near a deadline. What should you do?', ['Ignore the blocker','Discuss it and agree on a shared plan','Assign blame','Remove their work silently'],1,'Teamwork'),
        ('A handover contains unclear instructions. What should you do?', ['Guess and proceed','Delete the handover','Clarify the missing information and document it','Avoid communicating'],2,'Documentation')]
    keys={}
    for i,(title,options,answer,skill) in enumerate(cases):
        qid=f'{track}-s{i}'
        questions.append({'id':qid,'kind':'scenario','skills':[skill],'title':title,'hint':'Choose the best next step.','options':options})
        keys[qid]=answer
    return assessed,questions,keys
