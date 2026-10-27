import React,{useState} from 'react';
import {LayoutDashboard,Users,GraduationCap,FileCheck2,BriefcaseBusiness,ArrowUpRight,LogOut} from 'lucide-react';
import './PartnerLayout.css';

export default function PartnerLayout({user,onLogout,connections,internships,documents,recruitment}){
 const faculty=user.role==='faculty';
 const sections=faculty?[
  {id:'connections',title:'Connections',icon:Users,description:'Publish your expertise, explore industry requests and follow your interests.',action:'Explore connections'},
  {id:'mentoring',title:'Internship mentoring',icon:GraduationCap,description:'Support your assigned students with feedback and internship updates.',action:'View assigned internships'},
  {id:'documents',title:'Document review',icon:FileCheck2,description:'Review documents shared by students in your verified institution.',action:'Review student documents'}
 ]:[
  {id:'recruitment',title:'Student recruitment',icon:BriefcaseBusiness,description:'Post a role, compare shared assessments and manage your shortlist.',action:'Manage recruitment'},
  {id:'connections',title:'Faculty connections',icon:Users,description:'Post collaboration requests, find expertise and review faculty responses.',action:'Explore connections'}
 ];
 const [active,setActive]=useState('overview');
 const [visited,setVisited]=useState([]);
 function navigate(id){setActive(id);setVisited(previous=>previous.includes(id)?previous:[...previous,id]);}
 const current=sections.find(s=>s.id===active);
 const content={connections,mentoring:internships,documents,recruitment};
 return <div className="partner-organized">
  <aside className="partner-rail">
   <a className="brand" href="/">bridge<span className="brand-dot">.</span></a>
   <div className="partner-role"><span className="partner-symbol">{faculty?<GraduationCap/>:<BriefcaseBusiness/>}</span><div><strong>{faculty?'Faculty':'Industry'} workspace</strong><small>{user.organization||'Your collaboration workspace'}</small></div></div>
   <p className="eyebrow">YOUR WORKSPACE</p>
   <nav aria-label={`${user.role} workspace`}>
    {[{id:'overview',title:'Overview',icon:LayoutDashboard},...sections].map(({id,title,icon:Icon})=><button type="button" key={id} className={active===id?'active':''} aria-current={active===id?'page':undefined} onClick={()=>navigate(id)}><Icon size={20}/><span>{title}</span></button>)}
   </nav>
   <div className="partner-rail-note"><strong>{faculty?'Help the next step happen.':'Build your next partnership.'}</strong><p>{faculty?'Your expertise connects learning with real experience.':'Connect student potential and faculty expertise with your team.'}</p></div>
  </aside>
  <div className="partner-body">
   <header className="partner-top"><div className="partner-breadcrumb">Workspace <span>/</span> <strong>{current?.title||'Overview'}</strong></div><div className="partner-account"><span>{user.name}</span><button className="button secondary" type="button" onClick={onLogout}><LogOut size={16}/>Sign out</button></div></header>
   <main className="partner-content">
    <div hidden={active!=='overview'}>
     <div className="partner-page-heading"><span className="eyebrow">{faculty?'EXPERTISE WITH PURPOSE':'PEOPLE MEET POSSIBILITY'}</span><h1>{faculty?'Make room for what comes next.':'Find the people to move forward.'}</h1><p>{faculty?'Your collaborations, student mentoring and document reviews, in one workspace.':'Recruit students and build faculty partnerships, with a clear place for each.'}</p></div>
     <section className="partner-hero"><div><span className="eyebrow">{faculty?'FROM CLASSROOM TO COLLABORATION':'FROM POTENTIAL TO OPPORTUNITY'}</span><h2>{faculty?'Share what you know.\nShape what comes next.':'A stronger team starts\nwith the right connection.'}</h2><p>{faculty?'Explore industry opportunities and bring practical experience back to your students.':'Create a student role or work with faculty on your next practical challenge.'}</p><button className="button primary" type="button" onClick={()=>navigate(sections[0].id)}>{sections[0].action}<ArrowUpRight size={18}/></button></div><div className="partner-hero-art" aria-hidden="true"><span/><span/><span/><span className="partner-hero-glyph">✳</span></div></section>
     <div className="partner-section-heading"><h2>Your workspace</h2><p>Choose what you want to work on.</p></div>
     <div className="partner-action-grid">{sections.map(({id,title,description,action,icon:Icon})=><button key={id} type="button" className="partner-action-card" onClick={()=>navigate(id)}><span className="partner-symbol"><Icon size={24}/></span><h3>{title}</h3><p>{description}</p><span className="partner-card-link">{action}<ArrowUpRight size={18}/></span></button>)}</div>
    </div>
    {sections.map(section=>visited.includes(section.id)&&<div key={section.id} hidden={active!==section.id} className="partner-work-section"><div className="partner-section-heading"><div><span className="eyebrow">{faculty?'FACULTY':'INDUSTRY'} WORKSPACE</span><h1>{section.title}</h1><p>{section.description}</p></div></div>{content[section.id]}</div>)}
   </main>
  </div>
 </div>;
}
