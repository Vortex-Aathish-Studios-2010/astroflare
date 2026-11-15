  // Motion is progressive enhancement: never hide content before an observer or animation runs.
  const activeMotion=new Set();let sectionObserver=null,lastMotionStage=null;
  function playMotion(node,frames,options={}){
    if(!node||reducedMotion()||typeof node.animate!=='function')return;
    try{const animation=node.animate(frames,{duration:180,easing:'cubic-bezier(.2,.7,.2,1)',...options});activeMotion.add(animation);animation.finished?.then(()=>activeMotion.delete(animation),()=>activeMotion.delete(animation));return animation;}catch{return;}
  }
  function animateArrival(node){return playMotion(node,[{opacity:.72,transform:'translateY(5px)'},{opacity:1,transform:'none'}]);}
  function enhanceInterface(){
    const research=S.stage==='research',demo=research&&EXPLORER.mode!=='research';const nav={homeBtn:S.stage==='home',demoBtn:demo,researchBtn:research&&!demo,labsBtn:S.stage==='labs',missionBtn:!['home','research','labs'].includes(S.stage)};
    Object.entries(nav).forEach(([id,on])=>{const b=$(id);if(b){if(on)b.setAttribute('aria-current','page');else b.removeAttribute('aria-current');}});
    document.querySelectorAll('#stage details:not([id])').forEach((d,i)=>{const title=d.querySelector('summary')?.textContent||'notes';d.id='disclosure-'+S.stage+'-'+title.toLowerCase().replace(/[^a-z0-9]+/g,'-').slice(0,65)+'-'+i;});
    if(lastMotionStage===S.stage)return;lastMotionStage=S.stage;sectionObserver?.disconnect();
    if(S.stage==='home')document.querySelectorAll('.hero-copy h1,.hero-question,.hero-copy>.row').forEach((node,i)=>playMotion(node,[{opacity:.72,transform:'translateY(8px)'},{opacity:1,transform:'none'}],{duration:220,delay:i*45}));
    if(typeof IntersectionObserver!=='function'||reducedMotion())return;
    try{sectionObserver=new IntersectionObserver(entries=>entries.forEach(entry=>{if(entry.isIntersecting){sectionObserver.unobserve(entry.target);animateArrival(entry.target);}}),{threshold:.08});document.querySelectorAll('#stage>.card:not(.research-hero):not(.home-how),#stage>details.sec,.decision-layout').forEach(e=>sectionObserver.observe(e));}catch{sectionObserver=null;}
  }
  const motionPreference=typeof matchMedia==='function'?matchMedia('(prefers-reduced-motion: reduce)'):null;
  motionPreference?.addEventListener?.('change',e=>{if(e.matches){sectionObserver?.disconnect();activeMotion.forEach(a=>{try{a.cancel();}catch{}});activeMotion.clear();}});
  document.addEventListener('click',event=>{if(event.target.closest?.('#homeBtn,#researchBtn,#labsBtn,#missionBtn,#demoBtn,#stepper button,#context button'))collectVisibleDrafts();},true);
