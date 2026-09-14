"""Explicit alignment configuration. Shared candidates are withheld, never first-picked."""
import re

# Candidate pools, not approval to share an occupation across tracks.
POOLS = {
 'backend':['15-1251.00','15-1252.00','15-1254.00','15-1243.00'],
 'frontend':['15-1251.00','15-1252.00','15-1254.00','15-1255.00'],
 'data-ml':['15-2051.00','15-2041.00','15-1243.00'],
 'cloud-devops':['15-1241.00','15-1244.00','15-1242.00'],
 'qa-testing':['15-1253.00'],
 'business-marketing':['11-2021.00','13-1161.00'],
 'business-sales':['11-2022.00','41-3091.00'],
 'business-development':['11-2022.00','41-3091.00'],
 'hr':['11-3111.00','11-3121.00','11-3131.00','13-1071.00','13-1141.00','13-1151.00','43-4161.00'],
 'business-finance':['13-2011.00','13-2051.00'],
 'business-operations':['13-1081.00','13-1082.00'],
 'ui-ux':['15-1255.00'],
 'graphic':['27-1024.00'],
 'product-design':['27-1021.00','15-1255.00'],
 'mechanical':['17-2141.00','17-3027.00'],
 'civil':['17-2051.00','17-3022.00'],
 'electrical':['17-2071.00'],
 'electronics':['17-2072.00'],
 'accounting':['13-2011.00'],
 'financial-analysis':['13-2051.00'],
 'banking':['13-2041.00','13-2072.00'],
 'marketing':['11-2021.00','13-1161.00'],
 'sales-track':['11-2022.00','41-3091.00'],
 'logistics':['13-1081.00'],
 'project-operations':['13-1082.00'],
 'clinical':['31-9092.00'],
 'health-admin':['43-6013.00','29-2072.00'],
 'health-it':['29-9021.00','29-2072.00'],
 'general':['43-6014.00','43-6011.00'],
 'education-track':['25-2021.00','13-1151.00','11-3131.00'],
 'legal-support':['23-2011.00','43-6012.00','13-1041.00'],
}

# Explicit user decisions; these override candidate overlap without changing quiz tracks.
APPROVED = {
 '15-1251.00':['backend','frontend'], '15-1252.00':['backend','frontend'],
 '15-1254.00':['backend','frontend'], '15-1243.00':['backend','data-ml'],
 '11-2021.00':['marketing'], '13-1161.00':['marketing'],
 '11-2022.00':['sales-track'], '41-3091.00':['sales-track'],
 '15-1255.00':['frontend'],
 '11-3131.00':['hr'], '13-1151.00':['hr'],
 '29-2072.00':['health-admin','health-it'],
}
HELD = {
 '13-2011.00':'Finance occupation held by user until an authored track is available.',
 '13-2051.00':'Finance occupation held by user until an authored track is available.',
 '13-1081.00':'Operations occupation held by user until an authored track is available.',
 '13-1082.00':'Operations occupation held by user until an authored track is available.',
}
DEFERRED_INTERFACE_TRACKS = ['ui-ux','product-design']

def assignments():
    result={}
    for code,tracks in candidates().items():
        selected=APPROVED.get(code,tracks if len(tracks)==1 else [])
        if code in HELD: selected=[]
        if any(t not in tracks for t in selected): raise ValueError('Approval is outside reviewed candidates')
        if selected: result[code]=selected
    return result

# Same-product names only. Broad software classes do not prove specialised skill.
SOFTWARE = {
 'Python':['Python','Python for Data Science'], 'Microsoft Excel':['Excel'],
 'Structured query language SQL':['SQL'], 'SQL':['SQL'], 'JavaScript':['JavaScript'],
 'Hypertext markup language HTML':['HTML'], 'Cascading style sheets CSS':['CSS'],
 'React':['React'], 'React.js':['React'], 'TypeScript':['TypeScript'], 'Git':['Git'],
 'Docker':['Docker'], 'Kubernetes':['Kubernetes'], 'Linux':['Linux'],
 'Microsoft Azure':['Azure'], 'Amazon Web Services AWS software':['AWS'],
 'PostgreSQL':['PostgreSQL'], 'MongoDB':['MongoDB'], 'NumPy':['NumPy'],
 'Pandas':['Pandas'], 'TensorFlow':['TensorFlow'], 'Microsoft Power BI':['Power BI'],
 'Autodesk AutoCAD':['AutoCAD'], 'Dassault Systemes SolidWorks':['SolidWorks'],
 'The MathWorks MATLAB':['MATLAB'], 'MATLAB':['MATLAB'], 'Figma':['Figma'],
 'Selenium':['Selenium'], 'SAP software':['SAP'], 'C++':['C++'],
}

# Explicit user-approved occupation-specific proxies, not universal skill aliases.
# Only these two occupations and the marketing track may use them.
MARKETING_PROXY_CODES = {'11-2021.00','13-1161.00'}
MARKETING_SOFTWARE_PROXIES = {
 'Google Ads':['Digital Marketing','Search Engine Marketing'],
 'Marketo Marketing Automation':['Digital Marketing'],
 'Facebook':['Social Media Marketing'], 'Instagram':['Social Media Marketing'],
 'Constant Contact':['Email Marketing'], 'Oracle Eloqua':['Email Marketing'],
}
MARKETING_TASK_PROXIES = {
 '5433':['Customer Segmentation'],
 '20709':['Campaign Management'], '961':['Campaign Management'],
}
# Final decisions: never infer these from CMS, generic communications or ad tools.
MARKETING_UNMAPPED = {
 'Content Marketing':'rejected: CMS usage is too generic',
 'Marketing Communications':'rejected: measuring effectiveness does not establish creation/management',
 'Search Engine Optimization':'unsupported: no explicit SEO evidence',
 'Brand Management':'unsupported: no specific brand-management evidence',
 'Conversion Rate Optimization':'unsupported: no specific conversion-optimization evidence',
}

# Scoped task evidence: task IDs and exact Astra labels, not invented questions/aliases.
TASK_SKILLS = {
 # Marketing: direct rated task evidence only, not broad software-to-competency aliases.
 # 11-2021.00: develop/evaluate marketing strategy; initiate market research studies.
 '951':['Marketing Strategy'], '963':['Market Research'],
 # 13-1161.00: research consumer opinions; analyze customer needs/buying habits;
 # measure marketing effectiveness; analyze marketing/sales trends.
 '5439':['Market Research','Customer Research'], '5433':['Customer Research'],
 '5438':['Marketing Analytics'], '5436':['Marketing Analytics'],
 '18861':['HR Policies'], '18852':['Employee Relations'],
 '18868':['Recruitment Screening'], '18871':['Selection'], '18870':['Onboarding'],
 '18862':['Interviewing'], '18865':['Recruitment Sourcing'],
 '18853':['HR Analytics'], '18858':['Talent Acquisition'],
 '18866':['HR Information Systems'], '18874':['Recruitment Screening'],
 '982':['Performance Management','Compensation and Benefits'],
 '988':['Compensation and Benefits'], '992':['Training Needs Analysis'],
 '1000':['Workforce Planning'], '3366':['Job Analysis'],
 '1015':['Training Needs Analysis'], '1012':['Training Needs Analysis'],
 '103':['Training Needs Analysis'], '1014':['Learning and Development'],
 '1011':['Learning and Development'], '1009':['Training Evaluation'], '98':['Training Evaluation'],
 '21828':['Data Visualization'], '21837':['Model Evaluation'],
 '21827':['Model Evaluation'], '21826':['Data Cleaning'],
 '21824':['Feature Engineering'],
 '1636':['Legal Research'], '21062':['Legal Research'],
 '23994':['Contract Review','Legal Writing'], '18491':['Legal Documentation'],
 '21460':['Compliance Auditing'], '21461':['Regulatory Compliance'],
 '775':['Patient Scheduling'], '20438':['Patient Scheduling'],
 '788':['Insurance & Billing Support'], '780':['Patient Intake'],
 '781':['Medical Records'], '786':['Clinical Documentation Support'],
 '22886':['Confidentiality & Privacy'], '22878':['Medical Records'],
 '22882':['Healthcare Data Management'], '22885':['Patient Intake'],
}

def title_key(value):
    """Case/punctuation normalization and explicit seniority prefixes only; no fuzzy join."""
    text=re.sub(r'\s+',' ',str(value).casefold()).strip()
    text=re.sub(r'^(?:senior|junior|sr\.?|jr\.?)\s+','',text)
    return re.sub(r'[^\w+#]+',' ',text).strip()

def candidates():
    result={}
    for track,codes in POOLS.items():
        for code in codes: result.setdefault(code,[]).append(track)
    return result
