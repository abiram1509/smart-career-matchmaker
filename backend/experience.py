"""Preserve source experience and distinguish description mentions from requirements."""
import re

def describe_experience(row):
    explicit=row.get('experience_level') or row.get('job_experience_level') or row.get('formatted_experience_level')
    structured=row.get('job_required_experience')
    if isinstance(structured,dict):
        if structured.get('no_experience_required') is True:
            return {'experience_level':'No experience required','experience_basis':'Provider-stated requirement','experience_snippet':''}
        months=structured.get('required_experience_in_months')
        if isinstance(months,(int,float)) and not isinstance(months,bool) and 0<months<=600:
            amount=f'{months/12:g} years' if months>=12 else f'{months:g} months'
            return {'experience_level':amount+(' preferred' if structured.get('experience_preferred') else ' required'),'experience_basis':'Provider-stated requirement','experience_snippet':''}
    if explicit and str(explicit).strip().lower() not in {'not specified','not stated','not stated in source','none','nan','null'}:
        return {'experience_level':str(explicit),'experience_basis':row.get('experience_basis') or 'Source-listed level','experience_snippet':row.get('experience_snippet') or ''}
    combined=str(row.get('full_time_remote') or '')
    for level in ['Entry level','Associate','Mid-Senior level','Director','Executive','Internship']:
        if level.lower() in combined.lower():
            return {'experience_level':level,'experience_basis':'Source-listed level','experience_snippet':combined}
    text=str(row.get('description') or row.get('job_description') or row.get('job_details') or '')
    no_exp=re.search(r'\b(?:no (?:prior |previous |work )?experience (?:is )?(?:required|needed)|freshers? (?:are )?(?:welcome|eligible|can apply))\b',text,re.I)
    if no_exp:return {'experience_level':'No experience required','experience_basis':'Stated in description','experience_snippet':no_exp.group(0)}
    pattern=r'\b(\d{1,2}(?:\s*[-–]\s*\d{1,2})?\+?)\s+years?[\x27’]?(?:\s+of)?\s+(?:[\w-]+\s+){0,4}experience\b'
    mentions=list(re.finditer(pattern,text,re.I))
    if mentions:
        match=mentions[0]
        return {'experience_level':re.sub(r'\s+',' ',match.group(1))+' years mentioned','experience_basis':'Description mention; verify the full requirement','experience_snippet':text[max(0,match.start()-50):min(len(text),match.end()+80)].strip()}
    return {'experience_level':'Not stated in source','experience_basis':'Not available','experience_snippet':''}
