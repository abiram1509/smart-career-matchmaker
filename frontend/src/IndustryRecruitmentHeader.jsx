import React from 'react';
import {BriefcaseBusiness,ClipboardCheck,Plus,RefreshCw} from 'lucide-react';
import './IndustryRecruitment.css';

export default function IndustryRecruitmentHeader({roles,loading,busy,view,onView,selectedTitle,review,onRefresh}){
 return <>
  <div className="industry-recruitment-hero"><div><span className="eyebrow">FROM SKILLS TO YOUR SHORTLIST</span><h2>Find potential. Make an informed decision.</h2><p>Post the skills your team needs and review students who choose to share their assessment with you.</p><button className="button primary" onClick={()=>onView('post')}><Plus size={17} aria-hidden="true"/>Post a role</button></div><div className="industry-summary"><div><BriefcaseBusiness size={22} aria-hidden="true"/><strong>{loading?'—':roles.filter(role=>role.status==='open').length}</strong><span>Open roles</span></div><div><ClipboardCheck size={22} aria-hidden="true"/><strong>{loading?'—':roles.filter(role=>role.status==='closed').length}</strong><span>Closed roles</span></div></div></div>
  <ol className="industry-recruitment-steps"><li><span>01</span><div><strong>Define the role</strong><p>Set required skills and eligibility.</p></div></li><li><span>02</span><div><strong>Review shared profiles</strong><p>Compare assessment evidence.</p></div></li><li><span>03</span><div><strong>Record your decision</strong><p>Shortlist and track your reviews.</p></div></li></ol>
  <div className="industry-section-nav"><div aria-label="Recruitment sections">{[['roles','Your roles'],['post','Post a role'],['review','Applicant review']].map(([id,title])=><button key={id} type="button" aria-pressed={view===id} onClick={()=>onView(id)}>{title}</button>)}</div><button className="button secondary" disabled={busy||loading} onClick={onRefresh}><RefreshCw size={16} aria-hidden="true"/>Refresh</button></div>
  {view==='review'&&selectedTitle&&<div className="industry-review-summary"><div><span>REVIEWING</span><h3>{selectedTitle}</h3></div>{review?.metrics&&<div className="industry-review-counts"><span><strong>{review.metrics.applicants}</strong> applicants</span><span><strong>{review.metrics.unreviewed}</strong> unreviewed</span><span><strong>{review.metrics.shortlisted}</strong> shortlisted</span></div>}<button className="text-button" onClick={()=>onView('roles')}>Choose another role</button></div>}
 </>;
}
