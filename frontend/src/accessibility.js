export function installDialogAccessibility(){
 let active=null,previous=null,inerted=[];
 const focusable=()=>active?[...active.querySelectorAll('button:not([disabled]),a[href],input:not([disabled]),select:not([disabled]),textarea:not([disabled]),summary,[tabindex="0"]')].filter(e=>e.getClientRects().length):[];
 const observer=new MutationObserver(()=>{
  const next=[...document.querySelectorAll('[role="dialog"][aria-modal="true"]')].at(-1)||null;
  if(next===active)return;
  inerted.forEach(e=>e.inert=false);inerted=[];
  if(active&&previous?.isConnected)previous.focus();
  active=next;
  if(!active)return;
  previous=document.activeElement;
  active.tabIndex=-1;
  for(let node=active;node?.parentElement&&node!==document.body;node=node.parentElement){for(const sibling of node.parentElement.children){if(sibling!==node&&!sibling.inert){sibling.inert=true;inerted.push(sibling)}}}
  (focusable()[0]||active).focus();
 });
 observer.observe(document.body,{childList:true,subtree:true});
 document.addEventListener('keydown',e=>{
  if(!active)return;
  if(e.key==='Escape'){e.preventDefault();active.querySelector('button[aria-label^="Close"]')?.click();return}
  if(e.key!=='Tab')return;
  const items=focusable(),first=items[0],last=items.at(-1);
  if(!first){e.preventDefault();active.focus()}
  else if(e.shiftKey&&(document.activeElement===first||document.activeElement===active)){e.preventDefault();last.focus()}
  else if(!e.shiftKey&&(document.activeElement===last||document.activeElement===active)){e.preventDefault();first.focus()}
 });
}
