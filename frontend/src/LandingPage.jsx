import React,{useEffect,useRef,useState} from 'react';
import {ArrowUpRight,ArrowRight,Menu,X,MoveUpRight,ScanLine,Layers,Compass} from 'lucide-react';
import './LandingPage.css';

const links=[['How it works','how-it-works'],['For Students','for-students'],['For Institutions','for-institutions'],['For Industry','for-industry']];
const bars=[['Python',76],['SQL',62],['React',88],['Comms',70],['Analysis',82],['Teamwork',91]];
export function LandingEntry({children}){
 const [workspace,setWorkspace]=useState(()=>window.location.hash==='#workspace');
 useEffect(()=>{const update=()=>{setWorkspace(window.location.hash==='#workspace');window.scrollTo(0,0)};window.addEventListener('hashchange',update);return()=>window.removeEventListener('hashchange',update)},[]);
 return workspace?children:<LandingPage/>;
}
export default function LandingPage(){
 const [menuOpen,setMenuOpen]=useState(false);const menu=useRef(null),toggle=useRef(null),content=useRef(null);
 useEffect(()=>{
  if(!menuOpen)return;
  const oldOverflow=document.body.style.overflow;document.body.style.overflow='hidden';
  const previous=document.activeElement;if(content.current)content.current.inert=true;
  menu.current?.querySelector('button')?.focus();
  function keys(e){
   if(e.key==='Escape'){e.preventDefault();setMenuOpen(false)}
   if(e.key==='Tab'){const items=[...menu.current.querySelectorAll('a,button')];const first=items[0],last=items.at(-1);if(e.shiftKey&&document.activeElement===first){e.preventDefault();last.focus()}else if(!e.shiftKey&&document.activeElement===last){e.preventDefault();first.focus()}}
  }
  window.addEventListener('keydown',keys);
  const media=window.matchMedia('(min-width: 1001px)');const resize=()=>{if(media.matches)setMenuOpen(false)};media.addEventListener('change',resize);
  return()=>{document.body.style.overflow=oldOverflow;if(content.current)content.current.inert=false;window.removeEventListener('keydown',keys);media.removeEventListener('change',resize);if(previous?.isConnected)previous.focus()};
 },[menuOpen]);
 function section(e,id){e.preventDefault();setMenuOpen(false);requestAnimationFrame(()=>{const target=document.getElementById(id);target?.scrollIntoView({behavior:'instant'});target?.focus({preventScroll:true})})}
 const enter=()=>setMenuOpen(false);
 return <div className="scm-landing">
  <div ref={content}>
   <a className="scm-skip" href="#scm-main">Skip to content</a>
   <section className="scm-hero" aria-labelledby="scm-title">
    <div className="scm-atmosphere" aria-hidden="true"><div className="scm-orb scm-orb-one"/><div className="scm-orb scm-orb-two"/><div className="scm-grid"/></div>
    <header className="scm-nav">
     <a href="/" className="scm-brand scm-enter"><span className="scm-logo"><MoveUpRight aria-hidden="true" size={21}/></span><span>smart career<span className="scm-wordmark-bottom">matchmaker<span className="scm-brand-dot">.</span></span></span></a>
     <nav className="scm-nav-links scm-glass scm-enter" aria-label="Landing navigation">{links.map(([label,id])=><a key={id} href={'#'+id} onClick={e=>section(e,id)}>{label}</a>)}</nav>
     <div className="scm-nav-actions scm-glass scm-enter"><a className="scm-login" href="#workspace">Login</a><a className="scm-button scm-button-light scm-nav-cta" href="#workspace">Get started<ArrowUpRight aria-hidden="true" size={16}/></a></div>
     <button ref={toggle} className="scm-menu-toggle scm-glass" aria-label="Open navigation menu" aria-expanded={menuOpen} aria-controls="scm-mobile-menu" onClick={()=>setMenuOpen(true)}><Menu aria-hidden="true"/></button>
    </header>
    <main id="scm-main" className="scm-hero-content" tabIndex={-1}>
     <div className="scm-copy">
      <div className="scm-kicker scm-enter"><span className="scm-live-dot"/> LESS GUESSWORK. MORE DIRECTION.</div>
      <h1 id="scm-title" className="scm-enter">Find out what <br/>you’re really<br/><span>ready for.</span></h1>
      <p className="scm-subhead scm-enter">Assess your skills. Understand your gaps.<br className="scm-desktop-break"/> Explore opportunities that fit.</p>
      <div className="scm-cta-row scm-enter"><a href="#workspace" className="scm-button scm-button-light">Take the Assessment<ArrowUpRight aria-hidden="true" size={18}/></a><a href="#how-it-works" onClick={e=>section(e,'how-it-works')} className="scm-button scm-button-outline">See How It Works<ArrowRight aria-hidden="true" size={17}/></a></div>
      <p className="scm-cta-note scm-enter">Sign in or create an account to begin.</p>
      <div className="scm-proof scm-enter"><span><Layers size={15} aria-hidden="true"/>9 career fields</span><i aria-hidden="true"/><span>8 full authored assessment tracks</span></div>
     </div>
     <div className="scm-visual scm-enter">
      <div className="scm-card-halo" aria-hidden="true"/>
      <article className="scm-score-card scm-glass" aria-label="Illustrative skill match preview, not a real assessment">
       <div className="scm-card-top"><span className="scm-card-icon"><ScanLine aria-hidden="true" size={22}/></span><span className="scm-preview-badge">ILLUSTRATIVE PREVIEW</span><span className="scm-card-dots" aria-hidden="true">•••</span></div>
       <div className="scm-score-label">Skill Match Score</div>
       <div className="scm-score-row"><strong>82<span>%</span></strong><span className="scm-coverage">9 fields covered<ArrowUpRight aria-hidden="true" size={14}/></span></div>
       <p className="scm-score-caption">A clearer picture of your next step.</p>
       <div className="scm-chart" role="img" aria-label="Illustrative skill bars: Python, SQL, React, communication, analysis and teamwork. Example values only.">{bars.map(([label,height],i)=><div className="scm-chart-column" key={label}><div className="scm-chart-track"><div className="scm-chart-bar" style={{height:height+'%',animationDelay:(1100+i*30)+'ms'}}/></div><span>{label}</span></div>)}</div>
       <div className="scm-card-footer"><span className="scm-mini-mark"><Compass aria-hidden="true" size={17}/></span><div><strong>Understand the match.</strong><span>See the skills and gaps behind every result.</span></div><ArrowUpRight aria-hidden="true" size={17}/></div>
       <p className="scm-disclaimer">Example score and bars, not measured user data.<br/>Similarity is not a hiring probability.</p>
      </article>
      <div className="scm-floating-label scm-glass"><span className="scm-float-dot"/><span>Potential, with a little perspective.</span></div>
     </div>
    </main>
    <div className="scm-hero-bottom"><span>BUILT FOR YOUR NEXT CHAPTER</span><span>STUDENTS <i/> ACADEMIA <i/> INDUSTRY</span><a href="#how-it-works" onClick={e=>section(e,'how-it-works')} aria-label="Explore how it works">↓</a></div>
   </section>
   <section className="scm-explainer" id="how-it-works" tabIndex={-1}><div className="scm-section-heading"><p>FROM SELF-DISCOVERY TO YOUR NEXT STEP</p><h2>Know your skills.<br/>See where they can take you.</h2></div><div className="scm-steps">{[['01','Build your profile','Confidence, experience and eligible applied questions build a skill profile with evidence.'],['02','Understand your matches','Compare your skills with job requirements and explore the reasoning behind the similarity score.'],['03','Choose your next step','Explore learning resources, follow an external job link or opt in to an internal company role.']].map(([n,t,d])=><article key={n}><span>{n}</span><h3>{t}</h3><p>{d}</p></article>)}</div></section>
   <section className="scm-audiences" aria-label="Who it is for">{[['for-students','For Students','Find direction in your skills.','Assess your strengths, understand gaps and explore opportunities across disciplines.'],['for-institutions','For Institutions','See the bigger picture.','Explore protected, platform-wide aggregate assessment analytics. Institution-specific isolation is not yet available.'],['for-industry','For Industry','Start with clearer skill evidence.','Post roles, review consenting applicants and shortlist manually. Connect with faculty through collaboration requests.']].map(([id,label,title,copy])=><article id={id} tabIndex={-1} className="scm-glass" key={id}><span>{label}</span><h2>{title}</h2><p>{copy}</p><a href="#workspace">Enter the workspace<ArrowUpRight aria-hidden="true" size={17}/></a></article>)}</section>
   <footer className="scm-footer"><span>Smart Career Matchmaker · Prototype</span><p>Skill estimates support exploration. They are not credentials or guarantees of employment.</p><a href="#workspace">Open workspace <ArrowUpRight aria-hidden="true" size={15}/></a></footer>
  </div>
  <div ref={menu} id="scm-mobile-menu" className={'scm-mobile-overlay '+(menuOpen?'scm-menu-open':'')} aria-hidden={!menuOpen} inert={!menuOpen}>
   <div className="scm-mobile-top"><span>Smart Career Matchmaker</span><button aria-label="Close navigation menu" onClick={()=>setMenuOpen(false)}><X aria-hidden="true"/></button></div>
   <nav aria-label="Mobile landing navigation">{links.map(([label,id],i)=><a href={'#'+id} key={id} onClick={e=>section(e,id)}><span>0{i+1}</span>{label}<ArrowUpRight aria-hidden="true" size={23}/></a>)}</nav>
   <div className="scm-mobile-actions"><a href="#workspace" className="scm-button scm-button-outline" onClick={enter}>Login</a><a href="#workspace" className="scm-button scm-button-light" onClick={enter}>Get started<ArrowUpRight aria-hidden="true" size={18}/></a></div>
  </div>
 </div>
}
