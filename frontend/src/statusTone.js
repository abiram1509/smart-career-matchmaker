// Visual meaning only; never changes a stored status or workflow.
export function statusTone(value){
 const state=String(value||'').toLowerCase();
 if(['pending','received','self-reported','ongoing'].includes(state))return 'pending';
 if(['accepted','shortlisted','completed','verified','open'].includes(state))return 'positive';
 if(['rejected','declined','not_shortlisted','closed'].includes(state))return 'negative';
 return 'neutral';
}
