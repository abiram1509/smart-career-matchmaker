"""Map RapidAPI JSearch responses to the application's normalized job schema."""
from .prepare_data import salary
from .experience import describe_experience

HOST='jsearch.p.rapidapi.com'

def adapt_jobs(payload):
    if not isinstance(payload,dict):raise ValueError('Invalid JSearch response.')
    data=payload.get('data')
    rows=data.get('jobs') if isinstance(data,dict) else data
    if not isinstance(rows,list):raise ValueError('JSearch response lacks job records.')
    if payload.get('status') not in (None,'OK'): raise ValueError('JSearch reported an unsuccessful response.')
    jobs=[]
    for row in rows:
        if not isinstance(row,dict):continue
        identity=row.get('job_id');title=row.get('job_title');description=row.get('job_description')
        if not identity or not isinstance(title,str) or not title.strip():continue
        work=row.get('job_employment_type') or next(iter(row.get('job_employment_types') or []),'')
        work_map={'FULLTIME':'Full-time','PARTTIME':'Part-time','CONTRACTOR':'Contract','CONTRACT':'Contract','INTERN':'Internship','INTERNSHIP':'Internship','TEMPORARY':'Contract'}
        work=work_map.get(str(work).replace('-','').replace(' ','').upper(),str(work) or 'Not specified')
        period={'YEAR':'YEARLY','MONTH':'MONTHLY','HOUR':'HOURLY'}.get(row.get('job_salary_period'),row.get('job_salary_period'))
        text,data=salary({'currency':row.get('job_salary_currency'),'pay_period':period,'min_salary':row.get('job_min_salary'),'max_salary':row.get('job_max_salary'),'med_salary':None})
        if data: data['basis']='Reported by JSearch; not a prediction'
        elif isinstance(row.get('job_salary'),str) and row['job_salary'].strip():text=row['job_salary'].strip()
        benefits=row.get('job_benefits')
        location=row.get('job_location') or ', '.join(str(row[k]) for k in ['job_city','job_state','job_country'] if row.get(k)) or 'Not specified'
        if row.get('job_is_remote') is True: location='Remote · '+location
        jobs.append({'id':'jsearch-'+str(identity),'title':title.strip(),'description':description if isinstance(description,str) else '',
            'company':row.get('employer_name') or 'Company not provided','location':location,'type':work,
            'url':row.get('job_apply_link') or row.get('job_google_link') or '',
            'salary':text,'salary_data':data,'benefits':[{'type':str(b).replace('_',' '),'inferred':False} for b in benefits] if isinstance(benefits,list) else [],
            **describe_experience(row),'provider_job_id':str(identity)})
    return jobs
