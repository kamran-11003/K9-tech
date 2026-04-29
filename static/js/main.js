/* ================================================================
   K9 Technologies — Main script
   Theme, nav, GSAP animations, particles, chat, voice & call.
================================================================ */

gsap.registerPlugin(ScrollTrigger, ScrollToPlugin);
const TA = "play none none reverse";
const st = (trigger, extra) => Object.assign({trigger, start:"top 85%", toggleActions:TA}, extra||{});

/* ─────────── NAV ─────────── */
window.addEventListener('scroll', () =>
  document.getElementById('navbar').classList.toggle('scrolled', window.scrollY > 50));
function toggleMenu(){document.getElementById('mobile-menu').classList.toggle('open')}
function closeMenu(){document.getElementById('mobile-menu').classList.remove('open')}

/* ─────────── THEME ─────────── */
(function initTheme(){
  applyTheme(localStorage.getItem('k9-theme') || 'dark');
})();
function applyTheme(t){
  document.documentElement.setAttribute('data-theme', t);
  const icon = document.getElementById('theme-icon');
  const lbl  = document.getElementById('theme-lbl');
  if(icon) icon.textContent = t === 'light' ? '🌙' : '☀️';
  if(lbl)  lbl.textContent  = t === 'light' ? 'Dark' : 'Light';
  localStorage.setItem('k9-theme', t);
}
function toggleTheme(){
  const cur = document.documentElement.getAttribute('data-theme') || 'dark';
  applyTheme(cur === 'dark' ? 'light' : 'dark');
}

/* ─────────── HERO + GENERIC ANIMATIONS ─────────── */
gsap.from('#navbar',{y:-80,opacity:0,duration:.9,ease:'power3.out',delay:.1});

gsap.timeline({defaults:{ease:'power3.out'}})
  .from('.hero-badge',{y:24,opacity:0,duration:.65,delay:.25})
  .from('.hero-title',{y:48,opacity:0,duration:.85},'-=.35')
  .from('.hero-sub',{y:32,opacity:0,duration:.7},'-=.55')
  .from('.hero-btns',{y:24,opacity:0,duration:.65},'-=.45')
  .from('.hero-stats .hs-item',{y:20,opacity:0,duration:.55,stagger:.1},'-=.4')
  .from('.hero-visual',{x:64,opacity:0,duration:1,ease:'power4.out'},'-=.75')
  .from('.hero-float',{y:-22,opacity:0,duration:.6,ease:'back.out(1.6)'},'-=.3');

gsap.to('.hero-bg',{yPercent:40,ease:'none',scrollTrigger:{trigger:'#hero',start:'top top',end:'bottom top',scrub:1.5}});
gsap.to('.hero-dots',{yPercent:22,ease:'none',scrollTrigger:{trigger:'#hero',start:'top top',end:'bottom top',scrub:2}});

gsap.utils.toArray('.hc-fill').forEach(bar=>{
  const target = bar.style.width || '80%';
  bar.style.width='0%';
  gsap.to(bar,{width:target,ease:'power2.inOut',scrollTrigger:{trigger:'#hero',start:'top top',end:'bottom 60%',scrub:1.2}});
});

gsap.utils.toArray('.fade-up').forEach(el=>{
  gsap.fromTo(el,{opacity:0,y:36},{opacity:1,y:0,duration:.7,ease:'power2.out',scrollTrigger:st(el)});
});

/* trust + tech */
gsap.fromTo('.tl',{opacity:0,y:14},{opacity:.55,y:0,duration:.5,stagger:.05,ease:'power2.out',scrollTrigger:st('.trust-inner')});
gsap.fromTo('.ts-item',{opacity:0,y:16},{opacity:.55,y:0,duration:.45,stagger:.07,ease:'power2.out',scrollTrigger:{trigger:'#techstack',start:'top 88%',toggleActions:TA}});

/* services / projects / testimonials — staggered with reverse */
function staggeredEntry(parent,sel,opts={}){
  const items = gsap.utils.toArray(`${parent} ${sel}`);
  gsap.set(items,{opacity:0,y:opts.y||44});
  ScrollTrigger.create({
    trigger:parent,start:opts.start||'top 82%',toggleActions:TA,
    onEnter:()=>gsap.to(items,{opacity:1,y:0,duration:.6,stagger:.09,ease:'power2.out',overwrite:'auto'}),
    onLeaveBack:()=>gsap.to(items,{opacity:0,y:opts.y||44,duration:.4,stagger:{each:.06,from:'end'},ease:'power2.in',overwrite:'auto'})
  });
}
staggeredEntry('#services','.svc');
staggeredEntry('#projects','.proj',{y:52,start:'top 80%'});
staggeredEntry('#testimonials','.testi',{y:44});

/* about */
gsap.fromTo('#about .label,#about h2,#about > .about-grid > div:first-child > p',{opacity:0,x:-30},{opacity:1,x:0,duration:.65,stagger:.1,ease:'power2.out',scrollTrigger:st('#about')});
gsap.fromTo('.ap',{opacity:0,x:-36},{opacity:1,x:0,duration:.55,stagger:.1,ease:'power2.out',scrollTrigger:st('.about-points',{start:'top 88%'})});
gsap.fromTo('.av-card',{opacity:0,scale:.92,y:30},{opacity:1,scale:1,y:0,duration:.75,ease:'back.out(1.4)',scrollTrigger:st('.av-card',{start:'top 88%'})});
gsap.fromTo('.avs',{opacity:0,scale:.82},{opacity:1,scale:1,duration:.5,stagger:.1,ease:'back.out(1.8)',scrollTrigger:st('.av-stats',{start:'top 90%'})});

/* metrics — count up */
gsap.set('.met',{opacity:0,y:30});
const metNums = gsap.utils.toArray('.met-num').map(el=>{
  const raw = el.textContent.trim();
  return {el, num: parseInt(raw.replace(/[^0-9]/g,''))||0, suf: raw.replace(/[0-9]/g,'')};
});
ScrollTrigger.create({
  trigger:'#metrics',start:'top 85%',toggleActions:TA,
  onEnter:()=>{
    gsap.to('.met',{opacity:1,y:0,duration:.6,stagger:.13,ease:'power2.out',overwrite:'auto'});
    metNums.forEach(({el,num,suf})=>{
      if(!num){el.textContent=suf;return;}
      const o={v:0};
      gsap.to(o,{v:num,duration:2,ease:'power2.out',overwrite:'auto',onUpdate:()=>el.textContent=Math.round(o.v)+suf});
    });
  },
  onLeaveBack:()=>{
    gsap.to('.met',{opacity:0,y:30,duration:.35,overwrite:'auto'});
    metNums.forEach(({el,suf})=>el.textContent='0'+suf);
  }
});

/* demo + contact + footer + showcase */
gsap.fromTo('.demo-wrap > div:first-child',{opacity:0,x:-55},{opacity:1,x:0,duration:.8,ease:'power3.out',scrollTrigger:st('.demo-wrap',{start:'top 80%'})});
gsap.fromTo('.demo-wrap .cp',{opacity:0,x:55},{opacity:1,x:0,duration:.8,ease:'power3.out',scrollTrigger:st('.demo-wrap',{start:'top 80%'})});
gsap.fromTo('.df',{opacity:0,x:-22},{opacity:1,x:0,duration:.5,stagger:.1,ease:'power2.out',scrollTrigger:st('.demo-feats',{start:'top 88%'})});
gsap.fromTo('.contact-info .ci',{opacity:0,x:-32},{opacity:1,x:0,duration:.55,stagger:.12,ease:'power2.out',scrollTrigger:st('.contact-info',{start:'top 84%'})});
gsap.fromTo('.contact-form',{opacity:0,x:44},{opacity:1,x:0,duration:.75,ease:'power3.out',scrollTrigger:st('.contact-form',{start:'top 84%'})});
gsap.fromTo('footer .fc',{opacity:0,y:26},{opacity:1,y:0,duration:.55,stagger:.12,ease:'power2.out',scrollTrigger:st('footer',{start:'top 90%'})});
gsap.fromTo('.showcase-video-wrap',{opacity:0,scale:.93,y:40},{opacity:1,scale:1,y:0,duration:.9,ease:'power3.out',scrollTrigger:{trigger:'#showcase',start:'top 80%',toggleActions:TA}});
gsap.fromTo('#showcase .showcase-text',{opacity:0,x:50},{opacity:1,x:0,duration:.85,ease:'power3.out',scrollTrigger:{trigger:'#showcase',start:'top 80%',toggleActions:TA}});
gsap.fromTo('.sp',{opacity:0,x:22},{opacity:1,x:0,duration:.5,stagger:.1,ease:'power2.out',scrollTrigger:{trigger:'.showcase-points',start:'top 88%',toggleActions:TA}});

/* dock */
gsap.from('#ai-dock',{y:80,opacity:0,duration:.7,ease:'back.out(2)',delay:1.5});

/* ─────────── PARTICLE NETWORK ─────────── */
(function initParticles(){
  const canvas = document.getElementById('particles-canvas');
  if(!canvas)return;
  const ctx = canvas.getContext('2d');
  let W,H,pts=[];
  function resize(){W=canvas.width=canvas.offsetWidth;H=canvas.height=canvas.offsetHeight;}
  resize();
  window.addEventListener('resize',resize);
  const COUNT=90,DIST=130,SPEED=.28,COL='rgba(59,130,246,';
  for(let i=0;i<COUNT;i++)pts.push({
    x:Math.random()*W,y:Math.random()*H,
    vx:(Math.random()-.5)*SPEED*2,vy:(Math.random()-.5)*SPEED*2,
    r:Math.random()*1.4+.6
  });
  (function draw(){
    ctx.clearRect(0,0,W,H);
    pts.forEach(p=>{p.x+=p.vx;p.y+=p.vy;if(p.x<0||p.x>W)p.vx*=-1;if(p.y<0||p.y>H)p.vy*=-1;});
    for(let i=0;i<COUNT;i++){
      for(let j=i+1;j<COUNT;j++){
        const dx=pts[i].x-pts[j].x,dy=pts[i].y-pts[j].y,d=Math.hypot(dx,dy);
        if(d<DIST){
          ctx.beginPath();ctx.moveTo(pts[i].x,pts[i].y);ctx.lineTo(pts[j].x,pts[j].y);
          ctx.strokeStyle=COL+(1-d/DIST)*.22+')';ctx.lineWidth=.8;ctx.stroke();
        }
      }
    }
    pts.forEach(p=>{ctx.beginPath();ctx.arc(p.x,p.y,p.r,0,Math.PI*2);ctx.fillStyle=COL+'.55)';ctx.fill();});
    requestAnimationFrame(draw);
  })();
})();

/* ─────────── CONTACT FORM ─────────── */
document.getElementById('contact-form').onsubmit = async e => {
  e.preventDefault();
  const btn = e.target.querySelector('button[type=submit]');
  btn.disabled = true; btn.textContent = 'Sending…';
  try{
    const r = await fetch('/contact',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({
      name:document.getElementById('f-name').value,
      email:document.getElementById('f-email').value,
      phone:document.getElementById('f-phone').value,
      service:document.getElementById('f-service').value,
      message:document.getElementById('f-message').value
    })});
    const d = await r.json();
    if(d.success){
      document.getElementById('form-ok').classList.add('show');
      e.target.reset();
      btn.textContent='✓ Sent!';
    } else { btn.disabled=false; btn.textContent='Send Message →'; alert('Error: '+(d.error||'Unknown')); }
  } catch { btn.disabled=false; btn.textContent='Send Message →'; alert('Something went wrong.'); }
};

/* ─────────── CHAT PANEL ─────────── */
let panelOpen=false, sessionId=null, busy=false;
function togglePanel(){
  panelOpen = !panelOpen;
  document.getElementById('ai-panel').classList.toggle('open', panelOpen);
  if(panelOpen) setTimeout(()=>document.getElementById('panel-txt').focus(), 300);
}
function openPanel(){ if(!panelOpen) togglePanel(); }
function addMsg(role, text){
  const d = document.createElement('div');
  d.className = 'pm '+role;
  d.textContent = text;
  const c = document.getElementById('panel-msgs');
  c.appendChild(d); c.scrollTop = c.scrollHeight;
  return d;
}

/* TTS */
let _ttsAudio = null;
async function speak(text){
  try{
    if(_ttsAudio){_ttsAudio.pause();_ttsAudio=null;}
    const r = await fetch('/tts',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({text})});
    if(!r.ok) return;
    const url = URL.createObjectURL(await r.blob());
    _ttsAudio = new Audio(url);
    _ttsAudio.play();
    _ttsAudio.onended = ()=>{URL.revokeObjectURL(url);_ttsAudio=null;};
  } catch(e){ console.warn('TTS error', e); }
}

async function sendChat(){
  const inp = document.getElementById('panel-txt');
  const msg = inp.value.trim();
  if(!msg||busy) return;
  inp.value=''; busy=true; document.getElementById('send-btn').disabled = true;
  addMsg('user', msg);
  const t = addMsg('bot thinking', 'Aria is typing…');
  try{
    const r = await fetch('/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({message:msg, session_id:sessionId})});
    const d = await r.json();
    sessionId = d.session_id || sessionId;
    t.remove();
    addMsg('bot', d.reply);
    speak(d.reply);
    /* Auto-refresh calendar slots if Aria booked / cancelled / rescheduled */
    if(d.tool && ['book','cancel','reschedule'].includes(d.tool) && typeof loadSlots === 'function'){
      loadSlots();
    }
  } catch { t.remove(); addMsg('bot','Sorry, I ran into an issue. Please try again.'); }
  busy=false; document.getElementById('send-btn').disabled=false; document.getElementById('panel-txt').focus();
}

/* mic for chat panel */
let mr=null, chunks=[], recording=false;
async function toggleVoice(){
  const btn = document.getElementById('mic-btn');
  if(recording){ mr.stop(); recording=false; btn.classList.remove('rec'); btn.innerHTML='&#127908;'; return; }
  try{
    const s = await navigator.mediaDevices.getUserMedia({audio:true});
    mr = new MediaRecorder(s); chunks=[];
    mr.ondataavailable = e => chunks.push(e.data);
    mr.onstop = async () => {
      s.getTracks().forEach(t=>t.stop());
      if(busy) return;
      busy=true; document.getElementById('send-btn').disabled=true;
      const t = addMsg('bot thinking','Transcribing…');
      try{
        const blob = new Blob(chunks,{type:'audio/webm'});
        const fd = new FormData();
        fd.append('audio', blob, 'voice.webm');
        if(sessionId) fd.append('session_id', sessionId);
        const r = await fetch('/voice',{method:'POST',body:fd});
        const d = await r.json();
        sessionId = d.session_id || sessionId;
        t.remove();
        if(d.transcript) addMsg('user', d.transcript);
        if(d.reply){ addMsg('bot', d.reply); speak(d.reply); }
        else if(!d.transcript) addMsg('bot',"Didn't catch that — please try again.");
        if(d.tool && ['book','cancel','reschedule'].includes(d.tool) && typeof loadSlots === 'function'){
          loadSlots();
        }
      } catch { t.remove(); addMsg('bot','Voice processing failed. Try typing instead.'); }
      busy=false; document.getElementById('send-btn').disabled=false;
    };
    mr.start(); recording=true; btn.classList.add('rec'); btn.innerHTML='&#9209;';
  } catch { alert('Microphone access denied.'); }
}

/* ─────────── REAL-TIME CALL (VAD) ─────────── */
let callActive=false, callBusy=false, callSessionId=null;
let callStream=null, callCtx=null, callAnalyser=null;
let callMr=null, callChunks=[];
let vadSpeaking=false, vadTimer=null, vadRAF=null;
const VAD_THRESHOLD=0.018, SILENCE_MS=900;

async function startCallUI(){
  if(callActive){ endCall(); return; }
  try{ callStream = await navigator.mediaDevices.getUserMedia({audio:true,video:false}); }
  catch{ alert('Microphone access denied.'); return; }
  callCtx = new AudioContext();
  callAnalyser = callCtx.createAnalyser();
  callAnalyser.fftSize = 512;
  callCtx.createMediaStreamSource(callStream).connect(callAnalyser);
  callActive = true;
  callSessionId = sessionId;
  document.getElementById('call-overlay').classList.add('active');
  document.getElementById('call-dock-btn').classList.add('in-call');
  document.getElementById('call-dock-lbl').textContent = 'End Call';
  setCallStatus('Listening…');
  _startVADLoop();
}
function _startVADLoop(){
  if(!callActive) return;
  callChunks=[];
  callMr = new MediaRecorder(callStream,{mimeType:MediaRecorder.isTypeSupported('audio/webm;codecs=opus')?'audio/webm;codecs=opus':'audio/webm'});
  callMr.ondataavailable = e => { if(e.data.size>0) callChunks.push(e.data); };
  callMr.onstop = _processCallTurn;
  const buf = new Float32Array(callAnalyser.frequencyBinCount);
  function vad(){
    if(!callActive) return;
    vadRAF = requestAnimationFrame(vad);
    if(callBusy) return;
    callAnalyser.getFloatTimeDomainData(buf);
    let sum=0; for(let i=0;i<buf.length;i++) sum += buf[i]*buf[i];
    const rms = Math.sqrt(sum/buf.length);
    if(rms > VAD_THRESHOLD){
      if(!vadSpeaking){
        vadSpeaking=true;
        if(callMr.state==='inactive') callMr.start(100);
        setCallStatus('Listening…');
      }
      if(vadTimer){ clearTimeout(vadTimer); vadTimer=null; }
    } else if(vadSpeaking && !vadTimer){
      vadTimer = setTimeout(()=>{
        vadSpeaking=false; vadTimer=null;
        if(callMr && callMr.state==='recording') callMr.stop();
      }, SILENCE_MS);
    }
  }
  vad();
}
async function _processCallTurn(){
  if(!callActive || callChunks.length===0){ if(callActive) _startVADLoop(); return; }
  callBusy=true;
  setCallStatus('Processing…');
  try{
    const blob = new Blob(callChunks,{type:'audio/webm'});
    const fd = new FormData();
    fd.append('audio', blob, 'call.webm');
    if(callSessionId) fd.append('session_id', callSessionId);
    const r = await fetch('/voice',{method:'POST',body:fd});
    const d = await r.json();
    callSessionId = d.session_id || callSessionId;
    sessionId = callSessionId;
    if(d.transcript) addCallLog('You', d.transcript);
    if(d.reply){
      addCallLog('Aria', d.reply);
      setCallStatus('Aria is speaking…');
      await _speakCall(d.reply);
      if(d.tool && ['book','cancel','reschedule'].includes(d.tool) && typeof loadSlots === 'function'){
        loadSlots();
      }
    } else if(!d.transcript){ setCallStatus("Didn't catch that — try again…"); }
  } catch(e){ console.warn('Call turn error', e); setCallStatus('Connection issue, retrying…'); }
  callBusy=false;
  if(callActive){ setCallStatus('Listening…'); _startVADLoop(); }
}
async function _speakCall(text){
  return new Promise(async resolve => {
    try{
      const r = await fetch('/tts',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({text})});
      if(!r.ok) return resolve();
      const url = URL.createObjectURL(await r.blob());
      const audio = new Audio(url);
      audio.onended = ()=>{URL.revokeObjectURL(url); resolve();};
      audio.onerror = ()=>resolve();
      audio.play();
    } catch { resolve(); }
  });
}
function endCall(){
  callActive=false;
  if(vadRAF){ cancelAnimationFrame(vadRAF); vadRAF=null; }
  if(vadTimer){ clearTimeout(vadTimer); vadTimer=null; }
  try{ if(callMr && callMr.state!=='inactive') callMr.stop(); } catch{}
  if(callStream){ callStream.getTracks().forEach(t=>t.stop()); callStream=null; }
  if(callCtx){ callCtx.close(); callCtx=null; }
  callBusy=false; vadSpeaking=false;
  document.getElementById('call-overlay').classList.remove('active');
  document.getElementById('call-dock-btn').classList.remove('in-call');
  document.getElementById('call-dock-lbl').textContent = 'Call Aria';
  const log = document.getElementById('call-log');
  log.innerHTML=''; log.classList.remove('has-log');
}
function setCallStatus(msg){
  const el = document.getElementById('call-status');
  if(el) el.textContent = msg;
}
function addCallLog(who, text){
  const log = document.getElementById('call-log');
  const line = document.createElement('div');
  line.className = who==='You'?'cl-user':'cl-aria';
  line.textContent = who+': '+text;
  log.appendChild(line);
  log.scrollTop = log.scrollHeight;
  log.classList.add('has-log');
}
