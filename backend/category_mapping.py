"""Explicit broad-category mappings from the supplied addendum, not proficiency labels."""
CATEGORY_CODE_TO_FIELD_TRACK={
 'IT':('technology',['backend','frontend','data-ml','cloud-devops']), 'SALE':('sales',['sales-track']), 'MGMT':('operations',['project-operations']),
 'MNFC':('operations',['mechanical']), 'BD':('sales',['business-sales']), 'ENG':('operations',['mechanical','civil','electrical','electronics']),
 'OTHR':('other',['general']), 'HCPR':('healthcare',['clinical','health-admin']), 'FIN':('finance',['financial-analysis','banking']),
 'ACCT':('finance',['accounting']), 'MRKT':('creative',['marketing']), 'PRJM':('operations',['project-operations']), 'ADM':('people',['hr']),
 'ANLS':('finance',['financial-analysis']), 'RSCH':('education',['education-track']), 'HR':('people',['hr']), 'CUST':('sales',['sales-track']),
 'DSGN':('creative',['ui-ux','graphic','product-design']), 'EDU':('education',['education-track']), 'ART':('creative',['graphic']),
 'LGL':('legal',['legal-support']), 'CNSL':('operations',['project-operations']), 'GENB':('other',['general']), 'PR':('creative',['marketing']),
 'WRT':('creative',['marketing']), 'QA':('operations',['qa-testing']), 'ADVR':('creative',['marketing']), 'STRA':('operations',['project-operations']),
 'TRNG':('education',['education-track']), 'SUPL':('operations',['logistics']), 'PRDM':('operations',['project-operations']),
 'SCI':('education',['education-track']), 'PRCH':('operations',['logistics']), 'PROD':('operations',['mechanical']), 'DIST':('operations',['logistics'])}
_NAMES={
 'IT':['Python','SQL','Problem Solving'],'SALE':['Negotiation','CRM','Communication'],'MGMT':['Leadership','Project Management','Communication'],
 'MNFC':['Manufacturing','Quality Assurance','Safety Procedures'],'BD':['Business Development','Sales','Communication'],'ENG':['AutoCAD','MATLAB','Problem Solving'],
 'OTHR':['Computer Literacy','Communication'],'HCPR':['Patient Support','Medical Terminology','Confidentiality'],'FIN':['Financial Modeling','Excel','Accounting'],
 'ACCT':['Accounting','Excel','Auditing'],'MRKT':['SEO','Content Strategy','Analytics'],'PRJM':['Project Management','Scheduling','Communication'],
 'ADM':['Office Administration','Record Keeping','Scheduling'],'ANLS':['Statistics','Excel','Financial Analysis'],'RSCH':['Research','Statistics','Documentation'],
 'HR':['Recruitment','HR Management','Payroll'],'CUST':['Customer Service','Communication','CRM'],'DSGN':['Figma','Prototyping','User Research'],
 'EDU':['Teaching','Assessment Design','Lesson Planning'],'ART':['Graphic Design','Adobe Suite','Typography'],'LGL':['Legal Research','Contract Review','Confidentiality'],
 'CNSL':['Research','Presentation','Problem Solving'],'GENB':['Excel','Communication','Computer Literacy'],'PR':['Communication','Content Writing','Presentation'],
 'WRT':['Writing','Content Writing','Research'],'QA':['Testing','Quality Assurance','Documentation'],'ADVR':['Campaign Management','Copywriting','Analytics'],
 'STRA':['Project Management','Research','Risk Management'],'TRNG':['Training','Assessment Design','Presentation'],'SUPL':['Supply Chain','Inventory Management','Logistics'],
 'PRDM':['Project Management','Market Research','Prototyping'],'SCI':['Research','Statistics','Documentation'],'PRCH':['Procurement','Negotiation','Supply Chain'],
 'PROD':['Manufacturing','Quality Assurance','Safety Procedures'],'DIST':['Logistics','Inventory Management','Scheduling']}
# These are disclosed fallback assumptions about a category, never employer assertions.
CATEGORY_TO_SKILLS_TEMPLATE={code:{s:5 for s in names} for code,names in _NAMES.items()}
