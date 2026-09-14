import React,{useEffect,useRef,useState} from 'react';
import {sessionApi} from './AccountsConnector';

export default function Portfolio({reviewer=false}){
 const [items,setItems]=useState([]),[title,setTitle]=useState(''),[file,setFile]=useState(null),[busy,setBusy]=useState(false),[loading,setLoading]=useState(true),[error,setError]=useState(''),[message,setMessage]=useState(''),[offset,setOffset]=useState(0);
 const input=useRef(null);
 async function load(){setLoading(true);try{setItems(await sessionApi('/portfolio?offset='+offset))}catch(e){setError(e.message)}finally{setLoading(false)}}
 useEffect(()=>{load()},[offset]);
 async function upload(e){e.preventDefault();setError('');setMessage('');if(!file||!file.size||file.size>5*1024*1024){setError('Choose a non-empty file up to 5 MB.');return}setBusy(true);try{
  const encoded=await new Promise((resolve,reject)=>{const reader=new FileReader();reader.onload=()=>resolve(String(reader.result).split(',')[1]);reader.onerror=()=>reject(new Error('Could not read the file.'));reader.readAsDataURL(file)});
  await sessionApi('/portfolio/upload',{title,filename:file.name,content_base64:encoded});setTitle('');setFile(null);if(input.current)input.current.value='';await load();setMessage('Document uploaded as self-reported.');
 }catch(e){setError(e.message)}finally{setBusy(false)}}
 async function verify(item){setBusy(true);setError('');setMessage('');try{await sessionApi('/portfolio/'+item.id+'/status',{status:item.status==='verified'?'self-reported':'verified'},'PATCH');await load();setMessage('Document status updated.')}catch(e){setError(e.message)}finally{setBusy(false)}}
 return <section className="panel portfolio-panel"><h2>{reviewer?'Document review':'My document portfolio'}</h2><p>{reviewer?'Download a document before marking it verified. Verification records your manual review.':'Add certificates and project documents. Your files are private to you and the platform administrator.'} Document status does not affect quiz scores or job matches.</p>
 {!reviewer&&<form onSubmit={upload} className="portfolio-upload"><label>Document title<input required maxLength={150} value={title} onChange={e=>setTitle(e.target.value)}/></label><label>Document file<input ref={input} type="file" required accept=".pdf,.png,.jpg,.jpeg,.txt,.zip,.docx" onChange={e=>setFile(e.target.files?.[0]||null)}/></label><small>PDF, PNG, JPG, UTF-8 TXT, ZIP or DOCX. Up to 5 MB each; 30 documents per account.</small><button className="button primary" disabled={busy}>{busy?'Saving…':'Upload document'}</button></form>}
 {error&&<p role="alert" className="error">{error}</p>}{message&&<p role="status">{message}</p>}{loading&&<p role="status">Loading documents…</p>}
 {!loading&&!items.length&&!error&&<p>No documents uploaded yet.</p>}
 {items.map(item=><article className="portfolio-item" key={item.id}><div><h3>{item.title}</h3>{reviewer&&<p>{item.student_name}</p>}<small>{item.original_name} · {Math.ceil(item.size_bytes/1024)} KB · {new Date(item.uploaded_at).toLocaleDateString()}</small><p><span className={'portfolio-badge '+(item.status==='verified'?'verified':'')}>{item.status==='verified'?'Verified by administrator':'Self-reported'}</span></p>{item.verified_at&&<small>Reviewed {new Date(item.verified_at).toLocaleDateString()}</small>}</div><div className="portfolio-actions"><a className="button secondary" href={item.download_url}>Download</a>{reviewer&&<button className="button secondary" disabled={busy} onClick={()=>verify(item)}>{item.status==='verified'?'Mark self-reported':'Mark verified'}</button>}</div></article>)}
 {reviewer&&<div className="portfolio-actions"><button className="button secondary" disabled={!offset||busy} onClick={()=>setOffset(Math.max(0,offset-100))}>Previous</button><button className="button secondary" disabled={items.length<100||busy} onClick={()=>setOffset(offset+100)}>Next</button><button className="button secondary" disabled={busy||loading} onClick={load}>Refresh documents</button></div>}
 </section>
}
