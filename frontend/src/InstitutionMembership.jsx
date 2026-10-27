import React,{useEffect,useState} from 'react';
import {sessionApi} from './AccountsConnector';

export default function InstitutionMembership(){
 const [data,setData]=useState({institutions:[],accounts:[]}),[name,setName]=useState(''),[choices,setChoices]=useState({}),[busy,setBusy]=useState(false),[error,setError]=useState(''),[message,setMessage]=useState('');
 async function load(){const result=await sessionApi('/owner/institutions');setData(result);setChoices(Object.fromEntries(result.accounts.map(a=>[a.id,a.institution_id||''])));}
 useEffect(()=>{load().catch(e=>setError(e.message));},[]);
 async function create(e){e.preventDefault();setBusy(true);setError('');setMessage('');try{await sessionApi('/owner/institutions',{name});setName('');await load();setMessage('Institution created. Assign its accounts below.');}catch(e){setError(e.message)}finally{setBusy(false)}}
 async function assign(a){setBusy(true);setError('');setMessage('');try{await sessionApi('/owner/institutions/members/'+encodeURIComponent(a.id),{institution_id:choices[a.id]||null},'PUT');await load();setMessage('Verified membership updated for '+a.name+'.');}catch(e){setError(e.message)}finally{setBusy(false)}}
 return <section className="panel"><h2>Institution membership</h2><p>Assign membership only after checking the account’s affiliation. Display organization text does not grant access. Faculty can download and review documents of students assigned to the same institution.</p>
 <form onSubmit={create}><label>New institution name<input value={name} onChange={e=>setName(e.target.value)} required maxLength={150}/></label><button className="button secondary" disabled={busy}>Create institution</button></form>
 {error&&<p role="alert" className="error">{error}</p>}{message&&<p role="status">{message}</p>}
 {data.accounts.map(a=><article className="portfolio-item" key={a.id}><div><h3>{a.name} · {a.role}</h3><p>{a.email}</p><small>Display organization: {a.organization||'Not provided'}</small></div><div className="portfolio-actions"><label>Verified institution for {a.email}<select value={choices[a.id]||''} onChange={e=>setChoices({...choices,[a.id]:e.target.value})} disabled={busy}><option value="">Unassigned — no institution access</option>{data.institutions.map(i=><option key={i.id} value={i.id}>{i.name}</option>)}</select></label><button className="button secondary" disabled={busy||(choices[a.id]||'')===(a.institution_id||'')} onClick={()=>assign(a)}>Save membership</button></div></article>)}
 </section>;
}
