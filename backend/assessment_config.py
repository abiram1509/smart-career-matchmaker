"""Field/track configuration for the addendum assessment; shared skill names."""
SOFT=['Communication','Leadership','Problem Solving','Teamwork','Adaptability']
FIELDS={
 'tech':{'label':'Tech','tracks':['backend','frontend','data-ml','cloud-devops','qa-testing']},
 'business':{'label':'Business / Management','tracks':['business-marketing','business-sales','hr','business-finance','business-operations']},
 'design':{'label':'Design','tracks':['ui-ux','graphic','product-design']},
 'core-engineering':{'label':'Core Engineering','tracks':['mechanical','civil','electrical','electronics']},
 'finance-commerce':{'label':'Finance / Commerce','tracks':['accounting','financial-analysis','banking']},
 'marketing-sales':{'label':'Marketing / Sales','tracks':['marketing','sales-track']},
 'operations-field':{'label':'Operations','tracks':['logistics','project-operations']},
 'healthcare-field':{'label':'Healthcare','tracks':['clinical','health-admin','health-it']},
 'other-field':{'label':'Other','tracks':['general','education-track','legal-support']},
}
def entry(label,skills,job_field):return {'label':label,'skills':skills.split('|'),'job_field':job_field}
ASSESSMENT_TRACKS={
 'backend':entry('Backend','Python|Java / Node.js|SQL|Relational Databases|NoSQL|REST APIs|Authentication|Git|Data Structures|Error Handling|Testing|API Integration|Deployment|Performance|Security','technology'),
 'frontend':entry('Frontend','JavaScript|React|HTML|CSS|TypeScript|Vue|Angular|Accessibility|Responsive Design|Git','technology'),
 'data-ml':entry('Data / ML','Statistics|SQL|Python|Pandas|Data Visualization|Data Science|Machine Learning|NumPy|Excel|Data Engineering','technology'),
 'cloud-devops':entry('Cloud / DevOps','Docker|AWS|Linux|Networking|Git|Kubernetes|Azure|GCP|Terraform|CI/CD','technology'),
 'qa-testing':entry('QA / Testing','Testing|Manual Testing|Automation Testing|Test Case Design|Selenium|SQL|Debugging|Documentation|Git|Quality Assurance','technology'),
 'business-marketing':entry('Marketing','SEO|Digital Marketing|Market Research|Campaign Management|Analytics|Content Writing|Social Media|CRM|Presentation|Excel','creative'),
 'business-sales':entry('Sales','CRM|Sales|Negotiation|Lead Generation|Customer Service|Account Management|Business Development|Market Research|Presentation|Excel','sales'),
 'hr':entry('HR','Recruitment|HR Management|Payroll|Scheduling|Record Keeping|Training|Confidentiality|Excel|Office Administration|Compliance','people'),
 'business-finance':entry('Finance','Accounting|Financial Analysis|Budgeting|Excel|Auditing|Financial Reporting|Risk Management|Reconciliation|Financial Modeling|Taxation','finance'),
 'business-operations':entry('Operations','Inventory Management|Supply Chain|Logistics|Project Management|Quality Assurance|Process Optimization|Scheduling|Excel|Safety Procedures|Documentation','operations'),
 'ui-ux':entry('UI / UX','Accessibility|Figma|User Research|Wireframing|Prototyping|UI/UX|Responsive Design|Graphic Design|Presentation|Research','creative'),
 'graphic':entry('Graphic Design','Graphic Design|Adobe Suite|Typography|Color Theory|Figma|Content Writing|Presentation|Prototyping|Video Editing|Research','creative'),
 'product-design':entry('Product Design','Prototyping|User Research|Figma|Wireframing|Accessibility|UI/UX|Graphic Design|Market Research|Presentation|Research','creative'),
 'mechanical':entry('Mechanical','Thermodynamics|SolidWorks|AutoCAD|MATLAB|GD&T|Manufacturing|Maintenance|Safety Procedures|Quality Assurance|CAD','operations'),
 'civil':entry('Civil','Structural Analysis|AutoCAD|STAAD Pro|Surveying|Project Management|Safety Procedures|CAD|Quality Assurance|Excel|Documentation','operations'),
 'electrical':entry('Electrical','Circuit Design|Power Systems|PLC Programming|MATLAB|Maintenance|Safety Procedures|AutoCAD|Testing|Quality Assurance|Documentation','operations'),
 'electronics':entry('Electronics','Circuit Design|Digital Electronics|Embedded Systems|MATLAB|Testing|Debugging|C++|Python|Safety Procedures|Documentation','operations'),
 'accounting':entry('Accounting','Accounting|Bookkeeping|Reconciliation|Auditing|Taxation|Excel|Financial Reporting|Tally|SAP|Budgeting','finance'),
 'financial-analysis':entry('Financial Analysis','Financial Modeling|Financial Analysis|Statistics|Excel|Budgeting|Financial Reporting|Risk Management|Accounting|Power BI|Research','finance'),
 'banking':entry('Banking','Financial Analysis|Risk Management|Accounting|Compliance|Reconciliation|Excel|Customer Service|Financial Reporting|Confidentiality|Research','finance'),
 'marketing':entry('Marketing','SEO|Content Strategy|Digital Marketing|Campaign Management|Analytics|Market Research|Content Writing|Social Media|Copywriting|CRM','creative'),
 'sales-track':entry('Sales','CRM|Sales|Negotiation|Lead Generation|Customer Service|Account Management|Business Development|Presentation|Market Research|Excel','sales'),
 'logistics':entry('Logistics / Supply Chain','Inventory Management|Supply Chain|Logistics|Scheduling|Excel|Quality Assurance|Safety Procedures|Record Keeping|Process Optimization|Procurement','operations'),
 'project-operations':entry('Project Operations','Project Management|Scheduling|Process Optimization|Quality Assurance|Excel|Risk Management|Documentation|Budgeting|Supply Chain|Safety Procedures','operations'),
 'clinical':entry('Clinical — example bank only','Patient Support|Medical Terminology|Infection Prevention|Care Coordination|Health Records|Confidentiality|Safety Procedures|Record Keeping|Quality Assurance|Documentation','healthcare'),
 'health-admin':entry('Healthcare Administration','Health Records|Scheduling|Confidentiality|Medical Terminology|Care Coordination|Record Keeping|Customer Service|Excel|Office Administration|Quality Assurance','healthcare'),
 'health-it':entry('Healthcare IT','Health Records|SQL|Confidentiality|Networking|Cybersecurity|Data Entry|Quality Assurance|Documentation|Testing|Medical Terminology','healthcare'),
 'general':entry('General / Cross-functional','Computer Literacy|Excel|Research|Writing|Presentation|Scheduling|Record Keeping|Customer Service|Documentation|Data Entry','other'),
 'education-track':entry('Education / Training','Assessment Design|Teaching|Lesson Planning|Curriculum Development|Classroom Management|Student Support|Training|Research|Presentation|Record Keeping','education'),
 'legal-support':entry('Legal / Compliance Support','Contract Review|Legal Research|Compliance|Record Keeping|Confidentiality|Case Management|Risk Management|Writing|Research|Office Administration','legal'),
}
# Approved authoritative-bank configuration; no scoring or routing changes.
FIELDS['business']['tracks'].append('business-development')
ASSESSMENT_TRACKS['business-development']=entry('Business Development','','sales')
ASSESSMENT_TRACKS['business-development']['skills']=[]
_IMPORTED_BANK_SKILLS = {'data-ml': ['Python for Data Science', 'SQL', 'NumPy', 'Pandas', 'Data Cleaning', 'Exploratory Data Analysis', 'Statistics', 'Data Visualization', 'Feature Engineering', 'Machine Learning', 'Model Evaluation', 'Deep Learning', 'NLP', 'Model Deployment', 'Git / ML Workflow', 'Data Cleaning / EDA', 'Data Engineering / SQL', 'EDA', 'Hypothesis Testing'], 'health-admin': ['Patient Support', 'Healthcare Administration', 'Patient Scheduling', 'Medical Records', 'Patient Communication', 'Healthcare Data Management', 'Confidentiality & Privacy', 'Insurance & Billing Support', 'Patient Intake', 'Clinical Documentation Support', 'Healthcare Quality', 'Patient Safety', 'Referral Coordination', 'Healthcare Technology', 'Healthcare Workflow', 'Medical Records / Data', 'Patient Safety / Quality', 'Scheduling / Referral Coordination', 'Healthcare Support / Project Verification'], 'legal-support': ['Legal Research', 'Legal Writing', 'Contract Management', 'Contract Review', 'Compliance Management', 'Regulatory Research', 'Risk & Compliance Analysis', 'Policy Development', 'Legal Documentation', 'Due Diligence', 'Corporate Governance', 'Privacy & Data Protection', 'Compliance Auditing', 'Regulatory Compliance', 'Dispute / Issue Management', 'Contract Review / Management', 'Legal / Compliance Risk', 'Due Diligence / Governance', 'Compliance / Regulatory Research', 'Risk Analysis', 'Legal Risk Analysis', 'Compliance Risk Analysis', 'Risk Management', 'Compliance Governance', 'Governance / Privacy', 'Legal / Compliance Project Verification'], 'hr': ['Talent Acquisition', 'Recruitment Sourcing', 'Interviewing', 'Employee Relations', 'Performance Management', 'Learning and Development', 'Training Needs Analysis', 'Compensation and Benefits', 'HR Analytics', 'Workforce Planning', 'Employee Engagement', 'HR Policies', 'Onboarding', 'HR Information Systems', 'Conflict Resolution', 'Job Analysis', 'Recruitment Screening', 'Candidate Experience', 'Selection', 'Interview Evaluation', 'Performance Management / Engagement', 'Training Evaluation', 'HR Analytics / Project Verification'], 'business-development': ['Business Development', 'Lead Generation', 'Lead Qualification', 'Market Expansion', 'Partnership Development', 'Client Relationship Management', 'Sales Prospecting', 'Business Pitching', 'Negotiation', 'Competitive Analysis', 'Proposal Development', 'Account Growth', 'CRM Management', 'Revenue Opportunity Analysis', 'Strategic Partnerships', 'Lead Generation / Prospecting', 'Competitive / Account Strategy', 'Strategic Business Development', 'Business Development Strategy', 'Business Development / Project Verification']}
for _track,_skills in _IMPORTED_BANK_SKILLS.items():
 ASSESSMENT_TRACKS[_track]['skills']=list(dict.fromkeys([*ASSESSMENT_TRACKS[_track]['skills'],*_skills]))
# Exact source labels from MARKETING_TRACK_QUESTION_BANK.md. Existing labels are retained.
ASSESSMENT_TRACKS['marketing']['skills']=list(dict.fromkeys([
 *ASSESSMENT_TRACKS['marketing']['skills'],
 'Digital Marketing','Market Research','Search Engine Optimization','Search Engine Marketing',
 'Social Media Marketing','Content Marketing','Email Marketing','Marketing Analytics',
 'Customer Segmentation','Brand Management','Campaign Management','Conversion Rate Optimization',
 'Marketing Strategy','Customer Research','Marketing Communications','SEO / SEM',
 'Social / Content Marketing','SEO','Paid Search','A/B Testing',
 'Marketing Analytics / Project Verification','Marketing Strategy / Project Verification',
]))
# Exact labels from the authored Frontend source; no aliases or score changes.
ASSESSMENT_TRACKS['frontend']['skills']=list(dict.fromkeys([
 *ASSESSMENT_TRACKS['frontend']['skills'],
 'HTML','CSS','JavaScript','React','TypeScript','Responsive Design','State Management',
 'API Integration','Accessibility','Git','Debugging','Performance','Forms & Validation',
 'Testing','UI Component Design','HTML/CSS','Project-Informed React','Project-Informed API Integration',
]))
for field,config in FIELDS.items():
 for track in config['tracks']:ASSESSMENT_TRACKS[track]['field']=field
