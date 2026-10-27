import introUrl from './assets/bridge-opening.mp3';

// User-supplied opening sound. Audio must never block authentication.
export function createIntroSound(){
 let context,decoded,source,gain,playing=false,disposed=false;
 const bytes=fetch(introUrl).then(response=>{
  if(!response.ok)throw new Error('Opening audio unavailable');
  return response.arrayBuffer();
 }).catch(()=>null);
 function unlock(){
  try{
   const Audio=window.AudioContext||window.webkitAudioContext;
   if(!Audio||disposed)return;
   context??=new Audio();
   void context.resume().catch(()=>{});
   decoded??=bytes.then(data=>data?context.decodeAudioData(data):null).catch(()=>null);
  }catch{}
 }
 async function play(){
  if(!context||disposed)return;
  playing=true;
  try{
   const buffer=await decoded;
   if(!buffer||!playing||disposed||context.state!=='running')return;
   // Peak normalization keeps the supplied recording clear without clipping.
   let peak=0;
   for(let channel=0;channel<buffer.numberOfChannels;channel++){
    const samples=buffer.getChannelData(channel);
    for(let i=0;i<samples.length;i++)peak=Math.max(peak,Math.abs(samples[i]));
   }
   source=context.createBufferSource();source.buffer=buffer;
   gain=context.createGain();gain.gain.value=peak?Math.min(4,.95/peak):1;
   source.connect(gain);gain.connect(context.destination);source.start();
  }catch{}
 }
 function stop(){
  playing=false;disposed=true;
  try{source?.stop();source?.disconnect();gain?.disconnect()}catch{}
  if(context)void context.close().catch(()=>{});
 }
 return {unlock,play,stop};
}
