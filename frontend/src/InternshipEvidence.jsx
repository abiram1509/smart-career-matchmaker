import React,{useState} from 'react';
import {sessionApi} from './AccountsConnector';
import './InternshipEvidence.css';

export default function InternshipEvidence({item,mentor,busy,act}){
 const [rejecting,setRejecting]=useState(false),[reason,setReason]=useState('');
 const documents=item.documents||[];
 function upload(event){
  event.preventDefault();const form=event.currentTarget;const fields=new FormData(form);const file=fields.get('file');
  act(async()=>{
   if(!file?.size||file.size>5*1024*1024)throw new Error('Choose a non-empty file up to 5 MB.');
   const content=await new Promise((resolve,reject)=>{const reader=new FileReader();reader.onload=()=>resolve(String(reader.result).split(',')[1]);reader.onerror=()=>reject(new Error('Could not read the file.'));reader.readAsDataURL(file)});
   await sessionApi('/internships/'+item.id+'/documents',{title:String(fields.get('title')).trim(),filename:file.name,content_base64:content});form.reset();
  },'Evidence submitted. Your assigned mentor can now download and review it.');
 }
 function reject(event){event.preventDefault();act(async()=>{await sessionApi('/internships/'+item.id+'/status',{status:'rejected',reason:reason.trim()},'PATCH');setRejecting(false);setReason('')},'Internship rejected. The reason is visible to the student.');}
 return <div className="internship-evidence">
  {item.status==='rejected'&&<div className="internship-rejection"><strong>REJECTED</strong><p>{item.rejection_reason}</p><small>Mentor decision{item.rejected_at?' · '+new Date(item.rejected_at).toLocaleString():''}. Evidence and feedback are retained.</small></div>}
  <div className="internship-evidence-heading"><h4>Supporting documents</h4><span className="internship-evidence-count">{documents.length} submitted</span></div>
  <p>Upload an internship report, thesis, resume or completion letter. Submission is evidence for manual mentor review, not automatic proof of completion.</p>
  {documents.length?<ul className="internship-document-list">{documents.map(document=><li key={document.id}><div><strong>{document.title}</strong><small>{document.original_name} · {Math.ceil(document.size_bytes/1024)} KB · Submitted {new Date(document.uploaded_at).toLocaleString()}</small></div><a className="button secondary" href={document.download_url}>Download</a></li>)}</ul>:<p className="internship-no-evidence">No supporting documents submitted yet.</p>}
  {!mentor&&item.status==='ongoing'&&<form className="internship-form" onSubmit={upload}><label>Document title<input name="title" required maxLength={150} placeholder="Final internship report"/></label><label>Supporting file<input name="file" type="file" required accept=".pdf,.docx,.txt,.png,.jpg,.jpeg"/></label><small>PDF, DOCX, TXT, PNG or JPG. Up to 5 MB per file; 20 files per internship. Shared only with your assigned mentor. Avoid sensitive personal or confidential information.</small><button className="button primary" disabled={busy||documents.length>=20}>Submit evidence</button></form>}
  {!mentor&&item.status!=='ongoing'&&<p>Uploads are closed. Ask your mentor to reopen the internship if more evidence is needed.</p>}
  {mentor&&<div className="internship-review-actions"><p>Review the supporting documents and your feedback before recording a decision. You may request further evidence through mentor feedback.</p><div className="internship-decision-buttons"><button type="button" className="button secondary" disabled={busy} onClick={()=>act(()=>sessionApi('/internships/'+item.id+'/status',{status:item.status==='ongoing'?'completed':'ongoing'},'PATCH'),'Internship status updated.')}>{item.status==='ongoing'?'Mark completed':item.status==='rejected'?'Reopen internship':'Mark ongoing'}</button>{item.status!=='rejected'&&<button type="button" data-status-tone="negative" className="button internship-reject-button" disabled={busy} onClick={()=>setRejecting(!rejecting)}>{rejecting?'Cancel rejection':'Reject internship'}</button>}</div>{rejecting&&item.status!=='rejected'&&<form className="internship-form internship-rejection-form" onSubmit={reject}><label>Reason for rejection<textarea required maxLength={1500} value={reason} onChange={event=>setReason(event.target.value)} placeholder="Explain why the internship is being rejected or discontinued."/></label><p>The student will see REJECTED and this reason. Existing documents and feedback will remain available.</p><button data-status-tone="negative" className="button internship-reject-button" disabled={busy||!reason.trim()}>Confirm rejection</button></form>}</div>}
 </div>;
}
